import threading
import time

from backend.hooks_guard import try_register_hook, unregister_hook
from backend.logger_manager import get_logger

logger = get_logger('low_level_hook')


class MouseHookManager:

    def __init__(self, on_click_callback):
        logger.info("MouseHookManager.__init__: ВЫЗОВ")
        self.on_click_callback = on_click_callback
        self.running = False
        self.thread = None
        self._hook_handle = None
        self._stop_event = threading.Event()
        logger.info("MouseHookManager.__init__: ГОТОВО")

    def _on_mouse_event(self, event):
        if not self.running:
            return

        if not hasattr(event, 'event_type'):
            return

        if event.event_type == 'down' and event.button == 'left':
            logger.info("mouse_hook: ЛКМ нажата!")

            if self.on_click_callback:
                try:
                    result = self.on_click_callback()
                    if result:
                        logger.info("mouse_hook: Клик заблокирован (калибровка)")
                except Exception as e:
                    logger.error(f"mouse_hook: Ошибка в callback: {e}", exc_info=True)

    def start(self):
        logger.info("MouseHookManager.start: ВЫЗОВ")

        self._stop_event.clear()
        if self.thread and self.thread.is_alive():
            logger.warning("MouseHookManager.start: Уже запущен, останавливаем старый поток")
            self.stop()

        self._hook_handle = None
        self.running = True
        self.thread = threading.Thread(target=self._hook_thread, daemon=True)
        self.thread.start()

        logger.info(f"MouseHookManager.start: Поток запущен, alive={self.thread.is_alive()}")

        for i in range(20):
            if self._hook_handle is not None:
                logger.info("MouseHookManager.start: Hook установлен!")
                return
            time.sleep(0.1)

        logger.warning(f"MouseHookManager.start: Hook не подтверждён за 2 сек, но поток alive={self.thread.is_alive()}")

    def _hook_thread(self):
        logger.info("MouseHookManager._hook_thread: ЗАПУСК")

        try:
            import mouse
            try_register_hook('MouseHookManager', 'WH_MOUSE_LL')
            self._hook_handle = mouse.hook(self._on_mouse_event)
            logger.info("MouseHookManager._hook_thread: mouse.hook установлен")

            while self.running:
                if self._stop_event.wait(timeout=0.1):
                    break

            logger.info("MouseHookManager._hook_thread: Выход из цикла")

        except Exception as e:
            logger.error(f"MouseHookManager._hook_thread: ИСКЛЮЧЕНИЕ: {e}", exc_info=True)
        finally:
            self._remove_hook()
            logger.info("MouseHookManager._hook_thread: ЗАВЕРШЕНИЕ")

    def _remove_hook(self):
        try:
            if self._hook_handle is not None:
                import mouse
                mouse.unhook(self._hook_handle)
                logger.info("MouseHookManager._remove_hook: Хук удалён")
                self._hook_handle = None
        except Exception as e:
            logger.error(f"MouseHookManager._remove_hook: Ошибка: {e}", exc_info=True)
        finally:
            unregister_hook('WH_MOUSE_LL')

    def stop(self):
        logger.info("MouseHookManager.stop: ВЫЗОВ")

        self.running = False
        self._stop_event.set()
        self._remove_hook()

        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=2.0)

        logger.info("MouseHookManager.stop: ГОТОВО")

    @property
    def is_active(self) -> bool:
        return self._hook_handle is not None and self.running
