import time

from ..helper.threading import SubprocessWorker, SubprocessWorkerThread


class TrainingThread(SubprocessWorkerThread):
    def __init__(self, exec: str, **kwargs):
        super().__init__(
            worker=ExecProcesscWorker(exec=exec, **kwargs),
        )

    def interrupt(self):
        super().interrupt()


class TestThread(SubprocessWorkerThread):
    def __init__(self, exec: str, **kwargs):
        super().__init__(
            worker=ExecProcesscWorker(exec=exec, **kwargs),
        )


class DetectThread(SubprocessWorkerThread):
    def __init__(self, exec: str, **kwargs):
        super().__init__(
            worker=ExecProcesscWorker(exec=exec, **kwargs),
        )


class FormatThread(SubprocessWorkerThread):
    def __init__(self, exec: str, **kwargs):
        super().__init__(
            worker=ExecProcesscWorker(exec=exec, **kwargs),
        )


class ExecProcesscWorker(SubprocessWorker):
    def __call__(self):
        self.workerStart.emit()
        self.debug.emit("Enter worker loop.")

        with self.lock_obj:
            self.stop_flag = True

        while True:
            self.exec_subprocess()
            with self.lock_obj:
                if self.stop_flag:
                    self.debug.emit("Break worker loop.")
                    break

            self.waiting.emit()
            time.sleep(self.wait_interval)

        self.debug.emit("Exit worker loop.")
        self.workerEnd.emit()

    def interrupt(self):
        super().interrupt()

        if self.proc:
            self.proc.terminate()
