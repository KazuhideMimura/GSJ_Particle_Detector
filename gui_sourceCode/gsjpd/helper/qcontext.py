from contextlib import contextmanager

from PySide6.QtCore import QObject


@contextmanager
def QContext(*object: QObject):
    try:
        yield object if len(object) > 1 else object[0]
    finally:
        object = None
        pass
