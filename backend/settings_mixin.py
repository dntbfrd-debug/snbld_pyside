import json
import os
import logging

from backend.logger_manager import get_logger

logger = get_logger('settings')


class SettingsMixin:

    def _validate_setting(self, key, value):
        numeric_keys = {"ocrScale", "castbar_threshold", "castbar_size", "ocr_scale", "ocr_psm",
                        "target_interval", "ping_check_interval", "average_ping",
                        "global_step_delay", "first_step_delay", "cooldown_margin",
                        "cast_lock_margin", "cast_finish_delay", "movement_delay_ms",
                        "distance_tolerance", "window_opacity", "base_channeling"}
        string_keys = {"swap_key_chant", "swap_key_pa", "castbar_point", "process_name",
                       "server_ip", "start_all_hotkey", "stop_all_hotkey",
                       "mob_area", "player_area", "target_window_title",
                       "accent_color", "buff_8004_click_point"}
        bool_keys = {"castbar_enabled", "movement_delay_enabled", "check_distance",
                     "use_castbar_detection", "ocr_use_morph", "ping_auto",
                     "window_locked", "window_manager_skip_activation",
                     "force_sendinput", "use_fixed_delays", "use_ping_delays"}
        if key in numeric_keys:
            if not isinstance(value, (int, float)) or value <= 0:
                raise ValueError(f"Invalid setting {key}: {value!r} (must be positive number)")
        elif key in string_keys:
            if not isinstance(value, str) or len(value) == 0:
                raise ValueError(f"Invalid setting {key}: {value!r} (must be non-empty string)")
        elif key in bool_keys:
            if not isinstance(value, bool):
                raise ValueError(f"Invalid setting {key}: {value!r} (must be bool)")

    def load_settings(self):
        from backend.settings_manager import SettingsManager
        settings_path = os.path.join(self.data_dir, 'settings.json')
        settings_manager = SettingsManager(settings_file=settings_path)
        self._settings = settings_manager.get_all()
        self._apply_settings_to_attributes()
        logger.info(f"Настройки загружены: castbar_enabled={self.castbar_enabled}, castbar_point={self.castbar_point}, castbar_color={self.castbar_color}, castbar_threshold={self.castbar_threshold}")

    def _load_castbar_color(self, color_value):
        if isinstance(color_value, str):
            try:
                return [int(x.strip()) for x in color_value.split(',')]
            except Exception:
                return [94, 123, 104]
        elif isinstance(color_value, list):
            return [int(x) for x in color_value]
        return [94, 123, 104]

    def save_settings(self):
        with self._settings_lock:
            try:
                settings_path = os.path.join(self.data_dir, 'settings.json')
                with open(settings_path, 'w', encoding='utf-8') as f:
                    json.dump(self._settings, f, indent=2, ensure_ascii=False)
                logger.info("Настройки сохранены в settings.json")
                if self._current_profile:
                    logger.debug(f"[PROFILE] Автосохранение настроек в профиль: {self._current_profile}")
                    self._save_profile_no_notify(self._current_profile)
            except Exception as e:
                logger.error(f"Ошибка сохранения настроек: {e}", exc_info=True)

    def _save_profile_no_notify(self, name):
        try:
            macros_data = []
            for m in self._macros:
                try:
                    macros_data.append(self._macro_to_dict(m))
                except Exception as e:
                    logger.error(f"[SETTINGS] Ошибка сериализации макроса '{m.name}': {e}", exc_info=True)
            profile_data = {
                "settings": dict(self._settings),
                "macros": macros_data,
                "window_locked": self._settings.get("window_locked", False),
                "target_window_title": self._settings.get("target_window_title", "")
            }
            profile_path = os.path.join(self.profiles_dir, f"{name}.json")
            with open(profile_path, 'w', encoding='utf-8') as f:
                json.dump(profile_data, f, ensure_ascii=False, indent=2)
            logger.debug(f"[PROFILE] Настройки автосохранены в {name}.json")
        except Exception as e:
            logger.error(f"[PROFILE] Ошибка автосохранения: {e}", exc_info=True)
