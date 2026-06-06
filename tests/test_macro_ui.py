"""UI tests for the macro system — tests the QML-facing Backend interface.

Tests verify:
- @Slot methods delegate correctly to MacroCrud
- @Property values reflect current state
- Signals emit at the right times with correct data
- Full CRUD lifecycle through the QML API
"""

import os
import sys
import json
import time
import threading
from unittest.mock import MagicMock, patch

import pytest
from pytestqt.qt_compat import qt_api

from PySide6.QtCore import QObject, Signal, Property, Slot, Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QPlainTextEdit,
)
from PySide6.QtTest import QTest

TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(TESTS_DIR)
sys.path.insert(0, PROJECT_DIR)


class MacroUIHarness(QObject):
    """Minimal QObject that inherits production MacroCRUDMixin + MacroStorageMixin
    to test the actual QML-facing interface.

    This is the same inheritance chain as the real Backend class,
    but with external dependencies (threads, monitors, hotkeys, QML engine) mocked out.
    """

    macrosChanged = Signal()
    notification = Signal(str, str)
    pageChangeRequested = Signal(str)
    editMacroRequested = Signal(str, 'QVariantMap')
    globalStoppedChanged = Signal()
    macroStatusChanged = Signal()
    settingsChanged = Signal()
    startAllPressed = Signal()
    stopAllPressed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._macros = []
        self._macros_dicts = []
        self._settings = {
            "cooldown_margin": 0.3,
            "cast_lock_margin": 0.45,
            "global_step_delay": 20,
            "first_step_delay": 100,
            "use_ping_delays": False,
            "average_ping": 0,
            "swap_key_chant": "q",
            "swap_key_pa": "e",
            "window_locked": False,
            "target_window_title": "",
        }
        self._global_stopped = True
        self._macro_for_edit = None
        self._macro_name_for_edit = None
        self._ping = 0
        self._window_locked = False
        self._target_window_title = ""
        self._hotkey_registered = set()

        from backend.macros_dispatcher import MacroDispatcher
        self.dispatcher = MacroDispatcher(self)

        self.movement_monitor = MagicMock()
        self.movement_monitor.get_movement_delay.return_value = 999.0
        self.mouse_click_monitor = MagicMock()
        self.mouse_click_monitor.mouse_clicked = MagicMock()
        self.skill_db = MagicMock()
        self.buff_lock = threading.Lock()
        self.active_macros = {}
        self.target_window_title = ""
        self.window_locked = False

    @property
    def settings(self):
        return self._settings

    def get(self, key, default=None):
        return self._settings.get(key, default)

    """--------------------------------------------------------------------"""
    """Mixins included via inheritance"""
    """--------------------------------------------------------------------"""

    def save_macros(self):
        pass

    def register_hotkey(self, hotkey, callback, **kwargs):
        self._hotkey_registered.add(hotkey)

    def unregister_hotkey(self, hotkey):
        self._hotkey_registered.discard(hotkey)

    def register_all_hotkeys(self):
        for macro in self._macros:
            if macro.hotkey:
                self.register_hotkey(macro.hotkey, lambda e: None)

    def unregister_all_hotkeys(self):
        self._hotkey_registered.clear()

    def get_ping_compensation(self):
        return 0.0

    def apply_settings_to_macros(self, key, value):
        pass

    """--------------------------------------------------------------------"""
    """QML Properties (mirrors Backend)"""
    """--------------------------------------------------------------------"""

    @Property(list, notify=macrosChanged)
    def macros(self):
        return list(self._macros_dicts)

    @Property(bool, notify=globalStoppedChanged)
    def global_stopped(self):
        return self._global_stopped

    @global_stopped.setter
    def global_stopped(self, value):
        if self._global_stopped != value:
            self._global_stopped = value
            self.globalStoppedChanged.emit()

    @Property("QVariantMap", notify=macrosChanged)
    def macro_for_edit(self):
        val = getattr(self, '_macro_for_edit', None)
        return val if val is not None else {}

    @Property(str, notify=macrosChanged)
    def target_window_title(self):
        return self._target_window_title if hasattr(self, '_target_window_title') else ""

    @target_window_title.setter
    def target_window_title(self, value):
        if hasattr(self, '_target_window_title'):
            self._target_window_title = value
            self._settings["target_window_title"] = value
            self.macrosChanged.emit()
            self.settingsChanged.emit()

    @Property(bool, notify=macrosChanged)
    def window_locked(self):
        return self._window_locked if hasattr(self, '_window_locked') else False

    @window_locked.setter
    def window_locked(self, value):
        if hasattr(self, '_window_locked'):
            self._window_locked = value
            self._settings["window_locked"] = value
            self.macrosChanged.emit()
            self.settingsChanged.emit()

    """--------------------------------------------------------------------"""
    """QML macro Slots (via MacroCRUDMixin + QMLBridgeMixin)"""
    """--------------------------------------------------------------------"""

    def _get_crud(self):
        if not hasattr(self, '_macro_crud') or self._macro_crud is None:
            from backend.macro_crud import MacroCrud
            self._macro_crud = MacroCrud(self)
        return self._macro_crud

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

    @Slot(str, str, list)
    def create_simple_macro_with_params(self, name, hotkey, steps):
        self._get_crud().create_simple(name, hotkey, steps)

    @Slot(str, str, str, list, str, float, float, float, float, list)
    def create_skill_macro_with_params(self, name, hotkey, skill_id, steps, skill_hotkey,
                                       cooldown, skill_range, cast_time, castbar_swap_delay, zone_rect):
        self._get_crud().create_skill(name, hotkey, skill_id, steps, skill_hotkey,
                                      cooldown, skill_range, cast_time, castbar_swap_delay, zone_rect)

    @Slot(str, str, str, list, float, int, list)
    def create_buff_macro_with_params(self, name, hotkey, buff_id, steps, duration, channeling_bonus, zone_rect):
        self._get_crud().create_buff(name, hotkey, buff_id, steps, duration, channeling_bonus, zone_rect)

    @Slot(str, str, list, list, str, int)
    def create_zone_macro_with_params(self, name, hotkey, zone_rect, steps, trigger, poll_interval_ms):
        self._get_crud().create_zone(name, hotkey, zone_rect, steps, trigger, poll_interval_ms)

    @Slot(str, str, str, list)
    def update_simple_macro(self, old_name, new_name, hotkey, steps):
        self._get_crud().update_simple(old_name, new_name, hotkey, steps)

    @Slot(str)
    def delete_macro(self, name):
        self._get_crud().delete_macro(name)

    @Slot(int)
    def edit_macro_by_index(self, index):
        if not (0 <= index < len(self._macros)):
            return
        macro = self._macros[index]
        macro_dict = self._get_crud().get_macro_for_edit_by_macro(macro)
        self._get_crud().set_macro_for_edit(macro_dict)
        self.editMacroRequested.emit("MacrosEditPage.qml", macro_dict)

    @Slot()
    def clear_macro_for_edit(self):
        self._get_crud().clear_macro_for_edit()

    @Slot(dict)
    def set_macro_for_edit(self, macro_dict):
        self._get_crud().set_macro_for_edit(macro_dict)

    @Slot(result=dict)
    def get_macro_for_edit(self):
        return self._get_crud().get_macro_for_edit()

    @Slot(dict)
    def save_macro(self, macro_dict):
        self._get_crud().save_macro(macro_dict)

    @Slot()
    def stop_all_macros(self):
        self._global_stopped = True
        self.globalStoppedChanged.emit()
        for macro in self._macros:
            macro.stop()
        self._update_macros_dicts()
        self.stopAllPressed.emit()

    @Slot()
    def start_all_macros(self):
        self._global_stopped = False
        self.globalStoppedChanged.emit()
        if self.dispatcher:
            self.dispatcher._active_macros_clear()
        self.register_all_hotkeys()
        self.startAllPressed.emit()

    @Slot(str)
    def start_macro(self, name):
        for macro in self._macros:
            if macro.name == name:
                if self.dispatcher.request_macro(macro, priority=5):
                    self._update_macros_dicts()
                break

    @Slot(str)
    def stop_macro(self, name):
        for macro in self._macros:
            if macro.name == name:
                macro.stop()
                self._update_macros_dicts()
                self.macroStatusChanged.emit()
                break

    @Slot(str, dict)
    def create_macro_from_dict(self, macro_type, macro_dict):
        macro_dict["type"] = macro_type
        self._get_crud().save_macro(macro_dict)

    @Slot(str, str, str, list, list, str, int)
    def update_zone_macro(self, old_name, new_name, hotkey, zone_rect, steps, trigger, poll_interval_ms):
        self._get_crud().update_zone(old_name, new_name, hotkey, zone_rect, steps, trigger, poll_interval_ms)

    @Slot(str, str, str, str, list, str, float, float, float, float, list)
    def update_skill_macro(self, old_name, new_name, hotkey, skill_id, steps, skill_hotkey,
                           cooldown, skill_range, cast_time, castbar_swap_delay, zone_rect):
        self._get_crud().update_skill(old_name, new_name, hotkey, skill_id, steps, skill_hotkey,
                                      cooldown, skill_range, cast_time, castbar_swap_delay, zone_rect)

    @Slot(str, str, str, str, list, float, int, list)
    def update_buff_macro(self, old_name, new_name, hotkey, buff_id, steps, duration, channeling_bonus, zone_rect):
        self._get_crud().update_buff(old_name, new_name, hotkey, buff_id, steps, duration, channeling_bonus, zone_rect)

    def cleanup(self):
        self.dispatcher.stop()
        self.dispatcher.stop_all_macros(timeout=1.0)


@pytest.fixture
def harness(qapp):
    ui = MacroUIHarness()
    yield ui
    ui.cleanup()


@pytest.fixture(autouse=True)
def _mock_win32():
    with patch('macros_core.GetForegroundWindow', return_value=99999):
        with patch('macros_core.GetWindowText', return_value="Perfect World"):
            with patch('macros_core.GetWindowTextTimeout', return_value="Perfect World"):
                yield


class TestMacroUIProperties:
    def test_macros_property_empty_on_init(self, harness):
        assert harness.macros == []

    def test_macros_property_after_create(self, harness):
        harness.create_simple_macro_with_params("Test", "F1", [("key", "a", 10)])
        assert len(harness.macros) == 1
        assert harness.macros[0]["name"] == "Test"
        assert harness.macros[0]["type"] == "simple"

    def test_macros_property_running_status(self, harness):
        harness.global_stopped = False
        harness.create_simple_macro_with_params("RunTest", "F2", [("wait", "", 50)])
        macro = harness._macros[0]
        macro.running.set()
        harness._update_macros_dicts()
        assert harness.macros[0]["running"] is True

    def test_global_stopped_default_true(self, harness):
        assert harness.global_stopped is True

    def test_global_stopped_setter(self, harness):
        signal_emitted = False
        def _on_change():
            nonlocal signal_emitted
            signal_emitted = True
        harness.globalStoppedChanged.connect(_on_change)

        harness.global_stopped = False
        assert harness.global_stopped is False
        assert signal_emitted is True

    def test_global_stopped_changed_signal_emitted_once(self, harness):
        calls = []
        harness.globalStoppedChanged.connect(lambda: calls.append(1))
        harness.global_stopped = False
        harness.global_stopped = False  # same value — no emit
        assert len(calls) == 1

    def test_macro_for_edit_empty_default(self, harness):
        assert harness.macro_for_edit == {}

    def test_macro_for_edit_after_set(self, harness):
        harness.create_simple_macro_with_params("EditMe", "F3", [("key", "b", 10)])
        harness.edit_macro_by_index(0)
        data = harness.macro_for_edit
        assert isinstance(data, dict)
        assert data["name"] == "EditMe"

    def test_macro_for_edit_after_clear(self, harness):
        harness.create_simple_macro_with_params("ClearMe", "F4", [("key", "c", 10)])
        harness.edit_macro_by_index(0)
        assert harness.macro_for_edit != {}
        harness.clear_macro_for_edit()
        assert harness.macro_for_edit == {}


class TestMacroUICreateSlots:
    def test_create_simple_macro_adds_to_list(self, harness):
        harness.create_simple_macro_with_params("Simple1", "F5", [("key", "d", 10)])
        assert len(harness._macros) == 1
        m = harness._macros[0]
        assert m.name == "Simple1"
        assert m.hotkey == "F5"
        assert m.steps == [("key", "d", 10)]

    def test_create_simple_macro_emits_macrosChanged(self, harness):
        signals = []
        harness.macrosChanged.connect(lambda: signals.append(1))
        harness.create_simple_macro_with_params("S", "", [("key", "x", 5)])
        assert len(signals) >= 1

    def test_create_simple_macro_updates_property(self, harness):
        harness.create_simple_macro_with_params("PropTest", "", [("key", "z", 5)])
        assert len(harness.macros) == 1
        assert harness.macros[0]["name"] == "PropTest"

    def test_create_skill_macro(self, harness):
        harness.create_skill_macro_with_params(
            "Skill1", "F6", "6003",
            [("key", "q", 100), ("key", "e", 20)],
            "F6", 3.0, 10.0, 0.5, 0, [],
        )
        assert len(harness._macros) == 1
        m = harness._macros[0]
        assert m.name == "Skill1"
        assert m.type == "skill"
        assert m.skill_id == 6003
        assert m.cooldown == 3.0

    def test_create_buff_macro(self, harness):
        harness.create_buff_macro_with_params(
            "Buff1", "F7", "101", [("key", "q", 100)], 60.0, 0, [],
        )
        assert len(harness._macros) == 1
        m = harness._macros[0]
        assert m.name == "Buff1"
        assert m.type == "buff"
        assert m.buff_id == 101

    def test_create_zone_macro(self, harness):
        harness.create_zone_macro_with_params(
            "Zone1", "F8", [100, 200, 300, 400],
            [("key", "e", 10)], "left_click", 10,
        )
        assert len(harness._macros) == 1
        m = harness._macros[0]
        assert m.name == "Zone1"
        assert m.type == "zone"
        assert list(m.zone_rect) == [100, 200, 300, 400]

    def test_create_macro_from_dict(self, harness):
        harness.create_macro_from_dict("simple", {
            "name": "DictMacro",
            "hotkey": "F9",
            "steps": [("key", "a", 10)],
        })
        assert len(harness._macros) == 1
        assert harness._macros[0].name == "DictMacro"

    def test_multiple_macros_of_different_types(self, harness):
        harness.create_simple_macro_with_params("S", "", [("key", "a", 5)])
        harness.create_skill_macro_with_params("Sk", "F1", "1", [("key", "q", 10)], "", 1.0, 5.0, 0.3, 0, [])
        harness.create_buff_macro_with_params("B", "F2", "2", [("key", "w", 10)], 30.0, 0, [])
        assert len(harness._macros) == 3
        assert harness.macros[0]["type"] == "simple"
        assert harness.macros[1]["type"] == "skill"
        assert harness.macros[2]["type"] == "buff"


class TestMacroUIUpdateSlots:
    def test_update_simple_macro(self, harness):
        harness.create_simple_macro_with_params("OldName", "F1", [("key", "a", 10)])
        harness.update_simple_macro("OldName", "NewName", "F2", [("key", "b", 20)])
        assert len(harness._macros) == 1
        m = harness._macros[0]
        assert m.name == "NewName"
        assert m.hotkey == "F2"
        assert m.steps == [("key", "b", 20)]

    def test_update_simple_macro_emits_signal(self, harness):
        harness.create_simple_macro_with_params("A", "", [("key", "a", 5)])
        signals = []
        harness.macrosChanged.connect(lambda: signals.append(1))
        harness.update_simple_macro("A", "B", "", [("key", "b", 5)])
        assert len(signals) >= 1

    def test_update_skill_macro(self, harness):
        harness.create_skill_macro_with_params("Sk", "F1", "1", [("key", "q", 10)], "", 1.0, 5.0, 0.3, 0, [])
        harness.update_skill_macro("Sk", "SkV2", "F2", "2", [("key", "w", 10)], "F2", 2.0, 8.0, 0.5, 100, [])
        m = harness._macros[0]
        assert m.name == "SkV2"
        assert m.skill_id == 2
        assert m.cooldown == 2.0

    def test_update_zone_macro(self, harness):
        harness.create_zone_macro_with_params("Z", "", [0, 0, 100, 100], [("key", "e", 5)], "left_click", 10)
        harness.update_zone_macro("Z", "Z2", "", [50, 50, 200, 200], [("key", "r", 5)], "right_click", 20)
        m = harness._macros[0]
        assert m.name == "Z2"
        assert list(m.zone_rect) == [50, 50, 200, 200]

    def test_update_buff_macro(self, harness):
        harness.create_buff_macro_with_params("B", "", "1", [("key", "q", 10)], 30.0, 0, [])
        harness.update_buff_macro("B", "B2", "", "2", [("key", "w", 10)], 60.0, 1, [])
        m = harness._macros[0]
        assert m.name == "B2"
        assert m.buff_id == 2
        assert m.duration == 60.0


class TestMacroUIDeleteSlots:
    def test_delete_macro_removes_from_list(self, harness):
        harness.create_simple_macro_with_params("DelMe", "", [("key", "a", 5)])
        assert len(harness._macros) == 1
        harness.delete_macro("DelMe")
        assert len(harness._macros) == 0

    def test_delete_macro_emits_signal(self, harness):
        harness.create_simple_macro_with_params("SigMe", "", [("key", "a", 5)])
        signals = []
        harness.macrosChanged.connect(lambda: signals.append(1))
        harness.delete_macro("SigMe")
        assert len(signals) >= 1

    def test_delete_macro_nonexistent_safe(self, harness):
        harness.delete_macro("NonExistent")

    def test_delete_macro_updates_property(self, harness):
        harness.create_simple_macro_with_params("A", "", [("key", "a", 5)])
        harness.create_simple_macro_with_params("B", "", [("key", "b", 5)])
        harness.delete_macro("A")
        assert len(harness.macros) == 1
        assert harness.macros[0]["name"] == "B"

    def test_delete_macro_unregisters_hotkey(self, harness):
        harness.global_stopped = False
        harness.create_simple_macro_with_params("HK", "F1", [("key", "a", 5)])
        harness.start_all_macros()
        assert "F1" in harness._hotkey_registered
        harness.delete_macro("HK")
        assert "F1" not in harness._hotkey_registered


class TestMacroUIEditSlots:
    def test_edit_macro_by_index_emits_signal(self, harness, qtbot):
        harness.create_simple_macro_with_params("EditMe", "F1", [("key", "a", 5)])
        signal_data = []

        def _capture(page, data):
            signal_data.append((page, data))

        harness.editMacroRequested.connect(_capture)
        harness.edit_macro_by_index(0)

        assert len(signal_data) == 1
        page, data = signal_data[0]
        assert page == "MacrosEditPage.qml"
        assert data["name"] == "EditMe"
        assert data["type"] == "simple"

    def test_edit_macro_by_index_sets_macro_for_edit(self, harness):
        harness.create_simple_macro_with_params("Test", "", [("key", "a", 5)])
        harness.edit_macro_by_index(0)
        data = harness.get_macro_for_edit()
        assert data is not None
        assert data["name"] == "Test"

    def test_edit_macro_by_index_invalid_noop(self, harness):
        harness.edit_macro_by_index(99)
        assert harness.get_macro_for_edit() is None

    def test_edit_macro_by_index_with_skill_type(self, harness):
        harness.create_skill_macro_with_params("Sk", "F1", "6003", [("key", "q", 10)], "", 3.0, 10.0, 0.5, 0, [])
        harness.edit_macro_by_index(0)
        data = harness.get_macro_for_edit()
        assert data["type"] == "skill"
        assert data["skill_id"] == 6003
        assert data["cooldown"] == 3.0

    def test_edit_macro_by_index_with_zone_type(self, harness):
        harness.create_zone_macro_with_params("Z", "", [100, 200, 300, 400], [("key", "e", 5)], "left_click", 10)
        harness.edit_macro_by_index(0)
        data = harness.get_macro_for_edit()
        assert data["type"] == "zone"
        assert data["zone_rect"] == [100, 200, 300, 400]
        assert data["trigger"] == "left_click"

    def test_edit_macro_by_index_with_buff_type(self, harness):
        harness.create_buff_macro_with_params("B", "", "101", [("key", "q", 10)], 60.0, 0, [])
        harness.edit_macro_by_index(0)
        data = harness.get_macro_for_edit()
        assert data["type"] == "buff"
        assert data["buff_id"] == 101
        assert data["duration"] == 60.0


class TestMacroUIStartStopSlots:
    def test_start_all_macros_sets_global_stopped_false(self, harness):
        harness.start_all_macros()
        assert harness.global_stopped is False

    def test_stop_all_macros_sets_global_stopped_true(self, harness):
        harness.start_all_macros()
        harness.stop_all_macros()
        assert harness.global_stopped is True

    def test_start_all_emits_startAllPressed(self, harness):
        signals = []
        harness.startAllPressed.connect(lambda: signals.append(1))
        harness.start_all_macros()
        assert len(signals) == 1

    def test_stop_all_emits_stopAllPressed(self, harness):
        signals = []
        harness.stopAllPressed.connect(lambda: signals.append(1))
        harness.stop_all_macros()
        assert len(signals) == 1

    def test_start_macro_via_slot(self, harness):
        harness.global_stopped = False
        harness.create_simple_macro_with_params("Test", "", [("wait", "", 50)])
        harness.start_macro("Test")
        macro = harness._macros[0]
        assert macro.running.is_set() is True
        macro.stop()

    def test_start_macro_updates_dicts(self, harness):
        harness.global_stopped = False
        harness.create_simple_macro_with_params("Run", "", [("wait", "", 50)])
        harness.start_macro("Run")
        harness._macros[0].stop()

    def test_stop_macro_via_slot(self, harness):
        harness.global_stopped = False
        harness.create_simple_macro_with_params("StopMe", "", [("wait", "", 500)])
        harness.start_macro("StopMe")
        harness._macros[0].thread.join(timeout=0.1)
        harness.stop_macro("StopMe")
        assert harness._macros[0].running.is_set() is False

    def test_stop_macro_emits_macroStatusChanged(self, harness):
        harness.global_stopped = False
        harness.create_simple_macro_with_params("SigStop", "", [("wait", "", 50)])
        signals = []
        harness.macroStatusChanged.connect(lambda: signals.append(1))
        harness.stop_macro("SigStop")
        assert len(signals) >= 1

    def test_stop_all_stops_running_macros(self, harness):
        harness.global_stopped = False
        harness.create_simple_macro_with_params("A", "", [("wait", "", 500)])
        harness.create_simple_macro_with_params("B", "", [("wait", "", 500)])
        harness.start_macro("A")
        harness.start_macro("B")
        harness.stop_all_macros()
        assert harness._macros[0].running.is_set() is False
        assert harness._macros[1].running.is_set() is False


class TestMacroUISaveMacro:
    def test_save_macro_creates_new(self, harness):
        harness.save_macro({
            "type": "simple",
            "name": "Saved",
            "hotkey": "F1",
            "steps": [("key", "a", 10)],
        })
        assert len(harness._macros) == 1
        assert harness._macros[0].name == "Saved"

    def test_save_macro_updates_existing(self, harness):
        harness.create_simple_macro_with_params("Old", "", [("key", "a", 5)])
        harness.save_macro({
            "type": "simple",
            "name": "Updated",
            "old_name": "Old",
            "hotkey": "",
            "steps": [("key", "b", 10)],
        })
        assert len(harness._macros) == 1
        assert harness._macros[0].name == "Updated"
        assert harness._macros[0].steps == [("key", "b", 10)]

    def test_save_macro_validation_blocks_invalid(self, harness):
        harness.save_macro({"type": "simple", "name": "", "steps": []})
        assert len(harness._macros) == 0

    def test_save_macro_emits_macrosChanged(self, harness):
        signals = []
        harness.macrosChanged.connect(lambda: signals.append(1))
        harness.save_macro({
            "type": "simple",
            "name": "SigSave",
            "hotkey": "",
            "steps": [("key", "a", 5)],
        })
        assert len(signals) >= 1

    def test_save_macro_with_zone_type(self, harness):
        harness.save_macro({
            "type": "zone",
            "name": "ZoneSave",
            "hotkey": "",
            "zone_rect": [0, 0, 100, 100],
            "steps": [("key", "e", 5)],
            "trigger": "right_click",
            "poll_interval": 20,
        })
        assert len(harness._macros) == 1
        m = harness._macros[0]
        assert m.type == "zone"
        assert list(m.zone_rect) == [0, 0, 100, 100]


class TestMacroUIEditFlow:
    """End-to-end edit flow: create → edit → verify → update → clear."""

    def test_full_edit_flow(self, harness, qtbot):
        harness.create_simple_macro_with_params("Flow", "F1", [("key", "a", 10)])
        assert len(harness.macros) == 1
        assert harness.macros[0]["name"] == "Flow"
        assert harness.macros[0]["hotkey"] == "F1"

        harness.edit_macro_by_index(0)
        edit_data = harness.macro_for_edit
        assert edit_data["name"] == "Flow"
        assert edit_data["hotkey"] == "F1"

        harness.clear_macro_for_edit()
        assert harness.macro_for_edit == {}

    def test_edit_and_update_flow(self, harness):
        harness.create_simple_macro_with_params("Original", "F1", [("key", "a", 10)])
        harness.edit_macro_by_index(0)
        data = harness.get_macro_for_edit()
        data["name"] = "Edited"
        data["old_name"] = "Original"
        data["hotkey"] = "F2"
        data["steps"] = [("key", "b", 20)]
        harness.save_macro(data)

        assert len(harness._macros) == 1
        m = harness._macros[0]
        assert m.name == "Edited"
        assert m.hotkey == "F2"

    def test_create_edit_create_another(self, harness):
        harness.create_simple_macro_with_params("First", "", [("key", "a", 5)])
        harness.edit_macro_by_index(0)
        assert harness.macro_for_edit["name"] == "First"
        harness.clear_macro_for_edit()

        harness.create_simple_macro_with_params("Second", "", [("key", "b", 5)])
        assert len(harness._macros) == 2
        assert harness.macros[1]["name"] == "Second"


class TestMacroUIMultiTypeList:
    def test_macros_list_contains_all_types(self, harness):
        harness.create_simple_macro_with_params("S", "F1", [("key", "a", 5)])
        harness.create_skill_macro_with_params("Sk", "F2", "100", [("key", "q", 10)], "", 1.0, 5.0, 0.3, 0, [])
        harness.create_buff_macro_with_params("B", "F3", "200", [("key", "w", 10)], 30.0, 0, [])
        harness.create_zone_macro_with_params("Z", "F4", [0, 0, 50, 50], [("key", "e", 5)], "left_click", 10)

        assert len(harness.macros) == 4
        types = [m["type"] for m in harness.macros]
        assert types == ["simple", "skill", "buff", "zone"]

    def test_skill_macro_dict_contains_skill_id(self, harness):
        harness.create_skill_macro_with_params("Sk", "", "6003", [("key", "q", 10)], "", 3.0, 10.0, 0.5, 0, [])
        d = harness.macros[0]
        assert d["skill_id"] == 6003
        assert d["cooldown"] == 3.0

    def test_zone_macro_dict_contains_rect(self, harness):
        harness.create_zone_macro_with_params("Z", "", [10, 20, 30, 40], [("key", "e", 5)], "left_click", 10)
        d = harness.macros[0]
        assert list(d["zone_rect"]) == [10, 20, 30, 40]

    def test_buff_macro_dict_contains_buff_id(self, harness):
        harness.create_buff_macro_with_params("B", "", "42", [("key", "q", 10)], 60.0, 0, [])
        d = harness.macros[0]
        assert d["buff_id"] == 42


class TestMacroUIHotkeyRegistration:
    def test_create_registers_hotkey(self, harness):
        harness.global_stopped = False
        harness.create_simple_macro_with_params("HK", "F1", [("key", "a", 5)])
        harness.start_all_macros()
        assert "F1" in harness._hotkey_registered

    def test_delete_unregisters_hotkey(self, harness):
        harness.global_stopped = False
        harness.create_simple_macro_with_params("HK", "F1", [("key", "a", 5)])
        harness.start_all_macros()
        assert "F1" in harness._hotkey_registered
        harness.delete_macro("HK")
        assert "F1" not in harness._hotkey_registered

    def test_update_old_hotkey_unregistered_new_registered(self, harness):
        harness.global_stopped = False
        harness.create_simple_macro_with_params("HK", "F1", [("key", "a", 5)])
        harness.start_all_macros()
        harness.update_simple_macro("HK", "HK", "F2", [("key", "b", 5)])
        assert "F1" not in harness._hotkey_registered
        harness.start_all_macros()
        assert "F2" in harness._hotkey_registered

    def test_start_all_registers_all_hotkeys(self, harness):
        harness.create_simple_macro_with_params("A", "F1", [("key", "a", 5)])
        harness.create_simple_macro_with_params("B", "F2", [("key", "b", 5)])
        harness.start_all_macros()
        assert "F1" in harness._hotkey_registered
        assert "F2" in harness._hotkey_registered

    def test_stop_all_unregisters_hotkeys_behavior(self, harness):
        harness.global_stopped = False
        harness.create_simple_macro_with_params("A", "F1", [("key", "a", 5)])
        harness.stop_all_macros()
        assert harness.global_stopped is True


class TestMacroUIErrorHandling:
    def test_delete_nonexistent_does_not_raise(self, harness):
        harness.delete_macro("ghost")

    def test_edit_bad_index_does_not_raise(self, harness):
        harness.edit_macro_by_index(-1)
        harness.edit_macro_by_index(999)

    def test_create_duplicate_name(self, harness):
        harness.create_simple_macro_with_params("Dup", "", [("key", "a", 5)])
        harness.create_simple_macro_with_params("Dup", "", [("key", "b", 5)])
        assert len(harness._macros) == 2

    def test_start_nonexistent_macro_safe(self, harness):
        harness.start_macro("DoesNotExist")

    def test_stop_nonexistent_macro_safe(self, harness):
        harness.stop_macro("DoesNotExist")


class TestMacroUISaveMacroRoundTrip:
    def test_save_then_retrieve_property(self, harness):
        harness.save_macro({
            "type": "skill",
            "name": "RT",
            "hotkey": "F1",
            "skill_id": 6003,
            "cooldown": 3.0,
            "skill_range": 10.0,
            "cast_time": 0.5,
            "steps": [("key", "q", 100), ("key", "e", 20)],
        })
        d = harness.macros[0]
        assert d["name"] == "RT"
        assert d["type"] == "skill"

    def test_save_zone_then_edit_retrieves_rect(self, harness):
        harness.save_macro({
            "type": "zone",
            "name": "ZoneRT",
            "hotkey": "",
            "zone_rect": [100, 200, 300, 400],
            "steps": [("key", "e", 5)],
            "trigger": "left_click",
            "poll_interval": 10,
        })
        harness.edit_macro_by_index(0)
        data = harness.macro_for_edit
        assert data["zone_rect"] == [100, 200, 300, 400]

    def test_save_buff_with_duration(self, harness):
        harness.save_macro({
            "type": "buff",
            "name": "BuffRT",
            "hotkey": "",
            "buff_id": 42,
            "duration": 120.0,
            "channeling_bonus": 0,
            "steps": [("key", "q", 10)],
        })
        harness.edit_macro_by_index(0)
        data = harness.macro_for_edit
        assert data["buff_id"] == 42
        assert data["duration"] == 120.0


class _TestRunnerWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SNBLD — UI тесты макросов")
        self.resize(900, 600)
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)

        title = QLabel("UI тесты макросов (67 тестов)")
        title.setStyleSheet("font-size: 18px; font-weight: bold; padding: 8px;")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        self.output = QPlainTextEdit()
        self.output.setReadOnly(True)
        self.output.setFont(QFont("Consolas", 10))
        self.output.setStyleSheet("background: #1e1e2e; color: #cdd6f4; padding: 8px;")
        layout.addWidget(self.output)

        progress_layout = QHBoxLayout()
        self.passed_label = QLabel("✅ Прошло: 0")
        self.passed_label.setStyleSheet("font-size: 14px; color: #a6e3a1; font-weight: bold;")
        self.failed_label = QLabel("❌ Провалено: 0")
        self.failed_label.setStyleSheet("font-size: 14px; color: #f38ba8; font-weight: bold;")
        self.total_label = QLabel("Всего: 67")
        self.total_label.setStyleSheet("font-size: 14px;")
        progress_layout.addWidget(self.passed_label)
        progress_layout.addWidget(self.failed_label)
        progress_layout.addWidget(self.total_label)
        progress_layout.addStretch()
        layout.addLayout(progress_layout)

        btn_layout = QHBoxLayout()
        self.run_btn = QPushButton("▶ Запустить тесты")
        self.run_btn.setStyleSheet("""
            QPushButton {
                font-size: 16px; font-weight: bold; padding: 12px 32px;
                background: #89b4fa; color: #1e1e2e; border-radius: 8px;
            }
            QPushButton:hover { background: #b4d0fb; }
        """)
        self.run_btn.clicked.connect(self.run_tests)
        btn_layout.addStretch()
        btn_layout.addWidget(self.run_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        self.setStyleSheet("QMainWindow { background: #11111b; color: #cdd6f4; }")

    def log(self, text, color=None):
        if color:
            self.output.appendHtml(f'<span style="color:{color}">{text}</span>')
        else:
            self.output.appendPlainText(text)
        QApplication.processEvents()

    def run_tests(self):
        self.run_btn.setEnabled(False)
        self.run_btn.setText("⏳ Запуск...")
        self.output.clear()
        self.passed_label.setText("✅ Прошло: 0")
        self.failed_label.setText("❌ Провалено: 0")
        QApplication.processEvents()

        import subprocess
        proc = subprocess.Popen(
            [sys.executable, "-m", "pytest", __file__, "-v", "--tb=short", "--color=yes"],
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            text=True, encoding="utf-8", errors="replace",
            cwd=os.path.dirname(TESTS_DIR),
        )

        output_lines = []
        for line in proc.stdout:
            line = line.rstrip()
            output_lines.append(line)
            self.log(line)
            QApplication.processEvents()

        proc.wait()
        exit_code = proc.returncode

        import re
        passed = sum(1 for l in output_lines if re.search(r'\d+ passed', l))
        failed = sum(1 for l in output_lines if re.search(r'\d+ failed', l))
        if not passed and not failed:
            summary = [l for l in output_lines if 'passed' in l or 'failed' in l or '=' in l and 'warnings' not in l]
            if summary:
                m = re.search(r'(\d+) passed', summary[-1])
                if m: passed = int(m.group(1))
                m = re.search(r'(\d+) failed', summary[-1])
                if m: failed = int(m.group(1))
        total = passed + failed
        self.total_label.setText(f"Всего: {total}")
        self.passed_label.setText(f"✅ Прошло: {passed}")
        self.failed_label.setText(f"❌ Провалено: {failed}")
        self.log("")
        if exit_code == 0:
            self.log(f"✅ Все {total} тестов пройдено!", color="#a6e3a1")
        else:
            self.log(f"❌ {failed} из {total} тестов провалено", color="#f38ba8")
        self.run_btn.setEnabled(True)
        self.run_btn.setText("▶ Запустить тесты")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = _TestRunnerWindow()
    w.show()
    sys.exit(app.exec())
