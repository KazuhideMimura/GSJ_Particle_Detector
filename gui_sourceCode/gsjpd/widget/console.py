import logging
import re

from PySide6.QtCore import Signal
from PySide6.QtGui import QFont, QTextCursor
from PySide6.QtWidgets import QApplication, QPlainTextEdit, QVBoxLayout, QWidget

from ..helper.qcontext import QContext

ansi_escape = re.compile(r"\x1b\[[0-9;]*[mG]")


class ConsoleHandler(logging.Handler):
    plaintext: QPlainTextEdit = None

    def __init__(self, plaintext: QPlainTextEdit, callback: callable = None):
        super().__init__()
        logging.Handler.__init__(self)

        self.plaintext = plaintext
        self.callback = callback

    def emit(self, record):
        cursor = self.plaintext.textCursor()
        cursor.movePosition(QTextCursor.End)

        if record.msg.startswith("\r"):
            # 先頭にLFがある場合は現在行を置換
            # 行の先頭に移動
            cursor.movePosition(QTextCursor.StartOfLine)
            # 行の末尾まで選択
            cursor.movePosition(QTextCursor.EndOfLine, QTextCursor.KeepAnchor)

            # LFを削除
            record.msg = record.msg[1:]
        elif not cursor.atStart():
            # 次の行に移動
            cursor.insertText("\n")

        logtext = ansi_escape.sub("", self.format(record))
        cursor.insertText(logtext.strip("\r\n"))

        self.plaintext.setTextCursor(cursor)
        self.plaintext.ensureCursorVisible()
        self.plaintext.repaint()

        QApplication.processEvents()

        if self.callback:
            self.callback(record)


class ConsoleWidget(QWidget):
    messageRecieved = Signal(str)

    plaintext: QPlainTextEdit = None
    handler: ConsoleHandler = None

    def __init__(self, logLevel=None, maxLines: int = 10000, parent=None):
        super().__init__(parent=parent)

        with QContext(QVBoxLayout()) as layout:
            layout.setContentsMargins(0, 0, 0, 0)
            layout.setSpacing(0)
            self.setLayout(layout)

        with QContext(QFont(["Cascadia Code", "Consolas", "monospace"])) as font:
            font.setPointSizeF(10)
            font.setStretch(QFont.Unstretched)
            font.setStyleHint(QFont.Monospace)
            font.setWeight(QFont.Light)
            self.setFont(font)

        with QContext(QPlainTextEdit(parent=self)) as plaintext:
            plaintext.setReadOnly(True)
            plaintext.setLineWrapMode(QPlainTextEdit.WidgetWidth)
            plaintext.setProperty("style", "console")
            plaintext.setMaximumBlockCount(maxLines)
            plaintext.setFont(self.font())
            self.layout().addWidget(plaintext)
            self.plaintext = plaintext

            self.handler = ConsoleHandler(plaintext, callback=self.emitMessageRecieved)
            self.handler.setLevel(logLevel or "DEBUG")

        formatter = logging.Formatter("[%(asctime)s] %(message)s", datefmt="%a %b %d %X")
        self.handler.setFormatter(formatter)

    def __del__(self):
        if self.handler:
            self.handler.close()
            self.handler = None

    def attachLogger(self, logger: logging.Logger):
        # loggerにself.handlerが設定されていない場合は追加
        if not any(handler == self.handler for handler in logger.handlers):
            logger.addHandler(self.handler)

    def detachLogger(self, logger: logging.Logger):
        # loggerにself.handlerが設定されている場合は削除
        if any(handler == self.handler for handler in logger.handlers):
            logger.removeHandler(self.handler)

    def emitMessageRecieved(self, record: logging.LogRecord):
        self.messageRecieved.emit(record.message)

    def clear(self):
        self.plaintext.clear()
        self.plaintext.repaint()
        QApplication.processEvents()

    def text(self):
        return self.plaintext.toPlainText()

    def setText(self, text: str):
        self.plaintext.setPlainText(text)

        cursor = self.plaintext.textCursor()
        cursor.movePosition(QTextCursor.End)
        self.plaintext.setTextCursor(cursor)
        self.plaintext.ensureCursorVisible()

        QApplication.processEvents()
