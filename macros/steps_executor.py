import time
from backend.input_system import click_left, click_right, send_key
from backend.logger_manager import get_logger as _get_logger

_log = _get_logger('steps_executor')


VALID_ACTIONS = ("key", "left", "right", "wait", "repeat")
MAX_DELAY_MS = 60000  # 60 секунд — потолок для одного шага, чтобы избежать "зависших" макросов


def _validate_step(step) -> bool:
    if not isinstance(step, (list, tuple)):
        _log.error(f"Шаг имеет неверный тип ({type(step).__name__}): {step!r}")
        return False
    if len(step) < 2:
        _log.error(f"Шаг слишком короткий: {step!r}")
        return False
    action = step[0]
    if action not in VALID_ACTIONS:
        _log.error(f"Неизвестное действие: {action!r} (допустимо: {VALID_ACTIONS})")
        return False
    if action == "key":
        value = step[1]
        if not isinstance(value, str) or not value.strip():
            _log.error(f"Действие 'key' требует непустую строку, получено: {value!r}")
            return False
    if action == "repeat":
        if len(step) < 3:
            _log.error(f"Действие 'repeat' требует аргумент repeat_count, получено: {step!r}")
            return False
        repeat_count = step[1]
        if not isinstance(repeat_count, int) or repeat_count < 1:
            _log.error(f"repeat_count должен быть int >= 1, получено: {repeat_count!r}")
            return False
        return True
    if len(step) >= 3:
        delay_ms = step[2]
        if not isinstance(delay_ms, (int, float)) or delay_ms < 0:
            _log.error(f"Задержка должна быть числом >= 0, получено: {delay_ms!r}")
            return False
        if delay_ms > MAX_DELAY_MS:
            _log.error(f"Задержка слишком большая ({delay_ms}мс), максимум {MAX_DELAY_MS}мс")
            return False
    return True


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
            _log.debug("Окно неактивно, прерывание шага")
            return False

        try:
            if action == "key":
                self._send_key(value)
            elif action == "left":
                self._click_left()
            elif action == "right":
                self._click_right()
            elif action == "wait":
                _log.debug(f"Пауза {delay_ms}мс")

            if delay_ms > 0:
                if self.stop_event:
                    self.stop_event.wait(delay_ms / 1000.0)
                else:
                    time.sleep(delay_ms / 1000.0)

            return True

        except Exception as e:
            _log.error(f"Ошибка выполнения шага {action}={value}: {e}", exc_info=True)
            return False

    def execute_sequence(
        self,
        steps: list,
        check_window=None,
        running_check=None,
        cast_lock_callback=None
    ) -> bool:
        _log.debug(f"Начало выполнения последовательности ({len(steps)} шагов)")
        start_time = time.time()

        for i, step in enumerate(steps):
            if self.stop_event and self.stop_event.is_set():
                _log.debug(f"Последовательность прервана на шаге {i+1}")
                return False

            if running_check and not running_check():
                _log.debug(f"Макрос остановлен на шаге {i+1}")
                return False

            if check_window and not check_window():
                _log.debug(f"Окно неактивно на шаге {i+1}")
                return False

            if not isinstance(step, (list, tuple)) or len(step) < 2:
                _log.error(f"Шаг {i+1} имеет неверный формат: {step}, пропускаем")
                continue
            if not _validate_step(step):
                _log.error(f"Шаг {i+1} не прошёл валидацию: {step}, пропускаем")
                continue
            action = step[0]
            value = step[1] if len(step) > 1 else ""
            delay_ms = step[2] if len(step) > 2 else 0
            if not self.execute_step(action, value, delay_ms, check_window):
                _log.warning(f"Шаг {i+1} не выполнен")
                self.reset()
                return False

            self._current_step = i + 1

            if i == 1 and cast_lock_callback is not None:
                cast_lock_callback()
                _log.debug(" Уведомление о блокировке каста (управляется диспетчером)")

        total_duration = (time.time() - start_time) * 1000
        _log.debug(f"Последовательность выполнена за {total_duration:.2f}мс")
        return True

    def _send_key(self, key: str) -> bool:
        try:
            send_key(key)
            _log.debug(f"Клавиша '{key}' отправлена")
            return True
        except Exception as e:
            _log.error(f"Ошибка отправки клавиши '{key}': {e}", exc_info=True)
            return False

    def _click_left(self) -> None:
        click_left()
        _log.debug("Левый клик мыши")

    def _click_right(self) -> None:
        click_right()
        _log.debug("Правый клик мыши")

    @property
    def current_step(self) -> int:
        return self._current_step

    def reset(self) -> None:
        self._current_step = 0


