import os
from logging import Formatter, Logger
from logging import getLogger as _getLogger
from logging.handlers import RotatingFileHandler

MiB = 1024**2


def getLogger(
    filename: os.PathLike = None,
    level: int | str = None,
    **kwargs,
):
    logger = _getLogger(os.fspath(filename))
    if level is not None:
        logger.setLevel(level)

    # loggerにRotatingFileHandlerが設定されていない場合は追加
    if not any(isinstance(handler, RotatingFileHandler) for handler in logger.handlers):
        maxBytes = kwargs.get("maxBytes", 2 * MiB)
        backupCount = kwargs.get("backupCount", 5)
        delay = kwargs.get("delay", True)
        errors = kwargs.get("errors", "ignore")

        handler = RotatingFileHandler(
            filename,
            maxBytes=maxBytes,
            backupCount=backupCount,
            encoding="utf-8",
            delay=delay,
            errors=errors,
        )
        if level is not None:
            handler.setLevel(level)

        formatter = Formatter("[%(asctime)s] %(levelname)s %(message)s", datefmt="%a %b %d %X")
        handler.setFormatter(formatter)

        logger.addHandler(handler)

    return logger


def closeLogger(logger: Logger | None):
    if logger is None:
        return

    handlers = logger.handlers.copy()

    for handler in handlers:
        try:
            handler.close()
            logger.removeHandler(handler)
        except Exception:
            pass
        finally:
            del handler
