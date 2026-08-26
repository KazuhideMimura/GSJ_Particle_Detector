from PySide6.QtCore import Qt, Slot
from PySide6.QtGui import QDoubleValidator
from PySide6.QtWidgets import (
    QDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from ..helper import settings
from ..helper.qcontext import QContext
from ..widget.filesystem import FolderInputWidget


class DetectionDialog(QDialog):
    basedir: FolderInputWidget = None
    conf_thres: QLineEdit = None
    iou_thres: QLineEdit = None

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle(self.tr("Start detection"))
        self.setFixedWidth(560)
        self.setWindowFlag(Qt.WindowType.MSWindowsFixedSizeDialogHint)

        with QContext(QVBoxLayout()) as layout:
            layout.setContentsMargins(8, 8, 8, 8)
            self.setLayout(layout)

        with QContext(QWidget(), QFormLayout()) as (widget, layout):
            layout.setContentsMargins(0, 0, 0, 0)
            layout.setSpacing(2)
            widget.setLayout(layout)
            self.layout().addWidget(widget)

            with QContext(QLabel(), FolderInputWidget(parent=self)) as (label, input):
                label.setText(self.tr("Base folder"))
                label.setProperty("style", "property")
                input.setObjectName("basedir")
                layout.addRow(label, input)
                self.basedir = input

            with QContext(QLabel(), QLineEdit(parent=self)) as (label, input):
                label.setText(self.tr("Confidence threshold"))
                label.setProperty("style", "property")
                input.setValidator(QDoubleValidator(0.0, 1.0, 2))
                input.setObjectName("conf_thres")
                input.setFixedWidth(100)
                layout.addRow(label, input)
                self.conf_thres = input

            with QContext(QLabel(), QLineEdit(parent=self)) as (label, input):
                label.setText(self.tr("NMS IoU threshold"))
                label.setProperty("style", "property")
                input.setValidator(QDoubleValidator(0.0, 1.0, 2))
                input.setObjectName("iou_thres")
                input.setFixedWidth(100)
                layout.addRow(label, input)
                self.iou_thres = input

        with QContext(QWidget(), QHBoxLayout()) as (widget, layout):
            layout.setContentsMargins(0, 0, 0, 0)
            layout.setSpacing(2)
            widget.setLayout(layout)
            self.layout().addWidget(widget)

            layout.addStretch()

            with QContext(QPushButton(self.tr("Start"), parent=self)) as button:
                button.setProperty("style", "primary")
                button.clicked.connect(self.accept)
                layout.addWidget(button)
                self.start_button = button

            with QContext(QPushButton(self.tr("Cancel"), parent=self)) as button:
                button.setProperty("style", "secondary")
                button.clicked.connect(self.reject)
                layout.addWidget(button)
                self.cancel_button = button

        self.loadSettings()
        self.adjustSize()
        self.accepted.connect(self.onAccepted)

    @Slot()
    def onAccepted(self):
        self.saveSettings()

    def loadSettings(self):
        with settings.group("Detection") as group:
            self.basedir.setText(group.value("basedir", "share"))
            self.conf_thres.setText(group.value("conf_thres", "0.25"))
            self.iou_thres.setText(group.value("iou_thres", "0.1"))

    def saveSettings(self):
        with settings.group("Detection", sync=True) as group:
            group.setValue("basedir", self.basedir.text())
            group.setValue("conf_thres", self.conf_thres.text())
            group.setValue("iou_thres", self.iou_thres.text())
