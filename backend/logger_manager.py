import sys
import os
import logging
from logging.handlers import RotatingFileHandler

LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
LOG_MAX_BYTES = 10 * 1024 * 1024
LOG_BACKUP_COUNT = 2

_log_dir = 'logs'
_initialized = False
_log_levels = {}


def _resolve_log_dir():
    global _log_dir
    try:
        is_packaged = (getattr(sys, 'frozen', False) or
                       hasattr(sys, 'compiled') or
                       hasattr(sys, '_MEIPASS'))
        if is_packaged:
            from utils.paths import get_install_dir
            app_dir = str(get_install_dir())
        else:
            app_dir = os.getcwd()
            temp_dir = os.environ.get('TEMP', '') or os.environ.get('TMP', '')
            if temp_dir and app_dir.startswith(temp_dir):
                if hasattr(sys, 'argv') and sys.argv and sys.argv[0]:
                    app_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
                else:
                    app_dir = os.path.dirname(sys.executable)
        _log_dir = os.path.join(app_dir, 'logs')
    except Exception:
        _log_dir = 'logs'
    from pathlib import Path
    Path(_log_dir).mkdir(parents=True, exist_ok=True)


def setup_logging():
    global _initialized
    if _initialized:
        return
    _initialized = True

    _resolve_log_dir()

    formatter = logging.Formatter(LOG_FORMAT, datefmt=LOG_DATE_FORMAT)

    file_path = os.path.join(_log_dir, 'snbld.log')
    file_handler = RotatingFileHandler(
        file_path,
        maxBytes=LOG_MAX_BYTES,
        backupCount=LOG_BACKUP_COUNT,
        encoding='utf-8',
        delay=True,
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.WARNING)
    console_handler.setFormatter(formatter)

    root = logging.getLogger()
    root.setLevel(logging.DEBUG)
    root.handlers.clear()
    root.addHandler(file_handler)
    root.addHandler(console_handler)


class LoggerManager:
    _log_dir = _log_dir
    _loggers = {}

    def __init__(self):
        setup_logging()

    @classmethod
    def get_logger(cls, category='debug'):
        setup_logging()
        logger = logging.getLogger(f"snbld.{category}")
        level = _log_levels.get(category, logging.DEBUG)
        logger.setLevel(level)
        cls._loggers[category] = logger
        return logger

    @classmethod
    def set_log_level(cls, category, level):
        _log_levels[category] = level
        logger = logging.getLogger(f"snbld.{category}")
        logger.setLevel(level)


def get_logger(category='debug'):
    setup_logging()
    logger = logging.getLogger(f"snbld.{category}")
    level = _log_levels.get(category, logging.DEBUG)
    logger.setLevel(level)
    return logger


def log_error(error, context=''):
    logger = get_logger('debug')
    logger.error(f"{context}: {type(error).__name__}: {error}", exc_info=True)


def shutdown_loggers():
    try:
        logging.shutdown()
    except Exception:
        pass
