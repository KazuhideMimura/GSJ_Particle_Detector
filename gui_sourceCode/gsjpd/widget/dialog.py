from enum import IntEnum

from PySide6.QtCore import Qt, Slot
from PySide6.QtWidgets import (
    QDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
)

from ..helper.qcontext import QContext


class MessageDialog(QDialog):
    message: QLabel = None
    accept_button: QPushButton = None
    reject_button: QPushButton = None

    def __init__(self, title: str, text: str = "", parent=None):
        super().__init__(parent)

        self.setWindowTitle(title)
        self.setFixedWidth(560)
        self.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Preferred)

        self.setWindowFlag(Qt.WindowType.MSWindowsFixedSizeDialogHint)

        with QContext(QVBoxLayout()) as layout:
            self.setLayout(layout)

            layout.setContentsMargins(18, 18, 18, 12)
            layout.setSpacing(12)

        with QContext(QLabel()) as label:
            self.message = label
            self.layout().addWidget(label)

            label.setText(text)
            label.setWordWrap(True)
            label.setAlignment(Qt.AlignTop | Qt.AlignLeft)
            label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

        with QContext(QHBoxLayout()) as layout:
            self.layout().addLayout(layout)

            layout.setContentsMargins(0, 0, 0, 0)
            layout.setSpacing(2)
            layout.addStretch()

            with QContext(QPushButton(self.tr("OK"))) as button:
                button.setProperty("style", "primary")
                button.clicked.connect(self.accept)
                layout.addWidget(button)
                self.accept_button = button

            with QContext(QPushButton(self.tr("Cancel"))) as button:
                button.setProperty("style", "secondary")
                button.clicked.connect(self.reject)
                layout.addWidget(button)
                self.reject_button = button

        self.adjustSize()

    def setAcceptLabel(self, label: str):
        self.accept_button.setText(label)

    def setCancelLabel(self, label: str):
        self.reject_button.setText(label)

    def setText(self, text: str):
        self.message.setText(text)
        self.adjustSize()


class ErrorDialog(MessageDialog):
    message: QLabel = None
    accept_button: QPushButton = None

    def __init__(self, title: str, text: str = "", parent=None):
        super().__init__(title, text, parent)
        self.reject_button.hide()

    @classmethod
    def show(cls, title: str, text: str, parent=None):
        dialog = cls(title, text, parent)
        dialog.exec_()


class PromptDialog(QDialog):
    message: QLabel = None

    meta_layout: QFormLayout

    yes_button: QPushButton = None
    no_button: QPushButton = None
    reject_button: QPushButton = None

    class Result(IntEnum):
        Yes = 1
        No = 2
        Cancel = 0

    def __init__(self, title: str, text: str = "", parent=None):
        super().__init__(parent)

        self.setWindowTitle(title)
        self.setFixedWidth(560)
        self.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Preferred)

        self.setWindowFlag(Qt.WindowType.MSWindowsFixedSizeDialogHint)

        with QContext(QVBoxLayout()) as layout:
            self.setLayout(layout)

            layout.setContentsMargins(18, 18, 18, 12)
            layout.setSpacing(12)

        with QContext(QLabel()) as label:
            self.message = label
            self.layout().addWidget(label)

            label.setText(text)
            label.setWordWrap(True)
            label.setAlignment(Qt.AlignTop | Qt.AlignLeft)
            label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

        with QContext(QFormLayout()) as layout:
            self.layout().addLayout(layout)
            self.meta_layout = layout

            layout.setContentsMargins(0, 0, 0, 0)
            layout.setSpacing(2)

        with QContext(QHBoxLayout()) as layout:
            self.layout().addLayout(layout)

            layout.setContentsMargins(0, 0, 0, 0)
            layout.setSpacing(2)
            layout.addStretch()

            with QContext(QPushButton(self.tr("Yes"))) as button:
                button.setProperty("style", "primary")
                button.clicked.connect(self.onClickedYes)
                layout.addWidget(button)
                self.yes_button = button

            with QContext(QPushButton(self.tr("No"))) as button:
                button.setProperty("style", "primary")
                button.clicked.connect(self.onClickedNo)
                layout.addWidget(button)
                self.no_button = button

            with QContext(QPushButton(self.tr("Cancel"))) as button:
                button.setProperty("style", "secondary")
                button.clicked.connect(self.reject)
                layout.addWidget(button)
                self.reject_button = button

        self.adjustSize()

    @Slot()
    def onClickedYes(self):
        self.done(self.Result.Yes)

    @Slot()
    def onClickedNo(self):
        self.done(self.Result.No)

    def addMetadata(self, name: str, value: str):
        with QContext(QLabel(name), QLineEdit(value)) as (label, edit):
            self.meta_layout.addRow(label, edit)

            label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            label.setProperty("style", "property")
            label.setText(name)
            edit.setEnabled(False)
            edit.setProperty("style", "property")

    def setYesLabel(self, label: str):
        self.yes_button.setText(label)

    def setNoLabel(self, label: str):
        self.no_button.setText(label)

    def setCancelLabel(self, label: str):
        self.reject_button.setText(label)

    def setText(self, text: str):
        self.message.setText(text)
        self.adjustSize()


class EditDialog(QDialog):
    message: QLabel = None
    input: QLineEdit = None
    accept_button: QPushButton = None
    reject_button: QPushButton = None

    def __init__(self, title: str, text: str = "", parent=None):
        super().__init__(parent)

        self.setWindowTitle(title)
        self.setFixedWidth(560)
        self.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Preferred)
        self.setWindowFlag(Qt.WindowType.MSWindowsFixedSizeDialogHint)

        with QContext(QVBoxLayout()) as layout:
            self.setLayout(layout)

            layout.setContentsMargins(18, 18, 18, 12)
            layout.setSpacing(12)

        with QContext(QLabel()) as label:
            self.message = label
            self.layout().addWidget(label)

            label.setText(text)
            label.setAlignment(Qt.AlignTop | Qt.AlignLeft)
            label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

        with QContext(QLineEdit()) as edit:
            self.input = edit
            self.layout().addWidget(edit)

            edit.textChanged.connect(self.onInputTextChanged)

        with QContext(QHBoxLayout()) as layout:
            self.layout().addLayout(layout)

            layout.setContentsMargins(0, 0, 0, 0)
            layout.setSpacing(2)
            layout.addStretch()

            with QContext(QPushButton(self.tr("OK"))) as button:
                button.setProperty("style", "primary")
                button.clicked.connect(self.accept)
                layout.addWidget(button)
                self.accept_button = button

            with QContext(QPushButton(self.tr("Cancel"))) as button:
                button.setProperty("style", "secondary")
                button.clicked.connect(self.reject)
                layout.addWidget(button)
                self.reject_button = button

        self.adjustSize()

    def setAcceptLabel(self, label: str):
        self.accept_button.setText(label)

    def setAcceptStyle(self, style: str):
        self.accept_button.setProperty("style", style)

    def setCancelLabel(self, label: str):
        self.reject_button.setText(label)

    def setText(self, text: str):
        self.message.setText(text)
        self.adjustSize()

    def setInputText(self, text: str):
        self.input.setText(text)

    def inputText(self) -> str:
        return self.input.text()

    def setInputValidator(self, validator):
        self.input.setValidator(validator)

    def setInputEnabled(self, enable: bool):
        self.input.setEnabled(enable)

    @Slot(str)
    def onInputTextChanged(self, text: str):
        self.accept_button.setEnabled(self.input.hasAcceptableInput())
