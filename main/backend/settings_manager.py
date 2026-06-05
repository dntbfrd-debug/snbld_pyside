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

    def _convert_settings_types(self) -> None:
        for key in ("base_channeling", "movement_delay_ms", "ocr_scale", "first_step_delay"):
            if key in self._settings:
                try:
                    self._settings[key] = int(self._settings[key])
                except (ValueError, TypeError):
                    self._settings[key] = self.DEFAULTS[key]

        for key in ("cooldown_margin", "cast_lock_margin"):
            if key in self._settings:
                try:
                    self._settings[key] = float(self._settings[key])
                except (ValueError, TypeError):
                    self._settings[key] = self.DEFAULTS[key]

        for key in ("castbar_swap_delay", "global_step_delay"):
            if key in self._settings:
                try:
                    self._settings[key] = float(self._settings[key])
                except (ValueError, TypeError):
                    self._settings[key] = self.DEFAULTS[key]

        if "castbar_threshold" in self._settings:
            try:
                self._settings["castbar_threshold"] = int(self._settings["castbar_threshold"])
            except (ValueError, TypeError):
                self._settings["castbar_threshold"] = self.DEFAULTS["castbar_threshold"]

        for key in ("use_castbar_detection", "castbar_enabled", "movement_delay_enabled", 
                    "check_distance", "ocr_use_morph", "ping_auto"):
            if key in self._settings:
                val = self._settings[key]
                if isinstance(val, str):
                    self._settings[key] = val.lower() in ("true", "1", "yes")
                elif not isinstance(val, bool):
                    self._settings[key] = bool(val)

        if "castbar_color" in self._settings:
            color = self._settings["castbar_color"]
            if isinstance(color, str):
                try:
                    self._settings["castbar_color"] = [int(x) for x in color.split(',')]
                except (ValueError, TypeError):
                    self._settings["castbar_color"] = self.DEFAULTS["castbar_color"]
            elif isinstance(color, list):
                self._settings["castbar_color"] = [int(x) for x in color]

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
            if key in ("base_channeling", "movement_delay_ms", "ocr_scale", "first_step_delay"):
                try:
                    value = int(value)
                except (ValueError, TypeError):
                    value = 0
            elif key in ("cooldown_margin", "cast_lock_margin"):
                try:
                    value = float(value)
                except (ValueError, TypeError):
                    value = 0.0
            elif key in ("castbar_swap_delay", "global_step_delay"):
                try:
                    value = float(value)
                except (ValueError, TypeError):
                    value = 0.0
            elif key in ("castbar_threshold",):
                try:
                    value = int(value)
                except (ValueError, TypeError):
                    value = 70
            elif key in ("use_castbar_detection", "castbar_enabled"):
                if isinstance(value, str):
                    value = value.lower() in ("true", "1", "yes")
            elif key in ("movement_delay_enabled", "check_distance", "ocr_use_morph", "ping_auto"):
                if isinstance(value, str):
                    value = value.lower() in ("true", "1", "yes")

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
