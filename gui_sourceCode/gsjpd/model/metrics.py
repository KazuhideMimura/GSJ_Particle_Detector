from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFormLayout,
    QGroupBox,
    QLabel,
    QLineEdit,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from ..helper.qcontext import QContext
from .data import Metrics


class MetricsWidget(QWidget):
    precision: QLineEdit = None
    recall: QLineEdit = None
    mAP50: QLineEdit = None
    mAP: QLineEdit = None

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Fixed)

        with QContext(QVBoxLayout()) as layout:
            layout.setSizeConstraint(QVBoxLayout.SetMinimumSize)
            layout.setContentsMargins(3, 3, 3, 3)
            layout.setSpacing(2)
            self.setLayout(layout)

        with QContext(QGroupBox(self.tr("Test metrics"), self)) as box:
            self.layout().addWidget(box)

            with QContext(QFormLayout()) as layout:
                layout.setContentsMargins(3, 3, 3, 3)
                layout.setSpacing(1)
                box.setLayout(layout)

            with QContext(QLabel(parent=self), QLineEdit(parent=self)) as (label, edit):
                label.setText(self.tr("precision"))
                label.setProperty("style", "property")
                edit.setObjectName("precision")
                edit.setAlignment(Qt.AlignRight)
                box.layout().addRow(label, edit)
                self.precision = edit

            with QContext(QLabel(parent=self), QLineEdit(parent=self)) as (label, edit):
                label.setText(self.tr("recall"))
                label.setProperty("style", "property")
                edit.setObjectName("recall")
                edit.setAlignment(Qt.AlignRight)
                box.layout().addRow(label, edit)
                self.recall = edit

            with QContext(QLabel(parent=self), QLineEdit(parent=self)) as (label, edit):
                label.setText(self.tr("mAP@0.5"))
                label.setProperty("style", "property")
                edit.setObjectName("mAP50")
                edit.setAlignment(Qt.AlignRight)
                box.layout().addRow(label, edit)
                self.mAP50 = edit

            with QContext(QLabel(parent=self), QLineEdit(parent=self)) as (label, edit):
                label.setText(self.tr("mAP@0.5:0.95"))
                label.setProperty("style", "property")
                edit.setObjectName("mAP")
                edit.setAlignment(Qt.AlignRight)
                box.layout().addRow(label, edit)
                self.mAP = edit

    def setValues(self, metrics: Metrics):
        if not metrics:
            self.precision.clear()
            self.recall.clear()
            self.mAP50.clear()
            self.mAP.clear()
            return

        def format(value):
            return f"{value:.6f}" if value is not None else ""

        self.precision.setText(format(metrics.precision))
        self.recall.setText(format(metrics.recall))
        self.mAP50.setText(format(metrics.mAP50))
        self.mAP.setText(format(metrics.mAP))


class MetricsView(MetricsWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.precision.setEnabled(False)
        self.recall.setEnabled(False)
        self.mAP50.setEnabled(False)
        self.mAP.setEnabled(False)
