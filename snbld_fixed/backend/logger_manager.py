# -*- coding: utf-8 -*-
"""
backend/logger_manager.py
Менеджер системы логирования
Централизованное управление логгерами по категориям
"""

import sys
import os
import logging
from logging.handlers import TimedRotatingFileHandler, RotatingFileHandler
from typing import Dict, Optional
from pathlib import Path


# Константы логирования
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
LOG_ROTATION_INTERVAL = 10  # минут
LOG_ROTATION_BACKUP_COUNT = 3  # количество резервных копий
LOG_MAX_BYTES = 10 * 1024 * 1024  # 10 MB для размерной ротации

# Категории логирования
LOG_CATEGORIES = {
    'macros': 'macros.log',
    'errors': 'errors.log',
    'ocr': 'ocr.log',
    'network': 'network.log',
    'settings': 'settings.log',
    'debug': 'debug.log',
    'shiboken': 'shiboken.log',
}

# Уровни логирования по умолчанию
DEFAULT_LOG_LEVELS = {
    'macros': logging.INFO,      # Все сообщения макросов
    'errors': logging.WARNING,   # WARNING и ERROR (не только ERROR!)
    'ocr': logging.DEBUG,        # Полная отладка OCR
    'network': logging.INFO,
    'settings': logging.INFO,
    'debug': logging.DEBUG,
    'shiboken': logging.WARNING,
}


class LoggerManager:
    """
    Менеджер системы логирования.
    Предоставляет централизованное управление логгерами по категориям.
    
    Использование:
        logger = LoggerManager.get_logger('macros')
        logger.info('Сообщение')
    """
    
    _instance: Optional['LoggerManager'] = None
    _loggers: Dict[str, logging.Logger] = {}
    _log_dir: str = 'logs'
    _initialized: bool = False
    
    def __new__(cls) -> 'LoggerManager':
        """Реализация паттерна Singleton"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            self._setup_log_directory()
            self._initialize_all_loggers()
            self._initialized = True
    
    @classmethod
    def get_logger(cls, category: str = 'debug') -> logging.Logger:
        """
        Получает логгер по категории.
        
        Args:
            category: Категория логгера (macros, errors, ocr, network, settings, debug, shiboken)
        
        Returns:
            Настроенный логгер
        
        Example:
            logger = LoggerManager.get_logger('macros')
            logger.info('Макрос запущен')
        """
        if cls._instance is None:
            cls._instance = LoggerManager()
        
        if category not in LOG_CATEGORIES:
            category = 'debug'
        
        if category not in cls._loggers:
            cls._instance._create_logger(category)
        
        return cls._loggers[category]
    
    @classmethod
    def set_log_level(cls, category: str, level: int) -> None:
        """
        Устанавливает уровень логирования для категории.
        
        Args:
            category: Категория логгера
            level: Уровень логирования (logging.DEBUG, logging.INFO, etc.)
        """
        if cls._instance is None:
            cls._instance = LoggerManager()
        
        if category in cls._loggers:
            cls._loggers[category].setLevel(level)
    
    @classmethod
    def get_log_file_path(cls, category: str) -> str:
        """
        Возвращает полный путь к файлу лога категории.
        
        Args:
            category: Категория логгера
        
        Returns:
            Полный путь к файлу лога
        """
        log_file = LOG_CATEGORIES.get(category, 'debug.log')
        return os.path.join(cls._log_dir, log_file)
    
    @classmethod
    def cleanup_old_logs(cls, days: int = 7) -> int:
        """
        Удаляет старые лог-файлы.
        
        Args:
            days: Количество дней, за которые хранить логи
        
        Returns:
            Количество удалённых файлов
        """
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
        """Создаёт директорию для логов если она не существует"""
        try:
            app_dir = os.getcwd()
            
            temp_dir = os.environ.get('TEMP', '') or os.environ.get('TMP', '')
            if temp_dir and app_dir.startswith(temp_dir):
                if hasattr(sys, 'argv') and sys.argv and sys.argv[0]:
                    app_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
                    print(f"[DEBUG LOGS] Used sys.argv[0]: {app_dir}")
                else:
                    app_dir = os.path.dirname(sys.executable)
                    print(f"[DEBUG LOGS] Used sys.executable: {app_dir}")
            else:
                print(f"[DEBUG LOGS] Used cwd: {app_dir}")
            
            self._log_dir = os.path.join(app_dir, 'logs')
            print(f"[DEBUG LOGS] Final log directory: {self._log_dir}")
            Path(self._log_dir).mkdir(parents=True, exist_ok=True)
        except Exception as e:
            self._log_dir = 'logs'
            print(f"[DEBUG LOGS] Error: {e}, fallback to: {self._log_dir}")
            Path(self._log_dir).mkdir(parents=True, exist_ok=True)
    
    def _initialize_all_loggers(self) -> None:
        """Инициализирует все логгеры по категориям"""
        for category in LOG_CATEGORIES:
            self._create_logger(category)
    
    def _create_logger(self, category: str) -> logging.Logger:
        """
        Создаёт и настраивает логгер для категории.
        
        Args:
            category: Категория логгера
        
        Returns:
            Настроенный логгер
        """
        logger = logging.getLogger(f"snbld.{category}")
        logger.setLevel(DEFAULT_LOG_LEVELS.get(category, logging.DEBUG))
        
        # Пропускаем если уже инициализировано
        if logger.handlers:
            return logger

        # Очищаем существующие обработчики
        logger.handlers.clear()

        # Создаём форматтер
        formatter = logging.Formatter(LOG_FORMAT, datefmt=LOG_DATE_FORMAT)

        # === Консольный обработчик (для отладки) ===
        # Для OCR ставим WARNING чтобы не спамил в консоль (логи всё равно пишутся в файл)
        console_level = logging.WARNING if category == 'ocr' else DEFAULT_LOG_LEVELS.get(category, logging.DEBUG)
        console_handler = logging.StreamHandler()
        console_handler.setLevel(console_level)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        
        # === Файловый обработчик с ротацией по времени и размеру ===
        try:
            log_file = LOG_CATEGORIES.get(category, 'debug.log')
            file_path = os.path.join(self._log_dir, log_file)
            
            # Используем комбинированную ротацию: по времени + по размеру
            file_handler = TimedRotatingFileHandler(
                file_path,
                when='M',
                interval=LOG_ROTATION_INTERVAL,
                backupCount=LOG_ROTATION_BACKUP_COUNT,
                encoding='utf-8',
                delay=True
            )
            file_handler.setLevel(DEFAULT_LOG_LEVELS.get(category, logging.DEBUG))
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
            
        except Exception as e:
            # Если не удалось создать файловый обработчик - пишем в консоль
            print(f"Ошибка создания файлового логгера для {category}: {e}")
        
        self._loggers[category] = logger
        return logger


# ==================== УДОБНЫЕ ФУНКЦИИ-ШОРТКАТЫ ====================

def get_logger(category: str = 'debug') -> logging.Logger:
    """
    Получает логгер по категории (shortcut).
    
    Args:
        category: Категория логгера
    
    Returns:
        Настроенный логгер
    """
    return LoggerManager.get_logger(category)


def log_error(error: Exception, context: str = "") -> None:
    """
    Логирует ошибку в errors.log.
    
    Args:
        error: Исключение для логирования
        context: Контекст ошибки
    """
    logger = LoggerManager.get_logger('errors')
    logger.error(f"{context}: {type(error).__name__}: {error}", exc_info=True)


def log_macros(message: str, level: int = logging.INFO) -> None:
    """Логирует сообщение в macros.log"""
    logger = LoggerManager.get_logger('macros')
    logger.log(level, message)


def log_ocr(message: str, level: int = logging.DEBUG) -> None:
    """Логирует сообщение в ocr.log"""
    logger = LoggerManager.get_logger('ocr')
    logger.log(level, message)


def log_network(message: str, level: int = logging.INFO) -> None:
    """Логирует сообщение в network.log"""
    logger = LoggerManager.get_logger('network')
    logger.log(level, message)


def log_settings(message: str, level: int = logging.INFO) -> None:
    """Логирует сообщение в settings.log"""
    logger = LoggerManager.get_logger('settings')
    logger.log(level, message)


def log_debug(message: str) -> None:
    """Логирует сообщение в debug.log"""
    logger = LoggerManager.get_logger('debug')
    logger.debug(message)


import zipfile
import json
import platform
import psutil
from datetime import datetime

# Импортируем sys для определения режима работы
import sys


# ==================== СИСТЕМА СБОРА ОТЧЁТОВ ====================

def generate_support_report() -> str:
    """
    Генерирует полный отчёт поддержки со всеми логами, конфигурацией и системной информацией.
    
    Returns:
        Путь к созданному zip архиву с отчётом
    """
    logger = get_logger('debug')
    logger.info("🔧 Генерация отчёта поддержки")
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_filename = f"snbld_report_{timestamp}.zip"
    report_path = os.path.join(LoggerManager._log_dir, report_filename)
    
    try:
        with zipfile.ZipFile(report_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            
            # 1. Добавляем все лог файлы
            for category, filename in LOG_CATEGORIES.items():
                log_path = os.path.join(LoggerManager._log_dir, filename)
                if os.path.exists(log_path):
                    zipf.write(log_path, f"logs/{filename}")
            
            # 2. Создаём и добавляем системный отчёт
            system_report = {
                "timestamp": timestamp,
                "version": "1.0.0",
                "platform": {
                    "system": platform.system(),
                    "release": platform.release(),
                    "version": platform.version(),
                    "machine": platform.machine(),
                    "processor": platform.processor()
                },
                "python": {
                    "version": sys.version,
                    "frozen": getattr(sys, 'frozen', False),
                    "executable": sys.executable
                },
                "memory": {
                    "total": psutil.virtual_memory().total,
                    "available": psutil.virtual_memory().available,
                    "percent": psutil.virtual_memory().percent
                },
                "cpu": {
                    "count": psutil.cpu_count(),
                    "percent": psutil.cpu_percent(interval=0.5)
                },
                "disk": {
                    "total": psutil.disk_usage('.').total,
                    "free": psutil.disk_usage('.').free,
                    "percent": psutil.disk_usage('.').percent
                },
                "logs_size": {}
            }
            
            # Добавляем размеры логов
            for category, filename in LOG_CATEGORIES.items():
                log_path = os.path.join(LoggerManager._log_dir, filename)
                if os.path.exists(log_path):
                    system_report['logs_size'][category] = os.path.getsize(log_path)
            
            # Записываем системный отчёт
            system_report_json = json.dumps(system_report, indent=2, ensure_ascii=False)
            zipf.writestr("system_report.json", system_report_json)
            
            # 3. Добавляем настройки если они существуют
            settings_path = "settings.json"
            if os.path.exists(settings_path):
                with open(settings_path, 'r', encoding='utf-8') as f:
                    settings_data = f.read()
                    # Удаляем чувствительные данные
                    try:
                        settings = json.loads(settings_data)
                        for key in list(settings.keys()):
                            if 'key' in key.lower() or 'password' in key.lower() or 'token' in key.lower():
                                settings[key] = "[REMOVED]"
                        settings_data = json.dumps(settings, indent=2, ensure_ascii=False)
                    except:
                        pass
                zipf.writestr("settings.json", settings_data)
            
            # 4. Добавляем файл с описанием
            readme = """
            Отчёт поддержки snbld
            =====================
            
            Этот отчёт содержит:
            - Все логи программы
            - Системную информацию
            - Настройки программы (без чувствительных данных)
            
            Для анализа распакуйте архив и посмотрите файлы в папке logs/
            """
            zipf.writestr("README.txt", readme)
        
        logger.info(f"✅ Отчёт поддержки создан: {report_path}")
        return report_path
    
    except Exception as e:
        logger.error(f"❌ Ошибка генерации отчёта: {e}", exc_info=True)
        return ""


def send_support_report(report_path: str, user_comment: str = "") -> bool:
    """
    Отправляет отчёт поддержки на сервер.
    
    Args:
        report_path: Путь к zip отчёту
        user_comment: Комментарий пользователя
        
    Returns:
        True если отправка успешна
    """
    if not os.path.exists(report_path):
        return False
    
    logger = get_logger('debug')
    logger.info(f"📤 Отправка отчёта поддержки: {os.path.basename(report_path)}")
    
    try:
        import requests
        
        url = "https://snbld.ru/api/report"
        files = {'report': open(report_path, 'rb')}
        data = {
            'comment': user_comment,
            'version': '1.0.0',
            'timestamp': datetime.now().isoformat()
        }
        
        response = requests.post(url, files=files, data=data, timeout=10)
        response.raise_for_status()
        
        logger.info("✅ Отчёт успешно отправлен")
        return True
        
    except Exception as e:
        logger.error(f"❌ Ошибка отправки отчёта: {e}")
        return False


def get_crash_logs(last_minutes: int = 15) -> list:
    """
    Получает последние логи ошибок для отображения пользователю.
    
    Args:
        last_minutes: Количество минут для анализа
        
    Returns:
        Список ошибок
    """
    errors = []
    errors_path = os.path.join(LoggerManager._log_dir, 'errors.log')
    
    if not os.path.exists(errors_path):
        return errors
    
    try:
        import re
        from datetime import timedelta
        
        now = datetime.now()
        time_regex = re.compile(r'^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})')
        
        with open(errors_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        for line in reversed(lines):
            match = time_regex.match(line)
            if match:
                log_time = datetime.strptime(match.group(1), "%Y-%m-%d %H:%M:%S")
                if now - log_time > timedelta(minutes=last_minutes):
                    break
                errors.append(line.strip())
        
        return errors
    
    except:
        return errors


def shutdown_loggers() -> None:
    """
    Корректно закрывает все логгеры и обработчики перед выходом из программы.
    Должно вызываться при завершении работы приложения.
    """
    try:
        for logger in LoggerManager._loggers.values():
            for handler in logger.handlers:
                try:
                    handler.acquire()
                    handler.flush()
                    handler.close()
                except:
                    pass
                finally:
                    handler.release()
            logger.handlers.clear()
        
        LoggerManager._loggers.clear()
        logging.shutdown()
    except Exception as e:
        print(f"Ошибка завершения логгеров: {e}")


def flush_all_loggers() -> None:
    """
    Принудительно сбрасывает буферы всех логгеров на диск.
    Используется перед критическими операциями.
    """
    try:
        for logger in LoggerManager._loggers.values():
            for handler in logger.handlers:
                try:
                    handler.flush()
                except:
                    pass
    except Exception as e:
        print(f"Ошибка сброса буферов логгеров: {e}")
