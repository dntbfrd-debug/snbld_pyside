import json
import os
import re
import time
import threading

from PySide6.QtCore import Slot

from backend.logger_manager import get_logger
from constants import ALLOWED_SETTINGS
from utils.sound_alert import play_alert_sound, SOUND_START, SOUND_STOP

logger = get_logger('backend')


class MacroMixin:
    def _update_macros_dicts(self):
        new_list = []
        for macro in self._macros:
            item = {
                "name": macro.name,
                "type": macro.type,
                "hotkey": macro.hotkey or "",
                "running": macro.running,
                "steps": macro.steps,
                "zone_rect": macro.zone_rect,
            }
            if macro.type in ("skill", "zone"):
                item["cooldown"] = macro.cooldown
                item["skill_range"] = macro.skill_range
            if macro.type == "skill":
                item["skill_id"] = macro.skill_id
                item["icon"] = getattr(macro, 'icon', "")
            if macro.type == "buff":
                item["buff_id"] = macro.buff_id
                item["icon"] = getattr(macro, 'icon', "")
            new_list.append(item)
        self._macros_dicts = list(new_list)
        self.macrosChanged.emit()

    def recalculate_macro_delays(self):
        use_ping_delays = self._settings.get("use_ping_delays", False)
        if use_ping_delays:
            ping_comp = self.get_ping_compensation() * 1000
            first_step_delay = round(30 + ping_comp)
            step_delay = round(ping_comp)
        else:
            first_step_delay = self._settings.get("first_step_delay", 100)
            step_delay = self._settings.get("global_step_delay", 20)
        logger.debug(f"[MACROS] Пересчёт задержек: ping={self._ping}мс, use_ping_delays={use_ping_delays}, first_step={first_step_delay}мс, step={step_delay}мс")
        for macro in self._macros:
            if hasattr(macro, 'steps') and len(macro.steps) >= 3:
                if macro.steps[0][0] == "key":
                    macro.steps[0] = ["key", macro.steps[0][1], first_step_delay]
                if macro.steps[1][0] in ("key", "left", "right"):
                    macro.steps[1] = [macro.steps[1][0], macro.steps[1][1], step_delay]
                if macro.steps[2][0] == "key":
                    macro.steps[2] = ["key", macro.steps[2][1], step_delay]
        self._update_macros_dicts()
        logger.info(f"[MACROS] Задержки обновлены в {len(self._macros)} макросах")

    def apply_settings_to_macros(self, key, value):
        logger.info(f"apply_settings_to_macros: key={key}, value={value}")
        if key == "swap_key_chant":
            for macro in self._macros:
                if hasattr(macro, 'steps') and len(macro.steps) > 0:
                    step = macro.steps[0]
                    if len(step) >= 1 and step[0] == "key":
                        delay = step[2] if len(step) > 2 else 100
                        macro.steps[0] = ["key", value, delay]
            self.macrosChanged.emit()
        elif key == "swap_key_pa":
            for macro in self._macros:
                if hasattr(macro, 'steps') and len(macro.steps) >= 3:
                    step = macro.steps[2]
                    if len(step) >= 1 and step[0] == "key":
                        delay = step[2] if len(step) > 2 else 20
                        macro.steps[2] = ["key", value, delay]
            self.macrosChanged.emit()
        elif key == "global_step_delay":
            for macro in self._macros:
                if hasattr(macro, 'steps') and len(macro.steps) >= 2:
                    step = macro.steps[1]
                    delay = float(value)
                    macro.steps[1] = [step[0], step[1], delay]
                    if len(macro.steps) >= 3:
                        step3 = macro.steps[2]
                        macro.steps[2] = [step3[0], step3[1], delay]
            self.macrosChanged.emit()
        elif key == "first_step_delay":
            for macro in self._macros:
                if hasattr(macro, 'steps') and len(macro.steps) > 0:
                    step = macro.steps[0]
                    delay = int(value)
                    macro.steps[0] = [step[0], step[1], delay]
            self.macrosChanged.emit()
        elif key == "ocr_scale":
            self.stop_ocr()
            self.start_ocr()
        elif key == "ocr_psm":
            self.stop_ocr()
            self.start_ocr()
        elif key == "ocr_use_morph":
            self.stop_ocr()
            self.start_ocr()
        elif key == "window_locked":
            self._window_locked = value
            self.macrosChanged.emit()
        elif key == "target_window_title":
            self._target_window_title = value
            self.macrosChanged.emit()
        elif key in ("ping_auto", "process_name", "server_ip", "ping_check_interval"):
            self._stop_ping_monitor()
            if self._settings.get("ping_auto"):
                import threads
                interval = self._settings.get("ping_check_interval", 5)
                self.ping_monitor = threads.PingMonitor(self._settings.get("process_name", "elementclient.exe"), interval)
                self.ping_monitor.ping_updated.connect(self.on_ping_updated)
                self.ping_monitor.start()
        elif key in ("start_all_hotkey", "stop_all_hotkey"):
            self.unregister_all_hotkeys()
            self.register_all_hotkeys()
        elif key in ("castbar_enabled", "castbar_point", "castbar_threshold", "movement_delay_enabled", "movement_delay_ms", "check_distance", "use_castbar_detection", "distance_tolerance"):
            logger.info(f"{key}={value} будет применён при следующем запуске макроса")
        elif key == "window_opacity":
            if hasattr(self, '_main_window'):
                self._main_window.setWindowOpacity(float(value))
            self.settingsChanged.emit()
        elif key == "accent_color":
            self.settingsChanged.emit()
        elif key.startswith("log_level_"):
            from backend.logger_manager import LoggerManager
            category = key.replace("log_level_", "")
            level_map = {"DEBUG": 10, "INFO": 20, "WARNING": 30, "ERROR": 40, "CRITICAL": 50}
            level = level_map.get(str(value).upper(), 20)
            LoggerManager.set_log_level(category, level)
        else:
            logger.info(f"Настройка '{key}={value}' не требует применения к макросам")

    def _update_and_notify(self):
        self._update_macros_dicts()
        self.globalStoppedChanged.emit()

    @Slot()
    def stop_all_macros(self):
        logger.info(f"[STOP_ALL] Начало остановки всех макросов, global_stopped={self._global_stopped}")
        self._global_stopped = True
        self.globalStoppedChanged.emit()
        try:
            if self.mouse_click_monitor:
                self.mouse_click_monitor.pause()
                logger.info("[STOP_ALL] MouseClickMonitor поставлен на паузу")
        except RuntimeError as e:
            logger.debug(f"[STOP_ALL] Ошибка паузы MouseClickMonitor: {e}")
        if self._ocr_running:
            self.stop_ocr()
            logger.info("[STOP_ALL] OCR остановлен")
        for macro in self._macros:
            logger.info(f"[STOP_ALL] Остановка макроса '{macro.name}', running={macro.running}")
            macro.stop()
        for macro in self._macros:
            if macro.thread and macro.thread.is_alive():
                logger.debug(f"[STOP_ALL] Ожидание завершения '{macro.name}'...")
                macro.thread.join(timeout=3.0)
                if macro.thread.is_alive():
                    logger.warning(f"[STOP_ALL] Поток '{macro.name}' не завершился за 3с")
        logger.info(f"[STOP_ALL] Все макросы остановлены")
        for macro in self._macros:
            macro.running = False
        for macro in self._macros:
            if macro.hotkey:
                logger.info(f"[STOP_ALL] Перерегистрация hotkey '{macro.hotkey}' для макроса '{macro.name}' с suppress=False")
                self.unregister_hotkey(macro.hotkey)
                def make_callback(m):
                    def callback(e):
                        logger.debug(f"Горячая клавиша '{m.hotkey}' нажата, но макросы остановлены")
                    return callback
                self.register_hotkey(macro.hotkey, make_callback(macro), check_window=True, check_global_stop=True, suppress=False)
        self._update_and_notify()
        self.stopAllPressed.emit()
        self.notification.emit(" Все макросы ОСТАНОВЛЕНЫ", "warning")
        play_alert_sound(SOUND_STOP)
        logger.info(f"[STOP_ALL] Завершение остановки всех макросов")

    @Slot()
    def start_all_macros(self):
        import threads
        import time
        logger.info(f"[START_ALL] Начало запуска, global_stopped={self._global_stopped}")
        if not self._global_stopped:
            logger.debug("[START_ALL] Макросы уже запущены, игнорирую повторный вызов")
            return
        if hasattr(self, 'dispatcher') and self.dispatcher:
            try:
                if hasattr(self.dispatcher, 'restart_queue_processor'):
                    self.dispatcher.restart_queue_processor()
                    logger.info("[START_ALL] Диспетчер очереди перезапущен")
            except Exception as e:
                logger.debug(f"[START_ALL] Диспетчер не имеет метода restart_queue_processor, пропускаем: {e}")
        self._global_stopped = False
        self.globalStoppedChanged.emit()
        if hasattr(self, 'dispatcher') and self.dispatcher:
            self.dispatcher._active_macros_clear()
        elif hasattr(self, 'active_macros'):
            self.active_macros.clear()
        self.register_all_hotkeys()
        try:
            if self.mouse_click_monitor:
                self.mouse_click_monitor.resume()
                logger.info("[START_ALL]  MouseClickMonitor возобновлен")
            else:
                self.mouse_click_monitor = threads.MouseClickMonitor(self._target_window_title)
                self.mouse_click_monitor.start()
                logger.info("[START_ALL]  MouseClickMonitor создан и запущен ПЕРВЫЙ РАЗ")
                for macro in self._macros:
                    if hasattr(macro, 'zone_rect') and macro.zone_rect:
                        macro._connect_mouse_click(self)
                        logger.info(f"[START_ALL] Подключён макрос '{macro.name}'")
        except Exception as e:
            logger.error(f"[START_ALL]  Ошибка MouseClickMonitor: {e}", exc_info=True)
        if self._ocr_enabled:
            self.start_ocr()
            logger.info("[START_ALL] OCR reader перезапущен")
        self.startAllPressed.emit()
        self.notification.emit(" Все макросы запущены", "success")
        play_alert_sound(SOUND_START)
        logger.info("[START_ALL] Завершение запуска всех макросов")

    @Slot(str)
    def delete_macro(self, name):
        for macro in self._macros:
            if macro.name == name:
                # Отключаем сигналы мыши для зональных макросов
                if hasattr(macro, '_mouse_click_connected') and macro._mouse_click_connected:
                    try:
                        if hasattr(macro, '_connect_mouse_click'):
                            macro._connect_mouse_click(self)
                            macro._mouse_click_connected = False
                            logger.debug(f"[DELETE] Сигналы мыши для '{name}' отключены")
                    except Exception as e:
                        logger.warning(f"[DELETE] Ошибка отключения сигналов: {e}")
                macro.stop()
                self._macros.remove(macro)
                self.save_macros()
                self._update_macros_dicts()
                self.notification.emit(f"Макрос '{name}' удалён", "warning")
                if macro.hotkey:
                    self.unregister_hotkey(macro.hotkey)
                break

    @Slot(str)
    def edit_macro(self, name):
        for macro in self._macros:
            if macro.name == name:
                self._macro_name_for_edit = name
                logger.debug(f"edit_macro: найден макрос '{name}', открываем редактирование")
                self.pageChangeRequested.emit("MacrosEditPage.qml")
                return
        logger.warning(f"edit_macro: макрос '{name}' не найден")
        self.notification.emit(f"Макрос '{name}' не найден", "error")

    @Slot()
    def create_simple_macro(self):
        self.open_macro_dialog("simple")

    @Slot()
    def create_zone_macro(self):
        self.open_macro_dialog("zone")

    @Slot()
    def create_skill_macro(self):
        self.open_macro_dialog("skill")

    @Slot()
    def create_buff_macro(self):
        self.open_macro_dialog("buff")

    @Slot(str)
    def load_profile(self, name):
        if not name:
            self.notification.emit(" Введите имя профиля", "warning")
            return
        if self._current_profile and self._current_profile != name:
            logger.info(f"[PROFILE] Сохранение текущего профиля '{self._current_profile}' перед загрузкой '{name}'...")
            self.save_profile(self._current_profile)
        profile_path = os.path.join(self.profiles_dir, f"{name}.json")
        if not os.path.exists(profile_path):
            self.notification.emit(f" Профиль '{name}' не найден", "error")
            return
        try:
            with open(profile_path, 'r', encoding='utf-8') as f:
                profile_data = json.load(f)
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
            logger.info(f"[PROFILE] Окно: locked={self._window_locked}, title={self._target_window_title}")
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
                    logger.info("[PROFILE] OCR запущен с областями из профиля")
                else:
                    self.stop_ocr()
                    self.start_ocr()
                    logger.info("[PROFILE] OCR перезапущен с новыми областями из профиля")
            self.register_all_hotkeys()
            self.notification.emit(f" Профиль '{name}' загружен", "success")
            logger.info(f"[PROFILE] Загружен профиль: {name}, макросов: {len(self._macros)}")
        except Exception as e:
            logger.error(f"[PROFILE] Ошибка загрузки профиля: {e}", exc_info=True)
            self.notification.emit(f" Ошибка загрузки: {e}", "error")

    def _apply_settings_to_attributes(self):
        logger.info("[PROFILE] Применение настроек к атрибутам backend...")
        self.castbar_enabled = self._settings.get("castbar_enabled", False)
        self.castbar_point = self._settings.get("castbar_point", "1273,1005")
        castbar_color = self._settings.get("castbar_color", [94, 123, 104])
        self.castbar_color = self._load_castbar_color(castbar_color)
        threshold = self._settings.get("castbar_threshold", 70)
        self.castbar_threshold = int(threshold) if isinstance(threshold, (int, float)) else 70
        self.mob_area = self._settings.get("mob_area", "1266,32,1303,56")
        self.player_area = self._settings.get("player_area", "1271,16,1294,32")
        self._window_locked = self._settings.get("window_locked", False)
        self._target_window_title = self._settings.get("target_window_title", "")
        if self._window_locked and self._target_window_title:
            try:
                from macros_core import find_window_hwnd, set_game_window_hwnd, set_skip_window_activation
                from backend.input_system import input_system
                game_hwnd = find_window_hwnd(self._target_window_title)
                if game_hwnd:
                    set_game_window_hwnd(game_hwnd)
                    input_system.set_target(game_hwnd)
                    skip_activation = self._settings.get("window_manager_skip_activation", False)
                    set_skip_window_activation(skip_activation)
                    force_si = self._settings.get("force_sendinput", False)
                    input_system.set_use_sendinput(force_si)
                    logger.info(f"[HWND] Окно игры найдено: hwnd={game_hwnd}, skip_activation={skip_activation}, force_sendinput={force_si}")
                else:
                    logger.warning(f"[HWND] Окно '{self._target_window_title}' не найдено")
            except Exception as e:
                logger.debug(f"[HWND] Ошибка установки hwnd: {e}")
        self._ping = self._settings.get("average_ping", 30)
        self._target_distance = None
        self.settingsChanged.emit()
        self.pingUpdated.emit(self._ping)

    @Slot(str)
    def create_profile(self, name):
        if not name:
            self.notification.emit(" Введите имя профиля", "warning")
            return
        clean_name = re.sub(r'[<>:"/\\|?*]', '', name.strip())
        clean_name = re.sub(r'[\x00-\x1f\x7f]', '', clean_name)
        clean_name = clean_name.rstrip('. ')
        if not clean_name:
            self.notification.emit(" Имя профиля не может содержать только специальные символы", "warning")
            return
        profile_path = os.path.join(self.profiles_dir, f"{clean_name}.json")
        if os.path.exists(profile_path):
            self.notification.emit(f" Профиль '{clean_name}' уже существует", "warning")
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
            self.notification.emit(f" Профиль '{clean_name}' создан", "success")
            logger.info(f"[PROFILE] Создан профиль: {clean_name}")
        except Exception as e:
            logger.error(f"[PROFILE] Ошибка создания профиля: {e}", exc_info=True)
            self.notification.emit(f" Ошибка создания: {e}", "error")

    @Slot(str, str)
    def rename_profile(self, old_name, new_name):
        if not old_name or not new_name:
            self.notification.emit(" Неверное имя профиля", "warning")
            return
        clean_name = re.sub(r'[<>:"/\\|?*]', '', new_name.strip())
        clean_name = re.sub(r'[\x00-\x1f\x7f]', '', clean_name)
        clean_name = clean_name.rstrip('. ')
        if not clean_name:
            self.notification.emit(" Имя профиля не может содержать только специальные символы", "warning")
            return
        if clean_name == old_name:
            self.notification.emit(" Имя не изменилось", "info")
            return
        old_path = os.path.join(self.profiles_dir, f"{old_name}.json")
        new_path = os.path.join(self.profiles_dir, f"{clean_name}.json")
        if not os.path.exists(old_path):
            self.notification.emit(f" Профиль '{old_name}' не найден", "error")
            return
        if os.path.exists(new_path):
            self.notification.emit(f" Профиль '{clean_name}' уже существует", "warning")
            return
        try:
            os.rename(old_path, new_path)
            self._current_profile = clean_name
            self._settings["last_active_profile"] = clean_name
            self.profileChanged.emit()
            self.profilesChanged.emit()
            self.save_settings()
            self.notification.emit(f" Профиль переименован в '{clean_name}'", "success")
            logger.info(f"[PROFILE] Профиль '{old_name}' переименован в '{clean_name}'")
        except Exception as e:
            logger.error(f"[PROFILE] Ошибка переименования профиля: {e}", exc_info=True)
            self.notification.emit(f" Ошибка переименования: {e}", "error")

    @Slot(str)
    def save_profile(self, name=None):
        if name is None:
            name = self._current_profile
        if not name:
            self.notification.emit(" Введите имя профиля", "warning")
            return
        clean_name = re.sub(r'[<>:"/\\|?*]', '', name.strip())
        clean_name = re.sub(r'[\x00-\x1f\x7f]', '', clean_name)
        clean_name = clean_name.rstrip('. ')
        if not clean_name:
            self.notification.emit(" Имя профиля не может содержать только специальные символы", "warning")
            return
        try:
            logger.info(f"[PROFILE] Сохранение профиля '{clean_name}': макросов={len(self._macros)}, настроек={len(self._settings)}")
            profile_data = {
                "settings": dict(self._settings),
                "macros": [self._macro_to_dict(m) for m in self._macros],
                "window_locked": self._settings.get("window_locked", False),
                "target_window_title": self._settings.get("target_window_title", "")
            }
            logger.info(f"[PROFILE] Сериализовано макросов: {len(profile_data['macros'])}")
            profile_path = os.path.join(self.profiles_dir, f"{clean_name}.json")
            with open(profile_path, 'w', encoding='utf-8') as f:
                json.dump(profile_data, f, ensure_ascii=False, indent=2)
            self._current_profile = clean_name
            self.profileChanged.emit()
            self.profilesChanged.emit()
            self.notification.emit(f" Профиль '{clean_name}' сохранён", "success")
            logger.info(f"[PROFILE] Сохранён профиль: {clean_name}")
        except Exception as e:
            logger.error(f"[PROFILE] Ошибка сохранения профиля: {e}", exc_info=True)
            self.notification.emit(f" Ошибка сохранения: {e}", "error")

    @Slot(str)
    def delete_profile(self, name=None):
        if name is None:
            name = self._current_profile
        if not name:
            self.notification.emit(" Профиль не выбран", "warning")
            return
        profile_path = os.path.join(self.profiles_dir, f"{name}.json")
        if not os.path.exists(profile_path):
            self.notification.emit(f" Профиль '{name}' не найден", "error")
            return
        try:
            os.remove(profile_path)
            if self._current_profile == name:
                self._current_profile = None
                self.profileChanged.emit()
            self.profilesChanged.emit()
            self.notification.emit(f" Профиль '{name}' удалён", "success")
            logger.info(f"[PROFILE] Удалён профиль: {name}")
        except Exception as e:
            logger.error(f"[PROFILE] Ошибка удаления профиля: {e}", exc_info=True)
            self.notification.emit(f" Ошибка удаления: {e}", "error")

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

    def _create_macro_from_dict(self, data):
        try:
            macro_type = data.get("type", "simple")
            macro = None
            if macro_type == "simple":
                from macros import SimpleMacro
                macro = SimpleMacro(
                    name=data.get("name", "Макрос"),
                    app=self,
                    hotkey=data.get("hotkey", ""),
                    steps=data.get("steps", [])
                )
            elif macro_type == "skill":
                from macros import SkillMacro
                macro = SkillMacro(
                    name=data.get("name", "Скилл"),
                    app=self,
                    hotkey=data.get("hotkey", ""),
                    skill_id=data.get("skill_id", 0),
                    cooldown=data.get("cooldown", 3.0),
                    skill_range=data.get("skill_range", 10.0),
                    cast_time=data.get("cast_time", 0.5),
                    steps=data.get("steps", []),
                    castbar_swap_delay=data.get("castbar_swap_delay", 0)
                )
                if data.get("zone_rect"):
                    macro.zone_rect = tuple(data["zone_rect"])
                    macro._connect_mouse_click(self)
                    logger.info(f"[SKILL+ZONE] Макрос '{macro.name}' загружен с областью {macro.zone_rect}, подписка={macro._mouse_click_connected}")
            elif macro_type == "zone":
                from macros import ZoneMacro
                macro = ZoneMacro(
                    name=data.get("name", "Зона"),
                    app=self,
                    hotkey=data.get("hotkey", ""),
                    zone_rect=tuple(data.get("zone_rect", [0, 0, 0, 0])),
                    steps=data.get("steps", []),
                    poll_interval=data.get("poll_interval", 10)
                )
            elif macro_type == "buff":
                from macros import BuffMacro
                zone_rect = data.get("zone_rect")
                macro = BuffMacro(
                    name=data.get("name", "Бафф"),
                    app=self,
                    hotkey=data.get("hotkey", ""),
                    buff_id=data.get("buff_id", 0),
                    duration=data.get("duration", 60.0),
                    channeling_bonus=data.get("channeling_bonus", 0),
                    steps=data.get("steps", []),
                    icon=data.get("icon", "buff.png")
                )
                if zone_rect and len(zone_rect) == 4:
                    macro.zone_rect = zone_rect
                    macro._connect_mouse_click(self)
                    logger.info(f"[BUFF+ZONE] Бафф '{macro.name}' загружен с областью {macro.zone_rect}")
            return macro
        except Exception as e:
            logger.error(f"[PROFILE] Ошибка создания макроса: {e}", exc_info=True)
            return None

    def _macro_to_dict(self, macro):
        try:
            logger.debug(f"[PROFILE] Сериализация макроса: {macro.name} (type={macro.type})")
            data = {
                "type": macro.type,
                "name": macro.name,
                "hotkey": macro.hotkey or "",
                "steps": macro.steps
            }
            if macro.type == "skill":
                data["skill_id"] = macro.skill_id
                data["cooldown"] = macro.cooldown
                data["skill_range"] = macro.skill_range
                data["cast_time"] = macro.cast_time
                data["castbar_swap_delay"] = macro.castbar_swap_delay
                if macro.zone_rect:
                    data["zone_rect"] = list(macro.zone_rect)
            elif macro.type == "buff":
                data["buff_id"] = macro.buff_id
                data["duration"] = macro.duration
                data["channeling_bonus"] = macro.channeling_bonus
                if macro.zone_rect:
                    data["zone_rect"] = list(macro.zone_rect)
            elif macro.type == "zone":
                data["trigger"] = getattr(macro, 'trigger', 'left_click')
                data["poll_interval"] = getattr(macro, 'poll_interval', 10)
                if macro.zone_rect:
                    data["zone_rect"] = list(macro.zone_rect)
            return data
        except Exception as e:
            logger.error(f"[PROFILE] Ошибка сериализации макроса: {e}", exc_info=True)
            return {}

    def open_macro_dialog(self, macro_type):
        if macro_type == "simple" and self.engine:
            try:
                qml_file = os.path.join(self.app_dir, "qml", "SimpleMacroDialog.qml")
                from PySide6.QtCore import QUrl
                from PySide6.QtQml import QQmlComponent
                component = QQmlComponent(self.engine, QUrl.fromLocalFile(qml_file))
                if component.isReady():
                    dialog = component.create()
                    if dialog:
                        dialog.open()
                else:
                    self.notification.emit("Ошибка загрузки диалога", "error")
            except Exception as e:
                logger.error(f"Ошибка открытия диалога: {e}", exc_info=True)
                self.notification.emit(f"Ошибка: {e}", "error")
        else:
            self.notification.emit(f"Создание макроса типа {macro_type} (в разработке)", "info")

    @Slot(str, str, list)
    def create_simple_macro_with_params(self, name, hotkey, steps):
        try:
            import macros
            macro = macros.SimpleMacro(name, steps, self, hotkey if hotkey else "")
            self._macros.append(macro)
            self.save_macros()
            self._update_macros_dicts()
            self.notification.emit(f"Макрос '{name}' создан", "success")
        except Exception as e:
            logger.error(f"Ошибка создания макроса: {e}", exc_info=True)
            self.notification.emit(f"Ошибка создания макроса: {e}", "error")

    @Slot(str, str, list, list, str, int)
    def create_zone_macro_with_params(self, name, hotkey, zone_rect, steps, trigger, poll_interval_ms):
        try:
            import macros
            poll_interval = poll_interval_ms / 1000.0
            macro = macros.ZoneMacro(name, zone_rect, steps, self, trigger=trigger)
            if zone_rect and len(zone_rect) == 4:
                macro._connect_mouse_click(self)
                logger.info(f"[ZONE] Макрос '{name}' создан с зоной {zone_rect}, подписка={macro._mouse_click_connected}")
            macro.start()
            logger.info(f"[ZONE] Макрос '{name}' запущен")
            self._macros.append(macro)
            self._update_macros_dicts()
            self.macrosChanged.emit()
            return
        except Exception as e:
            logger.error(f"Ошибка создания зонального макроса: {e}", exc_info=True)

    @Slot(str, str, str, list, list, str, int)
    def update_zone_macro(self, old_name, new_name, hotkey, zone_rect, steps, trigger, poll_interval_ms):
        try:
            import macros
            for i, macro in enumerate(self._macros):
                if macro.name == old_name and macro.type == "zone":
                    poll_interval = poll_interval_ms / 1000.0
                    new_macro = macros.ZoneMacro(
                        new_name, zone_rect, steps, self,
                        trigger=trigger,
                        poll_interval=poll_interval,
                        hotkey=hotkey if hotkey else "",
                        skill_id=None, cooldown=0, skill_range=0, cast_time=0, castbar_swap_delay=0
                    )
                    self._macros[i] = new_macro
                    self.save_macros()
                    self._update_macros_dicts()
                    self.notification.emit(f"Зональный макрос '{new_name}' обновлён", "success")
                    return
            self.notification.emit("Макрос не найден", "error")
        except Exception as e:
            logger.error(f"Ошибка обновления зонального макроса: {e}", exc_info=True)
            self.notification.emit(f"Ошибка: {e}", "error")

    @Slot(str, str, str, list)
    def update_simple_macro(self, old_name, new_name, hotkey, steps):
        try:
            import macros
            for i, macro in enumerate(self._macros):
                if macro.name == old_name and macro.type == "simple":
                    new_macro = macros.SimpleMacro(new_name, steps, self, hotkey if hotkey else "")
                    self._macros[i] = new_macro
                    self.save_macros()
                    self._update_macros_dicts()
                    self.notification.emit(f"Макрос '{new_name}' обновлён", "success")
                    return
            self.notification.emit("Макрос не найден", "error")
        except Exception as e:
            logger.error(f"Ошибка обновления макроса: {e}", exc_info=True)
            self.notification.emit(f"Ошибка: {e}", "error")

    @Slot(dict)
    def set_macro_for_edit(self, macro_dict):
        self._macro_name_for_edit = macro_dict["name"]
        self._macro_for_edit = macro_dict
        logger.debug(f"set_macro_for_edit -> name={self._macro_name_for_edit}")

    @Slot(result=dict)
    def get_macro_for_edit(self):
        if not hasattr(self, '_macro_name_for_edit') or not self._macro_name_for_edit:
            logger.debug("get_macro_for_edit -> no name set")
            return None
        name = self._macro_name_for_edit
        logger.debug(f"get_macro_for_edit: searching for macro '{name}'")
        for macro in self._macros:
            if macro.name == name:
                logger.debug(f"found macro: {macro.name}, type={macro.type}")
                result = {
                    "name": macro.name,
                    "type": macro.type,
                    "hotkey": macro.hotkey or "",
                    "steps": macro.steps if hasattr(macro, "steps") else [],
                    "running": macro.running,
                    "cooldown": getattr(macro, "cooldown", 0),
                    "skill_range": getattr(macro, "skill_range", 0),
                }
                if macro.type == "zone":
                    result["zone_rect"] = list(macro.zone_rect) if hasattr(macro, "zone_rect") and macro.zone_rect else []
                    result["trigger"] = macro.trigger if hasattr(macro, "trigger") else "left_click"
                    result["poll_interval"] = macro.poll_interval if hasattr(macro, "poll_interval") else 10
                if macro.type == "skill":
                    result["skill_id"] = macro.skill_id if hasattr(macro, "skill_id") else None
                    result["cooldown"] = macro.cooldown if hasattr(macro, "cooldown") else 0
                    result["skill_range"] = macro.skill_range if hasattr(macro, "skill_range") else 0
                    result["cast_time"] = macro.cast_time if hasattr(macro, "cast_time") else 0.0
                    result["castbar_swap_delay"] = macro.castbar_swap_delay if hasattr(macro, "castbar_swap_delay") else 0
                    result["zone_rect"] = list(macro.zone_rect) if hasattr(macro, "zone_rect") and macro.zone_rect else []
                if macro.type == "buff":
                    result["buff_id"] = macro.buff_id if hasattr(macro, "buff_id") else None
                    result["duration"] = macro.duration if hasattr(macro, "duration") else 0
                    result["channeling_bonus"] = macro.channeling_bonus if hasattr(macro, "channeling_bonus") else 0
                    result["icon"] = macro.icon if hasattr(macro, "icon") else ""
                return result
        logger.debug(f"macro '{name}' not found")
        return None

    @Slot()
    def clear_macro_for_edit(self):
        self._macro_name_for_edit = None
        self._macro_for_edit = None
        self.macrosChanged.emit()

    def save_macro(self, macro_dict):
        try:
            self._validate_macro_dict(macro_dict)
            name = macro_dict.get("name", "")
            hotkey = macro_dict.get("hotkey", "")
            if not name:
                self.notification.emit("Имя макроса не может быть пустым", "error")
                return
            old_name = macro_dict.get("old_name", name)
            existing_macro = None
            for m in self._macros:
                if m.name == old_name:
                    existing_macro = m
                    break
            new_macro = self._create_macro_from_dict(macro_dict)
            if new_macro is None:
                self.notification.emit("Не удалось создать макрос", "error")
                return
            new_macro.hotkey = hotkey if hotkey else ""

            if existing_macro:
                if existing_macro.hotkey and existing_macro.hotkey != hotkey:
                    self.unregister_hotkey(existing_macro.hotkey)
                index = self._macros.index(existing_macro)
                self._macros[index] = new_macro
                self.notification.emit(f"Макрос '{name}' обновлён", "success")
            else:
                for existing_m in self._macros:
                    if existing_m.hotkey == hotkey:
                        logger.debug(f"Горячая клавиша '{hotkey}' уже используется макросом '{existing_m.name}', удаляем")
                        self.unregister_hotkey(hotkey)
                        existing_m.hotkey = None
                        break
                self._macros.append(new_macro)
                self.notification.emit(f"Макрос '{name}' создан", "success")
            if hotkey:
                for existing_m in self._macros:
                    if existing_m.hotkey == hotkey and existing_m != new_macro:
                        logger.debug(f"Горячая клавиша '{hotkey}' уже используется макросом '{existing_m.name}', удаляем")
                        self.unregister_hotkey(hotkey)
                        break
                def make_callback(m):
                    def callback(e=None):
                        if not m.running:
                            if not self.dispatcher.request_macro(m):
                                logger.warning(f" '{m.name}': ЗАБЛОКИРОВАНО диспетчером")
                                return
                            logger.info(f" '{m.name}': ЗАПУЩЕН через hotkey")
                        else:
                            logger.debug(f"[HOTKEY] '{m.name}': уже выполняется, игнорируем")
                    return callback
                self.register_hotkey(hotkey, make_callback(new_macro))
            self.save_macros()
            self._update_macros_dicts()
        except Exception as e:
            logger.error(f"Ошибка сохранения макроса: {e}", exc_info=True)
            self.notification.emit(f"Ошибка: {e}", "error")

    @Slot(str, dict)
    def create_macro_from_dict(self, macro_type, macro_dict):
        macro_dict["type"] = macro_type
        self.save_macro(macro_dict)

    @Slot(str, str, str, list, str, float, float, float, float, list)
    def create_skill_macro_with_params(self, name, hotkey, skill_id, steps, skill_hotkey,
                                       cooldown, skill_range, cast_time, castbar_swap_delay, zone_rect):
        import macros
        try:
            logger.debug(f"create_skill_macro_with_params: name={name}, skill_id={skill_id}, skill_hotkey={skill_hotkey}, zone_rect={zone_rect}")
            icon = ""
            if skill_id:
                skill = self.skill_db.get_skill(int(skill_id))
                if skill:
                    icon = skill.icon
            macro_hotkey = skill_hotkey if not hotkey else hotkey
            logger.debug(f"macro_hotkey={macro_hotkey}, hotkey={hotkey}, skill_hotkey={skill_hotkey}")
            macro = macros.SkillMacro(name, steps, self, macro_hotkey if macro_hotkey else "",
                skill_id=int(skill_id) if skill_id else None, cooldown=cooldown,
                skill_range=skill_range, cast_time=cast_time, castbar_swap_delay=castbar_swap_delay)
            macro.icon = icon
            logger.debug(f"Макрос создан: name={name}, hotkey={macro.hotkey}, icon={icon}")
            if zone_rect and len(zone_rect) == 4:
                macro.zone_rect = zone_rect
                macro._connect_mouse_click(self)
                logger.info(f"[SKILL+ZONE] Макрос '{name}' создан с областью {zone_rect}, подписка={macro._mouse_click_connected}")
            else:
                logger.debug(f"[SKILL+ZONE] Макрос '{name}' создан без зоны (обычный скилл-макрос)")
            self._macros.append(macro)
            self.save_macros()
            self._update_macros_dicts()
            if macro_hotkey:
                def make_callback(m):
                    def callback(e=None):
                        logger.debug(f"Горячая клавиша '{m.hotkey}' нажата, макрос '{m.name}'")
                        if time.time() < self.dispatcher.cast_lock_until:
                            logger.debug(f"[CAST LOCK] Горячая клавиша '{m.hotkey}' ЗАБЛОКИРОВАНА: идёт каст")
                            return
                        if not m.running:
                            if not self.dispatcher.request_macro(m):
                                logger.debug(f" '{m.name}': ЗАБЛОКИРОВАНО диспетчером")
                                return
                    return callback
                self.register_hotkey(macro_hotkey, make_callback(macro))
                logger.debug(f"Горячая клавиша '{macro_hotkey}' зарегистрирована для макроса '{name}'")
            self.notification.emit(f"Скилл-макрос '{name}' создан", "success")
        except Exception as e:
            logger.error(f"Ошибка создания скилл-макроса: {e}", exc_info=True)
            self.notification.emit(f"Ошибка: {e}", "error")

    @Slot(str, str, str, str, list, str, float, float, float, float, list)
    def update_skill_macro(self, old_name, new_name, hotkey, skill_id, steps, skill_hotkey,
                           cooldown, skill_range, cast_time, castbar_swap_delay, zone_rect):
        import macros
        try:
            icon = ""
            if skill_id:
                skill = self.skill_db.get_skill(int(skill_id))
                if skill:
                    icon = skill.icon
            for i, macro in enumerate(self._macros):
                if macro.name == old_name and macro.type == "skill":
                    new_macro = macros.SkillMacro(new_name, steps, self, hotkey if hotkey else "",
                        skill_id=int(skill_id) if skill_id else None, cooldown=cooldown,
                        skill_range=skill_range, cast_time=cast_time, castbar_swap_delay=castbar_swap_delay)
                    new_macro.icon = icon
                    if zone_rect and len(zone_rect) == 4:
                        new_macro.zone_rect = zone_rect
                        logger.info(f"[SKILL+ZONE] Макрос '{new_name}' обновлён с НОВОЙ областью {zone_rect}")
                    else:
                        new_macro.zone_rect = None
                        logger.info(f"[SKILL+ZONE] Макрос '{new_name}' обновлён БЕЗ области (обычный)")
                    if hasattr(new_macro, 'zone_rect') and new_macro.zone_rect:
                        new_macro._connect_mouse_click(self)
                        logger.info(f"[SKILL+ZONE] Макрос '{new_name}' подписан на клики, зона={new_macro.zone_rect}")
                    self._macros[i] = new_macro
                    self.save_macros()
                    self._update_macros_dicts()
                    self.notification.emit(f"Скилл-макрос '{new_name}' обновлён", "success")
                    return
            self.notification.emit("Макрос не найден", "error")
        except Exception as e:
            logger.error(f"Ошибка обновления скилл-макроса: {e}", exc_info=True)
            self.notification.emit(f"Ошибка: {e}", "error")

    @Slot(str, str, str, list, float, int, list)
    def create_buff_macro_with_params(self, name, hotkey, buff_id, steps, duration, channeling_bonus, zone_rect):
        import macros
        try:
            logger.debug(f"create_buff_macro_with_params: name={name}, buff_id={buff_id}")
            icon = ""
            if buff_id:
                buff = self.skill_db.get_buff(int(buff_id))
                if buff:
                    icon = buff.icon
            macro = macros.BuffMacro(name, steps, self,
                buff_id=int(buff_id) if buff_id else None, duration=duration,
                channeling_bonus=channeling_bonus, hotkey=hotkey if hotkey else "",
                icon=icon if icon else "buff.png")
            if zone_rect and len(zone_rect) == 4:
                macro.zone_rect = zone_rect
            if self._settings.get("use_ping_delays", False):
                ping_comp = self.get_ping_compensation() * 1000
                for i, step in enumerate(macro.steps):
                    if step[0] == "key":
                        macro.steps[i] = [step[0], step[1], round(ping_comp)]
                logger.info(f"[BUFF] Задержки пересчитаны: ping_comp={ping_comp}мс")
            self._macros.append(macro)
            self.save_macros()
            self._update_macros_dicts()
            if macro.hotkey:
                self.register_all_hotkeys()
                logger.info(f"[BUFF] Горячая клавиша '{macro.hotkey}' зарегистрирована для бафф-макроса '{macro.name}'")
            self.notification.emit(f"Бафф-макрос '{name}' создан", "success")
        except Exception as e:
            logger.error(f"Ошибка создания бафф-макроса: {e}", exc_info=True)
            self.notification.emit(f"Ошибка: {e}", "error")

    @Slot(str, str, str, str, list, float, int, list)
    def update_buff_macro(self, old_name, new_name, hotkey, buff_id, steps, duration, channeling_bonus, zone_rect):
        import macros
        try:
            icon = ""
            if buff_id:
                buff = self.skill_db.get_buff(int(buff_id))
                if buff:
                    icon = buff.icon
            for i, macro in enumerate(self._macros):
                if macro.name == old_name and macro.type == "buff":
                    new_macro = macros.BuffMacro(new_name, steps, self,
                        buff_id=int(buff_id) if buff_id else None, duration=duration,
                        channeling_bonus=channeling_bonus, hotkey=hotkey if hotkey else "",
                        icon=icon if icon else "buff.png")
                    if zone_rect and len(zone_rect) == 4:
                        new_macro.zone_rect = zone_rect
                        logger.info(f"[BUFF+ZONE] Бафф '{new_name}' обновлён с НОВОЙ областью {zone_rect}")
                    else:
                        new_macro.zone_rect = None
                        logger.info(f"[BUFF+ZONE] Бафф '{new_name}' обновлён БЕЗ области")
                    if hasattr(new_macro, 'zone_rect') and new_macro.zone_rect:
                        new_macro._connect_mouse_click(self)
                        logger.info(f"[BUFF+ZONE] Бафф '{new_name}' подписан на клики, зона={new_macro.zone_rect}")
                    if self._settings.get("use_ping_delays", False):
                        ping_comp = self.get_ping_compensation() * 1000
                        for i, step in enumerate(new_macro.steps):
                            if step[0] == "key":
                                new_macro.steps[i] = [step[0], step[1], round(ping_comp)]
                        logger.info(f"[BUFF] Задержки обновлены: ping_comp={ping_comp}мс")
                    self._macros[i] = new_macro
                    self.save_macros()
                    self._update_macros_dicts()
                    self.register_all_hotkeys()
                    logger.info(f"[BUFF] Горячая клавиша '{new_macro.hotkey}' перерегистрирована для бафф-макроса '{new_macro.name}'")
                    self.notification.emit(f"Бафф-макрос '{new_name}' обновлён", "success")
                    return
            self.notification.emit("Макрос не найден", "error")
        except Exception as e:
            logger.error(f"Ошибка обновления бафф-макроса: {e}", exc_info=True)
            self.notification.emit(f"Ошибка: {e}", "error")

    @Slot()
    def selectAreaForMacro(self):
        if not self.engine:
            return
        from utils.resource_utils import resource_path
        qml_file = resource_path("qml/ZoneAreaSelector.qml")
        if not qml_file or not os.path.exists(qml_file):
            self.notification.emit("Файл ZoneAreaSelector.qml не найден", "error")
            return
        from PySide6.QtCore import QUrl
        from PySide6.QtQml import QQmlComponent
        component = QQmlComponent(self.engine, QUrl.fromLocalFile(qml_file))
        if component.isReady():
            window = component.create()
            if window:
                window.zoneAreaSelected.connect(self.onZoneAreaSelected)
                window.cancelled.connect(lambda: self.notification.emit("Выбор области отменён", "info"))
                window.show()
                logger.info("ZoneAreaSelector window created and shown")
            else:
                self.notification.emit("Не удалось создать окно выбора области", "error")
        else:
            error_str = component.errorString()
            logger.error(f"ZoneAreaSelector load error: {error_str}", exc_info=True)
            self.notification.emit("Ошибка загрузки ZoneAreaSelector.qml: " + error_str, "error")

    @Slot(int, int, int, int)
    def onZoneAreaSelected(self, x1, y1, x2, y2):
        self.zoneAreaSelectedSignal.emit([x1, y1, x2, y2])
        self.notification.emit(f"Зона выбрана: {x1},{y1},{x2},{y2}", "success")
