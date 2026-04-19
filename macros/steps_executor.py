# -*- coding: utf-8 -*-
"""
macros/steps_executor.py
Исполнитель шагов макроса
Логика выполнения отдельных шагов и последовательностей
"""

import logging
import time
import mouse
import keyboard as kb

# Отложенный импорт логгера для избежания циклической зависимости
_logger = None

def _get_logger():
    global _logger
    if _logger is None:
        from backend.logger_manager import get_logger
        _logger = get_logger('macros')
    return _logger


class StepsExecutor:
    """
    Исполнитель шагов макроса.
    Отвечает за выполнение последовательности действий.
    """

    def __init__(self, stop_event=None):
        self.stop_event = stop_event
        self._current_step = 0

    def execute_step(
        self,
        action: str,
        value: str,
        delay_ms: int,
        check_window=None
    ) -> bool:
        """
        Выполняет один шаг макроса.

        Args:
            action: Тип действия ("key", "left", "right", "wait")
            value: Значение (клавиша или пусто)
            delay_ms: Задержка после действия (мс)
            check_window: Функция проверки активного окна (опционально)

        Returns:
            True если шаг выполнен успешно
        """
        # Проверка окна
        if check_window and not check_window():
            _get_logger().debug("Окно неактивно, прерывание шага")
            return False

        _get_logger().debug(f"Шаг: действие='{action}', значение='{value}', задержка={delay_ms}мс")

        try:
            if action == "key":
                self._send_key(value)
            elif action == "left":
                self._click_left()
            elif action == "right":
                self._click_right()
            elif action == "wait":
                _get_logger().debug(f"Пауза {delay_ms}мс")
            
            if delay_ms > 0:
                time.sleep(delay_ms / 1000.0)
            
            return True

        except Exception as e:
            _get_logger().error(f"Ошибка выполнения шага {action}={value}: {e}")
            return False

    def execute_sequence(
        self,
        steps: list,
        check_window=None,
        running_check=None
    ) -> bool:
        """
        Выполняет последовательность шагов.

        Args:
            steps: Список шагов [(action, value, delay_ms), ...]
            check_window: Функция проверки активного окна
            running_check: Функция проверки статуса запуска

        Returns:
            True если вся последовательность выполнена
        """
        _get_logger().debug(f"Начало выполнения последовательности ({len(steps)} шагов)")
        start_time = time.time()

        for i, step in enumerate(steps):
            # Проверка остановки
            if self.stop_event and self.stop_event.is_set():
                _get_logger().debug(f"Последовательность прервана на шаге {i+1}")
                return False

            if running_check and not running_check():
                _get_logger().debug(f"Макрос остановлен на шаге {i+1}")
                return False

            # Проверка окна
            if check_window and not check_window():
                _get_logger().debug(f"Окно неактивно на шаге {i+1}")
                return False

            # Выполнение шага
            action, value, delay_ms = step
            if not self.execute_step(action, value, delay_ms, check_window):
                _get_logger().warning(f"Шаг {i+1} не выполнен")
                return False

            self._current_step = i + 1

        total_duration = (time.time() - start_time) * 1000
        _get_logger().debug(f"Последовательность выполнена за {total_duration:.2f}мс")
        return True

    def _send_key(self, key: str) -> bool:
        """Отправляет клавишу"""
        try:
            kb.send(key)
            _get_logger().debug(f"Клавиша '{key}' отправлена")
            return True
        except Exception as e:
            _get_logger().error(f"Ошибка отправки клавиши '{key}': {e}")
            return False

    def _click_left(self) -> None:
        """Выполняет левый клик"""
        mouse.click(button="left")
        _get_logger().debug("Левый клик мыши")

    def _click_right(self) -> None:
        """Выполняет правый клик"""
        mouse.click(button="right")
        _get_logger().debug("Правый клик мыши")

    @property
    def current_step(self) -> int:
        """Возвращает номер текущего шага"""
        return self._current_step

    def reset(self) -> None:
        """Сбрасывает счётчик шагов"""
        self._current_step = 0


# ========== Устаревшая функция для совместимости ==========

def send_key(key: str) -> bool:
    """
    Устаревшая функция отправки клавиш.
    Для совместимости со старым кодом.
    """
    _get_logger().debug(f"send_key: попытка отправить клавишу '{key}'")
    try:
        kb.send(key)
        _get_logger().debug(f"send_key: клавиша '{key}' отправлена")
        return True
    except Exception as e:
        _get_logger().error(f"send_key: ошибка: {e}")
        return False
