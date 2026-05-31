import sys
import ctypes

# Немедленное скрытие консоли (до main()) — только для собранного .exe
is_packaged = getattr(sys, 'frozen', False) or hasattr(sys, 'compiled') or hasattr(sys, '_MEIPASS')
if is_packaged:
    try:
        ctypes.windll.kernel32.FreeConsole()
    except Exception:
        pass

import builtins
_original_print = builtins.print
def _safe_print(*args, **kwargs):
    try:
        _original_print(*args, **kwargs)
    except (OSError, ValueError):
        try:
            kwargs.pop('file', None)
            _original_print(*args, file=sys.stderr, **kwargs)
        except (OSError, ValueError):
            pass
builtins.print = _safe_print

try:
    ctypes.windll.user32.SetProcessDpiAwarenessContext(-4)
except:
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
    except:
        try:
            ctypes.windll.user32.SetProcessDPIAware()
        except:
            pass

import os
import re
import atexit
import threading
from backend.win32_api import CreateMutex, ReleaseMutex, GetLastError, MessageBox, ERROR_ALREADY_EXISTS
import traceback
from datetime import datetime

_CHANGE_WINDOW_MESSAGE_FILTER_EX = 0x00FF
_MSG_FILTER_ALLOW = 1

class _CHANGEFILTERSTRUCT(ctypes.Structure):
    _fields_ = [("cbSize", ctypes.wintypes.DWORD), ("ExtStatus", ctypes.wintypes.DWORD)]

_ALLOWED_MESSAGES = [
    0x00FF, 0x0100, 0x0101, 0x0104, 0x0105,
    0x0201, 0x0202, 0x0204, 0x0205, 0x020A,
]

def _allow_uipi_messages():
    """Снимает UIPI-блокировку с сообщений ввода для текущего процесса.
    Использует ChangeWindowMessageFilterEx (Windows 8+) с fallback на ChangeWindowMessageFilter."""
    try:
        user32 = ctypes.windll.user32
        user32.ChangeWindowMessageFilterEx.restype = ctypes.wintypes.BOOL
        user32.ChangeWindowMessageFilterEx.argtypes = [
            ctypes.c_void_p, ctypes.wintypes.UINT, ctypes.wintypes.DWORD,
            ctypes.POINTER(_CHANGEFILTERSTRUCT),
        ]
        cf_struct = _CHANGEFILTERSTRUCT()
        cf_struct.cbSize = ctypes.sizeof(_CHANGEFILTERSTRUCT)
        # NULL hwnd = модификация для всего процесса (мгновенно)
        for msg in _ALLOWED_MESSAGES:
            user32.ChangeWindowMessageFilterEx(None, msg, _MSG_FILTER_ALLOW, ctypes.byref(cf_struct))
    except Exception:
        try:
            for msg in _ALLOWED_MESSAGES:
                ctypes.windll.user32.ChangeWindowMessageFilter(msg, 1)
        except Exception:
            pass

_allow_uipi_messages()

def _get_app_dir():
    if hasattr(sys, '_MEIPASS'):
        if hasattr(sys, 'argv') and sys.argv and sys.argv[0]:
            return os.path.dirname(os.path.abspath(sys.argv[0]))
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    if hasattr(sys, 'argv') and sys.argv and sys.argv[0].endswith('.exe'):
        return os.path.dirname(os.path.abspath(sys.argv[0]))
    if 'TEMP' in os.getcwd() or 'TMP' in os.getcwd():
        if hasattr(sys, 'argv') and sys.argv and sys.argv[0]:
            return os.path.dirname(os.path.abspath(sys.argv[0]))
    return os.path.dirname(os.path.abspath(__file__))

app_path = _get_app_dir()
has_non_ascii = any(ord(c) > 127 for c in app_path)
if has_non_ascii:
    print(f"WARNING: Path contains non-ASCII characters: {app_path}")
    print("The program will attempt to work, but some features may be limited.")

mutex = CreateMutex("snbld_pyside_single_instance_mutex")
if GetLastError() == ERROR_ALREADY_EXISTS:
    MessageBox(0, "Программа уже запущена.\nПроверьте трей системного трея.", "SNBLD", 0x40 | 0x1000)
    sys.exit(1)

def _release_mutex():
    try:
        ReleaseMutex(mutex)
    except:
        pass

atexit.register(_release_mutex)

def _global_exception_handler(exc_type, exc_value, exc_traceback):
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    crash_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    crash_file = os.path.join(_get_app_dir(), f"crash_{crash_time}.log")
    try:
        from backend.logger_manager import LoggerManager
        logger_errors = LoggerManager.get_logger('errors')
        logger_errors.critical(
            "КРИТИЧЕСКАЯ ОШИБКА",
            exc_info=(exc_type, exc_value, exc_traceback)
        )
    except Exception:
        pass
    try:
        with open(crash_file, 'w', encoding='utf-8') as f:
            f.write("=== SNBLD CRASH REPORT ===\n")
            f.write(f"Time: {crash_time}\n")
            version_path = os.path.join(_get_app_dir(), 'version.json')
            version_text = 'unknown'
            try:
                with open(version_path, 'r', encoding='utf-8') as vf:
                    version_text = vf.read()
            except Exception:
                pass
            f.write(f"Version: {version_text}\n")
            f.write("\n=== TRACEBACK ===\n")
            traceback.print_exception(exc_type, exc_value, exc_traceback, file=f)
        # Ротация: оставляем не более 10 crash-логов
        crash_dir = _get_app_dir()
        crash_logs = sorted(
            [f for f in os.listdir(crash_dir) if f.startswith('crash_') and f.endswith('.log')],
            key=lambda f: os.path.getmtime(os.path.join(crash_dir, f))
        )
        while len(crash_logs) > 10:
            oldest = crash_logs.pop(0)
            try:
                os.remove(os.path.join(crash_dir, oldest))
            except Exception:
                pass
    except Exception:
        pass
    error_msg = f"\u041f\u0440\u043e\u0438\u0437\u043e\u0448\u043b\u0430 \u043a\u0440\u0438\u0442\u0438\u0447\u0435\u0441\u043a\u0430\u044f \u043e\u0448\u0438\u0431\u043a\u0430.\n\u041a\u0440\u0430\u0448\u043b\u043e\u0433 \u0441\u043e\u0445\u0440\u0430\u043d\u0451\u043d:\n{crash_file}\n\n\u041e\u0448\u0438\u0431\u043a\u0430: {exc_value}"
    try:
        MessageBox(0, error_msg, "SNBLD - Критическая ошибка", 0x10 | 0x1000)
    except Exception:
        pass
    try:
        import low_level_hook
        low_level_hook.unhook_all()
    except Exception:
        pass
    sys.exit(1)

sys.excepthook = _global_exception_handler

def _thread_exception_handler(args):
    crash_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    crash_file = os.path.join(_get_app_dir(), f"crash_{crash_time}.log")
    try:
        from backend.logger_manager import LoggerManager
        logger_errors = LoggerManager.get_logger('errors')
        logger_errors.critical(
            "КРИТИЧЕСКАЯ ОШИБКА В ПОТОКЕ",
            exc_info=(args.exc_type, args.exc_value, args.exc_traceback)
        )
    except Exception:
        pass
    try:
        with open(crash_file, 'w', encoding='utf-8') as f:
            f.write("=== SNBLD CRASH REPORT (thread) ===\n")
            f.write(f"Time: {crash_time}\n")
            f.write(f"Thread: {args.thread}\n")
            f.write("\n=== TRACEBACK ===\n")
            traceback.print_exception(args.exc_type, args.exc_value, args.exc_traceback, file=f)
    except Exception:
        pass

threading.excepthook = _thread_exception_handler

def _cleanup_on_exit():
    try:
        import low_level_hook
        low_level_hook.unhook_all()
        print("[CLEANUP] \u0425\u0443\u043a\u0438 \u043a\u043b\u0430\u0432\u0438\u0430\u0442\u0443\u0440\u044b/\u043c\u044b\u0448\u0438 \u043e\u0442\u043a\u043b\u044e\u0447\u0435\u043d\u044b")
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
    logger.info("[CLEANUP] \u0420\u0435\u0441\u0443\u0440\u0441\u044b \u043e\u0447\u0438\u0449\u0435\u043d\u044b, \u043f\u0440\u043e\u0433\u0440\u0430\u043c\u043c\u0430 \u0437\u0430\u0432\u0435\u0440\u0448\u0435\u043d\u0430")

atexit.register(_cleanup_on_exit)

def cleanup_old_logs():
    import glob
    from utils.file_utils import get_install_dir
    logs_dir = os.path.join(str(get_install_dir()), 'logs')
    os.makedirs(logs_dir, exist_ok=True)
    if os.path.exists(logs_dir):
        try:
            for log_file in glob.glob(os.path.join(logs_dir, '*.log')):
                try:
                    with open(log_file, 'w', encoding='utf-8') as f:
                        f.write('')
                except Exception:
                    pass
            for old_log in glob.glob(os.path.join(logs_dir, '*.log.*')):
                try:
                    os.remove(old_log)
                except Exception:
                    pass
            print("[LOGS] Old logs cleaned (content cleared, files preserved)")
        except Exception as e:
            print(f"[LOGS] Clean error: {e}")

cleanup_old_logs()

os.environ['QT_LOGGING_RULES'] = '*.debug=false;qt.qpa.*=false;shiboken=false;PySide6=false'
os.environ['QT_DEBUG_PLUGINS'] = '0'
os.environ['QML_DEBUG_DISABLED'] = '1'

from typing import Dict
import json
import time
import webbrowser
import threading

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
from constants import ALLOWED_SETTINGS, OCR_TARGET_INTERVAL
import auth
import macros
from macros import (
    Macro, SimpleMacro, ZoneMacro, SkillMacro, BuffMacro,
)
import skill_database
import tesseract_reader
import threads
from utils import resource_path, ensure_all_resources
from utils_qml import QMLResourceHelper
from tooltips_qml import get_tooltips_provider
from backend.logger_manager import LoggerManager, get_logger, log_error

logger = get_logger('debug')
logger_errors = get_logger('errors')
logger.info("=== \u0417\u0430\u043f\u0443\u0441\u043a \u043f\u0440\u0438\u043b\u043e\u0436\u0435\u043d\u0438\u044f snbld resvap QML ===")
logger_errors.info("=== \u0417\u0430\u043f\u0443\u0441\u043a \u043f\u0440\u0438\u043b\u043e\u0436\u0435\u043d\u0438\u044f snbld resvap QML ===")

threading.Thread(target=tesseract_reader.ensure_tesseract, daemon=True).start()
logger.info("Tesseract OCR \u0438\u043d\u0438\u0446\u0438\u0430\u043b\u0438\u0437\u0438\u0440\u043e\u0432\u0430\u043d \u0432 \u0444\u043e\u043d\u0435")

from backend.qml_bridge import QMLBridgeMixin
from backend.auth_mixin import AuthMixin
from backend.macro_mixin import MacroMixin
from backend.ocr_mixin import OCRMixin
from backend.castbar_mixin import CastbarMixin
from backend.window_mixin import WindowMixin
from backend.settings_mixin import SettingsMixin


class Backend(QObject, QMLBridgeMixin, AuthMixin, MacroMixin, OCRMixin, CastbarMixin, WindowMixin, SettingsMixin):
    macrosChanged = Signal()
    settingsChanged = Signal()
    subscriptionChanged = Signal()
    pingUpdated = Signal(int)
    distanceUpdated = Signal(str, float, list)
    profileChanged = Signal()
    profilesChanged = Signal()
    notification = Signal(str, str)
    pageChangeRequested = Signal(str)
    globalStoppedChanged = Signal()
    activeBuffsUpdated = Signal()

    minimizeRequested = Signal()
    closeRequested = Signal()
    activationStatusChanged = Signal()
    logSendStatusChanged = Signal()
    createHeartbeatTimerRequested = Signal()
    updateAvailable = Signal(dict)
    updateDownloadProgress = Signal(int, int)
    updateDownloadComplete = Signal(str, str)
    areaSelectedSignal = Signal(int, int, int, int)
    zoneAreaSelectedSignal = Signal(list)
    ocrAreaSelected = Signal(str, str)
    ocrTestResult = Signal(str, dict)
    areaSelected = Signal(int, int, int, int)
    ocrCalibrationCompleted = Signal()
    ocrCalibrationDialogRequested = Signal()
    ocrAreaSelectorRequested = Signal(str)
    startAllPressed = Signal()
    stopAllPressed = Signal()
    macroStatusChanged = Signal()
    castbarColorCaptured = Signal(str, str)
    buffCalibrationDialogRequested = Signal()
    buffCalibrationCompleted = Signal(str)
    windowsListUpdated = Signal(list)
    openWindowSelector = Signal()
    targetWindowChanged = Signal()
    windowLockedChanged = Signal()
    fastOCROverlayRequested = Signal()

    @Slot()
    def requestFastOCROverlay(self):
        self.fastOCROverlayRequested.emit()

    @Property(list, notify=macrosChanged)
    def macros(self):
        result = list(self._macros_dicts)
        logger.debug(f"[MACROS_PROP] getter called, dicts count={len(result)}, _macros count={len(getattr(self, '_macros', []))}")
        if result:
            logger.debug(f"[MACROS_PROP] first item: {result[0].get('name')}")
        return result

    @Property(bool, notify=globalStoppedChanged)
    def global_stopped(self):
        return self._global_stopped

    @global_stopped.setter
    def global_stopped(self, value):
        if self._global_stopped != value:
            self._global_stopped = value
            self.globalStoppedChanged.emit()

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
            self.settingsChanged.emit()

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
            self.settingsChanged.emit()

    @Property(dict, notify=settingsChanged)
    def settings(self):
        return dict(self._settings)

    @Property(dict, notify=subscriptionChanged)
    def subscription_info(self):
        if not self._subscription_info:
            return {}
        info = dict(self._subscription_info)
        if info.get('valid') and 'expires_at' in info and info['expires_at']:
            try:
                from datetime import datetime
                expires = datetime.fromisoformat(info['expires_at'].replace('Z', '+00:00'))
                now = datetime.now(expires.tzinfo)
                delta = expires - now
                if delta.total_seconds() <= 0:
                    info['expires_pretty'] = "\u0418\u0441\u0442\u0451\u043a"
                else:
                    days = delta.days
                    hours = delta.seconds // 3600
                    minutes = (delta.seconds % 3600) // 60
                    if days > 0:
                        info['expires_pretty'] = f"\u041e\u0441\u0442\u0430\u043b\u043e\u0441\u044c: {days} \u0434\u043d. {hours} \u0447."
                    elif hours > 0:
                        info['expires_pretty'] = f"\u041e\u0441\u0442\u0430\u043b\u043e\u0441\u044c: {hours} \u0447. {minutes} \u043c\u0438\u043d."
                    else:
                        info['expires_pretty'] = f"\u041e\u0441\u0442\u0430\u043b\u043e\u0441\u044c: {minutes} \u043c\u0438\u043d."
            except:
                info['expires_pretty'] = info['expires_at']
        return info

    @Property(bool, notify=activationStatusChanged)
    def isActivated(self):
        return self._is_activated

    @Property(str, notify=activationStatusChanged)
    def activationStatus(self):
        return getattr(self, '_activation_status', '')

    @Property(bool, notify=logSendStatusChanged)
    def isSendingLogs(self):
        return getattr(self, '_is_sending_logs', False)

    @Property(str, notify=profileChanged)
    def current_profile(self):
        return self._current_profile or "\u043d\u0435 \u0432\u044b\u0431\u0440\u0430\u043d"

    @Property(list, notify=profilesChanged)
    def profiles_list(self):
        return self.get_profile_list()

    @Property(dict, notify=macrosChanged)
    def macro_for_edit(self):
        result = getattr(self, '_macro_for_edit', None)
        return result if result is not None else {}

    @Property(int, notify=pingUpdated)
    def ping(self):
        return self._ping

    @property
    def fast_distance(self):
        if hasattr(self, 'fast_distance_reader') and self.fast_distance_reader:
            d = self.fast_distance_reader.distance
            return d if d is not None else 0.0
        return 0.0

    @property
    def fast_raw_distance(self):
        if hasattr(self, 'fast_distance_reader') and self.fast_distance_reader:
            d = self.fast_distance_reader.raw_distance
            return d if d is not None else 0.0
        return 0.0

    @Slot(result=str)
    def getFastOCRDict(self):
        import json, base64, io
        import cv2
        from PIL import Image as PILImage
        result = {
            "distance": 0.0,
            "raw_text": "",
            "image": "",
            "history": []
        }
        if hasattr(self, 'fast_distance_reader') and self.fast_distance_reader:
            reader = self.fast_distance_reader
            d = reader.distance
            result["distance"] = round(d, 1) if d is not None else 0.0
            result["raw_text"] = reader.get_last_raw_text() or ""
            result["history"] = [round(h, 1) for h in reader.get_history()]
            img = reader.get_last_image()
            if img is not None:
                if len(img.shape) == 2:
                    preview = cv2.cvtColor(img, cv2.COLOR_GRAY2RGB)
                else:
                    preview = img
                pil = PILImage.fromarray(preview)
                buf = io.BytesIO()
                pil.save(buf, format="PNG")
                result["image"] = base64.b64encode(buf.getvalue()).decode()
        return json.dumps(result)

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
        url = getattr(self, '_background_video_url', '')
        import logging
        logging.getLogger('debug').info(f"[VIDEO] backgroundVideoUrl Property \u0432\u044b\u0437\u0432\u0430\u043d: '{url}'")
        return url if url else ''

    def _get_background_video_url(self) -> str:
        import logging
        import sys
        _vlogger = logging.getLogger('debug')
        _vlogger.info(f"[VIDEO DEBUG] sys.frozen={getattr(sys, 'frozen', False)}")
        _vlogger.info(f"[VIDEO DEBUG] sys.argv[0]={sys.argv[0]}")
        _vlogger.info(f"[VIDEO DEBUG] hasattr _MEIPASS={hasattr(sys, '_MEIPASS')}")
        _vlogger.info(f"[VIDEO DEBUG] hasattr compiled={hasattr(sys, 'compiled')}")
        video_names = ["12.mp4", "12.webm"]
        from utils import resource_path, resource_path_debug
        for name in video_names:
            path = resource_path(name)
            exists = os.path.exists(path)
            _vlogger.info(f"[VIDEO] resource_path({name}) = {path}, exists={exists}")
            if not exists:
                path_debug = resource_path_debug(name)
                _vlogger.info(f"[VIDEO] resource_path_debug({name}) = {path_debug}")
                if os.path.exists(path_debug):
                    path = path_debug
                    exists = True
            if exists:
                path_fixed = path.replace('\\', '/')
                url = f"file:///{path_fixed}"
                _vlogger.info(f"[VIDEO]  \u0412\u0438\u0434\u0435\u043e \u043d\u0430\u0439\u0434\u0435\u043d\u043e: {url}")
                return url
        _vlogger.warning(f"[VIDEO]  \u0412\u0438\u0434\u0435\u043e \u043d\u0435 \u043d\u0430\u0439\u0434\u0435\u043d\u043e")
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
        self._global_stopped = True
        self._window_locked = False
        self._target_window_title = ""
        self.window_x = 0
        self.window_y = 0
        self.app_dir = _get_app_dir()
        from utils.file_utils import get_data_dir, get_install_dir
        self.runtime_dir = str(get_data_dir())
        self.data_dir = str(get_install_dir())
        self.profiles_dir = os.path.join(self.data_dir, "profiles")
        os.makedirs(self.profiles_dir, exist_ok=True)
        logger.debug(f"[INIT] app_dir={self.app_dir}, data_dir={self.data_dir}, profiles={self.profiles_dir}")
        self.skill_db = None
        self.target_reader = None
        self.ping_monitor = None
        self.movement_monitor = None
        self.mouse_click_monitor = None
        self.buff_check_thread = None
        self.active_buffs = {}
        self.buff_lock = threading.Lock()
        self._settings_lock = threading.Lock()
        self._hotkey_registered = set()
        self.engine = None
        self._background_video_url = self._get_background_video_url()
        self._last_ocr_numbers = []
        self.active_macros: Dict[str, 'Macro'] = {}
        self.target_reader = None
        self._ocr_running = False
        self._ocr_enabled = False
        from backend.macros_dispatcher import MacroDispatcher
        self.dispatcher = MacroDispatcher(self)
        self.castbar_enabled = False
        self.castbar_point = ""
        self.castbar_color = [94, 123, 104]
        self.castbar_threshold = 70
        self._activation_key = None
        self._is_activated = False
        self._heartbeat_manager = None
        self._secrets = {}
        self._auth_deferred = False
        self._activation_status = "checking"
        self._is_sending_logs = False
        self.createHeartbeatTimerRequested.connect(self._createHeartbeatTimer)
        self.updateDownloadComplete.connect(self.install_update)

    def copyToClipboard(self, text):
        from PySide6.QtGui import QGuiApplication
        QGuiApplication.clipboard().setText(text)

    @Slot(str, str)
    def set_setting(self, key, value):
        if key not in ALLOWED_SETTINGS:
            logger.warning(f"\u041f\u043e\u043f\u044b\u0442\u043a\u0430 \u0443\u0441\u0442\u0430\u043d\u043e\u0432\u0438\u0442\u044c \u043d\u0435\u0434\u043e\u043f\u0443\u0441\u0442\u0438\u043c\u044b\u0439 \u043a\u043b\u044e\u0447: {key}")
            self.notification.emit(f" \u041d\u0435\u0434\u043e\u043f\u0443\u0441\u0442\u0438\u043c\u0430\u044f \u043d\u0430\u0441\u0442\u0440\u043e\u0439\u043a\u0430: {key}", "error")
            return
        expected_type, min_val, max_val = ALLOWED_SETTINGS[key]
        try:
            if expected_type == int:
                value = int(float(value))
            elif expected_type == float:
                value = float(value)
            elif expected_type == bool:
                value = str(value).lower() in ("true", "1", "yes")
            elif expected_type == list:
                if isinstance(value, str):
                    value = [int(x.strip()) for x in value.split(',')]
            elif expected_type == (str, list):
                if isinstance(value, str) and ',' in value:
                    value = [int(x.strip()) for x in value.split(',')]
        except (ValueError, TypeError) as e:
            logger.error(f"\u041d\u0435\u0432\u0435\u0440\u043d\u044b\u0439 \u0442\u0438\u043f \u0434\u043b\u044f {key}: {value} ({e})")
            self.notification.emit(f" \u041d\u0435\u0432\u0435\u0440\u043d\u044b\u0439 \u0444\u043e\u0440\u043c\u0430\u0442: {value}", "warning")
            return
        if min_val is not None and max_val is not None:
            if value < min_val or value > max_val:
                logger.error(f"\u0417\u043d\u0430\u0447\u0435\u043d\u0438\u0435 {key} \u0432\u043d\u0435 \u0434\u0438\u0430\u043f\u0430\u0437\u043e\u043d\u0430: {value} (\u0434\u043e\u043f\u0443\u0441\u0442\u0438\u043c\u043e: {min_val}-{max_val})")
                self.notification.emit(f" \u0412\u043d\u0435 \u0434\u0438\u0430\u043f\u0430\u0437\u043e\u043d\u0430: {min_val}-{max_val}", "warning")
                value = max(min_val, min(max_val, value))
        if key == "ocr_scale" and value < 5:
            logger.warning(f"ocr_scale={value} \u043c\u043e\u0436\u0435\u0442 \u0443\u0445\u0443\u0434\u0448\u0438\u0442\u044c \u0440\u0430\u0441\u043f\u043e\u0437\u043d\u0430\u0432\u0430\u043d\u0438\u0435")
            self.notification.emit(" OCR scale < 5 \u0443\u0445\u0443\u0434\u0448\u0430\u0435\u0442 \u0440\u0430\u0441\u043f\u043e\u0437\u043d\u0430\u0432\u0430\u043d\u0438\u0435", "warning")
        if key == "castbar_threshold" and value < 50:
            logger.warning(f"castbar_threshold={value} может вызвать ложные срабатывания")
            self.notification.emit("Внимание: Порог < 50 может вызвать ложные срабатывания", "warning")
        old_value = self._settings.get(key)
        self._settings[key] = value
        logger.info(f"Настройка {key} изменена: {old_value} → {value}")
        if key == "castbar_color":
            if isinstance(value, str):
                value = [int(x.strip()) for x in value.split(',')]
            self.castbar_color = value
            self._settings[key] = self.castbar_color
            self.settingsChanged.emit()
            self.apply_settings_to_macros(key, self.castbar_color)
        elif key == "castbar_threshold":
            try:
                self.castbar_threshold = int(value)
            except Exception:
                self.castbar_threshold = 70
            self._settings[key] = self.castbar_threshold
            self.apply_settings_to_macros(key, self.castbar_threshold)
        elif key in ("movement_delay_enabled", "check_distance", "ocr_use_morph", "ping_auto", "use_fixed_delays", "use_ping_delays", "use_castbar_detection", "castbar_enabled", "window_locked"):
            if isinstance(value, str):
                value = value.lower() in ("true", "1", "yes")
            self._settings[key] = value
            if key == "ping_auto":
                if value:
                    interval = self._settings.get("ping_check_interval", 5)
                    self._stop_ping_monitor()
                    if not self.ping_monitor or not self.ping_monitor.isRunning():
                        self.ping_monitor = threads.PingMonitor(self._settings["process_name"], interval)
                        self.ping_monitor.ping_updated.connect(self.on_ping_updated)
                        self.ping_monitor.start()
                        logger.info(f"[PING] PingMonitor вклюен")
                else:
                    self._stop_ping_monitor()
                    logger.info("[PING] PingMonitor выключен")
            self.apply_settings_to_macros(key, value)
        else:
            self.apply_settings_to_macros(key, value)
        self.settingsChanged.emit()

    def _validate_macros_json(self, data):
        if not isinstance(data, dict):
            raise ValueError("macros.json \u0434\u043e\u043b\u0436\u0435\u043d \u0431\u044b\u0442\u044c \u043e\u0431\u044a\u0435\u043a\u0442\u043e\u043c (dict)")
        if "macros" not in data:
            raise ValueError("macros.json \u0434\u043e\u043b\u0436\u0435\u043d \u0441\u043e\u0434\u0435\u0440\u0436\u0430\u0442\u044c \u043a\u043b\u044e\u0447 'macros'")
        if not isinstance(data["macros"], list):
            raise ValueError("'macros' \u0434\u043e\u043b\u0436\u0435\u043d \u0431\u044b\u0442\u044c \u0441\u043f\u0438\u0441\u043a\u043e\u043c")
        logger.debug("[VALIDATION] \u0421\u0442\u0440\u0443\u043a\u0442\u0443\u0440\u0430 macros.json \u0432\u0430\u043b\u0438\u0434\u043d\u0430")

    def _validate_macro_dict(self, m_dict):
        required_fields = ["type", "name", "steps"]
        for field in required_fields:
            if field not in m_dict:
                raise ValueError(f"\u041c\u0430\u043a\u0440\u043e\u0441 '{m_dict.get('name', 'unknown')}' \u043d\u0435 \u0441\u043e\u0434\u0435\u0440\u0436\u0438\u0442 \u043e\u0431\u044f\u0437\u0430\u0442\u0435\u043b\u044c\u043d\u043e\u0433\u043e \u043f\u043e\u043b\u044f '{field}'")
        if not isinstance(m_dict["steps"], list):
            raise ValueError(f"\u041c\u0430\u043a\u0440\u043e\u0441 '{m_dict['name']}': 'steps' \u0434\u043e\u043b\u0436\u0435\u043d \u0431\u044b\u0442\u044c \u0441\u043f\u0438\u0441\u043a\u043e\u043c")
        if m_dict["type"] == "zone":
            if "zone_rect" not in m_dict:
                raise ValueError(f"\u0417\u043e\u043d\u0430\u043b\u044c\u043d\u044b\u0439 \u043c\u0430\u043a\u0440\u043e\u0441 '{m_dict['name']}' \u043d\u0435 \u0441\u043e\u0434\u0435\u0440\u0436\u0438\u0442 'zone_rect'")
            zone_rect = m_dict["zone_rect"]
            if not isinstance(zone_rect, list) or len(zone_rect) != 4:
                raise ValueError(f"\u041c\u0430\u043a\u0440\u043e\u0441 '{m_dict['name']}': 'zone_rect' \u0434\u043e\u043b\u0436\u0435\u043d \u0431\u044b\u0442\u044c \u0441\u043f\u0438\u0441\u043a\u043e\u043c \u0438\u0437 4 \u0447\u0438\u0441\u0435\u043b")
            if not all(isinstance(x, (int, float)) for x in zone_rect):
                raise ValueError(f"\u041c\u0430\u043a\u0440\u043e\u0441 '{m_dict['name']}': 'zone_rect' \u0434\u043e\u043b\u0436\u0435\u043d \u0441\u043e\u0434\u0435\u0440\u0436\u0430\u0442\u044c \u0442\u043e\u043b\u044c\u043a\u043e \u0447\u0438\u0441\u043b\u0430")
        logger.debug(f"[VALIDATION] \u041c\u0430\u043a\u0440\u043e\u0441 '{m_dict['name']}' \u0432\u0430\u043b\u0438\u0434\u0435\u043d")

    def load_macros(self):
        macro_file = os.path.join(self.app_dir, constants.MACROS_JSON_FILE)
        if not os.path.exists(macro_file):
            self._macros = []
            self._update_macros_dicts()
            return
        try:
            with open(macro_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            self._validate_macros_json(data)
            self._window_locked = data.get("window_locked", False)
            self._target_window_title = data.get("target_window_title", "")
            self.window_locked = self._window_locked
            self.target_window_title = self._target_window_title
            self.macrosChanged.emit()
            self._macros = []
            for m_dict in data.get("macros", []):
                self._validate_macro_dict(m_dict)
                macro = self._create_macro_from_dict(m_dict)
                if macro is None:
                    continue
                if macro.type == "zone":
                    macro._connect_mouse_click(self)
                    macro.start()
                    logger.info(f"[ZONE] \u041c\u0430\u043a\u0440\u043e\u0441 '{macro.name}' \u0437\u0430\u043f\u0443\u0449\u0435\u043d \u0430\u0432\u0442\u043e\u043c\u0430\u0442\u0438\u0447\u0435\u0441\u043a\u0438")
                self._macros.append(macro)
            self._update_macros_dicts()
            logger.info(f"\u0417\u0430\u0433\u0440\u0443\u0436\u0435\u043d\u043e {len(self._macros)} \u043c\u0430\u043a\u0440\u043e\u0441\u043e\u0432")
        except Exception as e:
            logger.error(f"\u041e\u0448\u0438\u0431\u043a\u0430 \u0437\u0430\u0433\u0440\u0443\u0437\u043a\u0438 \u043c\u0430\u043a\u0440\u043e\u0441\u043e\u0432: {e}")
            self._macros = []
            self._update_macros_dicts()

    def save_macros(self):
        logger.debug(f"[MACROS] save_macros \u0432\u044b\u0437\u0432\u0430\u043d | _current_profile={self._current_profile} | \u043c\u0430\u043a\u0440\u043e\u0441\u043e\u0432={len(self._macros)}")
        if self._current_profile:
            logger.info(f"[MACROS] \u0421\u043e\u0445\u0440\u0430\u043d\u0435\u043d\u0438\u0435 \u0432 \u043f\u0440\u043e\u0444\u0438\u043b\u044c: {self._current_profile}")
            self.save_profile(self._current_profile)
            logger.debug(f"[PROFILE] \u041c\u0430\u043a\u0440\u043e\u0441\u044b \u0430\u0432\u0442\u043e\u0441\u043e\u0445\u0440\u0430\u043d\u0435\u043d\u044b \u0432 \u043f\u0440\u043e\u0444\u0438\u043b\u044c: {self._current_profile}")
        self._save_macros_to_file()
        logger.debug("[MACROS] \u041c\u0430\u043a\u0440\u043e\u0441\u044b \u0441\u043e\u0445\u0440\u0430\u043d\u0435\u043d\u044b \u0432 macros.json")

    def _save_macros_to_file(self):
        macro_file = os.path.join(self.app_dir, constants.MACROS_JSON_FILE)
        data = {
            "window_locked": self._window_locked,
            "target_window_title": self._target_window_title,
            "macros": [self._macro_to_dict(m) for m in self._macros]
        }
        try:
            with open(macro_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            logger.info(f"[MACROS] \u0421\u043e\u0445\u0440\u0430\u043d\u0435\u043d\u043e {len(data['macros'])} \u043c\u0430\u043a\u0440\u043e\u0441\u043e\u0432 \u0432 {macro_file}")
        except Exception as e:
            logger.error(f"[MACROS] \u041e\u0448\u0438\u0431\u043a\u0430 \u0441\u043e\u0445\u0440\u0430\u043d\u0435\u043d\u0438\u044f \u043c\u0430\u043a\u0440\u043e\u0441\u043e\u0432: {e}")

    def _init_icons_async(self):
        """Загрузка иконок скиллов в фоновом потоке — не блокирует запуск UI."""
        def _do_icons():
            try:
                if not self.skill_db:
                    return
                from utils import ensure_skill_icons
                skill_list = self.skill_db.get_all_skills_simple()
                ensure_skill_icons(skill_list)
                logger.info(f"[ICONS] [+] \u0418\u043a\u043e\u043d\u043a\u0438 \u0441\u043a\u0438\u043b\u043b\u043e\u0432 \u0437\u0430\u0433\u0440\u0443\u0436\u0435\u043d\u044b \u0432 \u043a\u0435\u0448")
            except Exception as e:
                logger.error(f"[ICONS] \u041e\u0448\u0438\u0431\u043a\u0430 \u0437\u0430\u0433\u0440\u0443\u0437\u043a\u0438 \u0438\u043a\u043e\u043d\u043e\u043a: {e}", exc_info=True)
        threading.Thread(target=_do_icons, daemon=True, name="IconLoader").start()

    def _run_auth_async(self):
        """Запускает проверку активации в фоновом потоке.
        Сетевые запросы — в потоке, обновление UI/QTimer — на главном потоке."""
        def _network_part():
            try:
                self._check_activation_on_startup()
            except Exception as e:
                logger.error(f"[AUTH] Ошибка в фоновой проверке: {e}", exc_info=True)
                self._is_activated = False
                self._activation_status = "error"
                self.activationStatusChanged.emit()
        threading.Thread(target=_network_part, daemon=True, name="AuthAsync").start()

    def init_subsystems(self):
        self.skill_db = skill_database.SkillDatabase(constants.SKILLS_JSON_FILE)
        # UI стартует без ожидания сети
        self._subscription_info = {}
        self.subscriptionChanged.emit()
        # Проверка активации в потоке — не блокирует главный поток
        if not self._auth_deferred:
            self._auth_deferred = True
            from PySide6.QtCore import QTimer
            QTimer.singleShot(100, self._run_auth_async)
        # Асинхронная загрузка иконок
        self._init_icons_async()
        self.target_distance = None
        self.movement_monitor = threads.MovementMonitor()
        self.movement_monitor.start()
        self.fast_distance_reader = threads.FastDistanceReader(
            get_area_fn=lambda: self._settings.get("mob_area"),
            get_settings_fn=lambda: self._settings,
        )
        self.fast_distance_reader.start()
        self.mouse_click_monitor = threads.MouseClickMonitor(self._target_window_title)
        self.mouse_click_monitor.start()
        logger.info("[MOUSE] MouseClickMonitor \u0437\u0430\u043f\u0443\u0449\u0435\u043d")
        from threads import BuffCheckThread
        self.buff_check_thread = BuffCheckThread(self)
        self.buff_check_thread.buffExpired.connect(self._on_buff_expired)
        self.buff_check_thread.start()
        logger.info("[BUFF] BuffCheckThread \u0437\u0430\u043f\u0443\u0449\u0435\u043d")
        from PySide6.QtCore import QTimer
        QTimer.singleShot(3000, lambda: self._check_updates_and_notify())
        if self._settings.get("ping_auto", True):
            interval = self._settings.get("ping_check_interval", 5)
            logger.info(f"[PING] \u0417\u0430\u043f\u0443\u0441\u043a PingMonitor: \u0438\u043d\u0442\u0435\u0440\u0432\u0430\u043b={interval}\u0441\u0435\u043a, process={self._settings['process_name']}")
            self.ping_monitor = threads.PingMonitor(self._settings["process_name"], interval)
            self.ping_monitor.ping_updated.connect(self.on_ping_updated)
            self.ping_monitor.start()
        else:
            logger.info(f"[PING] PingMonitor \u043e\u0442\u043a\u043b\u044e\u0447\u0435\u043d (ping_auto=False)")
        self.load_macros()
        if self._settings.get("use_ping_delays", False):
            self.recalculate_macro_delays()
        logger.info("[OCR] OCR \u043d\u0435 \u0437\u0430\u043f\u0443\u0449\u0435\u043d - \u043d\u0430\u0436\u043c\u0438\u0442\u0435 \u0421\u0422\u0410\u0420\u0422 \u0434\u043b\u044f \u0437\u0430\u043f\u0443\u0441\u043a\u0430")
        self.register_all_hotkeys()

    def cleanup(self):
        if getattr(self, '_cleanup_done', False):
            return
        self._cleanup_done = True
        logger.info("\u041e\u0441\u0442\u0430\u043d\u043e\u0432\u043a\u0430 \u043f\u0440\u043e\u0433\u0440\u0430\u043c\u043c\u044b...")

        tray_mgr = getattr(self, '_tray_icon_manager', None)
        if tray_mgr:
            try:
                tray_mgr.disconnect_signals()
            except Exception:
                pass

        self.unregister_all_hotkeys()

        logger.debug("\u042d\u0442\u0430\u043f 1: \u0431\u043b\u043e\u043a\u0438\u0440\u043e\u0432\u043a\u0430 \u043d\u043e\u0432\u044b\u0445 \u0437\u0430\u043f\u0443\u0441\u043a\u043e\u0432...")
        self._global_stopped = True
        self.globalStoppedChanged.emit()

        if self.mouse_click_monitor:
            try:
                self.mouse_click_monitor.stop()
                if self.mouse_click_monitor.isRunning():
                    self.mouse_click_monitor.wait(500)
            except Exception as e:
                logger.debug(f"[CLEANUP] MouseClickMonitor error: {e}")

        if hasattr(self, 'dispatcher') and self.dispatcher:
            logger.debug("\u042d\u0442\u0430\u043f 2: \u043e\u0441\u0442\u0430\u043d\u043e\u0432\u043a\u0430 \u0434\u0438\u0441\u043f\u0435\u0442\u0447\u0435\u0440\u0430...")
            try:
                self.dispatcher.stop_all_macros(timeout=3.0)
                self.dispatcher.stop()
            except Exception as e:
                logger.error(f"[CLEANUP] Dispatcher error: {e}")

        logger.debug("\u042d\u0442\u0430\u043f 3: \u043e\u0441\u0442\u0430\u043d\u043e\u0432\u043a\u0430 \u0432\u0441\u0435\u0445 \u043c\u0430\u043a\u0440\u043e\u0441\u043e\u0432...")
        for macro in self._macros:
            try:
                macro.stop()
            except Exception:
                pass
        for macro in self._macros:
            if macro.thread and macro.thread.is_alive():
                macro.thread.join(timeout=2.0)

        logger.debug("\u042d\u0442\u0430\u043f 4: \u043e\u0441\u0442\u0430\u043d\u043e\u0432\u043a\u0430 InputBlocker...")
        try:
            from input_blocker import get_global_blocker
            blocker = get_global_blocker()
            if blocker:
                blocker.stop()
        except Exception as e:
            logger.debug(f"[CLEANUP] InputBlocker error: {e}")

        logger.debug("\u042d\u0442\u0430\u043f 5: \u043e\u0441\u0442\u0430\u043d\u043e\u0432\u043a\u0430 \u0444\u043e\u043d\u043e\u0432\u044b\u0445 \u0441\u0435\u0440\u0432\u0438\u0441\u043e\u0432...")
        if self.target_reader:
            try:
                self.target_reader.stop()
                if self.target_reader.isRunning():
                    self.target_reader.wait(500)
            except Exception as e:
                logger.debug(f"[CLEANUP] OCR error: {e}")
        if self.ping_monitor:
            try:
                self._stop_ping_monitor()
            except Exception as e:
                logger.debug(f"[CLEANUP] PingMonitor error: {e}")
        if self.movement_monitor:
            self.movement_monitor.stop()
        if self.buff_check_thread:
            try:
                self.buff_check_thread.stop()
                if self.buff_check_thread.isRunning():
                    self.buff_check_thread.wait(500)
            except Exception as e:
                logger.debug(f"[CLEANUP] BuffCheckThread error: {e}")
        if hasattr(self, '_mouse_hook_manager') and self._mouse_hook_manager:
            try:
                self._mouse_hook_manager.stop()
                if hasattr(self._mouse_hook_manager, 'isRunning') and self._mouse_hook_manager.isRunning():
                    self._mouse_hook_manager.wait(1000)
            except Exception as e:
                logger.debug(f"[CLEANUP] MouseHookManager error: {e}")

        logger.debug("\u042d\u0442\u0430\u043f 6: \u0441\u043e\u0445\u0440\u0430\u043d\u0435\u043d\u0438\u0435 \u0434\u0430\u043d\u043d\u044b\u0445...")
        self.save_settings()
        self.save_macros()
        if self._current_profile:
            logger.info(f"[CLEANUP] \u0421\u043e\u0445\u0440\u0430\u043d\u0435\u043d\u0438\u0435 \u043f\u0440\u043e\u0444\u0438\u043b\u044f '{self._current_profile}' \u043f\u0435\u0440\u0435\u0434 \u0437\u0430\u043a\u0440\u044b\u0442\u0438\u0435\u043c...")
            self.save_profile(self._current_profile)
        logger.info("\u0417\u0430\u0432\u0435\u0440\u0448\u0435\u043d\u0438\u0435 \u0440\u0430\u0431\u043e\u0442\u044b.")

def main():
    logger.info("=" * 60)
    logger.info("[*] snbld resvap (QML + PySide6)")
    logger.info(f"[*] sys.frozen: {getattr(sys, 'frozen', False)}")
    logger.info(f"[*] sys._MEIPASS: {getattr(sys, '_MEIPASS', 'NOT SET')}")
    logger.info(f"[*] sys.executable: {sys.executable}")
    logger.info(f"[*] cwd: {os.getcwd()}")
    logger.info("=" * 60)

    is_frozen = getattr(sys, 'frozen', False)
    is_onefile = hasattr(sys, '_MEIPASS') or ('TEMP' in os.getcwd() and 'onefile' in sys.executable)
    is_nuitka_standalone = hasattr(sys, 'compiled') or ('dist_standalone' in sys.executable) or ('dist_standalone' in os.getcwd())
    is_packaged = is_frozen or is_onefile or is_nuitka_standalone

    logger.info(f"[DIAG] sys.executable: {sys.executable}")
    logger.info(f"[DIAG] sys.frozen: {is_frozen}")
    logger.info(f"[DIAG] sys._MEIPASS: {getattr(sys, '_MEIPASS', 'NOT SET')}")
    logger.info(f"[DIAG] sys.compiled: {getattr(sys, 'compiled', 'NOT SET')}")
    logger.info(f"[DIAG] os.getcwd(): {os.getcwd()}")
    logger.info(f"[DIAG] is_nuitka_standalone: {is_nuitka_standalone}")
    logger.info(f"[DIAG] is_packaged: {is_packaged}")
    logger.info(f"[DIAG] --admin-requested in argv: {'--admin-requested' in sys.argv}")

    if is_packaged:
        from utils import is_admin, run_as_admin
        admin_requested = '--admin-requested' in sys.argv
        if not is_admin():
            if admin_requested:
                logger.warning("[-] \u041f\u0435\u0440\u0435\u0437\u0430\u043f\u0443\u0441\u043a \u043e\u0442 \u0438\u043c\u0435\u043d\u0438 \u0430\u0434\u043c\u0438\u043d\u0438\u0441\u0442\u0440\u0430\u0442\u043e\u0440\u0430 \u043d\u0435 \u0443\u0434\u0430\u043b\u0441\u044f (\u043e\u0442\u043c\u0435\u043d\u0435\u043d \u0438\u043b\u0438 \u043e\u0448\u0438\u0431\u043a\u0430).")
                logger.warning("[i] \u041f\u0440\u043e\u0434\u043e\u043b\u0436\u0435\u043d\u0438\u0435 \u0440\u0430\u0431\u043e\u0442\u044b \u0432 \u043e\u0431\u044b\u0447\u043d\u043e\u043c \u0440\u0435\u0436\u0438\u043c\u0435 (\u0444\u0443\u043d\u043a\u0446\u0438\u0438 \u043c\u043e\u0433\u0443\u0442 \u0431\u044b\u0442\u044c \u043e\u0433\u0440\u0430\u043d\u0438\u0447\u0435\u043d\u044b)")
            else:
                logger.info("\U0001f504 \u0417\u0430\u043f\u0443\u0441\u043a \u0441 \u043f\u0440\u0430\u0432\u0430\u043c\u0438 \u0430\u0434\u043c\u0438\u043d\u0438\u0441\u0442\u0440\u0430\u0442\u043e\u0440\u0430...")
                if run_as_admin():
                    logger.info("[+] \u0417\u0430\u043f\u0440\u043e\u0441 \u0430\u0434\u043c\u0438\u043d \u043f\u0440\u0430\u0432 \u043e\u0442\u043f\u0440\u0430\u0432\u043b\u0435\u043d, \u0437\u0430\u0432\u0435\u0440\u0448\u0430\u0435\u043c \u0442\u0435\u043a\u0443\u0449\u0438\u0439 \u043f\u0440\u043e\u0446\u0435\u0441\u0441...")
                    sys.exit(0)
                else:
                    logger.warning("[-] \u041d\u0435 \u0443\u0434\u0430\u043b\u043e\u0441\u044c \u0437\u0430\u043f\u0440\u043e\u0441\u0438\u0442\u044c \u043f\u0440\u0430\u0432\u0430 \u0430\u0434\u043c\u0438\u043d\u0438\u0441\u0442\u0440\u0430\u0442\u043e\u0440\u0430.")
                    logger.warning("[i] \u041f\u0440\u043e\u0434\u043e\u043b\u0436\u0435\u043d\u0438\u0435 \u0440\u0430\u0431\u043e\u0442\u044b \u0432 \u043e\u0431\u044b\u0447\u043d\u043e\u043c \u0440\u0435\u0436\u0438\u043c\u0435 (\u0444\u0443\u043d\u043a\u0446\u0438\u0438 \u043c\u043e\u0433\u0443\u0442 \u0431\u044b\u0442\u044c \u043e\u0433\u0440\u0430\u043d\u0438\u0447\u0435\u043d\u044b)")
    else:
        logger.info("[dev] \u0420\u0435\u0436\u0438\u043c \u0440\u0430\u0437\u0440\u0430\u0431\u043e\u0442\u043a\u0438 - \u043f\u0440\u043e\u0432\u0435\u0440\u043a\u0430 \u0430\u0434\u043c\u0438\u043d \u043f\u0440\u0430\u0432 \u043f\u0440\u043e\u043f\u0443\u0449\u0435\u043d\u0430")

    app = QApplication(sys.argv)

    if is_packaged:
        try:
            ctypes.windll.kernel32.FreeConsole()
        except Exception:
            pass

    icon_path = resource_path("123.ico")
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))
        logger.info(f"[+] \u0418\u043a\u043e\u043d\u043a\u0430 \u0437\u0430\u0433\u0440\u0443\u0436\u0435\u043d\u0430: {icon_path}")

    font = QFont("Rubik", 10)
    app.setFont(font)

    ensure_all_resources()

    from utils.sound_alert import set_sound_files
    set_sound_files(
        os.path.join(app_path, "onn.mp3"),
        os.path.join(app_path, "off.mp3"),
    )

    os.environ["QML_DISABLE_DISK_CACHE"] = "1"
    engine = QQmlApplicationEngine()

    backend = Backend()
    backend.load_settings()
    backend.init_subsystems()

    engine.rootContext().setContextProperty("backend", backend)

    resource_helper = QMLResourceHelper()
    engine.rootContext().setContextProperty("ResourceHelper", resource_helper)

    tooltips_provider = get_tooltips_provider()
    engine.rootContext().setContextProperty("Tooltips", tooltips_provider)

    backend.engine = engine
    logger.debug("backend.engine set")

    qml_file = resource_path("qml/main.qml")
    if not os.path.exists(qml_file):
        qml_file = os.path.join(_get_app_dir(), "qml", "main.qml")
    engine.load(QUrl.fromLocalFile(qml_file))

    if not engine.rootObjects():
        logger.error("[MAIN] QML \u043d\u0435 \u0437\u0430\u0433\u0440\u0443\u0437\u0438\u043b\u0441\u044f! \u041e\u0447\u0438\u0441\u0442\u043a\u0430 \u0440\u0435\u0441\u0443\u0440\u0441\u043e\u0432...")
        backend.cleanup()
        sys.exit(-1)

    window = engine.rootObjects()[0]
    backend._main_window = window

    content_layer = window.findChild(QObject, "contentArea", Qt.FindChildrenRecursively)
    if not content_layer:
        logger.warning("[-] contentArea not found")

    if os.path.exists(icon_path):
        app_icon = QIcon(icon_path)
        app.setWindowIcon(app_icon)
        window.setIcon(app_icon)
        try:
            hwnd = int(window.winId())
            pixmap = app_icon.pixmap(256, 256)
            if pixmap:
                window.setIcon(app_icon)
        except Exception as e:
            logger.warning(f"[-] \u041d\u0435 \u0443\u0434\u0430\u043b\u043e\u0441\u044c \u0443\u0441\u0442\u0430\u043d\u043e\u0432\u0438\u0442\u044c \u0438\u043a\u043e\u043d\u043a\u0443 \u043d\u0430 \u043f\u0430\u043d\u0435\u043b\u044c \u0437\u0430\u0434\u0430\u0447: {e}")
        logger.info(f"[+] \u0418\u043a\u043e\u043d\u043a\u0430 \u0443\u0441\u0442\u0430\u043d\u043e\u0432\u043b\u0435\u043d\u0430: {icon_path}")
    else:
        logger.warning(f"[-] \u0418\u043a\u043e\u043d\u043a\u0430 \u043d\u0435 \u043d\u0430\u0439\u0434\u0435\u043d\u0430: {icon_path}")

    try:
        from utils.tray_icon import TrayIconManager, STATUS_RUNNING, STATUS_STOPPED
        backend._tray_enabled = True
        backend._tray_icon_manager = TrayIconManager(backend, app)
        backend._tray_icon_manager.init_tray()
        tray = backend._tray_icon_manager
        backend.startAllPressed.connect(lambda: tray.update_status(STATUS_RUNNING, "Макросы запущены"))
        backend.stopAllPressed.connect(lambda: tray.update_status(STATUS_STOPPED, "Макросы остановлены"))
        logger.info("[TRAY] TrayIconManager инициализирован")
    except Exception as e:
        logger.warning(f"[TRAY] TrayIconManager недоступен: {e}")
        backend._tray_enabled = False
        backend._tray_icon_manager = None

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
                    logger.info("[DWM] \u0417\u0430\u043a\u0440\u0443\u0433\u043b\u0451\u043d\u043d\u044b\u0435 \u0443\u0433\u043b\u044b \u043f\u0440\u0438\u043c\u0435\u043d\u0435\u043d\u044b")
                else:
                    logger.debug(f"[DWM] \u0420\u0435\u0437\u0443\u043b\u044c\u0442\u0430\u0442: 0x{result:08X}")
            except Exception as e:
                logger.debug(f"[DWM] \u041d\u0435 \u0443\u0434\u0430\u043b\u043e\u0441\u044c: {e}")

        def remove_window_border():
            try:
                hwnd = ctypes.c_void_p(int(window.winId()))
                DWMWA_BORDER_COLOR = 34
                DWMWA_COLOR_NONE = 0xFFFFFFFD
                border_color = ctypes.c_int(DWMWA_COLOR_NONE)
                DwmSetWindowAttribute(
                    hwnd, DWMWA_BORDER_COLOR,
                    ctypes.byref(border_color), ctypes.sizeof(border_color)
                )
                logger.info("[DWM] \u0420\u0430\u043c\u043a\u0430 \u0443\u0431\u0440\u0430\u043d\u0430 (DWMWA_BORDER_COLOR)")
            except Exception:
                pass
            try:
                class MARGINS(ctypes.Structure):
                    _fields_ = [("cxLeftWidth", ctypes.c_int),
                                ("cxRightWidth", ctypes.c_int),
                                ("cyTopHeight", ctypes.c_int),
                                ("cyBottomHeight", ctypes.c_int)]
                DwmExtendFrameIntoClientArea = dwmapi.DwmExtendFrameIntoClientArea
                DwmExtendFrameIntoClientArea.restype = ctypes.HRESULT
                DwmExtendFrameIntoClientArea.argtypes = [ctypes.c_void_p, ctypes.POINTER(MARGINS)]
                margins = MARGINS(-1, -1, -1, -1)
                DwmExtendFrameIntoClientArea(hwnd, ctypes.byref(margins))
            except Exception:
                pass

        from PySide6.QtCore import QTimer, QAbstractNativeEventFilter

        class BorderlessNativeFilter(QAbstractNativeEventFilter):
            def nativeEventFilter(self, eventType, message):
                if eventType == "windows_generic_MSG":
                    try:
                        msg = ctypes.wintypes.MSG.from_address(message.__int__())
                        if msg.message == 0x0083:
                            return True, 0
                    except Exception:
                        pass
                return False, 0

        borderless_filter = BorderlessNativeFilter()
        app.installNativeEventFilter(borderless_filter)

        QTimer.singleShot(500, apply_rounded_corners)
        QTimer.singleShot(500, remove_window_border)
        QTimer.singleShot(2000, apply_rounded_corners)
        QTimer.singleShot(2000, remove_window_border)
        window.visibleChanged.connect(apply_rounded_corners)
        window.visibleChanged.connect(remove_window_border)
    except Exception as e:
        logger.debug(f"[DWM] API \u043d\u0435\u0434\u043e\u0441\u0442\u0443\u043f\u0435\u043d: {e}")

    backend.minimizeRequested.connect(window.hide)
    backend.closeRequested.connect(window.close)

    class CleanupEventFilter(QObject):
        def __init__(self, backend_instance):
            super().__init__()
            self.backend = backend_instance
            self._done = False
        def eventFilter(self, obj, event):
            from PySide6.QtCore import QEvent
            if not self._done and event.type() == QEvent.Close:
                self._done = True
                logger.info("[EVENTFILTER] \u041f\u0435\u0440\u0435\u0445\u0432\u0430\u0442 Close \u2014 \u043e\u0441\u0442\u0430\u043d\u043e\u0432\u043a\u0430 \u043f\u043e\u0442\u043e\u043a\u043e\u0432...")
                self.backend.cleanup()
            return super().eventFilter(obj, event)

    cleanup_filter = CleanupEventFilter(backend)
    window.installEventFilter(cleanup_filter)
    backend._cleanup_filter = cleanup_filter

    app.aboutToQuit.connect(backend.cleanup)

    backend._main_window = window

    last_profile = backend._settings.get("last_active_profile", "")
    if last_profile:
        profile_path = os.path.join(backend.profiles_dir, f"{last_profile}.json")
        if os.path.exists(profile_path):
            logger.info(f"[PROFILE] \u0417\u0430\u0433\u0440\u0443\u0437\u043a\u0430 \u043f\u043e\u0441\u043b\u0435\u0434\u043d\u0435\u0433\u043e \u043f\u0440\u043e\u0444\u0438\u043b\u044f: {last_profile}")
            backend.load_profile(last_profile)
        else:
            logger.warning(f"[PROFILE] \u041f\u043e\u0441\u043b\u0435\u0434\u043d\u0438\u0439 \u043f\u0440\u043e\u0444\u0438\u043b\u044c '{last_profile}' \u043d\u0435 \u043d\u0430\u0439\u0434\u0435\u043d")

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
