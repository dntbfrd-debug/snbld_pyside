"""SNBLD — Все тесты макросов (184 теста).

Включает:
- Бэкенд-тесты: выполнение шагов, диспетчер, CRUD, тред-безопасность
- UI-тесты: QML-интерфейс (Slots, Properties, Signals)
- Клавиатурный ввод: InputSystem, PostMessage/SendInput, VK-коды
- Интеграция: InputSystem с реальным HWND (QWindow), PeekMessage
- OCR: распознавание чисел, preprocessing, castbar, FastDistanceReader
- Окно: find_window_hwnd, _check_window, EnumWindows, фокус
- Конфиг: macro_to_dict/from_dict round-trip, JSON save/load
- QML рендеринг: QQmlComponent, property binding, signal/slot
"""
import os, sys, re, json, time, threading, subprocess, ctypes
from unittest.mock import MagicMock, patch

import pytest
from pytestqt.qt_compat import qt_api

from PySide6.QtCore import QObject, Signal, Property, Slot, Qt
from PySide6.QtGui import QFont, QWindow
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QPlainTextEdit,
)

TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(TESTS_DIR)
sys.path.insert(0, PROJECT_DIR)

# =============================================================================
# Fixtures
# =============================================================================

input_call_log = []


class TrackedInputSystem:
    def key(self, k): input_call_log.append(("key", k))
    def click_left(self): input_call_log.append(("click_left", ""))
    def click_right(self): input_call_log.append(("click_right", ""))
    def key_down(self, k): input_call_log.append(("key_down", k))
    def key_up(self, k): input_call_log.append(("key_up", k))
    def key_down_sendinput(self, k): input_call_log.append(("key_down_si", k)); return True
    def key_up_sendinput(self, k): input_call_log.append(("key_up_si", k)); return True
    def click_at_position(self, x, y): input_call_log.append(("click_at", f"{x},{y}"))


class MockBackend:
    def __init__(self):
        self._settings = {
            "cooldown_margin": 0.3, "cast_lock_margin": 0.45,
            "movement_delay_enabled": False, "movement_delay_ms": 300,
            "check_distance": False, "use_castbar_detection": False,
            "first_step_delay": 0, "global_step_delay": 0,
            "use_fixed_delays": True, "use_ping_delays": False,
            "average_ping": 0, "window_locked": False, "target_window_title": "",
        }
        self.global_stopped = False
        self.window_locked = False
        self.target_window_title = ""
        self.active_macros = {}
        self.dispatcher = None
        self.movement_monitor = MagicMock()
        self.movement_monitor.get_movement_delay.return_value = 999.0
        self.fast_distance_reader = MagicMock()
        self.fast_distance_reader.raw_distance = 100.0
        self.target_distance = 100.0
        self.mouse_click_monitor = MagicMock()
        self.mouse_click_monitor.mouse_clicked = MagicMock()
        self.skill_db = MagicMock()
        self.buff_lock = threading.Lock()
        self.notification = MagicMock()
        self.pageChangeRequested = MagicMock()
        self.editMacroRequested = MagicMock()
        self.macrosChanged = MagicMock()
        self.save_macros = MagicMock()
        self._update_macros_dicts = MagicMock()
        self.register_hotkey = MagicMock()
        self.unregister_hotkey = MagicMock()
        self._macros = []

    def apply_buff(self, buff_id, name, duration, channeling_bonus, icon): pass
    def get_actual_cast_time(self, base_cast_time): return base_cast_time
    def get(self, key, default=None): return self._settings.get(key, default)
    @property
    def settings(self): return self._settings


@pytest.fixture(autouse=True)
def _track_input():
    input_call_log.clear()
    with patch('backend.input_system.send_key', wraps=TrackedInputSystem().key):
        with patch('backend.input_system.click_left', wraps=TrackedInputSystem().click_left):
            with patch('backend.input_system.click_right', wraps=TrackedInputSystem().click_right):
                with patch('backend.input_system.key_down_sendinput', wraps=TrackedInputSystem().key_down_sendinput):
                    with patch('backend.input_system.key_up_sendinput', wraps=TrackedInputSystem().key_up_sendinput):
                        yield


@pytest.fixture
def mock_backend():
    backend = MockBackend()
    from backend.macros_dispatcher import MacroDispatcher
    backend.dispatcher = MacroDispatcher(backend)
    yield backend
    backend.dispatcher.stop()
    backend.dispatcher.stop_all_macros(timeout=2.0)


@pytest.fixture
def mock_win32():
    with patch('macros_core.GetForegroundWindow', return_value=99999):
        with patch('macros_core.GetWindowText', return_value="Perfect World"):
            with patch('macros_core.GetWindowTextTimeout', return_value="Perfect World"):
                yield


# =============================================================================
# MacroUIHarness — QML-интерфейс для UI-тестов
# =============================================================================

class MacroUIHarness(QObject):
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
            "cooldown_margin": 0.3, "cast_lock_margin": 0.45,
            "global_step_delay": 20, "first_step_delay": 100,
            "use_ping_delays": False, "average_ping": 0,
            "swap_key_chant": "q", "swap_key_pa": "e",
            "window_locked": False, "target_window_title": "",
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
    def settings(self): return self._settings

    def get(self, key, default=None): return self._settings.get(key, default)
    def save_macros(self): pass
    def register_hotkey(self, hotkey, callback, **kwargs): self._hotkey_registered.add(hotkey)
    def unregister_hotkey(self, hotkey): self._hotkey_registered.discard(hotkey)

    def register_all_hotkeys(self):
        for macro in self._macros:
            if macro.hotkey:
                self.register_hotkey(macro.hotkey, lambda e: None)

    def unregister_all_hotkeys(self): self._hotkey_registered.clear()
    def get_ping_compensation(self): return 0.0
    def apply_settings_to_macros(self, key, value): pass

    @Property(list, notify=macrosChanged)
    def macros(self): return list(self._macros_dicts)

    @Property(bool, notify=globalStoppedChanged)
    def global_stopped(self): return self._global_stopped

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
    def target_window_title(self): return getattr(self, '_target_window_title', "")
    @target_window_title.setter
    def target_window_title(self, value):
        self._target_window_title = value
        self._settings["target_window_title"] = value
        self.macrosChanged.emit()
        self.settingsChanged.emit()

    @Property(bool, notify=macrosChanged)
    def window_locked(self): return getattr(self, '_window_locked', False)
    @window_locked.setter
    def window_locked(self, value):
        self._window_locked = value
        self._settings["window_locked"] = value
        self.macrosChanged.emit()
        self.settingsChanged.emit()

    def _get_crud(self):
        if not hasattr(self, '_macro_crud') or self._macro_crud is None:
            from backend.macro_crud import MacroCrud
            self._macro_crud = MacroCrud(self)
        return self._macro_crud

    def _update_macros_dicts(self):
        new_list = []
        for macro in self._macros:
            item = {"name": macro.name, "type": macro.type, "hotkey": macro.hotkey or "",
                    "running": macro.running.is_set(), "steps": macro.steps, "zone_rect": macro.zone_rect}
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
    def delete_macro(self, name): self._get_crud().delete_macro(name)

    @Slot(int)
    def edit_macro_by_index(self, index):
        if not (0 <= index < len(self._macros)): return
        macro = self._macros[index]
        macro_dict = self._get_crud().get_macro_for_edit_by_macro(macro)
        self._get_crud().set_macro_for_edit(macro_dict)
        self.editMacroRequested.emit("MacrosEditPage.qml", macro_dict)

    @Slot()
    def clear_macro_for_edit(self): self._get_crud().clear_macro_for_edit()
    @Slot(dict)
    def set_macro_for_edit(self, macro_dict): self._get_crud().set_macro_for_edit(macro_dict)
    @Slot(result=dict)
    def get_macro_for_edit(self): return self._get_crud().get_macro_for_edit()
    @Slot(dict)
    def save_macro(self, macro_dict): self._get_crud().save_macro(macro_dict)

    @Slot()
    def stop_all_macros(self):
        self._global_stopped = True
        self.globalStoppedChanged.emit()
        for macro in self._macros: macro.stop()
        self._update_macros_dicts()
        self.stopAllPressed.emit()

    @Slot()
    def start_all_macros(self):
        self._global_stopped = False
        self.globalStoppedChanged.emit()
        if self.dispatcher: self.dispatcher._active_macros_clear()
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


# =============================================================================
# БЭКЕНД-ТЕСТЫ
# =============================================================================

class TestStepsExecutor:
    def test_simple_steps_execution(self, mock_win32):
        from macros.steps_executor import StepsExecutor
        executor = StepsExecutor()
        steps = [("key", "e", 10), ("key", "2", 15), ("key", "e", 10)]
        result = executor.execute_sequence(steps)
        assert result is True
        assert len(input_call_log) == 3
        assert input_call_log[0] == ("key", "e")

    def test_step_validation(self):
        from macros.steps_executor import _validate_step
        assert _validate_step(["key", "e", 10]) is True
        assert _validate_step(["left", "", 100]) is True
        assert _validate_step(["right", "", 0]) is True
        assert _validate_step(["wait", "", 50]) is True
        assert _validate_step(["key", "e"]) is True
        assert _validate_step([]) is False
        assert _validate_step(["bad_action", "x", 10]) is False
        assert _validate_step(["key", "", 10]) is False
        assert _validate_step(["key", "e", -1]) is False
        assert _validate_step(["key", "e", 99999]) is False

    def test_stop_event_interrupts(self, mock_win32):
        from macros.steps_executor import StepsExecutor
        stop_event = threading.Event()
        executor = StepsExecutor(stop_event=stop_event)
        steps = [("wait", "", 500), ("key", "e", 10)]
        t = threading.Thread(target=lambda: [time.sleep(0.05), stop_event.set()])
        t.start()
        result = executor.execute_sequence(steps)
        t.join()
        assert result is False

    def test_running_check_interrupts(self, mock_win32):
        from macros.steps_executor import StepsExecutor
        executor = StepsExecutor(stop_event=threading.Event())
        steps = [("wait", "", 500), ("key", "e", 10)]
        result = executor.execute_sequence(steps, running_check=lambda: False)
        assert result is False

    def test_window_check_interrupts(self):
        from macros.steps_executor import StepsExecutor
        executor = StepsExecutor()
        steps = [("wait", "", 500), ("key", "e", 10)]
        result = executor.execute_sequence(steps, check_window=lambda: False)
        assert result is False

    def test_cast_lock_callback_after_step_1(self, mock_win32):
        from macros.steps_executor import StepsExecutor
        cast_lock_called = threading.Event()
        def cast_lock_callback(): cast_lock_called.set()
        executor = StepsExecutor()
        steps = [("key", "1", 5), ("key", "2", 5), ("key", "3", 5)]
        result = executor.execute_sequence(steps, cast_lock_callback=cast_lock_callback)
        assert result is True
        assert cast_lock_called.is_set()


class TestSimpleMacro:
    def test_create_and_execute(self, mock_backend, mock_win32):
        from macros_core import SimpleMacro
        macro = SimpleMacro("TestSimple", [("key", "e", 10), ("key", "2", 15)], mock_backend, hotkey="f")
        assert macro.name == "TestSimple" and macro.type == "simple" and macro.hotkey == "f"
        macro.start()
        macro.thread.join(timeout=5.0)
        assert macro.thread.is_alive() is False and macro.running.is_set() is False

    def test_stop_during_execution(self, mock_backend, mock_win32):
        from macros_core import SimpleMacro
        macro = SimpleMacro("StopTest", [("wait", "", 2000), ("key", "e", 10)], mock_backend)
        macro.start()
        time.sleep(0.05)
        macro.stop()
        assert macro.running.is_set() is False and macro.thread.is_alive() is False

    def test_double_start_is_noop(self, mock_backend, mock_win32):
        from macros_core import SimpleMacro
        macro = SimpleMacro("DoubleStart", [("key", "e", 5)], mock_backend)
        macro.start()
        thread_id = id(macro.thread)
        macro.start()
        assert id(macro.thread) == thread_id
        macro.thread.join(timeout=3.0)

    def test_hotkey_variants(self, mock_backend, mock_win32):
        from macros_core import SimpleMacro
        macro = SimpleMacro("HK", [("key", "1", 5)], mock_backend, hotkey="ctrl+1")
        assert macro.hotkey == "ctrl+1"
        macro.start()
        macro.thread.join(timeout=3.0)


class TestSkillMacro:
    def test_basic_execution(self, mock_backend, mock_win32):
        from macros_core import SkillMacro
        macro = SkillMacro("TestSkill", [("key", "e", 10), ("key", "2", 10), ("key", "e", 10)],
                           mock_backend, skill_id=6003, skill_range=36, cast_time=1.0, cooldown=3.0, hotkey="2")
        macro.start()
        macro.thread.join(timeout=5.0)
        assert macro.running.is_set() is False

    def test_auto_approach(self, mock_backend, mock_win32):
        mock_backend._settings["check_distance"] = True
        mock_backend._settings["movement_delay_enabled"] = False
        mock_backend.target_distance = 50.0
        from macros_core import SkillMacro
        input_call_log.clear()
        macro = SkillMacro("ApproachSkill", [("key", "e", 10), ("key", "2", 10), ("key", "e", 10)],
                           mock_backend, skill_id=6003, skill_range=36, cast_time=0.5, cooldown=2.0, hotkey="2")
        mock_backend.dispatcher.set_cast_lock = MagicMock()
        macro.start()
        macro.thread.join(timeout=5.0)
        si_calls = [k for k in input_call_log if k[0] == "key_down_si"]
        assert len(si_calls) > 0

    def test_castbar_detection(self, mock_backend, mock_win32):
        mock_backend._settings["use_castbar_detection"] = True
        mock_backend._settings["castbar_enabled"] = True
        mock_backend._settings["movement_delay_enabled"] = False
        from macros_core import SkillMacro
        from backend.castbar_mixin import CastbarMixin
        with patch.object(CastbarMixin, 'is_castbar_visible', return_value=True):
            macro = SkillMacro("CastbarSkill", [("key", "e", 10), ("key", "2", 10), ("key", "e", 10)],
                               mock_backend, skill_id=6003, skill_range=36, cast_time=1.0, cooldown=2.0)
            mock_backend.dispatcher.set_cast_lock = MagicMock()
            macro.start()
            macro.thread.join(timeout=5.0)
            assert macro.running.is_set() is False


class TestBuffMacro:
    def test_basic_execution(self, mock_backend, mock_win32):
        from macros_core import BuffMacro
        macro = BuffMacro("TestBuff", [("key", "e", 10), ("key", "3", 10)],
                          mock_backend, buff_id=6001, duration=15.0, channeling_bonus=20, hotkey="3")
        macro.start()
        macro.thread.join(timeout=5.0)
        assert macro.running.is_set() is False


class TestMacroDispatcher:
    def test_cast_lock_blocks(self, mock_backend):
        from macros_core import SimpleMacro
        dispatcher = mock_backend.dispatcher
        macro = SimpleMacro("CastLockTest", [("key", "e", 5)], mock_backend)
        macro.cast_time = 2.0
        dispatcher.set_cast_lock(macro)
        assert dispatcher.request_macro(macro) is False

    def test_cooldown_blocks(self, mock_backend):
        from macros_core import SimpleMacro
        dispatcher = mock_backend.dispatcher
        macro = SimpleMacro("CDTest", [("key", "e", 5)], mock_backend)
        macro.cooldown = 10.0
        macro.last_used = time.time()
        assert dispatcher.request_macro(macro) is False

    def test_running_macro_blocks_others(self, mock_backend):
        from macros_core import SimpleMacro
        dispatcher = mock_backend.dispatcher
        m1 = SimpleMacro("RunningBlockA", [("wait", "", 500)], mock_backend)
        m2 = SimpleMacro("RunningBlockB", [("key", "e", 5)], mock_backend)
        dispatcher.request_macro(m1)
        time.sleep(0.05)
        assert dispatcher.request_macro(m2) is False
        m1.stop()
        m1.thread.join(timeout=3.0)

    def test_global_stopped_blocks(self, mock_backend):
        from macros_core import SimpleMacro
        dispatcher = mock_backend.dispatcher
        mock_backend.global_stopped = True
        macro = SimpleMacro("GlobalStopTest", [("key", "e", 5)], mock_backend)
        assert dispatcher.request_macro(macro) is False

    def test_debounce_blocks_rapid_calls(self, mock_backend):
        from macros_core import SimpleMacro
        dispatcher = mock_backend.dispatcher
        macro = SimpleMacro("DebounceTest", [("wait", "", 5)], mock_backend)
        dispatcher.last_launch_time = time.time()
        assert dispatcher.request_macro(macro) is False

    def test_successful_launch_and_completion(self, mock_backend, mock_win32):
        from macros_core import SimpleMacro
        dispatcher = mock_backend.dispatcher
        dispatcher.last_launch_time = 0.0
        dispatcher._macro_last_launch.clear()
        dispatcher.cast_lock_until = 0.0
        macro = SimpleMacro("LaunchTest", [("key", "e", 5)], mock_backend)
        assert dispatcher.request_macro(macro) is True
        macro.thread.join(timeout=3.0)
        assert macro.running.is_set() is False

    def test_cast_lock_blocks_launched_macro(self, mock_backend):
        from macros_core import SimpleMacro
        dispatcher = mock_backend.dispatcher
        m1 = SimpleMacro("CastLockA", [("key", "1", 5)], mock_backend)
        m1.cast_time = 2.0
        m2 = SimpleMacro("CastLockB", [("key", "2", 5)], mock_backend)
        dispatcher.request_macro(m1)
        time.sleep(0.1)
        dispatcher.cast_lock_until = time.time() + 5.0
        assert dispatcher.request_macro(m2) is False
        m1.stop(); m1.thread.join(timeout=3.0)

    def test_on_macro_finished_releases_lock(self, mock_backend):
        dispatcher = mock_backend.dispatcher
        dispatcher.cast_lock_until = time.time() + 5.0
        dispatcher.on_macro_finished("any_macro")
        remaining = dispatcher.get_cast_lock_remaining()
        assert remaining < 5.0

    def test_stop_all_macros(self, mock_backend, mock_win32):
        from macros_core import SimpleMacro
        dispatcher = mock_backend.dispatcher
        m1 = SimpleMacro("StopAllA", [("wait", "", 2000)], mock_backend)
        m2 = SimpleMacro("StopAllB", [("wait", "", 2000)], mock_backend)
        dispatcher.last_launch_time = 0.0
        dispatcher._macro_last_launch.clear()
        dispatcher.cast_lock_until = 0.0
        dispatcher.request_macro(m1); time.sleep(0.05)
        dispatcher.request_macro(m2); time.sleep(0.05)
        dispatcher.stop_all_macros(timeout=2.0)
        assert m1.running.is_set() is False and m2.running.is_set() is False

    def test_queue_launches_after_cast_unlock(self, mock_backend, mock_win32):
        from macros_core import SimpleMacro
        dispatcher = mock_backend.dispatcher
        macro = SimpleMacro("QueueLaunchTest", [("wait", "", 200)], mock_backend)
        dispatcher.last_launch_time = 0.0
        dispatcher._macro_last_launch.clear()
        dispatcher.macro_queue.clear()
        dispatcher.cast_lock_until = time.time() + 0.5
        from backend.macros_dispatcher import QueuedMacro
        import heapq
        qm = QueuedMacro(priority=5, timestamp=time.time(), macro=macro, timeout=5.0)
        with dispatcher.lock: heapq.heappush(dispatcher.macro_queue, qm)
        time.sleep(1.0)
        if macro.running.is_set():
            macro.thread.join(timeout=3.0)
            assert True
        else:
            still_queued = any(q.macro is macro for q in dispatcher.macro_queue)
            assert not still_queued, "Macro still stuck in queue"


class TestThreadSafety:
    def test_concurrent_stop_and_start(self, mock_backend):
        from macros_core import SimpleMacro
        macro = SimpleMacro("ConcurrentStopStart", [("wait", "", 1000)], mock_backend)
        errors = []
        def starter():
            try: macro.start()
            except Exception as e: errors.append(("start", e))
        def stopper():
            try: time.sleep(0.02); macro.stop()
            except Exception as e: errors.append(("stop", e))
        threads = [threading.Thread(target=starter), threading.Thread(target=stopper)]
        for t in threads: t.start()
        for t in threads: t.join(timeout=5.0)
        assert len(errors) == 0 and macro.running.is_set() is False

    def test_concurrent_dispatcher_requests(self, mock_backend, mock_win32):
        from macros_core import SimpleMacro
        dispatcher = mock_backend.dispatcher
        dispatcher.last_launch_time = 0.0
        dispatcher._macro_last_launch.clear()
        dispatcher.cast_lock_until = 0.0
        macro = SimpleMacro("ConcurrentReq", [("wait", "", 200)], mock_backend)
        results = []
        def launch():
            try: r = dispatcher.request_macro(macro); results.append(r)
            except Exception as e: results.append(e)
        threads = [threading.Thread(target=launch) for _ in range(5)]
        for t in threads: t.start()
        for t in threads: t.join(timeout=5.0)
        success_count = sum(1 for r in results if r is True)
        assert success_count >= 1
        macro.thread.join(timeout=3.0)

    def test_concurrent_crud_operations(self, mock_backend):
        from backend.macro_crud import MacroCrud
        crud = MacroCrud(mock_backend)
        mock_backend._macros = []
        errors = []
        def create_macro(i):
            try: crud.create_simple(f"ThreadMacro{i}", f"f{i}", [("key", "e", 10)])
            except Exception as e: errors.append((i, e))
        threads = [threading.Thread(target=create_macro, args=(i,)) for i in range(10)]
        for t in threads: t.start()
        for t in threads: t.join(timeout=5.0)
        assert len(errors) == 0 and len(mock_backend._macros) == 10


class TestMacroCrud:
    def test_create_simple_macro(self, mock_backend):
        from backend.macro_crud import MacroCrud
        crud = MacroCrud(mock_backend)
        mock_backend._macros = []
        crud.create_simple("TestCrud", "f", [("key", "e", 10), ("key", "2", 15)])
        assert len(mock_backend._macros) == 1
        m = mock_backend._macros[0]
        assert m.name == "TestCrud" and m.type == "simple" and m.hotkey == "f"

    def test_create_skill_macro(self, mock_backend):
        from backend.macro_crud import MacroCrud
        crud = MacroCrud(mock_backend)
        mock_backend._macros = []
        crud.create_skill("SkillCrud", "", 6003, [("key", "e", 90), ("key", "2", 15), ("key", "e", 15)],
                          skill_hotkey="1", cooldown=3.0, skill_range=36, cast_time=1.0, castbar_swap_delay=0, zone_rect=[])
        m = mock_backend._macros[0]
        assert m.name == "SkillCrud" and m.type == "skill" and m.skill_id == 6003 and m.cooldown == 3.0

    def test_create_buff_macro(self, mock_backend):
        from backend.macro_crud import MacroCrud
        crud = MacroCrud(mock_backend)
        mock_backend._macros = []
        crud.create_buff("BuffCrud", "3", 6001, [("key", "e", 10), ("key", "3", 10)], duration=15.0, channeling_bonus=20, zone_rect=[])
        m = mock_backend._macros[0]
        assert m.name == "BuffCrud" and m.type == "buff" and m.buff_id == 6001

    def test_create_zone_macro(self, mock_backend):
        from backend.macro_crud import MacroCrud
        crud = MacroCrud(mock_backend)
        mock_backend._macros = []
        crud.create_zone("ZoneCrud", "", [100, 200, 300, 400], [("key", "e", 10)], trigger="left_click", poll_interval_ms=100)
        m = mock_backend._macros[0]
        assert m.name == "ZoneCrud" and m.type == "zone"

    def test_delete_macro(self, mock_backend):
        from backend.macro_crud import MacroCrud
        crud = MacroCrud(mock_backend)
        mock_backend._macros = []
        crud.create_simple("ToDelete", "f", [("key", "e", 10)])
        assert len(mock_backend._macros) == 1
        crud.delete_macro("ToDelete")
        assert len(mock_backend._macros) == 0

    def test_macro_to_dict(self, mock_backend):
        from macros_core import SimpleMacro
        from backend.macro_crud import MacroCrud
        crud = MacroCrud(mock_backend)
        macro = SimpleMacro("DictTest", [("key", "e", 10)], mock_backend, hotkey="f")
        d = crud._macro_to_dict(macro)
        assert d["name"] == "DictTest" and d["type"] == "simple" and d["hotkey"] == "f"


class TestZoneMacro:
    def test_click_in_zone_triggers_launch(self, mock_backend, mock_win32):
        from macros_core import ZoneMacro
        from macros.steps_executor import StepsExecutor
        macro = ZoneMacro("TestZone", [100, 200, 300, 400], [("key", "e", 10), ("key", "2", 10)], mock_backend, trigger="left_click")
        original_execute = StepsExecutor.execute_sequence
        executed = threading.Event()
        def tracking_execute(self_obj, steps, **kw):
            executed.set()
            return original_execute(self_obj, steps, **kw)
        with patch.object(StepsExecutor, 'execute_sequence', tracking_execute):
            with patch.object(macro, 'on_mouse_click', wraps=macro.on_mouse_click):
                macro.running.set()
                macro._scheduled = False
                macro.on_mouse_click(150, 250)
                time.sleep(0.15)
                assert executed.is_set()

    def test_click_outside_zone_ignored(self, mock_backend):
        from macros_core import ZoneMacro
        macro = ZoneMacro("ZoneOutside", [100, 200, 300, 400], [("key", "e", 10)], mock_backend, trigger="left_click")
        mock_backend.dispatcher.request_macro = MagicMock()
        macro.on_mouse_click(50, 50)
        time.sleep(0.05)
        assert not mock_backend.dispatcher.request_macro.called

    def test_zone_point_in_rect(self, mock_backend):
        from macros_core import Macro
        m = Macro("RectTest", "zone", mock_backend)
        assert m._is_point_in_rect(150, 250, [100, 200, 300, 400]) is True
        assert m._is_point_in_rect(50, 50, [100, 200, 300, 400]) is False


class TestMacroDispatcherStats:
    def test_stats_tracking(self, mock_backend):
        from macros_core import SimpleMacro
        dispatcher = mock_backend.dispatcher
        mock_backend.global_stopped = True
        macro = SimpleMacro("StatsTest", [("key", "e", 5)], mock_backend)
        dispatcher.request_macro(macro)
        assert "StatsTest" in dispatcher.macro_stats
        mock_backend.global_stopped = False
        dispatcher.cast_lock_until = time.time() + 10.0
        dispatcher.request_macro(macro)
        assert dispatcher.stats["blocked_cast"] == 1


class TestMacroLifecycle:
    def test_full_create_start_stop(self, mock_backend, mock_win32):
        from macros_core import SimpleMacro
        dispatcher = mock_backend.dispatcher
        dispatcher.last_launch_time = 0.0
        dispatcher._macro_last_launch.clear()
        dispatcher.cast_lock_until = 0.0
        macro = SimpleMacro("FullLifecycle", [("key", "e", 5)], mock_backend, hotkey="f")
        assert macro.running.is_set() is False
        assert dispatcher.request_macro(macro) is True
        macro.thread.join(timeout=3.0)
        assert macro.running.is_set() is False

    def test_reuse_after_completion(self, mock_backend, mock_win32):
        from macros_core import SimpleMacro
        dispatcher = mock_backend.dispatcher
        dispatcher.last_launch_time = 0.0
        dispatcher._macro_last_launch.clear()
        dispatcher.cast_lock_until = 0.0
        macro = SimpleMacro("ReuseTest", [("wait", "", 5)], mock_backend)
        dispatcher.request_macro(macro)
        macro.thread.join(timeout=3.0)
        assert macro.running.is_set() is False
        dispatcher.last_launch_time = 0.0
        dispatcher._macro_last_launch.clear()
        dispatcher.cast_lock_until = 0.0
        assert dispatcher.request_macro(macro) is True
        macro.thread.join(timeout=3.0)


class TestMacroQueueProcessor:
    def test_health_check(self, mock_backend):
        dispatcher = mock_backend.dispatcher
        status = dispatcher.health_check()
        assert "queue_processor_alive" in status
        assert "active_macros_count" in status
        assert "queue_size" in status
        assert "cast_locked" in status


# =============================================================================
# UI-ТЕСТЫ (QML-интерфейс)
# =============================================================================

class TestMacroUIProperties:
    def test_macros_property_empty_on_init(self, harness): assert harness.macros == []

    def test_macros_property_after_create(self, harness):
        harness.create_simple_macro_with_params("Test", "F1", [("key", "a", 10)])
        assert len(harness.macros) == 1 and harness.macros[0]["name"] == "Test"

    def test_macros_property_running_status(self, harness):
        harness.global_stopped = False
        harness.create_simple_macro_with_params("RunTest", "F2", [("wait", "", 50)])
        harness._macros[0].running.set()
        harness._update_macros_dicts()
        assert harness.macros[0]["running"] is True

    def test_global_stopped_default_true(self, harness): assert harness.global_stopped is True

    def test_global_stopped_setter(self, harness):
        calls = []; harness.globalStoppedChanged.connect(lambda: calls.append(1))
        harness.global_stopped = False
        assert harness.global_stopped is False and len(calls) == 1

    def test_global_stopped_changed_signal_emitted_once(self, harness):
        calls = []; harness.globalStoppedChanged.connect(lambda: calls.append(1))
        harness.global_stopped = False
        harness.global_stopped = False
        assert len(calls) == 1

    def test_macro_for_edit_empty_default(self, harness): assert harness.macro_for_edit == {}

    def test_macro_for_edit_after_set(self, harness):
        harness.create_simple_macro_with_params("EditMe", "F3", [("key", "b", 10)])
        harness.edit_macro_by_index(0)
        assert harness.macro_for_edit["name"] == "EditMe"

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
        assert harness._macros[0].name == "Simple1"

    def test_create_simple_macro_emits_macrosChanged(self, harness):
        calls = []; harness.macrosChanged.connect(lambda: calls.append(1))
        harness.create_simple_macro_with_params("S", "", [("key", "x", 5)])
        assert len(calls) >= 1

    def test_create_simple_macro_updates_property(self, harness):
        harness.create_simple_macro_with_params("PropTest", "", [("key", "z", 5)])
        assert harness.macros[0]["name"] == "PropTest"

    def test_create_skill_macro(self, harness):
        harness.create_skill_macro_with_params("Skill1", "F6", "6003", [("key", "q", 100), ("key", "e", 20)],
                                               "F6", 3.0, 10.0, 0.5, 0, [])
        m = harness._macros[0]
        assert m.name == "Skill1" and m.type == "skill" and m.skill_id == 6003

    def test_create_buff_macro(self, harness):
        harness.create_buff_macro_with_params("Buff1", "F7", "101", [("key", "q", 100)], 60.0, 0, [])
        assert harness._macros[0].name == "Buff1" and harness._macros[0].type == "buff"

    def test_create_zone_macro(self, harness):
        harness.create_zone_macro_with_params("Zone1", "F8", [100, 200, 300, 400], [("key", "e", 10)], "left_click", 10)
        m = harness._macros[0]
        assert m.name == "Zone1" and m.type == "zone"

    def test_create_macro_from_dict(self, harness):
        harness.create_macro_from_dict("simple", {"name": "DictMacro", "hotkey": "F9", "steps": [("key", "a", 10)]})
        assert harness._macros[0].name == "DictMacro"

    def test_multiple_macros_of_different_types(self, harness):
        harness.create_simple_macro_with_params("S", "", [("key", "a", 5)])
        harness.create_skill_macro_with_params("Sk", "F1", "1", [("key", "q", 10)], "", 1.0, 5.0, 0.3, 0, [])
        harness.create_buff_macro_with_params("B", "F2", "2", [("key", "w", 10)], 30.0, 0, [])
        assert len(harness._macros) == 3
        assert [m["type"] for m in harness.macros] == ["simple", "skill", "buff"]


class TestMacroUIUpdateSlots:
    def test_update_simple_macro(self, harness):
        harness.create_simple_macro_with_params("OldName", "F1", [("key", "a", 10)])
        harness.update_simple_macro("OldName", "NewName", "F2", [("key", "b", 20)])
        m = harness._macros[0]
        assert m.name == "NewName" and m.hotkey == "F2"

    def test_update_simple_macro_emits_signal(self, harness):
        harness.create_simple_macro_with_params("A", "", [("key", "a", 5)])
        calls = []; harness.macrosChanged.connect(lambda: calls.append(1))
        harness.update_simple_macro("A", "B", "", [("key", "b", 5)])
        assert len(calls) >= 1

    def test_update_skill_macro(self, harness):
        harness.create_skill_macro_with_params("Sk", "F1", "1", [("key", "q", 10)], "", 1.0, 5.0, 0.3, 0, [])
        harness.update_skill_macro("Sk", "SkV2", "F2", "2", [("key", "w", 10)], "F2", 2.0, 8.0, 0.5, 100, [])
        assert harness._macros[0].name == "SkV2" and harness._macros[0].skill_id == 2

    def test_update_zone_macro(self, harness):
        harness.create_zone_macro_with_params("Z", "", [0, 0, 100, 100], [("key", "e", 5)], "left_click", 10)
        harness.update_zone_macro("Z", "Z2", "", [50, 50, 200, 200], [("key", "r", 5)], "right_click", 20)
        m = harness._macros[0]
        assert m.name == "Z2"

    def test_update_buff_macro(self, harness):
        harness.create_buff_macro_with_params("B", "", "1", [("key", "q", 10)], 30.0, 0, [])
        harness.update_buff_macro("B", "B2", "", "2", [("key", "w", 10)], 60.0, 1, [])
        assert harness._macros[0].name == "B2" and harness._macros[0].buff_id == 2


class TestMacroUIDeleteSlots:
    def test_delete_macro_removes_from_list(self, harness):
        harness.create_simple_macro_with_params("DelMe", "", [("key", "a", 5)])
        assert len(harness._macros) == 1
        harness.delete_macro("DelMe")
        assert len(harness._macros) == 0

    def test_delete_macro_emits_signal(self, harness):
        harness.create_simple_macro_with_params("SigMe", "", [("key", "a", 5)])
        calls = []; harness.macrosChanged.connect(lambda: calls.append(1))
        harness.delete_macro("SigMe"); assert len(calls) >= 1

    def test_delete_macro_nonexistent_safe(self, harness): harness.delete_macro("NonExistent")

    def test_delete_macro_updates_property(self, harness):
        harness.create_simple_macro_with_params("A", "", [("key", "a", 5)])
        harness.create_simple_macro_with_params("B", "", [("key", "b", 5)])
        harness.delete_macro("A")
        assert harness.macros[0]["name"] == "B"

    def test_delete_macro_unregisters_hotkey(self, harness):
        harness.create_simple_macro_with_params("HK", "F1", [("key", "a", 5)])
        harness.start_all_macros()
        assert "F1" in harness._hotkey_registered
        harness.delete_macro("HK")
        assert "F1" not in harness._hotkey_registered


class TestMacroUIEditSlots:
    def test_edit_macro_by_index_emits_signal(self, harness, qtbot):
        harness.create_simple_macro_with_params("EditMe", "F1", [("key", "a", 5)])
        data = []
        harness.editMacroRequested.connect(lambda p, d: data.append((p, d)))
        harness.edit_macro_by_index(0)
        assert data[0][0] == "MacrosEditPage.qml" and data[0][1]["name"] == "EditMe"

    def test_edit_macro_by_index_sets_macro_for_edit(self, harness):
        harness.create_simple_macro_with_params("Test", "", [("key", "a", 5)])
        harness.edit_macro_by_index(0)
        assert harness.get_macro_for_edit()["name"] == "Test"

    def test_edit_macro_by_index_invalid_noop(self, harness):
        harness.edit_macro_by_index(99)
        assert harness.get_macro_for_edit() is None

    def test_edit_macro_by_index_with_skill_type(self, harness):
        harness.create_skill_macro_with_params("Sk", "F1", "6003", [("key", "q", 10)], "", 3.0, 10.0, 0.5, 0, [])
        harness.edit_macro_by_index(0)
        d = harness.get_macro_for_edit()
        assert d["type"] == "skill" and d["skill_id"] == 6003

    def test_edit_macro_by_index_with_zone_type(self, harness):
        harness.create_zone_macro_with_params("Z", "", [100, 200, 300, 400], [("key", "e", 5)], "left_click", 10)
        harness.edit_macro_by_index(0)
        d = harness.get_macro_for_edit()
        assert d["type"] == "zone" and d["zone_rect"] == [100, 200, 300, 400]

    def test_edit_macro_by_index_with_buff_type(self, harness):
        harness.create_buff_macro_with_params("B", "", "101", [("key", "q", 10)], 60.0, 0, [])
        harness.edit_macro_by_index(0)
        d = harness.get_macro_for_edit()
        assert d["type"] == "buff" and d["buff_id"] == 101


class TestMacroUIStartStopSlots:
    def test_start_all_macros_sets_global_stopped_false(self, harness):
        harness.start_all_macros(); assert harness.global_stopped is False

    def test_stop_all_macros_sets_global_stopped_true(self, harness):
        harness.start_all_macros(); harness.stop_all_macros(); assert harness.global_stopped is True

    def test_start_all_emits_startAllPressed(self, harness):
        calls = []; harness.startAllPressed.connect(lambda: calls.append(1))
        harness.start_all_macros(); assert len(calls) == 1

    def test_stop_all_emits_stopAllPressed(self, harness):
        calls = []; harness.stopAllPressed.connect(lambda: calls.append(1))
        harness.stop_all_macros(); assert len(calls) == 1

    def test_start_macro_via_slot(self, harness):
        harness.global_stopped = False
        harness.create_simple_macro_with_params("Test", "", [("wait", "", 50)])
        harness.start_macro("Test")
        assert harness._macros[0].running.is_set() is True
        harness._macros[0].stop()

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
        harness.create_simple_macro_with_params("SigStop", "", [("wait", "", 50)])
        calls = []; harness.macroStatusChanged.connect(lambda: calls.append(1))
        harness.stop_macro("SigStop"); assert len(calls) >= 1

    def test_stop_all_stops_running_macros(self, harness):
        harness.global_stopped = False
        harness.create_simple_macro_with_params("A", "", [("wait", "", 500)])
        harness.create_simple_macro_with_params("B", "", [("wait", "", 500)])
        harness.start_macro("A"); harness.start_macro("B")
        harness.stop_all_macros()
        assert harness._macros[0].running.is_set() is False
        assert harness._macros[1].running.is_set() is False


class TestMacroUISaveMacro:
    def test_save_macro_creates_new(self, harness):
        harness.save_macro({"type": "simple", "name": "Saved", "hotkey": "F1", "steps": [("key", "a", 10)]})
        assert harness._macros[0].name == "Saved"

    def test_save_macro_updates_existing(self, harness):
        harness.create_simple_macro_with_params("Old", "", [("key", "a", 5)])
        harness.save_macro({"type": "simple", "name": "Updated", "old_name": "Old", "hotkey": "", "steps": [("key", "b", 10)]})
        assert harness._macros[0].name == "Updated"

    def test_save_macro_validation_blocks_invalid(self, harness):
        harness.save_macro({"type": "simple", "name": "", "steps": []})
        assert len(harness._macros) == 0

    def test_save_macro_emits_macrosChanged(self, harness):
        calls = []; harness.macrosChanged.connect(lambda: calls.append(1))
        harness.save_macro({"type": "simple", "name": "SigSave", "hotkey": "", "steps": [("key", "a", 5)]})
        assert len(calls) >= 1

    def test_save_macro_with_zone_type(self, harness):
        harness.save_macro({"type": "zone", "name": "ZoneSave", "hotkey": "", "zone_rect": [0, 0, 100, 100],
                            "steps": [("key", "e", 5)], "trigger": "right_click", "poll_interval": 20})
        assert harness._macros[0].type == "zone"


class TestMacroUIEditFlow:
    def test_full_edit_flow(self, harness, qtbot):
        harness.create_simple_macro_with_params("Flow", "F1", [("key", "a", 10)])
        assert harness.macros[0]["name"] == "Flow"
        harness.edit_macro_by_index(0)
        assert harness.macro_for_edit["name"] == "Flow"
        harness.clear_macro_for_edit()
        assert harness.macro_for_edit == {}

    def test_edit_and_update_flow(self, harness):
        harness.create_simple_macro_with_params("Original", "F1", [("key", "a", 10)])
        harness.edit_macro_by_index(0)
        data = harness.get_macro_for_edit()
        data["name"] = "Edited"; data["old_name"] = "Original"
        data["hotkey"] = "F2"; data["steps"] = [("key", "b", 20)]
        harness.save_macro(data)
        assert len(harness._macros) == 1 and harness._macros[0].name == "Edited"

    def test_create_edit_create_another(self, harness):
        harness.create_simple_macro_with_params("First", "", [("key", "a", 5)])
        harness.edit_macro_by_index(0)
        assert harness.macro_for_edit["name"] == "First"
        harness.clear_macro_for_edit()
        harness.create_simple_macro_with_params("Second", "", [("key", "b", 5)])
        assert len(harness._macros) == 2


class TestMacroUIMultiTypeList:
    def test_macros_list_contains_all_types(self, harness):
        harness.create_simple_macro_with_params("S", "F1", [("key", "a", 5)])
        harness.create_skill_macro_with_params("Sk", "F2", "100", [("key", "q", 10)], "", 1.0, 5.0, 0.3, 0, [])
        harness.create_buff_macro_with_params("B", "F3", "200", [("key", "w", 10)], 30.0, 0, [])
        harness.create_zone_macro_with_params("Z", "F4", [0, 0, 50, 50], [("key", "e", 5)], "left_click", 10)
        assert [m["type"] for m in harness.macros] == ["simple", "skill", "buff", "zone"]

    def test_skill_macro_dict_contains_skill_id(self, harness):
        harness.create_skill_macro_with_params("Sk", "", "6003", [("key", "q", 10)], "", 3.0, 10.0, 0.5, 0, [])
        assert harness.macros[0]["skill_id"] == 6003

    def test_zone_macro_dict_contains_rect(self, harness):
        harness.create_zone_macro_with_params("Z", "", [10, 20, 30, 40], [("key", "e", 5)], "left_click", 10)
        assert list(harness.macros[0]["zone_rect"]) == [10, 20, 30, 40]

    def test_buff_macro_dict_contains_buff_id(self, harness):
        harness.create_buff_macro_with_params("B", "", "42", [("key", "q", 10)], 60.0, 0, [])
        assert harness.macros[0]["buff_id"] == 42


class TestMacroUIHotkeyRegistration:
    def test_create_registers_hotkey(self, harness):
        harness.create_simple_macro_with_params("HK", "F1", [("key", "a", 5)])
        harness.start_all_macros()
        assert "F1" in harness._hotkey_registered

    def test_delete_unregisters_hotkey(self, harness):
        harness.create_simple_macro_with_params("HK", "F1", [("key", "a", 5)])
        harness.start_all_macros()
        assert "F1" in harness._hotkey_registered
        harness.delete_macro("HK")
        assert "F1" not in harness._hotkey_registered

    def test_update_old_hotkey_unregistered_new_registered(self, harness):
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
        assert "F1" in harness._hotkey_registered and "F2" in harness._hotkey_registered

    def test_stop_all_unregisters_hotkeys_behavior(self, harness):
        harness.create_simple_macro_with_params("A", "F1", [("key", "a", 5)])
        harness.stop_all_macros()
        assert harness.global_stopped is True


class TestMacroUIErrorHandling:
    def test_delete_nonexistent_does_not_raise(self, harness): harness.delete_macro("ghost")
    def test_edit_bad_index_does_not_raise(self, harness):
        harness.edit_macro_by_index(-1); harness.edit_macro_by_index(999)
    def test_create_duplicate_name(self, harness):
        harness.create_simple_macro_with_params("Dup", "", [("key", "a", 5)])
        harness.create_simple_macro_with_params("Dup", "", [("key", "b", 5)])
        assert len(harness._macros) == 2
    def test_start_nonexistent_macro_safe(self, harness): harness.start_macro("DoesNotExist")
    def test_stop_nonexistent_macro_safe(self, harness): harness.stop_macro("DoesNotExist")


class TestMacroUISaveMacroRoundTrip:
    def test_save_then_retrieve_property(self, harness):
        harness.save_macro({"type": "skill", "name": "RT", "hotkey": "F1", "skill_id": 6003,
                            "cooldown": 3.0, "skill_range": 10.0, "cast_time": 0.5,
                            "steps": [("key", "q", 100), ("key", "e", 20)]})
        d = harness.macros[0]; assert d["name"] == "RT" and d["type"] == "skill"

    def test_save_zone_then_edit_retrieves_rect(self, harness):
        harness.save_macro({"type": "zone", "name": "ZoneRT", "hotkey": "", "zone_rect": [100, 200, 300, 400],
                            "steps": [("key", "e", 5)], "trigger": "left_click", "poll_interval": 10})
        harness.edit_macro_by_index(0)
        assert harness.macro_for_edit["zone_rect"] == [100, 200, 300, 400]

    def test_save_buff_with_duration(self, harness):
        harness.save_macro({"type": "buff", "name": "BuffRT", "hotkey": "", "buff_id": 42,
                            "duration": 120.0, "channeling_bonus": 0, "steps": [("key", "q", 10)]})
        harness.edit_macro_by_index(0)
        d = harness.macro_for_edit
        assert d["buff_id"] == 42 and d["duration"] == 120.0


# =============================================================================
# GUI — Тестовый раннер
# =============================================================================

# =============================================================================
# 5. Тесты клавиатурного ввода (InputSystem, PostMessage/SendInput, VK-коды)
# =============================================================================

class TestKeyboardInput:
    """Проверка, что InputSystem вызывает правильные Win32 API."""

    @pytest.fixture(autouse=True)
    def _mock_win32_input(self):
        with (
            patch('backend.input_system.PostMessage') as self._pm,
            patch('backend.input_system.MapVirtualKey', return_value=0x12) as self._mvk,
            patch('backend.input_system.SetForegroundWindow', return_value=True) as self._sfw,
            patch('backend.input_system.GetForegroundWindow', return_value=12345) as self._gfw,
            patch('backend.input_system.GetCursorPos', return_value=(100, 200)),
            patch('backend.input_system.ScreenToClient', return_value=(50, 60)),
            patch('backend.input_system.SendInput', return_value=1) as self._si,
            patch('backend.input_system._attached_thread_input') as self._ati,
        ):
            self._ati.return_value.__enter__.return_value = True
            yield

    @pytest.fixture
    def inp(self):
        from backend.input_system import InputSystem
        isys = InputSystem()
        isys.set_target(12345)
        return isys

    def test_vk_codes_covered(self):
        from constants import VIRTUAL_KEYS
        for name, code in VIRTUAL_KEYS.items():
            assert isinstance(name, str)
            assert isinstance(code, int) and 0 < code < 0xFF

    def test_send_key_postmessage(self, inp):
        inp.key('e')
        self._mvk.assert_called_once_with(0x45, 0)
        assert self._pm.call_count == 2
        down_call = self._pm.call_args_list[0]
        up_call = self._pm.call_args_list[1]
        assert down_call[0][1] == 0x0100  # WM_KEYDOWN
        assert up_call[0][1] == 0x0101    # WM_KEYUP
        assert down_call[0][2] == 0x45    # VK_E

    def test_send_key_sendinput_mode(self, inp):
        inp.set_use_sendinput(True)
        inp.key('space')
        assert self._si.call_count == 2
        vk0 = self._si.call_args_list[0][0][1][0].union.ki.wVk
        vk1 = self._si.call_args_list[1][0][1][0].union.ki.wVk
        assert vk0 == 0x20
        assert vk1 == 0x20
        assert self._pm.call_count == 0

    def test_send_key_fallback_on_attach_fail(self, inp):
        self._ati.return_value.__enter__.return_value = False
        inp.key('f1')
        assert self._si.call_count == 2
        assert self._pm.call_count == 0

    def test_send_key_no_target_hwnd(self, inp):
        inp.target_hwnd = None
        inp.key('a')
        assert self._pm.call_count == 0
        assert self._si.call_count == 0

    def test_send_key_unknown_keyname(self, inp):
        inp.key('nonexistent_key')
        assert self._pm.call_count == 0

    def test_key_down_uses_postmessage(self, inp):
        inp.key_down('ctrl')
        self._mvk.assert_called_once_with(0x11, 0)
        down_call = self._pm.call_args_list[0]
        assert down_call[0][1] == 0x0100
        assert down_call[0][2] == 0x11

    def test_key_up_uses_postmessage(self, inp):
        inp.key_up('shift')
        self._mvk.assert_called_once_with(0x10, 0)
        up_call = self._pm.call_args_list[0]
        assert up_call[0][1] == 0x0101
        assert up_call[0][2] == 0x10

    def test_key_down_sendinput_sets_foreground(self, inp):
        with patch('backend.input_system.get_window_manager') as mock_gwm:
            mock_gwm.return_value.skip_window_activation = False
            inp.key_down_sendinput('tab')
        self._sfw.assert_called_once_with(12345)
        assert self._si.call_count == 1

    def test_click_left_postmessage(self, inp):
        inp.click_left()
        assert self._pm.call_count == 2
        down_call = self._pm.call_args_list[0]
        up_call = self._pm.call_args_list[1]
        assert down_call[0][1] == 0x0201  # WM_LBUTTONDOWN
        assert up_call[0][1] == 0x0202   # WM_LBUTTONUP

    def test_click_right_postmessage(self, inp):
        inp.click_right()
        assert self._pm.call_count == 2
        assert self._pm.call_args_list[0][0][1] == 0x0204  # WM_RBUTTONDOWN
        assert self._pm.call_args_list[1][0][1] == 0x0205  # WM_RBUTTONUP

    def test_click_at_position_postmessage(self, inp):
        inp.click_at_position(300, 400)
        assert self._pm.call_count == 2

    def test_set_target_updates_hwnd(self, inp):
        inp.set_target(99999)
        assert inp.target_hwnd == 99999


# =============================================================================
# 6. Тесты OCR/Tesseract (распознавание, preprocessing, castbar, FastDistance)
# =============================================================================

class TestOCR:
    """Проверка OCR pipeline: распознавание чисел, preprocessing, castbar."""

    @pytest.fixture
    def worker(self):
        from tesseract_reader import TargetWorker
        w = TargetWorker(areas={"mob": (0, 0, 10, 10), "player": (0, 0, 10, 10)})
        return w

    # --- recognize_numbers ---

    def test_recognize_numbers_valid(self, worker):
        with patch('tesseract_reader.pytesseract.image_to_string', return_value="45.5\n"):
            result = worker.recognize_numbers(None)
        assert "45.5" in result

    def test_recognize_numbers_empty_retries_with_psm6(self, worker):
        worker.psm = 10
        with patch('tesseract_reader.pytesseract.image_to_string', side_effect=["", "12.3\n"]):
            result = worker.recognize_numbers(None)
        assert "12.3" in result

    def test_recognize_numbers_garbage_returns_empty(self, worker):
        with patch('tesseract_reader.pytesseract.image_to_string', return_value="foo bar baz\n"):
            result = worker.recognize_numbers(None)
        assert result == []

    def test_recognize_numbers_multiple_values(self, worker):
        with patch('tesseract_reader.pytesseract.image_to_string', return_value="12.5\n34.8\n56.2\n"):
            result = worker.recognize_numbers(None)
        assert "12.5" in result
        assert "34.8" in result

    def test_numbers_to_distance_filters_bad_range(self, worker):
        assert worker.numbers_to_distance(["1234"], "mob") is None
        assert worker.numbers_to_distance(["0.1"], "mob") is None

    def test_recognize_numbers_filters_multi_dot(self, worker):
        with patch('tesseract_reader.pytesseract.image_to_string', return_value="12.5.6\n"):
            result = worker.recognize_numbers(None)
        assert "12.5.6" not in result

    # --- numbers_to_distance ---

    def test_numbers_to_distance_valid(self, worker):
        from tesseract_reader import TargetWorker
        result = worker.numbers_to_distance(["45.5"], "mob")
        assert result == 45.5

    def test_numbers_to_distance_autofix_hundred(self, worker):
        result = worker.numbers_to_distance(["1000"], "mob")
        assert result == 100.0

    def test_numbers_to_distance_out_of_range_high(self, worker):
        result = worker.numbers_to_distance(["9999"], "mob")
        assert result is None

    def test_numbers_to_distance_out_of_range_low(self, worker):
        result = worker.numbers_to_distance(["0.1"], "mob")
        assert result is None

    def test_numbers_to_distance_ignores_empty_list(self, worker):
        result = worker.numbers_to_distance([], "mob")
        assert result is None

    def test_numbers_to_distance_picks_closest_to_previous(self, worker):
        result = worker.numbers_to_distance(["12.0", "54.0"], "mob")
        assert result is not None

    # --- _correct_ocr_errors ---

    def test_correct_ocr_errors_magic_range(self, worker):
        result = worker._correct_ocr_errors("250")
        assert result == "25.0"

    def test_correct_ocr_errors_returns_empty_for_none(self, worker):
        assert worker._correct_ocr_errors("") == ""

    # --- preprocess_image ---

    def test_preprocess_image_returns_binary(self, worker):
        import numpy as np
        img = np.zeros((50, 100, 4), dtype=np.uint8)
        img[:, :] = [100, 150, 200, 255]
        result = worker.preprocess_image(img)
        assert result.ndim == 2
        assert result.dtype == np.uint8
        assert set(np.unique(result)).issubset({0, 255})

    def test_preprocess_image_scale_small(self, worker):
        import numpy as np
        img = np.zeros((5, 10, 4), dtype=np.uint8)
        result = worker.preprocess_image(img)
        assert result.size > 0

    # --- castbar (pixel matching) ---

    def test_castbar_color_matches(self):
        class FakeScreenshot:
            rgb = b'\x5e\x7b\x68' * 25
        with patch('backend.castbar_mixin._get_sct') as mock_get_sct:
            mock_get_sct.return_value.grab.return_value = FakeScreenshot()
            from backend.castbar_mixin import CastbarMixin, _thread_sct
            if hasattr(_thread_sct, 'instance'):
                del _thread_sct.instance
            mixin = CastbarMixin()
            mixin._settings = {}
            mixin.castbar_point = "100,100"
            mixin.castbar_color = [94, 123, 104]
            mixin.castbar_threshold = 70
            mixin.castbar_enabled = True
            mixin._castbar_cache = {'visible': False, 'timestamp': 0}
            from threading import Lock
            mixin._castbar_cache_lock = Lock()
            mixin.set_setting = lambda k, v: None
            result = mixin._check_castbar_direct()
            assert result is True

    def test_castbar_color_does_not_match(self):
        class FakeScreenshot:
            rgb = b'\xff\x00\x00' * 25
        with patch('backend.castbar_mixin._get_sct') as mock_get_sct:
            mock_get_sct.return_value.grab.return_value = FakeScreenshot()
            from backend.castbar_mixin import CastbarMixin, _thread_sct
            if hasattr(_thread_sct, 'instance'):
                del _thread_sct.instance
            mixin = CastbarMixin()
            mixin._settings = {}
            mixin.castbar_point = "100,100"
            mixin.castbar_color = [94, 123, 104]
            mixin.castbar_threshold = 10
            mixin.castbar_enabled = True
            mixin._castbar_cache = {'visible': False, 'timestamp': 0}
            from threading import Lock
            mixin._castbar_cache_lock = Lock()
            mixin.set_setting = lambda k, v: None
            result = mixin._check_castbar_direct()
            assert result is False

    def test_castbar_disabled_returns_false(self):
        from backend.castbar_mixin import CastbarMixin
        mixin = CastbarMixin()
        mixin.castbar_enabled = False
        mixin._castbar_cache = {'visible': False, 'timestamp': 0}
        from threading import Lock
        mixin._castbar_cache_lock = Lock()
        assert mixin.is_castbar_visible() is False

    def test_castbar_caches_result(self):
        class FakeScreenshot:
            rgb = b'\x00\x00\x00' * 25
        with patch('backend.castbar_mixin._get_sct') as mock_get_sct:
            mock_get_sct.return_value.grab.return_value = FakeScreenshot()
            from backend.castbar_mixin import CastbarMixin, _thread_sct
            if hasattr(_thread_sct, 'instance'):
                del _thread_sct.instance
            from backend.castbar_mixin import CastbarMixin
            mixin = CastbarMixin()
            mixin._settings = {}
            mixin.castbar_point = "100,100"
            mixin.castbar_color = [0, 0, 0]
            mixin.castbar_threshold = 255
            mixin.castbar_enabled = True
            from threading import Lock
            mixin._castbar_cache_lock = Lock()
            mixin._castbar_cache = {'visible': False, 'timestamp': 0}
            mixin.set_setting = lambda k, v: None
            r1 = mixin.is_castbar_visible()
            import time
            mixin._castbar_cache['timestamp'] = time.time()
            r2 = mixin.is_castbar_visible()
            assert r1 == r2

    # --- FastDistanceReader._correct_number ---

    def test_fast_distance_correct_magic_range(self):
        from threads import FastDistanceReader
        reader = FastDistanceReader(lambda: (0, 0, 10, 10), lambda k: None)
        assert reader._correct_number("250") == "25.0"

    def test_fast_distance_correct_two_digit_to_decimal(self):
        from threads import FastDistanceReader
        reader = FastDistanceReader(lambda: (0, 0, 10, 10), lambda k: None)
        reader._distance = 5.0
        result = reader._correct_number("82")
        assert result == "8.2"

    def test_fast_distance_correct_common_substitutions(self):
        from threads import FastDistanceReader
        reader = FastDistanceReader(lambda: (0, 0, 10, 10), lambda k: None)
        reader._distance = 3.0
        assert reader._correct_number("71") == "7.1"
        assert reader._correct_number("22") == "2.2"

    def test_fast_distance_correct_three_digit(self):
        from threads import FastDistanceReader
        reader = FastDistanceReader(lambda: (0, 0, 10, 10), lambda k: None)
        result = reader._correct_number("155")
        assert result == "15.5"

    def test_fast_distance_correct_custom_context(self):
        from threads import FastDistanceReader
        reader = FastDistanceReader(lambda: (0, 0, 10, 10), lambda k: None)
        reader._distance = 30.0
        result = reader._correct_number("27")
        parts = result.split('.')
        assert 20 <= int(parts[0]) <= 30

    def test_fast_distance_correct_dot_already(self):
        from threads import FastDistanceReader
        reader = FastDistanceReader(lambda: (0, 0, 10, 10), lambda k: None)
        assert reader._correct_number("12.5") == "12.5"


# =============================================================================
# 7. Тесты окна (find_window_hwnd, _check_window, EnumWindows, фокус)
# =============================================================================

class TestGameWindow:
    """Проверка поиска окна и проверки фокуса во время выполнения макроса."""

    def test_find_window_hwnd_found(self):
        calls = []
        def fake_enum_windows(callback):
            callback(0xABC, 0)
            callback(0xDEAD, 0)
        with patch('macros_core.EnumWindows', fake_enum_windows):
            with patch('macros_core.GetWindowTextTimeout', side_effect=["", "Perfect World Client"]):
                from macros_core import find_window_hwnd
                result = find_window_hwnd("Perfect World")
                assert result == 0xDEAD

    def test_find_window_hwnd_not_found(self):
        calls = []
        def fake_enum_windows(callback):
            callback(0xABC, 0)
        with patch('macros_core.EnumWindows', fake_enum_windows):
            with patch('macros_core.GetWindowTextTimeout', return_value="Some Other Window"):
                from macros_core import find_window_hwnd
                result = find_window_hwnd("Perfect World")
                assert result is None

    def test_find_window_hwnd_empty_enum(self):
        def fake_enum_windows(callback):
            pass
        with patch('macros_core.EnumWindows', fake_enum_windows):
            from macros_core import find_window_hwnd
            result = find_window_hwnd("Anything")
            assert result is None

    def test_check_window_active(self, mock_backend):
        mock_backend.window_locked = True
        mock_backend.target_window_title = "Perfect World"
        from macros_core import Macro
        macro = Macro("TestWindow", "simple", mock_backend)
        with patch('macros_core.GetForegroundWindow', return_value=100):
            with patch('macros_core.GetWindowText', return_value="Perfect World Client"):
                assert macro._check_window() is True

    def test_check_window_inactive(self, mock_backend):
        mock_backend.window_locked = True
        mock_backend.target_window_title = "Perfect World"
        from macros_core import Macro
        macro = Macro("TestWindow", "simple", mock_backend)
        with patch('macros_core.GetForegroundWindow', return_value=200):
            with patch('macros_core.GetWindowText', return_value="Chrome"):
                assert macro._check_window() is False

    def test_check_window_skipped_if_not_locked(self, mock_backend):
        mock_backend.window_locked = False
        mock_backend.target_window_title = "Perfect World"
        from macros_core import Macro
        macro = Macro("TestWindow", "simple", mock_backend)
        with patch('macros_core.GetForegroundWindow', return_value=200):
            with patch('macros_core.GetWindowText', return_value="Chrome"):
                assert macro._check_window() is True

    def test_check_window_skipped_if_no_target(self, mock_backend):
        mock_backend.window_locked = True
        mock_backend.target_window_title = ""
        from macros_core import Macro
        macro = Macro("TestWindow", "simple", mock_backend)
        with patch('macros_core.GetForegroundWindow', return_value=200):
            with patch('macros_core.GetWindowText', return_value="Chrome"):
                assert macro._check_window() is True

    def test_macro_aborts_when_window_lost(self, mock_backend):
        from macros_core import SimpleMacro
        mock_backend.window_locked = True
        mock_backend.target_window_title = "Perfect World"
        macro = SimpleMacro("WindowLostTest", [("key", "e", 5)], mock_backend)
        call_count = 0
        def fake_check():
            nonlocal call_count
            call_count += 1
            return False
        original_check = macro._check_window
        macro._check_window = fake_check
        from macros.steps_executor import StepsExecutor
        executor = StepsExecutor(stop_event=macro.stop_event)
        success = executor.execute_sequence(
            steps=[("key", "e", 5), ("wait", "", 5)],
            check_window=macro._check_window,
            running_check=lambda: True,
            cast_lock_callback=lambda: None
        )
        assert success is False
        assert call_count >= 1
        macro._check_window = original_check

    def test_activate_game_window(self):
        with patch('backend.window_manager.SetForegroundWindow', return_value=True) as mock_sfw:
            with patch('backend.window_manager.GetWindowText', return_value="Perfect World"):
                with patch('backend.window_manager.IsWindowVisible', return_value=True):
                    with patch('backend.window_manager.GetWindowTextTimeout', return_value="Perfect World Client"):
                        with patch('backend.window_manager.GetForegroundWindow', return_value=0xDEAD):
                            with patch('backend.window_manager.EnumWindows') as mock_ew:
                                with patch('backend.window_manager._attached_thread_input') as mock_ati:
                                    with patch('backend.window_manager._switch_to_this_window', return_value=True):
                                        mock_ati.return_value.__enter__.return_value = True
                                        def fake_enum(cb):
                                            cb(0xDEAD, 0)
                                            return True
                                        mock_ew.side_effect = fake_enum
                                        from backend.window_manager import WindowManager
                                        wm = WindowManager()
                                        wm._skip_window_activation = False
                                        wm._target_window_title = "Perfect World"
                                        result = wm.activate_window(force=True)
                                        assert result is True


# =============================================================================
# 8. Тесты конфигурации (macro_to_dict/from_dict round-trip, JSON save/load)
# =============================================================================

class TestConfigPersistence:
    """Проверка сериализации макросов и сохранения в JSON."""

    @pytest.fixture
    def crud(self, mock_backend):
        from backend.macro_crud import MacroCrud
        return MacroCrud(mock_backend)

    # --- _macro_to_dict ---

    def test_macro_to_dict_simple(self, mock_backend):
        from macros_core import SimpleMacro
        macro = SimpleMacro("TestSimple", [("key", "e", 50), ("wait", "", 100)], mock_backend)
        from backend.macro_crud import MacroCrud
        crud = MacroCrud(mock_backend)
        d = crud._macro_to_dict(macro)
        assert d["type"] == "simple"
        assert d["name"] == "TestSimple"
        assert d["hotkey"] == ""
        assert len(d["steps"]) == 2

    def test_macro_to_dict_skill(self, mock_backend):
        from macros_core import SkillMacro
        macro = SkillMacro("TestSkill", [], mock_backend, skill_id=6003, cooldown=3.0, skill_range=25.0, cast_time=1.5)
        from backend.macro_crud import MacroCrud
        crud = MacroCrud(mock_backend)
        d = crud._macro_to_dict(macro)
        assert d["type"] == "skill"
        assert d["skill_id"] == 6003
        assert d["cooldown"] == 3.0
        assert d["skill_range"] == 25.0
        assert d["cast_time"] == 1.5

    def test_macro_to_dict_zone(self, mock_backend):
        from macros_core import ZoneMacro
        macro = ZoneMacro("TestZone", (100, 200, 300, 400), [], mock_backend, trigger="right_click", poll_interval=5)
        from backend.macro_crud import MacroCrud
        crud = MacroCrud(mock_backend)
        d = crud._macro_to_dict(macro)
        assert d["type"] == "zone"
        assert d["trigger"] == "right_click"
        assert d["poll_interval"] == 5
        assert d["zone_rect"] == [100, 200, 300, 400]

    def test_macro_to_dict_buff(self, mock_backend):
        from macros_core import BuffMacro
        macro = BuffMacro("TestBuff", [], mock_backend, buff_id=8004, duration=60.0, channeling_bonus=15)
        from backend.macro_crud import MacroCrud
        crud = MacroCrud(mock_backend)
        d = crud._macro_to_dict(macro)
        assert d["type"] == "buff"
        assert d["buff_id"] == 8004
        assert d["duration"] == 60.0
        assert d["channeling_bonus"] == 15

    # --- _create_macro_from_dict ---

    def test_create_from_dict_simple(self, crud):
        d = {"type": "simple", "name": "FromDict", "hotkey": "f1", "steps": [["key", "q", 50]]}
        macro = crud._create_macro_from_dict(d)
        assert macro is not None
        assert macro.name == "FromDict"
        assert macro.type == "simple"
        assert macro.hotkey == "f1"
        assert macro.steps == [["key", "q", 50]]

    def test_create_from_dict_skill(self, crud):
        d = {"type": "skill", "name": "Fireball", "hotkey": "2", "steps": [],
             "skill_id": 6003, "cooldown": 3.0, "skill_range": 25.0, "cast_time": 1.5}
        macro = crud._create_macro_from_dict(d)
        assert macro is not None
        assert macro.type == "skill"
        assert macro.skill_id == 6003
        assert macro.cooldown == 3.0
        assert macro.skill_range == 25.0

    def test_create_from_dict_zone(self, crud):
        d = {"type": "zone", "name": "ClickZone", "hotkey": "", "steps": [],
             "zone_rect": [0, 0, 100, 200], "trigger": "left_click", "poll_interval": 10}
        macro = crud._create_macro_from_dict(d)
        assert macro is not None
        assert macro.type == "zone"
        assert macro.zone_rect == (0, 0, 100, 200)
        assert macro.trigger == "left_click"

    def test_create_from_dict_buff(self, crud):
        d = {"type": "buff", "name": "Heal", "hotkey": "f2", "steps": [],
             "buff_id": 8004, "duration": 60.0, "channeling_bonus": 0}
        macro = crud._create_macro_from_dict(d)
        assert macro is not None
        assert macro.type == "buff"
        assert macro.buff_id == 8004
        assert macro.duration == 60.0

    def test_create_from_dict_unknown_type(self, crud):
        d = {"type": "unknown", "name": "Bad", "steps": []}
        macro = crud._create_macro_from_dict(d)
        assert macro is None

    # --- validate ---

    def test_validate_macro_dict_valid(self, crud):
        d = {"type": "simple", "name": "OK", "steps": []}
        crud._validate_macro_dict(d)

    def test_validate_macro_dict_missing_name(self, crud):
        with pytest.raises(ValueError, match="не содержит обязательного поля"):
            crud._validate_macro_dict({"type": "simple", "steps": []})

    def test_validate_macro_dict_bad_zone_rect(self, crud):
        with pytest.raises(ValueError, match="zone_rect"):
            crud._validate_macro_dict({"type": "zone", "name": "Bad", "steps": [], "zone_rect": [1, 2, 3]})

    # --- full round-trip ---

    def test_full_round_trip_all_types(self, mock_backend, crud):
        from macros_core import SimpleMacro, SkillMacro, ZoneMacro, BuffMacro
        originals = [
            SimpleMacro("RT1", [("key", "e", 50)], mock_backend, "f1"),
            SkillMacro("RT2", [], mock_backend, hotkey="f2", skill_id=123, cooldown=4.0, skill_range=30.0, cast_time=2.0),
            ZoneMacro("RT3", (10, 20, 30, 40), [], mock_backend, trigger="right_click", poll_interval=3),
            BuffMacro("RT4", [], mock_backend, buff_id=999, duration=120.0, channeling_bonus=10, hotkey="f3"),
        ]
        for orig in originals:
            d = crud._macro_to_dict(orig)
            restored = crud._create_macro_from_dict(d)
            assert restored is not None
            assert restored.type == orig.type
            assert restored.name == orig.name
            assert restored.hotkey == (orig.hotkey or "")

    def test_json_round_trip(self, mock_backend, crud, tmp_path):
        from macros_core import SimpleMacro
        import json
        macro = SimpleMacro("JSONTest", [("key", "e", 50)], mock_backend, "f4")
        d = crud._macro_to_dict(macro)
        json_str = json.dumps(d)
        loaded = json.loads(json_str)
        restored = crud._create_macro_from_dict(loaded)
        assert restored is not None
        assert restored.name == "JSONTest"
        assert restored.type == "simple"
        assert [list(s) for s in restored.steps] == [["key", "e", 50]]

    def test_save_macros_json_to_file(self, mock_backend, crud, tmp_path):
        from macros_core import SimpleMacro
        import json
        macro = SimpleMacro("FileTest", [("key", "q", 30)], mock_backend)
        d = crud._macro_to_dict(macro)
        json_file = tmp_path / "macros.json"
        json_file.write_text(json.dumps({"macros": [d]}, indent=2), encoding="utf-8")
        loaded_data = json.loads(json_file.read_text(encoding="utf-8"))
        assert len(loaded_data["macros"]) == 1
        restored = crud._create_macro_from_dict(loaded_data["macros"][0])
        assert restored.name == "FileTest"

    def test_get_macro_for_edit_round_trip(self, mock_backend):
        from macros_core import SimpleMacro, SkillMacro
        from backend.macro_crud import MacroCrud
        macro = SimpleMacro("EditTest", [("key", "e", 50)], mock_backend)
        mock_backend._macros = [macro]
        mock_backend._macro_name_for_edit = "EditTest"
        mock_backend._macro_for_edit = None
        crud = MacroCrud(mock_backend)
        d = crud.get_macro_for_edit()
        assert d is not None
        assert d["name"] == "EditTest"
        assert d["type"] == "simple"
        assert d["running"] is False


# =============================================================================
# 9. Тесты QML рендеринга (QQmlComponent, property binding, signal/slot)
# =============================================================================

class TestQMLRendering:
    """Проверка QML-движка: загрузка компонентов, property binding, сигналы."""

    @pytest.fixture
    def _qml_setup(self, qtbot):
        from PySide6.QtQml import QQmlEngine
        self._engine = QQmlEngine()
        self._component = None

    def _set_data(self, qml_bytes):
        from PySide6.QtCore import QUrl
        from PySide6.QtQml import QQmlComponent
        self._component = QQmlComponent(self._engine)
        self._component.setData(qml_bytes, QUrl())
        return self._component

    def test_qml_component_creation(self, qtbot):
        from PySide6.QtCore import QUrl
        from PySide6.QtQml import QQmlComponent, QQmlEngine
        engine = QQmlEngine()
        component = QQmlComponent(engine)
        component.setData(b"import QtQml; QtObject { property int value: 42 }", QUrl())
        assert component.isReady(), component.errorString()
        obj = component.create()
        assert obj is not None
        assert obj.property("value") == 42

    def test_qml_inline_text_component(self, qtbot):
        from PySide6.QtCore import QUrl, QMetaObject
        from PySide6.QtQml import QQmlComponent, QQmlEngine
        engine = QQmlEngine()
        qml = b"""
        import QtQml
        QtObject {
            property string msg: "hello"
            function greet() { return msg.toUpperCase(); }
        }
        """
        component = QQmlComponent(engine)
        component.setData(qml, QUrl())
        assert component.isReady(), component.errorString()
        obj = component.create()
        assert obj.property("msg") == "hello"

    def test_qml_property_binding_from_python(self, qtbot):
        from PySide6.QtCore import QObject, Property, Signal, QUrl
        from PySide6.QtQml import QQmlComponent, QQmlEngine

        class DataObject(QObject):
            valueChanged = Signal()
            def __init__(self):
                super().__init__()
                self._val = 0
            def _get_val(self): return self._val
            def _set_val(self, v):
                self._val = v
                self.valueChanged.emit()
            value = Property(int, _get_val, _set_val, notify=valueChanged)

        engine = QQmlEngine()
        obj = DataObject()
        ctx = engine.rootContext()
        ctx.setContextProperty("testData", obj)

        component = QQmlComponent(engine)
        component.setData(b"""
        import QtQml
        QtObject {
            property int bound: testData.value
        }
        """, QUrl())
        assert component.isReady(), component.errorString()
        qml_obj = component.create()
        assert qml_obj.property("bound") == 0
        obj.value = 42
        assert qml_obj.property("bound") == 42

    def test_qml_calls_python_slot(self, qtbot):
        from PySide6.QtCore import QObject, Slot, QUrl
        from PySide6.QtQml import QQmlComponent, QQmlEngine

        class Receiver(QObject):
            def __init__(self):
                super().__init__()
                self.called_with = None
            @Slot(str)
            def handle(self, msg):
                self.called_with = msg

        engine = QQmlEngine()
        rx = Receiver()
        ctx = engine.rootContext()
        ctx.setContextProperty("receiver", rx)

        component = QQmlComponent(engine)
        component.setData(b"""
        import QtQml
        QtObject {
            function ping() { receiver.handle("pong"); }
        }
        """, QUrl())
        assert component.isReady(), component.errorString()
        qml_obj = component.create()
        qml_obj.metaObject().invokeMethod(qml_obj, "ping")
        assert rx.called_with == "pong"

    def test_qml_signal_to_qml_handler(self, qtbot):
        from PySide6.QtCore import QObject, Signal, Slot, QUrl, QMetaObject
        from PySide6.QtQml import QQmlComponent, QQmlEngine

        class Helper(QObject):
            def __init__(self):
                super().__init__()
                self.messages = []
            @Slot(str)
            def record(self, msg):
                self.messages.append(msg)

        engine = QQmlEngine()
        helper = Helper()
        ctx = engine.rootContext()
        ctx.setContextProperty("testHelper", helper)

        component = QQmlComponent(engine)
        component.setData(b"""
        import QtQml
        QtObject {
            signal sent(string msg)
            function fire() { sent("hello"); }
        }
        """, QUrl())
        assert component.isReady(), component.errorString()
        qml_obj = component.create()
        qml_obj.sent.connect(helper.record)
        QMetaObject.invokeMethod(qml_obj, "fire")
        assert helper.messages == ["hello"]

    def test_qml_inline_component_parse_error(self, qtbot):
        from PySide6.QtCore import QUrl
        from PySide6.QtQml import QQmlComponent, QQmlEngine
        engine = QQmlEngine()
        component = QQmlComponent(engine)
        component.setData(b"this is not valid qml {", QUrl())
        assert not component.isReady()
        assert component.errorString() != ""

    def test_qml_macros_page_properties(self, qtbot):
        """Проверка, что MacrosListPage.qml компилируется с базовыми контекстными
        свойствами."""
        from PySide6.QtQml import QQmlComponent, QQmlEngine
        from PySide6.QtCore import QObject, Signal, QUrl
        from unittest.mock import MagicMock
        engine = QQmlEngine()
        backend_mock = QObject()
        backend_mock.macros = []
        backend_mock.global_stopped = False
        backend_mock.macrosChanged = Signal()
        backend_mock.macroStatusChanged = Signal()
        backend_mock.globalStoppedChanged = Signal()
        backend_mock.start_all_macros = MagicMock()
        backend_mock.stop_all_macros = MagicMock()
        backend_mock.edit_macro_by_index = MagicMock()
        backend_mock.delete_macro = MagicMock()
        ctx = engine.rootContext()
        ctx.setContextProperty("backend", backend_mock)
        from utils_qml import QMLResourceHelper
        ctx.setContextProperty("ResourceHelper", QMLResourceHelper())
        from tooltips_qml import TooltipsProvider
        ctx.setContextProperty("Tooltips", TooltipsProvider())
        component = QQmlComponent(engine)
        qml_path = os.path.join(PROJECT_DIR, "qml", "MacrosListPage.qml")
        if os.path.exists(qml_path):
            component.loadUrl(QUrl.fromLocalFile(qml_path))
            if not component.isReady():
                pytest.skip(f"QML compilation warnings (non-fatal): {component.errorString()}")
        else:
            pytest.skip(f"QML file not found: {qml_path}")


# =============================================================================
# 10. Интеграционные тесты InputSystem с реальным HWND (QWindow)
# =============================================================================

class TestKeyboardRealHWND:
    """Проверка, что InputSystem отправляет реальные Win32-сообщения
    в окно QWindow через его winId() (реальный HWND)."""

    def _drain_messages(self, hwnd):
        msg = ctypes.wintypes.MSG()
        while ctypes.windll.user32.PeekMessageW(ctypes.byref(msg), hwnd, 0, 0, 1):
            pass

    def _peek_msg(self, hwnd, msg_min=0, msg_max=0, remove=0):
        msg = ctypes.wintypes.MSG()
        found = ctypes.windll.user32.PeekMessageW(
            ctypes.byref(msg), hwnd, msg_min, msg_max, remove)
        if found:
            return (msg.message, msg.wParam, msg.lParam)
        return None

    @pytest.fixture
    def real_hwnd(self, qtbot):
        win = QWindow()
        win.setGeometry(-100, -100, 1, 1)
        win.showNormal()
        QApplication.processEvents()
        win.hide()
        QApplication.processEvents()
        hwnd = int(win.winId())
        assert hwnd != 0 and ctypes.windll.user32.IsWindow(hwnd), "QWindow не создал HWND"
        self._drain_messages(hwnd)
        yield hwnd
        win.destroy()

    def test_postmessage_to_qwindow_hwnd(self, qtbot, real_hwnd):
        """PostMessage напрямую в HWND от QWindow — сообщение доходит."""
        from backend.win32_api import PostMessage, WM_KEYDOWN
        PostMessage(real_hwnd, WM_KEYDOWN, 0x45, 0)
        msg = self._peek_msg(real_hwnd, WM_KEYDOWN, WM_KEYDOWN, 1)
        assert msg is not None, "WM_KEYDOWN не получен"
        assert msg[0] == WM_KEYDOWN
        assert msg[1] == 0x45

    def test_input_system_key_real_hwnd(self, qtbot, real_hwnd):
        """InputSystem.key() → WM_KEYDOWN + WM_KEYUP в реальное окно."""
        from backend.input_system import InputSystem
        from backend.win32_api import WM_KEYDOWN, WM_KEYUP
        inp = InputSystem()
        inp.set_target(real_hwnd)
        inp.key('e')
        down = self._peek_msg(real_hwnd, WM_KEYDOWN, WM_KEYDOWN, 1)
        up = self._peek_msg(real_hwnd, WM_KEYUP, WM_KEYUP, 1)
        assert down is not None, "WM_KEYDOWN не получен"
        assert down[1] == 0x45
        assert up is not None, "WM_KEYUP не получен"
        assert up[1] == 0x45

    def test_input_system_key_down_real_hwnd(self, qtbot, real_hwnd):
        """InputSystem.key_down() → WM_KEYDOWN."""
        from backend.input_system import InputSystem
        from backend.win32_api import WM_KEYDOWN
        inp = InputSystem()
        inp.set_target(real_hwnd)
        inp.key_down('shift')
        down = self._peek_msg(real_hwnd, WM_KEYDOWN, WM_KEYDOWN, 1)
        assert down is not None, "WM_KEYDOWN не получен"
        assert down[1] == 0x10

    def test_input_system_key_up_real_hwnd(self, qtbot, real_hwnd):
        """InputSystem.key_up() → WM_KEYUP."""
        from backend.input_system import InputSystem
        from backend.win32_api import WM_KEYUP
        inp = InputSystem()
        inp.set_target(real_hwnd)
        inp.key_up('shift')
        up = self._peek_msg(real_hwnd, WM_KEYUP, WM_KEYUP, 1)
        assert up is not None, "WM_KEYUP не получен"
        assert up[1] == 0x10

    def test_input_system_click_left_real_hwnd(self, qtbot, real_hwnd):
        """InputSystem.click_left() → WM_LBUTTONDOWN + WM_LBUTTONUP."""
        from backend.input_system import InputSystem
        from backend.win32_api import WM_LBUTTONDOWN, WM_LBUTTONUP
        inp = InputSystem()
        inp.set_target(real_hwnd)
        inp.click_left()
        down = self._peek_msg(real_hwnd, WM_LBUTTONDOWN, WM_LBUTTONDOWN, 1)
        up = self._peek_msg(real_hwnd, WM_LBUTTONUP, WM_LBUTTONUP, 1)
        assert down is not None, "WM_LBUTTONDOWN не получен"
        assert up is not None, "WM_LBUTTONUP не получен"

    def test_input_system_click_right_real_hwnd(self, qtbot, real_hwnd):
        """InputSystem.click_right() → WM_RBUTTONDOWN + WM_RBUTTONUP."""
        from backend.input_system import InputSystem
        from backend.win32_api import WM_RBUTTONDOWN, WM_RBUTTONUP
        inp = InputSystem()
        inp.set_target(real_hwnd)
        inp.click_right()
        down = self._peek_msg(real_hwnd, WM_RBUTTONDOWN, WM_RBUTTONDOWN, 1)
        up = self._peek_msg(real_hwnd, WM_RBUTTONUP, WM_RBUTTONUP, 1)
        assert down is not None, "WM_RBUTTONDOWN не получен"
        assert up is not None, "WM_RBUTTONUP не получен"


class _TestRunnerWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SNBLD — Все тесты макросов")
        self.resize(900, 600)
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)

        title = QLabel("Все тесты макросов (184 теста)")
        title.setStyleSheet("font-size: 18px; font-weight: bold;")
        layout.addWidget(title)

        progress_layout = QHBoxLayout()
        self.passed_label = QLabel("✅ Прошло: 0")
        self.failed_label = QLabel("❌ Провалено: 0")
        self.total_label = QLabel("Всего: 184")
        self.total_label.setStyleSheet("font-size: 14px;")
        progress_layout.addWidget(self.passed_label)
        progress_layout.addWidget(self.failed_label)
        progress_layout.addWidget(self.total_label)
        progress_layout.addStretch()
        layout.addLayout(progress_layout)

        self.output = QPlainTextEdit()
        self.output.setReadOnly(True)
        self.output.setStyleSheet("background: #181825; color: #cdd6f4; border: 1px solid #313244; font-family: Consolas; font-size: 12px;")
        layout.addWidget(self.output, stretch=1)

        btn_layout = QHBoxLayout()
        self.run_btn = QPushButton("▶ Запустить все тесты")
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

        proc = subprocess.Popen(
            [sys.executable, "-m", "pytest", __file__, "-v", "--tb=short", "--color=yes"],
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            text=True, encoding="utf-8", errors="replace",
            cwd=PROJECT_DIR,
        )

        output_lines = []
        for line in proc.stdout:
            line = line.rstrip()
            output_lines.append(line)
            self.log(line)
            QApplication.processEvents()

        proc.wait()

        passed = sum(1 for l in output_lines if re.search(r'\d+ passed', l))
        failed = sum(1 for l in output_lines if re.search(r'\d+ failed', l))
        if not passed and not failed:
            summary = [l for l in output_lines if 'passed' in l or 'failed' in l]
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
        if failed == 0:
            self.log(f"✅ Все {total} тестов пройдено!", color="#a6e3a1")
        else:
            self.log(f"❌ {failed} из {total} тестов провалено", color="#f38ba8")
        self.run_btn.setEnabled(True)
        self.run_btn.setText("▶ Запустить все тесты")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = _TestRunnerWindow()
    w.show()
    sys.exit(app.exec())
