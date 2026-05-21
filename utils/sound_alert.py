import threading
import logging
import os

logger = logging.getLogger('debug')

SOUND_OCR_FAIL = "ocr_fail"
SOUND_MACRO_ERROR = "macro_error"
SOUND_WINDOW_LOST = "window_lost"
SOUND_PROCESS_DIED = "process_died"
SOUND_CRITICAL = "critical"
SOUND_START = "macro_start"
SOUND_STOP = "macro_stop"
SOUND_EXIT = "macro_exit"

_SOUND_PATTERNS = {
    SOUND_OCR_FAIL:      (440, 200),
    SOUND_MACRO_ERROR:   (330, 300),
    SOUND_WINDOW_LOST:   (520, 150),
    SOUND_PROCESS_DIED:  (220, 500),
    SOUND_CRITICAL:      (880, 100, 3),
}

_MESSAGE_BEEP_MAP = {
    SOUND_OCR_FAIL:      0x00000000,
    SOUND_MACRO_ERROR:   0x00000010,
    SOUND_WINDOW_LOST:   0x00000000,
    SOUND_PROCESS_DIED:  0x00000010,
    SOUND_CRITICAL:      0x00000010,
}

_sound_enabled = True

_start_mp3 = ""
_stop_mp3 = ""
_exit_mp3 = ""


def set_sound_files(start_path, stop_path, exit_path=""):
    global _start_mp3, _stop_mp3, _exit_mp3
    _start_mp3 = start_path
    _stop_mp3 = stop_path
    _exit_mp3 = exit_path
    logger.info(f"[SOUND] MP3: start={os.path.exists(start_path)}, stop={os.path.exists(stop_path)}, exit={os.path.exists(exit_path)}")


def enable_sounds(enabled=True):
    global _sound_enabled
    _sound_enabled = enabled


def are_sounds_enabled():
    return _sound_enabled


def _play_mp3(filepath):
    if not filepath or not os.path.isfile(filepath):
        return False
    try:
        import ctypes
        winmm = ctypes.windll.winmm
        alias = "snbld_snd"
        winmm.mciSendStringW(f"close {alias}", None, 0, 0)
        result = winmm.mciSendStringW(f'open "{filepath}" alias {alias}', None, 0, 0)
        if result == 0:
            winmm.mciSendStringW(f"play {alias}", None, 0, 0)
            return True
    except Exception as e:
        logger.debug(f"[SOUND] MCI error: {e}")
    return False


def _play_beep(pattern):
    import winsound
    if len(pattern) == 3:
        freq, duration, repeats = pattern
        for _ in range(repeats):
            winsound.Beep(freq, duration)
            import time
            time.sleep(0.15)
    else:
        freq, duration = pattern
        winsound.Beep(freq, duration)


def _play_message_beep(sound_type):
    import winsound
    winsound.MessageBeep(sound_type)


def play_alert_sound(alert_type=SOUND_CRITICAL):
    if not _sound_enabled:
        return

    pattern = _SOUND_PATTERNS.get(alert_type)
    if not pattern and alert_type not in (SOUND_START, SOUND_STOP, SOUND_EXIT):
        return

    def _play():
        if alert_type == SOUND_START:
            if _play_mp3(_start_mp3):
                return
            _play_message_beep(0x00000040)
            return

        if alert_type == SOUND_STOP:
            if _play_mp3(_stop_mp3):
                return
            _play_message_beep(0x00000030)
            return

        if alert_type == SOUND_EXIT:
            # Играем синхронно (не daemon поток) — при выходе daemon-потоки убиваются
            _play_mp3(_exit_mp3)
            time.sleep(0.05)  # дать MCI время начать воспроизведение
            return

        if pattern:
            try:
                _play_beep(pattern)
            except Exception:
                sound_type = _MESSAGE_BEEP_MAP.get(alert_type, 0x00000000)
                try:
                    _play_message_beep(sound_type)
                except Exception:
                    pass

    threading.Thread(target=_play, daemon=True).start()