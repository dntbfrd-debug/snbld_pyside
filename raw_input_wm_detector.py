import threading
import time
import ctypes
from typing import Callable, Optional
from backend.logger_manager import get_logger

logger = get_logger('macros')

class RawInputWMDetector:
    def __init__(self, target_window_title: str = ""):
        self._target_window_title = (target_window_title or "").strip().lower()
        self._stop_event = threading.Event()
        self._thread = None
        self._cb: Optional[Callable[[int, int], None]] = None
        self._running = False
        self._debounce = 0.05
        self._last_click = 0.0
        self._poll_interval = 0.02
        
        try:
            self._user32 = ctypes.windll.user32
            self._has_user32 = True
        except (AttributeError, OSError):
            self._user32 = None
            self._has_user32 = False
            logger.warning("[RAWWM] USER32 недоступен, монитор кликов будет использовать fallback")

    def set_target_window(self, title: str) -> None:
        self._target_window_title = (title or "").strip().lower()

    def set_click_callback(self, cb: Callable[[int, int], None]) -> None:
        self._cb = cb

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            logger.warning("[RAWWM] Поток уже запущен")
            return
        if not self._has_user32:
            logger.error("[RAWWM] Не могу запустить - USER32 недоступен")
            return
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()
        self._running = True
        logger.info("[RAWWM] WM_INPUT detector (polling) started")

    def stop(self) -> None:
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=2.0)
        self._running = False
        logger.info("[RAWWM] WM_INPUT detector (polling) stopped")

    def isRunning(self) -> bool:
        return self._running

    def _run(self) -> None:
        while not self._stop_event.is_set():
            try:
                if not self._has_user32 or not self._user32:
                    time.sleep(0.1)
                    continue
                    
                try:
                    pressed = bool(self._user32.GetAsyncKeyState(0x01) & 0x8000)
                except Exception:
                    pressed = False
                    
                if pressed:
                    now = time.time()
                    if now - self._last_click > self._debounce:
                        try:
                            pos = ctypes.wintypes.POINT()
                            self._user32.GetCursorPos(ctypes.byref(pos))
                            x, y = pos.x, pos.y
                        except Exception as e:
                            logger.debug(f"[RAWWM] Ошибка GetCursorPos: {e}")
                            x, y = 0, 0
                        
                        skip_emit = False
                        if self._target_window_title:
                            try:
                                hwnd = self._user32.GetForegroundWindow()
                                if hwnd:
                                    length = self._user32.GetWindowTextLengthW(hwnd)
                                    if length > 0:
                                        buf = ctypes.create_unicode_buffer(length + 1)
                                        self._user32.GetWindowTextW(hwnd, buf, length + 1)
                                        active_title = buf.value.lower()
                                        if self._target_window_title not in active_title:
                                            self._last_click = now
                                            skip_emit = True
                            except Exception:
                                pass
                        
                        if not skip_emit:
                            if self._cb:
                                try:
                                    self._cb(int(x), int(y))
                                except Exception as e:
                                    logger.error(f"[RAWWM] Ошибка в callback: {e}")
                            self._last_click = now
            except Exception as e:
                logger.error(f"[RAWWM] Ошибка в цикле мониторинга: {e}")
            
            time.sleep(self._poll_interval)