import os
import re
from datetime import datetime
from functools import partial
from logging import Logger
from pathlib import Path

from PySide6.QtCore import QDir, Qt, Signal, Slot
from PySide6.QtGui import QCloseEvent, QPixmap
from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QHBoxLayout,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from ..helper import settings
from ..helper.filesystem import abspath, argpath, relpath
from ..helper.qcontext import QContext
from ..helper.threading import SubprocessWorkerThread
from ..io.logging import closeLogger, getLogger
from ..widget.console import ConsoleWidget
from ..widget.dialog import MessageDialog
from ..widget.image import ImageViewWidget
from .arguments import ArgumentsForm
from .data import ModelInfo, Paramset
from .dialog import SampleDetectDialog
from .metadata import MetadtaForm
from .metrics import MetricsView
from .paramset import ParamsetForm
from .worker import DetectThread, FormatThread, TestThread, TrainingThread


class TrainerSidebar(QWidget):
    formatClicked = Signal()
    trainClicked = Signal()
    testClicked = Signal()
    detectClicked = Signal()
    stopClicked = Signal()

    model: ModelInfo = None

    metadata: MetadtaForm = None
    paramset: ParamsetForm = None
    arguments: ArgumentsForm = None
    metrics: MetricsView = None

    thread: SubprocessWorkerThread = None

    def __init__(self, model: ModelInfo, parent=None):
        super().__init__(parent)

        self.model = model

        self.setMinimumWidth(400)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Maximum)

        self.setLayout(QVBoxLayout())
        self.layout().setContentsMargins(3, 3, 3, 3)
        self.layout().setSpacing(2)

        with QContext(QScrollArea()) as scroll:
            self.layout().addWidget(scroll)

            scroll.setWidgetResizable(True)
            scroll.setSizeAdjustPolicy(QScrollArea.AdjustToContents)
            scroll.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.MinimumExpanding)

            with QContext(QWidget()) as widget:
                scroll.setWidget(widget)

                widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
                widget.setLayout(QVBoxLayout())
                widget.layout().setContentsMargins(0, 0, 0, 0)
                widget.layout().setSpacing(3)

                with QContext(MetadtaForm()) as metadata:
                    widget.layout().addWidget(metadata)
                    metadata.setValues(self.model.metadata)
                    self.metadata = metadata

                # widget.layout().addSpacing(3)

                with QContext(ParamsetForm()) as paramset:
                    self.paramset = paramset
                    widget.layout().addWidget(paramset)
                    paramset.setValues(self.model.paramset)

                with QContext(QHBoxLayout()) as layout:
                    widget.layout().addLayout(layout)

                    layout.setContentsMargins(3, 3, 3, 3)
                    layout.setSpacing(2)
                    layout.addStretch()

                    with QContext(QPushButton()) as button:
                        self.paramset_button = button
                        layout.addWidget(button)

                        button.setProperty("style", "primary")
                        button.setText(self.tr("Write parameter file"))
                        button.clicked.connect(self.formatClicked)

                # widget.layout().addSpacing(3)

                with QContext(ArgumentsForm()) as args:
                    self.arguments = args
                    widget.layout().addWidget(args)
                    args.init()
                    args.setValues(self.model.arguments)

                with QContext(QHBoxLayout()) as layout:
                    widget.layout().addLayout(layout)

                    layout.setContentsMargins(3, 3, 3, 3)
                    layout.setSpacing(2)
                    layout.addStretch()

                    with QContext(QPushButton()) as button:
                        self.train_button = button
                        layout.addWidget(button)

                        button.setProperty("style", "primary")
                        button.setText(self.tr("Train and test"))
                        button.clicked.connect(self.trainClicked)

                    with QContext(QPushButton()) as button:
                        self.test_button = button
                        layout.addWidget(button)

                        button.setProperty("style", "primary")
                        button.setText(self.tr("Test only"))
                        button.clicked.connect(self.testClicked)

                    with QContext(QPushButton()) as button:
                        self.test_button = button
                        layout.addWidget(button)

                        button.setProperty("style", "primary")
                        button.setText(self.tr("Sample detect"))
                        button.clicked.connect(self.detectClicked)

                    with QContext(QPushButton()) as button:
                        self.stop_button = button
                        layout.addWidget(button)

                        button.setProperty("style", "danger")
                        button.setText(self.tr("Stop"))
                        button.clicked.connect(self.stopClicked)
                        # stopボタン無効化
                        button.setEnabled(False)
                        button.hide()

                # widget.layout().addSpacing(3)

                with QContext(MetricsView(self)) as metrics:
                    self.metrics = metrics
                    widget.layout().addWidget(metrics)

        self.metadata.inputChanged.connect(self.onMetadataInputChanged)
        self.arguments.inputChanged.connect(self.onArgumentsInputChanged)
        self.arguments.fileSelected.connect(self.onArgumentsFileSelected)
        self.paramset.inputChanged.connect(self.onParamsetInputChanged)

    def updateData(self, model: ModelInfo = None):
        if model is not None:
            self.model = model

        self.metadata.setValues(self.model.metadata)
        self.paramset.setValues(self.model.paramset)
        self.arguments.setValues(self.model.arguments)
        self.metrics.setValues(self.model.metrics)

        self.updateParamsetButtonState()
        self.updateTrainButtonsState()

    def updateParamsetButtonState(self):
        enable = self.paramset.hasAcceptableInput()
        self.paramset_button.setEnabled(enable)

    def updateTrainButtonsState(self, running: bool = False):
        enable = self.metadata.hasAcceptableInput() and self.arguments.hasAcceptableInput()
        self.train_button.setEnabled(enable and not running)
        self.test_button.setEnabled(enable and not running)

    def setRunningState(self, running: bool = False):
        self.updateTrainButtonsState(running)

    @Slot(str, object)
    def onMetadataInputChanged(self, key: str, value: object):
        if hasattr(self.model.metadata, key):
            setattr(self.model.metadata, key, value)

        match key:
            case "name":
                self.renameRunsDir(value)

        self.updateTrainButtonsState()

    @Slot(str, object)
    def onParamsetInputChanged(self, key: str, value: object):
        # 'class#'の正規表現に一致する場合は、#を取り出してkeyとしてdictに格納する
        m = re.match(r"class(\d+)", key)
        if m:
            index = int(m.group(1))
            self.model.paramset.classes[index] = value
        else:
            if hasattr(self.model.paramset, key):
                setattr(self.model.paramset, key, value)

        # ファイルパスが変更された場合は設定に保存する
        match key:
            case "dataset_dir":
                settings.setValue(f"{key}", relpath(value, posix=True))

        self.updateParamsetButtonState()

    @Slot(str, object)
    def onArgumentsInputChanged(self, key: str, value: object):
        if hasattr(self.model.arguments, key):
            setattr(self.model.arguments, key, value)

        # ファイルパスが変更された場合は設定に保存する
        match key:
            case "data_yaml" | "hyp_yaml":
                settings.setValue(f"{key}", relpath(value, posix=True))

        self.updateTrainButtonsState()

    @Slot(str, object)
    def onArgumentsFileSelected(self, key: str, value: object):
        # ファイルが選択された場合は内容を読み込む
        match key:
            case "data_yaml":
                self.model.paramset.load_data_yaml(value)
            case "hyp_yaml":
                self.model.paramset.load_hyp_yaml(value)

        # 表示に反映
        self.updateData()

    def renameRunsDir(self, name: str):
        if not self.model.runs_dir or not abspath(self.model.runs_dir).exists():
            return


class TrainerDialog(QDialog):
    trainStart = Signal()
    testStart = Signal()
    detectStart = Signal()
    trainCompleted = Signal()
    testCompleted = Signal()
    detectCompleted = Signal()
    formatCompleted = Signal()
    runsdirChanged = Signal(str, str)

    logger: Logger = None
    model: ModelInfo = None
    detectDialog: SampleDetectDialog = None

    thread: TrainingThread = None

    terminating: bool = False

    def __init__(self, model: ModelInfo, parent=None):
        super().__init__(parent)

        # モデル情報が指定されていない場合は新規作成する
        self.model = model

        self.setWindowModality(Qt.WindowModality.NonModal)
        self.setWindowFlag(Qt.WindowType.WindowCloseButtonHint, True)
        self.setWindowFlag(Qt.WindowType.WindowMinimizeButtonHint, True)
        self.setWindowFlag(Qt.WindowType.WindowMaximizeButtonHint, True)
        self.setWindowFlag(Qt.WindowType.WindowContextHelpButtonHint, False)

        self.setSizeGripEnabled(True)
        self.setWindowTitle(self.tr("Train detection model"))

        with QContext(QHBoxLayout()) as layout:
            layout.setContentsMargins(3, 3, 3, 3)
            self.setLayout(layout)

        with QContext(TrainerSidebar(self.model, self)) as sidebar:
            sidebar.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Expanding)
            sidebar.trainClicked.connect(self.onTrainClicked)
            sidebar.testClicked.connect(self.onTestClicked)
            sidebar.detectClicked.connect(self.onDetectClicked)
            sidebar.stopClicked.connect(self.onStopClicked)
            sidebar.formatClicked.connect(self.onFormatClicked)
            self.layout().addWidget(sidebar)
            self.sidebar = sidebar

        with QContext(QTabWidget(self)) as tab:
            tab.setObjectName("MainTabWidget")
            tab.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            self.layout().addWidget(tab)
            self.tab = tab

            with QContext(ConsoleWidget(logLevel="DEBUG")) as console:
                console.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
                self.tab.addTab(console, self.tr("Process log"))
                self.console = console

            with QContext(ImageViewWidget()) as view:
                view.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
                view.setProperty("index", "1")
                view.setProperty("filename", "results.png")
                self.tab.addTab(view, self.tr("Results"))
                self.tab.setTabVisible(1, False)
                self.results = view

            with QContext(ImageViewWidget()) as view:
                view.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
                view.setProperty("index", "2")
                view.setProperty("filename", "confusion_matrix.png")
                self.tab.addTab(view, self.tr("Matrix"))
                self.tab.setTabVisible(2, False)
                self.matrix = view

            with QContext(ImageViewWidget()) as view:
                view.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
                view.setProperty("index", "3")
                view.setProperty("filename", "labels.jpg")
                self.tab.addTab(view, self.tr("Labels"))
                self.tab.setTabVisible(3, False)
                self.labels = view

            with QContext(ImageViewWidget()) as view:
                view.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
                view.setProperty("index", "4")
                view.setProperty("filename", "labels_correlogram.jpg")
                self.tab.addTab(view, self.tr("Correlogram"))
                self.tab.setTabVisible(4, False)
                self.correlogram = view

        if not self.isRunning():
            self.initConsole()
            self.updateData()

        geometry = settings.value("trainerGeometry", group="Internal")
        if geometry:
            self.restoreGeometry(geometry)
        else:
            self.resize(1600, 932)

    def initConsole(self):
        runs_train_dir = settings.value("runs_train_dir", "runs/train")
        train_log = settings.value("train_log", "train.log")

        file = Path(runs_train_dir, self.model.metadata.name, train_log)
        if file.exists():
            with open(file, "r", encoding="utf-8", errors="ignore") as f:
                self.console.setText(f.read())

    def initLogger(self):
        runs_train_dir = settings.value("runs_train_dir", "runs/train")
        train_log = settings.value("train_log", "train.log")
        log_level = os.environ.get("LOG_LEVEL", settings.value("log_level", "INFO")).upper()

        filename = Path(runs_train_dir, self.model.metadata.name, train_log).as_posix()

        # 既にログファイルが設定されている場合は何もしない
        if self.logger:
            if self.logger.name == filename:
                return
            else:
                self.closeLogger()

        self.logger = getLogger(
            filename=filename,
            level=log_level,
        )
        self.console.attachLogger(self.logger)

    def __del__(self):
        # スレッドが終了していない場合は終了させる
        if self.thread is not None:
            self.terminateThread()
            self.thread.deleteLater()

        self.closeLogger()

    def closeLogger(self):
        if self.logger:
            closeLogger(self.logger)
            self.logger

    def showEvent(self, evant):
        self.updateData()
        super().showEvent(evant)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        settings.setValue("trainerGeometry", self.saveGeometry(), group="Internal")

    def closeEvent(self, event):
        # モデルフォルダが存在しない場合はそのまま閉じる
        if not self.model.runs_dir:
            return super().closeEvent(event)

        # モデルフォルダが存在する場合またはスレッドが実行中の場合は非表示にするだけ
        if abspath(self.model.runs_dir).exists() or self.thread is not None:
            event.ignore()
            self.hide()
        else:
            super().closeEvent(event)

    def isThreadRunning(self):
        if self.thread is not None:
            return self.thread.isRunning()

        return False

    def terminateThread(self):
        if self.thread is None:
            return

        self.logger.info("Terminate thread.")

        self.terminating = True
        try:
            self.thread.interrupt()
            self.thread.terminate()
        except Exception:
            pass

    def terminate(self):
        self.terminateThread()

        event = QCloseEvent()
        event.ignore()
        super().closeEvent(event)

    @Slot()
    def onTrainClicked(self):
        self.initLogger()

        if self.thread is not None:
            self.logger.error("Training, test or detection process is currently running")
            return

        if not self.checkParamsetChanged():
            return

        self.startTrain()

    @Slot()
    def onThreadAbort(self):
        self.logger.error("Aborted.")

    @Slot()
    def onTrainStarted(self):
        self.logger.info("Training thread started.")

    @Slot()
    def onTrainSuccess(self):
        self.logger.info("Training completed.")

        self.model.metadata.timestamp = datetime.now().isoformat()
        self.model.save(self.model.runs_dir)
        self.updateData()
        self.trainCompleted.emit()

    @Slot()
    def onTrainFinished(self):
        self.logger.info("Training thread finished.")

        if self.thread is not None:
            self.thread.deleteLater()
            self.thread = None

        if not self.terminating:
            self.startTest()

    @Slot()
    def onTestClicked(self):
        self.initLogger()

        if self.thread is not None:
            self.logger.error("Training, test or detection process is currently running")
            return

        if not self.checkParamsetChanged():
            return

        self.startTest()

    @Slot()
    def onTestStarted(self):
        self.logger.info("Test thread started.")

    @Slot()
    def onTestSuccess(self):
        self.logger.info("Test completed.")

        self.model.save(self.model.runs_dir)
        self.updateData()
        self.testCompleted.emit()

    @Slot()
    def onTestFinished(self):
        self.logger.info("Test thread finished.")

        if self.thread is not None:
            self.thread.deleteLater()
            self.thread = None

    @Slot()
    def onDetectClicked(self):
        self.initLogger()

        if self.thread is not None:
            self.logger.error("Training, test or detection process is currently running")
            return

        if not self.checkParamsetChanged():
            return

        if self.detectDialog is None:
            self.detectDialog = SampleDetectDialog(self.model, parent=self)
            self.detectDialog.accepted.connect(self.onDetectAccepted)

        self.detectDialog.show()

    @Slot()
    def onDetectAccepted(self):
        self.startSampleDetect()

    @Slot()
    def onDetectStarted(self):
        self.logger.info("Detection thread started.")

    @Slot()
    def onDetectSuccess(self):
        self.logger.info("Sample detection completed.")

        self.updateData()
        self.detectCompleted.emit()

    @Slot()
    def onDetectFinished(self):
        self.logger.info("Detection thread finished.")

        if self.thread is not None:
            self.thread.deleteLater()
            self.thread = None

    @Slot()
    def onStopClicked(self):
        self.terminateThread()

    @Slot()
    def onFormatClicked(self):
        self.initLogger()
        if self.thread is not None:
            self.logger.error("Training, test or detection process is currently running")
            return

        self.startFormat()

    @Slot()
    def onFormatStarted(self):
        self.logger.info("Format thread started.")

    @Slot()
    def onFormatSuccess(self):
        self.logger.info("Format completed.")

        self.model.save(self.model.runs_dir)
        self.updateData()
        self.formatCompleted.emit()

    @Slot()
    def onFormatFinished(self):
        self.logger.info("Format thread finished.")

        if self.thread is not None:
            self.thread.deleteLater()
            self.thread = None

    @Slot(str)
    def captureMetrics(self, line: str):
        parts = line.strip().split()
        if len(parts) == 7 and parts[0] == "all":
            precision, recall, mAP50, mAP = map(float, parts[3:])
            self.logger.debug(
                f"Precision: {precision}, Recall: {recall}, mAP@50: {mAP50}, mAP@50:95: {mAP}"
            )
            self.model.metrics.precision = float(precision)
            self.model.metrics.recall = float(recall)
            self.model.metrics.mAP50 = float(mAP50)
            self.model.metrics.mAP = float(mAP)
            self.model.metrics.timestamp = datetime.now().isoformat()

    def checkParamsetChanged(self) -> bool:
        # argmentsのdata_yaml, hyp_yamlを読み込む
        paramset = Paramset()
        paramset.load_data_yaml(self.model.arguments.data_yaml)
        paramset.load_hyp_yaml(self.model.arguments.hyp_yaml)

        # modelのparamsetと比較する
        if not paramset.equals(self.model.paramset):
            msg = self.tr(
                "The parameter set shown on the screen differs from the contents of the specified YAML files. "
                "To apply the parameter set changes, you need to save them to the parameter files. \n"
                "Do you want to continue training with the current settings?"
            )

            dialog = MessageDialog(self.tr("Parameter set changed"), parent=self.window())
            dialog.setText(msg)
            dialog.setAcceptLabel(self.tr("OK"))

            return bool(dialog.exec())

        return True

    def startTrain(self):
        yolov9_dir = settings.value("yolov9_dir")
        runs_train_dir = settings.value("runs_train_dir", "runs/train")

        with settings.group("Training") as group:
            train_py = group.value("train_py", "train_dual.py")
            batch_size = group.value("train_batch_size", 8)
            device = group.value("device", 0)
            workers = group.value("workers", 8)

        assert yolov9_dir
        assert runs_train_dir
        assert train_py

        if not Path(yolov9_dir).exists():
            self.logger.error(f"Yolov9 folder not found: {yolov9_dir}")
            return

        if not abspath(train_py).exists():
            self.logger.error(f"Training script not found: {train_py}")
            return

        rundir = Path(abspath(runs_train_dir), self.model.metadata.name)
        if rundir.exists():
            mgs_tmpl = self.tr("Model folder `{0}` already exists. Overwrite it?")

            dialog = MessageDialog(self.tr("Overwrite model folder"), parent=self.window())
            dialog.setText(mgs_tmpl.format(relpath(rundir, posix=True)))
            dialog.setAcceptLabel(self.tr("Overwrite"))

            if not dialog.exec():
                return

        # 上書きキャンセルの場合はreturnしているので、学習実行時は常に上書きOK
        exist_ok = True

        def search_weights(cfg):
            # cfg名からweightsファイルを検索する
            # yolov9-?.yaml -> yolov9-?.pt or yolov9?.pt

            pt_names = [
                Path(cfg).with_suffix(".pt").name,
                Path(cfg.replace("-", "")).with_suffix(".pt").name,
            ]
            pretrained_dir = abspath(settings.value("pretrained_dir", "pretrained"))
            for pt in pt_names:
                path = Path(pretrained_dir, pt)
                if path.exists():
                    return argpath(path)

            return None

        # yolov9内で検索されるためファイル名のみを指定する
        cfg = Path(self.model.arguments.cfg).name
        weights = search_weights(cfg)
        if weights is None:
            self.logger.error(f"Pretrained weights not found for {cfg}")
            return

        data_yaml = argpath(self.model.arguments.data_yaml)
        hyp_yaml = argpath(self.model.arguments.hyp_yaml)
        img_size = int(self.model.arguments.img_size)
        epochs = int(self.model.arguments.epochs)

        args = {
            "--name": str(self.model.metadata.name),
            "--cfg": cfg,
            "--weights": weights,
            "--data": data_yaml,
            "--hyp": hyp_yaml,
            "--img-size": img_size,
            "--epochs": epochs,
            "--batch-size": int(batch_size),
            "--device": str(device),
            "--workers": int(workers),
            "--exist-ok": exist_ok,
        }

        self.thread = TrainingThread(exec=train_py, **args)

        self.thread.debug.connect(self.logger.debug)
        self.thread.info.connect(self.logger.info)
        self.thread.error.connect(self.logger.error)

        self.thread.started.connect(self.onTrainStarted)
        self.thread.finished.connect(self.onTrainFinished)
        self.thread.success.connect(self.onTrainSuccess)
        self.thread.abort.connect(self.onThreadAbort)
        self.thread.waiting.connect(QApplication.processEvents)

        QDir.setCurrent(yolov9_dir)

        if not rundir.exists():
            rundir.mkdir(parents=True)

        runs_dir = relpath(rundir, posix=True)
        if runs_dir != self.model.runs_dir:
            prev_runs_dir = self.model.runs_dir
            self.model.runs_dir = runs_dir
            self.runsdirChanged.emit(runs_dir, prev_runs_dir)

        self.model.save(self.model.runs_dir)

        # デフォルト値に保存
        with settings.group("Defaults") as group:
            group.setValue("img_size", img_size)
            group.setValue("epochs", epochs)

        self.trainStart.emit()
        self.thread.startWorker()

    def startTest(self):
        yolov9_dir = settings.value("yolov9_dir")

        with settings.group("Training") as group:
            test_py = group.value("test_py", "val.py")
            batch_size = group.value("test_batch_size", 16)
            device = group.value("device", 0)
            workers = group.value("workers", 8)

        assert yolov9_dir
        assert test_py

        if not Path(yolov9_dir).exists():
            self.logger.error(f"Yolov9 folder not found: {yolov9_dir}")
            return

        if not abspath(test_py).exists():
            self.logger.error(f"Test script not found: {test_py}")
            return

        # best.ptのパスを取得
        runs_dir = abspath(self.model.runs_dir)
        best_pt = next(runs_dir.glob("**/best.pt"), None)
        if not best_pt:
            self.logger.error("Pretrained weights not found")
            return
        else:
            weights = argpath(best_pt)

        data_yaml = argpath(self.model.arguments.data_yaml)

        args = {
            "--name": str(self.model.metadata.name),
            "--weights": weights,
            "--data": data_yaml,
            "--img-size": int(self.model.arguments.img_size),
            "--batch-size": int(batch_size),
            "--device": int(device),
            "--workers": int(workers),
        }

        self.thread = TestThread(exec=test_py, **args)

        self.thread.debug.connect(self.logger.debug)
        self.thread.info.connect(self.logger.info)
        self.thread.error.connect(self.logger.error)

        self.thread.info.connect(self.captureMetrics)

        self.thread.finished.connect(self.onTestFinished)
        self.thread.started.connect(self.onTestStarted)
        self.thread.success.connect(self.onTestSuccess)
        self.thread.abort.connect(self.onThreadAbort)
        self.thread.waiting.connect(QApplication.processEvents)

        QDir.setCurrent(yolov9_dir)

        self.testStart.emit()
        self.thread.startWorker()

    def startSampleDetect(self):
        yolov9_dir = settings.value("yolov9_dir")
        runs_detect_dir = settings.value("runs_detect_dir")

        with settings.group("Training") as group:
            sample_detect_py = group.value("sample_detect_py", "detect.py")
            device = group.value("device", 0)

        assert yolov9_dir
        assert runs_detect_dir
        assert sample_detect_py

        if not Path(yolov9_dir).exists():
            self.logger.error(f"Yolov9 folder not found: {yolov9_dir}")
            return

        if not abspath(sample_detect_py).exists():
            self.logger.error(f"Detection script not found: {sample_detect_py}")
            return

        # best.ptのパスを取得
        runs_dir = abspath(self.model.runs_dir)
        best_pt = next(runs_dir.glob("**/best.pt"), None)
        if not best_pt:
            self.logger.error("Pretrained weights not found")
            return
        else:
            weights = argpath(best_pt)

        data_yaml = argpath(self.model.arguments.data_yaml)
        project = argpath(Path(runs_detect_dir, self.model.metadata.name))

        source = self.detectDialog.value("source")
        name = self.detectDialog.value("name")
        img_size = int(self.detectDialog.value("img_size"))
        conf_thres = float(self.detectDialog.value("conf_thres"))
        iou_thres = float(self.detectDialog.value("iou_thres"))
        save_img = self.detectDialog.value("save_img")
        save_txt = self.detectDialog.value("save_txt")
        save_conf = self.detectDialog.value("save_conf")
        save_crop = self.detectDialog.value("save_crop")
        open_result = self.detectDialog.value("open_result")

        args = {
            "--project": project,
            "--name": name,
            "--weights": weights,
            "--source": source,
            "--data": data_yaml,
            "--img-size": img_size,
            "--conf-thres": conf_thres,
            "--iou-thres": iou_thres,
            "--nosave": not save_img,
            "--save-txt": save_txt,
            "--save-conf": save_conf,
            "--save-crop": save_crop,
            "--device": int(device),
            "--exist-ok": True,
        }

        self.thread = DetectThread(exec=sample_detect_py, **args)

        self.thread.debug.connect(self.logger.debug)
        self.thread.info.connect(self.logger.info)
        self.thread.error.connect(self.logger.error)

        self.thread.info.connect(self.captureMetrics)

        self.thread.finished.connect(self.onDetectFinished)
        self.thread.started.connect(self.onDetectStarted)
        self.thread.success.connect(self.onDetectSuccess)

        self.thread.abort.connect(self.onThreadAbort)
        self.thread.waiting.connect(QApplication.processEvents)

        if open_result:
            result_dir = abspath(Path(project, name))
            self.thread.success.connect(partial(os.startfile, result_dir))

        QDir.setCurrent(yolov9_dir)

        self.detectStart.emit()
        self.thread.startWorker()

    def startFormat(self):
        yolov9_dir = settings.value("yolov9_dir")

        with settings.group("Training") as group:
            format_py = group.value("format_py", "format_input.py")

        if not Path(yolov9_dir).exists():
            self.logger.error(f"Yolov9 folder not found: {yolov9_dir}")
            return

        if not abspath(format_py).exists():
            self.logger.error(f"Format script not found: {format_py}")
            return

        args = {
            "--path_to_dataset": relpath(self.model.paramset.dataset_dir, posix=True),
            "--name0": self.model.paramset.classes.get(0, "") or None,
            "--name1": self.model.paramset.classes.get(1, "") or None,
            "--name2": self.model.paramset.classes.get(2, "") or None,
            "--name3": self.model.paramset.classes.get(3, "") or None,
            "--name4": self.model.paramset.classes.get(4, "") or None,
            "--name5": self.model.paramset.classes.get(5, "") or None,
            "--name6": self.model.paramset.classes.get(6, "") or None,
            "--name7": self.model.paramset.classes.get(7, "") or None,
            "--name8": self.model.paramset.classes.get(8, "") or None,
            "--name9": self.model.paramset.classes.get(9, "") or None,
            "--lr0": str(self.model.paramset.lr0),
            "--flipud": str(self.model.paramset.flipud),
            "--fliplr": str(self.model.paramset.fliplr),
        }

        self.thread = FormatThread(exec=format_py, **args)

        self.thread.debug.connect(self.logger.debug)
        self.thread.info.connect(self.logger.info)
        self.thread.error.connect(self.logger.error)

        self.thread.finished.connect(self.onFormatFinished)
        self.thread.started.connect(self.onFormatStarted)
        self.thread.success.connect(self.onFormatSuccess)
        self.thread.abort.connect(self.onThreadAbort)
        self.thread.waiting.connect(QApplication.processEvents)

        QDir.setCurrent(yolov9_dir)
        self.thread.startWorker()

    def isRunning(self):
        if self.thread is not None:
            return self.thread.isRunning()

        return False

    def updateData(self):
        self.sidebar.updateData(self.model)

        if not abspath(self.model.runs_dir).exists():
            return

        for index in range(1, self.tab.count() + 1):
            self.updateImage(self.tab.widget(index))

    def updateImage(self, widget: ImageViewWidget):
        """タブ内のQLabelに画像を表示する

        Args:
            filename (Path): runs_dirからの相対パス
            label (QLabel): 表示先のQLabel
        """
        if not isinstance(widget, ImageViewWidget):
            return

        index = int(widget.property("index"))
        filename = widget.property("filename")

        path = Path(self.model.runs_dir, filename)
        if path.exists():
            pixmap = QPixmap(os.fspath(path))
            widget.setPixmap(pixmap)
            self.tab.setTabVisible(index, True)
        else:
            self.tab.setTabVisible(index, False)
