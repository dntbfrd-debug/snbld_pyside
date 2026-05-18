import ctypes
import ctypes.wintypes
import threading
import time
from backend.logger_manager import get_logger
import concurrent.futures

from backend.hooks_guard import try_register_hook, unregister_hook

logger = get_logger('input_blocker')


WH_KEYBOARD_LL = 13
WH_MOUSE_LL    = 14

HC_ACTION = 0

WM_KEYDOWN    = 0x0100
WM_SYSKEYDOWN = 0x0104
WM_KEYUP      = 0x0101
WM_SYSKEYUP   = 0x0105

WM_LBUTTONDOWN = 0x0201
WM_LBUTTONUP   = 0x0202
WM_RBUTTONDOWN = 0x0204
WM_RBUTTONUP   = 0x0205

WM_QUIT = 0x0012

_DEBUG_PASS_THROUGH = False

LLKHF_INJECTED = 0x10
LLMHF_INJECTED = 0x01

SMTO_ABORTIFHUNG = 0x0002
WM_GETTEXT = 0x000D

VK_SHIFT   = 0x10
VK_CONTROL = 0x11
VK_MENU    = 0x12


class KBDLLHOOKSTRUCT(ctypes.Structure):
    _fields_ = [
        ("vkCode",      ctypes.wintypes.DWORD),
        ("scanCode",    ctypes.wintypes.DWORD),
        ("flags",       ctypes.wintypes.DWORD),
        ("time",        ctypes.wintypes.DWORD),
        ("dwExtraInfo", ctypes.c_ulonglong),
    ]


class MSLLHOOKSTRUCT(ctypes.Structure):
    _fields_ = [
        ("pt",          ctypes.wintypes.POINT),
        ("mouseData",   ctypes.wintypes.DWORD),
        ("flags",       ctypes.wintypes.DWORD),
        ("time",        ctypes.wintypes.DWORD),
        ("dwExtraInfo", ctypes.c_ulonglong),
    ]


class MSG(ctypes.Structure):
    _fields_ = [
        ("hwnd",    ctypes.c_void_p),
        ("message", ctypes.wintypes.UINT),
        ("wParam",  ctypes.wintypes.WPARAM),
        ("lParam",  ctypes.wintypes.LPARAM),
        ("time",    ctypes.wintypes.DWORD),
        ("pt",      ctypes.wintypes.POINT),
    ]



KeyboardProc = ctypes.WINFUNCTYPE(
    ctypes.c_long,
    ctypes.c_int,
    ctypes.wintypes.WPARAM,
    ctypes.c_void_p,
)

MouseProc = ctypes.WINFUNCTYPE(
    ctypes.c_long,
    ctypes.c_int,
    ctypes.wintypes.WPARAM,
    ctypes.c_void_p,
)


user32   = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32

user32.SetWindowsHookExW.restype = ctypes.c_void_p
user32.SetWindowsHookExW.argtypes = [
    ctypes.c_int,
    ctypes.c_void_p,
    ctypes.c_void_p,
    ctypes.wintypes.DWORD,
]

user32.UnhookWindowsHookEx.restype = ctypes.wintypes.BOOL
user32.UnhookWindowsHookEx.argtypes = [ctypes.c_void_p]

user32.CallNextHookEx.restype = ctypes.c_ssize_t
user32.CallNextHookEx.argtypes = [
    ctypes.c_void_p,
    ctypes.c_int,
    ctypes.wintypes.WPARAM,
    ctypes.c_void_p,
]

user32.GetMessageW.restype = ctypes.wintypes.BOOL
user32.GetMessageW.argtypes = [
    ctypes.POINTER(MSG),
    ctypes.c_void_p,
    ctypes.wintypes.UINT,
    ctypes.wintypes.UINT,
]

user32.PeekMessageW.restype = ctypes.wintypes.BOOL
user32.PeekMessageW.argtypes = [
    ctypes.POINTER(MSG),
    ctypes.c_void_p,
    ctypes.wintypes.UINT,
    ctypes.wintypes.UINT,
    ctypes.wintypes.UINT,
]

PM_REMOVE = 1

user32.TranslateMessage.restype = ctypes.wintypes.BOOL
user32.TranslateMessage.argtypes = [ctypes.POINTER(MSG)]

user32.DispatchMessageW.restype = ctypes.c_longlong
user32.DispatchMessageW.argtypes = [ctypes.POINTER(MSG)]

user32.PostThreadMessageW.restype = ctypes.wintypes.BOOL
user32.PostThreadMessageW.argtypes = [
    ctypes.wintypes.DWORD,
    ctypes.wintypes.UINT,
    ctypes.wintypes.WPARAM,
    ctypes.wintypes.LPARAM,
]

user32.GetForegroundWindow.restype = ctypes.c_void_p
user32.GetWindowTextW.restype = ctypes.c_int
user32.GetWindowTextW.argtypes = [ctypes.c_void_p, ctypes.c_wchar_p, ctypes.c_int]

user32.GetAsyncKeyState.restype = ctypes.c_short
user32.GetAsyncKeyState.argtypes = [ctypes.c_int]

kernel32.GetModuleHandleW.restype = ctypes.c_void_p
kernel32.GetModuleHandleW.argtypes = [ctypes.c_wchar_p]

kernel32.GetCurrentThreadId.restype = ctypes.wintypes.DWORD


_VK_NAME = {
    'backspace': 0x08,  'tab': 0x09,   'enter': 0x0D,
    'shift': 0x10,       'ctrl': 0x11,  'alt': 0x12,
    'pause': 0x13,       'capslock': 0x14,  'esc': 0x1B,
    'space': 0x20,       'pageup': 0x21,    'pagedown': 0x22,
    'end': 0x23,         'home': 0x24,
    'left': 0x25,        'up': 0x26,        'right': 0x27,  'down': 0x28,
    'printscreen': 0x2C, 'insert': 0x2D,    'delete': 0x2E,
    'f1': 0x70, 'f2': 0x71,  'f3': 0x72,  'f4': 0x73,
    'f5': 0x74, 'f6': 0x75,  'f7': 0x76,  'f8': 0x77,
    'f9': 0x78, 'f10': 0x79, 'f11': 0x7A,  'f12': 0x7B,
}
_VK_NAME.update({str(k): ord(str(k)) for k in range(10)})
_VK_NAME.update({chr(c): ord(chr(c).upper()) for c in range(ord('a'), ord('z')+1)})

_MODIFIER_MAP = {
    'ctrl': VK_CONTROL, 'control': VK_CONTROL,
    'shift': VK_SHIFT,
    'alt': VK_MENU,
}


def _parse_hotkey(hotkey_str: str):
    if not hotkey_str:
        return None, None
    modifier = None
    key = None
    for part in hotkey_str.lower().strip().split('+'):
        part = part.strip()
        if part in _MODIFIER_MAP:
            modifier = _MODIFIER_MAP[part]
        elif part in _VK_NAME:
            key = _VK_NAME[part]
        elif len(part) == 1 and part.isalnum():
            key = ord(part.upper())
    return modifier, key



class InputBlocker:

    def __init__(self, backend_getter):
        self._get_backend = backend_getter

        self._running = False
        self._keyboard_hook = None
        self._mouse_hook = None
        self._thread = None
        self._thread_id = None
        self._lock = threading.Lock()

        self._kb_proc_ref = None
        self._mouse_proc_ref = None

        self.stats = {
            'kb_blocked': 0,
            'kb_passed':  0,
            'ms_blocked': 0,
            'ms_passed':  0,
        }

        self._blocked_keys = set()
        self._blocked_buttons = set()
        
        self._executor = concurrent.futures.ThreadPoolExecutor(max_workers=5, thread_name_prefix="InputBlocker")

        # Регистрация дополнительных callback'ов горячих клавиш
        # (чтобы не создавать отдельный WH_KEYBOARD_LL в HotkeyManager)
        self._hotkey_callbacks = {}
        self._hotkey_lock = threading.Lock()

        logger.info("[InputBlocker] Инициализирован")

    def register_hotkey_callback(self, hotkey_str: str, callback, suppress=True) -> bool:
        """Регистрирует callback на горячую клавишу.
        Использует существующий WH_KEYBOARD_LL — не создаёт новый хук."""
        mod_vk, key_vk = _parse_hotkey(hotkey_str)
        if key_vk is None:
            logger.error(f"[InputBlocker] Неверный формат горячей клавиши: {hotkey_str}")
            return False
        with self._hotkey_lock:
            key = (mod_vk, key_vk)
            if key not in self._hotkey_callbacks:
                self._hotkey_callbacks[key] = []
            self._hotkey_callbacks[key].append((callback, suppress))
            logger.debug(f"[InputBlocker] Зарегистрирован callback для '{hotkey_str}' (mod=0x{mod_vk:X}, key=0x{key_vk:X})")
        return True

    def unregister_hotkey_callback(self, hotkey_str: str):
        mod_vk, key_vk = _parse_hotkey(hotkey_str)
        if key_vk is None:
            return
        with self._hotkey_lock:
            key = (mod_vk, key_vk)
            self._hotkey_callbacks.pop(key, None)
            logger.debug(f"[InputBlocker] Удалён callback для '{hotkey_str}'")

    def unregister_all_hotkey_callbacks(self):
        with self._hotkey_lock:
            self._hotkey_callbacks.clear()
            logger.debug("[InputBlocker] Все горячие клавиши очищены")

    def _match_hotkey_callbacks(self, vk_code: int):
        """Проверяет vk_code по зарегистрированным callback'ам горячих клавиш.
        Возвращает True, если событие должно быть заблокировано (suppress)."""
        ctrl_held  = self._is_async_pressed(VK_CONTROL)
        shift_held = self._is_async_pressed(VK_SHIFT)
        alt_held   = self._is_async_pressed(VK_MENU)
        mods = 0
        if ctrl_held:  mods |= 1
        if shift_held: mods |= 2
        if alt_held:   mods |= 4

        suppress_all = False
        with self._hotkey_lock:
            for (mod_vk_arr, key_vk), callbacks in list(self._hotkey_callbacks.items()):
                if vk_code != key_vk:
                    continue
                mod = 0
                if mod_vk_arr == VK_CONTROL: mod = 1
                elif mod_vk_arr == VK_SHIFT: mod = 2
                elif mod_vk_arr == VK_MENU:  mod = 4
                if mods != mod and not (mod_vk_arr is None and mods == 0):
                    continue
                for cb, suppress in callbacks:
                    try:
                        cb()
                    except Exception as e:
                        logger.error(f"[InputBlocker] Ошибка в callback горячей клавиши: {e}", exc_info=True)
                    if suppress:
                        suppress_all = True
        return suppress_all


    def _macros(self):
        try:
            be = self._get_backend()
            if be is not None and hasattr(be, '_macros'):
                return be._macros
        except Exception:
            pass
        return []

    def _is_game_window_active(self) -> bool:
        try:
            be = self._get_backend()
            if be is None:
                logger.debug("[_is_game_window_active] be is None, returning False")
                return False
            window_locked = getattr(be, '_window_locked', False)
            if not window_locked:
                logger.debug("[_is_game_window_active] window not locked, returning False")
                return False
            title = getattr(be, '_target_window_title', '')
            if not title:
                logger.debug("[_is_game_window_active] no title set, returning False")
                return False
            hwnd = user32.GetForegroundWindow()
            if not hwnd:
                logger.debug("[_is_game_window_active] no foreground window, returning False")
                return False
            buf = ctypes.create_unicode_buffer(256)
            result = user32.SendMessageTimeoutW(hwnd, WM_GETTEXT, 256, buf, SMTO_ABORTIFHUNG, 500, None)
            foreground_title = buf.value if result else ''
            result = title.strip().lower() in foreground_title.lower()
            logger.debug(f"[_is_game_window_active] title='{title}', fg='{foreground_title}', result={result}")
            return result
        except Exception as e:
            logger.error(f"[_is_game_window_active] Exception: {e}", exc_info=True)
            return False

    def _is_async_pressed(self, vk: int) -> bool:
        return (user32.GetAsyncKeyState(vk) & 0x8000) != 0

    def _match_hotkey(self, vk_code: int) -> object:
        be = self._get_backend()
        if be is None:
            return None
        macros = be._get_macros_copy()
        for m in macros:
            hk = getattr(m, 'hotkey', None)
            if not hk:
                continue
            mod_vk, key_vk = _parse_hotkey(hk)
            if key_vk is None:
                continue
            if vk_code != key_vk:
                continue

            ctrl_held  = self._is_async_pressed(VK_CONTROL)
            shift_held = self._is_async_pressed(VK_SHIFT)
            alt_held   = self._is_async_pressed(VK_MENU)

            if mod_vk == VK_CONTROL and not ctrl_held:
                continue
            if mod_vk == VK_SHIFT  and not shift_held:
                continue
            if mod_vk == VK_MENU   and not alt_held:
                continue
            if mod_vk is None and (ctrl_held or shift_held or alt_held):
                continue

            return m
        return None

    def _match_zone(self, x: int, y: int) -> object:
        be = self._get_backend()
        if be is None:
            return None
        macros = be._get_macros_copy()
        for m in macros:
            zr = getattr(m, 'zone_rect', None)
            if not zr or len(zr) != 4:
                continue
            x1, y1, x2, y2 = zr
            if x1 <= x <= x2 and y1 <= y <= y2:
                return m
        return None


    def _keyboard_hook_callback(self, nCode, wParam, lParam_ptr):
        try:
            try:
                if wParam in (WM_KEYDOWN, WM_SYSKEYDOWN):
                    vk = ctypes.cast(lParam_ptr, ctypes.POINTER(KBDLLHOOKSTRUCT)).contents.vkCode
                    if vk == 0x1B and (user32.GetAsyncKeyState(VK_CONTROL) & 0x8000) and (user32.GetAsyncKeyState(VK_SHIFT) & 0x8000):
                        logger.warning("[InputBlocker]  ЭКСТРЕННАЯ ОСТАНОВКА по Ctrl+Shift+Esc!")
                        self.stop()
                        return user32.CallNextHookEx(self._keyboard_hook, nCode, wParam, lParam_ptr)
                    if vk == 0x7B and (user32.GetAsyncKeyState(VK_CONTROL) & 0x8000) and (user32.GetAsyncKeyState(VK_SHIFT) & 0x8000):
                        logger.warning("[InputBlocker]  ЭКСТРЕННАЯ ОСТАНОВКА по Ctrl+Shift+F12!")
                        self.stop()
                        return user32.CallNextHookEx(self._keyboard_hook, nCode, wParam, lParam_ptr)
            except:
                pass

            if _DEBUG_PASS_THROUGH:
                if nCode == HC_ACTION and wParam in (WM_KEYDOWN, WM_SYSKEYDOWN):
                    try:
                        kb = ctypes.cast(lParam_ptr, ctypes.POINTER(KBDLLHOOKSTRUCT)).contents
                        logger.debug(f"[InputBlocker][DEBUG] vk=0x{kb.vkCode:02X} (pass-through mode)")
                    except:
                        pass
                return user32.CallNextHookEx(self._keyboard_hook, nCode, wParam, lParam_ptr)

            if nCode != HC_ACTION:
                return user32.CallNextHookEx(self._keyboard_hook, nCode, wParam, lParam_ptr)

            kb = ctypes.cast(lParam_ptr, ctypes.POINTER(KBDLLHOOKSTRUCT)).contents
            
            if kb.flags & LLKHF_INJECTED:
                return user32.CallNextHookEx(self._keyboard_hook, nCode, wParam, lParam_ptr)
            
            if wParam in (WM_KEYUP, WM_SYSKEYUP):
                vkCode = kb.vkCode
                if vkCode in self._blocked_keys:
                    self._blocked_keys.remove(vkCode)
                    return 1
                return user32.CallNextHookEx(self._keyboard_hook, nCode, wParam, lParam_ptr)
            
            if wParam not in (WM_KEYDOWN, WM_SYSKEYDOWN):
                return user32.CallNextHookEx(self._keyboard_hook, nCode, wParam, lParam_ptr)

            # Проверка дополнительных горячих клавиш (калибровка кастбара и т.д.)
            # Вне зависимости от активности окна игры и глобальной блокировки
            if self._match_hotkey_callbacks(kb.vkCode):
                logger.debug(f"[InputBlocker]  Клавиша ЗАБЛОКИРОВАНА (callback): vk=0x{kb.vkCode:02X}")
                self._blocked_keys.add(kb.vkCode)
                return 1

            be = self._get_backend()
            if be is None or getattr(be, '_global_stopped', True):
                self.stats['kb_passed'] += 1
                return user32.CallNextHookEx(self._keyboard_hook, nCode, wParam, lParam_ptr)

            if not self._is_game_window_active():
                self.stats['kb_passed'] += 1
                return user32.CallNextHookEx(self._keyboard_hook, nCode, wParam, lParam_ptr)

            macro = self._match_hotkey(kb.vkCode)
            if macro is not None:
                self.stats['kb_blocked'] += 1
                logger.debug(f"[InputBlocker]  Клавиша ЗАБЛОКИРОВАНА: vk=0x{kb.vkCode:02X}  → макрос '{macro.name}'")
                self._blocked_keys.add(kb.vkCode)
                self._trigger_macro_async(macro)
                return 1

            self.stats['kb_passed'] += 1
        except Exception as e:
            logger.error(f"[InputBlocker] Ошибка в keyboard hook: {e}", exc_info=True)
            try:
                return user32.CallNextHookEx(self._keyboard_hook, nCode, wParam, lParam_ptr)
            except:
                return 0
        
        return user32.CallNextHookEx(self._keyboard_hook, nCode, wParam, lParam_ptr)

    def _mouse_hook_callback(self, nCode, wParam, lParam_ptr):
        try:
            if _DEBUG_PASS_THROUGH:
                if nCode == HC_ACTION and wParam in (WM_LBUTTONDOWN, WM_RBUTTONDOWN, WM_LBUTTONUP, WM_RBUTTONUP):
                    try:
                        ms = ctypes.cast(lParam_ptr, ctypes.POINTER(MSLLHOOKSTRUCT)).contents
                        logger.debug(f"[InputBlocker][DEBUG] mouse wParam=0x{wParam:04X} at ({ms.pt.x},{ms.pt.y}) (pass-through mode)")
                    except:
                        pass
                return user32.CallNextHookEx(self._mouse_hook, nCode, wParam, lParam_ptr)

            if nCode != HC_ACTION:
                return user32.CallNextHookEx(self._mouse_hook, nCode, wParam, lParam_ptr)

            ms = ctypes.cast(lParam_ptr, ctypes.POINTER(MSLLHOOKSTRUCT)).contents
            
            if ms.flags & LLMHF_INJECTED:
                return user32.CallNextHookEx(self._mouse_hook, nCode, wParam, lParam_ptr)
            
            if wParam == WM_LBUTTONUP and WM_LBUTTONDOWN in self._blocked_buttons:
                self._blocked_buttons.remove(WM_LBUTTONDOWN)
                return 1
            if wParam == WM_RBUTTONUP and WM_RBUTTONDOWN in self._blocked_buttons:
                self._blocked_buttons.remove(WM_RBUTTONDOWN)
                return 1
            
            if wParam not in (WM_LBUTTONDOWN, WM_RBUTTONDOWN):
                return user32.CallNextHookEx(self._mouse_hook, nCode, wParam, lParam_ptr)

            be = self._get_backend()
            if be is None or getattr(be, '_global_stopped', True):
                self.stats['ms_passed'] += 1
                return user32.CallNextHookEx(self._mouse_hook, nCode, wParam, lParam_ptr)

            if not self._is_game_window_active():
                self.stats['ms_passed'] += 1
                return user32.CallNextHookEx(self._mouse_hook, nCode, wParam, lParam_ptr)

            x, y = ms.pt.x, ms.pt.y

            macro = self._match_zone(x, y)
            if macro is not None:
                self.stats['ms_blocked'] += 1
                logger.debug(f"[InputBlocker]  Клик мыши ЗАБЛОКИРОВАН: ({x},{y})  → макрос '{macro.name}'")
                self._blocked_buttons.add(wParam)
                self._trigger_macro_async(macro)
                return 1

            self.stats['ms_passed'] += 1
        except Exception as e:
            logger.error(f"[InputBlocker] Ошибка в mouse hook: {e}", exc_info=True)
            try:
                return user32.CallNextHookEx(self._mouse_hook, nCode, wParam, lParam_ptr)
            except:
                return 0
        
        return user32.CallNextHookEx(self._mouse_hook, nCode, wParam, lParam_ptr)


    def _trigger_macro_async(self, macro):
        try:
            if hasattr(self, '_executor') and self._executor is not None:
                self._executor.submit(self._do_trigger, macro)
            else:
                self._do_trigger(macro)
        except Exception as e:
            logger.error(f"[InputBlocker] Ошибка запуска макроса: {e}", exc_info=True)

    def _do_trigger(self, macro):
        be = self._get_backend()
        if be is None:
            return
        try:
            if not macro.running:
                if hasattr(be, 'dispatcher') and be.dispatcher:
                    ok = be.dispatcher.request_macro(macro)
                    if ok:
                        logger.info(f"[InputBlocker]  Макрос '{macro.name}' запущен (через хук)")
                    else:
                        logger.debug(f"[InputBlocker]  Макрос '{macro.name}' отклонён диспетчером")
        except Exception as e:
            logger.error(f"[InputBlocker] Ошибка запуска макроса: {e}", exc_info=True)


    def _hook_thread_proc(self):
        logger.info("[InputBlocker] Поток хуков запущен")

        self._thread_id = kernel32.GetCurrentThreadId()

        try:
            hmod = kernel32.GetModuleHandleW(None)

            if not try_register_hook('input_blocker', 'WH_KEYBOARD_LL'):
                logger.error("[InputBlocker]  WH_KEYBOARD_LL уже занят другим модулем", exc_info=True)
                return
            self._kb_proc_ref = KeyboardProc(self._keyboard_hook_callback)
            self._keyboard_hook = user32.SetWindowsHookExW(WH_KEYBOARD_LL, self._kb_proc_ref, hmod, 0)
            if not self._keyboard_hook:
                logger.error("[InputBlocker]  Не удалось установить WH_KEYBOARD_LL. Попробуйте запустить программу от имени администратора (UIPI)", exc_info=True)
                unregister_hook('WH_KEYBOARD_LL')
                return
            logger.info(f"[InputBlocker]  WH_KEYBOARD_LL установлен: 0x{self._keyboard_hook:016X}")

            if not try_register_hook('input_blocker', 'WH_MOUSE_LL'):
                logger.error("[InputBlocker]  WH_MOUSE_LL уже занят другим модулем", exc_info=True)
                self._cleanup_hooks()
                return
            self._mouse_proc_ref = MouseProc(self._mouse_hook_callback)
            self._mouse_hook = user32.SetWindowsHookExW(WH_MOUSE_LL, self._mouse_proc_ref, hmod, 0)
            if not self._mouse_hook:
                logger.error("[InputBlocker]  Не удалось установить WH_MOUSE_LL. Попробуйте запустить программу от имени администратора (UIPI)", exc_info=True)
                self._cleanup_hooks()
                return
            logger.info(f"[InputBlocker]  WH_MOUSE_LL установлен: 0x{self._mouse_hook:016X}")

            msg = MSG()
            logger.info("[InputBlocker] Вход в цикл сообщений PeekMessageW")
            while self._running:
                ret = user32.PeekMessageW(ctypes.byref(msg), None, 0, 0, PM_REMOVE)
                if ret != 0:
                    if msg.message == WM_QUIT:
                        logger.info("[InputBlocker] Получено WM_QUIT, выход из цикла")
                        break
                    user32.TranslateMessage(ctypes.byref(msg))
                    user32.DispatchMessageW(ctypes.byref(msg))
                else:
                    user32.WaitMessage()

        except Exception as e:
            logger.error(f"[InputBlocker] Ошибка в потоке хуков: {e}", exc_info=True)
        finally:
            self._cleanup_hooks()
            logger.info("[InputBlocker] Поток хуков завершён")

    def _cleanup_hooks(self):
        try:
            if self._keyboard_hook:
                user32.UnhookWindowsHookEx(self._keyboard_hook)
                logger.info("[InputBlocker] WH_KEYBOARD_LL снят")
                self._keyboard_hook = None
        except Exception as e:
            logger.error(f"[InputBlocker] Ошибка снятия keyboard hook: {e}", exc_info=True)
        finally:
            unregister_hook('WH_KEYBOARD_LL')

        try:
            if self._mouse_hook:
                user32.UnhookWindowsHookEx(self._mouse_hook)
                logger.info("[InputBlocker] WH_MOUSE_LL снят")
                self._mouse_hook = None
        except Exception as e:
            logger.error(f"[InputBlocker] Ошибка снятия mouse hook: {e}", exc_info=True)
        finally:
            unregister_hook('WH_MOUSE_LL')

        self._kb_proc_ref = None
        self._mouse_proc_ref = None


    def start(self):
        with self._lock:
            if self._running:
                logger.debug("[InputBlocker] Уже запущен")
                return

            if self._executor is None:
                self._executor = concurrent.futures.ThreadPoolExecutor(max_workers=5, thread_name_prefix="InputBlocker")
                logger.info("[InputBlocker] ThreadPoolExecutor пересоздан")

            self._running = True
            self.stats = {k: 0 for k in self.stats}

            self._blocked_keys.clear()
            self._blocked_buttons.clear()

            self._thread = threading.Thread(
                target=self._hook_thread_proc,
                daemon=True,
                name="InputBlocker",
            )
            self._thread.start()

            for _ in range(40):
                if self._keyboard_hook and self._mouse_hook:
                    logger.info("[InputBlocker]  Блокировка ввода АКТИВНА")
                    return
                time.sleep(0.05)

            logger.warning("[InputBlocker]  Хуки могли не успеть встать за 2 сек")

    def stop(self):
        with self._lock:
            if not self._running:
                return

            self._running = False

            if self._thread_id:
                try:
                    user32.PostThreadMessageW(self._thread_id, WM_QUIT, 0, 0)
                except Exception:
                    pass

            if self._thread and self._thread.is_alive():
                self._thread.join(timeout=2.0)
                if self._thread.is_alive():
                    logger.warning("[InputBlocker]  Поток хуков не завершился за 2 сек")
                    self._cleanup_hooks()

            self._blocked_keys.clear()
            self._blocked_buttons.clear()

            if hasattr(self, '_executor'):
                try:
                    self._executor.shutdown(wait=True, timeout=1)
                except Exception:
                    pass
                self._executor = None
                logger.info("[InputBlocker] ThreadPoolExecutor остановлен и очищен")

            self._thread_id = None

            logger.info(f"[InputBlocker]  Блокировка ввода ОСТАНОВЛЕНА. Статистика: {self.stats}")

    @property
    def is_running(self) -> bool:
        return self._running

    def get_stats(self) -> dict:
        return self.stats.copy()



_global_blocker = None


def set_global_blocker(blocker):
    global _global_blocker
    _global_blocker = blocker


def get_global_blocker():
    global _global_blocker
    return _global_blocker


def register_hotkey_callback(hotkey_str, callback, suppress=True):
    """Регистрирует callback на горячую клавишу через глобальный InputBlocker.
    Не создаёт отдельный WH_KEYBOARD_LL хук."""
    blocker = get_global_blocker()
    if blocker is not None:
        return blocker.register_hotkey_callback(hotkey_str, callback, suppress)
    logger.warning(f"[InputBlocker] Глобальный blocker не доступен, hotkey '{hotkey_str}' не зарегистрирован")
    return False


def unregister_hotkey_callback(hotkey_str):
    blocker = get_global_blocker()
    if blocker is not None:
        blocker.unregister_hotkey_callback(hotkey_str)


def unhook_all():
    global _global_blocker
    if _global_blocker is not None:
        try:
            _global_blocker.stop()
        except Exception:
            pass
    try:
        import low_level_hook
        low_level_hook.unhook_all()
    except Exception:
        pass