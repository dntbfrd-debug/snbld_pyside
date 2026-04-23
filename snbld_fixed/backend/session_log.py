# -*- coding: utf-8 -*-
"""
backend/session_log.py
Таймлайн игровой сессии — единый лог всех важных событий
Записывает: запуск/стоп макросов, ошибки OCR, потерю окна, восстановление
"""

import os
import sys
import json
import time
import threading
from datetime import datetime
from typing import Optional

# Формат: одна строка = одно событие JSON
# Файл: session_<дата>.jsonl (JSON Lines)


class SessionLogger:
    """
    Пишет события в файл session_<дата>.jsonl рядом с exe.
    Каждое событие — одна строка JSON.
    """

    # Типы событий
    EVENT_MACRO_START = "macro_start"
    EVENT_MACRO_STOP = "macro_stop"
    EVENT_MACRO_ERROR = "macro_error"
    EVENT_OCR_START = "ocr_start"
    EVENT_OCR_STOP = "ocr_stop"
    EVENT_OCR_ERROR = "ocr_error"
    EVENT_OCR_RECOVERY = "ocr_recovery"
    EVENT_WINDOW_LOST = "window_lost"
    EVENT_WINDOW_FOUND = "window_found"
    EVENT_PROCESS_DIED = "process_died"
    EVENT_ALL_START = "all_start"
    EVENT_ALL_STOP = "all_stop"
    EVENT_PROFILE_LOAD = "profile_load"
    EVENT_ERROR = "error"
    EVENT_INFO = "info"

    def __init__(self, log_dir: Optional[str] = None):
        self._lock = threading.Lock()
        self._file = None
        self._current_date = None

        if log_dir is None:
            # Используем cwd - это работает правильно для onefile
            app_dir = os.getcwd()
            temp_dir = os.environ.get('TEMP', '') or os.environ.get('TMP', '')
            if temp_dir and app_dir.startswith(temp_dir):
                # cwd в TEMP, используем sys.argv[0]
                if hasattr(sys, 'argv') and sys.argv and sys.argv[0]:
                    app_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
            log_dir = app_dir

        self._log_dir = log_dir
        os.makedirs(self._log_dir, exist_ok=True)

    def _get_file(self):
        """Возвращает файловый объект для текущей даты (авторотация)"""
        today = datetime.now().strftime("%Y-%m-%d")
        if self._current_date != today:
            if self._file:
                try:
                    self._file.flush()
                    self._file.close()
                except Exception:
                    pass
            self._current_date = today
            path = os.path.join(self._log_dir, f"session_{today}.jsonl")
            self._file = open(path, "a", encoding="utf-8")
        return self._file

    def log(self, event_type: str, message: str = "", data: Optional[dict] = None):
        """
        Записывает событие в таймлайн.

        Args:
            event_type: Тип события (EVENT_*)
            message: Краткое описание
            data: Дополнительные данные (dict)
        """
        try:
            entry = {
                "ts": time.time(),
                "time": datetime.now().strftime("%H:%M:%S"),
                "event": event_type,
                "msg": message,
            }
            if data:
                entry["data"] = data

            with self._lock:
                f = self._get_file()
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")
                f.flush()

        except Exception:
            pass  # Тихо игнорируем — лог не должен ломать программу

    def close(self):
        """Закрывает файл"""
        with self._lock:
            if self._file:
                try:
                    self._file.flush()
                    self._file.close()
                except Exception:
                    pass
                self._file = None

    def get_today_events(self) -> list:
        """
        Возвращает события за сегодня.

        Returns:
            Список dict с событиями
        """
        today = datetime.now().strftime("%Y-%m-%d")
        path = os.path.join(self._log_dir, f"session_{today}.jsonl")
        events = []

        if not os.path.exists(path):
            return events

        try:
            with open(path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        try:
                            events.append(json.loads(line))
                        except json.JSONDecodeError:
                            pass
        except Exception:
            pass

        return events

    def get_session_summary(self) -> str:
        """
        Возвращает читаемый-summary сессии.

        Returns:
            Строка с таймлайном
        """
        events = self.get_today_events()
        if not events:
            return "Нет событий за сегодня"

        lines = [f"=== Сессия {datetime.now().strftime('%d.%m.%Y')} ==="]
        for e in events:
            time_str = e.get("time", "?")
            msg = e.get("msg", "")
            lines.append(f"  [{time_str}] {msg}")

        return "\n".join(lines)


# Singleton
_instance: Optional[SessionLogger] = None
_instance_lock = threading.Lock()


def get_session_log() -> SessionLogger:
    """Получает singleton экземпляр SessionLogger"""
    global _instance
    if _instance is None:
        with _instance_lock:
            if _instance is None:
                _instance = SessionLogger()
    return _instance
