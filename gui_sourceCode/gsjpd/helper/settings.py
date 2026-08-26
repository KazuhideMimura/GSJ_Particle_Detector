from contextlib import contextmanager

from PySide6.QtWidgets import QApplication


@contextmanager
def group(group: str, *, sync: bool = False):
    instance = QApplication.instance().settings
    instance.beginGroup(group)

    try:
        yield instance
    finally:
        instance.endGroup()
        if sync:
            instance.sync()

        instance = None


def beginGroup(group: str):
    instance = QApplication.instance().settings
    instance.beginGroup(group)
    return instance


def endGroup():
    QApplication.instance().settings.endGroup()


def sync():
    QApplication.instance().settings.sync()


def value(key: str, default=None, *, type=None, group: str = None):
    if group is not None:
        beginGroup(group)

    if type is not None:
        value = QApplication.instance().settings.value(key, default, type)
    else:
        value = QApplication.instance().settings.value(key, default)

    if group is not None:
        endGroup()

    return value


def setValue(key: str, value, *, group: str = None, sync: bool = False):
    if group is not None:
        beginGroup(group)

    QApplication.instance().settings.setValue(key, value)

    if group is not None:
        endGroup()

    if sync:
        sync()


def safeInt(value: str, default: int = 0) -> int:
    try:
        return int(value)
    except ValueError:
        return default


def safeFloat(value: str, default: float = 0.0) -> float:
    try:
        return float(value)
    except ValueError:
        return default
