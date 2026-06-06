import time
import ctypes
from ctypes import wintypes
from backend.logger_manager import get_logger
from backend.attach_thread import attached_thread_input as _attached_thread_input
from backend.window_manager import get_window_manager
from backend.win32_api import (MapVirtualKey, PostMessage, ScreenToClient,
    GetCursorPos, GetForegroundWindow, SetForegroundWindow,
    GetDC, GetDeviceCaps, ReleaseDC,
    WM_KEYDOWN, WM_KEYUP, WM_LBUTTONDOWN, WM_LBUTTONUP,
    WM_RBUTTONDOWN, WM_RBUTTONUP, MK_LBUTTON, MK_RBUTTON)

GetSystemMetrics = ctypes.windll.user32.GetSystemMetrics

logger = get_logger('input')

KEYEVENTF_KEYDOWN = 0x0000
KEYEVENTF_KEYUP = 0x0002


class KEYBDINPUT(ctypes.Structure):
    _fields_ = [
        ("wVk", wintypes.WORD),
        ("wScan", wintypes.WORD),
        ("dwFlags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ctypes.c_void_p)
    ]

class MOUSEINPUT(ctypes.Structure):
    _fields_ = [
        ("dx", wintypes.LONG),
        ("dy", wintypes.LONG),
        ("mouseData", wintypes.DWORD),
        ("dwFlags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ctypes.c_void_p)
    ]

class HARDWAREINPUT(ctypes.Structure):
    _fields_ = [
        ("uMsg", wintypes.DWORD),
        ("wParamL", wintypes.WORD),
        ("wParamH", wintypes.WORD)
    ]

class INPUT_UNION(ctypes.Union):
    _fields_ = [
        ("ki", KEYBDINPUT),
        ("mi", MOUSEINPUT),
        ("hi", HARDWAREINPUT)
    ]

class INPUT(ctypes.Structure):
    _fields_ = [
        ("type", wintypes.DWORD),
        ("union", INPUT_UNION)
    ]

user32 = ctypes.windll.user32
SendInput = user32.SendInput
SendInput.argtypes = [wintypes.UINT, ctypes.POINTER(INPUT), wintypes.INT]
SendInput.restype = wintypes.UINT


from constants import VIRTUAL_KEYS


class InputSystem:

    def __init__(self):
        self.target_hwnd = None
        self.use_sendinput = False
        self._vk_codes = VIRTUAL_KEYS.copy()

    def set_target(self, hwnd: int) -> None:
        self.target_hwnd = hwnd
        logger.info(f"[INPUT]  Целевое окно установлено: hwnd={hwnd}")

    def set_use_sendinput(self, enabled: bool) -> None:
        self.use_sendinput = bool(enabled)
        logger.info(f"[INPUT]  Принудительный SendInput: {'ВКЛ' if enabled else 'ВЫКЛ'}")

    def key(self, key_name: str) -> None:
        if not self.target_hwnd:
            logger.warning(f" Целевое окно не установлено, клавиша '{key_name}' не отправлена")
            return

        key_lower = key_name.lower()
        vk = self._vk_codes.get(key_lower)

        if not vk:
            logger.warning(f" Неизвестная клавиша: {key_name}")
            return

        try:
            if self.use_sendinput:
                self.key_down_sendinput(key_name)
                time.sleep(0.01)
                self.key_up_sendinput(key_name)
                logger.debug(f"[INPUT]  send_key '{key_name}' через SendInput (forced)")
                return
            with _attached_thread_input(self.target_hwnd) as attached:
                if not attached:
                    logger.debug(f"[INPUT] AttachThreadInput не удался для '{key_name}', fallback на SendInput")
                    self.key_down_sendinput(key_name)
                    time.sleep(0.01)
                    self.key_up_sendinput(key_name)
                    return
                scan = MapVirtualKey(vk, 0)
                PostMessage(self.target_hwnd, WM_KEYDOWN, vk, (scan << 16) | 1)
                PostMessage(self.target_hwnd, WM_KEYUP, vk, (scan << 16) | 0xC0000001)
                time.sleep(0.005)
                logger.debug(f"[INPUT]  send_key '{key_name}' → hwnd={self.target_hwnd}")
        except Exception as e:
            logger.error(f" Ошибка отправки клавиши: {e}")

    def key_down(self, key_name: str) -> None:
        if not self.target_hwnd:
            logger.warning(f" Целевое окно не установлено, key_down '{key_name}' не отправлен")
            return
        key_lower = key_name.lower()
        vk = self._vk_codes.get(key_lower)
        if not vk:
            logger.warning(f" key_down: неизвестная клавиша '{key_name}'")
            return
        try:
            if self.use_sendinput:
                self.key_down_sendinput(key_name)
                return
            with _attached_thread_input(self.target_hwnd) as attached:
                if not attached:
                    logger.debug(f"[INPUT] AttachThreadInput не удался для key_down '{key_name}', fallback на SendInput")
                    self.key_down_sendinput(key_name)
                    return
                scan = MapVirtualKey(vk, 0)
                lparam = (scan << 16) | 1
                PostMessage(self.target_hwnd, WM_KEYDOWN, vk, lparam)
                logger.debug(f" key_down: '{key_name}', vk=0x{vk:X}, lparam=0x{lparam:X}, hwnd={self.target_hwnd}")
        except Exception as e:
            logger.error(f" key_down '{key_name}': {e}")

    def key_up(self, key_name: str) -> None:
        if not self.target_hwnd:
            logger.warning(f" Целевое окно не установлено, key_up '{key_name}' не отправлен")
            return
        key_lower = key_name.lower()
        vk = self._vk_codes.get(key_lower)
        if not vk:
            logger.debug(f"key_up: неизвестная клавиша '{key_name}', пропускаем")
            return
        try:
            if self.use_sendinput:
                self.key_up_sendinput(key_name)
                return
            with _attached_thread_input(self.target_hwnd) as attached:
                if not attached:
                    logger.debug(f"[INPUT] AttachThreadInput не удался для key_up '{key_name}', fallback на SendInput")
                    self.key_up_sendinput(key_name)
                    return
                scan = MapVirtualKey(vk, 0)
                lparam = (scan << 16) | 0xC0000001
                PostMessage(self.target_hwnd, WM_KEYUP, vk, lparam)
                logger.debug(f" key_up: '{key_name}' отправлен, vk=0x{vk:X}, lparam=0x{lparam:X}, hwnd={self.target_hwnd}")
        except Exception as e:
            logger.error(f" key_up '{key_name}': {e}")

    def key_down_sendinput(self, key_name: str) -> bool:
        key_lower = key_name.lower()
        vk = self._vk_codes.get(key_lower)
        if not vk:
            logger.warning(f"key_down_sendinput: неизвестная клавиша '{key_name}'")
            return False
        
        try:
            if self.target_hwnd:
                if not get_window_manager().skip_window_activation:
                    fg = SetForegroundWindow(self.target_hwnd)
                    if not fg:
                        logger.debug(f"[INPUT] SetForegroundWindow не удался для key_down '{key_name}'")
                    time.sleep(0.01)
            
            inputs = (INPUT * 1)()
            inputs[0].type = 1
            inputs[0].union.ki.wVk = vk
            inputs[0].union.ki.wScan = 0
            inputs[0].union.ki.dwFlags = KEYEVENTF_KEYDOWN
            inputs[0].union.ki.time = 0
            inputs[0].union.ki.dwExtraInfo = 0
            
            result = SendInput(1, inputs, ctypes.sizeof(INPUT))
            logger.debug(f" SendInput key_down '{key_name}', vk=0x{vk:X}, result={result}")
            return result == 1
        except Exception as e:
            logger.error(f" key_down_sendinput '{key_name}': {e}")
            return False
    
    def key_up_sendinput(self, key_name: str) -> bool:
        key_lower = key_name.lower()
        vk = self._vk_codes.get(key_lower)
        if not vk:
            logger.debug(f"key_up_sendinput: неизвестная клавиша '{key_name}', пропускаем")
            return False
        
        try:
            if self.target_hwnd:
                if not get_window_manager().skip_window_activation:
                    fg = SetForegroundWindow(self.target_hwnd)
                    if not fg:
                        logger.debug(f"[INPUT] SetForegroundWindow не удался для key_up '{key_name}'")
                    time.sleep(0.01)
            
            inputs = (INPUT * 1)()
            inputs[0].type = 1
            inputs[0].union.ki.wVk = vk
            inputs[0].union.ki.wScan = 0
            inputs[0].union.ki.dwFlags = KEYEVENTF_KEYUP
            inputs[0].union.ki.time = 0
            inputs[0].union.ki.dwExtraInfo = 0
            
            result = SendInput(1, inputs, ctypes.sizeof(INPUT))
            logger.debug(f" SendInput key_up '{key_name}', vk=0x{vk:X}, result={result}")
            return result == 1
        except Exception as e:
            logger.error(f" key_up_sendinput '{key_name}': {e}")
            return False

    def click_left(self) -> None:
        if not self.target_hwnd:
            return

        try:
            if self.use_sendinput:
                self._sendinput_click(0x0002, 0x0004)
                logger.debug("[INPUT] Левый клик через SendInput (forced)")
                return
            with _attached_thread_input(self.target_hwnd) as attached:
                if not attached:
                    logger.debug("[INPUT] AttachThreadInput не удался для click_left, fallback на SendInput")
                    self._sendinput_click(0x0002, 0x0004)
                    return
                pos = ScreenToClient(self.target_hwnd, GetCursorPos())
                lparam = (pos[1] << 16) | pos[0]
                PostMessage(self.target_hwnd, WM_LBUTTONDOWN, MK_LBUTTON, lparam)
                time.sleep(0.01)
                PostMessage(self.target_hwnd, WM_LBUTTONUP, 0, lparam)
                logger.debug(f" Левый клик {pos}")
        except Exception as e:
            logger.error(f" Ошибка левого клика: {e}")

    def _sendinput_click(self, down_flag, up_flag):
        inputs = (INPUT * 2)()
        inputs[0].type = 0
        inputs[0].union.mi.dwFlags = down_flag
        inputs[0].union.mi.time = 0
        inputs[1].type = 0
        inputs[1].union.mi.dwFlags = up_flag
        inputs[1].union.mi.time = 0
        SendInput(2, inputs, ctypes.sizeof(INPUT))

    def _sendinput_click_at(self, x, y):
        if not get_window_manager().skip_window_activation:
            SetForegroundWindow(self.target_hwnd)
            time.sleep(0.05)
        screen_w = GetSystemMetrics(0)
        screen_h = GetSystemMetrics(1)
        if screen_w == 0 or screen_h == 0:
            screen_w, screen_h = 1920, 1080
        norm_x = int(x * 65535 / screen_w)
        norm_y = int(y * 65535 / screen_h)
        inputs = (INPUT * 2)()
        inputs[0].type = 0
        inputs[0].union.mi.dx = norm_x
        inputs[0].union.mi.dy = norm_y
        inputs[0].union.mi.dwFlags = 0x8000 | 0x0001 | 0x0002
        inputs[0].union.mi.time = 0
        inputs[1].type = 0
        inputs[1].union.mi.dx = norm_x
        inputs[1].union.mi.dy = norm_y
        inputs[1].union.mi.dwFlags = 0x8000 | 0x0001 | 0x0004
        inputs[1].union.mi.time = 0
        SendInput(2, inputs, ctypes.sizeof(INPUT))
        logger.debug(f" Клик AT ({x},{y}) через SendInput")

    def click_right(self) -> None:
        if not self.target_hwnd:
            return

        try:
            if self.use_sendinput:
                self._sendinput_click(0x0008, 0x0010)
                logger.debug("[INPUT] Правый клик через SendInput (forced)")
                return
            with _attached_thread_input(self.target_hwnd) as attached:
                if not attached:
                    logger.debug("[INPUT] AttachThreadInput не удался для click_right, fallback на SendInput")
                    self._sendinput_click(0x0008, 0x0010)
                    return
                pos = ScreenToClient(self.target_hwnd, GetCursorPos())
                lparam = (pos[1] << 16) | pos[0]
                PostMessage(self.target_hwnd, WM_RBUTTONDOWN, MK_RBUTTON, lparam)
                time.sleep(0.01)
                PostMessage(self.target_hwnd, WM_RBUTTONUP, 0, lparam)
                logger.debug(f" Правый клик {pos}")
        except Exception as e:
            logger.error(f" Ошибка правого клика: {e}")

    def click_at_position(self, x: int, y: int) -> None:
        if not self.target_hwnd:
            logger.warning(f" Целевое окно не установлено, клик в ({x},{y}) не отправлен")
            return

        try:
            if self.use_sendinput:
                self._sendinput_click_at(x, y)
                return
            with _attached_thread_input(self.target_hwnd) as attached:
                if not attached:
                    logger.debug(f"[INPUT] AttachThreadInput не удался для click_at ({x},{y}), fallback на SendInput")
                    self._sendinput_click_at(x, y)
                    return
                client_pos = ScreenToClient(self.target_hwnd, (x, y))
                lparam = (client_pos[1] << 16) | client_pos[0]
                PostMessage(self.target_hwnd, WM_LBUTTONDOWN, MK_LBUTTON, lparam)
                time.sleep(0.01)
                PostMessage(self.target_hwnd, WM_LBUTTONUP, 0, lparam)
                logger.debug(f" Клик AT ({x},{y}) -> клиентские ({client_pos[0]},{client_pos[1]})")
        except Exception as e:
            logger.error(f" click_at_position ({x},{y}): {e}")


input_system = InputSystem()


def send_key(key):
    input_system.key(key)


def click_left():
    input_system.click_left()


def click_right():
    input_system.click_right()


def key_down(key):
    input_system.key_down(key)


def key_up(key):
    input_system.key_up(key)


def key_down_sendinput(key):
    input_system.key_down_sendinput(key)


def key_up_sendinput(key):
    input_system.key_up_sendinput(key)


def set_use_sendinput(enabled: bool):
    input_system.set_use_sendinput(enabled)
