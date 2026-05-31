import time
import os

from backend.keyboard_shim import hook_key as _hook_key, unhook_key as _unhook_key, unhook_all as _unhook_all
KEYBOARD_AVAILABLE = True

from PySide6.QtCore import Slot

from backend.logger_manager import get_logger

logger = get_logger('window')


class WindowMixin:
    def register_hotkey(self, hotkey, callback, check_window=True, check_global_stop=True, suppress=True):
        if not hotkey or hotkey in self._hotkey_registered:
            logger.warning(f"register_hotkey: hotkey={hotkey} уже зарегистрирован или пустой!")
            return
        try:
            logger.info(f"[REGISTER] Регистрация hotkey '{hotkey}', check_window={check_window}, check_global_stop={check_global_stop}, suppress={suppress}")
            _last_press = {'time': 0}
            DEBOUNCE_MS = 200
            def wrapped_callback(e):
                now = time.time()
                if now - _last_press['time'] < DEBOUNCE_MS / 1000.0:
                    logger.debug(f"[DEBOUNCE] hotkey='{hotkey}' проигнорирован (повтор через {(now - _last_press['time'])*1000:.0f}мс)")
                    return
                _last_press['time'] = now
                logger.debug(f"[WRAPPED] hotkey='{hotkey}' нажата, global_stopped={getattr(self, 'global_stopped', 'N/A')}")
                if check_global_stop and hasattr(self, 'global_stopped') and self.global_stopped:
                    logger.debug(f"[WRAPPED] hotkey='{hotkey}' проигнорирована: global_stopped=True")
                    return
                if check_window and hasattr(self, 'window_locked') and self.window_locked:
                    target = self.target_window_title.strip().lower()
                    if target:
                        try:
                            from backend.win32_api import GetForegroundWindow, GetWindowTextTimeout
                            hwnd = GetForegroundWindow()
                            active_title = GetWindowTextTimeout(hwnd).lower()
                            if target not in active_title:
                                logger.debug(f"Горячая клавиша '{hotkey}' проигнорирована: окно '{active_title}' не активно")
                                return
                        except Exception as e:
                            logger.error(f"Ошибка проверки окна: {e}", exc_info=True)
                logger.debug(f"[WRAPPED] Вызов callback для hotkey='{hotkey}'")
                callback(e)
            _hook_key(hotkey, wrapped_callback, suppress=suppress)
            self._hotkey_registered.add(hotkey)
            logger.info(f"[REGISTER] [+] Горячая клавиша '{hotkey}' зарегистрирована (suppress={suppress})")
        except Exception as e:
            logger.error(f"Ошибка регистрации {hotkey}: {e}", exc_info=True)

    def unregister_hotkey(self, hotkey):
        if hotkey in self._hotkey_registered:
            try:
                _unhook_key(hotkey)
                self._hotkey_registered.discard(hotkey)
                logger.debug(f"Горячая клавиша удалена: {hotkey}")
            except Exception as e:
                logger.error(f"Ошибка удаления {hotkey}: {e}", exc_info=True)

    @Slot(result='QVariant')
    def getWindowList(self):
        try:
            from backend.win32_api import (IsWindowVisible, GetWindowTextTimeout,
                EnumWindows, GetWindowThreadProcessId, get_process_name)
            windows = []
            def enum_callback(hwnd, _):
                try:
                    if IsWindowVisible(hwnd):
                        title = GetWindowTextTimeout(hwnd)
                        if title:
                            windows.append((hwnd, title))
                except Exception as e:
                    logger.error(f"Ошибка получения окна: {e}", exc_info=True)
                return True
            EnumWindows(enum_callback)
            windows.sort(key=lambda x: x[1])
            result = []
            for hwnd, title in windows:
                pid = 0
                process_name = ""
                try:
                    _, pid = GetWindowThreadProcessId(hwnd)
                    pname = get_process_name(pid)
                    if pname:
                        process_name = pname
                except Exception:
                    pass
                result.append({
                    "hwnd": hwnd,
                    "title": title,
                    "pid": pid,
                    "processName": process_name
                })
            logger.debug(f"getWindowList: найдено {len(result)} окон")
            return result
        except Exception as e:
            logger.error(f"getWindowList: ОШИБКА: {e}", exc_info=True)
            return []

    @Slot()
    def selectWindowFromList(self):
        try:
            logger.debug("selectWindowFromList: вызов функции")
            windows = self.getWindowList()
            if not windows:
                self.notification.emit("Нет открытых окон с заголовками", "warning")
                return
            if not self.engine:
                logger.error("selectWindowFromList: engine не доступен", exc_info=True)
                return
            from utils.resource_utils import resource_path
            qml_file = resource_path("qml/WindowSelectorDialog.qml")
            if not qml_file or not os.path.exists(qml_file):
                self.notification.emit("Файл WindowSelectorDialog.qml не найден", "error")
                return
            from PySide6.QtCore import QUrl
            from PySide6.QtQml import QQmlComponent
            component = QQmlComponent(self.engine, QUrl.fromLocalFile(qml_file))
            if component.isReady():
                dialog = component.create()
                if dialog:
                    dialog.loadWindows()
                    dialog.windowSelected.connect(self.onWindowSelected)
                    dialog.dialogCancelled.connect(lambda: logger.debug("WindowSelector: Отменено"))
                    dialog.show()
                    getattr(dialog, 'raise')()
                    dialog.requestActivate()
                    logger.info("WindowSelectorDialog: Отображён")
                else:
                    self.notification.emit("Не удалось создать окно выбора", "error")
            else:
                error_str = component.errorString()
                logger.error(f"WindowSelectorDialog load error: {error_str}", exc_info=True)
                self.notification.emit("Ошибка загрузки WindowSelectorDialog.qml: " + error_str, "error")
        except Exception as e:
            logger.error(f"selectWindowFromList: ОШИБКА: {e}", exc_info=True)
            self.notification.emit(f"Ошибка: {e}", "error")

    def onWindowSelected(self, title):
        logger.info(f"onWindowSelected: выбрано окно '{title}'")
        self.set_target_window(title)
        self.notification.emit(f"Окно выбрано: {title}", "success")

    @Slot(str)
    def set_target_window(self, title):
        try:
            logger.info(f"[WINDOW] ========== set_target_window вызван: {title}")
            self.target_window_title = title
            self.window_locked = True
            if title:
                try:
                    from macros_core import find_window_hwnd, set_game_window_hwnd
                    from backend.input_system import input_system
                    game_hwnd = find_window_hwnd(title)
                    if game_hwnd:
                        set_game_window_hwnd(game_hwnd)
                        input_system.set_target(game_hwnd)
                        logger.info(f"[WINDOW]  HWND установлен: {game_hwnd}, input_system.target_hwnd установлен")
                    else:
                        logger.warning(f"[WINDOW]  hwnd не найден для '{title}'")
                except Exception as e:
                    logger.error(f"[WINDOW] Ошибка установки hwnd: {e}", exc_info=True)
            logger.info(f"[WINDOW] target_window_title={self.target_window_title}, window_locked={self.window_locked}")
            self.notification.emit(f" Окно выбрано: {title}", "success")
            logger.info(f"[WINDOW] Выбрано окно: {title}")
        except Exception as e:
            logger.error(f"Ошибка установки окна: {e}", exc_info=True)
            import traceback
            traceback.print_exc()
            self.notification.emit(f" Ошибка: {e}", "error")

    def register_all_hotkeys(self):
        start_key = self._settings.get("start_all_hotkey", "-")
        stop_key = self._settings.get("stop_all_hotkey", "=")
        if not start_key or start_key.strip() == "":
            start_key = "-"
        if not stop_key or stop_key.strip() == "":
            stop_key = "="
        for hotkey in list(self._hotkey_registered):
            if hotkey not in (start_key, stop_key):
                self.unregister_hotkey(hotkey)
        if start_key:
            self.register_hotkey(start_key, lambda e=None: self.start_all_macros(), check_window=False, check_global_stop=False, suppress=False)
            logger.debug(f"Горячая клавиша ЗАПУСКА '{start_key}' зарегистрирована (check_global_stop=False, suppress=False)")
        if stop_key:
            self.register_hotkey(stop_key, lambda e=None: self.stop_all_macros(), check_window=False, check_global_stop=False, suppress=False)
            logger.debug(f"Горячая клавиша ОСТАНОВКИ '{stop_key}' зарегистрирована (check_global_stop=False, suppress=False)")
        suppress_macros = not self._global_stopped
        for macro in self._macros:
            if macro.hotkey:
                def make_callback(m):
                    def callback(e):
                        event_type = e.event_type if e else 'None'
                        now = time.time()
                        last_start = getattr(m, 'last_start_time', 0)
                        age = now - last_start if last_start > 0 else 999
                        logger.debug(f"Hotkey '{m.hotkey}': running={m.running}, event_type={event_type}, last_start_age={age:.3f}с")
                        if now < self.dispatcher.cast_lock_until:
                            remaining = self.dispatcher.cast_lock_until - now
                            logger.debug(f"[CAST LOCK] Горячая клавиша '{m.hotkey}' ЗАБЛОКИРОВАНА: идёт каст (ост. {remaining:.2f}с)")
                            return
                        if m.running and e is not None and event_type in ('up', 'key up'):
                            if last_start > 0 and age < 0.3:
                                logger.debug(f"Игнорируем быструю остановку '{m.name}' (age={age:.3f}с < 0.3с)")
                                return
                            logger.debug(f"Остановка '{m.name}' (age={age:.3f}с >= 0.3с)")
                            m.stop()
                            return
                        if not m.running:
                            logger.debug(f"Запуск '{m.name}' через диспетчер")
                            if not self.dispatcher.request_macro(m):
                                logger.debug(f" '{m.name}': ЗАБЛОКИРОВАНО диспетчером")
                                return
                        else:
                            logger.debug(f"Остановка '{m.name}' по callback")
                            m.stop()
                    return callback
                callback = make_callback(macro)
                logger.debug(f"Регистрация горячей клавиши '{macro.hotkey}' для макроса '{macro.name}' с suppress={suppress_macros}")
                self.register_hotkey(macro.hotkey, callback, check_window=True, check_global_stop=True, suppress=suppress_macros)

    def unregister_all_hotkeys(self):
        for hotkey in list(self._hotkey_registered):
            self.unregister_hotkey(hotkey)

    def is_game_window_active(self):
        window_title = self._settings.get("target_window_title", "")
        if not window_title:
            return True
        try:
            from backend.win32_api import GetForegroundWindow, GetWindowTextTimeout
            hwnd = GetForegroundWindow()
            if hwnd:
                active_title = GetWindowTextTimeout(hwnd)
                return window_title.lower() in active_title.lower()
        except Exception as e:
            logger.error(f"is_game_window_active: Ошибка: {e}", exc_info=True)
        return False

    def activate_game_window(self):
        window_title = self._settings.get("target_window_title", "")
        if window_title:
            logger.info(f"activate_game_window: Разворачиваем окно '{window_title}'")
            try:
                from backend.win32_api import (IsWindowVisible, GetWindowTextTimeout,
                    EnumWindows, ShowWindow, SetForegroundWindow, SW_RESTORE,
                    GetWindowThreadProcessId, GetCurrentThreadId, AttachThreadInput)
                def enum_callback(hwnd, _):
                    if IsWindowVisible(hwnd):
                        title = GetWindowTextTimeout(hwnd)
                        if window_title.lower() in title.lower():
                            hwnds.append(hwnd)
                    return True
                hwnds = []
                EnumWindows(enum_callback)
                if hwnds:
                    hwnd = hwnds[0]
                    ShowWindow(hwnd, SW_RESTORE)
                    target_tid = GetWindowThreadProcessId(hwnd)[0]
                    current_tid = GetCurrentThreadId()
                    if current_tid != target_tid:
                        AttachThreadInput(current_tid, target_tid, True)
                    try:
                        SetForegroundWindow(hwnd)
                    finally:
                        if current_tid != target_tid:
                            AttachThreadInput(current_tid, target_tid, False)
                    logger.info(f"activate_game_window: Окно развёрнуто")
                else:
                    logger.warning(f"activate_game_window: Окно '{window_title}' не найдено")
            except Exception as e:
                logger.error(f"activate_game_window: ОШИБКА: {e}", exc_info=True)
        else:
            logger.info("activate_game_window: Окно игры не задано в настройках")

    @Slot()
    def minimizeWindow(self):
        self.minimizeRequested.emit()
        logger.debug("minimizeWindow: запрос на сворачивание отправлен")

    @Slot()
    def closeWindow(self):
        logger.info("closeWindow: запрос на закрытие программы")
        self.closeRequested.emit()
