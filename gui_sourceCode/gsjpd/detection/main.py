import os
from datetime import datetime
from enum import IntEnum
from logging import Logger
from pathlib import Path

from PySide6.QtCore import QDir, Signal, Slot
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from ..helper import settings
from ..helper.filesystem import abspath, file_hash, file_mtime, relpath
from ..helper.qcontext import QContext
from ..io.logging import closeLogger, getLogger
from ..widget.console import ConsoleWidget
from ..widget.dialog import PromptDialog
from .dialog import DetectionDialog
from .proc import DetectionThread


class InitialHandling(IntEnum):
    ProcessNewer = 0
    ShowDialog = 1
    ProcessAlways = 2
    SkipAlways = 3


class DetectionParams(QWidget):
    basedir: QLineEdit = None
    conf_thres: QLineEdit = None
    iou_thres: QLineEdit = None

    def __init__(self, parent=None):
        super().__init__(parent)

        with QContext(QHBoxLayout()) as layout:
            layout.setContentsMargins(0, 0, 0, 0)
            layout.setSpacing(6)
            self.setLayout(layout)

        with QContext(QLabel(self.tr("Base folder")), QLineEdit()) as (label, input):
            input.setEnabled(False)
            self.layout().addWidget(label)
            self.layout().addWidget(input)
            self.basedir = input

        self.layout().addSpacing(6)

        with QContext(QLabel(self.tr("Confidence threshold")), QLineEdit()) as (label, input):
            input.setEnabled(False)
            self.layout().addWidget(label)
            self.layout().addWidget(input)
            self.conf_thres = input

        self.layout().addSpacing(6)

        with QContext(QLabel(self.tr("NMS IoU threshold")), QLineEdit()) as (label, input):
            input.setEnabled(False)
            self.layout().addWidget(label)
            self.layout().addWidget(input)
            self.iou_thres = input

    def updateData(self, basedir: str, conf_thres: str, iou_thres: str):
        self.basedir.setText(basedir)
        self.conf_thres.setText(conf_thres)
        self.iou_thres.setText(iou_thres)

    def clear(self):
        self.basedir.clear()
        self.conf_thres.clear()
        self.iou_thres.clear()


class DetectionToolbar(QWidget):
    start = Signal()
    stop = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)

        with QContext(QHBoxLayout()) as layout:
            layout.setContentsMargins(3, 3, 3, 3)
            layout.setSpacing(2)
            self.setLayout(layout)

        start_icon = QIcon()

        with QContext(
            QPushButton(icon=start_icon, text=self.tr("Start"), parent=self)
        ) as button:
            button.setProperty("style", "primary")
            button.setFlat(True)
            button.clicked.connect(self.start)
            self.layout().addWidget(button)
            self.start_button = button

        stop_icon = QIcon()

        with QContext(QPushButton(icon=stop_icon, text=self.tr("Stop"), parent=self)) as button:
            button.setProperty("style", "danger")
            button.setFlat(True)
            button.clicked.connect(self.stop)
            self.layout().addWidget(button)
            self.stop_button = button

        self.layout().addStretch()

        with QContext(DetectionParams()) as params:
            params.setVisible(False)
            self.layout().addWidget(params)
            self.params = params


class DetectionMainWidget(QWidget):
    console: ConsoleWidget = None
    thread: DetectionThread = None
    logger: Logger = None

    def __init__(self, parent=None):
        super().__init__(parent)

        with QContext(QVBoxLayout()) as layout:
            layout.setContentsMargins(0, 0, 0, 0)
            layout.setSpacing(0)
            self.setLayout(layout)

        with QContext(DetectionToolbar(parent=self)) as toolbar:
            toolbar.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Maximum)
            toolbar.start.connect(self.onStart)
            toolbar.stop.connect(self.onStop)
            self.layout().addWidget(toolbar)
            self.toolbar = toolbar

        with QContext(ConsoleWidget(logLevel="DEBUG")) as console:
            console.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            self.layout().addWidget(console)
            self.console = console

        self.initLogger()

    def initLogger(self):
        if self.logger:
            return

        detect_log = settings.value("detect_log", "detect.log")
        log_level = os.environ.get("LOG_LEVEL", settings.value("log_level", "INFO")).upper()

        self.logger = getLogger(
            filename=abspath(detect_log),
            level=log_level,
        )
        self.console.attachLogger(self.logger)

    def closeLogger(self):
        if self.logger:
            closeLogger(self.logger)
            self.logger

    def __del__(self):
        self.closeLogger()

    def isThreadRunning(self):
        if self.thread is not None:
            return self.thread.isRunning()

        return False

    def terminate(self):
        if self.isThreadRunning():
            self.logger.info("Terminate detection thread.")

        self.kill()
        self.closeLogger()

    def kill(self):
        if self.thread is not None:
            self.thread.interrupt()

    @Slot()
    def onStart(self):
        if not self.logger:
            self.initLogger()

        if self.thread is not None:
            self.logger.error("Detection thread is already running")
            return

        dialog = DetectionDialog(self)
        if dialog.exec():
            self.startDetect(
                basedir=dialog.basedir.text(),
                conf_thres=dialog.conf_thres.text(),
                iou_thres=dialog.iou_thres.text(),
            )

    @Slot()
    def onStop(self):
        if self.thread is None:
            self.logger.warning("No detection thread is running")
            return

        self.thread.interrupt()

    @Slot()
    def onThreadStarted(self):
        self.logger.info("Detection thread started.")

    @Slot()
    def onThreadFinished(self):
        self.logger.info("Detection thread finished.")

        self.toolbar.params.setVisible(False)
        self.toolbar.params.clear()

        if self.thread is not None:
            self.thread.deleteLater()
            self.thread = None

    @Slot()
    def onSubprocSuccess(self):
        self.logger.error("Detection subprocess completed.")

    @Slot()
    def onSubprocAbort(self):
        self.logger.error("Aborted.")

    @Slot()
    def onSubprocWaiting(self):
        QApplication.processEvents()

    def startDetect(self, basedir: str, conf_thres: str, iou_thres: str):
        yolov9_dir = settings.value("yolov9_dir")
        if not Path(yolov9_dir).exists():
            self.logger.error(f"Yolov9 folder not found: {yolov9_dir}")
            return

        with settings.group("Detection") as group:
            detect_py = group.value("detect_py")
            start_txt = group.value("start_txt")
            device = group.value("device", "0")
            initial_handling = settings.safeInt(group.value("initial_handling", 0))

        assert detect_py is not None
        assert start_txt is not None
        assert device is not None

        if not abspath(detect_py).exists():
            self.logger.error(f"Detection script not found: {detect_py}")
            return

        basedir = abspath(basedir)
        if not basedir.exists():
            self.logger.error(f"Base folder not found: {basedir}")
            return

        args = {
            "--basedir": relpath(basedir, posix=True),
            "--conf_thres": conf_thres,
            "--iou_thres": iou_thres,
            "--device": device,
        }

        startfile = Path(basedir, start_txt)
        try:
            with settings.group("Internal") as group:
                last_mtime = settings.safeFloat(group.value("start_mtime", None))
                last_hash = group.value("start_hash", "")
        except Exception:
            last_mtime = 0
            last_hash = ""

        if startfile.exists():
            mtime = file_mtime(startfile)
            hash = file_hash(startfile)

            match initial_handling:
                case InitialHandling.ProcessNewer:
                    # default
                    pass
                case InitialHandling.ShowDialog:
                    retval = self.execInitialProcessDialog(startfile, mtime, hash)
                    match retval:
                        case PromptDialog.Result.Yes:
                            last_mtime = 0
                            last_hash = ""
                        case PromptDialog.Result.No:
                            last_mtime = mtime
                            last_hash = hash
                        case _:
                            return

                case InitialHandling.ProcessAlways:
                    # force
                    last_mtime = 0
                    last_hash = ""
                case InitialHandling.SkipAlways:
                    # force
                    last_mtime = mtime
                    last_hash = hash
                case _:
                    pass

        self.thread = DetectionThread(
            exec=detect_py,
            startfile=startfile,
            mtime=last_mtime,
            hash=last_hash,
            check_interval=5,
            **args,
        )
        self.thread.stateChanged.connect(self.onWorkerStateChanged)

        self.thread.debug.connect(self.logger.debug)
        self.thread.info.connect(self.logger.info)
        self.thread.error.connect(self.logger.error)

        self.thread.started.connect(self.onThreadStarted)
        self.thread.finished.connect(self.onThreadFinished)
        self.thread.success.connect(self.onSubprocSuccess)
        self.thread.abort.connect(self.onSubprocAbort)
        self.thread.waiting.connect(self.onSubprocWaiting)

        QDir.setCurrent(yolov9_dir)

        self.toolbar.params.updateData(relpath(basedir, posix=True), conf_thres, iou_thres)
        self.toolbar.params.setVisible(True)
        self.thread.startWorker()

    def execInitialProcessDialog(self, startfile, mtime, hash):
        msg = self.tr(
            "An existing start file was found. Do you want to run detection on this file?"
        )
        prompt = PromptDialog(self.tr("Start file found"), msg, parent=self.window())
        prompt.addMetadata(self.tr("Start file"), str(startfile))
        prompt.addMetadata(
            self.tr("Last Modified"),
            datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M:%S"),
        )
        prompt.setYesLabel(self.tr("Process"))
        prompt.setNoLabel(self.tr("Skip"))
        prompt.setCancelLabel(self.tr("Cancel"))
        return prompt.exec()

    @Slot(str, float, str)
    def onWorkerStateChanged(self, startfile: str, mtime: float, hash: str):
        with settings.group("Internal", sync=True) as group:
            group.setValue("startfile", startfile)
            group.setValue("start_mtime", mtime)
            group.setValue("start_hash", hash)

        self.logger.debug(f"StartFile {startfile} mtime:{mtime}, hash:{hash}")

    def updateData(self):
        pass
