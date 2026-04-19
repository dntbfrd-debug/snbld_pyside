# -*- coding: utf-8 -*-
import sys
import os
import re
import atexit
import win32api
import win32con
import win32event
import winerror
import traceback
from datetime import datetime

# Load environment variables from .env file if it exists
def _load_env_file():
    env_path = os.path.join(os.path.dirname(__file__), '.env')
    if os.path.exists(env_path):
        try:
            with open(env_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        os.environ[key] = value
            print("[ENV] Loaded environment variables from .env file")
        except Exception as e:
            print(f"[ENV] Warning: Could not load .env file: {e}")

_load_env_file()

# Debug: Check if critical environment variables are loaded
print(f"[ENV] TELEGRAM_BOT_TOKEN set: {bool(os.environ.get('TELEGRAM_BOT_TOKEN'))}")
print(f"[ENV] TELEGRAM_CHAT_ID set: {bool(os.environ.get('TELEGRAM_CHAT_ID'))}")
print(f"[ENV] SELECTEL_ACCESS_KEY set: {bool(os.environ.get('SELECTEL_ACCESS_KEY'))}")
print(f"[ENV] SELECTEL_SECRET_KEY set: {bool(os.environ.get('SELECTEL_SECRET_KEY'))}")

# Статические импорты для Nuitka
from macros_core import SimpleMacro, SkillMacro, ZoneMacro, BuffMacro, click_at_position

# ==================== ПРЕДОТВРАЩЕНИЕ НЕСКОЛЬКИХ ЗАПУСКОВ ====================
mutex = win32event.CreateMutex(None, 1, "snbld_pyside_single_instance_mutex")
if win32api.GetLastError() == winerror.ERROR_ALREADY_EXISTS:
    win32api.MessageBox(0, "Программа уже запущена.\nПроверьте трей системного трея.", "SNBLD", 0x40 | 0x1000)
    sys.exit(1)

def _release_mutex():
    """Гарантированное освобождение мьютекса при выходе"""
    try:
        win32event.ReleaseMutex(mutex)
    except:
        pass

def _get_app_dir():
    """Возвращает папку с EXE-файлом (или проекта в режиме разработки)"""
    # Nuitka onefile: sys._MEIPASS set, sys.executable указывает в TEMP
    if hasattr(sys, '_MEIPASS'):
        if hasattr(sys, 'argv') and sys.argv and sys.argv[0]:
            return os.path.dirname(os.path.abspath(sys.argv[0]))
    
    # Nuitka standalone non-onefile: sys.frozen=True
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    
    # Fallback для Nuitka: используем sys.argv[0] если это exe
    if hasattr(sys, 'argv') and sys.argv and sys.argv[0].endswith('.exe'):
        return os.path.dirname(sys.argv[0])
    
    # Для onefile распаковки - проверяем cwd
    if 'TEMP' in os.getcwd() or 'TMP' in os.getcwd():
        if hasattr(sys, 'argv') and sys.argv and sys.argv[0]:
            return os.path.dirname(os.path.abspath(sys.argv[0]))
    
    # Режим разработки
    return os.path.dirname(os.path.abspath(__file__))

atexit.register(_release_mutex)

# ==================== ГЛОБАЛЬНЫЙ ОБРАБОТЧИК ИСКЛЮЧЕНИЙ ====================
def _global_exception_handler(exc_type, exc_value, exc_traceback):
    """Глобальный обработчик крашей - пишет крашлог и показывает сообщение"""
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    
    crash_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    crash_file = os.path.join(_get_app_dir(), f"crash_{crash_time}.log")
    
    try:
        with open(crash_file, 'w', encoding='utf-8') as f:
            f.write("=== SNBLD CRASH REPORT ===\n")
            f.write(f"Time: {crash_time}\n")
            f.write(f"Version: {open('version.json').read() if os.path.exists('version.json') else 'unknown'}\n")
            f.write("\n=== TRACEBACK ===\n")
            traceback.print_exception(exc_type, exc_value, exc_traceback, file=f)
    except:
        pass
    
    error_msg = f"Произошла критическая ошибка.\nКрашлог сохранён:\n{crash_file}\n\nОшибка: {exc_value}"
    try:
        win32api.MessageBox(0, error_msg, "SNBLD - Критическая ошибка", 0x10 | 0x1000)
    except:
        pass
    
    # Запускаем очистку хуков перед выходом
    try:
        import low_level_hook
        low_level_hook.unhook_all()
    except:
        pass
    
    sys.exit(1)

sys.excepthook = _global_exception_handler

# ==================== ПРОВЕРКА ПРАВ АДМИНИСТРАТОРА ====================
def _is_admin():
    """Проверяет запущена ли программа с правами администратора"""
    import ctypes
    try:
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except:
        return False

# Проверяем флаг --admin-requested, чтобы избежать бесконечного цикла
admin_requested = '--admin-requested' in sys.argv

if not _is_admin():
    if admin_requested:
        # Мы уже пытались перезапуститься с админ правами, но пользователь отменил или что-то не так
        # Просто продолжаем работу без админ прав
        pass
    else:
        result = win32api.MessageBox(
            0,
            "Рекомендуется запускать программу с правами Администратора.\nБез них работа хуков клавиатуры и мыши может быть нестабильной.\n\nЗапустить повторно с правами Администратора?",
            "SNBLD - Внимание",
            0x30 | 0x4 | 0x1000
        )
        if result == 6: # IDYES
            # Добавляем флаг чтобы избежать бесконечного цикла
            new_args = list(sys.argv)
            if '--admin-requested' not in new_args:
                new_args.append('--admin-requested')
            
            # Отладочная информация
            print(f"[DEBUG] sys.frozen: {getattr(sys, 'frozen', False)}")
            print(f"[DEBUG] sys.executable: {sys.executable}")
            print(f"[DEBUG] sys.argv[0]: {sys.argv[0]}")
            print(f"[DEBUG] os.getcwd(): {os.getcwd()}")

            # Для packaged версии используем sys.argv[0]
            # В Nuitka onefile он указывает на реальный exe (не в TEMP!)
            if getattr(sys, 'frozen', False):
                exe_path = sys.argv[0]
            else:
                exe_path = sys.executable

            # Дополнительная проверка
            if not os.path.exists(exe_path):
                exe_path = os.path.abspath(sys.argv[0])
            
            # Проверяем что файл существует
            if not os.path.exists(exe_path):
                print(f"[ADMIN] ERROR: exe not found at {exe_path}")
                win32api.MessageBox(0, f"Не удается найти exe файл:\n{exe_path}", "SNBLD Error", 0x10)
                sys.exit(1)
            
            print(f"[ADMIN] Using exe_path: {exe_path}")
            
            args_str = " ".join(new_args)
            
            # Пробуем через ShellExecuteW
            import ctypes
            ret = ctypes.windll.shell32.ShellExecuteW(
                None, "runas", exe_path, args_str, None, 1
            )
            print(f"[ADMIN] ShellExecuteW result: {ret}")
            
            if ret > 32:
                sys.exit(0)
            else:
                print(f"[ADMIN] ERROR: ShellExecuteW failed with code {ret}")

# ==================== ГАРАНТИРОВАННАЯ ОЧИСТКА ПРИ ВЫХОДЕ ====================
def _cleanup_on_exit():
    """Обработчик который гарантированно вызывается при любом выходе из программы"""
    try:
        import low_level_hook
        low_level_hook.unhook_all()
        print("[CLEANUP] Хуки клавиатуры/мыши отключены")
    except:
        pass
    
    try:
        from backend.logger_manager import shutdown_loggers
        shutdown_loggers()
    except:
        pass
    
    try:
        _release_mutex()
    except:
        pass
    
    print("[CLEANUP] Ресурсы очищены, программа завершена")

atexit.register(_cleanup_on_exit)


def _get_app_dir():
    """Возвращает папку с EXE-файлом (или проекта в режиме разработки)"""
    # Nuitka standalone: sys.frozen=True, sys.executable указывает на exe
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    
    # Fallback для Nuitka: используем sys.argv[0]
    if hasattr(sys, 'argv') and sys.argv and sys.argv[0].endswith('.exe'):
        return os.path.dirname(sys.argv[0])
    
    # Режим разработки
    return os.path.dirname(os.path.abspath(__file__))


# ==================== ОЧИСТКА СТАРЫХ ЛОГОВ ПРИ ЗАПУСКЕ ====================
# Очищаем старые логи перед запуском чтобы не засорять диск
def cleanup_old_logs():
    """Очищает содержимое логов из папки logs/ (не удаляет файлы)"""
    import glob
    logs_dir = os.path.join(_get_app_dir(), 'logs')
    os.makedirs(logs_dir, exist_ok=True)
    if os.path.exists(logs_dir):
        try:
            # Очищаем содержимое .log файлов (не удаляем сами файлы)
            for log_file in glob.glob(os.path.join(logs_dir, '*.log')):
                try:
                    with open(log_file, 'w', encoding='utf-8') as f:
                        f.write('')  # Очищаем содержимое
                except Exception:
                    pass
            # Удаляем старые ротированные логи (*.log.*)
            for old_log in glob.glob(os.path.join(logs_dir, '*.log.*')):
                try:
                    os.remove(old_log)
                except Exception:
                    pass
            print("[LOGS] Old logs cleaned (content cleared, files preserved)")
        except Exception as e:
            logger.warning(f"[LOGS] Clean error: {e}")

# Очищаем логи ДО инициализации логгера
cleanup_old_logs()

# ==================== КОНСТАНТЫ И НАСТРОЙКИ ====================

# Допустимые настройки для set_setting (тип, min, max)
ALLOWED_SETTINGS = {
    # Ресвап
    "swap_key_chant": (str, None, None),
    "swap_key_pa": (str, None, None),

    # Каст
    "base_channeling": (int, 0, 1000),
    "cooldown_margin": (float, 0.0, 5.0),
    "cast_lock_margin": (float, 0.0, 2.0),
    "cast_finish_delay": (float, 0.0, 2.0),  # Задержка после конца макроса перед сбросом cast_lock
    "castbar_enabled": (bool, None, None),
    "castbar_point": (str, None, None),
    "castbar_threshold": (int, 1, 100),
    "castbar_color": (list, None, None),
    "castbar_size": (int, 1, 10),

    # Движение
    "movement_delay_enabled": (bool, None, None),
    "movement_delay_ms": (int, 0, 5000),
    "check_distance": (bool, None, None),
    "use_castbar_detection": (bool, None, None),
    "distance_tolerance": (float, 0.0, 10.0),

    # OCR
    "ocr_scale": (int, 1, 100),
    "ocr_psm": (int, 6, 13),
    "ocr_use_morph": (bool, None, None),
    "target_interval": (float, 0.1, 1.0),

    # Сеть
    "process_name": (str, None, None),
    "server_ip": (str, None, None),
    "ping_auto": (bool, None, None),
    "ping_check_interval": (int, 1, 300),
    "average_ping": (int, 0, 1000),

    # Задержки
    "global_step_delay": (int, 0, 500),
    "first_step_delay": (int, 0, 1000),
    "use_fixed_delays": (bool, None, None),
    "use_ping_delays": (bool, None, None),

    # Горячие клавиши
    "start_all_hotkey": (str, None, None),
    "stop_all_hotkey": (str, None, None),

    # OCR области
    "mob_area": ((str, list), None, None),
    "player_area": ((str, list), None, None),

    # Окно
    "window_opacity": (float, 0.1, 1.0),
    "window_locked": (bool, None, None),
    "target_window_title": (str, None, None),

    # Баффы
    "buff_8004_click_point": (str, None, None),

    # Внешний вид
    "accent_color": (str, None, None),

    # Логирование
    "log_level_macros": (str, None, None),
    "log_level_errors": (str, None, None),
    "log_level_ocr": (str, None, None),
    "log_level_network": (str, None, None),
    "log_level_settings": (str, None, None),
    "log_level_debug": (str, None, None),
    "log_level_shiboken": (str, None, None),
}
# =====================================================================

# ==================== ФИКСИРОВАННЫЕ НАСТРОЙКИ OCR ====================
# Эти настройки жёстко прописаны в коде и не отображаются в интерфейсе
OCR_TARGET_INTERVAL = 0.2  # Интервал опроса OCR (сек) - 5 раз в секунду
OCR_DISTANCE_TOLERANCE = 1.0  # Допуск дистанции (м) - автодобег до (skill_range - 1м)
# =====================================================================

# ОТКЛЮЧЕНИЕ SHIBOKEN WARNINGS на уровне Qt
os.environ['QT_LOGGING_RULES'] = '*.debug=false;qt.qpa.*=false;shiboken=false;PySide6=false'
os.environ['QT_DEBUG_PLUGINS'] = '0'
os.environ['QML_DEBUG_DISABLED'] = '1'

# Перенаправляем stderr в файл чтобы скрыть Shiboken ошибки
class StdErrRedirect:
    def __init__(self, original, log_file=None):
        self.original = original
        self.log_file = log_file
        self._skip_patterns = [
            'Shiboken::',
            'vendor_id',
            'Cannot copy-convert',
            'NoneType',
            'QQuickAnchor',
            'Binding loop detected',
            'handler_name'
        ]
    
    def write(self, text):
        if not text:
            return
        # Пропускаем Shiboken и другие известные ошибки
        for pattern in self._skip_patterns:
            if pattern in text:
                if self.log_file:
                    try:
                        self.log_file.write(text)
                        self.log_file.flush()
                    except Exception:
                        pass
                return

        if self.original is not None:
            try:
                self.original.write(text)
            except UnicodeEncodeError:
                text_safe = text.encode('cp1251', errors='replace').decode('cp1251')
                try:
                    self.original.write(text_safe)
                except Exception:
                    pass
            except Exception:
                pass

    def flush(self):
        if self.original is not None:
            try:
                self.original.flush()
            except Exception:
                pass

# Открываем файл для логов Shiboken
try:
    shiboken_log = open('shiboken_debug.log', 'w', encoding='utf-8')
except Exception:
    shiboken_log = None

# Применяем фильтр ДО импорта PySide6
sys.stderr = StdErrRedirect(sys.stderr, shiboken_log)
sys.stdout = StdErrRedirect(sys.stdout, shiboken_log)

import json
import time
import webbrowser
import threading
import numpy as np
import win32process

from PySide6.QtCore import QObject, Signal, Slot, Property, QUrl, Qt
from PySide6.QtGui import QFont, QIcon
from PySide6.QtWidgets import QApplication
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent

try:
    from PySide6.QtQuick import QQuickStyle
    QQuickStyle.setStyle("Basic")
except ImportError:
    pass

import constants
import auth
import macros
import skill_database
import tesseract_reader
import threads
from tesseract_reader import TargetWorker
from utils import resource_path, ensure_all_resources
from utils_qml import QMLResourceHelper
from tooltips_qml import get_tooltips_provider
from backend.logger_manager import LoggerManager, get_logger, log_error

# Инициализация системы логирования
# debug: общая отладка, errors: критические ошибки (также пишутся в errors.log)
logger = get_logger('debug')
logger_errors = get_logger('errors')
logger.info("=== Запуск приложения snbld resvap QML ===")

# Дублируем ошибки в errors.log для удобства
logger_errors.info("=== Запуск приложения snbld resvap QML ===")

# Инициализация Tesseract OCR
tesseract_reader.ensure_tesseract()
logger.info("Tesseract OCR инициализирован")

import keyboard

# Низкоуровневый перехват клавиш (работает в играх!)
try:
    from low_level_hook import MouseHookManager
    LOW_LEVEL_HOOK_AVAILABLE = True
    logger.info("low_level_hook: доступен")
except Exception as e:
    LOW_LEVEL_HOOK_AVAILABLE = False
    logger.warning(f"mouse_hook: НЕ доступен: {e}")
    log_error(e, "Ошибка инициализации mouse_hook")


from backend.qml_bridge import QMLBridgeMixin

class Backend(QObject, QMLBridgeMixin):
    # Основные сигналы
    macrosChanged = Signal()
    settingsChanged = Signal()
    subscriptionChanged = Signal()
    pingUpdated = Signal(int)
    distanceUpdated = Signal(str, float, list)  # target_type, distance, numbers
    profileChanged = Signal()
    profilesChanged = Signal()  # Изменён список профилей
    notification = Signal(str, str)
    pageChangeRequested = Signal(str)
    globalStoppedChanged = Signal()
    activeBuffsUpdated = Signal()
    consoleVisibilityChanged = Signal()  # Для чекбокса консоли

    minimizeRequested = Signal()
    closeRequested = Signal()

    # Сигнал активации (для блокировки кнопок меню)
    activationStatusChanged = Signal()
    updateAvailable = Signal(dict)  # Информация о доступном обновлении
    updateDownloadProgress = Signal(int, int)  # downloaded_bytes, total_bytes
    updateDownloadComplete = Signal(str, str)  # filepath, version
    areaSelectedSignal = Signal(int, int, int, int)  # Для OCR областей
    zoneAreaSelectedSignal = Signal(list)  # Для зон макросов [x1, y1, x2, y2]

    # Сигналы для OCR
    ocrAreaSelected = Signal(str, str)  # target_type, area
    ocrTestResult = Signal(str, dict)  # target_type, result
    areaSelected = Signal(int, int, int, int)  # x1, y1, x2, y2 - для AreaSelector
    ocrCalibrationCompleted = Signal()  # Завершение комплексной калибровки OCR
    ocrCalibrationDialogRequested = Signal()  # Запрос открытия диалога калибровки

    # Сигналы для обновления индикаторов кнопок старт/стоп
    startAllPressed = Signal()
    stopAllPressed = Signal()
    macroStatusChanged = Signal()  # Сигнал для обновления статуса макросов

    # Сигнал для обновления CastBarDialog (из потока мыши)
    castbarColorCaptured = Signal(str, str)  # point, color

    # Сигналы для калибровки точки баффа
    buffCalibrationDialogRequested = Signal()  # Запрос открытия диалога
    buffCalibrationCompleted = Signal(str)  # point

    # Сигналы для диалога выбора окна
    windowsListUpdated = Signal(list)
    openWindowSelector = Signal()
    
    # Сигналы для окна (должны быть перед Properties!)
    targetWindowChanged = Signal()
    windowLockedChanged = Signal()

    @Property(list, notify=macrosChanged)
    def macros(self):
        # Возвращаем копию списка чтобы QML увидел изменения
        return list(self._macros_dicts)

    @Property(bool, notify=globalStoppedChanged)
    def global_stopped(self):
        return self._global_stopped

    @global_stopped.setter
    def global_stopped(self, value):
        if self._global_stopped != value:
            self._global_stopped = value
            self.globalStoppedChanged.emit()

    @Property(bool, notify=consoleVisibilityChanged)
    def console_visible(self):
        return self._console_visible

    @console_visible.setter
    def console_visible(self, value):
        if self._console_visible != value:
            self._console_visible = value
            self.consoleVisibilityChanged.emit()

    @Property(bool, notify=macrosChanged)
    def window_locked(self):
        return self._window_locked if hasattr(self, '_window_locked') else False

    @window_locked.setter
    def window_locked(self, value):
        if hasattr(self, '_window_locked'):
            self._window_locked = value
            self._settings["window_locked"] = value
            self.save_settings()
            self.macrosChanged.emit()

    @Property(str, notify=macrosChanged)
    def target_window_title(self):
        return self._target_window_title if hasattr(self, '_target_window_title') else ""

    @target_window_title.setter
    def target_window_title(self, value):
        if hasattr(self, '_target_window_title'):
            self._target_window_title = value
            self._settings["target_window_title"] = value
            self.save_settings()
            self.macrosChanged.emit()

    @Property(dict, notify=settingsChanged)
    def settings(self):
        return self._settings

    @Property(dict, notify=subscriptionChanged)
    def subscription_info(self):
        if not self._subscription_info or not self._subscription_info.get('valid'):
            return {}
        
        # Форматируем красивое оставшееся время
        info = dict(self._subscription_info)
        if 'expires_at' in info and info['expires_at']:
            try:
                from datetime import datetime
                expires = datetime.fromisoformat(info['expires_at'].replace('Z', '+00:00'))
                now = datetime.now(expires.tzinfo)
                delta = expires - now
                
                if delta.total_seconds() <= 0:
                    info['expires_pretty'] = "Истёк"
                else:
                    days = delta.days
                    hours = delta.seconds // 3600
                    minutes = (delta.seconds % 3600) // 60
                    
                    if days > 0:
                        info['expires_pretty'] = f"Осталось: {days} дн. {hours} ч."
                    elif hours > 0:
                        info['expires_pretty'] = f"Осталось: {hours} ч. {minutes} мин."
                    else:
                        info['expires_pretty'] = f"Осталось: {minutes} мин."
            except:
                info['expires_pretty'] = info['expires_at']
        
        return info

    @Property(str, notify=profileChanged)
    def current_profile(self):
        return self._current_profile or "не выбран"

    @Property(list, notify=profilesChanged)
    def profiles_list(self):
        """Список всех профилей"""
        return self.get_profile_list()

    @Property(int, notify=pingUpdated)
    def ping(self):
        return self._ping

    @Property(float, notify=distanceUpdated)
    def target_distance(self):
        return self._target_distance if self._target_distance is not None else 0.0

    @target_distance.setter
    def target_distance(self, value):
        if self._target_distance != value:
            self._target_distance = value
            self.distanceUpdated.emit("target", value if value is not None else 0.0)

    @Property(list, constant=True)
    def skill_list(self):
        if self.skill_db:
            return self.skill_db.get_all_skills_simple()
        return []
    
    @Property(list, notify=activeBuffsUpdated)
    def active_buffs_list(self):
        """Возвращает список активных баффов для отображения в UI"""
        buffs = []
        now = time.time()
        with self.buff_lock:
            for buff_id, info in self.active_buffs.items():
                remaining = info.get("end_time", 0) - now
                if remaining > 0:
                    buffs.append({
                        "name": info.get("name", ""),
                        "remaining": remaining,
                        "bonus": info.get("bonus", 0),
                        "icon": info.get("icon", "")
                    })
        return buffs

    @Property(str, constant=True)
    def backgroundVideoUrl(self):
        """Возвращает URL фонового видео (динамический путь для QML)"""
        url = getattr(self, '_background_video_url', '')
        # Для отладки
        import logging
        logging.getLogger('debug').info(f"[VIDEO] backgroundVideoUrl Property вызван: '{url}'")
        return url if url else ''

    def _get_background_video_url(self) -> str:
        """Получает путь к фоновому видео (работает на любой машине)"""
        import logging
        import sys
        _vlogger = logging.getLogger('debug')
        
        # DEBUG: выводим информацию о среде
        _vlogger.info(f"[VIDEO DEBUG] sys.frozen={getattr(sys, 'frozen', False)}")
        _vlogger.info(f"[VIDEO DEBUG] sys.argv[0]={sys.argv[0]}")
        _vlogger.info(f"[VIDEO DEBUG] hasattr _MEIPASS={hasattr(sys, '_MEIPASS')}")
        _vlogger.info(f"[VIDEO DEBUG] hasattr compiled={hasattr(sys, 'compiled')}")

        # MP4 приоритет (лучше поддерживается Qt FFmpeg)
        video_names = ["12.mp4", "12.webm"]

        # Используем resource_path для поддержки Nuitka onefile
        from utils import resource_path
        from utils import resource_path_debug

        for name in video_names:
            # Сначала пробуем обычный resource_path
            path = resource_path(name)
            exists = os.path.exists(path)
            _vlogger.info(f"[VIDEO] resource_path({name}) = {path}, exists={exists}")
            
            if not exists:
                # Пробуем debug версию
                path_debug = resource_path_debug(name)
                _vlogger.info(f"[VIDEO] resource_path_debug({name}) = {path_debug}")
                
                # Если debug версия нашла, используем её
                if os.path.exists(path_debug):
                    path = path_debug
                    exists = True
            
            if exists:
                # ПРАВКА: используем file://// для локальных файлов
                path_fixed = path.replace('\\', '/')
                url = f"file:///{path_fixed}"
                _vlogger.info(f"[VIDEO] ✅ Видео найдено: {url}")
                return url

        _vlogger.warning(f"[VIDEO] ❌ Видео не найдено")
        return ""

    def __init__(self):
        super().__init__()
        self._macros = []
        self._macros_dicts = []
        self._settings = {}
        self._subscription_info = {}
        self._current_profile = None
        self._target_distance = None
        self._ping = 0
        self._macro_name_for_edit = None
        self._global_stopped = True  # По умолчанию макросы ОСТАНОВЛЕНЫ
        self._console_visible = False  # По умолчанию консоль скрыта

        # Настройки окна (для save_macros/load_macros)
        self._window_locked = False
        self._target_window_title = ""
        self.window_x = 0
        self.window_y = 0

        # Директория профилей — всегда рядом с EXE (не в _MEIPASS)
        self.app_dir = _get_app_dir()
        self.profiles_dir = os.path.join(self.app_dir, "profiles")
        os.makedirs(self.profiles_dir, exist_ok=True)

        self.skill_db = None
        self.target_reader = None
        self.ping_monitor = None
        self.movement_monitor = None
        self.mouse_click_monitor = None  # Монитор кликов мыши
        self.buff_check_thread = None  # Поток проверки истечения баффов
        self.cast_lock_until = 0
        self.active_buffs = {}
        self.buff_lock = threading.Lock()

        self._hotkey_registered = set()
        self.engine = None

        # Фоновое видео (динамический путь для QML)
        self._background_video_url = self._get_background_video_url()

        # OCR данные
        self._last_ocr_numbers = []

        # Tesseract OCR (как в старом проекте)
        self.target_reader = None
        self._ocr_running = False

        # Диспетчер макросов (единая точка проверки и запуска)
        from backend.macros_dispatcher import MacroDispatcher
        self.dispatcher = MacroDispatcher(self)

        # Настройки кастбара
        self.castbar_enabled = False
        self.castbar_point = ""
        self.castbar_color = [94, 123, 104]
        self.castbar_threshold = 70
        
        # ==================== ПРОВЕРКА АКТИВАЦИИ ====================
        self._activation_key = None
        self._is_activated = False
        self._heartbeat_manager = None
        self._secrets = {}  # Токены с сервера (только в памяти!)
        self._check_activation_on_startup()
    
    # ==================== МЕТОДЫ АКТИВАЦИИ ====================
    
    def _check_activation_on_startup(self):
        """Проверяет активацию при запуске программы"""
        logger.info("[AUTH] Проверка активации...")

        # 1. Сначала пробуем загрузить и проверить сессию (самый надёжный способ)
        from auth import load_session, check_session, check_key
        session_data = load_session()

        if session_data and 'session_id' in session_data:
            logger.info(f"[AUTH] Сессия найдена: {session_data['session_id'][:16]}...")
            valid, session_info = check_session(session_data['session_id'])

            if valid and session_info:
                self._is_activated = True
                self._activation_key = session_data.get('key', '')
                
                # Сохраняем ключ в файл (для восстановления после разблокировки)
                if self._activation_key:
                    from auth import save_key_to_file
                    save_key_to_file(self._activation_key)
                
                self._subscription_info = {
                    'valid': True,
                    'key_type': session_info.get('key_type', ''),
                    'expires_at': session_info.get('expires_at', ''),
                }
                logger.info("[AUTH] Программа активирована (сессия валидна)")
                self.activationStatusChanged.emit()
                self.subscriptionChanged.emit()
                self._start_heartbeat()
                self._load_server_tokens()
                return

        # 2. Сессии нет или невалидна — пробуем ключ из файла
        from auth import extract_key_from_exe, save_key_to_file, load_key_from_file
        
        # Пробуем загрузить ключ из файла (даже если сессия невалидна)
        file_key = load_key_from_file()
        if file_key:
            self._activation_key = file_key
            logger.info(f"[AUTH] Ключ найден в файле: {file_key[:4]}...{file_key[-4:]}")
        
        # Также пробуем извлечь из .exe
        exe_key = extract_key_from_exe()
        if exe_key:
            self._activation_key = exe_key
            save_key_to_file(exe_key)
            logger.info(f"[AUTH] Ключ найден в .exe: {exe_key[:4]}...{exe_key[-4:]}")

        # 3. Если ключ есть - проверяем на сервере
        if self._activation_key:
            from auth import get_hwid
            hwid = get_hwid()
            valid, key_data = check_key(self._activation_key, hwid=hwid)
            logger.info(f"[AUTH] check_key результат: valid={valid}, data={key_data}")
            
            is_blocked = key_data.get('blocked', False)

            if valid:
                # Если ключ валиден и НЕ заблокирован — активируем
                # (activated может быть False после разблокировки если сервер не восстановил флаг)
                server_activated = key_data.get('activated', False)
                self._is_activated = server_activated or not is_blocked
                logger.info(f"[AUTH] Ключ валиден, activated={server_activated}, blocked={is_blocked}, итог: {self._is_activated}")

                # Заполняем subscription_info
                self._subscription_info = {
                    'valid': self._is_activated,
                    'key_type': key_data.get('key_type', ''),
                    'expires_at': key_data.get('expires_at', '')
                }

                if self._is_activated:
                    # Ключ активен - но сессия может быть неактивна (после разблокировки)
                    # Проверяем нужна ли новая сессия
                    from auth import load_session, activate_key, save_session
                    
                    session_data = load_session()
                    if not session_data or 'session_id' not in session_data:
                        # Сессии нет - создаём новую
                        logger.info("[AUTH] Сессия отсутствует, создаю новую...")
                        act_success, act_data = activate_key(self._activation_key)
                        if act_success:
                            session_id = act_data.get('session_id', '')
                            if session_id:
                                save_session(
                                    session_id=session_id,
                                    key=self._activation_key,
                                    expires_at=act_data.get('expires_at')
                                )
                                logger.info("[AUTH] Новая сессия создана успешно")
                    
                    self._start_heartbeat()
                    self._load_server_tokens()
                    logger.info("[AUTH] Программа активирована (ключ активирован на сервере)")
                else:
                    logger.warning("[AUTH] Ключ есть, но не активирован на сервере!")
                    # Показываем уведомление о блокировке
                    from PySide6.QtCore import QTimer
                    QTimer.singleShot(2000, lambda: self.notification.emit(
                        "⚠ Ваш ключ был заблокирован. Если это ошибка, напишите разработчику.",
                        "warning"
                    ))
            else:
                # Ключ не валиден - проверяем заблокирован или не найден
                error_msg = key_data.get('error', 'Unknown')
                
                if is_blocked:
                    # Ключ заблокирован в админке
                    logger.warning(f"[AUTH] Ключ заблокирован в админке ({error_msg})")
                    self._is_activated = False
                    self._subscription_info = {}
                    from PySide6.QtCore import QTimer
                    QTimer.singleShot(2000, lambda: self.notification.emit(
                        "⚠ Ваш ключ заблокирован. Если это ошибка, напишите разработчику.",
                        "warning"
                    ))
                else:
                    # Ключ не найден - пробуем активировать повторно (вдруг разблокировали в админке)
                    logger.warning(f"[AUTH] Ключ не найден ({error_msg}), пробую повторную активацию...")
                    
                    from auth import activate_key
                    act_success, act_data = activate_key(self._activation_key)
                    logger.info(f"[AUTH] activate_key результат: success={act_success}, data={act_data}")
                    
                    if act_success:
                        self._is_activated = True
                        self._subscription_info = {
                            'valid': True,
                            'key_type': act_data.get('key_type', ''),
                            'expires_at': act_data.get('expires_at', '')
                        }
                        logger.info("[AUTH] Ключ восстановлен после повторной активации (разблокирован в админке)")
                        self._start_heartbeat()
                        self._load_server_tokens()
                    else:
                        logger.error(f"[AUTH] Повторная активация не удалась: {act_data.get('error', 'Unknown')}")
                        self._is_activated = False
                        self._subscription_info = {}
                        from PySide6.QtCore import QTimer
                        QTimer.singleShot(2000, lambda: self.notification.emit(
                            f"⚠ Ключ недействителен. Если это ошибка, напишите разработчику.",
                            "warning"
                        ))
        else:
            logger.warning("[AUTH] Ключ не найден - требуется активация!")
            self._is_activated = False
            self._subscription_info = {}

        # 4. Обновляем QML о статусе активации
        self.activationStatusChanged.emit()
        self.subscriptionChanged.emit()
    
    def _start_heartbeat(self):
        """Запускает автоматическую проверку сессии"""
        from auth import HeartbeatManager, load_session

        session_data = load_session()
        if session_data and 'session_id' in session_data:
            self._heartbeat_manager = HeartbeatManager(check_interval=300)  # 5 минут
            self._heartbeat_manager.start(session_data['session_id'])
            
            # Запускаем QTimer для периодической проверки
            from PySide6.QtCore import QTimer
            if not hasattr(self, '_heartbeat_timer'):
                self._heartbeat_timer = None
            
            if self._heartbeat_timer:
                self._heartbeat_timer.stop()
            
            self._heartbeat_timer = QTimer()
            self._heartbeat_timer.timeout.connect(self._check_heartbeat)
            self._heartbeat_timer.start(300000)  # Проверка каждые 5 минут
            logger.info("[AUTH] Heartbeat запущен (интервал: 5мин)")
        else:
            logger.warning("[AUTH] Сессия не найдена, heartbeat НЕ запущен")

    def _check_heartbeat(self):
        """Проверяет heartbeat и блокирует программу если ключ невалиден"""
        logger.debug(f"[AUTH] _check_heartbeat вызван, manager={self._heartbeat_manager}")
        if not self._heartbeat_manager:
            return
            
        if self._heartbeat_manager.should_check():
            logger.info("[AUTH] Выполняю проверку heartbeat...")
            
            # Сначала пробуем check_session (если сессия есть)
            valid, data = self._heartbeat_manager.check()
            logger.info(f"[AUTH] check_session: valid={valid}, data={data}")
            
            # Если сессия не найдена — проверяем ключ напрямую
            if not valid and data and 'Session not found' in data.get('error', ''):
                logger.info("[AUTH] Сессия не найдена, проверяю ключ напрямую...")
                from auth import check_key, get_hwid
                if self._activation_key:
                    hwid = get_hwid()
                    valid, data = check_key(self._activation_key, hwid=hwid)
                    logger.info(f"[AUTH] check_key: valid={valid}, data={data}")
            
            if valid and data:
                # Проверяем явную блокировку
                is_blocked = data.get('blocked', False)
                if not is_blocked:
                    error_msg = data.get('error', '')
                    if error_msg:
                        error_lower = error_msg.lower()
                        is_blocked = any(w in error_lower for w in ['blocked', 'disabled', 'inactive', 'no longer active'])
                
                if is_blocked:
                    logger.warning(f"[AUTH] Ключ заблокирован! Причина: {data.get('error', '')}")
                    self._is_activated = False
                    self._subscription_info = {}
                    self.activationStatusChanged.emit()
                    self.subscriptionChanged.emit()
                    self.stop_all_macros()
                    self.notification.emit("⚠ Ключ заблокирован! Обратитесь в поддержку.", "warning")
                else:
                    logger.debug("[AUTH] Heartbeat OK")
                    # Обновляем токены с сервера при успешном heartbeat
                    self._load_server_tokens()
            elif not valid:
                error_msg = data.get('error', '') if data else 'Нет данных'
                logger.warning(f"[AUTH] Сессия/ключ невалидны! Причина: {error_msg}")
                self._is_activated = False
                self._subscription_info = {}
                self.activationStatusChanged.emit()
                self.subscriptionChanged.emit()
                self.stop_all_macros()
                self.notification.emit(f"⚠ Ошибка проверки: {error_msg}", "warning")
    
    def _load_server_tokens(self):
        """Загружает токены с сервера (вызывается после успешного heartbeat)"""
        try:
            from auth import get_server_tokens, load_session
            
            session_data = load_session()
            if not session_data or not session_data.get('session_id'):
                logger.warning("[AUTH] Нет сессии для загрузки токенов")
                return
            
            result = get_server_tokens(session_id=session_data['session_id'])
            if result and result.get('tokens'):
                self._secrets = result['tokens']
                logger.info("[AUTH] Токены загружены с сервера")
            else:
                logger.warning("[AUTH] Не удалось загрузить токены с сервела")
        except Exception as e:
            logger.error(f"[AUTH] Ошибка загрузки токенов: {e}")
    
    def get_secret(self, key: str) -> str:
        """Возвращает токен из памяти (или из constants для совместимости)"""
        if key in self._secrets:
            return self._secrets[key]
        # Fallback на constants (для разработки)
        from constants import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, SELECTEL_ACCESS_KEY, SELECTEL_SECRET_KEY
        if key == 'TELEGRAM_BOT_TOKEN':
            return TELEGRAM_BOT_TOKEN
        if key == 'TELEGRAM_CHAT_ID':
            return TELEGRAM_CHAT_ID
        if key == 'SELECTEL_ACCESS_KEY':
            return SELECTEL_ACCESS_KEY
        if key == 'SELECTEL_SECRET_KEY':
            return SELECTEL_SECRET_KEY
        return ""
    
    @Slot(str, result=dict)
    def activateWithKey(self, key):
        """Активирует программу по ключу (вызывается из QML)"""
        from auth import activate_key
        
        logger.info(f"[AUTH] Запрос активации по ключу: {key[:4]}...{key[-4:] if len(key) > 4 else ''}")
        
        try:
            success, data = activate_key(key.strip())
            
            if success:
                self._activation_key = key.strip()
                self._is_activated = True
                
                self._subscription_info = {
                    'valid': True,
                    'key_type': data.get('key_type', ''),
                    'expires_at': data.get('expires_at', '')
                }
                
                self.activationStatusChanged.emit()
                self.subscriptionChanged.emit()
                
                self._start_heartbeat()
                self._load_server_tokens()
                
                logger.info("[AUTH] Активация прошла успешно")
                return {'success': True, 'message': '✅ Программа активирована'}
            else:
                error = data.get('error', 'Неизвестная ошибка')
                logger.warning(f"[AUTH] Ошибка активации: {error}")
                return {'success': False, 'error': error}
                
        except Exception as e:
            logger.error(f"[AUTH] Критическая ошибка активации: {e}")
            return {'success': False, 'error': str(e)}
    
    @Slot(result=str)
    def getHwid(self):
        """Возвращает HWID машины"""
        from auth import get_hwid
        return get_hwid()

    @Slot(str)
    def copyToClipboard(self, text):
        """Копирует текст в буфер обмена"""
        from PySide6.QtGui import QGuiApplication
        QGuiApplication.clipboard().setText(text)

    def _get_current_version(self):
        """Возвращает текущую версию программы из constants.py"""
        try:
            from constants import CURRENT_VERSION
            return CURRENT_VERSION
        except Exception:
            return "1.0.0"

    def _check_updates_and_notify(self):
        """Проверяет обновления и уведомляет UI"""
        try:
            import requests
            from packaging import version
            version_url = "https://resvap.snbld.ru/version.json"
            resp = requests.get(version_url, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                # Сравниваем версии на клиенте
                current = self._get_current_version()
                latest = data.get('latest_version', '0.0.0')
                try:
                    is_available = version.parse(latest) > version.parse(current)
                except Exception:
                    is_available = latest != current

                if is_available:
                    logger.info(f"[UPDATE] Доступно обновление: {current} -> {latest}")
                    self.updateAvailable.emit(data)
                    self.notification.emit(
                        f"🔄 Доступно обновление: {latest}\nПерейдите в Диагностика → Обновления",
                        "info"
                    )
        except Exception as e:
            logger.debug(f"[UPDATE] Ошибка проверки обновлений: {e}")

    @Slot(str, str)
    def download_update_async(self, download_url, version):
        """Асинхронная загрузка обновления + установка через updater.exe"""
        if not download_url or not version:
            return

        import threading
        def download_worker():
            try:
                import requests
                import os
                import sys
                import subprocess

                # Папка для временных файлов
                updates_dir = os.path.join(self.app_dir, 'updates')
                os.makedirs(updates_dir, exist_ok=True)

                filename = f"update_{version}.zip"
                filepath = os.path.join(updates_dir, filename)

                # Проверяем не загружен ли уже
                if os.path.exists(filepath) and os.path.getsize(filepath) > 1_000_000:
                    logger.info(f"[UPDATE] Обновление уже загружено: {filepath}")
                    self.updateDownloadComplete.emit(filepath, version)
                    return

                logger.info(f"[UPDATE] Загрузка обновления: {download_url}")
                self.updateDownloadProgress.emit(0, 0)  # сброс

                resp = requests.get(download_url, timeout=300, stream=True)
                resp.raise_for_status()

                total_size = int(resp.headers.get('content-length', 0))
                downloaded = 0

                with open(filepath, 'wb') as f:
                    for chunk in resp.iter_content(chunk_size=65536):
                        if chunk:
                            f.write(chunk)
                            downloaded += len(chunk)
                            if total_size > 0:
                                self.updateDownloadProgress.emit(downloaded, total_size)

                file_size = os.path.getsize(filepath)
                if file_size > 1_000_000:
                    logger.info(f"[UPDATE] Обновление загружено: {filepath} ({file_size / 1_000_000:.1f}MB)")
                    self.updateDownloadProgress.emit(file_size, file_size)  # 100%
                    # Сигналим QML что загрузка завершена — покажем диалог
                    self.updateDownloadComplete.emit(filepath, version)
                else:
                    logger.error(f"[UPDATE] Загруженный файл слишком мал: {file_size} байт")
                    self.notification.emit("❌ Ошибка загрузки: файл повреждён", "error")
                    if os.path.exists(filepath):
                        os.remove(filepath)

            except Exception as e:
                logger.error(f"[UPDATE] Ошибка загрузки обновления: {e}")
                self.notification.emit(f"❌ Ошибка загрузки: {e}", "error")

        threading.Thread(target=download_worker, daemon=True).start()

    @Slot(str, str)
    def install_update(self, update_zip_path, version):
        """Запускает updater.exe для установки обновления"""
        import os
        import sys
        import subprocess

        # Для не-frozen версии (разработка) — просто уведомление
        if not getattr(sys, 'frozen', False):
            logger.info(f"[UPDATE] Режим разработки — обновление не устанавливается автоматически")
            self.notification.emit(f"🔧 Режим разработки: скачайте обновление вручную из Диагностика → Обновления", "info")
            return

        # Проверяем что ZIP существует
        if not os.path.exists(update_zip_path):
            logger.error(f"[UPDATE] ZIP обновления не найден: {update_zip_path}")
            self.notification.emit("❌ Файл обновления не найден", "error")
            return

        # Ищем updater.exe в папке установки
        install_dir = _get_app_dir()
        updater_path = os.path.join(install_dir, 'updater.exe')

        if not os.path.exists(updater_path):
            logger.error(f"[UPDATE] updater.exe не найден: {updater_path}")
            self.notification.emit("❌ updater.exe не найден. Обновите вручную.", "error")
            return

        logger.info(f"[UPDATE] Запуск updater.exe: {update_zip_path} → {version}")
        self.notification.emit(f"🔄 Установка обновления {version}...", "info")

        # Запускаем updater.exe
        CREATE_NO_WINDOW = 0x08000000
        subprocess.Popen(
            [updater_path, update_zip_path, version],
            cwd=install_dir,
            creationflags=CREATE_NO_WINDOW,
            close_fds=True
        )

        # Закрываем программу
        logger.info("[UPDATE] Закрытие программы для установки обновления")
        from PySide6.QtCore import QTimer
        QTimer.singleShot(200, lambda: self.closeRequested.emit())

    @Slot(str, result='QVariant')
    def activateWithKey(self, key):
        """Активирует программу с ключом (вызывается из QML)"""
        from auth import activate_key, save_key_to_file

        success, data = activate_key(key)

        if success:
            # Сохраняем ключ локально (для восстановления после разблокировки)
            saved = save_key_to_file(key)
            if saved:
                logger.info(f"[AUTH] Ключ сохранён локально: {key[:4]}...{key[-4:]}")
            else:
                logger.error("[AUTH] КРИТИЧЕСКАЯ ОШИБКА: Не удалось сохранить ключ!")
            
            self._activation_key = key
            self._is_activated = True
            self._subscription_info = {
                'valid': True,
                'key_type': data.get('key_type', 'unknown'),
                'expires_at': data.get('expires_at', '')
            }
            self._start_heartbeat()
            self._load_server_tokens()
            self.activationStatusChanged.emit()
            self.subscriptionChanged.emit()
            logger.info(f"[AUTH] Программа активирована! Тип: {data.get('key_type')}, До: {data.get('expires_at')}")
            return {'success': True, 'data': data}
        else:
            logger.error(f"[AUTH] Ошибка активации: {data.get('error', 'Unknown')}")
            return {'success': False, 'error': data.get('error', 'Неизвестная ошибка')}
    
    def _is_program_activated(self):
        """Проверяет, активирована ли программа"""
        return self._is_activated
    
    def _stop_program_if_not_activated(self):
        """Останавливает программу если не активирована"""
        if not self._is_activated:
            logger.error("[AUTH] Программа не активирована - остановка!")
            # Здесь можно вызвать закрытие приложения
            self.closeRequested.emit()

    def _update_macros_dicts(self):
        new_list = []
        for macro in self._macros:
            item = {
                "name": macro.name,
                "type": macro.type,
                "hotkey": macro.hotkey or "",
                "running": macro.running,
                "cooldown": getattr(macro, 'cooldown', 0),
                "skill_range": getattr(macro, 'skill_range', 0),
                "icon": getattr(macro, 'icon', ""),
            }
            if hasattr(macro, "skill_id"):
                item["skill_id"] = macro.skill_id
            if hasattr(macro, "buff_id"):
                item["buff_id"] = macro.buff_id
            if hasattr(macro, "zone_rect"):
                item["zone_rect"] = macro.zone_rect
            if hasattr(macro, "steps"):
                item["steps"] = macro.steps
            new_list.append(item)
        
        # Создаём НОВЫЙ список чтобы QML увидел изменения
        self._macros_dicts = list(new_list)
        self.macrosChanged.emit()

    def _stop_ping_monitor(self):
        """Безопасно останавливает PingMonitor с отключением сигнала (защита от signal leak)"""
        if self.ping_monitor:
            try:
                # Отключаем сигнал ПЕРЕД остановкой
                try:
                    self.ping_monitor.ping_updated.disconnect(self.on_ping_updated)
                except (RuntimeError, TypeError):
                    pass  # Уже отключён или не был подключён
                if self.ping_monitor.isRunning():
                    self.ping_monitor.stop()
                    self.ping_monitor.wait(2000)
                self.ping_monitor.deleteLater()
            except Exception as e:
                logger.error(f"[PING] Ошибка при остановке PingMonitor: {e}")

    @Slot(str, str)
    def set_setting(self, key, value):
        """
        Устанавливает значение настройки с полной валидацией.
        
        Args:
            key: Ключ настройки (должен быть в ALLOWED_SETTINGS)
            value: Значение (строка из QML)
        """
        # ← ПРОВЕРКА 1: допустимый ключ
        if key not in ALLOWED_SETTINGS:
            logger.warning(f"Попытка установить недопустимый ключ: {key}")
            self.notification.emit(f"⚠ Недопустимая настройка: {key}", "error")
            return
        
        expected_type, min_val, max_val = ALLOWED_SETTINGS[key]
        
        # ← ПРОВЕРКА 2: преобразование типа
        try:
            if expected_type == int:
                value = int(float(value))  # "10.0" → 10
            elif expected_type == float:
                value = float(value)
            elif expected_type == bool:
                value = value.lower() in ("true", "1", "yes")
            elif expected_type == list:
                # Список из настроек (например castbar_color)
                if isinstance(value, str):
                    value = [int(x.strip()) for x in value.split(',')]
            elif expected_type == (str, list):
                # Может быть строкой или списком (mob_area, player_area)
                if isinstance(value, str) and ',' in value:
                    value = [int(x.strip()) for x in value.split(',')]
            # str оставляем как есть
        except (ValueError, TypeError) as e:
            logger.error(f"Неверный тип для {key}: {value} ({e})")
            self.notification.emit(f"⚠ Неверный формат: {value}", "warning")
            return
        
        # ← ПРОВЕРКА 3: диапазон значений (если указан)
        if min_val is not None and max_val is not None:
            if value < min_val or value > max_val:
                logger.error(f"Значение {key} вне диапазона: {value} (допустимо: {min_val}-{max_val})")
                self.notification.emit(f"⚠ Вне диапазона: {min_val}-{max_val}", "warning")
                # Используем ближайшее допустимое значение
                value = max(min_val, min(max_val, value))
        
        # ← ПРОВЕРКА 4: специальные предупреждения
        if key == "ocr_scale" and value < 5:
            logger.warning(f"ocr_scale={value} может ухудшить распознавание")
            self.notification.emit("⚠ OCR scale < 5 ухудшает распознавание", "warning")
        
        if key == "castbar_threshold" and value < 50:
            logger.warning(f"castbar_threshold={value} может вызвать ложные срабатывания")
            self.notification.emit("⚠ Порог < 50 может вызвать ложные срабатывания", "warning")
        
        # Сохраняем (единожды - в конце метода)
        old_value = self._settings.get(key)
        self._settings[key] = value

        logger.info(f"Настройка {key} изменена: {old_value} → {value}")

        # ← ПРИМЕНЯЕМ настройки к макросам
        if key == "castbar_color":
            # castbar_color - список RGB (list)
            if isinstance(value, str):
                value = [int(x.strip()) for x in value.split(',')]
            self.castbar_color = value
            # Сохраняем в настройки как список int
            self._settings[key] = self.castbar_color
            self.settingsChanged.emit()
            self.apply_settings_to_macros(key, self.castbar_color)

        elif key == "castbar_threshold":
            # castbar_threshold - порог чувствительности (int)
            try:
                self.castbar_threshold = int(value)
            except Exception:
                self.castbar_threshold = 70
            self._settings[key] = self.castbar_threshold
            self.settingsChanged.emit()
            self.apply_settings_to_macros(key, self.castbar_threshold)

        elif key in ("movement_delay_enabled", "check_distance", "ocr_use_morph", "ping_auto", "use_fixed_delays", "use_ping_delays", "use_castbar_detection", "castbar_enabled", "window_locked"):
            if isinstance(value, str):
                value = value.lower() in ("true", "1", "yes")
            self._settings[key] = value
            self.settingsChanged.emit()

            # Обработка ping_auto - запуск/остановка PingMonitor
            if key == "ping_auto":
                if value:
                    # Включаем PingMonitor
                    interval = self._settings.get("ping_check_interval", 5)
                    # Сначала останавливаем старый если работает
                    self._stop_ping_monitor()
                    if not self.ping_monitor or not self.ping_monitor.isRunning():
                        self.ping_monitor = threads.PingMonitor(self._settings["process_name"], interval)
                        self.ping_monitor.ping_updated.connect(self.on_ping_updated)
                        self.ping_monitor.start()
                        logger.info(f"[PING] PingMonitor включен")
                else:
                    # Выключаем PingMonitor
                    self._stop_ping_monitor()
                    logger.info(f"[PING] PingMonitor выключен")

            # Обработка use_ping_delays / use_fixed_delays - обновляем задержки в макросах
            if key in ("use_ping_delays", "use_fixed_delays"):
                # Пересоздаём шаги макросов с новыми задержками
                self.recalculate_macro_delays()

            self.apply_settings_to_macros(key, value)

        else:
            # Для всех остальных настроек
            self._settings[key] = value
            self.settingsChanged.emit()
            self.apply_settings_to_macros(key, value)

        # ✅ Сохраняем ОДИН РАЗ в конце (в settings.json и в профиль)
        self.save_settings()
    
    def recalculate_macro_delays(self):
        """Пересчитывает задержки в шагах макросов при переключении режима или обновлении пинга"""
        use_ping_delays = self._settings.get("use_ping_delays", False)
        
        if use_ping_delays:
            # Режим автозадержек (пинг)
            ping_comp = self.get_ping_compensation() * 1000  # в мс
            first_step_delay = round(30 + ping_comp)  # 30мс + компенсация
            step_delay = round(ping_comp)  # ТОЛЬКО компенсация
        else:
            # Режим фиксированных задержек
            first_step_delay = self._settings.get("first_step_delay", 100)
            step_delay = self._settings.get("global_step_delay", 20)
        
        logger.debug(f"[MACROS] Пересчёт задержек: ping={self._ping}мс, use_ping_delays={use_ping_delays}, first_step={first_step_delay}мс, step={step_delay}мс")
        
        # Обновляем шаги во всех макросах
        for macro in self._macros:
            if hasattr(macro, 'steps') and len(macro.steps) >= 3:
                # Шаг 1: свап в пение
                if macro.steps[0][0] == "key":
                    macro.steps[0] = ["key", macro.steps[0][1], first_step_delay]
                # Шаг 2: скилл
                if macro.steps[1][0] in ("key", "left", "right"):
                    macro.steps[1] = [macro.steps[1][0], macro.steps[1][1], step_delay]
                # Шаг 3: свап на ПА
                if macro.steps[2][0] == "key":
                    macro.steps[2] = ["key", macro.steps[2][1], step_delay]
        
        self._update_macros_dicts()
        logger.info(f"[MACROS] Задержки обновлены в {len(self._macros)} макросах")

    def apply_settings_to_macros(self, key, value):
        """Применяет изменения настроек ко всем существующим макросам"""
        logger.info(f"apply_settings_to_macros: key={key}, value={value}")

        if key == "swap_key_chant":
            # Обновляем первый шаг (свап в пение) во всех макросах
            for macro in self._macros:
                if hasattr(macro, 'steps') and len(macro.steps) > 0:
                    step = macro.steps[0]
                    logger.info(f"macro={macro.name}, step[0]={step}, type={type(step)}")
                    if len(step) >= 1 and step[0] == "key":
                        # Обновляем ТОЛЬКО клавишу, задержку сохраняем
                        delay = step[2] if len(step) > 2 else 100
                        macro.steps[0] = ["key", value, delay]
                        logger.info(f"Обновлён шаг 1 (свап в пение) в макросе '{macro.name}': {key}={value}, delay={delay}")
            self.macrosChanged.emit()

        elif key == "swap_key_pa":
            # Обновляем третий шаг (свап в ПА) во всех макросах
            for macro in self._macros:
                if hasattr(macro, 'steps') and len(macro.steps) >= 3:
                    step = macro.steps[2]
                    logger.info(f"macro={macro.name}, step[2]={step}, type={type(step)}")
                    if len(step) >= 1 and step[0] == "key":
                        # Обновляем ТОЛЬКО клавишу, задержку сохраняем
                        delay = step[2] if len(step) > 2 else 20
                        macro.steps[2] = ["key", value, delay]
                        logger.info(f"Обновлён шаг 3 (свап в ПА) в макросе '{macro.name}': {key}={value}, delay={delay}")
            self.macrosChanged.emit()

        elif key == "cooldown_margin":
            # cooldown_margin читается из настроек при выполнении, ничего обновлять не нужно
            logger.info(f"cooldown_margin будет применён при следующем запуске макроса")

        elif key == "global_step_delay":
            # Обновляем задержку ВТОРОГО и ТРЕТЬЕГО шага во всех макросах
            for macro in self._macros:
                if hasattr(macro, 'steps') and len(macro.steps) >= 2:
                    # Обновляем шаг 2
                    step = macro.steps[1]
                    delay = float(value)
                    macro.steps[1] = [step[0], step[1], delay]

                    # Обновляем шаг 3 если есть
                    if len(macro.steps) >= 3:
                        step3 = macro.steps[2]
                        macro.steps[2] = [step3[0], step3[1], delay]

                    logger.info(f"Обновлена задержка шагов 2 и 3 в макросе '{macro.name}': {key}={value}")
            self.macrosChanged.emit()

        elif key == "first_step_delay":
            # Обновляем задержку ПЕРВОГО шага во всех макросах
            for macro in self._macros:
                if hasattr(macro, 'steps') and len(macro.steps) > 0:
                    step = macro.steps[0]
                    # Сохраняем action и value, обновляем только задержку
                    delay = int(value)
                    macro.steps[0] = [step[0], step[1], delay]
                    logger.info(f"Обновлена задержка шага 1 в макросе '{macro.name}': {key}={value}")
            self.macrosChanged.emit()

        elif key == "movement_delay_enabled":
            # Применяется при выполнении макроса
            logger.info(f"movement_delay_enabled={value} будет применён при следующем запуске макроса")

        elif key == "movement_delay_ms":
            # Применяется при выполнении макроса
            logger.info(f"movement_delay_ms={value} будет применён при следующем запуске макроса")

        elif key == "check_distance":
            # Применяется при выполнении макроса
            logger.info(f"check_distance={value} будет применён при следующем запуске макроса")

        elif key == "ocr_scale":
            # Перезапускаем OCR с новыми настройками
            logger.info(f"ocr_scale={value}, перезапускаем OCR")
            self.stop_ocr()
            self.start_ocr()

        elif key == "ocr_psm":
            # Перезапускаем OCR с новыми настройками
            logger.info(f"ocr_psm={value}, перезапускаем OCR")
            self.stop_ocr()
            self.start_ocr()

        elif key == "ocr_use_morph":
            # Перезапускаем OCR с новыми настройками
            logger.info(f"ocr_use_morph={value}, перезапускаем OCR")
            self.stop_ocr()
            self.start_ocr()

        elif key == "window_locked":
            # Обновляем настройку окна для всех макросов
            self._window_locked = value
            logger.info(f"window_locked={value} применено ко всем макросам")
            self.macrosChanged.emit()

        elif key == "target_window_title":
            # Обновляем заголовок окна для всех макросов
            self._target_window_title = value
            logger.info(f"target_window_title={value} применено ко всем макросам")
            self.macrosChanged.emit()

        elif key in ("ping_auto", "process_name", "server_ip", "ping_check_interval"):
            # Перезапускаем PingMonitor с новыми настройками
            logger.info(f"{key}={value}, перезапускаем PingMonitor")
            self._stop_ping_monitor()
            # Запускаем если ping_auto=True
            if self._settings.get("ping_auto"):
                interval = self._settings.get("ping_check_interval", 5)
                self.ping_monitor = threads.PingMonitor(self._settings.get("process_name", "elementclient.exe"), interval)
                self.ping_monitor.ping_updated.connect(self.on_ping_updated)
                self.ping_monitor.start()

        elif key == "start_all_hotkey":
            # Перерегистрируем горячие клавиши
            logger.info(f"{key}={value}, перерегистрируем горячие клавиши")
            self.unregister_all_hotkeys()
            self.register_all_hotkeys()

        elif key == "stop_all_hotkey":
            # Перерегистрируем горячие клавиши
            logger.info(f"{key}={value}, перерегистрируем горячие клавиши")
            self.unregister_all_hotkeys()
            self.register_all_hotkeys()

        elif key == "castbar_enabled":
            logger.info(f"castbar_enabled={value}")
            self.settingsChanged.emit()

        elif key == "castbar_point":
            logger.info(f"castbar_point={value}")
            self.settingsChanged.emit()

        elif key == "castbar_threshold":
            logger.info(f"castbar_threshold={value} применено")
            self.settingsChanged.emit()

        elif key in ("movement_delay_enabled", "movement_delay_ms", "check_distance", "use_castbar_detection", "distance_tolerance"):
            logger.info(f"{key}={value} будет применён при следующем запуске макроса")

        elif key == "window_opacity":
            # Применяется к окну
            logger.info(f"window_opacity={value} применено к окну")
            if hasattr(self, '_main_window'):
                self._main_window.setWindowOpacity(float(value))
            self.settingsChanged.emit()

        elif key == "accent_color":
            # Передаём в UI через сигнал
            logger.info(f"accent_color={value}, обновляем UI")
            self.settingsChanged.emit()

        elif key in ("log_level_macros", "log_level_errors", "log_level_ocr", "log_level_network", "log_level_settings", "log_level_debug", "log_level_shiboken"):
            # Применяем уровень логирования
            logger.info(f"{key}={value}, применяем уровень логирования")
            from backend.logger_manager import LoggerManager
            category = key.replace("log_level_", "")
            level_map = {"DEBUG": 10, "INFO": 20, "WARNING": 30, "ERROR": 40, "CRITICAL": 50}
            level = level_map.get(str(value).upper(), 20)
            LoggerManager.set_log_level(category, level)

        else:
            logger.info(f"Настройка '{key}={value}' не требует применения к макросам")



    def _update_and_notify(self):
        self._update_macros_dicts()
        self.globalStoppedChanged.emit()

    @Slot()
    def stop_all_macros(self):
        """Остановить ВСЕ макросы - зарегистрировать горячие клавиши без блокировки"""
        logger.info(f"[STOP_ALL] Начало остановки всех макросов, global_stopped={self._global_stopped}")
        self._global_stopped = True
        self.globalStoppedChanged.emit()

        # ✅ ОСТАНАВЛИВАЕМ MouseClickMonitor (чтобы клики не блокировались)
        try:
            if self.mouse_click_monitor and self.mouse_click_monitor.isRunning():
                self.mouse_click_monitor.stop()
                if self.mouse_click_monitor.isRunning():
                    self.mouse_click_monitor.wait(500)
                logger.info("[STOP_ALL] MouseClickMonitor остановлен")
        except RuntimeError as e:
            logger.debug(f"[STOP_ALL] MouseClickMonitor уже удалён: {e}")

        # ОСТАНАВЛИВАЕМ OCR
        if self._ocr_running:
            self.stop_ocr()
            logger.info("[STOP_ALL] OCR остановлен")

        # СНАЧАЛА останавливаем все макросы
        for macro in self._macros:
            logger.info(f"[STOP_ALL] Остановка макроса '{macro.name}', running={macro.running}")
            macro.stop()

        # Ждём завершения ВСЕХ потоков (каждый поток отдельно!)
        import time
        for macro in self._macros:
            if macro.thread and macro.thread.is_alive():
                logger.debug(f"[STOP_ALL] Ожидание завершения '{macro.name}'...")
                macro.thread.join(timeout=3.0)  # ← Ждём до 3 секунд!
                if macro.thread.is_alive():
                    logger.warning(f"[STOP_ALL] Поток '{macro.name}' не завершился за 3с")

        logger.info(f"[STOP_ALL] Все макросы остановлены")

        # ПРИНУДИТЕЛЬНО сбрасываем running=False для всех макросов
        for macro in self._macros:
            macro.running = False

        # ТЕПЕРЬ перерегистрируем горячие клавиши с suppress=False (НЕ блокировать клавиши)
        for macro in self._macros:
            if macro.hotkey:
                logger.info(f"[STOP_ALL] Перерегистрация hotkey '{macro.hotkey}' для макроса '{macro.name}' с suppress=False")
                # Сначала удаляем старую
                self.unregister_hotkey(macro.hotkey)
                # Потом регистрируем новую с suppress=False
                macro_to_use = macro
                def make_callback(m):
                    def callback(e):
                        logger.debug(f"Горячая клавиша '{m.hotkey}' нажата, но макросы остановлены")
                        # Ничего не делаем - макросы остановлены
                    return callback
                self.register_hotkey(macro.hotkey, make_callback(macro_to_use), check_window=True, check_global_stop=True, suppress=False)

        # Обновляем UI в главном потоке
        self._update_and_notify()
        # Сигнал для обновления индикатора кнопки СТОП
        self.stopAllPressed.emit()
        self.notification.emit("⏹️ Все макросы ОСТАНОВЛЕНЫ", "warning")
        logger.info(f"[STOP_ALL] Завершение остановки всех макросов")

    @Slot(str)
    def delete_macro(self, name):
        for macro in self._macros:
            if macro.name == name:
                self._macros.remove(macro)
                self.save_macros()
                self._update_macros_dicts()
                self.notification.emit(f"Макрос '{name}' удалён", "warning")
                if macro.hotkey:
                    self.unregister_hotkey(macro.hotkey)
                break

    @Slot(str)
    def edit_macro(self, name):
        """Открывает макрос на редактирование"""
        # Находим макрос по имени и сохраняем для редактирования
        for macro in self._macros:
            if macro.name == name:
                self._macro_name_for_edit = name
                logger.debug(f"edit_macro: найден макрос '{name}', открываем редактирование")
                # Открываем страницу редактирования
                self.pageChangeRequested.emit("MacrosEditPage.qml")
                return
        logger.warning(f"edit_macro: макрос '{name}' не найден")
        self.notification.emit(f"Макрос '{name}' не найден", "error")

    @Slot()
    def create_simple_macro(self):
        self.open_macro_dialog("simple")

    @Slot()
    def create_zone_macro(self):
        self.open_macro_dialog("zone")

    @Slot()
    def create_skill_macro(self):
        self.open_macro_dialog("skill")

    @Slot()
    def create_buff_macro(self):
        self.open_macro_dialog("buff")

    @Slot(str)
    def load_profile(self, name):
        """Загрузить профиль по имени"""
        if not name:
            self.notification.emit("⚠ Введите имя профиля", "warning")
            return

        # ✅ СОХРАНЯЕМ ТЕКУЩИЙ ПРОФИЛЬ ПЕРЕД ЗАГРУЗКОЙ НОВОГО!
        if self._current_profile and self._current_profile != name:
            logger.info(f"[PROFILE] Сохранение текущего профиля '{self._current_profile}' перед загрузкой '{name}'...")
            self.save_profile(self._current_profile)

        profile_path = os.path.join(self.profiles_dir, f"{name}.json")
        if not os.path.exists(profile_path):
            self.notification.emit(f"⚠ Профиль '{name}' не найден", "error")
            return

        try:
            with open(profile_path, 'r', encoding='utf-8') as f:
                profile_data = json.load(f)

            # ✅ 1. Загружаем настройки в self._settings
            settings = profile_data.get("settings", {})
            for key, value in settings.items():
                if key in ALLOWED_SETTINGS:
                    self._settings[key] = value

            # ✅ 2. Применяем настройки К ВСЕМ атрибутам backend
            self._apply_settings_to_attributes()

            # ✅ 3. Загружаем макросы
            macros_data = profile_data.get("macros", [])
            logger.info(f"[PROFILE] Загрузка {len(macros_data)} макросов из профиля")
            self._macros = []
            for macro_data in macros_data:
                macro = self._create_macro_from_dict(macro_data)
                if macro:
                    self._macros.append(macro)
                    logger.debug(f"[PROFILE] Загружен макрос: {macro.name} (type={macro.type})")

            logger.info(f"[PROFILE] Загружено {len(self._macros)} макросов")

            # ✅ 4. Загружаем привязку окна
            if "window_locked" in profile_data:
                self._window_locked = profile_data["window_locked"]
                self._settings["window_locked"] = profile_data["window_locked"]
            if "target_window_title" in profile_data:
                self._target_window_title = profile_data["target_window_title"]
                self._settings["target_window_title"] = profile_data["target_window_title"]

            logger.info(f"[PROFILE] Окно: locked={self._window_locked}, title={self._target_window_title}")

            # ✅ 5. Обновляем текущий профиль ДО сохранения настроек!
            self._current_profile = name
            self._settings["last_active_profile"] = name  # Сохраняем имя последнего профиля

            # ✅ 6. Сохраняем настройки (обновляем settings.json и текущий профиль)
            self.save_settings()

            # ✅ 7. Обновляем UI
            self._update_macros_dicts()  # ← Обновляем _macros_dicts для UI
            self.profileChanged.emit()
            self.profilesChanged.emit()  # ← Обновляем список профилей для UI
            self.settingsChanged.emit()

            # ✅ 8. Перезапускаем OCR с новыми областями из профиля
            if self._settings.get("mob_area") or self._settings.get("player_area"):
                if not self._ocr_running:
                    self.start_ocr()
                    logger.info("[PROFILE] OCR запущен с областями из профиля")
                else:
                    # OCR уже работает — перезапускаем с новыми областями
                    self.stop_ocr()
                    self.start_ocr()
                    logger.info("[PROFILE] OCR перезапущен с новыми областями из профиля")

            # ✅ 9. Перерегистрируем горячие клавиши
            self.register_all_hotkeys()

            self.notification.emit(f"✓ Профиль '{name}' загружен", "success")
            logger.info(f"[PROFILE] Загружен профиль: {name}, макросов: {len(self._macros)}")

        except Exception as e:
            logger.error(f"[PROFILE] Ошибка загрузки профиля: {e}")
            self.notification.emit(f"⚠ Ошибка загрузки: {e}", "error")
    
    def _apply_settings_to_attributes(self):
        """
        Применяет все настройки из self._settings к атрибутам backend.
        Вызывается при загрузке профиля чтобы все настройки соответствовали профилю.
        """
        logger.info("[PROFILE] Применение настроек к атрибутам backend...")
        
        # ==================== КАСТБАР ====================
        self.castbar_enabled = self._settings.get("castbar_enabled", False)
        self.castbar_point = self._settings.get("castbar_point", "1273,1005")
        
        castbar_color = self._settings.get("castbar_color", [94, 123, 104])
        self.castbar_color = self._load_castbar_color(castbar_color)
        
        threshold = self._settings.get("castbar_threshold", 70)
        self.castbar_threshold = int(threshold) if isinstance(threshold, (int, float)) else 70
        
        # ==================== OCR ОБЛАСТИ ====================
        self.mob_area = self._settings.get("mob_area", "1266,32,1303,56")
        self.player_area = self._settings.get("player_area", "1271,16,1294,32")
        
        # ==================== ОКНО ====================
        self._window_locked = self._settings.get("window_locked", False)
        self._target_window_title = self._settings.get("target_window_title", "")
        
        # ==================== ПИНГ ====================
        self._ping = self._settings.get("average_ping", 30)
        
        # ==================== ДИСТАНЦИЯ ====================
        self._target_distance = None  # Будет обновлена из OCR
        
        logger.info(
            f"[PROFILE] Настройки применены: "
            f"castbar_enabled={self.castbar_enabled}, "
            f"castbar_point={self.castbar_point}, "
            f"castbar_color={self.castbar_color}, "
            f"castbar_threshold={self.castbar_threshold}, "
            f"mob_area={self.mob_area}, "
            f"player_area={self.player_area}, "
            f"window_locked={self._window_locked}, "
            f"target_window_title={self._target_window_title}, "
            f"ping={self._ping}"
        )
        
        # ✅ Эмитим сигнал чтобы UI обновился
        self.settingsChanged.emit()
        self.pingUpdated.emit(self._ping)

    @Slot(str)
    def create_profile(self, name):
        """Создать новый пустой профиль"""
        if not name:
            self.notification.emit("⚠ Введите имя профиля", "warning")
            return
        
        # Очищаем имя от недопустимых символов Windows
        # Удаляем недопустимые символы: < > : " / \ | ? *
        clean_name = re.sub(r'[<>:"/\\|?*]', '', name.strip())
        # Удаляем контрольные символы
        clean_name = re.sub(r'[\x00-\x1f\x7f]', '', clean_name)
        # Удаляем точки и пробелы в конце
        clean_name = clean_name.rstrip('. ')
        
        if not clean_name:
            self.notification.emit("⚠ Имя профиля не может содержать только специальные символы", "warning")
            return

        profile_path = os.path.join(self.profiles_dir, f"{clean_name}.json")
        if os.path.exists(profile_path):
            self.notification.emit(f"⚠ Профиль '{clean_name}' уже существует", "warning")
            return

        try:
            # Создаём пустой профиль с текущими настройками но без макросов
            profile_data = {
                "settings": dict(self._settings),
                "macros": [],  # Пустой список макросов
                "window_locked": self._settings.get("window_locked", False),
                "target_window_title": self._settings.get("target_window_title", "")
            }

            with open(profile_path, 'w', encoding='utf-8') as f:
                json.dump(profile_data, f, ensure_ascii=False, indent=2)

            # Переключаемся на новый профиль
            self._current_profile = clean_name
            self._settings["last_active_profile"] = clean_name
            self._macros = []  # Очищаем макросы
            self._update_macros_dicts()
            self.profileChanged.emit()
            self.profilesChanged.emit()
            self.settingsChanged.emit()
            self.save_settings()
            self.register_all_hotkeys()

            self.notification.emit(f"✓ Профиль '{clean_name}' создан", "success")
            logger.info(f"[PROFILE] Создан профиль: {clean_name}")

        except Exception as e:
            logger.error(f"[PROFILE] Ошибка создания профиля: {e}")
            self.notification.emit(f"⚠ Ошибка создания: {e}", "error")

    @Slot(str, str)
    def rename_profile(self, old_name, new_name):
        """Переименовать профиль"""
        if not old_name or not new_name:
            self.notification.emit("⚠ Неверное имя профиля", "warning")
            return
        
        # Очищаем имя от недопустимых символов Windows
        # Удаляем недопустимые символы: < > : " / \ | ? *
        clean_name = re.sub(r'[<>:"/\\|?*]', '', new_name.strip())
        # Удаляем контрольные символы
        clean_name = re.sub(r'[\x00-\x1f\x7f]', '', clean_name)
        # Удаляем точки и пробелы в конце
        clean_name = clean_name.rstrip('. ')
        
        if not clean_name:
            self.notification.emit("⚠ Имя профиля не может содержать только специальные символы", "warning")
            return
        
        if clean_name == old_name:
            self.notification.emit("ℹ️ Имя не изменилось", "info")
            return

        old_path = os.path.join(self.profiles_dir, f"{old_name}.json")
        new_path = os.path.join(self.profiles_dir, f"{clean_name}.json")

        if not os.path.exists(old_path):
            self.notification.emit(f"⚠ Профиль '{old_name}' не найден", "error")
            return

        if os.path.exists(new_path):
            self.notification.emit(f"⚠ Профиль '{clean_name}' уже существует", "warning")
            return

        try:
            # Переименовываем файл
            os.rename(old_path, new_path)

            # Обновляем текущий профиль
            self._current_profile = clean_name
            self._settings["last_active_profile"] = clean_name
            self.profileChanged.emit()
            self.profilesChanged.emit()
            self.save_settings()

            self.notification.emit(f"✓ Профиль переименован в '{clean_name}'", "success")
            logger.info(f"[PROFILE] Профиль '{old_name}' переименован в '{clean_name}'")

        except Exception as e:
            logger.error(f"[PROFILE] Ошибка переименования профиля: {e}")
            self.notification.emit(f"⚠ Ошибка переименования: {e}", "error")

    @Slot(str)
    def save_profile(self, name=None):
        """Сохранить текущий профиль"""
        if name is None:
            name = self._current_profile

        if not name:
            self.notification.emit("⚠ Введите имя профиля", "warning")
            return
        
        # Очищаем имя от недопустимых символов Windows
        # Удаляем недопустимые символы: < > : " / \ | ? *
        clean_name = re.sub(r'[<>:"/\\|?*]', '', name.strip())
        # Удаляем контрольные символы
        clean_name = re.sub(r'[\x00-\x1f\x7f]', '', clean_name)
        # Удаляем точки и пробелы в конце
        clean_name = clean_name.rstrip('. ')
        
        if not clean_name:
            self.notification.emit("⚠ Имя профиля не может содержать только специальные символы", "warning")
            return

        try:
            logger.info(f"[PROFILE] Сохранение профиля '{clean_name}': макросов={len(self._macros)}, настроек={len(self._settings)}")
            
            profile_data = {
                "settings": dict(self._settings),
                "macros": [self._macro_to_dict(m) for m in self._macros],
                "window_locked": self._settings.get("window_locked", False),
                "target_window_title": self._settings.get("target_window_title", "")
            }
            
            logger.info(f"[PROFILE] Сериализовано макросов: {len(profile_data['macros'])}")

            profile_path = os.path.join(self.profiles_dir, f"{clean_name}.json")
            with open(profile_path, 'w', encoding='utf-8') as f:
                json.dump(profile_data, f, ensure_ascii=False, indent=2)

            # Обновляем текущий профиль
            self._current_profile = clean_name
            self.profileChanged.emit()
            self.profilesChanged.emit()

            self.notification.emit(f"✓ Профиль '{clean_name}' сохранён", "success")
            logger.info(f"[PROFILE] Сохранён профиль: {clean_name}")

        except Exception as e:
            logger.error(f"[PROFILE] Ошибка сохранения профиля: {e}")
            self.notification.emit(f"⚠ Ошибка сохранения: {e}", "error")

    @Slot(str)
    def delete_profile(self, name=None):
        """Удалить профиль"""
        if name is None:
            name = self._current_profile
        
        if not name:
            self.notification.emit("⚠ Профиль не выбран", "warning")
            return
        
        profile_path = os.path.join(self.profiles_dir, f"{name}.json")
        if not os.path.exists(profile_path):
            self.notification.emit(f"⚠ Профиль '{name}' не найден", "error")
            return
        
        try:
            os.remove(profile_path)
            
            if self._current_profile == name:
                self._current_profile = None
                self.profileChanged.emit()
            
            self.profilesChanged.emit()
            self.notification.emit(f"✓ Профиль '{name}' удалён", "success")
            logger.info(f"[PROFILE] Удалён профиль: {name}")
            
        except Exception as e:
            logger.error(f"[PROFILE] Ошибка удаления профиля: {e}")
            self.notification.emit(f"⚠ Ошибка удаления: {e}", "error")

    @Slot()
    def get_profile_list(self):
        """Получить список всех профилей"""
        try:
            profiles = []
            if os.path.exists(self.profiles_dir):
                for file in os.listdir(self.profiles_dir):
                    if file.endswith('.json'):
                        profiles.append(file[:-5])  # убираем .json
            return profiles
        except Exception as e:
            logger.error(f"[PROFILE] Ошибка получения списка профилей: {e}")
            return []

    def _create_macro_from_dict(self, data):
        """Создать макрос из словаря"""
        try:
            macro_type = data.get("type", "simple")
            macro = None

            if macro_type == "simple":
                macro = SimpleMacro(
                    name=data.get("name", "Макрос"),
                    app=self,
                    hotkey=data.get("hotkey", ""),
                    steps=data.get("steps", [])
                )
            elif macro_type == "skill":
                macro = SkillMacro(
                    name=data.get("name", "Скилл"),
                    app=self,
                    hotkey=data.get("hotkey", ""),
                    skill_id=data.get("skill_id", 0),
                    cooldown=data.get("cooldown", 3.0),
                    skill_range=data.get("skill_range", 10.0),
                    cast_time=data.get("cast_time", 0.5),
                    steps=data.get("steps", []),
                    castbar_swap_delay=data.get("castbar_swap_delay", 0)
                )
                # zone_rect устанавливаем отдельно если есть И подписываем на клики
                if data.get("zone_rect"):
                    macro.zone_rect = tuple(data["zone_rect"])
                    macro._connect_mouse_click(self)
                    logger.info(f"[SKILL+ZONE] Макрос '{macro.name}' загружен с областью {macro.zone_rect}, подписка={macro._mouse_click_connected}")
            elif macro_type == "zone":
                macro = ZoneMacro(
                    name=data.get("name", "Зона"),
                    app=self,
                    hotkey=data.get("hotkey", ""),
                    zone_rect=tuple(data.get("zone_rect", [0, 0, 0, 0])),
                    steps=data.get("steps", []),
                    poll_interval=data.get("poll_interval", 10)
                )
            elif macro_type == "buff":
                zone_rect = data.get("zone_rect")
                macro = BuffMacro(
                    name=data.get("name", "Бафф"),
                    app=self,
                    hotkey=data.get("hotkey", ""),
                    buff_id=data.get("buff_id", 0),
                    duration=data.get("duration", 60.0),
                    channeling_bonus=data.get("channeling_bonus", 0),
                    steps=data.get("steps", [])
                )
                # Если есть зона - добавляем и подписываем на клики
                if zone_rect and len(zone_rect) == 4:
                    macro.zone_rect = zone_rect
                    macro._connect_mouse_click(self)
                    logger.info(f"[BUFF+ZONE] Бафф '{macro.name}' загружен с областью {macro.zone_rect}")

            return macro
        except Exception as e:
            logger.error(f"[PROFILE] Ошибка создания макроса: {e}")
            return None

    def _macro_to_dict(self, macro):
        """Преобразовать макрос в словарь для сохранения"""
        try:
            logger.debug(f"[PROFILE] Сериализация макроса: {macro.name} (type={macro.type})")
            data = {
                "type": macro.type,
                "name": macro.name,
                "hotkey": macro.hotkey,
                "steps": macro.steps
            }

            if hasattr(macro, 'skill_id'):
                data["skill_id"] = macro.skill_id
                data["cooldown"] = macro.cooldown
                data["skill_range"] = macro.skill_range
                data["cast_time"] = macro.cast_time
                data["castbar_swap_delay"] = macro.castbar_swap_delay
                if hasattr(macro, 'zone_rect') and macro.zone_rect:
                    data["zone_rect"] = list(macro.zone_rect)
                logger.debug(f"[PROFILE] SkillMacro: skill_id={macro.skill_id}, cooldown={macro.cooldown}")

            if hasattr(macro, 'buff_id'):
                data["buff_id"] = macro.buff_id
                data["duration"] = macro.duration
                data["channeling_bonus"] = macro.channeling_bonus
                if hasattr(macro, 'zone_rect') and macro.zone_rect:
                    data["zone_rect"] = list(macro.zone_rect)
                logger.debug(f"[PROFILE] BuffMacro: buff_id={macro.buff_id}, duration={macro.duration}, channeling_bonus={macro.channeling_bonus}")

            if hasattr(macro, 'poll_interval'):
                data["poll_interval"] = macro.poll_interval
                if hasattr(macro, 'zone_rect') and macro.zone_rect:
                    data["zone_rect"] = list(macro.zone_rect)
                logger.debug(f"[PROFILE] ZoneMacro: poll_interval={macro.poll_interval}")

            return data
        except Exception as e:
            logger.error(f"[PROFILE] Ошибка сериализации макроса: {e}")
            return {}

    @Slot()
    def bind_computer(self):
        hwid = auth.get_hwid()
        webbrowser.open(f"https://t.me/snbld_bot?start=bind_{hwid}")

    @Slot()
    def buy_subscription(self):
        webbrowser.open("https://boosty.to/snbld")
    
    # ==================== АКТИВАЦИЯ ПРОГРАММЫ ====================
    
    @Slot(str, result='QVariant')
    def activateProgram(self, key):
        """
        Активирует программу с ключом.
        Возвращает: {success: bool, message: str}
        """
        logger.info(f"[API] Активация программы ключом: {key[:4]}...{key[-4:]}")

        result = self.activateWithKey(key)

        if result.get('success'):
            self.subscriptionChanged.emit()
            return {
                'success': True,
                'message': 'Программа активирована!',
                'key_type': result.get('data', {}).get('key_type', 'unknown'),
                'expires_at': result.get('data', {}).get('expires_at', '')
            }
        else:
            return {
                'success': False,
                'message': result.get('error', 'Ошибка активации'),
                'key_type': '',
                'expires_at': ''
            }
    
    @Property(bool, notify=activationStatusChanged)
    def isActivated(self):
        """Статус активации для блокировки кнопок меню"""
        return self._is_activated

    @Slot(result=bool)
    def isProgramActivated(self):
        """
        Проверяет, активирована ли программа.
        Возвращает: True/False
        """
        return self._is_program_activated()
    
    @Slot(result='QVariant')
    def getActivationStatus(self):
        """
        Получает полный статус активации.
        Возвращает: dict с информацией
        """
        from auth import load_session, load_key_from_file, get_hwid, check_subscription_by_hwid

        session = load_session()
        hwid = get_hwid()
        sub_status = check_subscription_by_hwid(hwid)

        return {
            'activated': self._is_activated,
            'has_session': session is not None,
            'session_id': session[0] if session else None,
            'hwid': hwid,
            'subscription': sub_status
        }
    
    @Slot()
    def openActivationPage(self):
        """
        Открывает страницу активации.
        """
        self.pageChangeRequested.emit("ActivationPage")

    @Slot()
    def minimizeWindow(self):
        """Сворачивает окно в трей или на панель задач"""
        if self._tray_enabled and self._tray_icon_manager:
            self._tray_icon_manager.show_window()
        self.minimizeRequested.emit()

    @Slot()
    def closeWindow(self):
        """Закрывает окно"""
        self.closeRequested.emit()

    # горячие клавиши
    def register_hotkey(self, hotkey, callback, check_window=True, check_global_stop=True, suppress=True):
        """
        Регистрирует горячую клавишу.

        Args:
            hotkey: Клавиша
            callback: Функция обратного вызова
            check_window: Проверять ли окно игры (False для старт/стоп)
            check_global_stop: Проверять ли global_stopped (False для старт/стоп)
            suppress: Блокировать ли клавишу (True для макросов, False для старт/стоп)
        """
        if not hotkey or hotkey in self._hotkey_registered:
            logger.warning(f"register_hotkey: hotkey={hotkey} уже зарегистрирован или пустой!")
            return
        try:
            logger.info(f"[REGISTER] Регистрация hotkey '{hotkey}', check_window={check_window}, check_global_stop={check_global_stop}, suppress={suppress}")

            # Debounce — защита от двойного срабатывания
            _last_press = {'time': 0}
            DEBOUNCE_MS = 200

            # Создаём обёртку которая проверяет окно игры
            def wrapped_callback(e):
                import time
                now = time.time()
                if now - _last_press['time'] < DEBOUNCE_MS / 1000.0:
                    logger.debug(f"[DEBOUNCE] hotkey='{hotkey}' проигнорирован (повтор через {(now - _last_press['time'])*1000:.0f}мс)")
                    return
                _last_press['time'] = now

                logger.debug(f"[WRAPPED] hotkey='{hotkey}' нажата, global_stopped={getattr(self, 'global_stopped', 'N/A')}")

                # Проверяем глобальную блокировку (если требуется)
                if check_global_stop and hasattr(self, 'global_stopped') and self.global_stopped:
                    logger.debug(f"[WRAPPED] hotkey='{hotkey}' проигнорирована: global_stopped=True")
                    return

                # Проверяем активно ли окно игры (если требуется)
                if check_window and hasattr(self, 'window_locked') and self.window_locked:
                    target = self.target_window_title.strip().lower()
                    if target:
                        try:
                            import win32gui
                            hwnd = win32gui.GetForegroundWindow()
                            active_title = win32gui.GetWindowText(hwnd).lower()
                            if target not in active_title:
                                logger.debug(f"Горячая клавиша '{hotkey}' проигнорирована: окно '{active_title}' не активно")
                                return
                        except Exception as e:
                            logger.error(f"Ошибка проверки окна: {e}")

                # Выполняем макрос
                logger.debug(f"[WRAPPED] Вызов callback для hotkey='{hotkey}'")
                callback(e)

            # Используем hook_key с suppress для блокировки клавиши в игре
            keyboard.hook_key(hotkey, wrapped_callback, suppress=suppress)
            self._hotkey_registered.add(hotkey)
            logger.info(f"[REGISTER] [+] Горячая клавиша '{hotkey}' зарегистрирована (suppress={suppress})")
        except Exception as e:
            logger.error(f"Ошибка регистрации {hotkey}: {e}")

    def unregister_hotkey(self, hotkey):
        if hotkey in self._hotkey_registered:
            try:
                keyboard.unhook_key(hotkey)
                self._hotkey_registered.discard(hotkey)
                logger.debug(f"Горячая клавиша удалена: {hotkey}")
            except Exception as e:
                logger.error(f"Ошибка удаления {hotkey}: {e}")

    @Slot(result='QVariant')
    def getWindowList(self):
        """Возвращает список видимых окон для QML"""
        try:
            import win32gui
            import win32process
            import psutil

            windows = []
            def enum_callback(hwnd, hwnds):
                try:
                    if win32gui.IsWindowVisible(hwnd):
                        title = win32gui.GetWindowText(hwnd)
                        if title:
                            hwnds.append((hwnd, title))
                except Exception as e:
                    logger.error(f"Ошибка получения окна: {e}")
                return True

            win32gui.EnumWindows(enum_callback, windows)
            windows.sort(key=lambda x: x[1])

            result = []
            for hwnd, title in windows:
                pid = 0
                process_name = ""
                try:
                    _, pid = win32process.GetWindowThreadProcessId(hwnd)
                    process = psutil.Process(pid)
                    process_name = process.name()
                except Exception:
                    pass

                result.append({
                    "hwnd": hwnd,
                    "title": title,
                    "pid": pid,
                    "processName": process_name
                })

            logger.debug(f"getWindowList: найдено {len(result)} окон")
            return result

        except Exception as e:
            logger.error(f"getWindowList: ОШИБКА: {e}", exc_info=True)
            return []

    @Slot()
    def selectWindowFromList(self):
        """Открывает диалог выбора окна (QML версия)"""
        try:
            logger.debug("selectWindowFromList: вызов функции")

            # Загружаем список окон через backend
            windows = self.getWindowList()

            if not windows:
                self.notification.emit("Нет открытых окон с заголовками", "warning")
                return

            # Открываем QML диалог выбора окна
            if not self.engine:
                logger.error("selectWindowFromList: engine не доступен")
                return

            from utils.resource_utils import resource_path
            qml_file = resource_path("qml/WindowSelectorDialog.qml")
            if not qml_file or not os.path.exists(qml_file):
                self.notification.emit("Файл WindowSelectorDialog.qml не найден", "error")
                return

            from PySide6.QtCore import QUrl
            from PySide6.QtQml import QQmlComponent

            component = QQmlComponent(self.engine, QUrl.fromLocalFile(qml_file))
            if component.isReady():
                dialog = component.create()
                if dialog:
                    # Загружаем список окон
                    dialog.loadWindows()

                    # Подключаем сигналы
                    dialog.windowSelected.connect(self.onWindowSelected)
                    dialog.dialogCancelled.connect(lambda: logger.debug("WindowSelector: Отменено"))

                    dialog.show()
                    logger.info("WindowSelectorDialog: Отображён")
                else:
                    self.notification.emit("Не удалось создать окно выбора", "error")
            else:
                error_str = component.errorString()
                logger.error(f"WindowSelectorDialog load error: {error_str}")
                self.notification.emit("Ошибка загрузки WindowSelectorDialog.qml: " + error_str, "error")

        except Exception as e:
            logger.error(f"selectWindowFromList: ОШИБКА: {e}", exc_info=True)
            self.notification.emit(f"Ошибка: {e}", "error")

    def onWindowSelected(self, title):
        """Обработка выбора окна"""
        logger.info(f"onWindowSelected: выбрано окно '{title}'")
        self.set_target_window(title)
        self.notification.emit(f"Окно выбрано: {title}", "success")

    @Slot()
    def open_window_selector(self):
        """Открыть диалог выбора окна (устарело, используется selectWindowFromList)"""
        self.selectWindowFromList()

    @Slot(str)
    def set_target_window(self, title):
        """Установить целевое окно и заблокировать"""
        try:
            logger.info(f"[WINDOW] ========== set_target_window вызван: {title}")
            
            # Устанавливаем через setter для обновления UI
            self.target_window_title = title
            self.window_locked = True
            
            logger.info(f"[WINDOW] target_window_title={self.target_window_title}, window_locked={self.window_locked}")
            
            self.notification.emit(f"✓ Окно выбрано: {title}", "success")
            logger.info(f"[WINDOW] Выбрано окно: {title}")
        except Exception as e:
            logger.error(f"Ошибка установки окна: {e}")
            import traceback
            traceback.print_exc()
            self.notification.emit(f"⚠ Ошибка: {e}", "error")
    
    # Сигналы для окна
    targetWindowChanged = Signal()
    windowLockedChanged = Signal()

    def register_all_hotkeys(self):
        start_key = self._settings.get("start_all_hotkey", "-")
        stop_key = self._settings.get("stop_all_hotkey", "=")
        
        # СНАЧАЛА unregister'им ВСЕ горячие клавиши макросов (старт/стоп перерегистрируем)
        for hotkey in list(self._hotkey_registered):
            if hotkey not in (start_key, stop_key):
                self.unregister_hotkey(hotkey)
        
        if start_key:
            # Кнопка СТАРТ - работает ВСЕГДА, НЕ блокируем клавишу, НЕ проверяем global_stopped
            self.register_hotkey(start_key, lambda e=None: self.start_all_macros(), check_window=False, check_global_stop=False, suppress=False)
            logger.debug(f"Горячая клавиша ЗАПУСКА '{start_key}' зарегистрирована (check_global_stop=False, suppress=False)")
        if stop_key:
            # Кнопка СТОП - работает ВСЕГДА, НЕ блокируем клавишу, НЕ проверяем global_stopped
            self.register_hotkey(stop_key, lambda e=None: self.stop_all_macros(), check_window=False, check_global_stop=False, suppress=False)
            logger.debug(f"Горячая клавиша ОСТАНОВКИ '{stop_key}' зарегистрирована (check_global_stop=False, suppress=False)")
        
        # Определяем suppress в зависимости от global_stopped
        # Если макросы остановлены (global_stopped=True) → suppress=False (НЕ блокировать клавиши)
        # Если макросы запущены (global_stopped=False) → suppress=True (блокировать клавиши)
        suppress_macros = not self._global_stopped

        for macro in self._macros:
            if macro.hotkey:
                def make_callback(m):
                    def callback(e):
                        event_type = e.event_type if e else 'None'
                        now = time.time()
                        last_start = getattr(m, 'last_start_time', 0)
                        age = now - last_start if last_start > 0 else 999

                        logger.debug(f"Hotkey '{m.hotkey}': running={m.running}, event_type={event_type}, last_start_age={age:.3f}с")

                        # БЫСТРАЯ ПРОВЕРКА блокировки каста (без lock)
                        if now < self.dispatcher.cast_lock_until:
                            remaining = self.dispatcher.cast_lock_until - now
                            logger.debug(f"[CAST LOCK] Горячая клавиша '{m.hotkey}' ЗАБЛОКИРОВАНА: идёт каст (ост. {remaining:.2f}с)")
                            return  # ← Блокируем запуск!

                        # Защита от быстрой остановки (как в старой программе)
                        if m.running and e is not None and event_type in ('up', 'key up'):
                            if last_start > 0 and age < 0.3:
                                logger.debug(f"Игнорируем быструю остановку '{m.name}' (age={age:.3f}с < 0.3с)")
                                return
                            logger.debug(f"Остановка '{m.name}' (age={age:.3f}с >= 0.3с)")
                            m.stop()
                            return

                        # Запуск через диспетчер (если не выполняется)
                        if not m.running:
                            logger.debug(f"Запуск '{m.name}' через диспетчер")
                            # Приоритет 3 для боевых макросов
                            if not self.dispatcher.request_macro(m, priority=3):
                                logger.debug(f"❌ '{m.name}': ЗАБЛОКИРОВАНО диспетчером")
                                return  # ← Блокируем запуск!
                        else:
                            logger.debug(f"Остановка '{m.name}' по callback")
                            m.stop()
                    return callback
                callback = make_callback(macro)
                logger.debug(f"Регистрация горячей клавиши '{macro.hotkey}' для макроса '{macro.name}' с suppress={suppress_macros}")
                # Макросы - suppress зависит от состояния (остановлены/запущены)
                self.register_hotkey(macro.hotkey, callback, check_window=True, check_global_stop=True, suppress=suppress_macros)

    def unregister_all_hotkeys(self):
        for hotkey in list(self._hotkey_registered):
            self.unregister_hotkey(hotkey)

    # настройки
    def load_settings(self):
        """Загружает настройки из settings.json с использованием SettingsManager"""
        from backend.settings_manager import SettingsManager

        settings_path = os.path.join(self.app_dir, 'settings.json')
        settings_manager = SettingsManager(settings_file=settings_path)
        self._settings = settings_manager.get_all()

        # ✅ Применяем все настройки к атрибутам backend
        self._apply_settings_to_attributes()
        
        logger.info(f"Настройки загружены: castbar_enabled={self.castbar_enabled}, castbar_point={self.castbar_point}, castbar_color={self.castbar_color}, castbar_threshold={self.castbar_threshold}")

    def _load_castbar_color(self, color_value):
        """Загружает цвет кастбара из настроек (конвертирует строку в список int)"""
        if isinstance(color_value, str):
            try:
                return [int(x.strip()) for x in color_value.split(',')]
            except Exception:
                return [94, 123, 104]  # значение по умолчанию
        elif isinstance(color_value, list):
            return [int(x) for x in color_value]
        return [94, 123, 104]  # значение по умолчанию

    def save_settings(self):
        """Сохраняет настройки в settings.json и в текущий профиль"""
        import json

        try:
            # 1. Сохраняем в settings.json (рядом с EXE)
            settings_path = os.path.join(self.app_dir, 'settings.json')
            with open(settings_path, 'w', encoding='utf-8') as f:
                json.dump(self._settings, f, indent=2, ensure_ascii=False)
            logger.info("Настройки сохранены в settings.json")
            
            # 2. ✅ Сохраняем в текущий профиль (если активен)
            if self._current_profile:
                logger.debug(f"[PROFILE] Автосохранение настроек в профиль: {self._current_profile}")
                self._save_profile_no_notify(self._current_profile)
            
        except Exception as e:
            logger.error(f"Ошибка сохранения настроек: {e}")
    
    def _save_profile_no_notify(self, name):
        """Сохраняет профиль без уведомлений и смены текущего профиля (для автосохранения)"""
        try:
            profile_data = {
                "settings": dict(self._settings),
                "macros": [self._macro_to_dict(m) for m in self._macros],
                "window_locked": self._settings.get("window_locked", False),
                "target_window_title": self._settings.get("target_window_title", "")
            }
            
            profile_path = os.path.join(self.profiles_dir, f"{name}.json")
            with open(profile_path, 'w', encoding='utf-8') as f:
                json.dump(profile_data, f, ensure_ascii=False, indent=2)
            
            logger.debug(f"[PROFILE] Настройки автосохранены в {name}.json")
            
        except Exception as e:
            logger.error(f"[PROFILE] Ошибка автосохранения: {e}")

    # макросы
    def load_macros(self):
        """Загрузка макросов из macros.json (как в старом проекте)"""
        macro_file = os.path.join(self.app_dir, constants.MACROS_JSON_FILE)
        if not os.path.exists(macro_file):
            self._macros = []
            self._update_macros_dicts()
            return
        
        try:
            with open(macro_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Загружаем настройки окна
            self._window_locked = data.get("window_locked", False)
            self._target_window_title = data.get("target_window_title", "")
            self.window_locked = self._window_locked
            self.target_window_title = self._target_window_title
            self.macrosChanged.emit()

            self._macros = []
            for m_dict in data.get("macros", []):
                macro_type = m_dict["type"]
                name_m = m_dict["name"]
                hotkey = m_dict.get("hotkey")

                if macro_type == "simple":
                    macro = macros.SimpleMacro(name_m, m_dict["steps"], self, hotkey)
                elif macro_type == "zone":
                    macro = macros.ZoneMacro(
                        name=name_m, zone_rect=tuple(m_dict["zone_rect"]), steps=m_dict["steps"], app=self,
                        trigger=m_dict.get("trigger", "left_click"), poll_interval=m_dict.get("poll_interval", 10),
                        hotkey=hotkey, skill_id=m_dict.get("skill_id"), cooldown=m_dict.get("cooldown", 0),
                        skill_range=m_dict.get("skill_range", 0), cast_time=m_dict.get("cast_time", 0.0),
                        castbar_swap_delay=m_dict.get("castbar_swap_delay", 0)
                    )
                    # Автозапуск ZoneMacro - он должен постоянно мониторить область!
                    macro.start()
                    logger.info(f"[ZONE] Макрос '{name_m}' запущен автоматически (мониторинг области)")
                elif macro_type == "skill":
                    macro = macros.SkillMacro(
                        name=name_m, steps=m_dict["steps"], app=self, hotkey=hotkey,
                        skill_id=m_dict["skill_id"], cooldown=m_dict["cooldown"],
                        skill_range=m_dict.get("skill_range", 0), cast_time=m_dict.get("cast_time", 0.0),
                        castbar_swap_delay=m_dict.get("castbar_swap_delay", 0)
                    )
                    # Загружаем zone_rect если есть (для макросов по области)
                    if "zone_rect" in m_dict and m_dict["zone_rect"]:
                        macro.zone_rect = tuple(m_dict["zone_rect"])
                        logger.info(f"[SKILL+ZONE] Загрузка zone_rect={macro.zone_rect} для макроса '{name_m}'")
                        # Подписываем макрос на клики
                        macro._connect_mouse_click(self)
                        logger.info(f"[SKILL+ZONE] Макрос '{name_m}' загружен с областью {macro.zone_rect}, подписка={macro._mouse_click_connected}")
                    else:
                        logger.debug(f"[SKILL+ZONE] Макрос '{name_m}' без зоны (обычный скилл-макрос)")
                elif macro_type == "buff":
                    macro = macros.BuffMacro(
                        name=name_m, steps=m_dict["steps"], app=self, buff_id=m_dict["buff_id"],
                        duration=m_dict["duration"], channeling_bonus=m_dict["channeling_bonus"],
                        hotkey=hotkey, icon=m_dict.get("icon", "buff.png")
                    )
                else:
                    continue
                self._macros.append(macro)
            
            self._update_macros_dicts()
            logger.info(f"Загружено {len(self._macros)} макросов")
        except Exception as e:
            logger.error(f"Ошибка загрузки макросов: {e}")
            self._macros = []
            self._update_macros_dicts()

    def save_macros(self):
        """Сохранение макросов в текущий профиль (автосохранение при изменении макросов)"""
        logger.debug(f"[MACROS] save_macros вызван | _current_profile={self._current_profile} | макросов={len(self._macros)}")
        
        # Сохраняем макросы в текущий профиль если он есть
        if self._current_profile:
            logger.info(f"[MACROS] Сохранение в профиль: {self._current_profile}")
            self.save_profile(self._current_profile)
            logger.debug(f"[PROFILE] Макросы автосохранены в профиль: {self._current_profile}")
        else:
            # Если профиля нет - сохраняем в macros.json для совместимости
            logger.warning(f"[MACROS] Нет активного профиля! Сохранение в macros.json")
            self._save_macros_to_file()
            logger.debug("[MACROS] Макросы сохранены в macros.json (нет активного профиля)")
    
    def _save_macros_to_file(self):
        """Сохранение макросов в macros.json (для совместимости)"""
        macro_file = os.path.join(self.app_dir, constants.MACROS_JSON_FILE)
        data = {
            "window_locked": self._window_locked,
            "target_window_title": self._target_window_title,
            "macros": []
        }

        for m in self._macros:
            macro_dict = {
                "type": m.type,  # Сохраняем ТИП КАК ЕСТЬ!
                "name": m.name,
                "hotkey": m.hotkey,
            }

            if m.type in ("simple", "buff"):
                macro_dict["steps"] = m.steps
                if m.type == "buff":
                    macro_dict["buff_id"] = m.buff_id
                    macro_dict["duration"] = m.duration
                    macro_dict["channeling_bonus"] = m.channeling_bonus
                    macro_dict["icon"] = m.icon

            elif m.type == "zone":
                macro_dict["zone_rect"] = list(m.zone_rect)
                macro_dict["trigger"] = m.trigger
                macro_dict["poll_interval"] = int(m.poll_interval * 1000)
                macro_dict["steps"] = m.steps
                macro_dict["castbar_swap_delay"] = getattr(m, 'castbar_swap_delay', 0)
                if hasattr(m, 'skill_id') and m.skill_id:
                    macro_dict["skill_id"] = m.skill_id
                    macro_dict["cooldown"] = m.cooldown
                    macro_dict["skill_range"] = m.skill_range
                    macro_dict["cast_time"] = m.cast_time
                    
            elif m.type == "skill":
                macro_dict["skill_id"] = m.skill_id
                macro_dict["cooldown"] = m.cooldown
                macro_dict["skill_range"] = m.skill_range
                macro_dict["cast_time"] = m.cast_time
                macro_dict["steps"] = m.steps
                macro_dict["castbar_swap_delay"] = getattr(m, 'castbar_swap_delay', 0)
                # Сохраняем иконку если есть
                if hasattr(m, 'icon') and m.icon:
                    macro_dict["icon"] = m.icon
                # Сохраняем zone_rect если есть (для макросов по области)
                if hasattr(m, 'zone_rect') and m.zone_rect:
                    macro_dict["zone_rect"] = list(m.zone_rect)
            
            data["macros"].append(macro_dict)
        
        try:
            with open(macro_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            logger.info(f"Сохранено {len(self._macros)} макросов")
        except Exception as e:
            logger.error(f"Ошибка сохранения макросов: {e}")
    
    @Slot(int, int)
    def save_window_position(self, x, y):
        """Сохраняет позицию окна"""
        self.window_x = x
        self.window_y = y
        self.save_macros()
    
    @Slot(result=dict)
    def get_window_position(self):
        """Возвращает сохранённую позицию окна"""
        return {"x": self.window_x, "y": self.window_y}

    # OCR (Tesseract - как в старом проекте)
    def start_ocr(self):
        """Запуск OCR мониторинга расстояния (Tesseract)"""
        if self.target_reader:
            return
        
        self._ocr_running = True
        
        areas = {
            "mob": self._settings.get("mob_area", constants.DEFAULT_MOB_AREA),
            "player": self._settings.get("player_area", constants.DEFAULT_PLAYER_AREA)
        }
        
        self.target_reader = tesseract_reader.TargetReader(
            areas,
            interval_per_area=OCR_TARGET_INTERVAL,  # Фиксированный интервал
            scale=self._settings.get("ocr_scale", 10),
            psm=self._settings.get("ocr_psm", 7),
            use_morph=self._settings.get("ocr_use_morph", True),
            check_window=self.is_game_window_active,
            activate_window_title=self._settings.get("target_window_title")
        )
        self.target_reader.data_updated.connect(self.on_distance_updated)
        self.target_reader.start()
        logger.info("[OCR] OCR запущен (Tesseract)")

    def stop_ocr(self):
        """Остановка OCR мониторинга"""
        self._ocr_running = False
        if self.target_reader:
            try:
                self.target_reader.stop()
            except RuntimeError as e:
                # Qt C++ объект уже удалён — это нормально при shutdown
                logger.debug(f"[OCR] TargetReader уже удалён: {e}")
            except Exception as e:
                logger.error(f"[OCR] Ошибка остановки OCR: {e}")
            finally:
                self.target_reader = None
        logger.info("[OCR] OCR остановлен")
    
    @Slot()
    def hide_ocr_overlay(self):
        """Скрывает OCR оверлей — заглушка, оверлей больше не используется"""
        pass

    @Slot()
    def showOCRArea(self):
        """Показать OCR Viewer — заглушка, оверлей больше не используется"""
        pass

    @Slot()
    def selectCastbarPoint(self):
        """Выбор точки для проверки кастбара"""
        logger.debug("selectCastbarPoint: вызов")

        qml_file = resource_path("qml/AreaSelector.qml")
        if not qml_file or not os.path.exists(qml_file):
            self.notification.emit("Файл AreaSelector.qml не найден", "error")
            return

        component = QQmlComponent(self.engine, QUrl.fromLocalFile(qml_file))
        if component.isReady():
            window = component.create()
            if window:
                window.setProperty("targetType", "castbar")
                window.areaSelected.connect(lambda x1, y1, x2, y2: self.onCastbarPointSelected(x1, y1, x2, y2))
                window.cancelled.connect(lambda: self.notification.emit("Выбор точки отменён", "info"))
                window.show()
                logger.info("AreaSelector показан для выбора точки кастбара")
            else:
                self.notification.emit("Не удалось создать окно выбора точки", "error")
        else:
            error_str = component.errorString()
            logger.error(f"AreaSelector load error: {error_str}")
            self.notification.emit("Ошибка загрузки AreaSelector.qml: " + error_str, "error")

    @Slot(result=str)
    def getCursorPosition(self):
        """Возвращает позицию курсора в формате 'x,y'"""
        import win32api
        pos = win32api.GetCursorPos()
        logger.debug(f"getCursorPosition: ({pos[0]}, {pos[1]})")
        return f"{pos[0]},{pos[1]}"

    @Slot(int, int, int, result=str)
    def captureCastbarColorAt(self, x, y, size=1):
        """
        Захват цвета одного пикселя в точке (x, y).
        Возвращает цвет в формате 'R,G,B'.
        """
        try:
            import win32gui
            import win32con

            logger.debug(f"captureCastbarColorAt: ({x}, {y})")

            # Получаем HDC для всего экрана
            hdc = win32gui.GetWindowDC(0)
            
            # ← ПРОВЕРКА: hdc может быть 0 при нехватке ресурсов GDI
            if hdc == 0:
                logger.error("GetWindowDC вернул 0 (недостаточно ресурсов GDI)")
                return "0,0,0"

            # Получаем цвет одного пикселя
            color = win32gui.GetPixel(hdc, x, y)

            win32gui.ReleaseDC(0, hdc)

            if color != win32con.CLR_INVALID:
                # Формат цвета: 0x00BBGGRR
                r = color & 0xFF
                g = (color >> 8) & 0xFF
                b = (color >> 16) & 0xFF
                color_str = f"{r},{g},{b}"
                logger.debug(f"[CASTBAR] Захвачен цвет: RGB({color_str}) в точке ({x},{y})")
                return color_str
            else:
                logger.error("captureCastbarColorAt: Не удалось получить цвет пикселя")
                return "0,0,0"

        except Exception as e:
            logger.error(f"Ошибка захвата цвета: {e}", exc_info=True)
            return "0,0,0"

    @Slot(str, int, result=str)
    def captureCastbarColor(self, point_str, size=5):
        """
        Захват цвета кастбара в указанной точке.
        :param point_str: Строка формата 'x,y'
        :param size: Размер области (по умолчанию 5)
        :return: Цвет в формате 'R,G,B'
        """
        try:
            x, y = map(int, point_str.split(','))
            return self.captureCastbarColorAt(x, y, size)
        except Exception as e:
            logger.error(f"Ошибка парсинга координат: {e}")
            return "0,0,0"

    @Slot()
    def registerCastbarHotkey(self):
        """Регистрирует глобальную горячую клавишу Ctrl+A для калибровки"""
        try:
            import keyboard as kb
            # Регистрируем горячую клавишу Ctrl+A
            kb.add_hotkey('ctrl+a', self._onCastbarHotkey, suppress=True)
            logger.debug("registerCastbarHotkey: Ctrl+A зарегистрирована")
        except Exception as e:
            logger.error(f"Ошибка регистрации горячей клавиши: {e}")

    @Slot()
    def unregisterCastbarCtrlAHotkey(self):
        """Отменяет регистрацию горячей клавиши Ctrl+A"""
        try:
            import keyboard as kb
            kb.remove_hotkey('ctrl+a')
            logger.debug("unregisterCastbarCtrlAHotkey: Ctrl+A удалена")
        except Exception as e:
            logger.error(f"Ошибка отмены регистрации горячей клавиши: {e}")

    # Ссылка на CastBarDialog для вызова метода
    _castbar_dialog_ref = None
    _mouse_hook_manager = None  # Менеджер mouse hook
    _calibration_active = False  # Флаг активной калибровки

    # Ссылка на BuffCalibrationDialog
    _buff_calibration_dialog_ref = None

    @Slot()
    def startBuffCalibration(self):
        """Запускает режим калибровки точки клика для баффа"""
        logger.info("[BUFF] Запуск калибровки точки клика для баффа")
        self.buffCalibrationDialogRequested.emit()

    @Slot(str)
    def onBuffPointCaptured(self, point):
        """Обработка выбора точки для баффа"""
        logger.info(f"[BUFF] Точка клика захвачена: {point}")
        self.set_setting("buff_8004_click_point", point)
        self.buffCalibrationCompleted.emit(point)
        self.notification.emit(f"Точка клика сохранена: {point}", "success")

    @Slot(result=str)
    def getBuffClickPoint(self):
        """Возвращает текущую точку клика для баффа"""
        return self._settings.get("buff_8004_click_point", "0,0")

    @Slot()
    def performBuffClick(self):
        """Выполняет клик по калиброванным координатам баффа"""
        point_str = self._settings.get("buff_8004_click_point", "0,0")
        if point_str == "0,0":
            logger.warning("[BUFF] Точка клика не настроена, пропускаю")
            return

        try:
            parts = point_str.split(",")
            if len(parts) != 2:
                logger.error(f"[BUFF] Неверный формат точки: {point_str}")
                return

            x, y = int(parts[0]), int(parts[1])
            logger.info(f"[BUFF] Выполняю клик в точке ({x}, {y})")

            click_at_position(x, y)
            logger.info(f"[BUFF] Клик выполнен в ({x}, {y})")

        except Exception as e:
            logger.error(f"[BUFF] Ошибка выполнения клика: {e}", exc_info=True)

    @Slot()
    def startCastbarCalibration(self):
        """Запускает режим калибровки (захват по клику мыши)"""
        logger.info("=" * 60)
        logger.info("startCastbarCalibration: ЗАПУСК")
        logger.info(f"startCastbarCalibration: LOW_LEVEL_HOOK_AVAILABLE = {LOW_LEVEL_HOOK_AVAILABLE}")
        logger.info("=" * 60)
        
        if not LOW_LEVEL_HOOK_AVAILABLE:
            logger.error("startCastbarCalibration: low_level_hook НЕ доступен!")
            return
        
        # Разворачиваем окно игры если оно задано
        self.activate_game_window()
        
        self._calibration_active = True
        
        try:
            # Callback для обработки клика мыши
            def on_left_click():
                logger.info("=" * 30)
                logger.info("on_left_click: ЛКМ нажата!")
                logger.info(f"on_left_click: _calibration_active = {self._calibration_active}")
                
                if self._calibration_active:
                    logger.info("on_left_click: Калибровка активна, захват цвета...")
                    self._onCastbarHotkey()
                    return True  # Блокируем клик только если калибровка активна
                logger.info("on_left_click: Калибровка НЕ активна, пропускаем клик")
                return False  # Пропускаем клик дальше
            
            # Создаём и запускаем mouse hook менеджер
            logger.info("startCastbarCalibration: Создание MouseHookManager...")
            self._mouse_hook_manager = MouseHookManager(on_left_click)
            logger.info("startCastbarCalibration: Запуск hook...")
            self._mouse_hook_manager.start()
            
            logger.info("startCastbarCalibration: MouseHookManager запущен УСПЕШНО")
            logger.info(f"startCastbarCalibration: _mouse_hook_manager = {self._mouse_hook_manager}")
            logger.info("=" * 60)
            
        except Exception as e:
            logger.error(f"startCastbarCalibration: ОШИБКА: {e}", exc_info=True)
            logger.error("=" * 60)

    def activate_game_window(self):
        """Разворачивает окно игры если оно задано в настройках"""
        window_title = self.settings.get("target_window_title", "")
        if window_title:
            logger.info(f"activate_game_window: Разворачиваем окно '{window_title}'")
            try:
                import win32gui
                import win32con
                
                def enum_callback(hwnd, hwnds):
                    if win32gui.IsWindowVisible(hwnd):
                        title = win32gui.GetWindowText(hwnd)
                        if window_title.lower() in title.lower():
                            hwnds.append(hwnd)
                    return True
                
                hwnds = []
                win32gui.EnumWindows(enum_callback, hwnds)
                
                if hwnds:
                    hwnd = hwnds[0]
                    # Разворачиваем окно
                    win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
                    win32gui.SetForegroundWindow(hwnd)
                    logger.info(f"activate_game_window: Окно развёрнуто")
                else:
                    logger.warning(f"activate_game_window: Окно '{window_title}' не найдено")
            except Exception as e:
                logger.error(f"activate_game_window: ОШИБКА: {e}")
        else:
            logger.info("activate_game_window: Окно игры не задано в настройках")

    @Slot(QObject)
    def registerCastbarHotkeyForDialog(self, dialog):
        """Регистрирует горячую клавишу с ссылкой на CastBarDialog"""
        logger.info(f"registerCastbarHotkeyForDialog: dialog = {dialog}")
        self._castbar_dialog_ref = dialog
        self.startCastbarCalibration()

    @Slot()
    def stopCastbarCalibration(self):
        """Останавливает режим калибровки"""
        logger.info("stopCastbarCalibration: ВЫЗОВ")
        
        self._calibration_active = False
        
        if self._mouse_hook_manager:
            try:
                self._mouse_hook_manager.stop()
                self._mouse_hook_manager = None
                logger.info("stopCastbarCalibration: MouseHookManager остановлен")
            except Exception as e:
                logger.error(f"stopCastbarCalibration: ОШИБКА: {e}", exc_info=True)

    @Slot()
    def unregisterCastbarHotkey(self):
        """Отменяет регистрацию горячей клавиши"""
        self.stopCastbarCalibration()

    def _onCastbarHotkey(self):
        """Обработчик горячей клавиши — захват цвета кастбара (ОДИН раз)"""
        try:
            logger.info("[CASTBAR] Захват цвета кастбара")

            if not self._castbar_dialog_ref:
                logger.error("[CASTBAR] _castbar_dialog_ref = None!")
                return

            import win32api
            try:
                pos = win32api.GetCursorPos()
            except Exception as e:
                logger.error(f"[CASTBAR] Ошибка GetCursorPos: {e}")
                return

            x, y = pos[0], pos[1]
            logger.info(f"[CASTBAR] Позиция курсора: ({x}, {y})")

            color_str = self.captureCastbarColorAt(x, y, 5)
            logger.info(f"[CASTBAR] Захвачен цвет: RGB({color_str})")

            # Сохраняем результат
            self._castbar_calibration_point = f"{x},{y}"
            self._castbar_calibration_color = color_str

            # ⚠ ВАЖНО: Останавливаем hook СРАЗУ чтобы захватить цвет ТОЛЬКО ОДИН РАЗ
            self._calibration_active = False
            if self._mouse_hook_manager:
                try:
                    self._mouse_hook_manager.stop()
                    logger.info("[CASTBAR] MouseHookManager остановлен после захвата")
                except Exception as e:
                    logger.error(f"[CASTBAR] Ошибка остановки hook: {e}")
                self._mouse_hook_manager = None

            # Отправляем сигнал в QML
            self.castbarColorCaptured.emit(f"{x},{y}", color_str)
            logger.info("[CASTBAR] Калибровка завершена, сигнал отправлен в QML")

        except Exception as e:
            logger.error(f"[CASTBAR] Ошибка захвата цвета: {e}", exc_info=True)
            self._castbar_calibration_color = "0,0,0"

    # Свойства для хранения результатов калибровки
    _castbar_calibration_point = ""
    _castbar_calibration_color = ""

    @Slot(result=str)
    def getCastbarCalibrationPoint(self):
        """Возвращает точку последней калибровки"""
        return self._castbar_calibration_point

    @Slot(result=str)
    def getCastbarCalibrationColor(self):
        """Возвращает цвет последней калибровки"""
        return self._castbar_calibration_color

    @Slot(result=str)
    def getCurrentCastbarColor(self):
        """Возвращает текущий цвет кастбара из настроек в формате 'R,G,B'"""
        try:
            color = self._settings.get("castbar_color", [94, 123, 104])
            if isinstance(color, list) and len(color) >= 3:
                return f"{int(color[0])},{int(color[1])},{int(color[2])}"
            return "94,123,104"
        except Exception as e:
            logger.error(f"Ошибка получения цвета кастбара: {e}")
            return "94,123,104"

    def onCastbarPointSelected(self, x1, y1, x2, y2):
        """Обработка выбора точки кастбара"""
        # Берём центр области
        cx = (x1 + x2) // 2
        cy = (y1 + y2) // 2
        point = f"{cx},{cy}"
        
        logger.info(f"[CASTBAR] Выбрана точка проверки: {point}")
        self.set_setting("castbar_point", point)
        self.notification.emit(f"Точка кастбара: {cx},{cy}", "success")

    @Slot(str)
    def selectOCRArea(self, target_type):
        """
        Запускает режим выбора области OCR
        :param target_type: "mob" или "player"
        """
        logger.info(f"selectOCRArea: запуск для {target_type}")

        # Открываем AreaSelector для выбора области
        self._ocr_area_target = target_type
        self.ocrAreaSelectorRequested.emit(target_type)
        self.notification.emit(f"Выберите область для '{target_type}' на экране", "info")

    @Slot()
    def startOCRCalibration(self):
        """Запуск комплексной калибровки OCR (открывает диалог)"""
        logger.info("[OCR] Запуск комплексной калибровки OCR")
        self.ocrCalibrationDialogRequested.emit()

    # Сигнал для открытия AreaSelector
    ocrAreaSelectorRequested = Signal(str)  # target_type
    
    _ocr_area_target = ""

    @Slot(str, int, int, int, int)
    def onOCRAreaSelected(self, target_type, x1, y1, x2, y2):
        """
        Обработка выбора области OCR
        :param target_type: "mob" или "player"
        :param x1, y1, x2, y2: координаты области
        """
        area = f"{x1},{y1},{x2},{y2}"
        logger.info(f"[OCR] Выбрана область OCR для {target_type}: {area}")

        # Сохраняем область в настройках
        if target_type == "mob":
            self.set_setting("mob_area", f"{x1},{y1},{x2},{y2}")
        elif target_type == "player":
            self.set_setting("player_area", f"{x1},{y1},{x2},{y2}")

        # Обновляем область в Tesseract
        if self.target_reader and self.target_reader.worker:
            self.target_reader.worker.areas[target_type] = (x1, y1, x2, y2)

        # Уведомляем QML
        self.ocrAreaSelected.emit(target_type, area)
        self.notification.emit(f"[+] Область для '{target_type}' сохранена: {area}", "success")

    @Slot(str)
    def testOCRArea(self, target_type):
        """
        Тестирование области OCR
        :param target_type: "mob" или "player"
        """
        logger.debug(f"testOCRArea: вызов для {target_type}")

        # Активируем окно игры перед скриншотом
        import time
        try:
            import win32gui
            window_title = self._settings.get("target_window_title", "")
            if window_title:
                def find_window(hwnd, result):
                    if win32gui.IsWindowVisible(hwnd):
                        title = win32gui.GetWindowText(hwnd)
                        if window_title.lower() in title.lower():
                            result.append(hwnd)
                hwnds = []
                win32gui.EnumWindows(lambda h, _: find_window(h, hwnds), None)
                if hwnds:
                    win32gui.SetForegroundWindow(hwnds[0])
                    time.sleep(0.15)
                    logger.debug(f"[testOCRArea] Окно активировано: {window_title}")
        except Exception as e:
            logger.debug(f"[testOCRArea] Не удалось активировать окно: {e}")

        # Делаем скриншот ВСЕГО монитора (test_area сам вырежет область)
        import mss
        try:
            with mss.mss() as sct:
                mon = sct.monitors[1] if len(sct.monitors) > 1 else sct.monitors[0]
                screenshot = sct.grab(mon)
                screenshot_np = np.array(screenshot)

            # Тестируем область через Tesseract
            if self.target_reader and self.target_reader.worker:
                result = self.target_reader.worker.test_area(screenshot_np, target_type)
            else:
                # Если target_reader не запущен, создаём временный worker
                # С ТЕМИ ЖЕ настройками что и в backend
                areas = {
                    target_type: self._settings.get(f"{target_type}_area", (0, 0, 0, 0))
                }
                worker = TargetWorker(
                    areas,
                    interval=OCR_TARGET_INTERVAL,
                    scale=self._settings.get("ocr_scale", 10),
                    psm=self._settings.get("ocr_psm", 7),
                    use_morph=self._settings.get("ocr_use_morph", True),
                    skip_activate_window=True
                )
                result = worker.test_area(screenshot_np, target_type)

            logger.info(f"[OCR] Тест OCR для {target_type}: {result}")

            # Преобразуем изображение в base64 для передачи в QML
            image_source = None
            if result.get("image") is not None:
                import io
                import base64
                from PIL import Image
                img = Image.fromarray(result["image"])
                buffered = io.BytesIO()
                img.save(buffered, format="PNG")
                image_source = "data:image/png;base64," + base64.b64encode(buffered.getvalue()).decode()

            # Отправляем результат в QML
            self.ocrTestResult.emit(target_type, {
                "success": result.get("success", False),
                "distance": result.get("distance"),
                "numbers": result.get("numbers", []),
                "image": image_source,
                "area": result.get("area"),
                "engine": "Tesseract"
            })

            if result.get("distance"):
                self.notification.emit(f"Распознано: {result['distance']} м (Tesseract)", "success")
            else:
                self.notification.emit("Не распознано. Попробуйте другую область.", "warning")

        except Exception as e:
            logger.error(f"Ошибка тестирования OCR: {e}", exc_info=True)
            self.notification.emit(f"Ошибка: {e}", "error")

    def is_game_window_active(self):
        """Проверяет активно ли окно игры"""
        window_title = self.settings.get("target_window_title", "")
        if not window_title:
            return True  # Если окно не задано — разрешаем

        try:
            import win32gui
            hwnd = win32gui.GetForegroundWindow()
            if hwnd:
                active_title = win32gui.GetWindowText(hwnd)
                return window_title.lower() in active_title.lower()
        except Exception as e:
            logger.error(f"is_game_window_active: Ошибка: {e}")

        return False

    # Castbar детекция
    _castbar_cache = {'visible': False, 'timestamp': 0}
    _castbar_cache_lock = threading.Lock()
    
    def is_castbar_visible(self):
        """Проверка с кэшированием (10 мс)"""
        if not self.castbar_enabled:
            return False
        
        # Проверяем кэш (мгновенно!)
        with self._castbar_cache_lock:
            age = time.time() - self._castbar_cache['timestamp']
            if age < 0.010:  # Кэш актуален 10 мс
                return self._castbar_cache['visible']
        
        # Кэш устарел - проверяем напрямую
        return self._check_castbar_direct()
    
    def _check_castbar_direct(self):
        """
        Прямая проверка кастбара с улучшенной логикой.
        - Захватывает область 5x5 пикселей вокруг точки
        - Считает сколько пикселей совпадают с эталонным цветом
        - Кастбар виден если >= 30% пикселей совпали ИЛИ лучшее совпадение очень близкое
        """
        try:
            x, y = map(int, self.castbar_point.split(','))

            import mss
            with mss.mss() as sct:
                left = max(0, int(x) - 2)
                top = max(0, int(y) - 2)
                width = 5
                height = 5
                monitor = {"left": left, "top": top, "width": width, "height": height}
                screenshot = sct.grab(monitor)

                target_r = self.castbar_color[0]
                target_g = self.castbar_color[1]
                target_b = self.castbar_color[2]
                threshold = self.castbar_threshold

                match_count = 0
                total_pixels = width * height
                best_diff = float('inf')

                for dy in range(height):
                    for dx in range(width):
                        idx = (dy * width + dx) * 3
                        r = screenshot.rgb[idx]
                        g = screenshot.rgb[idx + 1]
                        b = screenshot.rgb[idx + 2]

                        diff = abs(r - target_r) + abs(g - target_g) + abs(b - target_b)

                        if diff < best_diff:
                            best_diff = diff

                        if diff <= threshold:
                            match_count += 1

                match_ratio = match_count / total_pixels if total_pixels > 0 else 0
                is_visible = (match_ratio >= 0.3) or (best_diff <= threshold // 2)

                # Диагностика при отладке
                if not is_visible and best_diff < threshold * 2:
                    logger.debug(
                        f"[CASTBAR] Почти: точка=({x},{y}), match={match_count}/{total_pixels} ({match_ratio:.0%}), "
                        f"best_diff={best_diff}, порог={threshold}, {'✅' if is_visible else '❌'}"
                    )

                with self._castbar_cache_lock:
                    self._castbar_cache['visible'] = is_visible
                    self._castbar_cache['timestamp'] = time.time()

                return is_visible
        except Exception as e:
            logger.error(f"[CASTBAR] Ошибка проверки: {e}")
            return False

    @Slot(result=float)
    def getPingCompensation(self):
        """Возвращает компенсацию пинга в секундах с учётом игрового коэффициента"""
        icmp_ping = self._settings.get("average_ping", 30)
        
        # Коэффициент для Perfect World (ICMP → Игровой пинг)
        GAME_PING_MULTIPLIER = 2.0  # Было 3.0
        game_ping = icmp_ping * GAME_PING_MULTIPLIER
        
        # Компенсация на основе игрового пинга
        compensation = min(game_ping / 1000.0 * 0.7 + 0.02, 0.3)
        return compensation

    def get_ping_compensation(self):
        """Получение пинг компенсации"""
        icmp_ping = self._settings.get("average_ping", 30)
        
        # Коэффициент для Perfect World (ICMP → Игровой пинг)
        GAME_PING_MULTIPLIER = 2.0  # Было 3.0
        game_ping = icmp_ping * GAME_PING_MULTIPLIER
        
        return game_ping / 1000.0  # конвертируем в секунды

    def on_distance_updated(self, target_type, distance, numbers):
        """Обновление дистанции от Tesseract"""
        # Просто используем расстояние от того кто прислал (активный ридер)
        if distance is not None:
            # Обновляем ТОЛЬКО если расстояние реалистичное (0.5-200м)
            if 0.5 <= distance <= 200:
                if self._target_distance != distance:
                    self._target_distance = distance
                    self._last_ocr_numbers = numbers if numbers is not None else []
                    # Сигнал требует 3 аргумента: target_type, distance, numbers
                    self.distanceUpdated.emit(target_type, distance, self._last_ocr_numbers)
                logger.debug(f"[DIST] {target_type}: {distance:.1f}м")
            else:
                logger.debug(f"[DIST] {target_type}: нереальное {distance:.1f}м - игнорируем")
        # Если distance is None - оставляем последнее значение (не сбрасываем!)

    def get_current_ocr_image(self, target_type="mob"):
        """Возвращает последнее обработанное изображение из Tesseract"""
        if self.target_reader and self.target_reader.worker:
            return self.target_reader.worker.get_last_processed(target_type)
        return None

    # пинг
    def on_ping_updated(self, ping):
        self._ping = ping
        self.pingUpdated.emit(ping)
        self._settings["average_ping"] = ping
        
        # Если включен режим автозадержек - пересчитываем задержки в макросах
        if self._settings.get("use_ping_delays", False):
            self.recalculate_macro_delays()
        
        # Сохраняем только если ping_auto включен
        if self._settings.get("ping_auto", True):
            self.save_settings()

    @Slot()
    def testPing(self):
        """Ручной тест пинга"""
        logger.info(f"[PING] Ручной тест пинга...")
        # Безопасно останавливаем старый PingMonitor
        self._stop_ping_monitor()
        # Создаём новый для немедленного измерения
        interval = self._settings.get("ping_check_interval", 5)
        self.ping_monitor = threads.PingMonitor(self._settings.get("process_name", "elementclient.exe"), interval)
        self.ping_monitor.ping_updated.connect(self.on_ping_updated)
        self.ping_monitor.start()
        self.notification.emit("Запуск теста пинга...", "info")

    # баффы
    def apply_buff(self, buff_id, name, duration, channeling_bonus, icon):
        with self.buff_lock:
            self.active_buffs[buff_id] = {
                "name": name,
                "end_time": time.time() + duration,
                "bonus": channeling_bonus,
                "icon": icon
            }
        self.activeBuffsUpdated.emit()

    def _on_buff_expired(self, buff_id):
        """Обработка истёкшего баффа от BuffCheckThread"""
        logger.info(f"[BUFF] Бафф {buff_id} истёк, удалён")
        self.activeBuffsUpdated.emit()

    def get_active_buffs_snapshot(self):
        """Возвращает безопасную копию активных баффов для использования в других потоках"""
        with self.buff_lock:
            return dict(self.active_buffs)

    def get_current_channeling_bonus(self):
        """Получает суммарный бонус к пению (база + баффы)"""
        bonus = self._settings.get("base_channeling", 0)
        with self.buff_lock:
            for buff in self.active_buffs.values():
                bonus += buff["bonus"]
        return bonus

    def get_actual_cast_time(self, base_cast_time):
        bonus_total = self.get_current_channeling_bonus()
        if bonus_total > 0:
            actual = base_cast_time * 100.0 / (100.0 + bonus_total)
            logger.debug(f"[CAST_TIME] base={base_cast_time:.2f}с, bonus={bonus_total}%, actual={actual:.2f}с")
            return actual
        return base_cast_time

    def lock_cast(self, duration):
        self.cast_lock_until = time.time() + duration
        logger.debug(f"[LOCK_CAST] Блокировка установлена: cast_lock_until={self.cast_lock_until:.3f}, now={time.time():.3f}, duration={duration:.2f}с")

    def is_cast_locked(self):
        now = time.time()
        locked = now < self.cast_lock_until
        remaining = self.cast_lock_until - now if locked else 0
        logger.debug(f"[IS_CAST_LOCKED] cast_lock_until={self.cast_lock_until:.3f}, now={now:.3f}, locked={locked}, remaining={remaining:.2f}с")
        return locked

    def init_subsystems(self):
        self.skill_db = skill_database.SkillDatabase(constants.SKILLS_JSON_FILE)
        hwid = auth.get_hwid()
        valid, info = auth.check_subscription_by_hwid(hwid)
        self._subscription_info = info
        self.subscriptionChanged.emit()
        if not valid:
            logger.warning("Подписка не активна, демо-режим")

        # Загрузка иконок скиллов в кеш
        if self.skill_db:
            from utils import ensure_skill_icons
            skill_list = self.skill_db.get_all_skills_simple()
            ensure_skill_icons(skill_list)
            logger.info(f"[ICONS] [+] Иконки скиллов загружены в кеш")

        # Инициализация переменных для макросов
        self.target_distance = None
        self.cast_lock_until = 0
        # castbar_enabled уже загружен из настроек в load_settings()

        self.movement_monitor = threads.MovementMonitor()
        self.movement_monitor.start()

        # Запускаем монитор кликов мыши (для зональных макросов)
        self.mouse_click_monitor = threads.MouseClickMonitor()
        self.mouse_click_monitor.start()
        logger.info("[MOUSE] MouseClickMonitor запущен")

        # Запускаем проверку истечения баффов
        from threads import BuffCheckThread
        self.buff_check_thread = BuffCheckThread(self)
        self.buff_check_thread.buffExpired.connect(self._on_buff_expired)
        self.buff_check_thread.start()
        logger.info("[BUFF] BuffCheckThread запущен")

        # Проверка обновлений (асинхронно, через 3 сек после запуска)
        from PySide6.QtCore import QTimer
        QTimer.singleShot(3000, lambda: self._check_updates_and_notify())

        if self._settings.get("ping_auto", True):
            interval = self._settings.get("ping_check_interval", 5)
            logger.info(f"[PING] Запуск PingMonitor: интервал={interval}сек, process={self._settings['process_name']}")
            self.ping_monitor = threads.PingMonitor(self._settings["process_name"], interval)
            self.ping_monitor.ping_updated.connect(self.on_ping_updated)
            self.ping_monitor.start()
        else:
            logger.info(f"[PING] PingMonitor отключен (ping_auto=False)")
        self.load_macros()
        # Пересчитываем задержки при старте (если включен ping режим)
        if self._settings.get("use_ping_delays", False):
            self.recalculate_macro_delays()
        
        # OCR запускается кнопкой СТАРТ (не запускаем автоматически)
        logger.info("[OCR] OCR не запущен - нажмите СТАРТ для запуска")
        self.register_all_hotkeys()

    def cleanup(self):
        # Защита от ДВОЙНОГО вызова (eventFilter + aboutToQuit)
        if getattr(self, '_cleanup_done', False):
            return
        logger.info("Остановка программы...")

        # 1. Останавливаем горячие клавиши
        self.unregister_all_hotkeys()

        # 2. Останавливаем ВСЕ макросы (каждый макрос — отдельный поток!)
        logger.debug("Остановка всех макросов...")
        for macro in self._macros:
            try:
                macro.stop()
            except Exception:
                pass
        # Ждём завершения потоков макросов
        for macro in self._macros:
            if macro.thread and macro.thread.is_alive():
                macro.thread.join(timeout=2.0)

        # 3. Останавливаем диспетчер очереди
        if hasattr(self, 'dispatcher') and self.dispatcher:
            logger.debug("Остановка диспетчера макросов...")
            try:
                self.dispatcher.stop()
            except Exception:
                pass

        # 4. Останавливаем MouseClickMonitor (QThread)
        if self.mouse_click_monitor:
            logger.debug("Остановка MouseClickMonitor...")
            try:
                self.mouse_click_monitor.stop()
                if self.mouse_click_monitor.isRunning():
                    self.mouse_click_monitor.wait(500)
            except Exception as e:
                logger.debug(f"[CLEANUP] MouseClickMonitor error: {e}")

        # 5. Останавливаем OCR (QThread)
        if self.target_reader:
            logger.debug("Остановка OCR...")
            try:
                self.target_reader.stop()
                if self.target_reader.isRunning():
                    self.target_reader.wait(500)
            except Exception as e:
                logger.debug(f"[CLEANUP] OCR error: {e}")

        # 6. Останавливаем PingMonitor (QThread)
        if self.ping_monitor:
            logger.debug("Остановка PingMonitor...")
            try:
                self._stop_ping_monitor()
            except Exception as e:
                logger.debug(f"[CLEANUP] PingMonitor error: {e}")

        # 7. Останавливаем MovementMonitor (threading.Thread)
        if self.movement_monitor:
            logger.debug("Остановка MovementMonitor...")
            self.movement_monitor.stop()

        # 7b. Останавливаем BuffCheckThread (QThread)
        if self.buff_check_thread:
            logger.debug("Остановка BuffCheckThread...")
            try:
                self.buff_check_thread.stop()
                if self.buff_check_thread.isRunning():
                    self.buff_check_thread.wait(500)
            except Exception as e:
                logger.debug(f"[CLEANUP] BuffCheckThread error: {e}")

        # 7a. Останавливаем MouseHookManager (QThread для калибровки кастбара)
        if hasattr(self, '_mouse_hook_manager') and self._mouse_hook_manager:
            logger.debug("Остановка MouseHookManager...")
            try:
                self._mouse_hook_manager.stop()
                if self._mouse_hook_manager.isRunning():
                    self._mouse_hook_manager.wait(1000)
            except Exception as e:
                logger.debug(f"[CLEANUP] MouseHookManager error: {e}")

        # 8. Сохраняем настройки и макросы
        logger.debug("Сохранение настроек...")
        self.save_settings()
        logger.debug("Сохранение макросов...")
        self.save_macros()

        # 9. Сохраняем текущий профиль (если есть)
        if self._current_profile:
            logger.info(f"[CLEANUP] Сохранение профиля '{self._current_profile}' перед закрытием...")
            self.save_profile(self._current_profile)

        # Помечаем что cleanup已完成 (защита от двойного вызова)
        self._cleanup_done = True

        # Закрываем глобальный лог shiboken
        global shiboken_log
        if shiboken_log:
            try:
                shiboken_log.flush()
                shiboken_log.close()
                shiboken_log = None
            except Exception:
                pass

        logger.info("Завершение работы.")

    def __del__(self):
        """Гарантированная очистка QThread при уничтожении объекта (защита от GC)"""
        try:
            # Дополнительная остановка QThread которые могли остаться живыми
            if hasattr(self, 'target_reader') and self.target_reader:
                try:
                    if self.target_reader.isRunning():
                        self.target_reader.stop()
                        self.target_reader.wait(1000)
                except Exception:
                    pass
            if hasattr(self, 'ping_monitor') and self.ping_monitor:
                try:
                    if self.ping_monitor.isRunning():
                        self.ping_monitor.stop()
                        self.ping_monitor.wait(1000)
                except Exception:
                    pass
            if hasattr(self, 'mouse_click_monitor') and self.mouse_click_monitor:
                try:
                    if self.mouse_click_monitor.isRunning():
                        self.mouse_click_monitor.stop()
                        self.mouse_click_monitor.wait(1000)
                except Exception:
                    pass
        except Exception:
            pass  # __del__ НЕ должен выбрасывать исключения

    def open_macro_dialog(self, macro_type):
        if macro_type == "simple" and self.engine:
            try:
                qml_file = os.path.join(self.app_dir, "qml", "SimpleMacroDialog.qml")
                component = QQmlComponent(self.engine, QUrl.fromLocalFile(qml_file))
                if component.isReady():
                    dialog = component.create()
                    if dialog:
                        dialog.open()
                else:
                    self.notification.emit("Ошибка загрузки диалога", "error")
            except Exception as e:
                logger.error(f"Ошибка открытия диалога: {e}")
                self.notification.emit(f"Ошибка: {e}", "error")
        else:
            self.notification.emit(f"Создание макроса типа {macro_type} (в разработке)", "info")

    # Создание простых
    @Slot(str, str, list)
    def create_simple_macro_with_params(self, name, hotkey, steps):
        try:
            macro = macros.SimpleMacro(name, steps, self, hotkey if hotkey else "")
            self._macros.append(macro)
            self.save_macros()
            self._update_macros_dicts()
            self.notification.emit(f"Макрос '{name}' создан", "success")
        except Exception as e:
            logger.error(f"Ошибка создания макроса: {e}")
            self.notification.emit(f"Ошибка создания макроса: {e}", "error")

    # Создание зональных
    @Slot(str, str, list, list, str, int)
    def create_zone_macro_with_params(self, name, hotkey, zone_rect, steps, trigger, poll_interval_ms):
        try:
            poll_interval = poll_interval_ms / 1000.0
            macro = macros.ZoneMacro(
                name, zone_rect, steps, self,
                trigger=trigger,
                poll_interval=poll_interval,
                hotkey=hotkey if hotkey else "",
                skill_id=None,
                cooldown=0,
                skill_range=0,
                cast_time=0,
                castbar_swap_delay=0
            )
            self._macros.append(macro)
            self.save_macros()
            self._update_macros_dicts()
            self.notification.emit(f"Зональный макрос '{name}' создан", "success")
        except Exception as e:
            logger.error(f"Ошибка создания зонального макроса: {e}")
            self.notification.emit(f"Ошибка: {e}", "error")

    # Редактирование зональных
    @Slot(str, str, str, list, list, str, int)
    def update_zone_macro(self, old_name, new_name, hotkey, zone_rect, steps, trigger, poll_interval_ms):
        try:
            for i, macro in enumerate(self._macros):
                if macro.name == old_name and macro.type == "zone":
                    poll_interval = poll_interval_ms / 1000.0
                    new_macro = macros.ZoneMacro(
                        new_name, zone_rect, steps, self,
                        trigger=trigger,
                        poll_interval=poll_interval,
                        hotkey=hotkey if hotkey else "",
                        skill_id=None,
                        cooldown=0,
                        skill_range=0,
                        cast_time=0,
                        castbar_swap_delay=0
                    )
                    self._macros[i] = new_macro
                    self.save_macros()
                    self._update_macros_dicts()
                    self.notification.emit(f"Зональный макрос '{new_name}' обновлён", "success")
                    return
            self.notification.emit("Макрос не найден", "error")
        except Exception as e:
            logger.error(f"Ошибка обновления зонального макроса: {e}")
            self.notification.emit(f"Ошибка: {e}", "error")

    # Редактирование простых
    @Slot(str, str, str, list)
    def update_simple_macro(self, old_name, new_name, hotkey, steps):
        try:
            for i, macro in enumerate(self._macros):
                if macro.name == old_name and macro.type == "simple":
                    new_macro = macros.SimpleMacro(new_name, steps, self, hotkey if hotkey else "")
                    self._macros[i] = new_macro
                    self.save_macros()
                    self._update_macros_dicts()
                    self.notification.emit(f"Макрос '{new_name}' обновлён", "success")
                    return
            self.notification.emit("Макрос не найден", "error")
        except Exception as e:
            logger.error(f"Ошибка обновления макроса: {e}")
            self.notification.emit(f"Ошибка: {e}", "error")

    # Редактирование: устанавливаем имя макроса для редактирования
    @Slot(dict)
    def set_macro_for_edit(self, macro_dict):
        self._macro_name_for_edit = macro_dict["name"]
        self._macro_for_edit = macro_dict  # Сохраняем весь макрос
        logger.debug(f"set_macro_for_edit -> name={self._macro_name_for_edit}")

    @Property(dict, notify=macrosChanged)
    def macro_for_edit(self):
        """Получить макрос для редактирования"""
        result = getattr(self, '_macro_for_edit', None)
        return result if result is not None else {}

    @Slot(result=dict)
    def get_macro_for_edit(self):
        if not hasattr(self, '_macro_name_for_edit') or not self._macro_name_for_edit:
            logger.debug("get_macro_for_edit -> no name set")
            return None
        name = self._macro_name_for_edit
        # НЕ очищаем имя здесь, очистим после сохранения
        logger.debug(f"get_macro_for_edit: searching for macro '{name}'")
        for macro in self._macros:
            if macro.name == name:
                logger.debug(f"found macro: {macro.name}, type={macro.type}")
                result = {
                    "name": macro.name,
                    "type": macro.type,
                    "hotkey": macro.hotkey or "",
                    "steps": macro.steps if hasattr(macro, "steps") else [],
                    "running": macro.running,
                    "cooldown": getattr(macro, "cooldown", 0),
                    "skill_range": getattr(macro, "skill_range", 0),
                }
                if macro.type == "zone":
                    result["zone_rect"] = list(macro.zone_rect) if hasattr(macro, "zone_rect") and macro.zone_rect else []
                    result["trigger"] = macro.trigger if hasattr(macro, "trigger") else "left_click"
                    result["poll_interval"] = macro.poll_interval if hasattr(macro, "poll_interval") else 10
                if macro.type == "skill":
                    result["skill_id"] = macro.skill_id if hasattr(macro, "skill_id") else None
                    result["cooldown"] = macro.cooldown if hasattr(macro, "cooldown") else 0
                    result["skill_range"] = macro.skill_range if hasattr(macro, "skill_range") else 0
                    result["cast_time"] = macro.cast_time if hasattr(macro, "cast_time") else 0.0
                    result["castbar_swap_delay"] = macro.castbar_swap_delay if hasattr(macro, "castbar_swap_delay") else 0
                    result["zone_rect"] = list(macro.zone_rect) if hasattr(macro, "zone_rect") and macro.zone_rect else []
                if macro.type == "buff":
                    result["buff_id"] = macro.buff_id if hasattr(macro, "buff_id") else None
                    result["duration"] = macro.duration if hasattr(macro, "duration") else 0
                    result["channeling_bonus"] = macro.channeling_bonus if hasattr(macro, "channeling_bonus") else 0
                    result["icon"] = macro.icon if hasattr(macro, "icon") else ""
                return result
        logger.debug(f"macro '{name}' not found")
        return None

    @Slot()
    def clear_macro_for_edit(self):
        """Очистить имя макроса после редактирования"""
        self._macro_name_for_edit = None
        self._macro_for_edit = None
        self.macrosChanged.emit()

    @Slot(dict)
    def save_macro(self, macro_dict):
        """
        Сохраняет макрос из словаря (после редактирования).
        Создаёт новый макрос или обновляет существующий.
        """
        try:
            name = macro_dict.get("name", "")
            macro_type = macro_dict.get("type", "simple")
            hotkey = macro_dict.get("hotkey", "")
            steps = macro_dict.get("steps", [])
            
            if not name:
                self.notification.emit("Имя макроса не может быть пустым", "error")
                return
            
            # Проверяем, существует ли макрос с таким именем (для обновления)
            old_name = macro_dict.get("old_name", name)
            existing_macro = None
            for m in self._macros:
                if m.name == old_name:
                    existing_macro = m
                    break
            
            # Создаём новый макрос в зависимости от типа
            new_macro = None
            
            if macro_type == "simple":
                new_macro = macros.SimpleMacro(name, steps, self, hotkey if hotkey else "")
            
            elif macro_type == "zone":
                zone_rect = macro_dict.get("zone_rect", [])
                trigger = macro_dict.get("trigger", "left_click")
                poll_interval = macro_dict.get("poll_interval", 10)
                skill_id = macro_dict.get("skill_id")
                cooldown = macro_dict.get("cooldown", 0)
                skill_range = macro_dict.get("skill_range", 0)
                cast_time = macro_dict.get("cast_time", 0.0)
                castbar_swap_delay = macro_dict.get("castbar_swap_delay", 0)
                
                new_macro = macros.ZoneMacro(
                    name, zone_rect, steps, self,
                    trigger=trigger,
                    poll_interval=poll_interval,
                    hotkey=hotkey if hotkey else "",
                    skill_id=skill_id,
                    cooldown=cooldown,
                    skill_range=skill_range,
                    cast_time=cast_time,
                    castbar_swap_delay=castbar_swap_delay
                )
            
            elif macro_type == "skill":
                skill_id = macro_dict.get("skill_id")
                cooldown = macro_dict.get("cooldown", 0)
                skill_range = macro_dict.get("skill_range", 0)
                cast_time = macro_dict.get("cast_time", 0.0)
                castbar_swap_delay = macro_dict.get("castbar_swap_delay", 0)
                zone_rect = macro_dict.get("zone_rect")
                
                # Получаем иконку скилла
                icon = ""
                if skill_id and self.skill_db:
                    skill = self.skill_db.get_skill(int(skill_id))
                    if skill:
                        icon = skill.icon
                
                new_macro = macros.SkillMacro(
                    name, steps, self, hotkey if hotkey else "",
                    skill_id=skill_id,
                    cooldown=cooldown,
                    skill_range=skill_range,
                    cast_time=cast_time,
                    castbar_swap_delay=castbar_swap_delay,
                    icon=icon
                )
                
                # Если есть зона - добавляем
                if zone_rect and len(zone_rect) == 4:
                    new_macro.zone_rect = zone_rect
            
            elif macro_type == "buff":
                buff_id = macro_dict.get("buff_id")
                duration = macro_dict.get("duration", 0)
                channeling_bonus = macro_dict.get("channeling_bonus", 0)
                icon = macro_dict.get("icon", "buff.png")
                zone_rect = macro_dict.get("zone_rect")
                
                # Получаем иконку баффа
                if buff_id and self.skill_db:
                    buff = self.skill_db.get_buff(int(buff_id))
                    if buff:
                        icon = buff.icon
                
                new_macro = macros.BuffMacro(
                    name, steps, self,
                    buff_id=buff_id,
                    duration=duration,
                    channeling_bonus=channeling_bonus,
                    hotkey=hotkey if hotkey else "",
                    icon=icon
                )
                
                # Если есть зона - добавляем
                if zone_rect and len(zone_rect) == 4:
                    new_macro.zone_rect = zone_rect
            
            if new_macro:
                if existing_macro:
                    # Обновляем существующий макрос
                    # Сначала unregister старую горячую клавишу если изменилась
                    if existing_macro.hotkey and existing_macro.hotkey != hotkey:
                        self.unregister_hotkey(existing_macro.hotkey)

                    index = self._macros.index(existing_macro)
                    self._macros[index] = new_macro
                    self.notification.emit(f"Макрос '{name}' обновлён", "success")
                else:
                    # Добавляем новый макрос
                    # Проверяем нет ли макроса с такой горячей клавишей
                    for existing_m in self._macros:
                        if existing_m.hotkey == hotkey:
                            logger.debug(f"Горячая клавиша '{hotkey}' уже используется макросом '{existing_m.name}', удаляем")
                            self.unregister_hotkey(hotkey)
                            # Удаляем горячую клавишу из старого макроса
                            existing_m.hotkey = None
                            break
                    
                    self._macros.append(new_macro)
                    self.notification.emit(f"Макрос '{name}' создан", "success")
                
                # Регистрируем горячую клавишу (сначала удаляем старую если есть)
                if hotkey:
                    # Проверяем нет ли уже макроса с такой горячей клавишей
                    for existing_m in self._macros:
                        if existing_m.hotkey == hotkey and existing_m != new_macro:
                            logger.debug(f"Горячая клавиша '{hotkey}' уже используется макросом '{existing_m.name}', удаляем")
                            self.unregister_hotkey(hotkey)
                            break

                    def make_callback(m):
                        def callback(e=None):
                            # Запускаем макрос через диспетчер только если он не выполняется
                            if not m.running:
                                # Приоритет 3 для боевых скилл-макросов
                                if not self.dispatcher.request_macro(m, priority=3):
                                    logger.debug(f"❌ '{m.name}': ЗАБЛОКИРОВАНО диспетчером")
                                    return
                            # Игнорируем повторные нажатия пока макрос выполняется
                        return callback
                    self.register_hotkey(hotkey, make_callback(new_macro))
                
                self.save_macros()
                self._update_macros_dicts()
        
        except Exception as e:
            logger.error(f"Ошибка сохранения макроса: {e}", exc_info=True)
            self.notification.emit(f"Ошибка: {e}", "error")

    @Slot(str, dict)
    def create_macro_from_dict(self, macro_type, macro_dict):
        """
        Создаёт макрос из словаря с указанным типом.
        Обёртка над save_macro для совместимости.
        """
        macro_dict["type"] = macro_type
        self.save_macro(macro_dict)

    # Создание скилл-макроса
    @Slot(str, str, str, list, str, float, float, float, float, list)
    def create_skill_macro_with_params(self, name, hotkey, skill_id, steps, skill_hotkey,
                                       cooldown, skill_range, cast_time, castbar_swap_delay, zone_rect):
        try:
            logger.debug(f"create_skill_macro_with_params: name={name}, skill_id={skill_id}, skill_hotkey={skill_hotkey}, zone_rect={zone_rect}")
            # Получаем иконку скилла
            icon = ""
            if skill_id:
                skill = self.skill_db.get_skill(int(skill_id))
                if skill:
                    icon = skill.icon

            # Используем skill_hotkey как горячую клавишу макроса (если hotkey пуст)
            macro_hotkey = skill_hotkey if not hotkey else hotkey
            logger.debug(f"macro_hotkey={macro_hotkey}, hotkey={hotkey}, skill_hotkey={skill_hotkey}")

            macro = macros.SkillMacro(
                name, steps, self, macro_hotkey if macro_hotkey else "",
                skill_id=int(skill_id) if skill_id else None,
                cooldown=cooldown,
                skill_range=skill_range,
                cast_time=cast_time,
                castbar_swap_delay=castbar_swap_delay
            )
            # Сохраняем иконку в атрибут макроса
            macro.icon = icon
            logger.debug(f"Макрос создан: name={name}, hotkey={macro.hotkey}, icon={icon}")
            
            # Если зональный макрос - сохраняем зону и подписываем на клики
            if zone_rect and len(zone_rect) == 4:
                macro.zone_rect = zone_rect
                macro._connect_mouse_click(self)
                logger.info(f"[SKILL+ZONE] Макрос '{name}' создан с областью {zone_rect}, подписка={macro._mouse_click_connected}")
            else:
                logger.debug(f"[SKILL+ZONE] Макрос '{name}' создан без зоны (обычный скилл-макрос)")

            self._macros.append(macro)
            self.save_macros()
            self._update_macros_dicts()

            # Регистрируем горячую клавишу нового макроса
            if macro_hotkey:
                def make_callback(m):
                    def callback(e=None):
                        logger.debug(f"Горячая клавиша '{m.hotkey}' нажата, макрос '{m.name}'")

                        # БЫСТРАЯ ПРОВЕРКА блокировки каста (без lock)
                        if time.time() < self.dispatcher.cast_lock_until:
                            logger.debug(f"[CAST LOCK] Горячая клавиша '{m.hotkey}' ЗАБЛОКИРОВАНА: идёт каст")
                            return  # ← Блокируем запуск!

                        # Запуск через диспетчер. Приоритет 3 для боевых макросов
                        if not m.running:
                            if not self.dispatcher.request_macro(m, priority=3):
                                logger.debug(f"❌ '{m.name}': ЗАБЛОКИРОВАНО диспетчером")
                                return
                        # Игнорируем повторные нажатия пока макрос выполняется
                    return callback
                self.register_hotkey(macro_hotkey, make_callback(macro))
                logger.debug(f"Горячая клавиша '{macro_hotkey}' зарегистрирована для макроса '{name}'")

            self.notification.emit(f"Скилл-макрос '{name}' создан", "success")
        except Exception as e:
            logger.error(f"Ошибка создания скилл-макроса: {e}")
            self.notification.emit(f"Ошибка: {e}", "error")

    # Обновление скилл-макроса
    @Slot(str, str, str, str, list, str, float, float, float, float, list)
    def update_skill_macro(self, old_name, new_name, hotkey, skill_id, steps, skill_hotkey,
                           cooldown, skill_range, cast_time, castbar_swap_delay, zone_rect):
        try:
            # Получаем иконку скилла
            icon = ""
            if skill_id:
                skill = self.skill_db.get_skill(int(skill_id))
                if skill:
                    icon = skill.icon

            for i, macro in enumerate(self._macros):
                if macro.name == old_name and macro.type == "skill":
                    new_macro = macros.SkillMacro(
                        new_name, steps, self, hotkey if hotkey else "",
                        skill_id=int(skill_id) if skill_id else None,
                        cooldown=cooldown,
                        skill_range=skill_range,
                        cast_time=cast_time,
                        castbar_swap_delay=castbar_swap_delay
                    )
                    # Сохраняем иконку в атрибут макроса
                    new_macro.icon = icon

                    # ✅ Сохраняем zone_rect только если он передан
                    if zone_rect and len(zone_rect) == 4:
                        new_macro.zone_rect = zone_rect
                        logger.info(f"[SKILL+ZONE] Макрос '{new_name}' обновлён с НОВОЙ областью {zone_rect}")
                    else:
                        # ✅ Очищаем зону если не передана (переключили на обычный макрос)
                        new_macro.zone_rect = None
                        logger.info(f"[SKILL+ZONE] Макрос '{new_name}' обновлён БЕЗ области (обычный)")

                    # Подписываем на клики если есть зона
                    if hasattr(new_macro, 'zone_rect') and new_macro.zone_rect:
                        new_macro._connect_mouse_click(self)
                        logger.info(f"[SKILL+ZONE] Макрос '{new_name}' подписан на клики, зона={new_macro.zone_rect}")

                    self._macros[i] = new_macro
                    self.save_macros()
                    self._update_macros_dicts()
                    self.notification.emit(f"Скилл-макрос '{new_name}' обновлён", "success")
                    return
            self.notification.emit("Макрос не найден", "error")
        except Exception as e:
            logger.error(f"Ошибка обновления скилл-макроса: {e}")
            self.notification.emit(f"Ошибка: {e}", "error")

    # Создание бафф-макроса
    @Slot(str, str, str, list, float, int, list)
    def create_buff_macro_with_params(self, name, hotkey, buff_id, steps, duration, channeling_bonus, zone_rect):
        try:
            logger.debug(f"create_buff_macro_with_params: name={name}, buff_id={buff_id}")
            
            # Получаем иконку баффа
            icon = ""
            if buff_id:
                buff = self.skill_db.get_buff(int(buff_id))
                if buff:
                    icon = buff.icon
            
            macro = macros.BuffMacro(
                name, steps, self,
                buff_id=int(buff_id) if buff_id else None,
                duration=duration,
                channeling_bonus=channeling_bonus,
                hotkey=hotkey if hotkey else "",  # ✅ Пустая строка вместо None
                icon=icon if icon else "buff.png"
            )

            # Если зональный макрос - сохраняем зону но тип не меняем
            if zone_rect and len(zone_rect) == 4:
                macro.zone_rect = zone_rect
            
            # Пересчитываем задержки в шагах если включен режим автозадержек (пинг)
            if self._settings.get("use_ping_delays", False):
                ping_comp = self.get_ping_compensation() * 1000  # в мс
                for i, step in enumerate(macro.steps):
                    if step[0] == "key":
                        # Пересчитываем задержку шага
                        macro.steps[i] = [step[0], step[1], round(ping_comp)]
                logger.info(f"[BUFF] Задержки пересчитаны: ping_comp={ping_comp}мс")

            self._macros.append(macro)
            self.save_macros()
            self._update_macros_dicts()
            
            # ✅ Регистрируем горячую клавишу для нового макроса
            if macro.hotkey:
                self.register_all_hotkeys()
                logger.info(f"[BUFF] Горячая клавиша '{macro.hotkey}' зарегистрирована для бафф-макроса '{macro.name}'")
            
            self.notification.emit(f"Бафф-макрос '{name}' создан", "success")
        except Exception as e:
            logger.error(f"Ошибка создания бафф-макроса: {e}")
            self.notification.emit(f"Ошибка: {e}", "error")

    # Обновление бафф-макроса
    @Slot(str, str, str, str, list, float, int, list)
    def update_buff_macro(self, old_name, new_name, hotkey, buff_id, steps, duration, channeling_bonus, zone_rect):
        try:
            # Получаем иконку баффа
            icon = ""
            if buff_id:
                buff = self.skill_db.get_buff(int(buff_id))
                if buff:
                    icon = buff.icon

            for i, macro in enumerate(self._macros):
                if macro.name == old_name and macro.type == "buff":
                    new_macro = macros.BuffMacro(
                        new_name, steps, self,
                        buff_id=int(buff_id) if buff_id else None,
                        duration=duration,
                        channeling_bonus=channeling_bonus,
                        hotkey=hotkey if hotkey else "",
                        icon=icon if icon else "buff.png"
                    )
                    # ✅ Сохраняем zone_rect только если он передан
                    if zone_rect and len(zone_rect) == 4:
                        new_macro.zone_rect = zone_rect
                        logger.info(f"[BUFF+ZONE] Бафф '{new_name}' обновлён с НОВОЙ областью {zone_rect}")
                    else:
                        # ✅ Очищаем зону если не передана
                        new_macro.zone_rect = None
                        logger.info(f"[BUFF+ZONE] Бафф '{new_name}' обновлён БЕЗ области")

                    # Подписываем на клики если есть зона
                    if hasattr(new_macro, 'zone_rect') and new_macro.zone_rect:
                        new_macro._connect_mouse_click(self)
                        logger.info(f"[BUFF+ZONE] Бафф '{new_name}' подписан на клики, зона={new_macro.zone_rect}")
                    
                    # Пересчитываем задержки в шагах если включен режим автозадержек (пинг)
                    if self._settings.get("use_ping_delays", False):
                        ping_comp = self.get_ping_compensation() * 1000  # в мс
                        for i, step in enumerate(new_macro.steps):
                            if step[0] == "key":
                                new_macro.steps[i] = [step[0], step[1], round(ping_comp)]
                        logger.info(f"[BUFF] Задержки обновлены: ping_comp={ping_comp}мс")

                    self._macros[i] = new_macro
                    self.save_macros()
                    self._update_macros_dicts()
                    
                    # ✅ Перерегистрируем горячие клавиши (могла измениться)
                    self.register_all_hotkeys()
                    logger.info(f"[BUFF] Горячая клавиша '{new_macro.hotkey}' перерегистрирована для бафф-макроса '{new_macro.name}'")
                    
                    self.notification.emit(f"Бафф-макрос '{new_name}' обновлён", "success")
                    return
            self.notification.emit("Макрос не найден", "error")
        except Exception as e:
            logger.error(f"Ошибка обновления бафф-макроса: {e}")
            self.notification.emit(f"Ошибка: {e}", "error")

    # Выбор области
    @Slot()
    def selectAreaForMacro(self):
        """Выбор области для макроса (использует ZoneAreaSelector - работает всегда)"""
        if not self.engine:
            return
        qml_file = resource_path("qml/ZoneAreaSelector.qml")
        if not qml_file or not os.path.exists(qml_file):
            self.notification.emit("Файл ZoneAreaSelector.qml не найден", "error")
            return
        component = QQmlComponent(self.engine, QUrl.fromLocalFile(qml_file))
        if component.isReady():
            window = component.create()
            if window:
                window.zoneAreaSelected.connect(self.onZoneAreaSelected)
                window.cancelled.connect(lambda: self.notification.emit("Выбор области отменён", "info"))
                window.show()
                logger.info("ZoneAreaSelector window created and shown")
            else:
                self.notification.emit("Не удалось создать окно выбора области", "error")
        else:
            error_str = component.errorString()
            logger.error(f"ZoneAreaSelector load error: {error_str}")
            self.notification.emit("Ошибка загрузки ZoneAreaSelector.qml: " + error_str, "error")

    @Slot(int, int, int, int)
    def onZoneAreaSelected(self, x1, y1, x2, y2):
        """Обработка выбора зоны для макроса"""
        self.zoneAreaSelectedSignal.emit([x1, y1, x2, y2])  # Передаём как массив
        self.notification.emit(f"Зона выбрана: {x1},{y1},{x2},{y2}", "success")


def main():
    logger.info("=" * 60)
    logger.info("[*] snbld resvap (QML + PySide6)")
    logger.info(f"[*] sys.frozen: {getattr(sys, 'frozen', False)}")
    logger.info(f"[*] sys._MEIPASS: {getattr(sys, '_MEIPASS', 'NOT SET')}")
    logger.info(f"[*] sys.executable: {sys.executable}")
    logger.info(f"[*] cwd: {os.getcwd()}")
    logger.info("=" * 60)

    # Проверка прав администратора (только для собранной версии)
    # Проверяем флаг --admin-requested, чтобы избежать бесконечного цикла при повторном запуске
    is_frozen = getattr(sys, 'frozen', False)
    is_onefile = hasattr(sys, '_MEIPASS') or ('TEMP' in os.getcwd() and 'onefile' in sys.executable)
    is_packaged = is_frozen or is_onefile
    
    if is_packaged:
        from utils import is_admin, run_as_admin
        
        # Флаг что мы уже запросили перезапуск - не запрашиваем снова
        admin_requested = '--admin-requested' in sys.argv
        
        if not is_admin():
            if admin_requested:
                # Мы уже пытались перезапуститься с админ правами, но видимо пользователь отменил или что-то пошло не так
                logger.warning("[-] Перезапуск от имени администратора не удался (отменен или ошибка).")
                logger.warning("[i] Продолжение работы в обычном режиме (функции могут быть ограничены)")
            else:
                logger.info("🔄 Запуск с правами администратора...")
                
                # Запрашиваем повышение прав только ОДИН раз
                if run_as_admin():
                    # UAC показан, новый процесс с админскими правами будет запущен после подтверждения
                    # Завершаем текущий процесс - новый будет иметь админ права
                    logger.info("[+] Запрос админ прав отправлен, завершаем текущий процесс...")
                    sys.exit(0)
                else:
                    logger.warning("[-] Не удалось запросить права администратора.")
                    logger.warning("[i] Продолжение работы в обычном режиме (функции могут быть ограничены)")
    else:
        logger.info("[dev] Режим разработки - проверка админ прав пропущена")

    app = QApplication(sys.argv)

    # Скрываем консоль при запуске (но она существует — можно показать через toggle_console)
    if is_packaged:
        try:
            import ctypes
            import win32gui
            kernel32 = ctypes.WinDLL('kernel32')
            hwnd = kernel32.GetConsoleWindow()
            if hwnd:
                win32gui.ShowWindow(hwnd, 0)  # SW_HIDE
        except Exception:
            pass

    icon_path = resource_path("123.ico")
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))
        logger.info(f"[+] Иконка загружена: {icon_path}")

    font = QFont("Segoe UI", 10)
    app.setFont(font)

    ensure_all_resources()

    engine = QQmlApplicationEngine()

    backend = Backend()
    backend.load_settings()  # Загружаем настройки ДО регистрации в QML
    # Настройки кастбара уже загружены в load_settings()

    backend.init_subsystems()
    
    # НЕ загружаем макросы из macros.json - они будут загружены из профиля
    # Очищаем макросы перед загрузкой профиля
    backend._macros = []
    backend._update_macros_dicts()

    engine.rootContext().setContextProperty("backend", backend)
    
    # Регистрируем помощник ресурсов для QML
    resource_helper = QMLResourceHelper()
    engine.rootContext().setContextProperty("ResourceHelper", resource_helper)
    
    # Регистрируем поставщика подсказок
    tooltips_provider = get_tooltips_provider()
    engine.rootContext().setContextProperty("Tooltips", tooltips_provider)

    backend.engine = engine
    logger.debug("backend.engine set")

    qml_file = resource_path("qml/main.qml")
    if not os.path.exists(qml_file):
        qml_file = os.path.join(self.app_dir, "qml", "main.qml")
    engine.load(QUrl.fromLocalFile(qml_file))

    if not engine.rootObjects():
        logger.error("[MAIN] QML не загрузился! Очистка ресурсов...")
        backend.cleanup()
        sys.exit(-1)

    window = engine.rootObjects()[0]

    # Сохраняем ссылку на окно для tray_icon
    backend._main_window = window

    # Установка иконки - для приложения и для окна
    if os.path.exists(icon_path):
        app_icon = QIcon(icon_path)
        app.setWindowIcon(app_icon)
        window.setIcon(app_icon)
        
        # Установка иконки на панели задач через WinAPI
        try:
            import win32gui
            import win32con
            
            hwnd = int(window.winId())
            # Получаем handle иконки через pixmap
            pixmap = app_icon.pixmap(256, 256)
            if pixmap:
                # Используем QPixmap для получения HICON
                from PySide6.QtGui import QGuiApplication
                screen = QGuiApplication.primaryScreen()
                if screen:
                    hIcon = pixmap.toImage()
                    # Простой способ - через QWindow
                    window.setIcon(app_icon)
        except Exception as e:
            logger.warning(f"[-] Не удалось установить иконку на панель задач: {e}")
        
        logger.info(f"[+] Иконка установлена: {icon_path}")
    else:
        logger.warning(f"[-] Иконка не найдена: {icon_path}")

    # Инициализация TrayIconManager для сворачивания в трей
    try:
        from utils.tray_icon import TrayIconManager
        backend._tray_enabled = True
        backend._tray_icon_manager = TrayIconManager(backend, app)
        backend._tray_icon_manager.init_tray()
        logger.info("[TRAY] TrayIconManager инициализирован")
    except Exception as e:
        logger.warning(f"[TRAY] TrayIconManager недоступен: {e}")
        backend._tray_enabled = False
        backend._tray_icon_manager = None

    # Закруглённые углы окна через DWM API (Windows 11+)
    import ctypes
    try:
        dwmapi = ctypes.WinDLL("dwmapi.dll")
        DwmSetWindowAttribute = dwmapi.DwmSetWindowAttribute
        DwmSetWindowAttribute.restype = ctypes.HRESULT
        DwmSetWindowAttribute.argtypes = [
            ctypes.c_void_p, ctypes.c_uint32,
            ctypes.POINTER(ctypes.c_int), ctypes.c_uint32
        ]
        DWMWA_WINDOW_CORNER_PREFERENCE = 33
        DWMWCP_ROUND = 2

        def apply_rounded_corners():
            try:
                hwnd = ctypes.c_void_p(int(window.winId()))
                corner_pref = ctypes.c_int(DWMWCP_ROUND)
                result = DwmSetWindowAttribute(
                    hwnd, DWMWA_WINDOW_CORNER_PREFERENCE,
                    ctypes.byref(corner_pref), ctypes.sizeof(corner_pref)
                )
                if result == 0:
                    logger.info("[DWM] Закруглённые углы применены")
                else:
                    logger.debug(f"[DWM] Результат: 0x{result:08X}")
            except Exception as e:
                logger.debug(f"[DWM] Не удалось: {e}")

        # Пробуем несколько раз с задержкой
        from PySide6.QtCore import QTimer
        QTimer.singleShot(500, apply_rounded_corners)
        QTimer.singleShot(2000, apply_rounded_corners)
        window.visibleChanged.connect(apply_rounded_corners)
    except Exception as e:
        logger.debug(f"[DWM] API недоступен: {e}")

    backend.minimizeRequested.connect(window.showMinimized)
    backend.closeRequested.connect(window.close)

    # Устанавливаем eventFilter для перехвата закрытия окна
    class CleanupEventFilter(QObject):
        def __init__(self, backend_instance):
            super().__init__()
            self.backend = backend_instance
            self._done = False
        def eventFilter(self, obj, event):
            from PySide6.QtCore import QEvent
            if not self._done and event.type() == QEvent.Close:
                self._done = True
                logger.info("[EVENTFILTER] Перехват Close — остановка потоков...")
                self.backend.cleanup()
            return super().eventFilter(obj, event)

    cleanup_filter = CleanupEventFilter(backend)
    window.installEventFilter(cleanup_filter)
    backend._cleanup_filter = cleanup_filter

    # АЛЬТЕРНАТИВА: также подключаем aboutToQuit как fallback
    app.aboutToQuit.connect(backend.cleanup)

    # Фиксируем ссылку на окно чтобы GC не удалил раньше времени
    backend._main_window = window

    # Загружаем последний активный профиль ПОСЛЕ инициализации QML
    last_profile = backend._settings.get("last_active_profile", "")
    if last_profile:
        profile_path = os.path.join(backend.profiles_dir, f"{last_profile}.json")
        if os.path.exists(profile_path):
            logger.info(f"[PROFILE] Загрузка последнего профиля: {last_profile}")
            backend.load_profile(last_profile)
        else:
            logger.warning(f"[PROFILE] Последний профиль '{last_profile}' не найден")

    app.aboutToQuit.connect(backend.cleanup)

    sys.exit(app.exec())


if __name__ == "__main__":
    main()