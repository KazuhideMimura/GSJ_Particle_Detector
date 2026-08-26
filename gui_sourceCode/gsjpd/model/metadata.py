from PySide6.QtCore import Signal, Slot
from PySide6.QtWidgets import (
    QFormLayout,
    QGroupBox,
    QLabel,
    QLineEdit,
    QSizePolicy,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from ..helper.filesystem import PathnameValidator
from ..helper.format import dtformat
from ..helper.qcontext import QContext
from .data import Metadata


class MetadataWidget(QWidget):
    form_layout: QFormLayout = None

    name: QLineEdit = None
    description: QTextEdit = None
    timestamp: QLineEdit = None

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Fixed)

        with QContext(QVBoxLayout()) as layout:
            layout.setSizeConstraint(QVBoxLayout.SetMinimumSize)
            layout.setContentsMargins(3, 3, 3, 3)
            layout.setSpacing(2)
            self.setLayout(layout)

        with QContext(QGroupBox(self.tr("Model metadata"), self)) as box:
            self.layout().addWidget(box)

            with QContext(QFormLayout()) as layout:
                self.form_layout = layout

                layout.setContentsMargins(3, 3, 3, 3)
                layout.setSpacing(1)
                box.setLayout(layout)

            with QContext(QLabel(parent=self), QLineEdit(parent=self)) as (label, edit):
                self.name = edit
                box.layout().addRow(label, edit)

                label.setText(self.tr("model name"))
                label.setProperty("style", "property")
                edit.setObjectName("name")

            with QContext(QLabel(parent=self), QTextEdit(parent=self)) as (label, edit):
                self.description = edit
                box.layout().addRow(label, edit)

                label.setText(self.tr("memo"))
                label.setProperty("style", "property")
                edit.setObjectName("description")
                edit.setFixedHeight(64)

            with QContext(QLabel(parent=self), QLineEdit(parent=self)) as (label, edit):
                self.timestamp = edit
                box.layout().addRow(label, edit)

                label.setText(self.tr("trained at"))
                label.setProperty("style", "property")
                edit.setObjectName("timestamp")
                edit.setEnabled(False)

    def setValues(self, metadata: Metadata):
        if not metadata:
            self.name.clear()
            self.description.clear()
            self.timestamp.clear()
        else:
            self.name.setText(metadata.name)
            self.description.setText(metadata.description)
            self.timestamp.setText(dtformat(metadata.timestamp))

        self.form_layout.setRowVisible(self.timestamp, bool(self.timestamp.text()))


class MetadataView(MetadataWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.name.setEnabled(False)
        self.description.setEnabled(False)
        self.timestamp.setEnabled(False)


class MetadtaForm(MetadataWidget):
    inputChanged = Signal(str, object)

    def __init__(self, parent=None):
        super().__init__(parent)

        self.name.setValidator(PathnameValidator())
        self.name.setPlaceholderText("save to project/name")
        self.name.textChanged.connect(self.onTextChanged)

        self.description.setPlaceholderText("memo")
        self.description.textChanged.connect(self.onTextChanged)

    @Slot()
    def onTextChanged(self):
        sender = self.sender()
        if sender is None:
            return

        if isinstance(sender, QTextEdit):
            self.inputChanged.emit(sender.objectName(), sender.toPlainText())
        else:
            self.inputChanged.emit(sender.objectName(), sender.text())

    def hasAcceptableInput(self):
        return self.name.hasAcceptableInput()
