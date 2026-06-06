import json
import os
import tempfile
import threading
from typing import Any, Dict
from pathlib import Path

from .logger_manager import get_logger

logger = get_logger('settings')


class SettingsManager:

    DEFAULTS = {
        "swap_key_chant": "",
        "swap_key_pa": "",
        "start_all_hotkey": "-",
        "stop_all_hotkey": "=",
        "base_channeling": 0,
        "castbar_swap_delay": 10.0,
        "cooldown_margin": 0.3,
        "cast_lock_margin": 0.45,
        "castbar_enabled": False,
        "castbar_point": "",
        "castbar_threshold": 70,
        "castbar_color": [94, 123, 104],
        "castbar_size": 5,
        "movement_delay_enabled": False,
        "movement_delay_ms": 300,
        "check_distance": False,
        "use_castbar_detection": False,
        "ocr_scale": 10,
        "ocr_psm": 10,
        "ocr_use_morph": True,
        "ocr_languages": "eng+rus",
        "process_name": "",
        "server_ip": "",
        "ping_auto": False,
        "ping_check_interval": 5,
        "average_ping": 0,
        "global_step_delay": 0.0,
        "first_step_delay": 0.0,
        "use_fixed_delays": True,
        "use_ping_delays": False,
        "mob_area": "",
        "player_area": [0, 0, 0, 0],
        "window_opacity": 1.0,
        "window_locked": False,
        "target_window_title": "",
        "buff_8004_click_point": "",
        "accent_color": "#fd79a8",
        "log_level_macros": "INFO",
        "log_level_errors": "ERROR",
        "log_level_ocr": "DEBUG",
        "log_level_network": "INFO",
        "log_level_settings": "INFO",
        "log_level_debug": "DEBUG",
        "log_level_shiboken": "WARNING",
    }

    def __init__(self, settings_file: str = "settings.json"):
        self.settings_file = Path(settings_file)
        self._lock = threading.RLock()
        self._settings: Dict[str, Any] = {}
        self._listeners: Dict[str, list] = {}
        self._load_settings()

    def _load_settings(self) -> None:
        with self._lock:
            if self.settings_file.exists():
                try:
                    with open(self.settings_file, 'r', encoding='utf-8') as f:
                        loaded = json.load(f)

                    self._settings = {**self.DEFAULTS, **loaded}
                    
                    self._convert_settings_types()
                    
                    logger.info(f"Загружено {len(loaded)} настроек из {self.settings_file}")
                except Exception as e:
                    logger.error(f"Ошибка загрузки настроек: {e}", exc_info=True)
                    self._settings = self.DEFAULTS.copy()
            else:
                self._settings = self.DEFAULTS.copy()
                logger.info("Настройки по умолчанию загружены")

    @staticmethod
    def _normalize(key: str, value: Any) -> Any:
        if key in ("base_channeling", "movement_delay_ms", "ocr_scale", "first_step_delay", "castbar_threshold"):
            try:
                return int(value)
            except (ValueError, TypeError):
                return SettingsManager.DEFAULTS.get(key, 0)
        if key in ("cooldown_margin", "cast_lock_margin", "castbar_swap_delay", "global_step_delay"):
            try:
                return float(value)
            except (ValueError, TypeError):
                return SettingsManager.DEFAULTS.get(key, 0.0)
        if key in ("use_castbar_detection", "castbar_enabled", "movement_delay_enabled",
                    "check_distance", "ocr_use_morph", "ping_auto"):
            if isinstance(value, str):
                return value.lower() in ("true", "1", "yes")
            if not isinstance(value, bool):
                return bool(value)
            return value
        if key == "castbar_color":
            if isinstance(value, str):
                try:
                    return [int(x) for x in value.split(',')]
                except (ValueError, TypeError):
                    return SettingsManager.DEFAULTS.get("castbar_color", [94, 123, 104])
            if isinstance(value, list):
                return [int(x) for x in value]
        return value

    def _convert_settings_types(self) -> None:
        for key in list(self._settings.keys()):
            if key in self.DEFAULTS:
                self._settings[key] = self._normalize(key, self._settings[key])

    def save_settings(self) -> bool:
        with self._lock:
            try:
                settings_to_save = self._settings.copy()
                
                if "castbar_color" in settings_to_save:
                    color = settings_to_save["castbar_color"]
                    if isinstance(color, str):
                        try:
                            settings_to_save["castbar_color"] = [int(x) for x in color.split(',')]
                        except (ValueError, TypeError):
                            settings_to_save["castbar_color"] = [94, 123, 104]
                
                fd, tmp_path = tempfile.mkstemp(
                    suffix='.tmp',
                    dir=str(self.settings_file.parent),
                    prefix='settings_'
                )
                try:
                    with os.fdopen(fd, 'w', encoding='utf-8') as f:
                        json.dump(settings_to_save, f, indent=2, ensure_ascii=False)
                    os.replace(tmp_path, str(self.settings_file))
                except Exception:
                    try:
                        os.unlink(tmp_path)
                    except Exception:
                        pass
                    raise
                logger.info(f"Настройки атомарно сохранены в {self.settings_file}")
                return True
            except Exception as e:
                logger.error(f"Ошибка сохранения настроек: {e}", exc_info=True)
                return False

    def get(self, key: str, default: Any = None) -> Any:
        with self._lock:
            if key in self._settings:
                return self._settings[key]
            if default is not None:
                return default
            return self.DEFAULTS.get(key)

    def set(self, key: str, value: Any, notify: bool = True) -> None:
        with self._lock:
            value = self._normalize(key, value)
            old_value = self._settings.get(key)
            self._settings[key] = value

            logger.debug(f"Настройка {key} изменена: {old_value} → {value}")

            if notify and old_value != value:
                self._notify_listeners(key, value)

            self.save_settings()

    def _notify_listeners(self, key: str, value: Any) -> None:
        if key in self._listeners:
            for callback in self._listeners[key]:
                try:
                    callback(key, value)
                except Exception as e:
                    logger.error(f"Ошибка в слушателе настройки {key}: {e}", exc_info=True)

    def get_all(self) -> Dict[str, Any]:
        with self._lock:
            return self._settings.copy()
