# -*- coding: utf-8 -*-
"""
utils/sound_alert.py
Звуковые уведомления при критических ошибках
Использует встроенный Windows Beep (winsound) — без внешних зависимостей
"""

import threading


# Типы звуковых событий
SOUND_OCR_FAIL = "ocr_fail"         # OCR не может распознать
SOUND_MACRO_ERROR = "macro_error"  # Макрос завершился с ошибкой
SOUND_WINDOW_LOST = "window_lost"  # Окно игры потеряно
SOUND_PROCESS_DIED = "process_died" # Процесс игры упал
SOUND_CRITICAL = "critical"         # Критическая ошибка

# Настройки звуков: (частота Гц, длительность мс)
_SOUND_PATTERNS = {
    SOUND_OCR_FAIL:      (440, 200),   # Один короткий сигнал
    SOUND_MACRO_ERROR:   (330, 300),   # Низкий тон
    SOUND_WINDOW_LOST:   (520, 150),   # Средний тон
    SOUND_PROCESS_DIED:  (220, 500),   # Длинный низкий
    SOUND_CRITICAL:      (880, 100, 3), # Тройной высокий (частота, длительность, повторы)
}

# Глобальная вкл/выкл
_sound_enabled = True


def enable_sounds(enabled=True):
    """Включить/выключить звуковые уведомления"""
    global _sound_enabled
    _sound_enabled = enabled


def are_sounds_enabled():
    return _sound_enabled


def play_alert_sound(alert_type=SOUND_CRITICAL):
    """
    Проигрывает звуковой сигнал.
    Выполняется в отдельном потоке чтобы не блокировать основной.

    Args:
        alert_type: Тип звукового события из _SOUND_PATTERNS
    """
    if not _sound_enabled:
        return

    pattern = _SOUND_PATTERNS.get(alert_type)
    if not pattern:
        return

    def _play():
        try:
            import winsound
            if len(pattern) == 3:
                # Тройной сигнал
                freq, duration, repeats = pattern
                for _ in range(repeats):
                    winsound.Beep(freq, duration)
                    import time
                    time.sleep(0.15)
            else:
                freq, duration = pattern
                winsound.Beep(freq, duration)
        except Exception:
            # winsound может не работать в некоторых окружениях — игнорируем
            pass

    threading.Thread(target=_play, daemon=True).start()
