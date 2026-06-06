import ctypes
import ctypes.wintypes
import threading
import time
from backend.logger_manager import get_logger
import concurrent.futures

from backend.hooks_guard import try_register_hook, unregister_hook
from constants import parse_hotkey as _constants_parse_hotkey

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


_MODIFIER_MAP = {
    'ctrl': VK_CONTROL, 'control': VK_CONTROL,
    'shift': VK_SHIFT,
    'alt': VK_MENU,
}


def _parse_hotkey(hotkey_str: str):
    if not hotkey_str:
        return None, None
    vk, mods = _constants_parse_hotkey(hotkey_str)
    if vk == 0:
        return None, None
    return mods, vk



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
        self._emergency_stop_requested = False

        # Регистрация дополнительных callback'ов горячих клавиш
        self._hotkey_callbacks = {}
        self._hotkey_lock = threading.Lock()

        # Регистрация callback'ов кликов мыши
        # (чтобы MouseDetector/MouseClickMonitor не ставил свой WH_MOUSE_LL)
        self._mouse_click_callbacks = []
        self._mouse_click_lock = threading.Lock()

        # Таймстемпы для защиты от залипания кнопок
        self._blocked_keys_time: dict = {}
        self._blocked_buttons_time: dict = {}
        self._BUTTON_STUCK_TIMEOUT = 5.0

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

    def register_mouse_click_callback(self, callback):
        """Регистрирует callback на клик мыши, вызывается из _mouse_hook_callback
        для всех НЕзаблокированных кликов. Используется MouseDetector
        вместо установки собственного WH_MOUSE_LL."""
        with self._mouse_click_lock:
            self._mouse_click_callbacks.append(callback)

    def unregister_mouse_click_callback(self, callback):
        with self._mouse_click_lock:
            try:
                self._mouse_click_callbacks.remove(callback)
            except ValueError:
                pass

    def _notify_mouse_click_callbacks(self, x, y, button):
        with self._mouse_click_lock:
            for cb in self._mouse_click_callbacks:
                try:
                    cb(x, y, button)
                except Exception as e:
                    logger.error(f"[InputBlocker] Ошибка в mouse click callback: {e}", exc_info=True)

    def _cleanup_stuck_buttons(self):
        now = time.time()
        stale_keys = [vk for vk, t in list(self._blocked_keys_time.items())
                      if now - t > self._BUTTON_STUCK_TIMEOUT]
        for vk in stale_keys:
            self._blocked_keys.discard(vk)
            self._blocked_keys_time.pop(vk, None)
            logger.warning(f"[InputBlocker] Принудительная очистка залипшей клавиши: vk=0x{vk:02X}")

        stale_buttons = [b for b, t in list(self._blocked_buttons_time.items())
                         if now - t > self._BUTTON_STUCK_TIMEOUT]
        for b in stale_buttons:
            self._blocked_buttons.discard(b)
            self._blocked_buttons_time.pop(b, None)
            logger.warning(f"[InputBlocker] Принудительная очистка залипшей кнопки: wParam=0x{b:04X}")

    def _match_hotkey_callbacks(self, vk_code: int):
        """Проверяет vk_code по зарегистрированным callback'ам горячих клавиш.
        Возвращает True, если событие должно быть заблокировано (suppress)."""
        ctrl_held  = self._is_async_pressed(VK_CONTROL)
        shift_held = self._is_async_pressed(VK_SHIFT)
        alt_held   = self._is_async_pressed(VK_MENU)
        mods = 0
        if ctrl_held:  mods |= 0x0002
        if shift_held: mods |= 0x0004
        if alt_held:   mods |= 0x0001

        suppress_all = False
        with self._hotkey_lock:
            for (mod_mask, key_vk), callbacks in list(self._hotkey_callbacks.items()):
                if vk_code != key_vk:
                    continue
                if mods != (mod_mask or 0) and not (mod_mask == 0 and mods == 0):
                    continue
                for cb, suppress in callbacks:
                    try:
                        cb(None)
                    except Exception as e:
                        logger.error(f"[InputBlocker] Ошибка в callback горячей клавиши: {e}", exc_info=True)
                    if suppress:
                        suppress_all = True
        return suppress_all


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
                        logger.warning("[InputBlocker] ЭКСТРЕННАЯ ОСТАНОВКА по Ctrl+Shift+Esc!")
                        self._emergency_stop_requested = True
                        if self._thread_id:
                            user32.PostThreadMessageW(self._thread_id, WM_QUIT, 0, 0)
                        return 1
                    if vk == 0x7B and (user32.GetAsyncKeyState(VK_CONTROL) & 0x8000) and (user32.GetAsyncKeyState(VK_SHIFT) & 0x8000):
                        logger.warning("[InputBlocker] ЭКСТРЕННАЯ ОСТАНОВКА по Ctrl+Shift+F12!")
                        self._emergency_stop_requested = True
                        if self._thread_id:
                            user32.PostThreadMessageW(self._thread_id, WM_QUIT, 0, 0)
                        return 1
            except:
                pass

            if _DEBUG_PASS_THROUGH:
                if nCode == HC_ACTION and wParam in (WM_KEYDOWN, WM_SYSKEYDOWN):
                    try:
                        kb = ctypes.cast(lParam_ptr, ctypes.POINTER(KBDLLHOOKSTRUCT)).contents
                        logger.debug(f"[InputBlocker][DEBUG] vk=0x{kb.vkCode:02X} (pass-through mode)")
                    except:
                        pass
                hook_handle = self._keyboard_hook
                return user32.CallNextHookEx(hook_handle, nCode, wParam, lParam_ptr)

            if nCode != HC_ACTION:
                hook_handle = self._keyboard_hook
                return user32.CallNextHookEx(hook_handle, nCode, wParam, lParam_ptr)

            kb = ctypes.cast(lParam_ptr, ctypes.POINTER(KBDLLHOOKSTRUCT)).contents
            
            if kb.flags & LLKHF_INJECTED:
                hook_handle = self._keyboard_hook
                return user32.CallNextHookEx(hook_handle, nCode, wParam, lParam_ptr)
            
            if wParam in (WM_KEYUP, WM_SYSKEYUP):
                vkCode = kb.vkCode
                if vkCode in self._blocked_keys:
                    self._blocked_keys.discard(vkCode)
                    self._blocked_keys_time.pop(vkCode, None)
                    return 1
                hook_handle = self._keyboard_hook
                return user32.CallNextHookEx(hook_handle, nCode, wParam, lParam_ptr)
            
            if wParam not in (WM_KEYDOWN, WM_SYSKEYDOWN):
                hook_handle = self._keyboard_hook
                return user32.CallNextHookEx(hook_handle, nCode, wParam, lParam_ptr)

            # Проверка дополнительных горячих клавиш (калибровка кастбара и т.д.)
            # Вне зависимости от активности окна игры и глобальной блокировки
            if self._match_hotkey_callbacks(kb.vkCode):
                logger.debug(f"[InputBlocker]  Клавиша ЗАБЛОКИРОВАНА (callback): vk=0x{kb.vkCode:02X}")
                self._blocked_keys.add(kb.vkCode)
                self._blocked_keys_time[kb.vkCode] = time.time()
                return 1

            be = self._get_backend()
            if be is None or getattr(be, '_global_stopped', True):
                self.stats['kb_passed'] += 1
                hook_handle = self._keyboard_hook
                return user32.CallNextHookEx(hook_handle, nCode, wParam, lParam_ptr)

            if not self._is_game_window_active():
                self.stats['kb_passed'] += 1
                hook_handle = self._keyboard_hook
                return user32.CallNextHookEx(hook_handle, nCode, wParam, lParam_ptr)

            self.stats['kb_passed'] += 1
        except Exception as e:
            logger.error(f"[InputBlocker] Ошибка в keyboard hook: {e}", exc_info=True)
            try:
                hook_handle = self._keyboard_hook
                return user32.CallNextHookEx(hook_handle, nCode, wParam, lParam_ptr)
            except:
                return 0
        
        hook_handle = self._keyboard_hook
        return user32.CallNextHookEx(hook_handle, nCode, wParam, lParam_ptr)

    def _mouse_hook_callback(self, nCode, wParam, lParam_ptr):
        try:
            if _DEBUG_PASS_THROUGH:
                if nCode == HC_ACTION and wParam in (WM_LBUTTONDOWN, WM_RBUTTONDOWN, WM_LBUTTONUP, WM_RBUTTONUP):
                    try:
                        ms = ctypes.cast(lParam_ptr, ctypes.POINTER(MSLLHOOKSTRUCT)).contents
                        logger.debug(f"[InputBlocker][DEBUG] mouse wParam=0x{wParam:04X} at ({ms.pt.x},{ms.pt.y}) (pass-through mode)")
                    except:
                        pass
                hook_handle = self._mouse_hook
                return user32.CallNextHookEx(hook_handle, nCode, wParam, lParam_ptr)

            if nCode != HC_ACTION:
                hook_handle = self._mouse_hook
                return user32.CallNextHookEx(hook_handle, nCode, wParam, lParam_ptr)

            ms = ctypes.cast(lParam_ptr, ctypes.POINTER(MSLLHOOKSTRUCT)).contents
            
            if ms.flags & LLMHF_INJECTED:
                hook_handle = self._mouse_hook
                return user32.CallNextHookEx(hook_handle, nCode, wParam, lParam_ptr)
            
            if wParam == WM_LBUTTONUP and WM_LBUTTONDOWN in self._blocked_buttons:
                self._blocked_buttons.discard(WM_LBUTTONDOWN)
                self._blocked_buttons_time.pop(WM_LBUTTONDOWN, None)
                return 1
            if wParam == WM_RBUTTONUP and WM_RBUTTONDOWN in self._blocked_buttons:
                self._blocked_buttons.discard(WM_RBUTTONDOWN)
                self._blocked_buttons_time.pop(WM_RBUTTONDOWN, None)
                return 1
            
            if wParam not in (WM_LBUTTONDOWN, WM_RBUTTONDOWN):
                hook_handle = self._mouse_hook
                return user32.CallNextHookEx(hook_handle, nCode, wParam, lParam_ptr)

            be = self._get_backend()
            if be is None or getattr(be, '_global_stopped', True):
                self.stats['ms_passed'] += 1
                hook_handle = self._mouse_hook
                return user32.CallNextHookEx(hook_handle, nCode, wParam, lParam_ptr)

            if not self._is_game_window_active():
                self.stats['ms_passed'] += 1
                hook_handle = self._mouse_hook
                return user32.CallNextHookEx(hook_handle, nCode, wParam, lParam_ptr)

            x, y = ms.pt.x, ms.pt.y

            macro = self._match_zone(x, y)
            if macro is not None:
                self.stats['ms_blocked'] += 1
                logger.debug(f"[InputBlocker]  Клик мыши ЗАБЛОКИРОВАН: ({x},{y})  → макрос '{macro.name}'")
                self._blocked_buttons.add(wParam)
                self._blocked_buttons_time[wParam] = time.time()
                self._executor.submit(macro.on_mouse_click, x, y)
                return 1

            # Клик не заблокирован — уведомляем колбэки (MouseClickMonitor и др.)
            self._executor.submit(self._notify_mouse_click_callbacks, x, y, wParam)

            self.stats['ms_passed'] += 1
        except Exception as e:
            logger.error(f"[InputBlocker] Ошибка в mouse hook: {e}", exc_info=True)
            try:
                hook_handle = self._mouse_hook
                return user32.CallNextHookEx(hook_handle, nCode, wParam, lParam_ptr)
            except:
                return 0
        
        hook_handle = self._mouse_hook
        return user32.CallNextHookEx(hook_handle, nCode, wParam, lParam_ptr)


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
            cleanup_counter = 0
            logger.info("[InputBlocker] Вход в цикл сообщений GetMessageW")
            while self._running:
                ret = user32.GetMessageW(ctypes.byref(msg), None, 0, 0)
                if ret == 0:
                    logger.info("[InputBlocker] Получено WM_QUIT, выход из цикла")
                    break
                user32.TranslateMessage(ctypes.byref(msg))
                user32.DispatchMessageW(ctypes.byref(msg))

                cleanup_counter += 1
                if cleanup_counter >= 100:
                    cleanup_counter = 0
                    self._cleanup_stuck_buttons()

        except Exception as e:
            logger.error(f"[InputBlocker] Ошибка в потоке хуков: {e}", exc_info=True)
        finally:
            self._cleanup_hooks()
            self._emergency_stop_requested = False
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

            self._running = True
            self.stats = {k: 0 for k in self.stats}

            self._blocked_keys.clear()
            self._blocked_keys_time.clear()
            self._blocked_buttons.clear()
            self._blocked_buttons_time.clear()

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
            self._blocked_keys_time.clear()
            self._blocked_buttons.clear()
            self._blocked_buttons_time.clear()

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