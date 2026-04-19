# macros.py
import threading
import time
import logging
import mouse
import win32gui
import win32con  # ← ДОБАВЛЕНО: константы для ShowWindow
import ctypes
import keyboard as kb
import win32api

# Отложенный импорт логгера для избежания циклической зависимости
_logger = None

def _get_logger():
    global _logger
    if _logger is None:
        from backend.logger_manager import get_logger
        _logger = get_logger('macros')
    return _logger

# Отложенный импорт для звука и session log
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


# ==================== SendInput API для клавиш и кликов ====================

# Загружаем user32.dll для SendInput и kernel32 для GetLastError
user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32

# Константы SendInput - Клавиатура
KEYEVENTF_KEYUP = 0x0002
KEYEVENTF_UNICODE = 0x0004

# Константы SendInput - Мышь
MOUSEEVENTF_ABSOLUTE = 0x8000
MOUSEEVENTF_LEFTDOWN = 0x0002
MOUSEEVENTF_LEFTUP = 0x0004

# Таблица виртуальных кодов клавиш
VK_CODES = {
    'a': 0x41, 'b': 0x42, 'c': 0x43, 'd': 0x44, 'e': 0x45,
    'f': 0x46, 'g': 0x47, 'h': 0x48, 'i': 0x49, 'j': 0x4A,
    'k': 0x4B, 'l': 0x4C, 'm': 0x4D, 'n': 0x4E, 'o': 0x4F,
    'p': 0x50, 'q': 0x51, 'r': 0x52, 's': 0x53, 't': 0x54,
    'u': 0x55, 'v': 0x56, 'w': 0x57, 'x': 0x58, 'y': 0x59,
    'z': 0x5A,
    '0': 0x30, '1': 0x31, '2': 0x32, '3': 0x33, '4': 0x34,
    '5': 0x35, '6': 0x36, '7': 0x37, '8': 0x38, '9': 0x39,
    'f1': 0x70, 'f2': 0x71, 'f3': 0x72, 'f4': 0x73, 'f5': 0x74,
    'f6': 0x75, 'f7': 0x76, 'f8': 0x77, 'f9': 0x78, 'f10': 0x79,
    'f11': 0x7A, 'f12': 0x7B,
    'space': 0x20, 'enter': 0x0D, 'esc': 0x1B, 'tab': 0x09,
    'shift': 0x10, 'ctrl': 0x11, 'alt': 0x12, 'caps': 0x14,
}

# Структура для клавиатуры
class KEYBDINPUT(ctypes.Structure):
    _fields_ = [
        ("wVk", ctypes.wintypes.WORD),
        ("wScan", ctypes.wintypes.WORD),
        ("dwFlags", ctypes.wintypes.DWORD),
        ("time", ctypes.wintypes.DWORD),
        ("dwExtraInfo", ctypes.POINTER(ctypes.wintypes.ULONG))
    ]

class MOUSEINPUT(ctypes.Structure):
    _fields_ = [
        ("dx", ctypes.wintypes.LONG),
        ("dy", ctypes.wintypes.LONG),
        ("mouseData", ctypes.wintypes.DWORD),
        ("dwFlags", ctypes.wintypes.DWORD),
        ("time", ctypes.wintypes.DWORD),
        ("dwExtraInfo", ctypes.POINTER(ctypes.wintypes.ULONG))
    ]

class INPUT(ctypes.Structure):
    _fields_ = [
        ("type", ctypes.wintypes.DWORD),
        ("ki", KEYBDINPUT),
        ("mi", MOUSEINPUT)
    ]

def send_key_via_sendinput(key):
    """
    Отправляет клавишу через WinAPI SendInput.
    Возвращает 1 если успешно, 0 если заблокировано, -1 если ошибка.
    """
    key_lower = key.lower()
    vk = VK_CODES.get(key_lower)
    if not vk:
        _get_logger().warning(f"Unknown key: {key}")
        return -1
    
    # Готовим массив INPUT - используем scan code вместо vk
    extra = ctypes.c_ulong(0)
    inputs = (INPUT * 2)()
    
    # MapVirtualKey для получения scan code
    scan = user32.MapVirtualKeyA(vk, 0)
    if scan == 0:
        scan = vk  # fallback
    
    # DOWN
    inputs[0].type = 1  # INPUT_KEYBOARD
    inputs[0].ki.wVk = vk
    inputs[0].ki.wScan = scan
    inputs[0].ki.dwFlags = 0
    inputs[0].ki.time = 0
    inputs[0].ki.dwExtraInfo = ctypes.pointer(extra)
    
    # UP
    inputs[1].type = 1
    inputs[1].ki.wVk = vk
    inputs[1].ki.wScan = scan
    inputs[1].ki.dwFlags = KEYEVENTF_KEYUP
    inputs[1].ki.time = 0
    inputs[1].ki.dwExtraInfo = ctypes.pointer(extra)
    
    # Отправляем
    result = user32.SendInput(2, ctypes.byref(inputs), ctypes.sizeof(INPUT))
    
    if result == 0:
        # Проверяем через GetLastError (из kernel32!)
        error = kernel32.GetLastError()
        if error == 5:  # ERROR_ACCESS_DENIED
            _get_logger().warning(f"SendInput blocked (access denied) for key: {key}")
            return 0  # действительно заблокировано
        _get_logger().error(f"SendInput error {error} for key: {key}")
        return -1  # ошибка
    
    _get_logger().debug(f"SendInput: key '{key}' sent (result={result})")
    return 1  # успешно

def click_at_position(x, y):
    """
    Эмулирует клик ЛКМ в точке (x, y) через SendInput.
    Скрывает курсор → перемещает → кликает → возвращает → показывает.
    """
    cursor_hidden = False
    current_x, current_y = None, None
    try:
        # Получаем текущую позицию курсора
        current_x, current_y = win32api.GetCursorPos()
        _get_logger().debug(f"[ClickAtPos] Старт: текущая=({current_x},{current_y}), цель=({x},{y})")

        # Скрываем курсор (ShowCursor в win32api, не в win32gui!)
        for _ in range(10):
            if win32api.ShowCursor(False) < 0:
                cursor_hidden = True
                break

        # Перемещаем курсор
        win32api.SetCursorPos((x, y))
        _get_logger().debug(f"[ClickAtPos] Курсор перемещён в ({x},{y})")

        # Готовим клик
        extra = ctypes.c_ulong(0)

        # ЛКМ вниз
        ii1 = INPUT()
        ii1.type = 0
        ii1.mi = MOUSEINPUT(0, 0, 0, MOUSEEVENTF_LEFTDOWN, 0, ctypes.pointer(extra))

        # ЛКМ вверх
        ii2 = INPUT()
        ii2.type = 0
        ii2.mi = MOUSEINPUT(0, 0, 0, MOUSEEVENTF_LEFTUP, 0, ctypes.pointer(extra))

        # Отправляем клик пакетом
        INPUT_ARRAY = INPUT * 2
        input_array = INPUT_ARRAY(ii1, ii2)
        user32.SendInput(2, input_array, ctypes.sizeof(INPUT))
        _get_logger().debug(f"[ClickAtPos] Клик отправлен")

        # Мгновенно возвращаем курсор
        win32api.SetCursorPos((current_x, current_y))

    except Exception as e:
        _get_logger().error(f"[ClickAtPos] Ошибка в ({x},{y}): {e}, fallback на mouse.click()", exc_info=True)
        mouse.click(button="left")
    finally:
        # Гарантированно показываем курсор при любой ошибке
        if cursor_hidden:
            for _ in range(10):
                if win32api.ShowCursor(True) >= 0:
                    break
        # Возвращаем курсор на исходную позицию даже при ошибке
        if current_x is not None and current_y is not None:
            try:
                win32api.SetCursorPos((current_x, current_y))
            except Exception:
                pass

# --- Функция отправки клавиш (через SendInput с fallback) ---
def send_key(key):
    """
    Отправляет клавишу через SendInput.
    - result = 1: успешно через SendInput
    - result = 0: заблокировано → игнорируем нажатие!
    - result = -1: ошибка → fallback на keyboard
    """
    _get_logger().debug(f"send_key: попытка отправить '{key}' через SendInput")
    
    result = send_key_via_sendinput(key)
    
    if result == 1:
        # Успешно через SendInput
        _get_logger().debug(f"send_key: '{key}' отправлен через SendInput")
        return True
    elif result == 0:
        # ЗАБЛОКИРОВАНО! SendInput не работает сейчас
        _get_logger().warning(f"⚠️ SendInput заблокирован для '{key}' - игнорируем!")
        return False  # Это и есть защита - игнорируем нажатие если заблокировано
    else:
        # Ошибка - пробуем keyboard
        _get_logger().warning(f"SendInput error, fallback на keyboard")
        try:
            kb.send(key)
            _get_logger().debug(f"send_key: '{key}' отправлен через keyboard")
            return True
        except Exception as e:
            _get_logger().error(f"send_key: ошибка при отправке '{key}': {e}")
            return False

def activate_game_window(window_title):
    """Активирует окно с указанным заголовком (частичное совпадение)."""
    def enum_callback(hwnd, hwnds):
        if win32gui.IsWindowVisible(hwnd):
            title = win32gui.GetWindowText(hwnd)
            if window_title.lower() in title.lower():
                hwnds.append(hwnd)
        return True
    hwnds = []
    win32gui.EnumWindows(enum_callback, hwnds)
    if hwnds:
        win32gui.SetForegroundWindow(hwnds[0])
        time.sleep(0.1)
        _get_logger().debug(f"Активировано окно: {hwnds[0]}")
        return True
    return False

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

            # Кулдаун уже проверен в dispatcher.request_macro() — не дублируем!
            # if hasattr(self, 'cooldown') and self.cooldown > 0: ...

            # Проверка cast_lock теперь делается в dispatcher.request_macro()
            # Здесь просто запускаем макрос

            self.running = True
            self.last_start_time = time.time()  # ← Защита от быстрой остановки
            _get_logger().debug(f"[START] Макрос '{self.name}' помечен как запущенный")

        self.stop_event.clear()
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()
        _get_logger().info(f"[+] Макрос '{self.name}' запущен")

    def stop(self):
        _get_logger().debug(f"[STOP] Попытка остановки макроса '{self.name}'")
        self.running = False
        self.stop_event.set()
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=2.0)
            if self.thread.is_alive():
                _get_logger().warning(f"Поток макроса '{self.name}' не завершился, принудительно...")
        _get_logger().info(f"⏹️ Макрос '{self.name}' остановлен")

    def _check_window(self):
        if not hasattr(self.app, "window_locked"):
            return True
        if not self.app.window_locked:
            return True
        target = self.app.target_window_title.strip().lower()
        if not target:
            return True
        try:
            hwnd = win32gui.GetForegroundWindow()
            active_title = win32gui.GetWindowText(hwnd).lower()
            result = target in active_title
            if not result:
                _get_logger().warning(f"[{self.name}] Окно потеряно: '{active_title}' != '{target}'")
                # Звук и session log при потере окна
                _play_window_lost_sound()
                _log_session_event(f"Окно потеряно: '{active_title}' вместо '{target}'")
            return result
        except Exception as e:
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
            for i, (action, value, delay_ms) in enumerate(self.steps):
                if not self.running or self.stop_event.is_set():
                    _get_logger().debug(f"[SIMPLE] Макрос '{self.name}' прерван на шаге {i+1}")
                    break
                if not self._check_window():
                    _get_logger().debug(f"[SIMPLE] Окно неактивно, прерывание на шаге {i+1}")
                    break
                step_start = time.time()
                _get_logger().debug(f"[SIMPLE] Шаг {i+1}: действие='{action}', значение='{value}', задержка={delay_ms}мс")
                try:
                    if action == "key":
                        send_key(value)
                        _get_logger().debug(f"[SIMPLE] Шаг {i+1}: клавиша '{value}' отправлена")
                    elif action == "left":
                        mouse.click(button="left")
                        _get_logger().debug(f"[SIMPLE] Шаг {i+1}: левый клик мыши")
                    elif action == "right":
                        mouse.click(button="right")
                        _get_logger().debug(f"[SIMPLE] Шаг {i+1}: правый клик мыши")
                    elif action == "wait":
                        _get_logger().debug(f"[SIMPLE] Шаг {i+1}: пауза {delay_ms}мс")
                except Exception as e:
                    _get_logger().error(f"[SIMPLE] Ошибка выполнения шага {i+1}: {e}")
                if delay_ms > 0 and self.running:
                    time.sleep(delay_ms / 1000.0)
                step_duration = (time.time() - step_start) * 1000
                _get_logger().debug(f"[SIMPLE] Шаг {i+1} выполнен за {step_duration:.2f}мс")
        except Exception as e:
            _get_logger().error(f"[SIMPLE] Ошибка в макросе '{self.name}': {e}", exc_info=True)
        finally:
            self.running = False
            total_duration = (time.time() - start_time) * 1000
            _get_logger().debug(f"[SIMPLE] Макрос '{self.name}' завершил выполнение за {total_duration:.2f}мс")
            # ✅ Сообщаем диспетчеру об окончании для сброса cast_lock
            if hasattr(self, 'app') and hasattr(self.app, 'dispatcher'):
                self.app.dispatcher.on_macro_finished(self.name)


class ZoneMacro(Macro):
    """
    Зональный макрос с событийной моделью (без polling).
    Реагирует на клики через MouseClickMonitor.mouse_clicked.
    """
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
        poll_interval=10,  # Устаревший параметр, игнорируется (для обратной совместимости)
    ):
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
        self._mouse_click_connected = False  # Флаг подписки на клики

    def _connect_mouse_click(self, app):
        """Подписывает макрос на клики мыши"""
        if self._mouse_click_connected:
            return  # Уже подписан

        if hasattr(app, 'mouse_click_monitor') and app.mouse_click_monitor:
            app.mouse_click_monitor.mouse_clicked.connect(self.on_mouse_click)
            self._mouse_click_connected = True
            _get_logger().debug(f"[ZONE] Макрос '{self.name}' подписан на клики мыши")

    def on_mouse_click(self, x, y):
        """Обработка клика мыши — проверяет попадание в зону и запускает макрос"""
        _get_logger().debug(f"[ZONE] on_mouse_click '{self.name}': клик ({x},{y}), зона={self.zone_rect}")

        # Проверяем есть ли зона и клик в ней
        if not self.zone_rect:
            _get_logger().warning(f"[ZONE] zone_rect не установлен для '{self.name}'")
            return

        if not self._is_point_in_rect(x, y, self.zone_rect):
            _get_logger().debug(f"[ZONE] Клик ({x},{y}) НЕ в зоне {self.zone_rect}")
            return

        _get_logger().info(f"[ZONE] ✓ Клик в области: ({x},{y}), зона={self.zone_rect}")

        # ✅ Проверка cooldown теперь в диспетчере - не проверяем здесь!
        # Диспетчер сам решает запускать или нет на основе last_used

        # Проверка global_stopped
        if self.app.global_stopped:
            _get_logger().debug(f"[ZONE] {self.name}: глобальная блокировка, игнорируем клик")
            return

        # Проверка задержки после движения
        if self.app.settings.get("movement_delay_enabled", True):
            delay_ms = self.app.settings.get("movement_delay_ms", 100)
            if delay_ms > 0:
                time_since_stop = self.app.movement_monitor.get_movement_delay()
                if time_since_stop < delay_ms / 1000.0:
                    sleep_time = (delay_ms / 1000.0) - time_since_stop
                    _get_logger().debug(f"[ZONE] {self.name}: Ожидание инерции движения: {sleep_time*1000:.0f} мс")
                    time.sleep(sleep_time)

        # Проверка дальности (опционально)
        if self.skill_id is not None and self.app.settings.get("check_distance", False):
            tolerance = self.app.settings.get("distance_tolerance", 1.0)
            if self.app.target_distance is None:
                _get_logger().debug(f"[ZONE] {self.name}: расстояние не определено, пропускаем")
                return
            cast_required = self.skill_range + tolerance
            if self.app.target_distance > cast_required:
                _get_logger().debug(f"[ZONE] {self.name}: цель слишком далеко ({self.app.target_distance:.1f}м)")
                return

        # Запускаем через dispatcher если есть
        if not self.running:
            _get_logger().info(f"[ZONE] ▶ Запрос на запуск '{self.name}' по клику в области ({x},{y})")
            if hasattr(self, 'app') and hasattr(self.app, 'dispatcher'):
                # Приоритет 2 для зональных макросов
                if self.app.dispatcher.request_macro(self, priority=2):
                    _get_logger().info(f"[ZONE] ✅ '{self.name}': ЗАПУЩЕН диспетчером")
                else:
                    _get_logger().warning(f"[ZONE] ❌ '{self.name}': ЗАБЛОКИРОВАНО диспетчером")
            else:
                self.start()
        else:
            _get_logger().info(f"[ZONE] Макрос '{self.name}' уже выполняется")

    def _is_point_in_rect(self, x, y, rect):
        """Проверяет находится ли точка в прямоугольнике"""
        x1, y1, x2, y2 = rect
        return x1 <= x <= x2 and y1 <= y <= y2

    def _run(self):
        """
        Выполнение зонального макроса (событийная модель).
        Подписывается на клики мыши, выполняет макрос при клике в зоне.
        """
        _get_logger().info(f"[ZONE] ====== Запуск зонального макроса '{self.name}', зона={self.zone_rect} ======")

        # Подписываемся на клики мыши
        self._connect_mouse_click(self.app)

        try:
            # Ждём сигнала остановки (без polling!)
            while self.running and not self.stop_event.is_set():
                self.stop_event.wait(0.1)  # Нет активного polling, просто ждём

        except Exception as e:
            _get_logger().error(f"[ZONE] Ошибка в макросе '{self.name}': {e}", exc_info=True)
        finally:
            self.was_inside = False
            self.running = False
            _get_logger().debug(f"[ZONE] Макрос '{self.name}' завершил работу (подписка на клики остаётся)")
            # ✅ Сообщаем диспетчеру об окончании для сброса cast_lock
            if hasattr(self, 'app') and hasattr(self.app, 'dispatcher'):
                self.app.dispatcher.on_macro_finished(self.name)

    def _execute_once(self):
        """Выполнение зонального макроса без привязанного скилла (эмулируем клик)."""
        _get_logger().debug(f"[ZONE] {self.name}: выполнение простого макроса (без скилла)")
        step_start_total = time.time()
        try:
            for i, (action, value, delay_ms) in enumerate(self.steps):
                # Проверка остановки
                if not self.running or self.stop_event.is_set():
                    _get_logger().debug(f"[ZONE] {self.name}: прерван на шаге {i+1}")
                    break
                # Проверка окна
                if not self._check_window():
                    _get_logger().debug(f"[ZONE] {self.name}: окно неактивно, прерывание")
                    break
                # Проверка что курсор ещё в зоне (можно выйти из зоны чтобы прервать)
                current_x, current_y = mouse.get_position()
                if self.zone_rect and not self._is_point_in_rect(current_x, current_y, self.zone_rect):
                    _get_logger().debug(f"[ZONE] {self.name}: курсор вышел из зоны ({current_x},{current_y}), прерывание")
                    break

                step_start = time.time()
                _get_logger().debug(f"[ZONE] {self.name}: шаг {i+1}: действие='{action}', значение='{value}', задержка={delay_ms}мс")
                try:
                    if action == "key":
                        send_key(value)
                    elif action in ("left", "right"):
                        # Для зональных макросов используем SendInput API (клик в центре зоны)
                        if hasattr(self, 'zone_rect') and self.zone_rect:
                            x1, y1, x2, y2 = self.zone_rect
                            center_x = (x1 + x2) // 2
                            center_y = (y1 + y2) // 2
                            _get_logger().debug(f"[ZONE] {self.name}: SendInput клик в центре зоны ({center_x},{center_y})")
                            click_at_position(center_x, center_y)
                        else:
                            mouse.click(button=action)
                    elif action == "wait":
                        pass
                except Exception as e:
                    _get_logger().error(f"[ZONE] {self.name}: ошибка шага {i+1}: {e}")
                if delay_ms > 0 and self.running:
                    time.sleep(delay_ms / 1000.0)
                step_duration = (time.time() - step_start) * 1000
                _get_logger().debug(f"[ZONE] {self.name}: шаг {i+1} выполнен за {step_duration:.2f}мс")
        except Exception as e:
            _get_logger().error(f"[ZONE] {self.name}: ошибка выполнения: {e}")
        finally:
            _get_logger().debug(f"[ZONE] {self.name}: весь макрос выполнен за {(time.time()-step_start_total)*1000:.2f}мс")

    def _execute_skill(self):
        """Выполнение зонального макроса с привязанным скиллом."""
        if len(self.steps) < 3:
            _get_logger().error(f"[ZONE] {self.name}: менее 3 шагов, невозможно выполнить")
            return

        step1, step2, step3 = self.steps[0], self.steps[1], self.steps[2]
        _get_logger().debug(f"[ZONE] {self.name}: выполнение скилл-макроса")

        actual_cast_time = self.app.get_actual_cast_time(self.cast_time)

        # Проверка что курсор в зоне перед началом
        current_x, current_y = mouse.get_position()
        if self.zone_rect and not self._is_point_in_rect(current_x, current_y, self.zone_rect):
            _get_logger().debug(f"[ZONE] {self.name}: курсор вышел из зоны ({current_x},{current_y}), отмена")
            return

        # --- Шаг 1 ---
        if step1[0] == "key":
            _get_logger().debug(f"[ZONE] {self.name}: шаг 1 – отправка клавиши '{step1[1]}'")
            send_key(step1[1])
            if step1[2] > 0:
                time.sleep(step1[2] / 1000.0)

        # Проверка что курсор ещё в зоне после шага 1
        if self.zone_rect:
            current_x, current_y = mouse.get_position()
            if not self._is_point_in_rect(current_x, current_y, self.zone_rect):
                _get_logger().debug(f"[ZONE] {self.name}: курсор вышел из зоны после шага 1, прерывание")
                return

        # Блокировка каста уже установлена в dispatcher.request_macro()!

        # --- Шаг 2 ---
        if step2[0] == "key":
            _get_logger().debug(f"[ZONE] {self.name}: шаг 2 – отправка клавиши '{step2[1]}'")
            send_key(step2[1])
        elif step2[0] in ("left", "right"):
            _get_logger().debug(f"[ZONE] {self.name}: шаг 2 – {step2[0]} клик")
            # Для зональных макросов используем SendInput API (клик в центре зоны)
            if hasattr(self, 'zone_rect') and self.zone_rect:
                x1, y1, x2, y2 = self.zone_rect
                center_x = (x1 + x2) // 2
                center_y = (y1 + y2) // 2
                _get_logger().debug(f"[ZONE] {self.name}: SendInput клик в центре зоны ({center_x},{center_y})")
                click_at_position(center_x, center_y)
            else:
                mouse.click(button=step2[0])
        if step2[2] > 0:
            time.sleep(step2[2] / 1000.0)

        # --- Шаг 3 ---
        if step3[0] == "key":
            _get_logger().debug(f"[ZONE] {self.name}: шаг 3 – отправка клавиши '{step3[1]}'")
            send_key(step3[1])
            if step3[2] > 0:
                time.sleep(step3[2] / 1000.0)
        _get_logger().debug(f"[ZONE] {self.name}: ресвап на ПА-сет выполнен")


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
            # Клик по калиброванным координатам ПЕРЕД шагами (если настроено)
            if hasattr(self.app, '_settings'):
                buff_click_point = self.app._settings.get("buff_8004_click_point", "0,0")
                if buff_click_point and buff_click_point != "0,0":
                    try:
                        parts = buff_click_point.split(",")
                        if len(parts) == 2:
                            x, y = int(parts[0]), int(parts[1])
                            _get_logger().info(f"[BUFF] Клик по калиброванным координатам: ({x}, {y})")
                            click_at_position(x, y)
                            time.sleep(0.1)  # Небольшая задержка после клика
                            _get_logger().info(f"[BUFF] Клик выполнен")
                    except Exception as e:
                        _get_logger().error(f"[BUFF] Ошибка клика по координатам: {e}")

            for i, (action, value, delay_ms) in enumerate(self.steps):
                if not self.running or self.stop_event.is_set():
                    _get_logger().info(f"[BUFF] Макрос прерван на шаге {i+1}")
                    break
                if not self._check_window():
                    _get_logger().info(f"[BUFF] Окно неактивно, прерывание")
                    break
                step_start = time.time()
                _get_logger().info(f"[BUFF] Шаг {i+1}: действие='{action}', значение='{value}', задержка={delay_ms}мс")
                try:
                    if action == "key":
                        send_key(value)
                        _get_logger().info(f"[BUFF] Нажата клавиша баффа: {value}")
                    elif action == "left":
                        mouse.click(button="left")
                    elif action == "right":
                        mouse.click(button="right")
                    elif action == "wait":
                        pass
                except Exception as e:
                    _get_logger().error(f"[BUFF] Ошибка выполнения шага {i+1}: {e}")
                if delay_ms > 0 and self.running:
                    time.sleep(delay_ms / 1000.0)
                step_duration = (time.time() - step_start) * 1000
                _get_logger().info(f"[BUFF] Шаг {i+1} выполнен за {step_duration:.2f}мс")

            if self.running and not self.stop_event.is_set():
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
                    _get_logger().error("[BUFF] Главное окно не имеет метода apply_buff")
        except Exception as e:
            _get_logger().error(f"[BUFF] Ошибка в макросе-баффе '{self.name}': {e}", exc_info=True)
        finally:
            self.running = False
            total_duration = (time.time() - start_time) * 1000
            _get_logger().info(f"[BUFF] Макрос-бафф '{self.name}' завершил выполнение за {total_duration:.2f}мс")
            # ✅ Сообщаем диспетчеру об окончании для сброса cast_lock
            if hasattr(self, 'app') and hasattr(self.app, 'dispatcher'):
                self.app.dispatcher.on_macro_finished(self.name)


class SkillMacro(SimpleMacro):
    def __init__(self, name, steps, app, hotkey=None,
                 skill_id=None, cooldown=0, skill_range=0, cast_time=0.0,
                 castbar_swap_delay=0):
        super().__init__(name, steps, app, hotkey)
        self.type = "skill"
        self.skill_id = skill_id
        self.cooldown = float(cooldown) if cooldown else 0.0
        self.skill_range = float(skill_range) if skill_range else 0.0
        self.cast_time = cast_time
        self.last_used = 0
        self.castbar_swap_delay = max(0, castbar_swap_delay)
        self.cooldown_lock = threading.Lock()
        self.zone_rect = None  # Область для автозапуска (устанавливается извне)
        self._mouse_click_connected = False  # Флаг подписки на клики
        
        # Подписываемся на клики ТОЛЬКО если есть зона
        # Подписка происходит позже когда zone_rect будет установлен
    
    def _connect_mouse_click(self, app):
        """Подписывает макрос на клики мыши"""
        if self._mouse_click_connected:
            return  # Уже подписан

        if hasattr(app, 'mouse_click_monitor') and app.mouse_click_monitor:
            app.mouse_click_monitor.mouse_clicked.connect(self.on_mouse_click)
            self._mouse_click_connected = True
            _get_logger().debug(f"[SKILL+ZONE] Макрос '{self.name}' подписан на клики")

    def on_mouse_click(self, x, y):
        """Обработка клика мыши для зональных макросов"""
        _get_logger().debug(f"[SKILL+ZONE] on_mouse_click вызван для '{self.name}': клик ({x},{y}), zone_rect={self.zone_rect}")
        
        # Проверяем есть ли зона и клик в ней
        if not self.zone_rect:
            _get_logger().warning(f"[SKILL+ZONE] zone_rect не установлен для '{self.name}'")
            return
        
        if not self._is_point_in_rect(x, y, self.zone_rect):
            _get_logger().debug(f"[SKILL+ZONE] Клик ({x},{y}) НЕ в зоне {self.zone_rect}")
            return
        
        _get_logger().info(f"[SKILL+ZONE] ✓ Клик в области: ({x},{y}), зона={self.zone_rect}")

        # ✅ Проверка cooldown теперь в диспетчере - не проверяем здесь!

        # ПРОВЕРКА БЛОКИРОВКИ КАСТА!
        if hasattr(self, 'app') and hasattr(self.app, 'dispatcher'):
            if self.app.dispatcher.is_cast_locked():
                remaining = self.app.dispatcher.get_cast_lock_remaining()
                _get_logger().warning(f"[SKILL+ZONE] ❌ ЗАБЛОКИРОВАНО: идёт каст (ост. {remaining:.2f}с)")
                return
            else:
                _get_logger().debug(f"[SKILL+ZONE] ✓ Блокировка каста: НЕ заблокировано")

        # Запускаем макрос через диспетчер если не выполняется
        if not self.running:
            _get_logger().info(f"[SKILL+ZONE] ▶ Запрос на запуск '{self.name}' по клику в области ({x},{y})")
            if hasattr(self, 'app') and hasattr(self.app, 'dispatcher'):
                # Приоритет 2 для зональных скиллов (критично для PvP)
                if self.app.dispatcher.request_macro(self, priority=2):
                    _get_logger().info(f"[SKILL+ZONE] ✅ '{self.name}': ЗАПУЩЕН диспетчером")
                else:
                    _get_logger().warning(f"[SKILL+ZONE] ❌ '{self.name}': ЗАБЛОКИРОВАНО диспетчером")
            else:
                # Фоллбэк если dispatcher не доступен
                self.start()
        else:
            _get_logger().info(f"[SKILL+ZONE] Макрос '{self.name}' уже выполняется")
    
    def _is_point_in_rect(self, x, y, rect):
        """Проверяет находится ли точка в прямоугольнике"""
        x1, y1, x2, y2 = rect
        return x1 <= x <= x2 and y1 <= y <= y2

    def _run(self):
        _get_logger().debug(f"[SKILL] Начало выполнения макроса-скилла '{self.name}'")
        start_time = time.time()

        # Проверяем тип макроса для логирования
        has_zone = hasattr(self, 'zone_rect') and self.zone_rect
        _get_logger().info(f"[SKILL] {'[ЗОНАЛЬНЫЙ]' if has_zone else '[ОБЫЧНЫЙ]'} макрос '{self.name}', zone_rect={self.zone_rect if has_zone else 'нет'}")

        # Проверка окна перед началом (НЕ проверяем для макросов с zone_rect - они работают в фоне)
        if not has_zone:
            if not self._check_window():
                _get_logger().debug(f"[SKILL] Окно неактивно, прерывание")
                self.running = False
                return

        # НЕ записываем last_used здесь — диспетчер уже сделал это в request_macro()!
        # last_used будет обновлён в finally после ЗАВЕРШЕНИЯ макроса

        # Автодобегание, если включено
        approach_used = False
        user_was_moving = False  # Пользователь сам бегал

        # Всегда проверяем, двигался ли пользователь перед запуском (независимо от check_distance)
        time_since_stop = self.app.movement_monitor.get_movement_delay()
        if time_since_stop < 0.5:  # Если прошло меньше 0.5с с последнего движения
            user_was_moving = True
            _get_logger().debug(f"[SKILL] Пользователь двигался (возраст={time_since_stop*1000:.0f}мс), используем цикл")

        # ПРОВЕРКА ДИСТАНЦИИ
        check_distance = self.app.settings.get("check_distance", False)
        _get_logger().info(f"[SKILL] check_distance={check_distance}, skill_range={self.skill_range}, target_distance={self.app.target_distance}")
        
        if check_distance and self.skill_range > 0:
            tolerance = self.app.settings.get("distance_tolerance", 1.0)
            cast_required = self.skill_range + tolerance
            target_dist = max(0, self.skill_range - 0.2)   # цель подбегания
            current = self.app.target_distance

            if current is None:
                # Расстояние не определено - выполняем как без автодобега
                _get_logger().warning(f"[SKILL] Макрос '{self.name}': расстояние не определено (OCR не работает?), выполняем без подбегания")
            elif current > target_dist:
                _get_logger().info(f"[SKILL] Макрос '{self.name}': цель слишком далеко ({current:.1f}м, нужно ≤{target_dist:.1f}), ПОДБЕГАЕМ")
                approach_used = True
                kb.press('w')
                try:
                    approach_start = time.time()
                    while self.running and not self.stop_event.is_set():
                        if not has_zone and not self._check_window():
                            _get_logger().debug(f"[SKILL] Окно неактивно, прерывание подбегания")
                            break
                        current_dist = self.app.target_distance
                        if current_dist is not None and current_dist <= target_dist:
                            _get_logger().info(f"[SKILL] Подбежали до {current_dist:.1f}м за {time.time()-approach_start:.2f}с")
                            break
                        time.sleep(0.01)  # Ускоренный цикл проверки дистанции (10 мс вместо 50 мс)
                finally:
                    kb.release('w')
                # Сокращённая задержка после остановки (60 мс вместо 200 мс)
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
            _get_logger().error(f"[SKILL] Макрос '{self.name}' содержит менее 3 шагов, невозможно выполнить")
            self.running = False
            return

        # Проверка задержки после движения ИЛИ детекция каста
        use_castbar_detection = self.app.settings.get("use_castbar_detection", False)
        movement_delay_enabled = self.app.settings.get("movement_delay_enabled", True)

        # ВАЖНО: При автодобегании ВСЕГДА используется детекция каста
        # При WASD — зависит от выбранного режима
        if approach_used:
            # Автодобег → всегда детекция каста
            _get_logger().info(f"[SKILL] [АВТОДОБЕГ] Режим детекции каста (всегда)")

        elif use_castbar_detection:
            # ===== РЕЖИМ 1: Детекция каста (ВСЕГДА когда включена) =====
            # Ничего не делаем - кастбар будет искаться ВО ВРЕМЯ шагов (в цикле спама шаг 2)
            _get_logger().info(f"[SKILL] [РЕЖИМ 1] Детекция каста - поиск в цикле шагов")

        elif movement_delay_enabled and user_was_moving:
            # ===== РЕЖИМ 2: Фиксированная задержка (только если двигался) =====
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

        step1, step2, step3 = self.steps[0], self.steps[1], self.steps[2]
        _get_logger().debug(f"[SKILL] Шаги: 1={step1}, 2={step2}, 3={step3}")

        actual_cast_time = self.app.get_actual_cast_time(self.cast_time)

        # Определяем задержки из шагов
        step1_delay = step1[2] if len(step1) > 2 else 90
        step23_delay = step2[2] if len(step2) > 2 else 15
        
        # Логируем режим
        use_ping_delays = self.app.settings.get("use_ping_delays", False)
        if use_ping_delays:
            ping_comp = self.app.get_ping_compensation() * 1000
            _get_logger().info(f"[SKILL] Режим авто задержек: step1={step1_delay:.0f}мс, step23={step23_delay:.0f}мс (пинг компенсация {ping_comp:.0f}мс)")
        else:
            _get_logger().info(f"[SKILL] Режим фиксированных задержек: step1={step1_delay:.0f}мс, step23={step23_delay:.0f}мс")

        if approach_used or user_was_moving:
            # ===== БЫЛ АВТОДОБЕГ или ПОЛЬЗОВАТЕЛЬ БЕГАЛ: логика с циклом =====

            # --- Шаг 1 (свап в пение) ---
            if step1[0] == "key":
                _get_logger().debug(f"[SKILL] Шаг 1: отправка клавиши '{step1[1]}'")
                send_key(step1[1])
                time.sleep(step1_delay / 1000.0)

            # Устанавливаем блокировку каста ПЕРЕД шагом 2 — когда реально начинается каст
            # Это точнее чем установка в request_macro() потому что учитывает время
            # потраченное на автодобег, задержки после движения и шаг 1
            if self.cast_time > 0 and hasattr(self, 'app') and hasattr(self.app, 'dispatcher'):
                actual_cast_time = self.app.get_actual_cast_time(self.cast_time)
                margin = self.app.settings.get("cast_lock_margin", 0.4)
                lock_duration = actual_cast_time + margin
                self.app.dispatcher.cast_lock_until = time.time() + lock_duration
                _get_logger().info(f"[SKILL] 🔒 Блокировка каста: {lock_duration:.2f}с (cast={actual_cast_time:.2f}с + margin={margin:.2f}с)")

            # --- ЦИКЛ: спамим шаг 2 + ищем полоску каста ---
            cast_detected = False
            
            # Проверяем: нужно ли использовать детекцию кастбара
            # (а не просто включён ли кастбар в настройках)
            if use_castbar_detection and self.app.castbar_point:
                _get_logger().debug(f"[SKILL] castbar_enabled={self.app.castbar_enabled}, castbar_point={self.app.castbar_point}")
                _get_logger().debug(f"[SKILL] castbar_color={self.app.castbar_color}, castbar_threshold={self.app.castbar_threshold}")

                _get_logger().info(f"[SKILL] ТЕСТ: ОДИН клик шаг 2 (без спама)")
                
                # ОДИН КЛИК ШАГА 2 (для теста)
                if step2[0] == "key":
                    _get_logger().debug(f"[SKILL] Шаг 2: отправка клавиши '{step2[1]}'")
                    send_key(step2[1])
                elif step2[0] == "left":
                    if hasattr(self, 'zone_rect') and self.zone_rect:
                        x1, y1, x2, y2 = self.zone_rect
                        center_x = (x1 + x2) // 2
                        center_y = (y1 + y2) // 2
                        _get_logger().info(f"[SKILL+ZONE] Шаг 2: SendInput клик в центре зоны ({center_x},{center_y}), rect=({x1},{y1},{x2},{y2})")
                        click_at_position(center_x, center_y)
                    else:
                        _get_logger().warning(f"[SKILL] Шаг 2: zone_rect НЕ установлен, клик в ТЕКУЩЕЙ позиции мыши!")
                        mouse.click(button="left")
                elif step2[0] == "right":
                    if hasattr(self, 'zone_rect') and self.zone_rect:
                        x1, y1, x2, y2 = self.zone_rect
                        center_x = (x1 + x2) // 2
                        center_y = (y1 + y2) // 2
                        _get_logger().info(f"[SKILL+ZONE] Шаг 2: SendInput клик в центре зоны ({center_x},{center_y}), rect=({x1},{y1},{x2},{y2})")
                        click_at_position(center_x, center_y)
                    else:
                        _get_logger().warning(f"[SKILL] Шаг 2: zone_rect НЕ установлен, клик в ТЕКУЩЕЙ позиции мыши!")
                        mouse.click(button="right")

                # Ждём кастбар без спама
                _get_logger().debug(f"[SKILL] Ожидание кастбара (макс 2 сек)...")
                start_wait = time.time()
                timeout = 2.0

                while time.time() - start_wait < timeout and self.running and not self.stop_event.is_set():
                    # Проверяем полоску каста БЕЗ ЗАДЕРЖКИ (мгновенно!)
                    if self.app.is_castbar_visible():
                        _get_logger().debug(f"[SKILL] Полоска обнаружена через {time.time()-start_wait:.2f}с")
                        _get_logger().info(f"[SKILL] ✅ Кастбар найден, выполняем Шаг 3")

                        # Блокировка уже установлена после шага 1, просто сбрасываем last_used
                        with self.cooldown_lock:
                            self.last_used = time.time()

                        # Свап на ПА НЕМЕДЛЕННО (без задержек)
                        cast_detected = True
                        _get_logger().debug(f"[SKILL] Выход из цикла (cast_detected=True), self.running={self.running}")
                        break

                if not cast_detected:
                    _get_logger().debug(f"[SKILL] Полоска не обнаружена за {timeout} сек, ресвап не выполняется")
                    self.running = False
                    return
            else:
                # РЕЖИМ 2 (задержка после движения) или кастбар не настроен
                # Просто выполняем шаг 2 без ожидания кастбара
                _get_logger().info(f"[SKILL] [РЕЖИМ 2] Без детекции кастбара — выполняем шаг 2")
                if step2[0] == "key":
                    _get_logger().debug(f"[SKILL] Шаг 2: отправка клавиши '{step2[1]}'")
                    send_key(step2[1])
                elif step2[0] == "left":
                    mouse.click(button="left")
                elif step2[0] == "right":
                    mouse.click(button="right")
                if step2[2] > 0:
                    time.sleep(step2[2] / 1000.0)

                # Блокировка уже установлена в start()!
                with self.cooldown_lock:
                    self.last_used = time.time()

            # Дошли ли мы до Шага 3?
            _get_logger().info(f"[SKILL] После цикла: cast_detected={cast_detected}, self.running={self.running}")

            # --- Шаг 3 (свап на ПА) ---
            _get_logger().info(f"[SKILL] Выполняем Шаг 3: {step3}")
            if step3[0] == "key":
                _get_logger().debug(f"[SKILL] Шаг 3: отправка клавиши '{step3[1]}'")
                send_key(step3[1])
                time.sleep(step23_delay / 1000.0)
            _get_logger().info(f"[SKILL] ✅ Шаг 3 выполнен")
                    
        else:
            # ===== НЕТ АВТОДОБЕГА и НЕ БЕГАЛ: простая логика - 3 шага с задержками =====
            _get_logger().info(f"[SKILL] ПРОСТОЙ РЕЖИМ: выполняем 3 шага")

            # --- Шаг 1 ---
            if step1[0] == "key":
                _get_logger().debug(f"[SKILL] Шаг 1: отправка клавиши '{step1[1]}'")
                send_key(step1[1])
            elif step1[0] == "left":
                _get_logger().debug(f"[SKILL] Шаг 1: левый клик")
                mouse.click(button="left")
            elif step1[0] == "right":
                _get_logger().debug(f"[SKILL] Шаг 1: правый клик")
                mouse.click(button="right")

            # Блокировка каста: устанавливаем ПЕРЕД шагом 2 когда реально начинается каст
            if self.cast_time > 0 and hasattr(self, 'app') and hasattr(self.app, 'dispatcher'):
                actual_cast_time = self.app.get_actual_cast_time(self.cast_time)
                margin = self.app.settings.get("cast_lock_margin", 0.4)
                lock_duration = actual_cast_time + margin
                self.app.dispatcher.cast_lock_until = time.time() + lock_duration
                _get_logger().info(f"[SKILL] 🔒 Блокировка каста: {lock_duration:.2f}с (cast={actual_cast_time:.2f}с + margin={margin:.2f}с)")

            time.sleep(step1_delay / 1000.0)
            _get_logger().debug(f"[SKILL] Задержка после шага 1: {step1_delay}мс")

            # --- Шаг 2 ---
            _get_logger().debug(f"[SKILL] Шаг 2: действие={step2[0]}, значение={step2[1]}")
            if step2[0] == "key":
                _get_logger().debug(f"[SKILL] Шаг 2: отправка клавиши '{step2[1]}'")
                send_key(step2[1])
            elif step2[0] == "left":
                _get_logger().debug(f"[SKILL] Шаг 2: левый клик")
                mouse.click(button="left")
            elif step2[0] == "right":
                _get_logger().debug(f"[SKILL] Шаг 2: правый клик")
                mouse.click(button="right")
            _get_logger().debug(f"[SKILL] Задержка после шага 2: {step23_delay}мс")
            time.sleep(step23_delay / 1000.0)

            # last_used обновляется в конце _run() — не здесь!

            # --- Шаг 3 ---
            _get_logger().debug(f"[SKILL] Шаг 3: действие={step3[0]}, значение={step3[1]}")
            if step3[0] == "key":
                _get_logger().debug(f"[SKILL] Шаг 3: отправка клавиши '{step3[1]}'")
                send_key(step3[1])
            elif step3[0] == "left":
                _get_logger().debug(f"[SKILL] Шаг 3: левый клик")
                mouse.click(button="left")
            elif step3[0] == "right":
                _get_logger().debug(f"[SKILL] Шаг 3: правый клик")
                mouse.click(button="right")
            if step3[2] > 0:
                time.sleep(step3[2] / 1000.0)

        _get_logger().debug("[SKILL] Ресвап на ПА-сет выполнен")

        # Обновляем last_used ПОСЛЕ реального завершения (для корректного КД)
        with self.cooldown_lock:
            self.last_used = time.time()
            # Записываем в session log успешное выполнение
            try:
                from backend.session_log import get_session_log
                get_session_log().log("macro_start", f"Макрос '{self.name}' выполнен")
            except Exception:
                pass

        self.running = False
        total_duration = (time.time() - start_time) * 1000
        _get_logger().debug(f"[SKILL] Макрос '{self.name}' завершил выполнение за {total_duration:.2f}мс")
        # ✅ Сообщаем диспетчеру об окончании для сброса cast_lock
        if hasattr(self, 'app') and hasattr(self.app, 'dispatcher'):
            self.app.dispatcher.on_macro_finished(self.name)