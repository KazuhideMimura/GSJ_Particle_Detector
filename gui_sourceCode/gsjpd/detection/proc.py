import time
from pathlib import Path

from PySide6.QtCore import Signal, Slot

from ..helper.filesystem import file_hash, file_mtime
from ..helper.threading import SubprocessWorker, SubprocessWorkerThread


class DetectionThread(SubprocessWorkerThread):
    stateChanged: Signal = Signal(str, float, str)

    def __init__(
        self,
        exec: str,
        startfile: str,
        mtime: float = 0,
        hash: str = "",
        check_interval: int = 5,
        **kwargs,
    ):
        super().__init__(
            worker=DetectionWorker(
                exec=exec,
                startfile=startfile,
                mtime=mtime,
                hash=hash,
                check_interval=check_interval,
                **kwargs,
            ),
        )
        self.worker.stateChanged.connect(self.stateChanged)


class DetectionWorker(SubprocessWorker):
    stateChanged = Signal(str, float, str)

    _mtime: float = None
    _hash: str = None
    _startfile: Path = None

    def __init__(
        self,
        exec: str,
        startfile: str,
        mtime: float = 0,
        hash: str = "",
        check_interval: int = 5,
        wait_interval: float = 0.1,
        **kwargs,
    ):
        super().__init__(exec=exec, wait_interval=wait_interval, **kwargs)

        self._startfile = Path(startfile)
        self.wait_interval = max(wait_interval, 0.05)
        self.check_interval = max(check_interval, 1)

        self.procStart.connect(self.onProcStart)
        self.procEnd.connect(self.onProcEnd)

        with self.lock_obj:
            self._mtime = mtime or 0
            self._hash = hash

    @Slot(int)
    def onProcStart(self, pid: int):
        pass

    @Slot(int)
    def onProcEnd(self, retval: int):
        self.stateChanged.emit(str(self._startfile), self._mtime, self._hash)

    def checkUpdate(self) -> bool:
        if not self._startfile.exists():
            return False

        mtime = file_mtime(self._startfile)
        hash = file_hash(self._startfile)
        if mtime <= self._mtime and hash == self._hash:
            return False

        with self.lock_obj:
            self._mtime = mtime
            self._hash = hash

        return True

    def __call__(self):
        self.workerStart.emit()
        self.debug.emit("Detection loop start.")

        while True:
            if self.checkUpdate():
                self.info.emit("Modified start file.")
                self.exec_subprocess()
            else:
                # Wait for a while before checking again
                for _ in range(self.check_interval):
                    self.waiting.emit()
                    time.sleep(self.wait_interval)

            with self.lock_obj:
                if self.stop_flag:
                    self.info.emit("Break detection worker.")
                    break

        self.debug.emit("Detection loop finished.")
        self.workerEnd.emit()
