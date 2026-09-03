import os
from hashlib import md5
from pathlib import Path

from PySide6.QtCore import QRegularExpression, QStandardPaths
from PySide6.QtGui import QRegularExpressionValidator

from . import settings


class PathnameValidator(QRegularExpressionValidator):
    def __init__(self, parent=None):
        pattern = r"^[^\\/:*?\"<>|]+$"
        super().__init__(QRegularExpression(pattern), parent)


def relpath(path: os.PathLike, fspath: bool = False, posix: bool = False) -> Path | str:
    path = Path(path)

    yolov9_dir = settings.value("yolov9_dir", None)
    if yolov9_dir and path.is_relative_to(yolov9_dir):
        path = path.relative_to(yolov9_dir)

    if fspath:
        return os.fspath(path)

    return path.as_posix() if posix else path


def abspath(path: os.PathLike, fspath: bool = False, posix: bool = False) -> Path | str:
    path = Path(path)

    yolov9_dir = settings.value("yolov9_dir", None)
    if yolov9_dir and not path.is_absolute():
        path = Path(yolov9_dir, path)

    if fspath:
        return os.fspath(path)

    return path.as_posix() if posix else path


def argpath(path: os.PathLike, fspath: bool = False, posix: bool = False) -> Path | str:
    path = relpath(path)

    # # yolov9の['data', 'models', 'utils']にあるファイルは検索されるのでファイル名のみ
    # if not path.is_absolute() and path.parts[0] in ["data", "models", "utils"]:
    #     path = Path(path.name)

    if fspath:
        return os.fspath(path)

    return path.as_posix() if posix else path


def file_hash(startfile: Path, default: str = "") -> str:
    if not startfile.exists():
        return default

    with open(startfile, "rb") as f:
        return md5(f.read()).hexdigest()


def file_mtime(startfile: Path, default: float = 0) -> float:
    if not startfile.exists():
        return default

    return startfile.stat().st_mtime


def getDesktopDir() -> os.PathLike | None:
    desktopDirs = [
        Path(QStandardPaths.writableLocation(QStandardPaths.DesktopLocation)),
        Path(QStandardPaths.writableLocation(QStandardPaths.HomeLocation), "OneDrive/Desktop"),
        Path(QStandardPaths.writableLocation(QStandardPaths.HomeLocation), "Desktop"),
        Path(QStandardPaths.writableLocation(QStandardPaths.HomeLocation)),
    ]

    for desktopDir in desktopDirs:
        if Path(desktopDir).exists():
            return desktopDir

    return None
