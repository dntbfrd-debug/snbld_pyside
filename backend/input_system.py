import time
import ctypes
from ctypes import wintypes
from backend.logger_manager import get_logger
from backend.attach_thread import attached_thread_input as _attached_thread_input
from backend.win32_api import (MapVirtualKey, PostMessage, ScreenToClient,
    GetCursorPos, GetForegroundWindow, SetForegroundWindow,
    GetDC, GetDeviceCaps, ReleaseDC,
    WM_KEYDOWN, WM_KEYUP, WM_LBUTTONDOWN, WM_LBUTTONUP,
    WM_RBUTTONDOWN, WM_RBUTTONUP, MK_LBUTTON, MK_RBUTTON)

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
        self._vk_codes = VIRTUAL_KEYS.copy()

    def set_target(self, hwnd: int) -> None:
        self.target_hwnd = hwnd
        logger.info(f"[INPUT]  Целевое окно установлено: hwnd={hwnd}")

    def _use_sendinput_fallback(self, key_name: str) -> bool:
        """Отправляет клавишу через SendInput (активация окна + глобальный ввод).
        Используется, когда AttachThreadInput не работает (UIPI на Windows 8+)."""
        return key_down_sendinput(key_name) and key_up_sendinput(key_name)

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
                logger.info(f" Клавиша '{key_name}' отправлена")
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
                SetForegroundWindow(self.target_hwnd)
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
                SetForegroundWindow(self.target_hwnd)
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
            with _attached_thread_input(self.target_hwnd) as attached:
                if not attached:
                    logger.debug("[INPUT] AttachThreadInput не удался для click_left, fallback на SendInput")
                    # Для SendInput клика используем MOUSEEVENTF_LEFTDOWN | MOUSEEVENTF_LEFTUP
                    inputs = (INPUT * 2)()
                    inputs[0].type = 0  # INPUT_MOUSE
                    inputs[0].union.mi.dwFlags = 0x0002  # MOUSEEVENTF_LEFTDOWN
                    inputs[0].union.mi.time = 0
                    inputs[1].type = 0
                    inputs[1].union.mi.dwFlags = 0x0004  # MOUSEEVENTF_LEFTUP
                    inputs[1].union.mi.time = 0
                    SendInput(2, inputs, ctypes.sizeof(INPUT))
                    return
                pos = ScreenToClient(self.target_hwnd, GetCursorPos())
                lparam = (pos[1] << 16) | pos[0]
                PostMessage(self.target_hwnd, WM_LBUTTONDOWN, MK_LBUTTON, lparam)
                time.sleep(0.01)
                PostMessage(self.target_hwnd, WM_LBUTTONUP, 0, lparam)
                logger.debug(f" Левый клик {pos}")
        except Exception as e:
            logger.error(f" Ошибка левого клика: {e}")

    def click_right(self) -> None:
        if not self.target_hwnd:
            return

        try:
            with _attached_thread_input(self.target_hwnd) as attached:
                if not attached:
                    logger.debug("[INPUT] AttachThreadInput не удался для click_right, fallback на SendInput")
                    inputs = (INPUT * 2)()
                    inputs[0].type = 0
                    inputs[0].union.mi.dwFlags = 0x0008  # MOUSEEVENTF_RIGHTDOWN
                    inputs[0].union.mi.time = 0
                    inputs[1].type = 0
                    inputs[1].union.mi.dwFlags = 0x0010  # MOUSEEVENTF_RIGHTUP
                    inputs[1].union.mi.time = 0
                    SendInput(2, inputs, ctypes.sizeof(INPUT))
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
            with _attached_thread_input(self.target_hwnd) as attached:
                if not attached:
                    logger.debug(f"[INPUT] AttachThreadInput не удался для click_at ({x},{y}), fallback на SendInput")
                    SetForegroundWindow(self.target_hwnd)
                    time.sleep(0.05)
                    # MOUSEEVENTF_ABSOLUTE использует нормализованные координаты 0..65535
                    hdc = GetDC(0)
                    if hdc:
                        screen_w = GetDeviceCaps(hdc, 118)  # HORZRES
                        screen_h = GetDeviceCaps(hdc, 117)  # VERTRES
                        ReleaseDC(0, hdc)
                    else:
                        screen_w, screen_h = 1920, 1080
                    norm_x = int(x * 65535 / screen_w)
                    norm_y = int(y * 65535 / screen_h)
                    inputs = (INPUT * 2)()
                    inputs[0].type = 0
                    inputs[0].union.mi.dx = norm_x
                    inputs[0].union.mi.dy = norm_y
                    inputs[0].union.mi.dwFlags = 0x8000 | 0x0002  # MOUSEEVENTF_ABSOLUTE | MOUSEEVENTF_LEFTDOWN
                    inputs[0].union.mi.time = 0
                    inputs[1].type = 0
                    inputs[1].union.mi.dx = norm_x
                    inputs[1].union.mi.dy = norm_y
                    inputs[1].union.mi.dwFlags = 0x8000 | 0x0004  # MOUSEEVENTF_ABSOLUTE | MOUSEEVENTF_LEFTUP
                    inputs[1].union.mi.time = 0
                    SendInput(2, inputs, ctypes.sizeof(INPUT))
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


def click_at_position(x, y):
    input_system.click_at_position(x, y)
