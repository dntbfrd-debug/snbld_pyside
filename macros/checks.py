# -*- coding: utf-8 -*-
"""
macros/checks.py
Проверки для макросов
Окно, кулдаун, дистанция, каст
"""

import logging
import time
import threading
import win32gui
from typing import Optional, Callable, Any

# Отложенный импорт логгера для избежания циклической зависимости
_logger = None

def _get_logger():
    global _logger
    if _logger is None:
        from backend.logger_manager import get_logger
        _logger = get_logger('macros')
    return _logger


class WindowChecker:
    """Проверка активного окна"""

    def __init__(self, window_manager: Any = None):
        self._window_manager = window_manager

    def check(self) -> bool:
        """
        Проверяет, активно ли целевое окно.

        Returns:
            True если окно активно или проверка отключена
        """
        if self._window_manager:
            return self._window_manager.check_window()

        # Fallback логика
        if not hasattr(self, '_window_locked') or not self._window_locked:
            return True

        target = getattr(self, '_target_window_title', '').strip().lower()
        if not target:
            return True

        try:
            hwnd = win32gui.GetForegroundWindow()
            active_title = win32gui.GetWindowText(hwnd).lower()
            return target in active_title
        except Exception as e:
            _get_logger().error(f"Ошибка проверки окна: {e}")
            return True


class CooldownChecker:
    """Проверка кулдауна"""

    def __init__(self):
        self._last_used: float = 0
        self._lock = threading.Lock()

    def can_use(self, cooldown: float, margin: float = 0.05) -> bool:
        """
        Проверяет, готов ли скилл к использованию.

        Args:
            cooldown: Базовый кулдаун (сек)
            margin: Запас (сек)

        Returns:
            True если кулдаун готов
        """
        if cooldown <= 0:
            return True

        with self._lock:
            now = time.time()
            effective_cooldown = cooldown + margin
            diff = now - self._last_used

            if diff < effective_cooldown:
                remaining = effective_cooldown - diff
                _get_logger().debug(f"Кулдаун: осталось {remaining:.1f}с")
                return False

            return True

    def reset(self) -> None:
        """Сбрасывает кулдаун"""
        with self._lock:
            self._last_used = time.time()
            _get_logger().debug("Кулдаун сброшен")

    def set_last_used(self, timestamp: Optional[float] = None) -> None:
        """Устанавливает время последнего использования"""
        with self._lock:
            self._last_used = timestamp or time.time()

    def get_remaining(self, cooldown: float, margin: float = 0.05) -> float:
        """Возвращает оставшееся время кулдауна"""
        with self._lock:
            now = time.time()
            effective_cooldown = cooldown + margin
            diff = now - self._last_used
            return max(0, effective_cooldown - diff)


class DistanceChecker:
    """Проверка дистанции до цели"""

    def __init__(self, get_distance_func: Callable[[], Optional[float]]):
        """
        Args:
            get_distance_func: Функция получения текущей дистанции
        """
        self._get_distance = get_distance_func

    def is_in_range(
        self,
        target_range: float,
        tolerance: float = 1.0
    ) -> bool:
        """
        Проверяет, находится ли цель в пределах дальности.

        Args:
            target_range: Дальность скилла (м)
            tolerance: Допуск (м)

        Returns:
            True если цель в пределах дальности
        """
        if target_range <= 0:
            return True

        current = self._get_distance()
        if current is None or current == 0:
            _get_logger().debug("Дистанция не определена")
            return False

        # Целевая дистанция с допуском
        target_dist = max(0, target_range - 0.2)
        in_range = current <= target_dist + tolerance

        if not in_range:
            _get_logger().debug(f"Цель слишком далеко: {current:.1f}м > {target_dist + tolerance:.1f}м")

        return in_range

    def needs_approach(
        self,
        target_range: float,
        tolerance: float = 1.0
    ) -> bool:
        """
        Проверяет, требуется ли подбег к цели.

        Returns:
            True если нужно подбежать
        """
        return not self.is_in_range(target_range, tolerance)

    def get_distance(self) -> Optional[float]:
        """Возвращает текущую дистанцию"""
        return self._get_distance()


class CastLockChecker:
    """Проверка блокировки каста"""

    def __init__(self, app_reference: Any = None):
        """
        Args:
            app_reference: Ссылка на приложение с методами is_cast_locked, lock_cast
        """
        self._app = app_reference

    def is_locked(self) -> bool:
        """Проверяет, заблокирован ли каст"""
        if self._app and hasattr(self._app, 'is_cast_locked'):
            return self._app.is_cast_locked()
        return False

    def lock(self, duration: float) -> None:
        """
        Блокирует каст на указанное время.

        Args:
            duration: Длительность блокировки (сек)
        """
        if self._app and hasattr(self._app, 'lock_cast'):
            self._app.lock_cast(duration)
            _get_logger().debug(f"Каст заблокирован на {duration}с")

    def get_remaining_lock(self) -> float:
        """Возвращает оставшееся время блокировки каста"""
        if self._app and hasattr(self._app, 'cast_lock_until'):
            return max(0, self._app.cast_lock_until - time.time())
        return 0


class MovementDelayChecker:
    """Проверка задержки после движения"""

    def __init__(self, movement_monitor: Any = None):
        """
        Args:
            movement_monitor: Монитор движения с методом get_movement_delay
        """
        self._movement_monitor = movement_monitor

    def get_delay(self) -> float:
        """
        Возвращает время с момента последней остановки движения.

        Returns:
            Время в секундах
        """
        if self._movement_monitor:
            return self._movement_monitor.get_movement_delay()
        return 0.0

    def needs_wait(
        self,
        required_delay_ms: int
    ) -> bool:
        """
        Проверяет, требуется ли ожидание после движения.

        Args:
            required_delay_ms: Требуемая задержка (мс)

        Returns:
            True если нужно ждать
        """
        if required_delay_ms <= 0:
            return False

        current_delay = self.get_delay()
        required_delay_s = required_delay_ms / 1000.0

        return current_delay < required_delay_s

    def wait_if_needed(
        self,
        required_delay_ms: int,
        stop_event=None
    ) -> bool:
        """
        Ждёт если требуется задержка после движения.

        Args:
            required_delay_ms: Требуемая задержка (мс)
            stop_event: Событие остановки

        Returns:
            True если ожидание завершено успешно
        """
        if not self.needs_wait(required_delay_ms):
            return True

        current_delay = self.get_delay()
        required_delay_s = required_delay_ms / 1000.0
        sleep_time = required_delay_s - current_delay

        _get_logger().debug(f"Ожидание инерции движения: {sleep_time*1000:.0f}мс")

        start = time.time()
        while time.time() - start < sleep_time:
            if stop_event and stop_event.is_set():
                return False
            time.sleep(0.01)

        return True
