"""MacroMixins — разделение MacroMixin на 3 миксина согласно [[04-backend-macros]].

MacroStorageMixin  — хранение и сериализация (load/save, dicts, settings→macros)
MacroCRUDMixin     — CRUD операции (create/update/delete/edit) — делегирует в MacroCrud
MacroExecutionMixin — start/stop всех макросов, управление жизненным циклом
"""

import json
import os
import re
import threading
import time
from typing import Optional

from PySide6.QtCore import Slot, QUrl
from PySide6.QtQml import QQmlComponent
from PySide6.QtWidgets import QFileDialog

from backend.logger_manager import get_logger
from constants import ALLOWED_SETTINGS
from utils.sound_alert import play_alert_sound, SOUND_START, SOUND_STOP

logger = get_logger('backend')


class MacroStorageMixin:
    """Хранение макросов, сериализация, реакция на изменение настроек."""

    def _get_crud(self):
        if not hasattr(self, '_macro_crud') or self._macro_crud is None:
            from backend.macro_crud import MacroCrud
            self._macro_crud = MacroCrud(self)
        return self._macro_crud

    def _create_macro_from_dict(self, data: dict):
        return self._get_crud()._create_macro_from_dict(data)

    def _macro_to_dict(self, macro):
        return self._get_crud()._macro_to_dict(macro)

    def _validate_macro_dict(self, m_dict: dict):
        return self._get_crud()._validate_macro_dict(m_dict)

    def _update_macros_dicts(self):
        new_list = []
        for macro in self._macros:
            item = {
                "name": macro.name,
                "type": macro.type,
                "hotkey": macro.hotkey or "",
                "running": macro.running.is_set(),
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
            level = LoggerManager.set_log_level(category, level_map.get(str(value).upper(), 20))
        else:
            logger.info(f"Настройка '{key}={value}' не требует применения к макросам")

    def _apply_settings_to_attributes(self):
        """Применяет настройки к атрибутам backend'а. Вызывается из settings_mixin.load_settings."""
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
                    logger.info(f"[HWND] HWND игры установлен: hwnd={game_hwnd}, skip_activation={skip_activation}, force_sendinput={force_si}")
                else:
                    logger.warning(f"[HWND] Окно '{self._target_window_title}' не найдено")
            except Exception as e:
                logger.debug(f"[HWND] Ошибка установки hwnd: {e}")
        self._ping = self._settings.get("average_ping", 30)
        self._target_distance = None
        self.settingsChanged.emit()
        self.pingUpdated.emit(self._ping)


class MacroExecutionMixin:
    """Запуск/остановка макросов, управление жизненным циклом."""

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
            logger.info(f"[STOP_ALL] Остановка макроса '{macro.name}', running={macro.running.is_set()}")
            macro.stop()
        for macro in self._macros:
            if macro.thread and macro.thread.is_alive():
                logger.debug(f"[STOP_ALL] Ожидание завершения '{macro.name}'...")
                macro.thread.join(timeout=3.0)
                if macro.thread.is_alive():
                    logger.warning(f"[STOP_ALL] Поток '{macro.name}' не завершился за 3с")
        logger.info(f"[STOP_ALL] Все макросы остановлены")
        for macro in self._macros:
            macro.running.clear()
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

    @Slot()
    def selectAreaForMacro(self):
        if not self.engine:
            return
        from utils.resource_utils import resource_path
        qml_file = resource_path("qml/ZoneAreaSelector.qml")
        if not qml_file or not os.path.exists(qml_file):
            self.notification.emit("Файл ZoneAreaSelector.qml не найден", "error")
            return
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


class MacroCRUDMixin:
    """CRUD-операции — прокси для MacroCrud. Реальная логика в backend/macro_crud.py."""

    def _get_crud(self):
        if not hasattr(self, '_macro_crud') or self._macro_crud is None:
            from backend.macro_crud import MacroCrud
            self._macro_crud = MacroCrud(self)
        return self._macro_crud

    @Slot(int)
    def edit_macro_by_index(self, index: int):
        """Один Slot для QML: открывает MacrosEditPage с заполненным editingMacro.
        Обходит проблему scope в onClicked вложенных кнопок И Property binding timing —
        передаёт dict напрямую через сигнал editMacroRequested."""
        logger.info(f"[EDIT] edit_macro_by_index: index={index}, total={len(self._macros)}")
        if not (0 <= index < len(self._macros)):
            self.notification.emit(f"Макрос #{index} не найден", "error")
            return
        macro = self._macros[index]
        logger.info(f"[EDIT] macro={macro.name!r} type={macro.type!r}")
        # Подготовим dict с данными макроса
        macro_dict = self._get_crud().get_macro_for_edit_by_macro(macro)
        # Сохраняем в backend для Property (для других мест, если используется)
        self._get_crud().set_macro_for_edit(macro_dict)
        logger.info(f"[EDIT] set_macro_for_edit done: name={macro_dict.get('name') if macro_dict else None}")
        # Эмитим НОВЫЙ сигнал — данные передаются как аргумент, минуя Property binding timing
        logger.info(f"[EDIT] emitting editMacroRequested('MacrosEditPage.qml', dict with name={macro_dict.get('name')!r}, type={macro_dict.get('type')!r})")
        self.editMacroRequested.emit("MacrosEditPage.qml", macro_dict)

    @Slot(int)
    def delete_macro_by_index(self, index: int):
        """Один Slot для QML: удаление макроса по индексу."""
        if not (0 <= index < len(self._macros)):
            return
        self.delete_macro(self._macros[index].name)

    @Slot(str)
    def delete_macro(self, name):
        self._get_crud().delete_macro(name)

    @Slot(str)
    def edit_macro(self, name):
        self._get_crud().edit_macro(name)

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

    @Slot(str, str, list)
    def create_simple_macro_with_params(self, name, hotkey, steps):
        self._get_crud().create_simple(name, hotkey, steps)

    @Slot(str, str, list, list, str, int)
    def create_zone_macro_with_params(self, name, hotkey, zone_rect, steps, trigger, poll_interval_ms):
        self._get_crud().create_zone(name, hotkey, zone_rect, steps, trigger, poll_interval_ms)

    @Slot(str, str, str, list, list, str, int)
    def update_zone_macro(self, old_name, new_name, hotkey, zone_rect, steps, trigger, poll_interval_ms):
        self._get_crud().update_zone(old_name, new_name, hotkey, zone_rect, steps, trigger, poll_interval_ms)

    @Slot(str, str, str, list)
    def update_simple_macro(self, old_name, new_name, hotkey, steps):
        self._get_crud().update_simple(old_name, new_name, hotkey, steps)

    @Slot(str, str, str, list, str, float, float, float, float, list)
    def create_skill_macro_with_params(self, name, hotkey, skill_id, steps, skill_hotkey,
                                       cooldown, skill_range, cast_time, castbar_swap_delay, zone_rect):
        self._get_crud().create_skill(name, hotkey, skill_id, steps, skill_hotkey,
                                      cooldown, skill_range, cast_time, castbar_swap_delay, zone_rect)

    @Slot(str, str, str, str, list, str, float, float, float, float, list)
    def update_skill_macro(self, old_name, new_name, hotkey, skill_id, steps, skill_hotkey,
                           cooldown, skill_range, cast_time, castbar_swap_delay, zone_rect):
        self._get_crud().update_skill(old_name, new_name, hotkey, skill_id, steps, skill_hotkey,
                                      cooldown, skill_range, cast_time, castbar_swap_delay, zone_rect)

    @Slot(str, str, str, list, float, int, list)
    def create_buff_macro_with_params(self, name, hotkey, buff_id, steps, duration, channeling_bonus, zone_rect):
        self._get_crud().create_buff(name, hotkey, buff_id, steps, duration, channeling_bonus, zone_rect)

    @Slot(str, str, str, str, list, float, int, list)
    def update_buff_macro(self, old_name, new_name, hotkey, buff_id, steps, duration, channeling_bonus, zone_rect):
        self._get_crud().update_buff(old_name, new_name, hotkey, buff_id, steps, duration, channeling_bonus, zone_rect)

    @Slot(dict)
    def set_macro_for_edit(self, macro_dict):
        self._get_crud().set_macro_for_edit(macro_dict)

    @Slot(result=dict)
    def get_macro_for_edit(self):
        return self._get_crud().get_macro_for_edit()

    @Slot()
    def clear_macro_for_edit(self):
        self._get_crud().clear_macro_for_edit()

    @Slot(dict)
    def save_macro(self, macro_dict):
        self._get_crud().save_macro(macro_dict)

    @Slot(str, dict)
    def create_macro_from_dict(self, macro_type, macro_dict):
        macro_dict["type"] = macro_type
        self._get_crud().save_macro(macro_dict)

    def open_macro_dialog(self, macro_type):
        if macro_type == "simple" and self.engine:
            try:
                qml_file = os.path.join(self.app_dir, "qml", "SimpleMacroDialog.qml")
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

    @Slot(str)
    def qmlLog(self, msg: str):
        """Маршрутизация QML console.log в Python logger (видно в snbld_backend.log)."""
        logger.info(f"[QML] {msg}")


# Сохранение обратной совместимости: MacroMixin теперь просто набор миксинов
class MacroMixin(MacroStorageMixin, MacroCRUDMixin, MacroExecutionMixin):
    pass
