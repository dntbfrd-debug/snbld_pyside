import time
import ctypes
import ctypes.wintypes
from typing import Optional, Tuple

from .logger_manager import get_logger
from .attach_thread import attached_thread_input as _attached_thread_input
from backend.win32_api import (GetForegroundWindow, GetWindowText, GetWindowTextTimeout,
    IsWindowVisible, EnumWindows, ShowWindow, SetForegroundWindow,
    SetWindowPos, GetDC, GetDeviceCaps, MonitorFromWindow, GetMonitorInfo,
    EnumDisplayMonitors, HWND_TOP, SWP_NOMOVE, SWP_NOSIZE,
    SWP_SHOWWINDOW, MONITOR_DEFAULTTONEAREST, SW_RESTORE)

logger = get_logger('macros')

_window_manager_instance = None

_user32 = ctypes.windll.user32

def _allow_set_foreground_window():
    try:
        _user32.AllowSetForegroundWindow.restype = ctypes.wintypes.BOOL
        _user32.AllowSetForegroundWindow.argtypes = [ctypes.wintypes.DWORD]
        _user32.AllowSetForegroundWindow(ctypes.wintypes.DWORD(-1))
    except Exception:
        pass

def _switch_to_this_window(hwnd):
    try:
        _user32.SwitchToThisWindow.restype = None
        _user32.SwitchToThisWindow.argtypes = [ctypes.c_void_p, ctypes.wintypes.BOOL]
        _user32.SwitchToThisWindow(hwnd, True)
        return True
    except Exception:
        return False

def get_window_manager():
    global _window_manager_instance
    if _window_manager_instance is None:
        _window_manager_instance = WindowManager()
    return _window_manager_instance


class WindowManager:
    def __init__(self):
        self._window_locked = False
        self._target_window_title = ""
        self._target_hwnd: Optional[int] = None
        self._window_position: Optional[Tuple[int, int]] = None
        self._last_activation_time = 0
        self._activation_cooldown = 0.5
        self._skip_window_activation = True
        self._use_window_message_input = False

    @property
    def window_locked(self) -> bool:
        return self._window_locked

    @window_locked.setter
    def window_locked(self, value: bool) -> None:
        self._window_locked = bool(value)
        logger.debug(f"Window locked: {self._window_locked}")

    @property
    def target_window_title(self) -> str:
        return self._target_window_title

    @target_window_title.setter
    def target_window_title(self, value: str) -> None:
        self._target_window_title = str(value).strip()
        logger.debug(f"Target window title: {self._target_window_title}")

    def set_window_lock(self, locked: bool, title: str = "") -> None:
        self._window_locked = locked
        self._target_window_title = title.strip()
        logger.info(f"Блокировка окна: locked={locked}, title='{self._target_window_title}'")

    def check_window(self) -> bool:
        if not self._window_locked:
            return True
        if self._skip_window_activation:
            return True
        target = self._target_window_title.strip().lower()
        if not target:
            return True
        try:
            hwnd = GetForegroundWindow()
            active_title = GetWindowText(hwnd).lower()
            result = target in active_title
            if not result:
                logger.debug(f"Окно неактивно: '{active_title}' != '{target}'")
            return result
        except Exception as e:
            logger.error(f"Ошибка проверки окна: {e}", exc_info=True)
            return True

    def activate_window(self, force: bool = False) -> bool:
        if not self._target_window_title:
            return False
        if self._skip_window_activation:
            logger.debug("Активация окна отключена в настройках")
            return self.check_window()
        current_time = time.time()
        if not force and current_time - self._last_activation_time < self._activation_cooldown:
            return self.check_window()
        self._last_activation_time = current_time

        def enum_callback(hwnd, _):
            try:
                if IsWindowVisible(hwnd):
                    title = GetWindowTextTimeout(hwnd)
                    if title and self._target_window_title.lower() in title.lower():
                        hwnds.append(hwnd)
            except Exception:
                pass
            return True

        hwnds = []
        EnumWindows(enum_callback)
        if not hwnds:
            return False
        hwnd = hwnds[0]
        if GetForegroundWindow() == hwnd:
            return True
        try:
            ShowWindow(hwnd, SW_RESTORE)
            _allow_set_foreground_window()

            with _attached_thread_input(hwnd) as attached:
                if not attached:
                    logger.warning(f"AttachThreadInput не удался (UIPI), использую SwitchToThisWindow: hwnd={hwnd}")
                SetWindowPos(hwnd, HWND_TOP, 0, 0, 0, 0,
                            SWP_NOMOVE | SWP_NOSIZE | SWP_SHOWWINDOW)
                success = False
                for attempt in range(3):
                    try:
                        _switch_to_this_window(hwnd)
                        time.sleep(0.05 + (attempt * 0.05))
                        if GetForegroundWindow() == hwnd:
                            success = True
                            break
                        SetForegroundWindow(hwnd)
                        time.sleep(0.05)
                        if GetForegroundWindow() == hwnd:
                            success = True
                            break
                    except Exception:
                        time.sleep(0.1)
            if success:
                logger.debug(f"Окно активировано успешно: {hwnd} (попытка {attempt+1})")
                time.sleep(0.08)
                return True
            else:
                logger.warning(f"Не удалось активировать окно после 3 попыток: {hwnd}")
                return False
        except Exception as e:
            logger.error(f"Ошибка активации окна: {e}", exc_info=True)
        return False

    @property
    def skip_window_activation(self) -> bool:
        return self._skip_window_activation

    @skip_window_activation.setter
    def skip_window_activation(self, value: bool) -> None:
        self._skip_window_activation = bool(value)
        logger.info(f"Автоматическая активация окна: {'ОТКЛЮЧЕНА' if value else 'ВКЛЮЧЕНА'}")

    @property
    def use_window_message_input(self) -> bool:
        return self._use_window_message_input

    @use_window_message_input.setter
    def use_window_message_input(self, value: bool) -> None:
        self._use_window_message_input = bool(value)
        logger.info(f"Отправка ввода напрямую в окно: {'ВКЛЮЧЕНО' if value else 'ОТКЛЮЧЕНО'}")

    def get_diagnostic_info(self) -> dict:
        try:
            foreground_hwnd = GetForegroundWindow()
            foreground_title = GetWindowText(foreground_hwnd)
            monitor_info = GetMonitorInfo(MonitorFromWindow(foreground_hwnd, MONITOR_DEFAULTTONEAREST))
            monitor_rect = monitor_info.get('Monitor', (0,0,0,0))
            work_area = monitor_info.get('Work', (0,0,0,0))
            return {
                "skip_activation": self._skip_window_activation,
                "window_locked": self._window_locked,
                "target_title": self._target_window_title,
                "last_activation": self._last_activation_time,
                "cooldown_ms": int(self._activation_cooldown * 1000),
                "foreground_hwnd": foreground_hwnd,
                "foreground_title": foreground_title,
                "monitor_left": monitor_rect[0],
                "monitor_top": monitor_rect[1],
                "monitor_right": monitor_rect[2],
                "monitor_bottom": monitor_rect[3],
                "work_area_width": work_area[2] - work_area[0],
                "work_area_height": work_area[3] - work_area[1],
                "monitors_count": EnumDisplayMonitors(),
                "current_dpi": GetDeviceCaps(GetDC(0), 88),
            }
        except Exception as e:
            logger.error(f"Ошибка получения диагностической информации: {e}", exc_info=True)
            return {}
