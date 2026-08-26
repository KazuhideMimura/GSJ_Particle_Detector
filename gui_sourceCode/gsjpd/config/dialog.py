import os
from pathlib import Path

from PySide6.QtCore import Qt, Slot
from PySide6.QtGui import QDoubleValidator, QIntValidator
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QDialog,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
)

from ..__metadata__ import APPLICATION_NAME
from ..__metadata__ import __version__ as version
from ..helper import settings
from ..helper.filesystem import PathnameValidator, getDesktopDir
from ..helper.qcontext import QContext
from ..scripts.shortcut import ShortCut
from ..widget.filesystem import FolderInputWidget
from ..widget.lineedit import RequiredLineEdit


class ConfigDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setFixedWidth(640)
        self.setWindowTitle(self.tr("Configuration"))

        self.setWindowFlag(Qt.WindowType.MSWindowsFixedSizeDialogHint)

        with QContext(QVBoxLayout()) as layout:
            layout.setContentsMargins(12, 12, 12, 12)
            layout.setSpacing(2)
            self.setLayout(layout)

        with QContext(QGroupBox(self.tr("Yolov9"), self)) as box:
            box.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Maximum)
            self.layout().addWidget(box)

            with QContext(QFormLayout()) as layout:
                layout.setFieldGrowthPolicy(QFormLayout.ExpandingFieldsGrow)
                layout.setContentsMargins(3, 3, 3, 3)
                layout.setSpacing(1)
                box.setLayout(layout)

            with QContext(QLabel(), FolderInputWidget()) as (label, dir):
                label.setText(self.tr("Yolov9 folder path"))
                label.setProperty("style", "property")
                dir.setFspath(True)
                dir.setAbsolute(True)
                dir.setObjectName("yolov9_dir")
                dir.setPlaceholderText(self.tr("Path to the yolov9 folder"))
                dir.textChanged.connect(self.onSettingChanged)
                box.layout().addRow(label, dir)
                self.yolov9_dir = dir

            with QContext(QLabel(), FolderInputWidget()) as (label, dir):
                label.setText(self.tr("Pretrained weights folder"))
                label.setProperty("style", "property")
                dir.setObjectName("pretrained_dir")
                dir.setPlaceholderText(
                    self.tr("Relative path to the pretrained weights folder")
                )
                layout.addRow(label, dir)
                self.pretrained_dir = dir

            with QContext(QLabel(), FolderInputWidget()) as (label, dir):
                label.setText(self.tr("Train models folder"))
                label.setProperty("style", "property")
                dir.setObjectName("runs_train_dir")
                dir.setPlaceholderText(self.tr("Relative path to the 'runs/train' folder"))
                layout.addRow(label, dir)
                self.runs_train_dir = dir

            with QContext(QLabel(), FolderInputWidget()) as (label, dir):
                label.setText(self.tr("Sample detection folder"))
                label.setProperty("style", "property")
                dir.setObjectName("runs_detect_dir")
                dir.setPlaceholderText(self.tr("Relative path to the 'runs/detect' folder"))
                layout.addRow(label, dir)
                self.runs_detect_dir = dir

        with QContext(QGroupBox(self.tr("Detection"), self)) as box:
            box.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Maximum)
            self.layout().addWidget(box)

            with QContext(QFormLayout()) as layout:
                layout.setContentsMargins(3, 3, 3, 3)
                layout.setSpacing(1)
                box.setLayout(layout)

            with QContext(QLabel(), RequiredLineEdit()) as (label, edit):
                label.setText(self.tr("Start file"))
                label.setProperty("style", "property")
                edit.setValidator(PathnameValidator())
                edit.setObjectName("start_txt")
                edit.setPlaceholderText(self.tr("Filename of the start file"))
                box.layout().addRow(label, edit)
                self.start_txt = edit

            with QContext(QLabel(), RequiredLineEdit()) as (label, edit):
                label.setText(self.tr("Detection script"))
                label.setProperty("style", "property")
                edit.setValidator(PathnameValidator())
                edit.setObjectName("detect_py")
                edit.setPlaceholderText(self.tr("Filename of the detection script"))
                box.layout().addRow(label, edit)
                self.detect_py = edit

            with QContext(QLabel(), FolderInputWidget()) as (label, dir):
                label.setText(self.tr("Base folder"))
                label.setProperty("style", "property")
                dir.setObjectName("basedir")
                layout.addRow(label, dir)
                self.basedir = dir

            with QContext(QLabel(), RequiredLineEdit()) as (label, input):
                label.setText(self.tr("Confidence threshold"))
                label.setProperty("style", "property")
                input.setValidator(QDoubleValidator(0.0, 1.0, 2))
                input.setObjectName("conf_thres")
                input.setFixedWidth(100)
                layout.addRow(label, input)
                self.conf_thres = input

            with QContext(QLabel(), RequiredLineEdit()) as (label, input):
                label.setText(self.tr("NMS IoU threshold"))
                label.setProperty("style", "property")
                input.setValidator(QDoubleValidator(0.0, 1.0, 2))
                input.setObjectName("iou_thres")
                input.setFixedWidth(100)
                layout.addRow(label, input)
                self.iou_thres = input

            with QContext(QLabel(), QComboBox()) as (label, select):
                label.setText(self.tr("Initial file handling"))
                label.setProperty("style", "property")
                select.setObjectName("initial_handling")
                select.addItem(self.tr("Process detection if newer than last processed file"))
                select.addItem(self.tr("Show dialog to select action"))
                select.addItem(self.tr("Process existing files first"))
                select.addItem(self.tr("Wait for updates without processing existing files"))
                layout.addRow(label, select)
                self.initial_handling = select

        with QContext(QGroupBox(self.tr("Train and test"), self)) as box:
            box.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Maximum)
            self.layout().addWidget(box)

            with QContext(QFormLayout()) as layout:
                layout.setContentsMargins(3, 3, 3, 3)
                layout.setSpacing(1)
                box.setLayout(layout)

            with QContext(QLabel(), RequiredLineEdit()) as (label, edit):
                label.setText(self.tr("Training script"))
                label.setProperty("style", "property")
                edit.setValidator(PathnameValidator())
                edit.setObjectName("train_py")
                edit.setPlaceholderText(self.tr("Filename of the training script"))
                box.layout().addRow(label, edit)
                self.train_py = edit

            with QContext(QLabel(), RequiredLineEdit()) as (label, edit):
                label.setText(self.tr("Test script"))
                label.setProperty("style", "property")
                edit.setValidator(PathnameValidator())
                edit.setObjectName("test_py")
                edit.setPlaceholderText(self.tr("Filename of the test script"))
                box.layout().addRow(label, edit)
                self.test_py = edit

            with QContext(QLabel(), RequiredLineEdit()) as (label, edit):
                label.setText(self.tr("Sample detection script"))
                label.setProperty("style", "property")
                edit.setValidator(PathnameValidator())
                edit.setObjectName("sample_detect_py")
                edit.setPlaceholderText(self.tr("Filename of the sample detection script"))
                box.layout().addRow(label, edit)
                self.sample_detect_py = edit

            with QContext(QLabel(), RequiredLineEdit()) as (label, input):
                label.setText(self.tr("Train batch size"))
                label.setProperty("style", "property")
                input.setValidator(QIntValidator(bottom=1, top=9999))
                input.setObjectName("train_batch_size")
                input.setFixedWidth(100)
                layout.addRow(label, input)
                self.train_batch_size = input

            with QContext(QLabel(), RequiredLineEdit()) as (label, input):
                label.setText(self.tr("Test batch size"))
                label.setProperty("style", "property")
                input.setValidator(QIntValidator(bottom=1, top=9999))
                input.setObjectName("test_batch_size")
                input.setFixedWidth(100)
                layout.addRow(label, input)
                self.test_batch_size = input

            with QContext(QLabel(), RequiredLineEdit()) as (label, input):
                label.setText(self.tr("Device"))
                label.setProperty("style", "property")
                input.setValidator(QIntValidator())
                input.setObjectName("device")
                input.setFixedWidth(100)
                layout.addRow(label, input)
                self.device = input

            with QContext(QLabel(), RequiredLineEdit()) as (label, input):
                label.setText(self.tr("Workers"))
                label.setProperty("style", "property")
                input.setValidator(QIntValidator())
                input.setObjectName("workers")
                input.setFixedWidth(100)
                layout.addRow(label, input)
                self.workers = input

        with QContext(QGroupBox(self.tr("Tools"), self)) as box:
            box.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Maximum)
            self.layout().addWidget(box)

            with QContext(QFormLayout()) as layout:
                layout.setContentsMargins(3, 3, 3, 3)
                layout.setSpacing(1)
                box.setLayout(layout)

            with QContext(QLabel(), QPushButton()) as (label, button):
                label.setText(self.tr("Startup shortcut"))
                label.setProperty("style", "property")
                button.setText(self.tr("Create shortcut"))
                button.setProperty("style", "primary")
                button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
                button.clicked.connect(self.onShortcutButtonClicked)
                layout.addRow(label, button)

        self.layout().addSpacing(6)

        with QContext(QHBoxLayout()) as layout:
            self.layout().addLayout(layout)

            layout.setContentsMargins(3, 6, 3, 3)
            layout.setSpacing(2)

            with QContext(QLabel()) as label:
                layout.addWidget(label)
                label.setText(f"{APPLICATION_NAME} {version}")

            layout.addStretch()

            with QContext(QPushButton()) as (button):
                button.setProperty("style", "primary")
                button.setText(self.tr("OK"))
                button.clicked.connect(self.accept)
                layout.addWidget(button)
                self.ok_button = button

            with QContext(QPushButton()) as (button):
                button.setProperty("style", "secondary")
                button.setText(self.tr("Cancel"))
                button.clicked.connect(self.reject)
                layout.addWidget(button)

        self.loadSettings()
        self.accepted.connect(self.saveSettings)
        self.updateButtonState()

        self.adjustSize()

    def loadSettings(self):
        self.yolov9_dir.setText(settings.value("yolov9_dir", ""))
        self.runs_train_dir.setText(settings.value("runs_train_dir", "runs/train"))
        self.runs_detect_dir.setText(settings.value("runs_detect_dir", "runs/detect"))
        self.pretrained_dir.setText(settings.value("pretrained_dir", "runs/pretrained"))

        with settings.group("Detection") as group:
            self.detect_py.setText(group.value("detect_py", "detect_collection_pro.py"))
            self.start_txt.setText(group.value("start_txt", "start.txt"))
            self.basedir.setText(group.value("basedir", "share"))
            self.conf_thres.setText(group.value("conf_thres", "0.25"))
            self.iou_thres.setText(group.value("iou_thres", "0.1"))
            self.initial_handling.setCurrentIndex(
                settings.safeInt(group.value("initial_handling", 0))
            )

        with settings.group("Training") as group:
            self.train_py.setText(group.value("train_py", "train_dual.py"))
            self.test_py.setText(group.value("test_py", "val.py"))
            self.sample_detect_py.setText(group.value("sample_detect_py", "detect.py"))
            self.train_batch_size.setText(group.value("train_batch_size", "16"))
            self.test_batch_size.setText(group.value("test_batch_size", "32"))
            self.device.setText(group.value("device", "0"))
            self.workers.setText(group.value("workers", "4"))

    def saveSettings(self):
        settings.setValue("yolov9_dir", self.yolov9_dir.text())
        settings.setValue("runs_train_dir", self.runs_train_dir.text())
        settings.setValue("runs_detect_dir", self.runs_detect_dir.text())
        settings.setValue("pretrained_dir", self.pretrained_dir.text())

        with settings.group("Detection") as group:
            group.setValue("detect_py", self.detect_py.text())
            group.setValue("start_txt", self.start_txt.text())
            group.setValue("basedir", self.basedir.text())
            group.setValue("conf_thres", self.conf_thres.text())
            group.setValue("iou_thres", self.iou_thres.text())
            group.setValue("initial_handling", self.initial_handling.currentIndex())

        with settings.group("Training") as group:
            group.setValue("train_py", self.train_py.text())
            group.setValue("test_py", self.test_py.text())
            group.setValue("sample_detect_py", self.sample_detect_py.text())
            group.setValue("train_batch_size", self.train_batch_size.text())
            group.setValue("test_batch_size", self.test_batch_size.text())
            group.setValue("device", self.device.text())
            group.setValue("workers", self.workers.text())

        settings.sync()

    @Slot(str)
    def onSettingChanged(self, text: str):
        self.updateButtonState()

    @Slot()
    def onShortcutButtonClicked(self):
        dialog = QFileDialog(self)
        dialog.setFileMode(QFileDialog.Directory)
        dialog.setOption(QFileDialog.ShowDirsOnly, True)
        dialog.setWindowTitle(self.tr("Select a folder to create a shortcut"))

        desktopDir = getDesktopDir()
        if desktopDir:
            dialog.setDirectory(os.fspath(desktopDir))

        if dialog.exec():
            QApplication.setOverrideCursor(Qt.WaitCursor)
            try:
                ShortCut().create()
            finally:
                QApplication.restoreOverrideCursor()

    def updateButtonState(self):
        yolov9_dir = Path(self.yolov9_dir.text())

        if yolov9_dir.is_absolute() and yolov9_dir.exists():
            self.ok_button.setEnabled(True)
        else:
            self.ok_button.setEnabled(False)
