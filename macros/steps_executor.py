import time
from backend.input_system import click_left, click_right, send_key
from backend.logger_manager import get_logger as _get_logger


class StepsExecutor:

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
            _get_logger().error(f"Ошибка выполнения шага {action}={value}: {e}", exc_info=True)
            return False

    def execute_sequence(
        self,
        steps: list,
        check_window=None,
        running_check=None,
        cast_lock_callback=None
    ) -> bool:
        _get_logger().debug(f"Начало выполнения последовательности ({len(steps)} шагов)")
        start_time = time.time()

        for i, step in enumerate(steps):
            if self.stop_event and self.stop_event.is_set():
                _get_logger().debug(f"Последовательность прервана на шаге {i+1}")
                return False

            if running_check and not running_check():
                _get_logger().debug(f"Макрос остановлен на шаге {i+1}")
                return False

            if check_window and not check_window():
                _get_logger().debug(f"Окно неактивно на шаге {i+1}")
                return False

            if not isinstance(step, (list, tuple)) or len(step) < 2:
                _get_logger().error(f"Шаг {i+1} имеет неверный формат: {step}, пропускаем")
                continue
            action = step[0]
            value = step[1] if len(step) > 1 else ""
            delay_ms = step[2] if len(step) > 2 else 0
            if not self.execute_step(action, value, delay_ms, check_window):
                _get_logger().warning(f"Шаг {i+1} не выполнен")
                self.reset()
                return False

            self._current_step = i + 1

            if i == 1 and cast_lock_callback is not None:
                cast_lock_callback()
                _get_logger().debug(" Уведомление о блокировке каста (управляется диспетчером)")

        total_duration = (time.time() - start_time) * 1000
        _get_logger().debug(f"Последовательность выполнена за {total_duration:.2f}мс")
        return True

    def _send_key(self, key: str) -> bool:
        try:
            send_key(key)
            _get_logger().debug(f"Клавиша '{key}' отправлена")
            return True
        except Exception as e:
            _get_logger().error(f"Ошибка отправки клавиши '{key}': {e}", exc_info=True)
            return False

    def _click_left(self) -> None:
        click_left()
        _get_logger().debug("Левый клик мыши")

    def _click_right(self) -> None:
        click_right()
        _get_logger().debug("Правый клик мыши")

    @property
    def current_step(self) -> int:
        return self._current_step

    def reset(self) -> None:
        self._current_step = 0


