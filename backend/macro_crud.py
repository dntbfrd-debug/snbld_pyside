"""MacroCrud — операции CRUD над макросами.

Согласно [[04-backend-macros]]: Backend делегирует все операции над макросами
сюда, а не держит логику в себе. Это разделение:
- MacroStorageMixin — хранилище (_macros, save/load JSON, _macros_dicts)
- MacroCRUDMixin — create/update/delete/edit, hotkeys
- MacroExecutionMixin — start/stop/start_all/stop_all
- SettingsMixin — apply_settings_to_macros (миграция)
"""

import json
import os
import re
import threading
import time
import heapq
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from backend.logger_manager import get_logger

if TYPE_CHECKING:
    from macros_core import Macro

logger = get_logger('backend')


@dataclass
class CreateSimpleParams:
    name: str
    hotkey: str
    steps: list


@dataclass
class CreateZoneParams:
    name: str
    hotkey: str
    zone_rect: list
    steps: list
    trigger: str
    poll_interval_ms: int


@dataclass
class CreateSkillParams:
    name: str
    hotkey: str
    skill_id: str
    steps: list
    skill_hotkey: str
    cooldown: float
    skill_range: float
    cast_time: float
    castbar_swap_delay: float
    zone_rect: list


@dataclass
class CreateBuffParams:
    name: str
    hotkey: str
    buff_id: str
    steps: list
    duration: float
    channeling_bonus: int
    zone_rect: list


class MacroCrud:
    """CRUD-операции над макросами.

    Зависит от Backend-миксинов через duck-typing:
    - self._macros : List[Macro]
    - self._macros_dicts : List[dict]
    - self.save_macros() : method
    - self._update_macros_dicts() : method
    - self.macrosChanged : Signal
    - self.notification : Signal(str, str)
    - self.register_hotkey(hotkey, callback) : method
    - self.unregister_hotkey(hotkey) : method
    - self.skill_db : SkillDatabase
    - self._settings : dict
    - self.dispatcher : MacroDispatcher
    - self._macro_name_for_edit : str
    """

    def __init__(self, backend):
        self._backend = backend
        self._lock = threading.RLock()

    def _emit(self, message: str, level: str = "info"):
        try:
            if level == "error":
                logger.error(message)
            else:
                logger.info(message)
            if hasattr(self._backend, 'notification'):
                self._backend.notification.emit(message, level if level in ("error", "warning", "success") else "info")
        except Exception:
            pass

    def _macro_to_dict(self, macro) -> dict:
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

    def _validate_macro_dict(self, m_dict: dict):
        required_fields = ["type", "name", "steps"]
        for field_name in required_fields:
            if field_name not in m_dict:
                raise ValueError(f"Макрос '{m_dict.get('name', 'unknown')}' не содержит обязательного поля '{field_name}'")
        if not isinstance(m_dict["steps"], list):
            raise ValueError(f"Макрос '{m_dict['name']}': 'steps' должен быть списком")
        if m_dict["type"] == "zone":
            if "zone_rect" not in m_dict:
                raise ValueError(f"Зональный макрос '{m_dict['name']}' не содержит 'zone_rect'")
            zone_rect = m_dict["zone_rect"]
            if not isinstance(zone_rect, list) or len(zone_rect) != 4:
                raise ValueError(f"Макрос '{m_dict['name']}': 'zone_rect' должен быть списком из 4 чисел")
            if not all(isinstance(x, (int, float)) for x in zone_rect):
                raise ValueError(f"Макрос '{m_dict['name']}': 'zone_rect' должен содержать только числа")

    def _create_macro_from_dict(self, data: dict):
        try:
            macro_type = data.get("type", "simple")
            macro = None
            if macro_type == "simple":
                from macros import SimpleMacro
                macro = SimpleMacro(
                    name=data.get("name", "Макрос"),
                    app=self._backend,
                    hotkey=data.get("hotkey", ""),
                    steps=data.get("steps", [])
                )
            elif macro_type == "skill":
                from macros import SkillMacro
                macro = SkillMacro(
                    name=data.get("name", "Скилл"),
                    app=self._backend,
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
                    macro._connect_mouse_click(self._backend)
                    logger.info(f"[CRUD] Skill '{macro.name}' загружен с зоной {macro.zone_rect}")
            elif macro_type == "zone":
                from macros import ZoneMacro
                macro = ZoneMacro(
                    name=data.get("name", "Зона"),
                    app=self._backend,
                    hotkey=data.get("hotkey", ""),
                    zone_rect=tuple(data.get("zone_rect", [0, 0, 0, 0])),
                    steps=data.get("steps", []),
                    trigger=data.get("trigger", "left_click"),
                    poll_interval=data.get("poll_interval", 10)
                )
            elif macro_type == "buff":
                from macros import BuffMacro
                macro = BuffMacro(
                    name=data.get("name", "Бафф"),
                    app=self._backend,
                    hotkey=data.get("hotkey", ""),
                    buff_id=data.get("buff_id", 0),
                    duration=data.get("duration", 60.0),
                    channeling_bonus=data.get("channeling_bonus", 0),
                    steps=data.get("steps", []),
                    icon=data.get("icon", "buff.png")
                )
                zone_rect = data.get("zone_rect")
                if zone_rect and len(zone_rect) == 4:
                    macro.zone_rect = zone_rect
                    macro._connect_mouse_click(self._backend)
                    logger.info(f"[CRUD] Buff '{macro.name}' загружен с зоной {macro.zone_rect}")
            return macro
        except Exception as e:
            logger.error(f"[CRUD] Ошибка создания макроса: {e}", exc_info=True)
            return None

    def delete_macro(self, name: str):
        with self._lock:
            target = None
            for macro in self._backend._macros:
                if macro.name == name:
                    target = macro
                    break
            if target is None:
                return

            try:
                target._disconnect_mouse_click()
            except Exception as e:
                logger.warning(f"[CRUD] Ошибка отключения сигнала: {e}")

            try:
                target.stop()
            except Exception as e:
                logger.warning(f"[CRUD] Ошибка остановки: {e}")

            self._backend._macros.remove(target)
            self._backend.save_macros()
            self._backend._update_macros_dicts()
            self._emit(f"Макрос '{name}' удалён", "warning")

            if target.hotkey:
                try:
                    self._backend.unregister_hotkey(target.hotkey)
                except Exception as e:
                    logger.warning(f"[CRUD] Ошибка снятия hotkey: {e}")

    def _resolve_hotkey_conflict(self, hotkey: str, new_macro):
        """Снять hotkey с существующего макроса, если он занимает ту же клавишу."""
        if not hotkey:
            return
        for existing in self._backend._macros:
            if existing is new_macro:
                continue
            if existing.hotkey == hotkey:
                logger.debug(f"[CRUD] Hotkey '{hotkey}' уже занят '{existing.name}', освобождаем")
                try:
                    self._backend.unregister_hotkey(hotkey)
                except Exception:
                    pass
                existing.hotkey = None

    def _register_hotkey_for(self, macro, suppress: bool = True):
        if not macro.hotkey:
            return
        hotkey = macro.hotkey
        def make_callback(m):
            def callback(e=None):
                if hasattr(self._backend, 'dispatcher') and self._backend.dispatcher:
                    if time.time() < self._backend.dispatcher.cast_lock_until:
                        logger.debug(f"[CAST LOCK] Hotkey '{m.hotkey}' blocked")
                        return
                if not m.running.is_set():
                    if hasattr(self._backend, 'dispatcher') and self._backend.dispatcher:
                        if not self._backend.dispatcher.request_macro(m):
                            logger.warning(f"[CRUD] '{m.name}': blocked by dispatcher")
                            return
                        logger.info(f"[CRUD] '{m.name}': launched via hotkey")
            return callback
        try:
            self._backend.register_hotkey(hotkey, make_callback(macro), suppress=suppress)
        except Exception as e:
            logger.warning(f"[CRUD] Ошибка регистрации hotkey '{hotkey}': {e}")

    def _resolve_icon(self, skill_id, buff_id) -> str:
        try:
            if skill_id:
                skill = self._backend.skill_db.get_skill(int(skill_id))
                if skill and skill.icon:
                    return skill.icon
            if buff_id:
                buff = self._backend.skill_db.get_buff(int(buff_id))
                if buff and buff.icon:
                    return buff.icon
        except Exception:
            pass
        return ""

    def create_simple(self, name: str, hotkey: str, steps: list):
        import macros
        with self._lock:
            try:
                macro = macros.SimpleMacro(name, steps, self._backend, hotkey if hotkey else "")
                self._backend._macros.append(macro)
                self._backend.save_macros()
                self._backend._update_macros_dicts()
                self._emit(f"Макрос '{name}' создан", "success")
            except Exception as e:
                logger.error(f"[CRUD] create_simple: {e}", exc_info=True)
                self._emit(f"Ошибка создания: {e}", "error")

    def create_zone(self, name: str, hotkey: str, zone_rect, steps: list, trigger: str, poll_interval_ms: int):
        import macros
        with self._lock:
            try:
                poll_interval = poll_interval_ms / 1000.0
                macro = macros.ZoneMacro(
                    name, zone_rect, steps, self._backend,
                    trigger=trigger,
                    poll_interval=poll_interval,
                    hotkey=hotkey if hotkey else ""
                )
                if zone_rect and len(zone_rect) == 4:
                    macro._connect_mouse_click(self._backend)
                    logger.info(f"[CRUD] Zone '{name}' создана с зоной {zone_rect}")
                self._backend._macros.append(macro)
                macro.start()
                self._backend._update_macros_dicts()
                self._emit(f"Зональный макрос '{name}' создан", "success")
            except Exception as e:
                logger.error(f"[CRUD] create_zone: {e}", exc_info=True)
                self._emit(f"Ошибка: {e}", "error")

    def update_zone(self, old_name, new_name, hotkey, zone_rect, steps, trigger, poll_interval_ms):
        import macros
        with self._lock:
            try:
                for i, macro in enumerate(self._backend._macros):
                    if macro.name == old_name and macro.type == "zone":
                        if macro.hotkey and macro.hotkey != hotkey:
                            try:
                                self._backend.unregister_hotkey(macro.hotkey)
                            except Exception:
                                pass

                        poll_interval = poll_interval_ms / 1000.0
                        new_macro = macros.ZoneMacro(
                            new_name, zone_rect, steps, self._backend,
                            trigger=trigger,
                            poll_interval=poll_interval,
                            hotkey=hotkey if hotkey else ""
                        )
                        if zone_rect and len(zone_rect) == 4:
                            new_macro._connect_mouse_click(self._backend)
                            logger.info(f"[CRUD] Zone '{new_name}' обновлена с зоной {zone_rect}")
                        self._backend._macros[i] = new_macro
                        self._backend.save_macros()
                        if getattr(self._backend, '_macro_name_for_edit', None) == old_name:
                            self._backend._macro_for_edit = self.get_macro_for_edit_by_macro(new_macro)
                        self._backend._update_macros_dicts()
                        self._emit(f"Зональный макрос '{new_name}' обновлён", "success")
                        return
                self._emit("Макрос не найден", "error")
            except Exception as e:
                logger.error(f"[CRUD] update_zone: {e}", exc_info=True)
                self._emit(f"Ошибка: {e}", "error")

    def update_simple(self, old_name, new_name, hotkey, steps):
        import macros
        with self._lock:
            try:
                for i, macro in enumerate(self._backend._macros):
                    if macro.name == old_name and macro.type == "simple":
                        if macro.hotkey and macro.hotkey != hotkey:
                            try:
                                self._backend.unregister_hotkey(macro.hotkey)
                            except Exception:
                                pass
                        new_macro = macros.SimpleMacro(new_name, steps, self._backend, hotkey if hotkey else "")
                        self._backend._macros[i] = new_macro
                        self._backend.save_macros()
                        if getattr(self._backend, '_macro_name_for_edit', None) == old_name:
                            self._backend._macro_for_edit = self.get_macro_for_edit_by_macro(new_macro)
                        self._backend._update_macros_dicts()
                        self._emit(f"Макрос '{new_name}' обновлён", "success")
                        return
                self._emit("Макрос не найден", "error")
            except Exception as e:
                logger.error(f"[CRUD] update_simple: {e}", exc_info=True)
                self._emit(f"Ошибка: {e}", "error")

    def create_skill(self, name, hotkey, skill_id, steps, skill_hotkey,
                     cooldown, skill_range, cast_time, castbar_swap_delay, zone_rect):
        import macros
        with self._lock:
            try:
                icon = self._resolve_icon(skill_id, None)
                macro_hotkey = skill_hotkey if not hotkey else hotkey
                macro = macros.SkillMacro(
                    name, steps, self._backend, macro_hotkey if macro_hotkey else "",
                    skill_id=int(skill_id) if skill_id else None,
                    cooldown=cooldown, skill_range=skill_range,
                    cast_time=cast_time, castbar_swap_delay=castbar_swap_delay
                )
                macro.icon = icon
                if zone_rect and len(zone_rect) == 4:
                    macro.zone_rect = zone_rect
                    macro._connect_mouse_click(self._backend)
                    logger.info(f"[CRUD] Skill '{name}' с зоной {zone_rect}")
                self._backend._macros.append(macro)
                self._backend.save_macros()
                self._backend._update_macros_dicts()
                if macro_hotkey:
                    self._register_hotkey_for(macro)
                self._emit(f"Скилл-макрос '{name}' создан", "success")
            except Exception as e:
                logger.error(f"[CRUD] create_skill: {e}", exc_info=True)
                self._emit(f"Ошибка: {e}", "error")

    def update_skill(self, old_name, new_name, hotkey, skill_id, steps, skill_hotkey,
                     cooldown, skill_range, cast_time, castbar_swap_delay, zone_rect):
        import macros
        with self._lock:
            try:
                icon = self._resolve_icon(skill_id, None)
                for i, macro in enumerate(self._backend._macros):
                    if macro.name == old_name and macro.type == "skill":
                        if macro.hotkey and macro.hotkey != hotkey:
                            try:
                                self._backend.unregister_hotkey(macro.hotkey)
                            except Exception:
                                pass
                        new_macro = macros.SkillMacro(
                            new_name, steps, self._backend, hotkey if hotkey else "",
                            skill_id=int(skill_id) if skill_id else None,
                            cooldown=cooldown, skill_range=skill_range,
                            cast_time=cast_time, castbar_swap_delay=castbar_swap_delay
                        )
                        new_macro.icon = icon
                        if zone_rect and len(zone_rect) == 4:
                            new_macro.zone_rect = zone_rect
                            new_macro._connect_mouse_click(self._backend)
                            logger.info(f"[CRUD] Skill '{new_name}' обновлена с зоной {zone_rect}")
                        else:
                            new_macro.zone_rect = None
                        self._backend._macros[i] = new_macro
                        self._backend.save_macros()
                        if getattr(self._backend, '_macro_name_for_edit', None) == old_name:
                            self._backend._macro_for_edit = self.get_macro_for_edit_by_macro(new_macro)
                        self._backend._update_macros_dicts()
                        self._emit(f"Скилл-макрос '{new_name}' обновлён", "success")
                        return
                self._emit("Макрос не найден", "error")
            except Exception as e:
                logger.error(f"[CRUD] update_skill: {e}", exc_info=True)
                self._emit(f"Ошибка: {e}", "error")

    def create_buff(self, name, hotkey, buff_id, steps, duration, channeling_bonus, zone_rect):
        import macros
        with self._lock:
            try:
                icon = self._resolve_icon(None, buff_id)
                macro = macros.BuffMacro(
                    name, steps, self._backend,
                    buff_id=int(buff_id) if buff_id else None,
                    duration=duration, channeling_bonus=channeling_bonus,
                    hotkey=hotkey if hotkey else "",
                    icon=icon if icon else "buff.png"
                )
                if zone_rect and len(zone_rect) == 4:
                    macro.zone_rect = zone_rect
                if self._backend._settings.get("use_ping_delays", False):
                    ping_comp = self._backend.get_ping_compensation() * 1000
                    for i, step in enumerate(macro.steps):
                        if step[0] == "key":
                            macro.steps[i] = [step[0], step[1], round(ping_comp)]
                self._backend._macros.append(macro)
                self._backend.save_macros()
                self._backend._update_macros_dicts()
                if macro.hotkey and hasattr(self._backend, 'register_all_hotkeys'):
                    self._backend.register_all_hotkeys()
                self._emit(f"Бафф-макрос '{name}' создан", "success")
            except Exception as e:
                logger.error(f"[CRUD] create_buff: {e}", exc_info=True)
                self._emit(f"Ошибка: {e}", "error")

    def update_buff(self, old_name, new_name, hotkey, buff_id, steps, duration, channeling_bonus, zone_rect):
        import macros
        with self._lock:
            try:
                icon = self._resolve_icon(None, buff_id)
                for i, macro in enumerate(self._backend._macros):
                    if macro.name == old_name and macro.type == "buff":
                        if macro.hotkey and macro.hotkey != hotkey:
                            try:
                                self._backend.unregister_hotkey(macro.hotkey)
                            except Exception:
                                pass
                        new_macro = macros.BuffMacro(
                            new_name, steps, self._backend,
                            buff_id=int(buff_id) if buff_id else None,
                            duration=duration, channeling_bonus=channeling_bonus,
                            hotkey=hotkey if hotkey else "",
                            icon=icon if icon else "buff.png"
                        )
                        if zone_rect and len(zone_rect) == 4:
                            new_macro.zone_rect = zone_rect
                            new_macro._connect_mouse_click(self._backend)
                        else:
                            new_macro.zone_rect = None
                        if self._backend._settings.get("use_ping_delays", False):
                            ping_comp = self._backend.get_ping_compensation() * 1000
                            for i_step, step in enumerate(new_macro.steps):
                                if step[0] == "key":
                                    new_macro.steps[i_step] = [step[0], step[1], round(ping_comp)]
                        self._backend._macros[i] = new_macro
                        self._backend.save_macros()
                        if getattr(self._backend, '_macro_name_for_edit', None) == old_name:
                            self._backend._macro_for_edit = self.get_macro_for_edit_by_macro(new_macro)
                        self._backend._update_macros_dicts()
                        if hasattr(self._backend, 'register_all_hotkeys'):
                            self._backend.register_all_hotkeys()
                        self._emit(f"Бафф-макрос '{new_name}' обновлён", "success")
                        return
                self._emit("Макрос не найден", "error")
            except Exception as e:
                logger.error(f"[CRUD] update_buff: {e}", exc_info=True)
                self._emit(f"Ошибка: {e}", "error")

    def save_macro(self, macro_dict: dict):
        with self._lock:
            try:
                self._validate_macro_dict(macro_dict)
                name = macro_dict.get("name", "")
                hotkey = macro_dict.get("hotkey", "")
                if not name:
                    self._emit("Имя макроса не может быть пустым", "error")
                    return
                old_name = macro_dict.get("old_name", name)
                existing = None
                for m in self._backend._macros:
                    if m.name == old_name:
                        existing = m
                        break
                new_macro = self._create_macro_from_dict(macro_dict)
                if new_macro is None:
                    self._emit("Не удалось создать макрос", "error")
                    return
                new_macro.hotkey = hotkey if hotkey else ""
                if existing:
                    if existing.hotkey and existing.hotkey != hotkey:
                        self._backend.unregister_hotkey(existing.hotkey)
                    index = self._backend._macros.index(existing)
                    self._backend._macros[index] = new_macro
                    self._emit(f"Макрос '{name}' обновлён", "success")
                else:
                    self._resolve_hotkey_conflict(hotkey, new_macro)
                    self._backend._macros.append(new_macro)
                    self._emit(f"Макрос '{name}' создан", "success")
                if hotkey:
                    self._register_hotkey_for(new_macro)
                self._backend.save_macros()
                self._backend._update_macros_dicts()
            except Exception as e:
                logger.error(f"[CRUD] save_macro: {e}", exc_info=True)
                self._emit(f"Ошибка: {e}", "error")

    def edit_macro(self, name: str):
        for macro in self._backend._macros:
            if macro.name == name:
                self._backend._macro_name_for_edit = name
                logger.debug(f"[CRUD] edit_macro: '{name}'")
                if hasattr(self._backend, 'pageChangeRequested'):
                    self._backend.pageChangeRequested.emit("MacrosEditPage.qml")
                return
        logger.warning(f"[CRUD] edit_macro: '{name}' не найден")
        self._emit(f"Макрос '{name}' не найден", "error")

    def get_macro_for_edit(self) -> Optional[dict]:
        if not getattr(self._backend, '_macro_name_for_edit', None):
            return None
        name = self._backend._macro_name_for_edit
        for macro in self._backend._macros:
            if macro.name == name:
                return self.get_macro_for_edit_by_macro(macro)
        return None

    def get_macro_for_edit_by_macro(self, macro) -> Optional[dict]:
        if macro is None:
            return None
        result = {
            "name": macro.name,
            "type": macro.type,
            "hotkey": macro.hotkey or "",
            "steps": macro.steps if hasattr(macro, "steps") else [],
            "running": macro.running.is_set(),
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

    def clear_macro_for_edit(self):
        self._backend._macro_name_for_edit = None
        if hasattr(self._backend, '_macro_for_edit'):
            self._backend._macro_for_edit = None

    def set_macro_for_edit(self, macro_dict: dict):
        self._backend._macro_name_for_edit = macro_dict.get("name")
        self._backend._macro_for_edit = macro_dict
        logger.debug(f"[CRUD] set_macro_for_edit -> name={self._backend._macro_name_for_edit}")
        if hasattr(self._backend, 'macrosChanged'):
            self._backend.macrosChanged.emit()
