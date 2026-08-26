from pathlib import Path

from PySide6.QtCore import Signal, Slot
from PySide6.QtWidgets import (
    QHBoxLayout,
    QListWidgetItem,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from ..helper.filesystem import PathnameValidator, abspath
from ..helper.qcontext import QContext
from ..widget.dialog import EditDialog, ErrorDialog
from .arguments import ArgumentsView
from .data import ModelInfo
from .metadata import MetadataView
from .metrics import MetricsView
from .model_list import ModelListHeaderRow, ModelListWidget
from .paramset import ParamsetView
from .trainer import TrainerDialog


class ModelControlWidget(QWidget):
    createModel = Signal()
    renameModel = Signal()
    deleteModel = Signal()

    create_button: QPushButton = None
    rename_button: QPushButton = None
    delete_button: QPushButton = None

    metadata: MetadataView = None
    paramset: ParamsetView = None
    arguments: ArgumentsView = None

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setMinimumWidth(400)
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)

        with QContext(QVBoxLayout()) as layout:
            self.setLayout(layout)

            layout.setContentsMargins(3, 3, 3, 3)
            layout.setSpacing(3)

        with QContext(QPushButton(self.tr("Create new model"))) as button:
            self.create_button = button
            self.layout().addWidget(button)

            button.setProperty("style", "primary")
            button.setFlat(True)
            button.clicked.connect(self.createModel)

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

                with QContext(MetadataView()) as metadata:
                    widget.layout().addWidget(metadata)
                    self.metadata = metadata

                with QContext(ParamsetView()) as paramset:
                    widget.layout().addWidget(paramset)
                    self.paramset = paramset

                with QContext(ArgumentsView()) as args:
                    widget.layout().addWidget(args)
                    self.arguments = args

                with QContext(MetricsView()) as metrics:
                    widget.layout().addWidget(metrics)
                    self.metrics = metrics

        with QContext(QWidget()) as toolbar:
            self.layout().addWidget(toolbar)

            toolbar.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            toolbar.setLayout(QHBoxLayout())
            toolbar.layout().setContentsMargins(0, 0, 0, 0)
            toolbar.layout().setSpacing(3)

            toolbar.layout().addStretch()

            with QContext(QPushButton(self.tr("Rename"))) as button:
                self.rename_button = button
                toolbar.layout().addWidget(button)

                button.setProperty("style", "danger")
                button.setFlat(True)
                button.clicked.connect(self.renameModel)

            with QContext(QPushButton(self.tr("Delete"))) as button:
                self.delete_button = button
                toolbar.layout().addWidget(button)

                button.setProperty("style", "danger")
                button.setFlat(True)
                button.clicked.connect(self.deleteModel)

        self.updateData(None)

    def updateData(self, model: ModelInfo | None):
        if not model:
            self.metadata.setValues(None)
            self.paramset.setValues(None)
            self.arguments.setValues(None)
            self.metrics.setValues(None)

            self.rename_button.setEnabled(False)
            self.delete_button.setEnabled(False)
            return

        self.metadata.setValues(model.metadata)
        self.paramset.setValues(model.paramset)
        self.arguments.setValues(model.arguments)
        self.metrics.setValues(model.metrics)

        self.rename_button.setEnabled(True)
        self.delete_button.setEnabled(True)


class ModelMainWidget(QWidget):
    header: ModelListHeaderRow = None
    models: ModelListWidget = None
    control: ModelControlWidget = None

    trainerDialogs: dict[str, TrainerDialog] = {}

    def __init__(self, parent=None):
        super().__init__(parent)

        self.trainerDialogs = {}

        with QContext(QHBoxLayout()) as layout:
            layout.setContentsMargins(0, 0, 0, 0)
            layout.setSpacing(0)
            self.setLayout(layout)

        with QContext(QWidget()) as content:
            self.layout().addWidget(content)

            content.setLayout(QVBoxLayout())
            content.layout().setContentsMargins(0, 0, 0, 0)
            content.layout().setSpacing(0)

            with QContext(ModelListHeaderRow()) as header:
                self.header = header
                content.layout().addWidget(header)

            with QContext(ModelListWidget()) as list:
                self.models = list
                content.layout().addWidget(list)

                list.itemSelectionChanged.connect(self.onItemSelectionChanged)
                list.itemDoubleClicked.connect(self.onItemDoubleClicked)

        with QContext(QWidget()) as sidebar:
            self.layout().addWidget(sidebar)

            sidebar.setLayout(QVBoxLayout())
            sidebar.layout().setContentsMargins(0, 0, 0, 0)
            sidebar.layout().setSpacing(0)

            with QContext(ModelControlWidget()) as control:
                self.control = control
                self.layout().addWidget(control)
                control.createModel.connect(self.onCreateModel)
                control.renameModel.connect(self.onRenameModel)
                control.deleteModel.connect(self.onDeleteModel)

            sidebar.layout().addStretch()

        self.header.clicked.connect(self.models.sort)

    @Slot()
    def onCreateModel(self):
        model = ModelInfo(runs_dir="")

        # デフォルトのdata_yamlが存在する場合は読み込む
        if abspath(model.arguments.data_yaml).exists():
            model.paramset.load_data_yaml(model.arguments.data_yaml)

        # デフォルトのhyp_yamlが存在する場合は読み込む
        if abspath(model.arguments.hyp_yaml).exists():
            model.paramset.load_hyp_yaml(model.arguments.hyp_yaml)

        self.openTrainerDialog(model)

    @Slot()
    def onRenameModel(self):
        model = self.getSelectedModel()

        dialog = self.findDialog(model.runs_dir)
        if dialog and dialog.isThreadRunning():
            ErrorDialog.show(
                self.tr("Processing"),
                self.tr(
                    "The model has a training/test process currently running. Cannot rename while a process is running."
                ),
                parent=self.window(),
            )
            return

        runs_dir = Path(model.runs_dir)
        if runs_dir.exists():
            dialog = EditDialog(self.tr("Rename model"), parent=self.window())
            dialog.setText(self.tr("Enter new name for the model"))
            dialog.setInputText(runs_dir.name)
            dialog.setInputValidator(PathnameValidator())

            if dialog.exec():
                try:
                    prev_runs_dir = model.runs_dir
                    model.rename(dialog.inputText())
                    new_runs_dir = model.runs_dir
                    if prev_runs_dir in self.trainerDialogs:
                        self.trainerDialogs[new_runs_dir] = self.trainerDialogs[prev_runs_dir]
                        del self.trainerDialogs[prev_runs_dir]

                    self.updateData(model.runs_dir)
                except Exception as e:
                    print(e)

    @Slot()
    def onDeleteModel(self):
        model = self.getSelectedModel()

        dialog = self.findDialog(model.runs_dir)
        if dialog and dialog.isThreadRunning():
            ErrorDialog.show(
                self.tr("Processing"),
                self.tr(
                    "The model has a training/test process currently running. Cannot delete while a process is running."
                ),
                parent=self.window(),
            )
            return

        runs_dir = Path(model.runs_dir)
        if runs_dir.exists():
            dialog = EditDialog(self.tr("Delete model"), parent=self.window())
            dialog.setText(
                self.tr("The model will be deleted with its folder. Do you want to continue?")
            )
            dialog.setInputText(runs_dir.as_posix())
            dialog.setInputEnabled(False)
            dialog.setAcceptStyle("danger")

            if dialog.exec():
                try:
                    runs_dir = model.runs_dir
                    model.delete()
                    if runs_dir in self.trainerDialogs:
                        self.removeDialog(runs_dir)

                    self.updateData()
                except Exception as e:
                    print(e)

    @Slot()
    def onItemSelectionChanged(self):
        self.control.updateData(self.getSelectedModel())

    @Slot(QListWidgetItem)
    def onItemDoubleClicked(self, item: QListWidgetItem):
        model = item.model
        if not model:
            return

        self.openTrainerDialog(model)

    def getSelectedModel(self) -> ModelInfo | None:
        items = self.models.selectedItems()
        if not items:
            return None

        return items[0].model

    def openTrainerDialog(self, model: ModelInfo):
        dialog = self.findDialog(model.runs_dir)

        if dialog is None:
            dialog = TrainerDialog(model, parent=None)
            dialog.runsdirChanged.connect(self.onRunsdirChanged)
            dialog.trainStart.connect(self.updateData)
            dialog.trainCompleted.connect(self.updateData)
            dialog.testCompleted.connect(self.updateData)
            dialog.detectCompleted.connect(self.updateData)
            dialog.rejected.connect(self.onRejectedTrainerDialog)
            self.addDialog(dialog)

        dialog.show()

    def terminate(self):
        dialogs = list(self.trainerDialogs.values())

        for dialog in dialogs:
            dialog.terminate()

    def isThreadRunning(self) -> bool:
        for dialog in self.trainerDialogs.values():
            if dialog.isThreadRunning():
                return True

        return False

    def findDialog(self, runs_dir: str) -> TrainerDialog | None:
        if runs_dir is None:
            return None

        dialog = self.trainerDialogs.get(runs_dir, None)
        return dialog

    def addDialog(self, dialog: TrainerDialog):
        self.trainerDialogs[dialog.model.runs_dir] = dialog

    def removeDialog(self, runs_dir: str):
        dialog = self.findDialog(runs_dir)
        if dialog:
            dialog.terminate()

    @Slot(str, str)
    def onRunsdirChanged(self, new_runs_dir, prev_runs_dir):
        if prev_runs_dir in self.trainerDialogs:
            self.trainerDialogs[new_runs_dir] = self.trainerDialogs[prev_runs_dir]
            del self.trainerDialogs[prev_runs_dir]

        self.updateData()

    @Slot()
    def onRejectedTrainerDialog(self):
        dialog = self.sender()

        if dialog.model.runs_dir in self.trainerDialogs:
            del self.trainerDialogs[dialog.model.runs_dir]

    def updateData(self, cur_runs_dir: str = None):
        if not cur_runs_dir:
            items = self.models.selectedItems()
            if items:
                cur_runs_dir = items[0].model.runs_dir
            else:
                cur_runs_dir = None

        self.models.updateData()

        if cur_runs_dir:
            item = self.models.findItem(cur_runs_dir)
            if item:
                self.models.setCurrentItem(item)

        # trainerDialogsの同期
        for runs_dir in list(self.trainerDialogs.keys()):
            item = self.models.findItem(runs_dir)
            if not item:
                self.removeDialog(runs_dir)
