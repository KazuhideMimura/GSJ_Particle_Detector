from pathlib import Path

from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QSizePolicy,
    QStyle,
    QWidget,
)

from ..helper import settings
from ..helper.filesystem import abspath
from ..helper.format import dtformat, fformat
from ..helper.qcontext import QContext
from .data import ModelInfo


class ModelListHeaderRow(QWidget):
    clicked = Signal(str)

    label: QPushButton = None
    description: QPushButton = None
    timestamp: QPushButton = None
    mAP50: QPushButton = None
    mAP: QPushButton = None

    def __init__(self, parent=None):
        super().__init__(parent)

        margin = 4
        scroll_width = self.style().pixelMetric(QStyle.PixelMetric.PM_ScrollBarExtent)

        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        self.setLayout(QHBoxLayout())
        self.layout().setContentsMargins(4, 0, 4, 0)
        self.layout().setSpacing(1)

        with QContext(QPushButton(self.tr("Name"), parent=self)) as button:
            button.setFixedWidth(200 + margin)
            button.clicked.connect(lambda: self.clicked.emit("name"))
            self.layout().addWidget(button)
            self.label = button

        with QContext(QPushButton(self.tr("Memo"), parent=self)) as button:
            button.clicked.connect(lambda: self.clicked.emit("description"))
            self.layout().addWidget(button)
            self.description = button

        with QContext(QPushButton(self.tr("Timestamp"), parent=self)) as button:
            button.setFixedWidth(128)
            button.clicked.connect(lambda: self.clicked.emit("timestamp"))
            self.layout().addWidget(button)
            self.description = button

        with QContext(QPushButton(self.tr("mAP@0.5"), parent=self)) as button:
            button.setFixedWidth(96)
            button.clicked.connect(lambda: self.clicked.emit("mAP50"))
            self.layout().addWidget(button)
            self.mAP50 = button

        with QContext(QPushButton(self.tr("mAP@0.5:0.95"), parent=self)) as button:
            button.setFixedWidth(96 + scroll_width + margin)
            button.clicked.connect(lambda: self.clicked.emit("mAP"))
            self.layout().addWidget(button)
            self.mAP = button


class ModelListItemRow(QWidget):
    label: QLabel = None
    description: QLabel = None
    timestamp: QLabel = None
    mAP50: QLabel = None
    mAP: QLabel = None

    model: ModelInfo = None

    def __init__(self, label, model: ModelInfo = None, parent=None):
        super().__init__(parent)

        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        self.setLayout(QHBoxLayout())
        self.layout().setContentsMargins(6, 6, 6, 6)
        self.layout().setSpacing(1)

        with QContext(QLabel("", parent=self)) as label:
            label.setFixedWidth(200)
            self.layout().addWidget(label)
            self.label = label

        with QContext(QLabel("", parent=self)) as label:
            label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            self.layout().addWidget(label)
            self.description = label

        with QContext(QLabel("", parent=self)) as label:
            label.setFixedWidth(128)
            label.setAlignment(Qt.AlignCenter)
            self.layout().addWidget(label)
            self.timestamp = label

        with QContext(QLabel("", parent=self)) as label:
            label.setFixedWidth(96)
            label.setAlignment(Qt.AlignRight)
            self.layout().addWidget(label)
            self.mAP50 = label

        with QContext(QLabel("", parent=self)) as label:
            label.setFixedWidth(96)
            label.setAlignment(Qt.AlignRight)
            self.layout().addWidget(label)
            self.mAP = label

        self.updateData(model)

    def updateData(self, model: ModelInfo):
        if model:
            self.label.setText(model.metadata.name)
            self.description.setText(model.metadata.description)
            self.timestamp.setText(dtformat(model.metadata.timestamp))
            self.mAP50.setText(fformat(model.metrics.mAP50))
            self.mAP.setText(fformat(model.metrics.mAP))

        self.model = model


class ModelListItem(QListWidgetItem):
    model: ModelInfo = None

    def __init__(self, model: ModelInfo = None, parent=None):
        super().__init__(parent)
        self.model = model


class ModelListWidget(QListWidget):
    sort_key: str = "name"
    sort_order: Qt.SortOrder = Qt.AscendingOrder

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setContentsMargins(0, 0, 0, 0)
        self.setSpacing(0)
        self.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.MinimumExpanding)

        self.setIconSize(QSize(0, 0))
        self.setDragEnabled(False)
        self.setAcceptDrops(False)
        self.setSortingEnabled(True)
        self.setSelectionMode(QListWidget.SingleSelection)
        self.setSizeAdjustPolicy(QListWidget.AdjustToContents)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self.updateData()

    def updateData(self):
        self.clear()

        runs_train = abspath(settings.value("runs_train_dir", "runs/train"))

        if runs_train.exists():
            for runs_dir in runs_train.iterdir():
                self.addModelItem(runs_dir)

            self.sort(self.sort_key, toggle=False)

    def addModelItem(self, runs_dir: Path):
        best_pt = next(runs_dir.glob("**/best.pt"), None)

        model = ModelInfo.from_dir(runs_dir)

        item = ModelListItem(model, parent=self)
        widget = ModelListItemRow(runs_dir.name, model, parent=self)

        # リストに追加
        item.setSizeHint(widget.sizeHint())
        self.addItem(item)
        self.setItemWidget(item, widget)

    def sort(self, key: str, toggle: bool = True):
        for i in range(self.count()):
            item = self.item(i)
            match key:
                case "name":
                    item.setText(item.model.metadata.name)
                case "description" | "memo":
                    item.setText(item.model.metadata.description)
                case "timestamp":
                    item.setText(dtformat(item.model.metadata.timestamp))
                case "mAP50":
                    item.setText(fformat(item.model.metrics.mAP50))
                case "mAP":
                    item.setText(fformat(item.model.metrics.mAP))
                case _:
                    pass

        if toggle and key == self.sort_key:
            if self.sort_order == Qt.AscendingOrder:
                self.sort_order = Qt.DescendingOrder
            else:
                self.sort_order = Qt.AscendingOrder

        self.sort_key = key
        self.sortItems(self.sort_order)

    def findItem(self, runs_dir: str) -> ModelListItem | None:
        for i in range(self.count()):
            item = self.item(i)
            if item.model.runs_dir == runs_dir:
                return item

        return None
