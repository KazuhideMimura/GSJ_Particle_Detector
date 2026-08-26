from PySide6.QtCore import Qt, Slot
from PySide6.QtGui import QDoubleValidator, QIntValidator
from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from ..helper import settings
from ..helper.filesystem import PathnameValidator
from ..helper.qcontext import QContext
from ..widget.filesystem import FolderInputWidget
from .data import ModelInfo


class SampleDetectDialog(QDialog):
    model: ModelInfo = None

    name: QLineEdit = None
    source: FolderInputWidget = None
    conf_thres: QLineEdit = None
    iou_thres: QLineEdit = None
    img_size: QLineEdit = None
    save_img: QCheckBox = None
    save_txt: QCheckBox = None
    save_conf: QCheckBox = None
    save_crop: QCheckBox = None

    open_result: QCheckBox = None

    start_button: QPushButton = None
    cancel_button: QPushButton = None

    def __init__(self, model, parent=None):
        super().__init__(parent)

        self.model = model

        self.setWindowTitle(self.tr("Sample detection"))
        self.setFixedWidth(560)
        self.setWindowFlag(Qt.WindowType.MSWindowsFixedSizeDialogHint)

        with QContext(QVBoxLayout()) as layout:
            layout.setContentsMargins(8, 8, 8, 8)
            self.setLayout(layout)

        with QContext(QGroupBox(self.tr("Parameters"), self)) as box:
            self.layout().addWidget(box)

            with QContext(QFormLayout()) as layout:
                box.setLayout(layout)

                layout.setContentsMargins(0, 0, 0, 0)
                layout.setSpacing(2)

            with QContext(QLabel(), QLineEdit()) as (label, input):
                label.setText(self.tr("Name"))
                label.setProperty("style", "property")
                input.setObjectName("name")
                input.setValidator(PathnameValidator())
                input.textChanged.connect(self.validate)
                box.layout().addRow(label, input)
                self.name = input

            with QContext(QLabel(), FolderInputWidget()) as (label, input):
                label.setText(self.tr("Source"))
                label.setProperty("style", "property")
                input.setObjectName("source")
                input.setExistRequired(True)
                input.textChanged.connect(self.validate)
                box.layout().addRow(label, input)
                self.source = input

            with QContext(QLabel(), QLineEdit()) as (label, input):
                label.setText(self.tr("Image size"))
                label.setProperty("style", "property")
                input.setValidator(QIntValidator())
                input.setObjectName("img_size")
                input.setFixedWidth(100)
                input.textChanged.connect(self.validate)
                box.layout().addRow(label, input)
                self.img_size = input

            with QContext(QLabel(), QLineEdit()) as (label, input):
                label.setText(self.tr("Confidence threshold"))
                label.setProperty("style", "property")
                input.setValidator(QDoubleValidator(0.0, 1.0, 2))
                input.setObjectName("conf_thres")
                input.setFixedWidth(100)
                input.textChanged.connect(self.validate)
                box.layout().addRow(label, input)
                self.conf_thres = input

            with QContext(QLabel(), QLineEdit()) as (label, input):
                label.setText(self.tr("NMS IoU threshold"))
                label.setProperty("style", "property")
                input.setValidator(QDoubleValidator(0.0, 1.0, 2))
                input.setObjectName("iou_thres")
                input.setFixedWidth(100)
                input.textChanged.connect(self.validate)
                box.layout().addRow(label, input)
                self.iou_thres = input

        with QContext(QGroupBox(self.tr("Save settings"), self)) as box:
            self.layout().addWidget(box)

            with QContext(QFormLayout()) as layout:
                box.setLayout(layout)

                layout.setContentsMargins(0, 0, 0, 0)
                layout.setSpacing(2)
            with QContext(QLabel(), QCheckBox()) as (label, check):
                label.setText(self.tr("Save images"))
                label.setProperty("style", "property")
                input.setObjectName("save_img")
                box.layout().addRow(label, check)
                self.save_img = check

            with QContext(QLabel(), QCheckBox()) as (label, check):
                label.setText(self.tr("Save results"))
                label.setProperty("style", "property")
                input.setObjectName("save_txt")
                box.layout().addRow(label, check)
                self.save_txt = check

            with QContext(QLabel(), QCheckBox()) as (label, check):
                label.setText(self.tr("Save confidences"))
                label.setProperty("style", "property")
                input.setObjectName("save_conf")
                box.layout().addRow(label, check)
                self.save_conf = check

            with QContext(QLabel(), QCheckBox()) as (label, check):
                label.setText(self.tr("Save cropped boxes"))
                label.setProperty("style", "property")
                input.setObjectName("save_crop")
                box.layout().addRow(label, check)
                self.save_crop = check

        with QContext(QWidget(), QHBoxLayout()) as (widget, layout):
            layout.setContentsMargins(3, 3, 3, 0)
            layout.setSpacing(2)
            widget.setLayout(layout)
            self.layout().addWidget(widget)

            with QContext(QCheckBox("")) as check:
                check.setText(self.tr("Open result folder after detection"))
                check.setObjectName("open_result")
                layout.addWidget(check)
                self.open_result = check

            layout.addStretch()

            with QContext(QPushButton(self.tr("OK"))) as button:
                button.setProperty("style", "primary")
                button.clicked.connect(self.accept)
                layout.addWidget(button)
                self.start_button = button

            with QContext(QPushButton(self.tr("Cancel"))) as button:
                button.setProperty("style", "secondary")
                button.clicked.connect(self.reject)
                layout.addWidget(button)
                self.cancel_button = button

        self.loadSettings()
        self.adjustSize()
        self.accepted.connect(self.onAccepted)

    def closeEvent(self, event):
        # 再利用するので非表示にするだけ
        event.ignore()
        self.hide()

    @Slot(str)
    def validate(self, text):
        inputs = [self.name, self.source, self.img_size, self.conf_thres, self.iou_thres]
        valid = all(x.hasAcceptableInput() for x in inputs)
        self.start_button.setEnabled(valid)

    @Slot()
    def onAccepted(self):
        self.saveSettings()

    def value(self, key: str, default=None):
        match key:
            case "name":
                return self.name.text() or default
            case "source":
                return self.source.text() or default
            case "conf_thres":
                return settings.safeFloat(self.conf_thres.text(), default)
            case "iou_thres":
                return settings.safeFloat(self.iou_thres.text(), default)
            case "img_size":
                return settings.safeInt(self.img_size.text(), default)
            case "save_img":
                return self.save_img.isChecked()
            case "save_txt":
                return self.save_txt.isChecked()
            case "save_conf":
                return self.save_conf.isChecked()
            case "save_crop":
                return self.save_crop.isChecked()
            case "open_result":
                return self.open_result.isChecked()
            case _:
                assert False, f"Invalid key: {key}"

    def loadSettings(self):
        with settings.group("SampleDetection") as group:
            self.name.setText(group.value("name", "exp"))
            self.source.setText(group.value("source", ""))
            self.conf_thres.setText(group.value("conf_thres", "0.25"))
            self.iou_thres.setText(group.value("iou_thres", "0.45"))
            self.img_size.setText(group.value("img_size", "640"))
            self.save_img.setChecked(group.value("save_img", True, type=bool))
            self.save_txt.setChecked(group.value("save_txt", True, type=bool))
            self.save_conf.setChecked(group.value("save_conf", True, type=bool))
            self.save_crop.setChecked(group.value("save_crop", True, type=bool))
            self.open_result.setChecked(group.value("open_result", True, type=bool))

    def saveSettings(self):
        # 初期値に同じデフォルト値を表示する項目は保存しない
        with settings.group("SampleDetection", sync=True) as group:
            # group.setValue("name", self.name.text())
            group.setValue("source", self.source.text())
            # group.setValue("conf_thres", self.conf_thres.text())
            # group.setValue("iou_thres", self.iou_thres.text())
            # group.setValue("img_size", self.img_size.text())
            # group.setValue("save_img", self.save_img.isChecked())
            # group.setValue("save_txt", self.save_txt.isChecked())
            # group.setValue("save_conf", self.save_conf.isChecked())
            # group.setValue("save_crop", self.save_crop.isChecked())
            group.setValue("open_result", self.open_result.isChecked())
