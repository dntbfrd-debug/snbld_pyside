import threading
import time
import logging
from backend.win32_api import GetForegroundWindow, GetWindowText, GetWindowTextTimeout, EnumWindows

from backend.input_system import send_key, click_left, click_right, key_down, key_up, key_down_sendinput, key_up_sendinput
from backend.logger_manager import get_logger as _get_logger

def _play_window_lost_sound():
    try:
        from utils.sound_alert import play_alert_sound, SOUND_WINDOW_LOST
        play_alert_sound(SOUND_WINDOW_LOST)
    except Exception:
        pass

def _log_session_event(msg):
    try:
        from backend.session_log import get_session_log
        get_session_log().log("window_lost", msg)
    except Exception:
        pass


def find_window_hwnd(window_title):
    result_hwnd = None
    def callback(hwnd, param):
        nonlocal result_hwnd
        if window_title.lower() in GetWindowTextTimeout(hwnd).lower():
            result_hwnd = hwnd
            return False
        return True
    try:
        EnumWindows(callback)
    except Exception as ex:
        _get_logger().warning(f"EnumWindows failed: {ex}")
    return result_hwnd


def set_game_window_hwnd(hwnd):
    from backend.input_system import input_system
    input_system.set_target(hwnd)


def set_skip_window_activation(skip):
    from backend.window_manager import WindowManager
    WindowManager().skip_window_activation = bool(skip)


def click_at_position(x, y):
    from backend.input_system import input_system
    
    if input_system.target_hwnd is None:
        _get_logger().warning(f"[ClickAtPos] Целевое окно не установлено, клик в ({x},{y}) пропущен")
        return
    
    try:
        _get_logger().debug(f"[ClickAtPos] Отправка клика через PostMessage в ({x},{y})")
        input_system.click_at_position(x, y)
        _get_logger().debug(f"[ClickAtPos] Клик отправлен")
    except Exception as e:
        _get_logger().error(f"[ClickAtPos] Ошибка в ({x},{y}): {e}, клик пропущен", exc_info=True)


class Macro:
    def __init__(self, name, macro_type, app, hotkey=None):
        self.name = name
        self.type = macro_type
        self.app = app
        self.hotkey = hotkey
        self.running = False
        self.thread = None
        self.stop_event = threading.Event()
        self.start_lock = threading.Lock()

    def start(self):
        with self.start_lock:
            _get_logger().debug(f"[START] Попытка запуска макроса '{self.name}'")
            if self.running:
                _get_logger().debug(f"[START] Макрос '{self.name}' уже запущен")
                return

            self.stop_event.clear()
            self.running = True
            self.last_start_time = time.time()
            try:
                self.thread = threading.Thread(target=self._run, daemon=True)
                self.thread.start()
                _get_logger().debug(f"[START] Макрос '{self.name}' помечен как запущенный, поток запущен")
            except Exception as e:
                self.running = False
                _get_logger().error(f"[START] Не удалось запустить поток макроса '{self.name}': {e}", exc_info=True)
                raise

        _get_logger().info(f"[+] Макрос '{self.name}' запущен")

    def stop(self):
        _get_logger().debug(f"[STOP] Попытка остановки макроса '{self.name}'")
        self.running = False
        self.stop_event.set()
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=3.0)
            if self.thread.is_alive():
                _get_logger().warning(f"Поток макроса '{self.name}' не завершился, принудительно...")
        _get_logger().info(f" Макрос '{self.name}' остановлен")

    def _check_window(self):
        try:
            if not self.app.window_locked:
                return True
            target = self.app.target_window_title.strip().lower()
            if not target:
                return True
            try:
                hwnd = GetForegroundWindow()
                active_title = GetWindowText(hwnd).lower()
                result = target in active_title
                if not result:
                    _get_logger().warning(f"[{self.name}] Окно потеряно: '{active_title}' != '{target}'")
                    _play_window_lost_sound()
                    _log_session_event(f"Окно потеряно: '{active_title}' вместо '{target}'")
                return result
            except Exception as e:
                _get_logger().error(f"[{self.name}] Ошибка проверки окна: {e}", exc_info=True)
                return False
        except AttributeError as e:
            _get_logger().error(f"[{self.name}] App missing required attribute for window check: {e}", exc_info=True)
            return False

    def _run(self):
        pass


class SimpleMacro(Macro):
    def __init__(self, name, steps, app, hotkey=None):
        super().__init__(name, "simple", app, hotkey)
        self.steps = steps

    def _run(self):
        _get_logger().debug(f"[SIMPLE] Начало выполнения макроса '{self.name}', шагов: {len(self.steps)}")
        start_time = time.time()
        try:
            from macros.steps_executor import StepsExecutor
            executor = StepsExecutor(stop_event=self.stop_event)
            def running_check():
                return self.running and not self.stop_event.is_set()
            success = executor.execute_sequence(
                steps=self.steps,
                check_window=self._check_window,
                running_check=running_check,
                cast_lock_callback=lambda: self.app.dispatcher.set_cast_lock(self) if hasattr(self.app, 'dispatcher') and hasattr(self.app.dispatcher, 'set_cast_lock') else None
            )
            if not success:
                _get_logger().debug(f"[SIMPLE] Макрос '{self.name}' прерван или не выполнен полностью")
        except Exception as e:
            _get_logger().error(f"[SIMPLE] Ошибка в макросе '{self.name}': {e}", exc_info=True)
        finally:
            self.running = False
            total_duration = (time.time() - start_time) * 1000
            _get_logger().debug(f"[SIMPLE] Макрос '{self.name}' завершил выполнение за {total_duration:.2f}мс")
            if hasattr(self, 'app') and hasattr(self.app, 'dispatcher') and hasattr(self.app.dispatcher, 'on_macro_finished'):
                self.app.dispatcher.on_macro_finished(self.name)


class ZoneMacro(Macro):
    def __init__(
        self,
        name,
        zone_rect,
        steps,
        app,
        trigger="left_click",
        hotkey=None,
        skill_id=None,
        cooldown=0,
        skill_range=0,
        cast_time=0.0,
        castbar_swap_delay=0,
        poll_interval=10,
    ):
        import warnings
        if poll_interval != 10:
            warnings.warn(
                f"Параметр poll_interval в ZoneMacro устарел и игнорируется. Используйте событийную модель.",
                DeprecationWarning,
                stacklevel=2
            )
        super().__init__(name, "zone", app, hotkey)
        self.zone_rect = zone_rect
        self.steps = steps
        self.trigger = trigger
        self.was_inside = False
        self.skill_id = skill_id
        self.cooldown = cooldown
        self.skill_range = skill_range
        self.cast_time = cast_time
        self.castbar_swap_delay = max(0, castbar_swap_delay)
        self.last_used = 0
        self.cooldown_lock = threading.Lock()
        self._mouse_click_connected = False
        self._scheduled = False
        self._schedule_lock = threading.Lock()

    def _connect_mouse_click(self, app):
        if self._mouse_click_connected:
            try:
                app.mouse_click_monitor.mouse_clicked.disconnect(self.on_mouse_click)
                _get_logger().debug(f"[{self.name}] Отвязан сигнал от MouseClickMonitor")
            except Exception as e:
                _get_logger().warning(f"[{self.name}] Ошибка при отключении сигнала: {e}", exc_info=True)
            finally:
                self._mouse_click_connected = False
        
        if hasattr(app, 'mouse_click_monitor') and app.mouse_click_monitor:
            try:
                app.mouse_click_monitor.mouse_clicked.connect(self.on_mouse_click)
                self._mouse_click_connected = True
                _get_logger().info(f" [{self.name}]  Подключен к новому MouseClickMonitor")
            except Exception as e:
                _get_logger().error(f"[{self.name}]  Ошибка подключения к MouseClickMonitor: {e}", exc_info=True)
                self._mouse_click_connected = False

    def on_mouse_click(self, x, y):
        _get_logger().debug(f"[ZONE] on_mouse_click '{self.name}': клик ({x},{y}), зона={self.zone_rect}")

        if not self.zone_rect:
            _get_logger().warning(f"[ZONE] zone_rect не установлен для '{self.name}'")
            return

        if not self._is_point_in_rect(x, y, self.zone_rect):
            _get_logger().debug(f"[ZONE] Клик ({x},{y}) НЕ в зоне {self.zone_rect}")
            return

        _get_logger().info(f"[ZONE]  Клик в области: ({x},{y}), зона={self.zone_rect}")

        if self.app.global_stopped:
            _get_logger().debug(f"[ZONE] {self.name}: глобальная блокировка, игнорируем клик")
            return

        if self.app.settings.get("movement_delay_enabled", True):
            delay_ms = self.app.settings.get("movement_delay_ms", 100)
            if delay_ms > 0:
                time_since_stop = self.app.movement_monitor.get_movement_delay()
                if time_since_stop < delay_ms / 1000.0:
                    sleep_time = (delay_ms / 1000.0) - time_since_stop
                    _get_logger().debug(f"[ZONE] {self.name}: Ожидание инерции движения: {sleep_time*1000:.0f} мс")
                    _get_logger().debug(f"[ZONE] {self.name}: требуется ожидание {sleep_time*1000:.0f}мс, пропускаем запуск")
                    return

        if self.skill_id is not None and self.app.settings.get("check_distance", False):
            tolerance = self.app.settings.get("distance_tolerance", 1.0)
            if self.app.target_distance is None:
                _get_logger().debug(f"[ZONE] {self.name}: расстояние не определено, пропускаем")
                return
            cast_required = self.skill_range + tolerance
            if self.app.target_distance > cast_required:
                _get_logger().debug(f"[ZONE] {self.name}: цель слишком далеко ({self.app.target_distance:.1f}м)")
                return

        # Атомарная проверка и установка флага _scheduled
        with self._schedule_lock:
            if self.running or self._scheduled:
                _get_logger().info(f"[ZONE] Макрос '{self.name}' уже выполняется или запланирован")
                return
            self._scheduled = True

        _get_logger().info(f"[ZONE]  Запрос на запуск '{self.name}' по клику в области ({x},{y})")
        def launch_macro():
            try:
                if hasattr(self, 'app') and self.app:
                    if hasattr(self.app, 'dispatcher') and self.app.dispatcher:
                        result = self.app.dispatcher.request_macro(self)
                        if result:
                            _get_logger().info(f"[ZONE]  '{self.name}': ЗАПУЩЕН диспетчером")
                        else:
                            _get_logger().warning(f"[ZONE]  '{self.name}': ОТКЛОНЕНО диспетчером")
                    else:
                        _get_logger().warning(f"[ZONE]  '{self.name}': dispatcher НЕ ДОСТУПЕН")
                        self.start()
                else:
                    _get_logger().warning(f"[ZONE]  '{self.name}': app НЕ ДОСТУПЕН")
                    self.start()
            except Exception as e:
                _get_logger().error(f"[ZONE]  '{self.name}': ошибка: {e}", exc_info=True)
                try:
                    self.start()
                except Exception as start_e:
                    _get_logger().error(f"[ZONE]  '{self.name}': ошибка при start: {start_e}", exc_info=True)
            finally:
                with self._schedule_lock:
                    self._scheduled = False
        threading.Thread(target=launch_macro, daemon=True).start()

    def _is_point_in_rect(self, x, y, rect):
        x1, y1, x2, y2 = rect
        return x1 <= x <= x2 and y1 <= y <= y2

    def _run(self):
        _get_logger().info(f"[ZONE] ====== Запуск зонального макроса '{self.name}', зона={self.zone_rect} ======")

        self._connect_mouse_click(self.app)

        try:
            while self.running and not self.stop_event.is_set():
                self.stop_event.wait(0.1)

        except Exception as e:
            _get_logger().error(f"[ZONE] Ошибка в макросе '{self.name}': {e}", exc_info=True)
        finally:
            self.was_inside = False
            self.running = False
            _get_logger().debug(f"[ZONE] Макрос '{self.name}' завершил работу")
            if hasattr(self, 'app') and hasattr(self.app, 'dispatcher'):
                self.app.dispatcher.on_macro_finished(self.name)


class BuffMacro(SimpleMacro):
    def __init__(
        self,
        name,
        steps,
        app,
        buff_id,
        duration,
        channeling_bonus,
        hotkey=None,
        icon="buff.png",
    ):
        super().__init__(name, steps, app, hotkey)
        self.type = "buff"
        self.buff_id = buff_id
        self.duration = duration
        self.channeling_bonus = channeling_bonus
        self.icon = icon

    def _run(self):
        _get_logger().info(f"[BUFF] Начало выполнения макроса-баффа '{self.name}'")
        start_time = time.time()
        try:
            if hasattr(self.app, '_settings') and self.buff_id == 8004:
                buff_click_point = self.app._settings.get("buff_8004_click_point", "0,0")
                if buff_click_point and buff_click_point != "0,0":
                    try:
                        parts = buff_click_point.split(",")
                        if len(parts) == 2:
                            x, y = int(parts[0]), int(parts[1])
                            _get_logger().info(f"[BUFF] Клик по калиброванным координатам: ({x}, {y})")
                            click_at_position(x, y)
                            time.sleep(0.1)
                            _get_logger().info(f"[BUFF] Клик выполнен")
                    except Exception as e:
                        _get_logger().error(f"[BUFF] Ошибка клика по координатам: {e}", exc_info=True)

            from macros.steps_executor import StepsExecutor
            executor = StepsExecutor(stop_event=self.stop_event)
            def running_check():
                return self.running and not self.stop_event.is_set()
            
            success = executor.execute_sequence(
                steps=self.steps,
                check_window=self._check_window,
                running_check=running_check,
                cast_lock_callback=lambda: self.app.dispatcher.set_cast_lock(self) if hasattr(self.app, 'dispatcher') and hasattr(self.app.dispatcher, 'set_cast_lock') else None
            )
            
            if success and self.running and not self.stop_event.is_set():
                if hasattr(self.app, "apply_buff"):
                    self.app.apply_buff(
                        self.buff_id,
                        self.name,
                        self.duration,
                        self.channeling_bonus,
                        self.icon,
                    )
                    _get_logger().info(f"[BUFF] [+] Бафф '{self.name}' активирован на {self.duration} сек (+{self.channeling_bonus}% пения)")
                else:
                    _get_logger().error("[BUFF] Главное окно не имеет метода apply_buff", exc_info=True)
            else:
                _get_logger().debug(f"[BUFF] Макрос '{self.name}' прерван или не выполнен полностью")
        except Exception as e:
            _get_logger().error(f"[BUFF] Ошибка в макросе-баффе '{self.name}': {e}", exc_info=True)
        finally:
            self.running = False
            total_duration = (time.time() - start_time) * 1000
            _get_logger().info(f"[BUFF] Макрос-бафф '{self.name}' завершил выполнение за {total_duration:.2f}мс")
            if hasattr(self, 'app') and hasattr(self.app, 'dispatcher'):
                self.app.dispatcher.on_macro_finished(self.name)


class SkillMacro(SimpleMacro):
    def __init__(self, name, steps, app, hotkey=None,
                 skill_id=None, cooldown=0, skill_range=0, cast_time=0.0,
                 castbar_swap_delay=0, step2_repeat_delay=0):
        super().__init__(name, steps, app, hotkey)
        self.type = "skill"
        self.skill_id = skill_id
        self.cooldown = float(cooldown) if cooldown else 0.0
        self.skill_range = float(skill_range) if skill_range else 0.0
        self.cast_time = cast_time
        self.last_used = 0
        self.castbar_swap_delay = max(0, castbar_swap_delay)
        self.cooldown_lock = threading.Lock()
        self.zone_rect = None
        self._mouse_click_connected = False
        self.step2_repeat_delay = step2_repeat_delay
        self._scheduled = False
        self._schedule_lock = threading.Lock()

    def _connect_mouse_click(self, app):
        if self._mouse_click_connected:
            try:
                if hasattr(app, 'mouse_click_monitor') and app.mouse_click_monitor:
                    app.mouse_click_monitor.mouse_clicked.disconnect(self.on_mouse_click)
                    _get_logger().debug(f"[{self.name}] Старое подключение к MouseClickMonitor отключено")
            except Exception as e:
                _get_logger().warning(f"[{self.name}] Ошибка при отключении сигнала: {e}", exc_info=True)
            finally:
                self._mouse_click_connected = False
        
        if hasattr(app, 'mouse_click_monitor') and app.mouse_click_monitor:
            try:
                app.mouse_click_monitor.mouse_clicked.connect(self.on_mouse_click)
                self._mouse_click_connected = True
                _get_logger().info(f" [{self.name}]  Подключен к новому MouseClickMonitor")
            except Exception as e:
                _get_logger().error(f"[{self.name}]  Ошибка подключения к MouseClickMonitor: {e}", exc_info=True)
                self._mouse_click_connected = False

    def on_mouse_click(self, x, y):
        _get_logger().debug(f"[SKILL+ZONE] on_mouse_click вызван для '{self.name}': клик ({x},{y}), zone_rect={self.zone_rect}")
        
        if not self.zone_rect:
            _get_logger().warning(f"[SKILL+ZONE] zone_rect не установлен для '{self.name}'")
            return
        
        if not self._is_point_in_rect(x, y, self.zone_rect):
            _get_logger().debug(f"[SKILL+ZONE] Клик ({x},{y}) НЕ в зоне {self.zone_rect}")
            return
        
        _get_logger().info(f"[SKILL+ZONE]  Клик в области: ({x},{y}), зона={self.zone_rect}")

        # Атомарная проверка и установка флага _scheduled
        with self._schedule_lock:
            if self.running or self._scheduled:
                _get_logger().info(f"[SKILL+ZONE] Макрос '{self.name}' уже выполняется или запланирован")
                return
            self._scheduled = True

        _get_logger().info(f"[SKILL+ZONE]  Запрос на запуск '{self.name}' по клику в области ({x},{y})")
        def launch_macro():
            try:
                if hasattr(self, 'app') and self.app:
                    if hasattr(self.app, 'dispatcher') and self.app.dispatcher:
                        result = self.app.dispatcher.request_macro(self)
                        if result:
                            _get_logger().info(f"[SKILL+ZONE]  '{self.name}': ЗАПУЩЕН диспетчером")
                        else:
                            _get_logger().warning(f"[SKILL+ZONE]  '{self.name}': ОТКЛОНЕНО диспетчером")
                    else:
                        _get_logger().warning(f"[SKILL+ZONE]  '{self.name}': dispatcher НЕ ДОСТУПЕН")
                        self.start()
                else:
                    _get_logger().warning(f"[SKILL+ZONE]  '{self.name}': app НЕ ДОСТУПЕН")
                    self.start()
            except Exception as e:
                _get_logger().error(f"[SKILL+ZONE]  '{self.name}': ошибка: {e}", exc_info=True)
                try:
                    self.start()
                except Exception as start_e:
                    _get_logger().error(f"[SKILL+ZONE]  '{self.name}': ошибка при start: {start_e}", exc_info=True)
            finally:
                with self._schedule_lock:
                    self._scheduled = False
        threading.Thread(target=launch_macro, daemon=True).start()

    def _is_point_in_rect(self, x, y, rect):
        x1, y1, x2, y2 = rect
        return x1 <= x <= x2 and y1 <= y <= y2

    def _run(self):
        _get_logger().debug(f"[SKILL] Начало выполнения макроса-скилла '{self.name}'")
        start_time = time.time()

        has_zone = hasattr(self, 'zone_rect') and self.zone_rect
        _get_logger().info(f"[SKILL] {'[ЗОНАЛЬНЫЙ]' if has_zone else '[ОБЫЧНЫЙ]'} макрос '{self.name}', zone_rect={self.zone_rect if has_zone else 'нет'}")

        if not has_zone:
            if not self._check_window():
                _get_logger().debug(f"[SKILL] Окно неактивно, прерывание")
                self.running = False
                return

        approach_used = False
        user_was_moving = False

        time_since_stop = self.app.movement_monitor.get_movement_delay()
        if time_since_stop < 0.5:
            user_was_moving = True
            _get_logger().debug(f"[SKILL] Пользователь двигался (возраст={time_since_stop*1000:.0f}мс), используем цикл")

        check_distance = self.app.settings.get("check_distance", False)
        fast_dist = self.app.fast_distance if hasattr(self.app, 'fast_distance') else self.app.target_distance
        _get_logger().info(f"[SKILL] check_distance={check_distance}, skill_range={self.skill_range}, target_distance={fast_dist}")
        
        if check_distance and self.skill_range > 0:
            tolerance = self.app.settings.get("distance_tolerance", 1.0)
            cast_required = self.skill_range + tolerance
            target_dist = max(0, self.skill_range - 0.2)
            current = fast_dist

            if current is None or current < 0.5:
                _get_logger().warning(f"[SKILL] Макрос '{self.name}': расстояние не определено (fast_reader: {current}), выполняем без подбегания")
            elif current > target_dist:
                _get_logger().info(f"[SKILL] Макрос '{self.name}': цель слишком далеко ({current:.1f}м, нужно ≤{target_dist:.1f}), ПОДБЕГАЕМ")
                approach_used = True
                key_down_sendinput('w')
                try:
                    approach_start = time.time()
                    last_keydown_time = time.time()
                    while self.running and not self.stop_event.is_set():
                        if not has_zone and not self._check_window():
                            _get_logger().debug(f"[SKILL] Окно неактивно, прерывание подбегания")
                            break
                        
                        if time.time() - last_keydown_time > 0.1:
                            key_down_sendinput('w')
                            last_keydown_time = time.time()

                        current_dist = self.app.fast_raw_distance if hasattr(self.app, 'fast_raw_distance') else (self.app.fast_distance if hasattr(self.app, 'fast_distance') else self.app.target_distance)
                        if current_dist is not None and current_dist <= target_dist:
                            _get_logger().info(f"[SKILL] Подбежали до {current_dist:.1f}м за {time.time()-approach_start:.2f}с")
                            break
                        time.sleep(0.03)
                finally:
                    key_up_sendinput('w')
                time.sleep(0.06)
                if not self.running or self.stop_event.is_set():
                    _get_logger().debug(f"[SKILL] Макрос '{self.name}' прерван во время подбегания")
                    self.running = False
                    return
            else:
                _get_logger().info(f"[SKILL] Дистанция {current:.1f}м в пределах дальности (нужно ≤{target_dist:.1f}м)")
        else:
            _get_logger().debug(f"[SKILL] Проверка дистанции отключена (check_distance={check_distance}) или skill_range={self.skill_range}")

        if len(self.steps) < 3:
            _get_logger().error(f"[SKILL] Макрос '{self.name}' содержит менее 3 шагов, невозможно выполнить", exc_info=True)
            self.running = False
            return

        use_castbar_detection = self.app.settings.get("use_castbar_detection", False)
        movement_delay_enabled = self.app.settings.get("movement_delay_enabled", True)

        if approach_used:
            _get_logger().info(f"[SKILL] [АВТОДОБЕГ] Режим детекции каста (всегда)")

        elif use_castbar_detection:
            _get_logger().info(f"[SKILL] [РЕЖИМ 1] Детекция каста - поиск в цикле шагов")

        elif movement_delay_enabled and user_was_moving:
            _get_logger().info(f"[SKILL] [РЕЖИМ 2] Фиксированная задержка после движения")
            delay_ms = self.app.settings.get("movement_delay_ms", 300)
            if delay_ms > 0:
                time_since_stop = self.app.movement_monitor.get_movement_delay()
                if time_since_stop < delay_ms / 1000.0:
                    sleep_time = (delay_ms / 1000.0) - time_since_stop
                    _get_logger().debug(f"[SKILL] Ожидание инерции движения: {sleep_time*1000:.0f} мс")
                    time.sleep(sleep_time)

        else:
            _get_logger().debug(f"[SKILL] [ИНФО] Режим не выбран (user_was_moving={user_was_moving})")

        num_steps = len(self.steps)
        _get_logger().debug(f"[SKILL] Шаги ({num_steps}): {self.steps}")
        
        step1 = self.steps[0]
        step1_delay = step1[2] if len(step1) > 2 else 90
        step2_repeat_delay = self.step2_repeat_delay if self.step2_repeat_delay else 200
        
        use_ping_delays = self.app.settings.get("use_ping_delays", False)
        if use_ping_delays:
            ping_comp = self.app.get_ping_compensation() * 1000
            # Применяем ping-компенсацию к задержкам
            step1_delay = max(10, step1_delay - ping_comp)
            step2_repeat_delay = max(10, step2_repeat_delay - ping_comp)
            _get_logger().info(f"[SKILL] Режим авто задержек: step1={step1_delay:.0f}мс (пинг компенсация {ping_comp:.0f}мс)")
        else:
            _get_logger().info(f"[SKILL] Режим фиксированных задержек: step1={step1_delay:.0f}мс")

        if approach_used or user_was_moving:
            
            if step1[0] == "key":
                _get_logger().debug(f"[SKILL] Шаг 1: отправка клавиши '{step1[1]}'")
                send_key(step1[1])
                time.sleep(step1_delay / 1000.0)
            
            middle_steps = self.steps[1:-1]
            _get_logger().debug(f"[SKILL] Средние шаги (повторы): {len(middle_steps)} шт.")
            
            if use_castbar_detection and self.app.castbar_point:
                _get_logger().debug(f"[SKILL] castbar_enabled={self.app.castbar_enabled}, castbar_point={self.app.castbar_point}")
                _get_logger().debug(f"[SKILL] castbar_color={self.app.castbar_color}, castbar_threshold={self.app.castbar_threshold}")
                
                first_middle = middle_steps[0]
                _get_logger().info(f"[SKILL] Выполняем первый средний шаг: {first_middle}")
                
                if first_middle[0] == "key":
                    _get_logger().debug(f"[SKILL] Средний шаг: отправка клавиши '{first_middle[1]}'")
                    send_key(first_middle[1])
                    if hasattr(self.app, 'dispatcher') and hasattr(self.app.dispatcher, 'set_cast_lock'):
                        self.app.dispatcher.set_cast_lock(self)
                elif first_middle[0] == "left":
                    if hasattr(self, 'zone_rect') and self.zone_rect:
                        x1, y1, x2, y2 = self.zone_rect
                        center_x = (x1 + x2) // 2
                        center_y = (y1 + y2) // 2
                        _get_logger().info(f"[SKILL+ZONE] Средний шаг: клик в центре зоны ({center_x},{center_y})")
                        click_at_position(center_x, center_y)
                    else:
                        _get_logger().warning(f"[SKILL] zone_rect НЕ установлен, клик в текущей позиции!")
                        click_left()
                    if hasattr(self.app, 'dispatcher') and hasattr(self.app.dispatcher, 'set_cast_lock'):
                        self.app.dispatcher.set_cast_lock(self)
                elif first_middle[0] == "right":
                    if hasattr(self, 'zone_rect') and self.zone_rect:
                        x1, y1, x2, y2 = self.zone_rect
                        center_x = (x1 + x2) // 2
                        center_y = (y1 + y2) // 2
                        _get_logger().info(f"[SKILL+ZONE] Средний шаг: правый клик в центре зоны ({center_x},{center_y})")
                        click_at_position(center_x, center_y)
                    else:
                        _get_logger().warning(f"[SKILL] zone_rect НЕ установлен, правый клик в текущей позиции!")
                        click_right()
                    if hasattr(self.app, 'dispatcher') and hasattr(self.app.dispatcher, 'set_cast_lock'):
                        self.app.dispatcher.set_cast_lock(self)
                
                _get_logger().debug(f"[SKILL] Ожидание кастбара (макс {max(2.0, self.cast_time):.1f} сек)...")
                start_wait = time.time()
                timeout = max(2.0, self.cast_time)
                cast_detected = False
                
                while time.time() - start_wait < timeout and self.running and not self.stop_event.is_set():
                    if self.app.is_castbar_visible():
                        _get_logger().debug(f"[SKILL] Полоска обнаружена через {time.time()-start_wait:.2f}с")
                        cast_detected = True
                        break
                    time.sleep(0.01)
                
                if not cast_detected:
                    _get_logger().debug(f"[SKILL] Полоска не обнаружена за {timeout} сек")
                    self.running = False
                    return
                
                if len(middle_steps) > 1:
                    _get_logger().info(f"[SKILL]  Кастбар найден! Выполняем оставшиеся средние шаги ({len(middle_steps)-1} шт)")
                    for i, step in enumerate(middle_steps[1:], 1):
                        _get_logger().debug(f"[SKILL] Оставшийся средний шаг {i+1}: {step}")
                        if step[0] == "key":
                            send_key(step[1])
                        elif step[0] == "left":
                            click_left()
                        elif step[0] == "right":
                            click_right()
                        elif step[0] == "wait":
                            time.sleep(step[2] / 1000.0)
                        if i < len(middle_steps) - 1:
                            time.sleep(step2_repeat_delay / 1000.0)
                    
                    if len(middle_steps[-1]) > 2 and middle_steps[-1][2] > 0:
                        time.sleep(middle_steps[-1][2] / 1000.0)
                
                with self.cooldown_lock:
                    self.last_used = time.time()
                    
            else:
                _get_logger().info(f"[SKILL] [РЕЖИМ 2] Без детекции кастбара — выполняем {len(middle_steps)} средних шагов")
                for i, step in enumerate(middle_steps):
                    _get_logger().debug(f"[SKILL] Средний шаг {i+1}: {step}")
                    if step[0] == "key":
                        send_key(step[1])
                    elif step[0] == "left":
                        click_left()
                    elif step[0] == "right":
                        click_right()
                    elif step[0] == "wait":
                        time.sleep(step[2] / 1000.0)
                        if i < len(middle_steps) - 1:
                            time.sleep(step2_repeat_delay / 1000.0)
                        continue
                    
                    if len(step) > 2 and step[2] > 0:
                        time.sleep(step[2] / 1000.0)
                    
                    if i < len(middle_steps) - 1:
                        time.sleep(step2_repeat_delay / 1000.0)
                
                with self.cooldown_lock:
                    self.last_used = time.time()
            
            step_last = self.steps[-1]
            _get_logger().info(f"[SKILL] Выполняем последний шаг (свап на ПА): {step_last}")
            if step_last[0] == "key":
                _get_logger().debug(f"[SKILL] Последний шаг: отправка клавиши '{step_last[1]}'")
                send_key(step_last[1])
            elif step_last[0] == "left":
                click_left()
            elif step_last[0] == "right":
                click_right()
            if len(step_last) > 2 and step_last[2] > 0:
                time.sleep(step_last[2] / 1000.0)
            _get_logger().info(f"[SKILL]  Последний шаг выполнен")
                    
        else:
            _get_logger().info(f"[SKILL] ПРОСТОЙ РЕЖИМ: выполняем {num_steps} шагов")
            
            step1 = self.steps[0]
            if step1[0] == "key":
                _get_logger().debug(f"[SKILL] Шаг 1: отправка клавиши '{step1[1]}'")
                send_key(step1[1])
            elif step1[0] == "left":
                _get_logger().debug(f"[SKILL] Шаг 1: левый клик")
                click_left()
            elif step1[0] == "right":
                _get_logger().debug(f"[SKILL] Шаг 1: правый клик")
                click_right()
            
            time.sleep(step1_delay / 1000.0)
            _get_logger().debug(f"[SKILL] Задержка после шага 1: {step1_delay}мс")
            
            middle_steps = self.steps[1:-1]
            _get_logger().debug(f"[SKILL] Средние шаги (повторы шага 2): {len(middle_steps)} шт.")
            
            for i, step in enumerate(middle_steps):
                _get_logger().debug(f"[SKILL] Шаг 2.{i+1}: действие={step[0]}, значение={step[1]}")
                if step[0] == "key":
                    _get_logger().debug(f"[SKILL] Шаг 2.{i+1}: отправка клавиши '{step[1]}'")
                    send_key(step[1])
                    if i == 0 and hasattr(self.app, 'dispatcher') and hasattr(self.app.dispatcher, 'set_cast_lock'):
                        self.app.dispatcher.set_cast_lock(self)
                elif step[0] == "left":
                    _get_logger().debug(f"[SKILL] Шаг 2.{i+1}: левый клик")
                    click_left()
                    if i == 0 and hasattr(self.app, 'dispatcher') and hasattr(self.app.dispatcher, 'set_cast_lock'):
                        self.app.dispatcher.set_cast_lock(self)
                elif step[0] == "right":
                    _get_logger().debug(f"[SKILL] Шаг 2.{i+1}: правый клик")
                    click_right()
                    if i == 0 and hasattr(self.app, 'dispatcher') and hasattr(self.app.dispatcher, 'set_cast_lock'):
                        self.app.dispatcher.set_cast_lock(self)
                
                if len(step) > 2 and step[2] > 0:
                    _get_logger().debug(f"[SKILL] Задержка после шага 2.{i+1}: {step[2]}мс")
                    time.sleep(step[2] / 1000.0)
                
                if i < len(middle_steps) - 1:
                    _get_logger().debug(f"[SKILL] Пауза между повторами шага 2: {step2_repeat_delay}мс")
                    time.sleep(step2_repeat_delay / 1000.0)
            
            step_last = self.steps[-1]
            _get_logger().info(f"[SKILL] Выполняем последний шаг (свап на ПА): {step_last}")
            if step_last[0] == "key":
                _get_logger().debug(f"[SKILL] Шаг 3: отправка клавиши '{step_last[1]}'")
                send_key(step_last[1])
            elif step_last[0] == "left":
                _get_logger().debug(f"[SKILL] Шаг 3: левый клик")
                click_left()
            elif step_last[0] == "right":
                _get_logger().debug(f"[SKILL] Шаг 3: правый клик")
                click_right()
            if len(step_last) > 2 and step_last[2] > 0:
                time.sleep(step_last[2] / 1000.0)
            _get_logger().info(f"[SKILL]  Последний шаг выполнен")

        _get_logger().debug("[SKILL] Ресвап на ПА-сет выполнен")

        with self.cooldown_lock:
            self.last_used = time.time()
            try:
                from backend.session_log import get_session_log
                get_session_log().log("macro_start", f"Макрос '{self.name}' выполнен")
            except Exception:
                pass

        self.running = False
        total_duration = (time.time() - start_time) * 1000
        _get_logger().debug(f"[SKILL] Макрос '{self.name}' завершил выполнение за {total_duration:.2f}мс")
        if hasattr(self, 'app') and hasattr(self.app, 'dispatcher'):
            self.app.dispatcher.on_macro_finished(self.name)