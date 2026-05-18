import os
import sys
import json
import time
import threading
from datetime import datetime
from typing import Optional


class SessionLogger:

    def __init__(self, log_dir: Optional[str] = None):
        self._lock = threading.Lock()
        self._file = None
        self._current_date = None

        if log_dir is None:
            app_dir = os.getcwd()
            temp_dir = os.environ.get('TEMP', '') or os.environ.get('TMP', '')
            if temp_dir and app_dir.startswith(temp_dir):
                if hasattr(sys, 'argv') and sys.argv and sys.argv[0]:
                    app_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
            log_dir = app_dir

        self._log_dir = log_dir
        os.makedirs(self._log_dir, exist_ok=True)

    def _get_file(self):
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
            pass

_instance: Optional[SessionLogger] = None
_instance_lock = threading.Lock()


def get_session_log() -> SessionLogger:
    global _instance
    if _instance is None:
        with _instance_lock:
            if _instance is None:
                _instance = SessionLogger()
    return _instance
