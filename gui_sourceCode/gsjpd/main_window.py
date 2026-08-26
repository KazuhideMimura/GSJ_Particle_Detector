from pathlib import Path

from PySide6.QtCore import QDir, QSize, Qt, QTimer, Slot
from PySide6.QtGui import QAction, QIcon
from PySide6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QMainWindow,
    QSizePolicy,
    QStyle,
    QStyleOptionTab,
    QStylePainter,
    QTabBar,
    QTabWidget,
    QToolBar,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from .config import ConfigDialog
from .detection import DetectionMainWidget
from .helper import QContext, settings
from .model import ModelMainWidget
from .widget.dialog import MessageDialog


class MainWindow(QMainWindow):
    application: QApplication = None

    toolbar: QToolBar = None
    tab: QTabWidget = None

    def __init__(self):
        super().__init__()

        self.application = QApplication.instance()

        self.setMinimumSize(QSize(1154, 768))
        self.setWindowTitle(self.tr("GSJ Particle Detector"))

        # icon
        appIcon = QIcon()
        appIcon.addFile(":/icons/app_icon_32.png", QSize(32, 32))
        appIcon.addFile(":/icons/app_icon_64.png", QSize(64, 64))
        self.application.setWindowIcon(appIcon)

        self.setCentralWidget(QWidget())
        with QContext(QVBoxLayout()) as layout:
            self.centralWidget().setLayout(layout)
            layout.setContentsMargins(3, 0, 3, 3)

        with QContext(QToolBar(self)) as toolbar:
            self.toolbar = toolbar
            self.addToolBar(toolbar)
            toolbar.setMovable(False)
            toolbar.setFloatable(False)
            toolbar.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)

        with QContext(QWidget(self)) as spacer:
            self.toolbar.addWidget(spacer)
            spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        with QContext(QAction(self.tr("Configuration"), self)) as action:
            self.toolbar.addAction(action)
            action.setIcon(QIcon(":/icons/gear.png"))
            action.triggered.connect(self.showConfiguration)

        with QContext(QTabWidget(self)) as tab:
            self.tab = tab
            self.centralWidget().layout().addWidget(tab)
            tab.setProperty("style", "main")
            tab.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        with QContext(DetectionMainWidget()) as detection:
            self.detection = detection
            self.tab.addTab(detection, self.tr("Detection"))
            detection.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        with QContext(ModelMainWidget(parent=self)) as models:
            self.models = models
            self.tab.addTab(models, self.tr("Models"))
            models.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        geometry = settings.value("windowGeometry", group="Internal")
        if geometry:
            self.restoreGeometry(geometry)
        else:
            self.resize(1600, 932)

    @Slot()
    def showConfiguration(self):
        dialog = ConfigDialog(self.window())

        if dialog.exec():
            yolov9_dir = settings.value("yolov9_dir", "")
            if yolov9_dir and Path(yolov9_dir).exists():
                QDir.setCurrent(yolov9_dir)

            self.models.updateData()

    def show(self):
        super().show()

        # ウィンドウが開いた後の処理を遅延実行
        QTimer.singleShot(0, self.onWindowOpened)

    def closeEvent(self, event):
        if self.detection.isThreadRunning() or self.models.isThreadRunning():
            dialog = MessageDialog(self.tr("Confirm Exit"), parent=self.window())
            dialog.setText(self.tr("Detection or train process is running. Terminate it?"))
            dialog.setAcceptLabel(self.tr("Terminate"))

            if not dialog.exec():
                event.ignore()
                return

        self.detection.terminate()
        self.models.terminate()

        settings = self.application.settings
        settings.beginGroup("Internal")
        settings.setValue("windowGeometry", self.saveGeometry())
        settings.endGroup()

        super().closeEvent(event)

    def onWindowOpened(self):
        # yolov9_dirが設定されていない場合は設定画面を表示
        yolov9_dir = settings.value("yolov9_dir", "")
        if not yolov9_dir or not Path(yolov9_dir).exists():
            self.showConfiguration()

    def keyPressEvent(self, event):
        """
        キーボードのキーが押されたときに呼び出されるイベントハンドラ。
        """
        if event.key() == Qt.Key.Key_F5:
            self.detection.updateData()
            self.models.updateData()
        else:
            super().keyPressEvent(event)


class MainTabBar(QTabBar):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Maximum)

        with QContext(QHBoxLayout()) as layout:
            layout.setContentsMargins(0, 0, 0, 0)
            self.setLayout(layout)

        self.layout().addStretch()

        with QContext(QToolButton(self)) as button:
            button.setText("Prefereces")
            button.setFixedSize(QSize(20, 20))
            self.layout().addWidget(button)
            self.config_button = button

    def updateLayout(self):
        if self.parent() is not None:
            self.setFixedWidth(self.parent().width())

    def paintEvent(self, event):
        painter = QStylePainter(self)
        option = QStyleOptionTab()

        h_margin = self.style().pixelMetric(QStyle.PM_TabBarTabHSpace, option, self)
        v_margin = self.style().pixelMetric(QStyle.PM_TabBarTabVSpace, option, self)

        for index in range(self.count()):
            self.initStyleOption(option, index)
            text = self.tabText(index)

            rect = option.fontMetrics.boundingRect(text)

            option.rect.setWidth(rect.width() + h_margin)
            option.rect.setHeight(rect.height() + v_margin)

            painter.drawControl(QStyle.CE_TabBarTab, option)

        # event.accept()

        # # 最後にデフォルトのpaintEventを呼び出して残りの部分を描画
        # super().paintEvent(event)
        painter.end()


class MainTabWidget(QTabWidget):
    tabbar: MainTabBar = None

    def __init__(self, parent=None):
        super().__init__(parent)

        with QContext(MainTabBar(self)) as tabbar:
            self.setTabBar(tabbar)
            self.tabbar = tabbar

    def resizeEvent(self, event):
        self.tabbar.updateLayout()

        return super().resizeEvent(event)
