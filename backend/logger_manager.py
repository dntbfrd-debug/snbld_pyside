import sys
import os
import logging
from logging.handlers import TimedRotatingFileHandler
from typing import Dict, Optional
from pathlib import Path


LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
LOG_ROTATION_INTERVAL = 10
LOG_ROTATION_BACKUP_COUNT = 3

LOG_CATEGORIES = {
    'debug': 'debug.log',
    'errors': 'errors.log',
    'macros': 'macros.log',
    'ocr': 'ocr.log',
    'network': 'network.log',
    'settings': 'settings.log',
    'shiboken': 'shiboken.log',
    'backend': 'backend.log',
    'auth': 'auth.log',
    'input': 'input.log',
    'hotkey': 'hotkey.log',
    'input_blocker': 'input_blocker.log',
    'qml_bridge': 'qml_bridge.log',
    'attach_thread': 'attach_thread.log',
        'keyboard_shim': 'keyboard_shim.log',
    'hooks_guard': 'hooks_guard.log',
    'mouse': 'mouse.log',
    'resource_utils': 'resource_utils.log',
    'file_utils': 'file_utils.log',
    'threads': 'threads.log',
    'utils': 'utils.log',
    'session': 'session.log',
    'updater': 'updater.log',
    'other': 'other.log',
}

DEFAULT_LOG_LEVELS = {
    'debug': logging.DEBUG,
    'errors': logging.WARNING,
    'macros': logging.DEBUG,
    'ocr': logging.DEBUG,
    'network': logging.INFO,
    'settings': logging.INFO,
    'shiboken': logging.WARNING,
    'backend': logging.DEBUG,
    'auth': logging.INFO,
    'input': logging.DEBUG,
    'hotkey': logging.DEBUG,
    'input_blocker': logging.DEBUG,
    'qml_bridge': logging.DEBUG,
    'attach_thread': logging.DEBUG,
    'keyboard_shim': logging.DEBUG,
    'hooks_guard': logging.DEBUG,
    'mouse': logging.DEBUG,
    'resource_utils': logging.DEBUG,
    'file_utils': logging.DEBUG,
    'threads': logging.DEBUG,
    'utils': logging.DEBUG,
    'session': logging.DEBUG,
    'updater': logging.DEBUG,
}


class LoggerManager:
    _instance: Optional['LoggerManager'] = None
    _loggers: Dict[str, logging.Logger] = {}
    _log_dir: str = 'logs'
    _initialized: bool = False
    _original_get_logger: Optional[object] = None

    def __new__(cls) -> 'LoggerManager':
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not self._initialized:
            self._setup_log_directory()
            self._initialize_all_loggers()
            self._setup_root_error_handler()
            self._patch_logging_module()
            self._initialized = True

    def _setup_root_error_handler(self):
        formatter = logging.Formatter(LOG_FORMAT, datefmt=LOG_DATE_FORMAT)
        try:
            file_path = os.path.join(self._log_dir, 'errors.log')
            handler = TimedRotatingFileHandler(
                file_path,
                when='M',
                interval=LOG_ROTATION_INTERVAL * 6,
                backupCount=LOG_ROTATION_BACKUP_COUNT,
                encoding='utf-8',
                delay=True,
            )
            handler.setLevel(logging.ERROR)
            handler.setFormatter(formatter)
            root = logging.getLogger()
            root.addHandler(handler)
        except Exception:
            pass

    def _patch_logging_module(self):
        if LoggerManager._original_get_logger is not None:
            return
        LoggerManager._original_get_logger = logging.getLogger

        def _patched_get_logger(name=None):
            logger = LoggerManager._original_get_logger(name)
            cls = LoggerManager
            if cls._instance is None:
                cls._instance = LoggerManager()
            if name and not name.startswith('snbld.') and not logger.handlers:
                cls._instance._ensure_file_handler(logger, name)
            return logger

        logging.getLogger = _patched_get_logger

    @classmethod
    def get_logger(cls, category: str = 'debug') -> logging.Logger:
        if cls._instance is None:
            cls._instance = LoggerManager()
        if category not in LOG_CATEGORIES:
            category = 'other'
        if category not in cls._loggers:
            cls._instance._create_logger(category)
        return cls._loggers[category]

    def _ensure_file_handler(self, logger: logging.Logger, name: str):
        for handler in logger.handlers:
            if isinstance(handler, TimedRotatingFileHandler):
                return
        safe_name = name.replace('.', '_').replace(' ', '_') or 'unknown'
        formatter = logging.Formatter(LOG_FORMAT, datefmt=LOG_DATE_FORMAT)
        try:
            file_path = os.path.join(self._log_dir, f'{safe_name}.log')
            file_handler = TimedRotatingFileHandler(
                file_path,
                when='M',
                interval=LOG_ROTATION_INTERVAL,
                backupCount=LOG_ROTATION_BACKUP_COUNT,
                encoding='utf-8',
                delay=True,
            )
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        except Exception:
            pass

    @classmethod
    def set_log_level(cls, category: str, level: int) -> None:
        if cls._instance is None:
            cls._instance = LoggerManager()
        if category in cls._loggers:
            cls._loggers[category].setLevel(level)

    @classmethod
    def cleanup_old_logs(cls, days: int = 7) -> int:
        import time
        deleted_count = 0
        current_time = time.time()
        max_age_seconds = days * 24 * 60 * 60
        try:
            for filename in os.listdir(cls._log_dir):
                if not filename.endswith('.log'):
                    continue
                file_path = os.path.join(cls._log_dir, filename)
                file_age = current_time - os.path.getmtime(file_path)
                if file_age > max_age_seconds:
                    os.remove(file_path)
                    deleted_count += 1
        except Exception as e:
            logger = cls.get_logger('errors')
            logger.error(f"Ошибка очистки старых логов: {e}")
        return deleted_count

    def _setup_log_directory(self) -> None:
        try:
            is_packaged = (getattr(sys, 'frozen', False) or
                           hasattr(sys, 'compiled') or
                           hasattr(sys, '_MEIPASS'))
            if is_packaged:
                from utils.file_utils import get_install_dir
                app_dir = str(get_install_dir())
            else:
                app_dir = os.getcwd()
                temp_dir = os.environ.get('TEMP', '') or os.environ.get('TMP', '')
                if temp_dir and app_dir.startswith(temp_dir):
                    if hasattr(sys, 'argv') and sys.argv and sys.argv[0]:
                        app_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
                    else:
                        app_dir = os.path.dirname(sys.executable)
            self._log_dir = os.path.join(app_dir, 'logs')
            Path(self._log_dir).mkdir(parents=True, exist_ok=True)
        except Exception:
            self._log_dir = 'logs'
            Path(self._log_dir).mkdir(parents=True, exist_ok=True)

    def _initialize_all_loggers(self) -> None:
        for category in LOG_CATEGORIES:
            self._create_logger(category)

    def _create_logger(self, category: str) -> logging.Logger:
        logger = logging.getLogger(f"snbld.{category}")
        logger.setLevel(DEFAULT_LOG_LEVELS.get(category, logging.DEBUG))
        if logger.handlers:
            return logger
        logger.handlers.clear()
        formatter = logging.Formatter(LOG_FORMAT, datefmt=LOG_DATE_FORMAT)
        console_level = logging.WARNING if category == 'ocr' else DEFAULT_LOG_LEVELS.get(category, logging.DEBUG)
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(console_level)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        try:
            log_file = LOG_CATEGORIES.get(category, f'{category}.log')
            file_path = os.path.join(self._log_dir, log_file)
            file_handler = TimedRotatingFileHandler(
                file_path,
                when='M',
                interval=LOG_ROTATION_INTERVAL,
                backupCount=LOG_ROTATION_BACKUP_COUNT,
                encoding='utf-8',
                delay=True,
            )
            file_handler.setLevel(DEFAULT_LOG_LEVELS.get(category, logging.DEBUG))
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        except Exception:
            pass
        self._loggers[category] = logger
        return logger


def get_logger(category: str = 'debug') -> logging.Logger:
    return LoggerManager.get_logger(category)


def log_error(error: Exception, context: str = "") -> None:
    logger = LoggerManager.get_logger('errors')
    logger.error(f"{context}: {type(error).__name__}: {error}", exc_info=True)


def shutdown_loggers() -> None:
    try:
        for logger in list(LoggerManager._loggers.values()):
            for handler in list(logger.handlers):
                try:
                    handler.flush()
                    handler.close()
                except Exception:
                    pass
            logger.handlers.clear()
        LoggerManager._loggers.clear()
        logging.shutdown()
    except Exception:
        pass
