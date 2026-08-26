from enum import IntEnum
from math import sqrt

from PySide6.QtCore import QPointF, QSize, Qt
from PySide6.QtGui import (
    QColor,  # 追加
    QMouseEvent,
    QPainter,
    QPixmap,
    QTransform,
    QWheelEvent,
)
from PySide6.QtWidgets import QApplication, QSizePolicy, QWidget


class DragMode(IntEnum):
    NONE = 0
    IMAGE = 1


class ImageViewWidget(QWidget):
    DefaultScale = 0.5

    dragMode: DragMode = DragMode.NONE

    pixmap: QPixmap = None
    transform: QTransform = None

    dragTransform: QTransform = None

    backgroundColor: QColor = QColor(Qt.white)

    def __init__(self, pixmap: QPixmap = None, parent=None):
        super().__init__(parent)

        self.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.MinimumExpanding)
        self.setContentsMargins(0, 0, 0, 0)

        self.setMouseTracking(True)

        self.transform = QTransform().scale(self.DefaultScale, self.DefaultScale)
        self.resetTransform()

        self.dragMode = DragMode.NONE
        self.dragStartPosition = QPointF()

        self.fitToWindow = True

        self.setPixmap(pixmap)

    def setPixmap(self, pixmap: QPixmap):
        prevSize = self.pixmap.size() if self.pixmap else QSize()
        self.pixmap = pixmap

        if self.pixmap is None:
            self.transform = QTransform().scale(self.DefaultScale, self.DefaultScale)
            self.update()
            return

        # 背景色を取得して保存
        self.backgroundColor = QColor(Qt.white)
        if self.pixmap:
            image = self.pixmap.toImage()
            if not image.isNull():
                self.backgroundColor = QColor(image.pixel(0, 0))

        if prevSize.width() != self.pixmap.width() or prevSize.height() != self.pixmap.height():
            self.resetTransform()
        else:
            self.update()

    def resizeEvent(self, event):
        super().resizeEvent(event)

        if self.fitToWindow:
            self.resetTransform()

    def paintEvent(self, event):
        painter = QPainter(self)

        try:
            # 保存した背景色で塗りつぶす
            painter.fillRect(event.rect(), self.backgroundColor)

            painter.setRenderHint(QPainter.Antialiasing)
            painter.setTransform(self.transform)

            if self.pixmap:
                painter.drawPixmap(0, 0, self.pixmap)

        finally:
            painter.end()

    def wheelEvent(self, event: QWheelEvent):
        delta = event.angleDelta().y()
        factor = sqrt(2.0) if delta > 0 else 1.0 / sqrt(2.0)

        if (self.transform.m11() * 16) < 1 and factor < 1.0:
            return
        if (self.transform.m11() / 16) > 1 and factor > 1.0:
            return

        # マウスカーソルの位置を取得
        cursorPos = event.position()

        # 画像座標でのカーソル位置
        inverted, invertible = self.transform.inverted()
        if invertible:
            # カーソル位置を中心として拡大・縮小
            imgPos = inverted.map(cursorPos)
            self.transform.translate(imgPos.x(), imgPos.y())
            self.transform.scale(factor, factor)
            self.transform.translate(-imgPos.x(), -imgPos.y())

            self.fitToWindow = False
            self.update()
            event.accept()

    def mousePressEvent(self, event: QMouseEvent):
        if self.dragMode != DragMode.NONE:
            return event.accept()

        self.dragMode = DragMode.IMAGE
        self.dragStartPosition = event.pos()
        QApplication.setOverrideCursor(Qt.ClosedHandCursor)

    def mouseMoveEvent(self, event: QMouseEvent):
        if self.dragMode == DragMode.IMAGE:
            sx, sy = self.transform.m11(), self.transform.m22()
            delta = event.pos() - self.dragStartPosition
            self.fitToWindow = False
            self.transform.translate(delta.x() / sx, delta.y() / sy)
            self.dragStartPosition = event.pos()
            self.update()
            return event.accept()

        QApplication.restoreOverrideCursor()

    def mouseReleaseEvent(self, event: QMouseEvent):
        if self.dragMode == DragMode.IMAGE:
            self.dragMode = DragMode.NONE
            QApplication.restoreOverrideCursor()
            return event.accept()

        return super().mouseReleaseEvent(event)

    def resetTransform(self):
        if not self.pixmap:
            return

        widgetSize = self.size()
        pixmapSize = self.pixmap.size()
        if widgetSize.isEmpty() or pixmapSize.isEmpty():
            return

        # 画像をウィジェットにフィットさせるためのスケーリング
        sx = widgetSize.width() / pixmapSize.width()
        sy = widgetSize.height() / pixmapSize.height()
        scale = min(sx, sy)

        self.transform = QTransform().scale(scale, scale)

        # 画像を中央に配置するための平行移動
        dx = (widgetSize.width() - pixmapSize.width() * scale) / 2
        dy = (widgetSize.height() - pixmapSize.height() * scale) / 2
        self.transform.translate(dx / scale, dy / scale)

        self.fitToWindow = True
        self.update()

    def mouseDoubleClickEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.LeftButton:
            self.resetTransform()
            return event.accept()

        return super().mouseDoubleClickEvent(event)
