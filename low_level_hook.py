import ctypes
import threading
import time

from backend.hooks_guard import try_register_hook, unregister_hook
from backend.logger_manager import get_logger

logger = get_logger('low_level_hook')


_VK_LBUTTON = 0x01


class MouseHookManager:

    def __init__(self, on_click_callback):
        logger.info("MouseHookManager.__init__: ВЫЗОВ")
        self.on_click_callback = on_click_callback
        self.running = False
        self.thread = None
        self._stop_event = threading.Event()
        self._prev_state = False
        logger.info("MouseHookManager.__init__: ГОТОВО")

    def _poll_once(self):
        state = ctypes.windll.user32.GetAsyncKeyState(_VK_LBUTTON)
        pressed = (state & 0x8000) != 0

        if pressed and not self._prev_state:
            logger.info("mouse_poll: ЛКМ нажата!")
            if self.on_click_callback:
                try:
                    self.on_click_callback()
                except Exception as e:
                    logger.error(f"mouse_poll: Ошибка в callback: {e}", exc_info=True)
        self._prev_state = pressed

    def start(self):
        logger.info("MouseHookManager.start: ВЫЗОВ")

        self._stop_event.clear()
        if self.thread and self.thread.is_alive():
            logger.warning("MouseHookManager.start: Уже запущен, останавливаем старый поток")
            self.stop()

        self.running = True
        self.thread = threading.Thread(target=self._hook_thread, daemon=True)
        self.thread.start()

        logger.info(f"MouseHookManager.start: Поток запущен, alive={self.thread.is_alive()}")

    def _hook_thread(self):
        logger.info("MouseHookManager._hook_thread: ЗАПУСК")

        try:
            try_register_hook('MouseHookManager', 'WH_MOUSE_POLL')

            while self.running:
                self._poll_once()
                if self._stop_event.wait(timeout=0.05):
                    break

            logger.info("MouseHookManager._hook_thread: Выход из цикла")

        except Exception as e:
            logger.error(f"MouseHookManager._hook_thread: ИСКЛЮЧЕНИЕ: {e}", exc_info=True)
        finally:
            unregister_hook('WH_MOUSE_POLL')
            logger.info("MouseHookManager._hook_thread: ЗАВЕРШЕНИЕ")

    def stop(self):
        logger.info("MouseHookManager.stop: ВЫЗОВ")

        self.running = False
        self._stop_event.set()

        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=2.0)

        logger.info("MouseHookManager.stop: ГОТОВО")

    @property
    def is_active(self) -> bool:
        return self.running
