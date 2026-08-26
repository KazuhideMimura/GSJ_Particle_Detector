import os
from pathlib import Path

from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QHBoxLayout,
    QPushButton,
    QSizePolicy,
    QWidget,
)

from ..helper.filesystem import abspath, relpath
from .lineedit import RequiredLineEdit


class YamlComboBox(QComboBox):
    itemSelected = Signal(str)

    def __init__(
        self,
        dir: os.PathLike = None,
        pattern: str = "*.yaml",
        *,
        empty_item: str = None,
        parent=None,
    ):
        super().__init__(parent)

        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Maximum)

        if dir is not None:
            self.init(dir, pattern)

        self.currentIndexChanged.connect(self.onCurrentIndexChanged)

    @Slot(int)
    def onCurrentIndexChanged(self, index: int):
        self.itemSelected.emit(self.currentData())

    def setCurrentData(self, data: str):
        index = self.findData(relpath(data, posix=True))
        if index >= 0:
            if index != self.currentIndex():
                self.setCurrentIndex(index)
            else:
                # 変わらない場合でもシグナルを発行
                self.onCurrentIndexChanged(index)

    def init(self, dir: os.PathLike, pattern: str = "*.yaml", empty_item: str = None):
        self.clear()
        if not os.path.exists(dir):
            return

        if empty_item is not None:
            self.addItem(empty_item, None)

        for path in Path(dir).glob(pattern):
            self.addItem(path.stem, relpath(path, posix=True))

        self.setCurrentIndex(0)

    def hasAcceptableInput(self):
        return self.currentData() is not None and abspath(self.currentData()).exists()


class FileSystemInputWidget(QWidget):
    selected = Signal(str)
    textChanged = Signal(str)

    filter: str = None
    start_dir: os.PathLike = None
    initial_dir: os.PathLike = None

    exist_required: bool = False

    def __init__(
        self,
        mode: QFileDialog.FileMode = QFileDialog.AnyFile,
        path: os.PathLike = None,
        *,
        start_dir: os.PathLike = None,
        fspath: bool = False,
        absolute: bool = False,
        parent=None,
    ):
        super().__init__(parent)

        self.file_mode = mode
        self.fspath = fspath
        self.absolute = absolute

        self.setLayout(QHBoxLayout())
        self.layout().setContentsMargins(0, 0, 0, 0)
        self.layout().setSpacing(2)

        self.input = RequiredLineEdit("", self)
        self.input.setAlignment(Qt.AlignLeft)
        self.input.textChanged.connect(self.onInutTextChanged)
        self.input.setReadOnly(True)
        self.layout().addWidget(self.input)

        self.button = QPushButton("...", self)
        self.button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.button.setProperty("style", "small")
        self.button.setFlat(True)
        self.button.clicked.connect(self.onButtonClicked)
        self.layout().addWidget(self.button)

        self.setPath(path)
        self.setNameFilter("All Files (*)")

        if start_dir is None:
            start_dir = os.getcwd()

        self.setStartDir(start_dir)

    def clear(self):
        self.input.clear()

    def setPlaceholderText(self, text: str):
        self.input.setPlaceholderText(text)

    def text(self):
        return self.input.text()

    def path(self):
        return Path(self.text())

    def validator(self):
        return self.input.validator()

    def setText(self, text: str):
        self.input.setText(text)

    def setPath(self, path: Path):
        self.input.setText(os.fspath(path or ""))

    def setNameFilter(self, filter: str):
        self.filter = filter

    def setInitialDir(self, path: os.PathLike):
        self.initial_dir = path

    def setStartDir(self, path: os.PathLike):
        self.start_dir = path
        if self.initial_dir is None:
            self.initial_dir = path

    def setEnabled(self, enabled: bool):
        # disableの場合はボタンを表示しない
        self.button.setVisible(enabled)

        return super().setEnabled(enabled)

    def setFspath(self, fspath: bool):
        self.fspath = fspath

    def setAbsolute(self, absolute: bool):
        self.absolute = absolute

    def setRequired(self, required: bool):
        self.input.setRequired(required)

    def setExistRequired(self, exist_required: bool):
        self.input.setRequired(exist_required or self.input.required)
        self.exist_required = exist_required

    def hasAcceptableInput(self):
        if self.input.text() == "":
            return False

        if self.exist_required:
            input_path = self.input.text() or self.initial_dir
            if not Path(input_path).is_absolute():
                input_path = Path(self.start_dir or os.getcwd(), input_path)

            return Path(input_path).exists()
        else:
            return self.input.hasAcceptableInput()

    @Slot()
    def onButtonClicked(self):
        dialog = QFileDialog(self)
        dialog.setFileMode(self.file_mode)

        if self.file_mode == QFileDialog.Directory:
            input_dir = self.input.text() or self.initial_dir
            if not Path(input_dir).is_absolute():
                input_dir = Path(self.start_dir or os.getcwd(), input_dir)

            dialog.setOption(QFileDialog.ShowDirsOnly, True)
            dialog.setDirectory(abspath(input_dir, fspath=True))

        elif self.filter is not None:
            dialog.setNameFilter(self.filter)
            dialog.setDirectory(abspath(self.initial_dir, fspath=True))

        if dialog.exec():
            path = Path(dialog.selectedFiles()[0])

            if self.start_dir:
                try:
                    path = path.relative_to(self.start_dir)
                except ValueError:
                    path = path.absolute()

            if self.absolute:
                path = path.absolute()

            pathname = os.fspath(path) if self.fspath else path.as_posix()
            self.input.setText(pathname)
            self.selected.emit(pathname)

    @Slot(str)
    def onInutTextChanged(self, text: str):
        if self.exist_required:
            input_path = self.input.text() or self.initial_dir
            if not Path(input_path).is_absolute():
                input_path = Path(self.start_dir or os.getcwd(), input_path)

            state = "required" if Path(input_path).exists() else "accepted"
            self.input.setProperty("state", state)

        self.textChanged.emit(text)


class FolderInputWidget(FileSystemInputWidget):
    def __init__(self, path: os.PathLike = None, *, start_dir: os.PathLike = None, parent=None):
        super().__init__(QFileDialog.Directory, path, start_dir=start_dir, parent=parent)


class FileInputWidget(FileSystemInputWidget):
    def __init__(self, path: os.PathLike = None, *, start_dir: os.PathLike = None, parent=None):
        super().__init__(QFileDialog.ExistingFile, path, start_dir=start_dir, parent=parent)
