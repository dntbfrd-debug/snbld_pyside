import os
import sys
import time
import logging
import threading
from unittest.mock import MagicMock, PropertyMock, patch

import pytest


TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(TESTS_DIR)

sys.path.insert(0, PROJECT_DIR)


logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    force=True,
)


input_call_log = []


class TrackedInputSystem:
    def key(self, key_name):
        input_call_log.append(("key", key_name))

    def click_left(self):
        input_call_log.append(("click_left", ""))

    def click_right(self):
        input_call_log.append(("click_right", ""))

    def key_down(self, key_name):
        input_call_log.append(("key_down", key_name))

    def key_up(self, key_name):
        input_call_log.append(("key_up", key_name))

    def key_down_sendinput(self, key_name):
        input_call_log.append(("key_down_si", key_name))
        return True

    def key_up_sendinput(self, key_name):
        input_call_log.append(("key_up_si", key_name))
        return True

    def click_at_position(self, x, y):
        input_call_log.append(("click_at", f"{x},{y}"))


class MockBackend:
    def __init__(self):
        self._settings = {
            "cooldown_margin": 0.3,
            "cast_lock_margin": 0.45,
            "movement_delay_enabled": False,
            "movement_delay_ms": 300,
            "check_distance": False,
            "use_castbar_detection": False,
            "first_step_delay": 0,
            "global_step_delay": 0,
            "use_fixed_delays": True,
            "use_ping_delays": False,
            "average_ping": 0,
            "window_locked": False,
            "target_window_title": "",
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

    def apply_buff(self, buff_id, name, duration, channeling_bonus, icon):
        pass

    def get_actual_cast_time(self, base_cast_time):
        return base_cast_time

    def get(self, key, default=None):
        return self._settings.get(key, default)

    @property
    def settings(self):
        return self._settings


@pytest.fixture(autouse=True)
def _track_input():
    input_call_log.clear()
    with patch('backend.input_system.send_key', wraps=TrackedInputSystem().key) as mk:
        with patch('backend.input_system.click_left', wraps=TrackedInputSystem().click_left) as mcl:
            with patch('backend.input_system.click_right', wraps=TrackedInputSystem().click_right) as mcr:
                with patch('backend.input_system.key_down_sendinput', wraps=TrackedInputSystem().key_down_sendinput) as mkdsi:
                    with patch('backend.input_system.key_up_sendinput', wraps=TrackedInputSystem().key_up_sendinput) as mkusi:
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
