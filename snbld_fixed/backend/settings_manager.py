# -*- coding: utf-8 -*-
"""
backend/settings_manager.py
Менеджер настроек приложения
"""

import json
import logging
from typing import Any, Dict, Optional
from pathlib import Path

from .logger_manager import get_logger

logger = get_logger('settings')


class SettingsManager:
    """Менеджер настроек приложения."""

    # Настройки по умолчанию
    DEFAULTS = {
        "swap_key_chant": "e", "swap_key_pa": "e",
        "base_channeling": 91, "castbar_swap_delay": 10.0,
        "cooldown_margin": 0.3, "cast_lock_margin": 0.45,
        "castbar_enabled": False, "castbar_point": "1081,1337",
        "castbar_threshold": 70, "castbar_color": [94, 123, 104],
        "castbar_size": 5, "movement_delay_enabled": True,
        "movement_delay_ms": 300, "check_distance": True,
        "use_castbar_detection": False, "ocr_scale": 10,
        "ocr_psm": 10, "ocr_use_morph": True,
        "process_name": "ElementClient_x64.exe",
        "server_ip": "147.45.96.78", "ping_auto": True,
        "ping_check_interval": 5, "average_ping": 29,
        "global_step_delay": 15.0, "first_step_delay": 90,
        "use_fixed_delays": True, "use_ping_delays": False,
        "start_all_hotkey": "-", "stop_all_hotkey": "=",
        "mob_area": "1266,32,1303,56",
        "player_area": [1271, 16, 1294, 32],
        "window_opacity": 1.0, "window_locked": False,
        "target_window_title": "",
        "buff_8004_click_point": "0,0",
        "accent_color": "#fd79a8",
        "log_level_macros": "INFO", "log_level_errors": "ERROR",
        "log_level_ocr": "DEBUG", "log_level_network": "INFO",
        "log_level_settings": "INFO", "log_level_debug": "DEBUG",
        "log_level_shiboken": "WARNING",
    }

    def __init__(self, settings_file: str = "settings.json"):
        self.settings_file = Path(settings_file)
        self._settings: Dict[str, Any] = {}
        self._listeners: Dict[str, list] = {}
        self._load_settings()

    def _load_settings(self) -> None:
        """Загружает настройки из файла"""
        if self.settings_file.exists():
            try:
                with open(self.settings_file, 'r', encoding='utf-8') as f:
                    loaded = json.load(f)

                # Объединяем с настройками по умолчанию
                self._settings = {**self.DEFAULTS, **loaded}
                
                # Преобразуем типы настроек
                self._convert_settings_types()
                
                logger.info(f"Загружено {len(loaded)} настроек из {self.settings_file}")
            except Exception as e:
                logger.error(f"Ошибка загрузки настроек: {e}")
                self._settings = self.DEFAULTS.copy()
        else:
            self._settings = self.DEFAULTS.copy()
            logger.info("Настройки по умолчанию загружены")

    def _convert_settings_types(self) -> None:
        """Преобразует типы настроек к правильным значениям"""
        # Числовые настройки
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

        # Булевы настройки
        for key in ("use_castbar_detection", "castbar_enabled", "movement_delay_enabled", 
                    "check_distance", "ocr_use_morph", "ping_auto"):
            if key in self._settings:
                val = self._settings[key]
                if isinstance(val, str):
                    self._settings[key] = val.lower() in ("true", "1", "yes")
                elif not isinstance(val, bool):
                    self._settings[key] = bool(val)

        # castbar_color - преобразуем в список int
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
        """Сохраняет настройки в файл"""
        try:
            # Создаём копию настроек для сохранения
            settings_to_save = self._settings.copy()
            
            # Преобразуем castbar_color в список int если это строка
            if "castbar_color" in settings_to_save:
                color = settings_to_save["castbar_color"]
                if isinstance(color, str):
                    try:
                        settings_to_save["castbar_color"] = [int(x) for x in color.split(',')]
                    except (ValueError, TypeError):
                        settings_to_save["castbar_color"] = [94, 123, 104]
            
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(settings_to_save, f, indent=2, ensure_ascii=False)
            logger.info(f"Настройки сохранены в {self.settings_file}")
            return True
        except Exception as e:
            logger.error(f"Ошибка сохранения настроек: {e}")
            return False

    def get(self, key: str, default: Any = None) -> Any:
        """Получает значение настройки"""
        if key in self._settings:
            return self._settings[key]
        if default is not None:
            return default
        return self.DEFAULTS.get(key)

    def set(self, key: str, value: Any, notify: bool = True) -> None:
        """
        Устанавливает значение настройки.

        Args:
            key: Ключ настройки
            value: Новое значение
            notify: Уведомлять слушателей об изменении
        """
        # Преобразование типов
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
        
        # Автоматическое сохранение настроек при изменении
        self.save_settings()

    def add_listener(self, key: str, callback) -> None:
        """
        Добавляет слушателя изменений настройки.
        
        Args:
            key: Ключ настройки для отслеживания
            callback: Функция обратного вызова (key, value)
        """
        if key not in self._listeners:
            self._listeners[key] = []
        self._listeners[key].append(callback)

    def remove_listener(self, key: str, callback) -> None:
        """Удаляет слушателя изменений настройки"""
        if key in self._listeners:
            try:
                self._listeners[key].remove(callback)
            except ValueError:
                pass

    def _notify_listeners(self, key: str, value: Any) -> None:
        """Уведомляет слушателей об изменении настройки"""
        if key in self._listeners:
            for callback in self._listeners[key]:
                try:
                    callback(key, value)
                except Exception as e:
                    logger.error(f"Ошибка в слушателе настройки {key}: {e}")

    def get_all(self) -> Dict[str, Any]:
        """Возвращает все настройки"""
        return self._settings.copy()

    def update_batch(self, updates: Dict[str, Any]) -> None:
        """
        Массовое обновление настроек.
        
        Args:
            updates: Словарь с обновлениями {key: value}
        """
        for key, value in updates.items():
            self.set(key, value, notify=False)
        
        # Уведомляем об изменениях (можно доработать для пакетных уведомлений)
        for key in updates:
            self._notify_listeners(key, self._settings[key])
        
        # Сохраняем все изменения после пакетного обновления
        self.save_settings()

    def reset_to_defaults(self, keys: Optional[list] = None) -> None:
        """
        Сбрасывает настройки к значениям по умолчанию.

        Args:
            keys: Список ключей для сброса (None = все настройки)
        """
        if keys is None:
            keys = list(self.DEFAULTS.keys())

        for key in keys:
            if key in self.DEFAULTS:
                old_value = self._settings.get(key)
                new_value = self.DEFAULTS[key]
                if old_value != new_value:
                    self._settings[key] = new_value
                    self._notify_listeners(key, new_value)
        
        # Сохраняем после сброса настроек
        self.save_settings()

    def apply_log_levels(self) -> None:
        """
        Применяет уровни логирования из настроек.
        Вызывать после инициализации LoggerManager.
        """
        from .logger_manager import LoggerManager
        
        log_levels = {
            'macros': self.get('log_level_macros', 'INFO'),
            'errors': self.get('log_level_errors', 'ERROR'),
            'ocr': self.get('log_level_ocr', 'DEBUG'),
            'network': self.get('log_level_network', 'INFO'),
            'settings': self.get('log_level_settings', 'INFO'),
            'debug': self.get('log_level_debug', 'DEBUG'),
            'shiboken': self.get('log_level_shiboken', 'WARNING'),
        }
        
        level_map = {
            'DEBUG': logging.DEBUG,
            'INFO': logging.INFO,
            'WARNING': logging.WARNING,
            'ERROR': logging.ERROR,
            'CRITICAL': logging.CRITICAL,
        }
        
        import logging
        
        for category, level_str in log_levels.items():
            level = level_map.get(level_str.upper(), logging.INFO)
            LoggerManager.set_log_level(category, level)
        
        logger.info(f"Уровни логирования применены: {log_levels}")
