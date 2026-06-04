"""ProfileMixin — управление профилями (создание/загрузка/сохранение/удаление/переименование).

Профили живут в self.profiles_dir как *.json. Каждый профиль содержит
копию настроек + список макросов. Методы ProfileMixin дергаются QML.
"""

import json
import os
import re
import shutil
import threading

from PySide6.QtCore import Slot
from PySide6.QtWidgets import QFileDialog

from backend.logger_manager import get_logger

logger = get_logger('backend')


class ProfileMixin:

    def _clean_profile_name(self, name: str) -> str:
        clean_name = re.sub(r'[<>:"/\\|?*]', '', name.strip())
        clean_name = re.sub(r'[\x00-\x1f\x7f]', '', clean_name)
        clean_name = clean_name.rstrip('. ')
        return clean_name

    @Slot()
    def get_profile_list(self):
        try:
            profiles = []
            if os.path.exists(self.profiles_dir):
                for file in os.listdir(self.profiles_dir):
                    if file.endswith('.json'):
                        profiles.append(file[:-5])
            return profiles
        except Exception as e:
            logger.error(f"[PROFILE] Ошибка получения списка профилей: {e}", exc_info=True)
            return []

    @Slot(str)
    def create_profile(self, name):
        if not name:
            self.notification.emit("Укажите имя профиля", "warning")
            return
        clean_name = self._clean_profile_name(name)
        if not clean_name:
            self.notification.emit("Имя профиля не может содержать только спецсимволов", "warning")
            return
        profile_path = os.path.join(self.profiles_dir, f"{clean_name}.json")
        if os.path.exists(profile_path):
            self.notification.emit(f"Профиль '{clean_name}' уже существует", "warning")
            return
        try:
            profile_data = {
                "settings": dict(self._settings),
                "macros": [],
                "window_locked": self._settings.get("window_locked", False),
                "target_window_title": self._settings.get("target_window_title", "")
            }
            with open(profile_path, 'w', encoding='utf-8') as f:
                json.dump(profile_data, f, ensure_ascii=False, indent=2)
            self._current_profile = clean_name
            self._settings["last_active_profile"] = clean_name
            self._macros = []
            self._update_macros_dicts()
            self.profileChanged.emit()
            self.profilesChanged.emit()
            self.settingsChanged.emit()
            self.save_settings()
            self.register_all_hotkeys()
            self.notification.emit(f"Профиль '{clean_name}' создан", "success")
            logger.info(f"[PROFILE] Создан профиль: {clean_name}")
        except Exception as e:
            logger.error(f"[PROFILE] Ошибка создания профиля: {e}", exc_info=True)
            self.notification.emit(f"Ошибка создания: {e}", "error")

    @Slot(str, str)
    def rename_profile(self, old_name, new_name):
        if not old_name or not new_name:
            self.notification.emit("Некорректное имя профиля", "warning")
            return
        clean_name = self._clean_profile_name(new_name)
        if not clean_name:
            self.notification.emit("Имя профиля не может содержать только спецсимволов", "warning")
            return
        if clean_name == old_name:
            self.notification.emit("Имя не изменилось", "info")
            return
        old_path = os.path.join(self.profiles_dir, f"{old_name}.json")
        new_path = os.path.join(self.profiles_dir, f"{clean_name}.json")
        if not os.path.exists(old_path):
            self.notification.emit(f"Профиль '{old_name}' не найден", "error")
            return
        if os.path.exists(new_path):
            self.notification.emit(f"Профиль '{clean_name}' уже существует", "warning")
            return
        try:
            os.rename(old_path, new_path)
            self._current_profile = clean_name
            self._settings["last_active_profile"] = clean_name
            self.profileChanged.emit()
            self.profilesChanged.emit()
            self.save_settings()
            self.notification.emit(f"Профиль переименован в '{clean_name}'", "success")
            logger.info(f"[PROFILE] Профиль '{old_name}' переименован в '{clean_name}'")
        except Exception as e:
            logger.error(f"[PROFILE] Ошибка переименования профиля: {e}", exc_info=True)
            self.notification.emit(f"Ошибка переименования: {e}", "error")

    @Slot(str)
    def save_profile(self, name=None):
        if name is None:
            name = self._current_profile
        if not name:
            self.notification.emit("Укажите имя профиля", "warning")
            return
        clean_name = self._clean_profile_name(name)
        if not clean_name:
            self.notification.emit("Имя профиля не может содержать только спецсимволов", "warning")
            return
        try:
            logger.info(f"[PROFILE] Сохранение профиля '{clean_name}': макросов={len(self._macros)}, настроек={len(self._settings)}")
            macros_data = []
            for m in self._macros:
                try:
                    macros_data.append(self._macro_to_dict(m))
                except Exception as e:
                    logger.error(f"[PROFILE] Ошибка сериализации макроса '{m.name}': {e}", exc_info=True)
            profile_data = {
                "settings": dict(self._settings),
                "macros": macros_data,
                "window_locked": self._settings.get("window_locked", False),
                "target_window_title": self._settings.get("target_window_title", "")
            }
            logger.info(f"[PROFILE] Подготовлено макросов: {len(profile_data['macros'])}")
            profile_path = os.path.join(self.profiles_dir, f"{clean_name}.json")
            with open(profile_path, 'w', encoding='utf-8') as f:
                json.dump(profile_data, f, ensure_ascii=False, indent=2)
            self._current_profile = clean_name
            self.profileChanged.emit()
            self.profilesChanged.emit()
            self.notification.emit(f"Профиль '{clean_name}' сохранён", "success")
            logger.info(f"[PROFILE] Сохранён профиль: {clean_name}")
        except Exception as e:
            logger.error(f"[PROFILE] Ошибка сохранения профиля: {e}", exc_info=True)
            self.notification.emit(f"Ошибка сохранения: {e}", "error")

    @Slot(str)
    def delete_profile(self, name=None):
        if name is None:
            name = self._current_profile
        if not name:
            self.notification.emit("Профиль не выбран", "warning")
            return
        profile_path = os.path.join(self.profiles_dir, f"{name}.json")
        if not os.path.exists(profile_path):
            self.notification.emit(f"Профиль '{name}' не найден", "error")
            return
        try:
            os.remove(profile_path)
            if self._current_profile == name:
                self._current_profile = None
                self.profileChanged.emit()
            self.profilesChanged.emit()
            self.notification.emit(f"Профиль '{name}' удалён", "success")
            logger.info(f"[PROFILE] Удалён профиль: {name}")
        except Exception as e:
            logger.error(f"[PROFILE] Ошибка удаления профиля: {e}", exc_info=True)
            self.notification.emit(f"Ошибка удаления: {e}", "error")

    @Slot(str)
    def load_profile(self, name):
        if not name:
            self.notification.emit("Укажите имя профиля", "warning")
            return
        if self._current_profile and self._current_profile != name:
            logger.info(f"[PROFILE] Сохранение текущего профиля '{self._current_profile}' перед загрузкой '{name}'...")
            self.save_profile(self._current_profile)
        profile_path = os.path.join(self.profiles_dir, f"{name}.json")
        if not os.path.exists(profile_path):
            self.notification.emit(f"Профиль '{name}' не найден", "error")
            return
        try:
            with open(profile_path, 'r', encoding='utf-8') as f:
                profile_data = json.load(f)
            from constants import ALLOWED_SETTINGS
            settings = profile_data.get("settings", {})
            for key, value in settings.items():
                if key in ALLOWED_SETTINGS:
                    self._settings[key] = value
            self._apply_settings_to_attributes()
            macros_data = profile_data.get("macros", [])
            logger.info(f"[PROFILE] Загрузка {len(macros_data)} макросов из профиля")
            self._macros = []
            for macro_data in macros_data:
                macro = self._create_macro_from_dict(macro_data)
                if macro:
                    self._macros.append(macro)
                    logger.debug(f"[PROFILE] Загружен макрос: {macro.name} (type={macro.type})")
            logger.info(f"[PROFILE] Загружено {len(self._macros)} макросов")
            if "window_locked" in profile_data:
                self._window_locked = profile_data["window_locked"]
                self._settings["window_locked"] = profile_data["window_locked"]
            if "target_window_title" in profile_data:
                self._target_window_title = profile_data["target_window_title"]
                self._settings["target_window_title"] = profile_data["target_window_title"]
            logger.info(f"[PROFILE] Профиль: locked={self._window_locked}, title={self._target_window_title}")
            self._current_profile = name
            self._settings["last_active_profile"] = name
            self.save_settings()
            self._update_macros_dicts()
            self.profileChanged.emit()
            self.profilesChanged.emit()
            self.settingsChanged.emit()
            if self._settings.get("mob_area") or self._settings.get("player_area"):
                if not self._ocr_running:
                    self.start_ocr()
                    logger.info("[PROFILE] OCR запущен в фоне по профилю")
                else:
                    self.stop_ocr()
                    self.start_ocr()
                    logger.info("[PROFILE] OCR перезапущен в фоне с новыми зонами по профилю")
            self.register_all_hotkeys()
            self.notification.emit(f"Профиль '{name}' загружен", "success")
            logger.info(f"[PROFILE] Загружен профиль: {name}, макросов: {len(self._macros)}")
        except Exception as e:
            logger.error(f"[PROFILE] Ошибка загрузки профиля: {e}", exc_info=True)
            self.notification.emit(f"Ошибка загрузки: {e}", "error")

    @Slot()
    def load_profile_from_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            None,
            "Выберите файл профиля",
            "",
            "Файлы профилей (*.json)"
        )
        if not file_path:
            return
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                profile_data = json.load(f)
            base_name = os.path.splitext(os.path.basename(file_path))[0]
            clean_name = self._clean_profile_name(base_name)
            if not clean_name:
                clean_name = "imported_profile"
            dest_path = os.path.join(self.profiles_dir, f"{clean_name}.json")
            suffix = 1
            while os.path.exists(dest_path):
                dest_path = os.path.join(self.profiles_dir, f"{clean_name}_{suffix}.json")
                suffix += 1
                if suffix > 100:
                    self.notification.emit("Слишком много дубликатов профиля", "error")
                    return
            shutil.copy2(file_path, dest_path)
            import_name = os.path.splitext(os.path.basename(dest_path))[0]
            self.load_profile(import_name)
            self.notification.emit(f"Профиль '{import_name}' импортирован и загружен", "success")
        except Exception as e:
            logger.error(f"[PROFILE] Ошибка импорта профиля: {e}", exc_info=True)
            self.notification.emit(f"Ошибка импорта: {e}", "error")
