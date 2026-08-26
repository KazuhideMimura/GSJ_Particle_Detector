import asyncio
import os
import re
import sys
from pathlib import Path
from subprocess import Popen
from threading import Lock

from PySide6.QtCore import QObject, QThread, Signal, Slot

ansi_escape = re.compile(r"\x1b\[[0-9;]*[mG]")


def split_buffer(buffer: str) -> list[str]:
    result = []

    def push_back(part: str):
        if result and result[-1] == "\r":
            if part == "\n":
                result[-1] = "\n"
            else:
                result[-1] += part
        else:
            result.append(part)

    current_part = ""
    for i, char in enumerate(buffer):
        if char == "\r":
            if current_part:
                push_back(current_part)
                current_part = ""

            push_back("\r")
        elif char == "\n":
            if current_part:
                push_back(current_part)
                current_part = ""

            push_back("\n")
        else:
            current_part += char

    if current_part:
        push_back(current_part)

    return result


def quote_arg(arg: str) -> str:
    if not arg:
        return "''"

    if " " in arg:
        return f"'{arg}'"
    else:
        return arg


class SubprocessWorker(QObject):
    # worker signals (internal)
    workerStart = Signal()
    workerEnd = Signal()

    # subprocess signals (internal)
    procStart = Signal(int)
    procEnd = Signal(int)

    # worker signals (public)
    success = Signal()
    abort = Signal()
    waiting = Signal()

    # logging signals (public)
    debug = Signal(str)
    info = Signal(str)
    error = Signal(str)

    exec: str = None
    kwargs: dict = None

    proc: Popen = None
    lock_obj: Lock = Lock()
    stop_flag: bool = None

    proc: asyncio.subprocess.Process = None
    stdout_buf: str = None

    def __init__(self, exec: str, wait_interval: float = 0.1, **kwargs):
        super().__init__()

        self.kwargs = kwargs
        self.wait_interval = max(wait_interval, 0.05)

        if Path(exec).exists():
            self.exec = os.fspath(exec)
        else:
            raise FileNotFoundError(f"File not found: {exec}")

        self.encoding = os.environ.get("PYTHONIOENCODING", sys.getdefaultencoding())
        self.lock_obj = Lock()

    def __call__(self):
        raise NotImplementedError("SubprocessWorker.__call__")

    def interrupt(self):
        with self.lock_obj:
            self.stop_flag = True
            self.info.emit("Interrupted.")

    def exec_subprocess(self):
        try:
            asyncio.run(self.exec_subprocess_async())
        except Exception:
            self.error.emit("Failed to exec subprocess.")

    def generate_args(self):
        for key, value in self.kwargs.items():
            if isinstance(value, bool):
                # store_trueフラグの場合はTrueの場合にフラグを出力
                if value:
                    yield key
            elif isinstance(value, Path):
                yield key
                yield os.fspath(value)
            elif value is not None:
                yield key
                yield str(value)

    async def exec_subprocess_async(self):
        args = [self.exec] + [*self.generate_args()]

        try:
            self.info.emit(f"Start subprocess. [{self.exec}] (encoding: {self.encoding})")
            self.info.emit(" ".join(map(quote_arg, args)))

            self.stdout_buf = ""

            self.proc = await asyncio.create_subprocess_exec(
                sys.executable,
                *args,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
                env=dict(os.environ, PYTHONIOENCODING=self.encoding),
            )

            self.procStart.emit(self.proc.pid)

            read_task = asyncio.create_task(self.read_stdout(self.proc.stdout))
            wait_task = asyncio.create_task(self.emit_waiting())

            retval = await self.proc.wait()

            await read_task
            wait_task.cancel()
            try:
                await wait_task  # キャンセルされたタスクの完了を待機
            except asyncio.CancelledError:
                pass  # キャンセルは想定された動作なので無視

            if retval == 0:
                self.success.emit()
            else:
                raise Exception(f"Illeagl return code ({retval})")

            self.debug.emit("End subprocess.")

        except Exception as e:
            exc_type, exc_value, exc_traceback = sys.exc_info()
            self.error.emit(str(e))
            self.debug.emit(str(exc_type))
            self.debug.emit(str(exc_value))
            self.debug.emit(str(exc_traceback))

            try:
                if isinstance(self.proc, Popen):
                    self.proc.kill()
            finally:
                self.abort.emit()
                retval = -1

        finally:
            self.procEnd.emit(retval if retval is not None else -1)
            self.proc = None

        return retval

    async def emit_waiting(self):
        while True:
            await asyncio.sleep(self.wait_interval)
            self.waiting.emit()

    async def read_stdout(self, stream: asyncio.StreamReader):
        def emit_parts(parts: list[str]):
            for part in filter(lambda x: x != "\n", parts):
                self.info.emit(part)

        while True:
            chunk = await stream.read(1024)
            if chunk:
                self.stdout_buf += ansi_escape.sub(
                    "", chunk.decode(self.encoding, errors="ignore")
                )

                *parts, tail = split_buffer(self.stdout_buf)
                if parts:
                    emit_parts(parts)
                elif tail == "\n":
                    # 改行が単独で出力された場合は空行をemit
                    emit_parts([""])

                self.stdout_buf = tail.replace("\n", "")  # 末尾の改行を削除

            if stream.at_eof():
                # 最後の未完了分を分割してemit
                emit_parts(split_buffer(self.stdout_buf))
                break


class SubprocessWorkerThread(QThread):
    # worker proc signals
    success = Signal()
    abort = Signal()
    waiting = Signal()

    # logging signals
    debug = Signal(str)
    info = Signal(str)
    error = Signal(str)

    worker: SubprocessWorker = None

    def __init__(self, worker: SubprocessWorker):
        super().__init__()

        self.worker = worker

        # connect worker proc signals
        self.worker.success.connect(self.success)
        self.worker.abort.connect(self.abort)
        self.worker.waiting.connect(self.waiting)

        # connect logging signals
        self.worker.debug.connect(self.debug)
        self.worker.info.connect(self.info)
        self.worker.error.connect(self.error)

        # connect internal worker signals
        self.worker.workerStart.connect(self.onWorkerStart)
        self.worker.workerEnd.connect(self.onWorkerEnd)

    def startWorker(self, /, priority=QThread.InheritPriority):
        if os.environ.get("DEBUG_THREADING", False):
            self.started.emit()
            self.worker()
            self.finished.emit()
        else:
            self.worker.moveToThread(self)
            self.started.connect(self.worker)
            super().start(priority=priority)

    def interrupt(self):
        if self.worker is None:
            return

        self.worker.interrupt()

    @Slot()
    def onWorkerStart(self):
        self.debug.emit("Worker started.")

    @Slot()
    def onWorkerEnd(self):
        self.debug.emit("Worker finished.")

        self.quit()
        self.wait(0)

        if self.worker is not None:
            self.worker.deleteLater()
            self.worker = None
