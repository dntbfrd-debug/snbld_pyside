# -*- coding: utf-8 -*-
"""
low_level_hook.py - ВЕРСИЯ 5 (НА БАЗЕ mouse.hook)
Использует библиотеку mouse вместо SetWindowsHookExW — работает стабильнее.
"""

import threading
import logging
import time

logger = logging.getLogger(__name__)


class MouseHookManager:
    """
    Менеджер mouse hook — использует mouse.hook() вместо WinAPI SetWindowsHookExW.
    Работает стабильнее, не зависит от hInstance и прав администратора.
    """

    def __init__(self, on_click_callback):
        logger.info("MouseHookManager.__init__: ВЫЗОВ")
        self.on_click_callback = on_click_callback
        self.running = False
        self.thread = None
        self._hook_handle = None
        self._lock = threading.Lock()
        logger.info("MouseHookManager.__init__: ГОТОВО")

    def _on_mouse_event(self, event):
        """Обработчик событий мыши"""
        if not self.running:
            return

        # Проверяем наличие атрибута event_type
        if not hasattr(event, 'event_type'):
            return

        # Левый клик вниз
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
        """Запускает перехват мыши"""
        logger.info("MouseHookManager.start: ВЫЗОВ")

        with self._lock:
            # ✅ Исправление утечки хэндлов: сначала полностью останавливаем старый поток если существует
            if self.thread and self.thread.is_alive():
                logger.warning("MouseHookManager.start: Уже запущен, останавливаем старый поток")
                self.running = False
                try:
                    self._remove_hook()
                    self.thread.join(timeout=2.0)
                except Exception as e:
                    logger.error(f"MouseHookManager.start: Ошибка остановки старого потока: {e}")
            
            # Сброс состояния
            self._hook_handle = None
            self.running = True

            # Создаём поток с mouse.hook ✅ daemon=True чтобы поток не блокировал закрытие приложения
            self.thread = threading.Thread(target=self._hook_thread, daemon=True)
            self.thread.start()

            logger.info(f"MouseHookManager.start: Поток запущен, alive={self.thread.is_alive()}")

        # Ждём пока hook установится
        for i in range(20):
            if self._hook_handle is not None:
                logger.info("MouseHookManager.start: Hook установлен!")
                return
            time.sleep(0.1)

        logger.warning(f"MouseHookManager.start: Hook не подтверждён за 2 сек, но поток alive={self.thread.is_alive()}")

    def _hook_thread(self):
        """Поток для mouse.hook"""
        logger.info("MouseHookManager._hook_thread: ЗАПУСК")

        try:
            import mouse
            # mouse.hook() блокирует поток и вызывает callback при каждом событии
            self._hook_handle = mouse.hook(self._on_mouse_event)
            logger.info("MouseHookManager._hook_thread: mouse.hook установлен")

            # Ждём сигнала остановки
            while self.running:
                locked = False
                try:
                    locked = self._lock.acquire(timeout=0.1)
                    if not self.running:
                        break
                finally:
                    if locked:
                        self._lock.release()

            logger.info("MouseHookManager._hook_thread: Выход из цикла")

        except Exception as e:
            logger.error(f"MouseHookManager._hook_thread: ИСКЛЮЧЕНИЕ: {e}", exc_info=True)
        finally:
            self._remove_hook()
            logger.info("MouseHookManager._hook_thread: ЗАВЕРШЕНИЕ")

    def _remove_hook(self):
        """Надёжное удаление хука"""
        try:
            if self._hook_handle is not None:
                import mouse
                mouse.unhook(self._hook_handle)
                logger.info("MouseHookManager._remove_hook: Хук удалён")
                self._hook_handle = None
        except Exception as e:
            logger.error(f"MouseHookManager._remove_hook: Ошибка: {e}")

    def stop(self):
        """Останавливает перехват"""
        logger.info("MouseHookManager.stop: ВЫЗОВ")

        self.running = False
        self._remove_hook()

        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=2.0)

        logger.info("MouseHookManager.stop: ГОТОВО")

    @property
    def is_active(self) -> bool:
        """Проверяет активен ли hook"""
        return self._hook_handle is not None and self.running
