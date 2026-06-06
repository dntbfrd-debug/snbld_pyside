import time
import threading
from unittest.mock import patch, MagicMock

import pytest

from conftest import input_call_log


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

        def cast_lock_callback():
            cast_lock_called.set()

        executor = StepsExecutor()
        steps = [("key", "1", 5), ("key", "2", 5), ("key", "3", 5)]
        result = executor.execute_sequence(steps, cast_lock_callback=cast_lock_callback)

        assert result is True
        assert cast_lock_called.is_set()


class TestSimpleMacro:

    def test_create_and_execute(self, mock_backend, mock_win32):
        from macros_core import SimpleMacro

        macro = SimpleMacro("TestSimple", [("key", "e", 10), ("key", "2", 15)], mock_backend, hotkey="f")
        assert macro.name == "TestSimple"
        assert macro.type == "simple"
        assert macro.hotkey == "f"

        macro.start()
        macro.thread.join(timeout=5.0)
        assert macro.thread.is_alive() is False
        assert macro.running.is_set() is False

    def test_stop_during_execution(self, mock_backend, mock_win32):
        from macros_core import SimpleMacro

        macro = SimpleMacro("StopTest", [("wait", "", 2000), ("key", "e", 10)], mock_backend)
        macro.start()
        time.sleep(0.05)
        macro.stop()

        assert macro.running.is_set() is False
        assert macro.thread.is_alive() is False

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

        macro = SkillMacro(
            "TestSkill", [("key", "e", 10), ("key", "2", 10), ("key", "e", 10)],
            mock_backend, skill_id=6003, skill_range=36,
            cast_time=1.0, cooldown=3.0, hotkey="2",
        )
        macro.start()
        macro.thread.join(timeout=5.0)
        assert macro.running.is_set() is False

    def test_auto_approach(self, mock_backend, mock_win32):
        mock_backend._settings["check_distance"] = True
        mock_backend._settings["movement_delay_enabled"] = False
        mock_backend.target_distance = 50.0

        from macros_core import SkillMacro

        input_call_log.clear()
        macro = SkillMacro(
            "ApproachSkill", [("key", "e", 10), ("key", "2", 10), ("key", "e", 10)],
            mock_backend, skill_id=6003, skill_range=36,
            cast_time=0.5, cooldown=2.0, hotkey="2",
        )

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
            macro = SkillMacro(
                "CastbarSkill", [("key", "e", 10), ("key", "2", 10), ("key", "e", 10)],
                mock_backend, skill_id=6003, skill_range=36,
                cast_time=1.0, cooldown=2.0,
            )
            mock_backend.dispatcher.set_cast_lock = MagicMock()
            macro.start()
            macro.thread.join(timeout=5.0)
            assert macro.running.is_set() is False


class TestBuffMacro:

    def test_basic_execution(self, mock_backend, mock_win32):
        from macros_core import BuffMacro

        macro = BuffMacro(
            "TestBuff", [("key", "e", 10), ("key", "3", 10)],
            mock_backend, buff_id=6001, duration=15.0,
            channeling_bonus=20, hotkey="3",
        )
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

        result = dispatcher.request_macro(macro)
        assert result is False

    def test_cooldown_blocks(self, mock_backend):
        from macros_core import SimpleMacro
        dispatcher = mock_backend.dispatcher

        macro = SimpleMacro("CDTest", [("key", "e", 5)], mock_backend)
        macro.cooldown = 10.0
        macro.last_used = time.time()

        result = dispatcher.request_macro(macro)
        assert result is False

    def test_running_macro_blocks_others(self, mock_backend):
        from macros_core import SimpleMacro
        dispatcher = mock_backend.dispatcher

        m1 = SimpleMacro("RunningBlockA", [("wait", "", 500)], mock_backend)
        m2 = SimpleMacro("RunningBlockB", [("key", "e", 5)], mock_backend)

        dispatcher.request_macro(m1)
        time.sleep(0.05)

        result = dispatcher.request_macro(m2)
        assert result is False

        m1.stop()
        m1.thread.join(timeout=3.0)

    def test_global_stopped_blocks(self, mock_backend):
        from macros_core import SimpleMacro
        dispatcher = mock_backend.dispatcher

        mock_backend.global_stopped = True
        macro = SimpleMacro("GlobalStopTest", [("key", "e", 5)], mock_backend)

        result = dispatcher.request_macro(macro)
        assert result is False

    def test_debounce_blocks_rapid_calls(self, mock_backend):
        from macros_core import SimpleMacro
        dispatcher = mock_backend.dispatcher

        macro = SimpleMacro("DebounceTest", [("wait", "", 5)], mock_backend)
        dispatcher.last_launch_time = time.time()

        result = dispatcher.request_macro(macro)
        assert result is False

    def test_successful_launch_and_completion(self, mock_backend, mock_win32):
        from macros_core import SimpleMacro
        dispatcher = mock_backend.dispatcher

        dispatcher.last_launch_time = 0.0
        dispatcher._macro_last_launch.clear()
        dispatcher.cast_lock_until = 0.0

        macro = SimpleMacro("LaunchTest", [("key", "e", 5)], mock_backend)
        result = dispatcher.request_macro(macro)
        assert result is True

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

        result = dispatcher.request_macro(m2)
        assert result is False

        m1.stop()
        m1.thread.join(timeout=3.0)

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

        dispatcher.request_macro(m1)
        time.sleep(0.05)

        dispatcher.request_macro(m2)
        time.sleep(0.05)

        dispatcher.stop_all_macros(timeout=2.0)
        assert m1.running.is_set() is False
        assert m2.running.is_set() is False

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
        with dispatcher.lock:
            heapq.heappush(dispatcher.macro_queue, qm)

        time.sleep(1.0)

        if macro.running.is_set():
            macro.thread.join(timeout=3.0)
            assert True
        else:
            from backend.macros_dispatcher import QueuedMacro
            still_queued = any(
                q.macro is macro
                for q in dispatcher.macro_queue
            )
            assert not still_queued, "Macro still stuck in queue"


class TestThreadSafety:

    def test_concurrent_stop_and_start(self, mock_backend):
        from macros_core import SimpleMacro

        macro = SimpleMacro("ConcurrentStopStart", [("wait", "", 1000)], mock_backend)
        errors = []

        def starter():
            try:
                macro.start()
            except Exception as e:
                errors.append(("start", e))

        def stopper():
            try:
                time.sleep(0.02)
                macro.stop()
            except Exception as e:
                errors.append(("stop", e))

        threads = [threading.Thread(target=starter), threading.Thread(target=stopper)]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=5.0)

        assert len(errors) == 0
        assert macro.running.is_set() is False

    def test_concurrent_dispatcher_requests(self, mock_backend, mock_win32):
        from macros_core import SimpleMacro
        dispatcher = mock_backend.dispatcher

        dispatcher.last_launch_time = 0.0
        dispatcher._macro_last_launch.clear()
        dispatcher.cast_lock_until = 0.0

        macro = SimpleMacro("ConcurrentReq", [("wait", "", 200)], mock_backend)
        results = []

        def launch():
            try:
                r = dispatcher.request_macro(macro)
                results.append(r)
            except Exception as e:
                results.append(e)

        threads = [threading.Thread(target=launch) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=5.0)

        success_count = sum(1 for r in results if r is True)
        assert success_count >= 1, f"At least 1 success expected, got: {results}"
        macro.thread.join(timeout=3.0)

    def test_concurrent_crud_operations(self, mock_backend):
        from backend.macro_crud import MacroCrud

        crud = MacroCrud(mock_backend)
        mock_backend._macros = []
        errors = []

        def create_macro(i):
            try:
                crud.create_simple(f"ThreadMacro{i}", f"f{i}", [("key", "e", 10)])
            except Exception as e:
                errors.append((i, e))

        threads = [threading.Thread(target=create_macro, args=(i,)) for i in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=5.0)

        assert len(errors) == 0
        assert len(mock_backend._macros) == 10


class TestMacroCrud:

    def test_create_simple_macro(self, mock_backend):
        from backend.macro_crud import MacroCrud

        crud = MacroCrud(mock_backend)
        mock_backend._macros = []

        crud.create_simple("TestCrud", "f", [("key", "e", 10), ("key", "2", 15)])
        assert len(mock_backend._macros) == 1
        m = mock_backend._macros[0]
        assert m.name == "TestCrud"
        assert m.type == "simple"
        assert m.hotkey == "f"

    def test_create_skill_macro(self, mock_backend):
        from backend.macro_crud import MacroCrud

        crud = MacroCrud(mock_backend)
        mock_backend._macros = []

        crud.create_skill(
            "SkillCrud", "", 6003,
            [("key", "e", 90), ("key", "2", 15), ("key", "e", 15)],
            skill_hotkey="1", cooldown=3.0, skill_range=36,
            cast_time=1.0, castbar_swap_delay=0, zone_rect=[],
        )
        assert len(mock_backend._macros) == 1
        m = mock_backend._macros[0]
        assert m.name == "SkillCrud"
        assert m.type == "skill"
        assert m.skill_id == 6003
        assert m.cooldown == 3.0
        assert m.skill_range == 36

    def test_create_buff_macro(self, mock_backend):
        from backend.macro_crud import MacroCrud

        crud = MacroCrud(mock_backend)
        mock_backend._macros = []

        crud.create_buff(
            "BuffCrud", "3", 6001,
            [("key", "e", 10), ("key", "3", 10)],
            duration=15.0, channeling_bonus=20, zone_rect=[],
        )
        assert len(mock_backend._macros) == 1
        m = mock_backend._macros[0]
        assert m.name == "BuffCrud"
        assert m.type == "buff"
        assert m.buff_id == 6001
        assert m.duration == 15.0

    def test_create_zone_macro(self, mock_backend):
        from backend.macro_crud import MacroCrud

        crud = MacroCrud(mock_backend)
        mock_backend._macros = []

        crud.create_zone(
            "ZoneCrud", "", [100, 200, 300, 400],
            [("key", "e", 10)], trigger="left_click", poll_interval_ms=100,
        )
        assert len(mock_backend._macros) == 1
        m = mock_backend._macros[0]
        assert m.name == "ZoneCrud"
        assert m.type == "zone"
        assert m.zone_rect == [100, 200, 300, 400]

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

        assert d["name"] == "DictTest"
        assert d["type"] == "simple"
        assert d["hotkey"] == "f"
        assert d["steps"] == [["key", "e", 10]] or d["steps"] == [("key", "e", 10)]


class TestZoneMacro:

    def test_click_in_zone_triggers_launch(self, mock_backend, mock_win32):
        from macros_core import ZoneMacro

        macro = ZoneMacro(
            "TestZone", [100, 200, 300, 400],
            [("key", "e", 10), ("key", "2", 10)],
            mock_backend, trigger="left_click",
        )
        from macros.steps_executor import StepsExecutor
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
                assert executed.is_set(), "Steps should have been executed"

    def test_click_outside_zone_ignored(self, mock_backend):
        from macros_core import ZoneMacro

        macro = ZoneMacro(
            "ZoneOutside", [100, 200, 300, 400],
            [("key", "e", 10)],
            mock_backend, trigger="left_click",
        )
        mock_backend.dispatcher.request_macro = MagicMock()

        macro.on_mouse_click(50, 50)
        time.sleep(0.05)
        assert not mock_backend.dispatcher.request_macro.called

    def test_zone_point_in_rect(self, mock_backend):
        from macros_core import Macro

        m = Macro("RectTest", "zone", mock_backend)
        assert m._is_point_in_rect(150, 250, [100, 200, 300, 400]) is True
        assert m._is_point_in_rect(50, 50, [100, 200, 300, 400]) is False
        assert m._is_point_in_rect(100, 200, [100, 200, 300, 400]) is True
        assert m._is_point_in_rect(300, 400, [100, 200, 300, 400]) is True
        assert m._is_point_in_rect(301, 401, [100, 200, 300, 400]) is False


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

        result = dispatcher.request_macro(macro)
        assert result is True

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
        result = dispatcher.request_macro(macro)
        assert result is True
        macro.thread.join(timeout=3.0)


class TestMacroQueueProcessor:

    def test_health_check(self, mock_backend):
        dispatcher = mock_backend.dispatcher
        status = dispatcher.health_check()
        assert "queue_processor_alive" in status
        assert "active_macros_count" in status
        assert "queue_size" in status
        assert "cast_locked" in status


if __name__ == "__main__":
    import subprocess, sys, os
    proc = subprocess.Popen(
        [sys.executable, "-m", "pytest", __file__, "-v", "--tb=short", "--color=yes"],
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        text=True, encoding="utf-8", errors="replace",
        cwd=os.path.dirname(os.path.abspath(__file__)),
    )
    for line in proc.stdout:
        print(line, end="")
    proc.wait()
    sys.exit(proc.returncode)
