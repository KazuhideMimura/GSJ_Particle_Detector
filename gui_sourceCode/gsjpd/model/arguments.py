from pathlib import Path

from PySide6.QtCore import Signal, Slot
from PySide6.QtGui import QIntValidator
from PySide6.QtWidgets import (
    QFormLayout,
    QGroupBox,
    QLabel,
    QLineEdit,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from ..helper import settings
from ..helper.filesystem import abspath, relpath
from ..helper.qcontext import QContext
from ..widget.filesystem import FileInputWidget, YamlComboBox
from ..widget.lineedit import RequiredLineEdit
from .data import Arguments


class ArgumentsWidget(QWidget):
    data_yaml: FileInputWidget = None
    hyp_yaml: FileInputWidget = None
    img_size: QLineEdit = None
    cfg: YamlComboBox = None
    epochs: QLineEdit = None

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Fixed)

        with QContext(QVBoxLayout()) as layout:
            layout.setSizeConstraint(QVBoxLayout.SetMinimumSize)
            layout.setContentsMargins(3, 3, 3, 3)
            layout.setSpacing(2)
            self.setLayout(layout)

        with QContext(QGroupBox(self.tr("Train / Test"), self)) as box:
            self.layout().addWidget(box)

            with QContext(QFormLayout()) as layout:
                layout.setContentsMargins(3, 3, 3, 3)
                layout.setSpacing(1)
                box.setLayout(layout)

            with QContext(QLabel(), FileInputWidget()) as (label, file):
                label.setText(self.tr("data yaml"))
                label.setProperty("style", "property")
                file.setObjectName("data_yaml")
                file.setNameFilter("YAML files (*.yaml);;All files (*.*)")
                file.setExistRequired(True)
                box.layout().addRow(label, file)
                self.data_yaml = file

            # --hyp
            with QContext(QLabel(), FileInputWidget()) as (label, file):
                label.setText(self.tr("hyperparam yaml"))
                label.setProperty("style", "property")
                file.setObjectName("hyp_yaml")
                file.setNameFilter("YAML files (*.yaml);;All files (*.*)")
                file.setExistRequired(True)
                box.layout().addRow(label, file)
                self.hyp_yaml = file

            # --cfg and --weights
            with QContext(QLabel(), YamlComboBox()) as (label, combo):
                label.setText(self.tr("model size"))
                label.setProperty("style", "property")
                combo.setObjectName("cfg")
                box.layout().addRow(label, combo)
                self.cfg = combo

            # --img-size
            with QContext(QLabel(), RequiredLineEdit()) as (label, edit):
                label.setText(self.tr("img size"))
                label.setProperty("style", "property")
                edit.setObjectName("img_size")
                box.layout().addRow(label, edit)
                self.img_size = edit

            # --epochs
            with QContext(QLabel(), RequiredLineEdit()) as (label, edit):
                label.setText(self.tr("epoch"))
                label.setProperty("style", "property")
                edit.setObjectName("epochs")
                box.layout().addRow(label, edit)
                self.epochs = edit

    def init(self, empty=None):
        # init cfg combobox
        yolov9_dir = settings.value("yolov9_dir")
        cfg_dir = Path(yolov9_dir, "models", "detect")
        cfg_pattern = "yolov9-?.yaml"
        self.cfg.init(cfg_dir, cfg_pattern, empty_item=empty)

    def setValues(self, args: Arguments | None):
        if not args:
            self.data_yaml.clear()
            self.hyp_yaml.clear()
            self.img_size.clear()
            self.epochs.clear()
            self.cfg.setCurrentIndex(-1)
            return

        self.data_yaml.setPath(args.data_yaml)
        self.hyp_yaml.setPath(args.hyp_yaml)
        self.img_size.setText(str(args.img_size))
        self.cfg.setCurrentData(args.cfg)
        self.epochs.setText(str(args.epochs))


class ArgumentsView(ArgumentsWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.data_yaml.setEnabled(False)
        self.hyp_yaml.setEnabled(False)
        self.cfg.setEnabled(False)
        self.img_size.setEnabled(False)
        self.epochs.setEnabled(False)

        self.init(empty="")


class ArgumentsForm(ArgumentsWidget):
    inputChanged = Signal(str, object)
    fileSelected = Signal(str, object)

    def __init__(self, parent=None):
        super().__init__(parent)

        yolov9_dir = settings.value("yolov9_dir")
        data_yaml_dir = relpath(settings.value("data_yaml_dir", yolov9_dir))
        hyp_yaml_dir = relpath(settings.value("hyp_yaml_dir", yolov9_dir))

        self.data_yaml.setPlaceholderText("path to dataset.yaml")
        self.data_yaml.setInitialDir(data_yaml_dir)
        self.data_yaml.setStartDir(yolov9_dir)
        self.hyp_yaml.setPlaceholderText("hyperparameters path")
        self.hyp_yaml.setInitialDir(hyp_yaml_dir)
        self.hyp_yaml.setStartDir(yolov9_dir)
        self.cfg.setPlaceholderText("model size")
        self.img_size.setPlaceholderText("train, val image size (pixels)")
        self.img_size.setValidator(QIntValidator(1, 8192))
        self.epochs.setPlaceholderText("total training epochs")
        self.epochs.setValidator(QIntValidator(1, 99999))

        self.data_yaml.textChanged.connect(self.onTextChanged)
        self.hyp_yaml.textChanged.connect(self.onTextChanged)
        self.cfg.itemSelected.connect(self.onItemSelected)
        self.img_size.textChanged.connect(self.onTextChanged)
        self.epochs.textChanged.connect(self.onTextChanged)

        self.data_yaml.selected.connect(self.onFileSelected)
        self.hyp_yaml.selected.connect(self.onFileSelected)

        self.init()

    @Slot()
    def onTextChanged(self):
        sender = self.sender()
        if sender is None:
            return

        if isinstance(sender.validator(), QIntValidator):
            if sender.hasAcceptableInput():
                self.inputChanged.emit(sender.objectName(), int(sender.text()))
        else:
            self.inputChanged.emit(sender.objectName(), sender.text())

    @Slot(str)
    def onFileSelected(self, path: str):
        sender = self.sender()
        if sender is None:
            return

        self.fileSelected.emit(self.sender().objectName(), relpath(path, posix=True))

    @Slot(str)
    def onItemSelected(self, text: str):
        sender = self.sender()
        if sender is None:
            return

        self.inputChanged.emit(self.sender().objectName(), relpath(text, posix=True))

    def hasAcceptableInput(self):
        return (
            abspath(self.data_yaml.path()).exists()
            and abspath(self.hyp_yaml.path()).exists()
            and self.cfg.hasAcceptableInput()
            and self.img_size.hasAcceptableInput()
            and self.epochs.hasAcceptableInput()
        )
