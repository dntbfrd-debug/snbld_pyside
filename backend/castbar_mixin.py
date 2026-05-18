import time
import os
import threading
import logging

from PySide6.QtCore import Slot, QObject

from backend.logger_manager import get_logger

logger = get_logger('castbar')

try:
    from low_level_hook import MouseHookManager
    LOW_LEVEL_HOOK_AVAILABLE = True
except Exception:
    LOW_LEVEL_HOOK_AVAILABLE = False


class CastbarMixin:
    _castbar_dialog_ref = None
    _mouse_hook_manager = None
    _calibration_active = False
    _buff_calibration_dialog_ref = None
    _castbar_calibration_point = ""
    _castbar_calibration_color = ""
    _castbar_cache = {'visible': False, 'timestamp': 0}
    _castbar_cache_lock = threading.Lock()

    @Slot()
    def selectCastbarPoint(self):
        logger.debug("selectCastbarPoint: вызов")
        from utils.resource_utils import resource_path
        qml_file = resource_path("qml/AreaSelector.qml")
        if not qml_file or not os.path.exists(qml_file):
            self.notification.emit("Файл AreaSelector.qml не найден", "error")
            return
        from PySide6.QtCore import QUrl
        from PySide6.QtQml import QQmlComponent
        component = QQmlComponent(self.engine, QUrl.fromLocalFile(qml_file))
        if component.isReady():
            window = component.create()
            if window:
                window.setProperty("targetType", "castbar")
                window.areaSelected.connect(lambda x1, y1, x2, y2: self.onCastbarPointSelected(x1, y1, x2, y2))
                window.cancelled.connect(lambda: self.notification.emit("Выбор точки отменён", "info"))
                window.show()
                logger.info("AreaSelector показан для выбора точки кастбара")
            else:
                self.notification.emit("Не удалось создать окно выбора точки", "error")
        else:
            error_str = component.errorString()
            logger.error(f"AreaSelector load error: {error_str}", exc_info=True)
            self.notification.emit("Ошибка загрузки AreaSelector.qml: " + error_str, "error")

    @Slot(result=str)
    def getCursorPosition(self):
        from backend.win32_api import GetCursorPos
        pos = GetCursorPos()
        logger.debug(f"getCursorPosition: ({pos[0]}, {pos[1]})")
        return f"{pos[0]},{pos[1]}"

    def _capture_pixel_mss(self, x, y, size=1):
        """Захват цвета пикселя через mss (DXGI) — работает на Windows 7-11, включая GPU-ускоренные окна"""
        try:
            import mss
            import numpy as np
            with mss.mss() as sct:
                half = size // 2
                monitor = {
                    "left": max(0, int(x) - half),
                    "top": max(0, int(y) - half),
                    "width": size,
                    "height": size,
                }
                img = sct.grab(monitor)
                img_np = np.array(img)
                if img_np.size == 0:
                    return None
                # Средний цвет пикселей области
                avg_r = int(np.mean(img_np[:, :, 2]))
                avg_g = int(np.mean(img_np[:, :, 1]))
                avg_b = int(np.mean(img_np[:, :, 0]))
                return (avg_r, avg_g, avg_b)
        except Exception:
            return None

    @Slot(int, int, int, result=str)
    def captureCastbarColorAt(self, x, y, size=1):
        try:
            logger.debug(f"captureCastbarColorAt: ({x}, {y}), size={size}")

            # Способ 1: mss (DXGI) — работает на всех версиях Windows
            rgb = self._capture_pixel_mss(x, y, size)
            if rgb is not None:
                r, g, b = rgb
                logger.debug(f"[CASTBAR] Захвачен цвет (mss): RGB({r},{g},{b}) в точке ({x},{y})")
                return f"{r},{g},{b}"

            # Способ 2: GetPixel (GDI fallback для обычных окон)
            from backend.win32_api import GetWindowDC, GetPixel, ReleaseDC, CLR_INVALID
            hdc = GetWindowDC(0)
            if hdc == 0:
                logger.error("GetWindowDC вернул 0 (недостаточно ресурсов GDI)", exc_info=True)
                return "0,0,0"
            color = GetPixel(hdc, x, y)
            ReleaseDC(0, hdc)
            if color != CLR_INVALID:
                r = color & 0xFF
                g = (color >> 8) & 0xFF
                b = (color >> 16) & 0xFF
                color_str = f"{r},{g},{b}"
                logger.debug(f"[CASTBAR] Захвачен цвет (GDI): RGB({color_str}) в точке ({x},{y})")
                return color_str
            return "0,0,0"
        except Exception as e:
            logger.error(f"Ошибка захвата цвета: {e}", exc_info=True)
            return "0,0,0"

    @Slot(str, int, result=str)
    def captureCastbarColor(self, point_str, size=5):
        try:
            x, y = map(int, point_str.split(','))
            return self.captureCastbarColorAt(x, y, size)
        except Exception as e:
            logger.error(f"Ошибка парсинга координат: {e}", exc_info=True)
            return "0,0,0"

    @Slot()
    def registerCastbarHotkey(self):
        try:
            from backend.keyboard_shim import add_hotkey
            add_hotkey('ctrl+a', self._onCastbarHotkey, suppress=True)
            logger.debug("registerCastbarHotkey: Ctrl+A зарегистрирована")
        except Exception as e:
            logger.error(f"Ошибка регистрации горячей клавиши: {e}", exc_info=True)

    @Slot()
    def unregisterCastbarCtrlAHotkey(self):
        try:
            from backend.keyboard_shim import remove_hotkey
            remove_hotkey('ctrl+a')
            logger.debug("unregisterCastbarCtrlAHotkey: Ctrl+A удалена")
        except Exception as e:
            logger.error(f"Ошибка отмены регистрации горячей клавиши: {e}", exc_info=True)

    @Slot()
    def startBuffCalibration(self):
        logger.info("[BUFF] Запуск калибровки точки клика для баффа")
        self.buffCalibrationDialogRequested.emit()

    @Slot(str)
    def onBuffPointCaptured(self, point):
        logger.info(f"[BUFF] Точка клика захвачена: {point}")
        self.set_setting("buff_8004_click_point", point)
        self.buffCalibrationCompleted.emit(point)
        self.notification.emit(f"Точка клика сохранена: {point}", "success")

    @Slot(result=str)
    def getBuffClickPoint(self):
        return self._settings.get("buff_8004_click_point", "0,0")

    @Slot()
    def performBuffClick(self):
        point_str = self._settings.get("buff_8004_click_point", "0,0")
        if point_str == "0,0":
            logger.warning("[BUFF] Точка клика не настроена, пропускаю")
            return
        try:
            parts = point_str.split(",")
            if len(parts) != 2:
                logger.error(f"[BUFF] Неверный формат точки: {point_str}", exc_info=True)
                return
            x, y = int(parts[0]), int(parts[1])
            logger.info(f"[BUFF] Выполняю клик в точке ({x}, {y})")
            from macros_core import click_at_position
            click_at_position(x, y)
            logger.info(f"[BUFF] Клик выполнен в ({x}, {y})")
        except Exception as e:
            logger.error(f"[BUFF] Ошибка выполнения клика: {e}", exc_info=True)

    @Slot()
    def startCastbarCalibration(self):
        logger.info("=" * 60)
        logger.info("startCastbarCalibration: ЗАПУСК")
        logger.info("=" * 60)
        if not LOW_LEVEL_HOOK_AVAILABLE:
            logger.error("startCastbarCalibration: low_level_hook НЕ доступен!", exc_info=True)
            return
        self.activate_game_window()
        self._calibration_active = True
        try:
            def on_left_click():
                logger.info("=" * 30)
                logger.info("on_left_click: ЛКМ нажата!")
                if self._calibration_active:
                    logger.info("on_left_click: Калибровка активна, захват цвета...")
                    self._onCastbarHotkey()
                    return True
                logger.info("on_left_click: Калибровка НЕ активна, пропускаем клик")
                return False
            logger.info("startCastbarCalibration: Создание MouseHookManager...")
            self._mouse_hook_manager = MouseHookManager(on_left_click)
            logger.info("startCastbarCalibration: Запуск hook...")
            self._mouse_hook_manager.start()
            logger.info("startCastbarCalibration: MouseHookManager запущен УСПЕШНО")
        except Exception as e:
            logger.error(f"startCastbarCalibration: ОШИБКА: {e}", exc_info=True)

    @Slot(QObject)
    def registerCastbarHotkeyForDialog(self, dialog):
        logger.info(f"registerCastbarHotkeyForDialog: dialog = {dialog}")
        self._castbar_dialog_ref = dialog
        self.startCastbarCalibration()

    @Slot()
    def stopCastbarCalibration(self):
        logger.info("stopCastbarCalibration: ВЫЗОВ")
        self._calibration_active = False
        if self._mouse_hook_manager:
            try:
                self._mouse_hook_manager.stop()
                self._mouse_hook_manager = None
                logger.info("stopCastbarCalibration: MouseHookManager остановлен")
            except Exception as e:
                logger.error(f"stopCastbarCalibration: ОШИБКА: {e}", exc_info=True)

    @Slot()
    def unregisterCastbarHotkey(self):
        self.stopCastbarCalibration()

    def _onCastbarHotkey(self):
        try:
            logger.info("[CASTBAR] Захват цвета кастбара")
            if not self._castbar_dialog_ref:
                logger.error("[CASTBAR] _castbar_dialog_ref = None!", exc_info=True)
                return
            from backend.win32_api import GetCursorPos
            try:
                pos = GetCursorPos()
            except Exception as e:
                logger.error(f"[CASTBAR] Ошибка GetCursorPos: {e}", exc_info=True)
                return
            x, y = pos[0], pos[1]
            logger.info(f"[CASTBAR] Позиция курсора: ({x}, {y})")
            color_str = self.captureCastbarColorAt(x, y, 5)
            logger.info(f"[CASTBAR] Захвачен цвет: RGB({color_str})")
            self._castbar_calibration_point = f"{x},{y}"
            self._castbar_calibration_color = color_str
            self._calibration_active = False
            if self._mouse_hook_manager:
                try:
                    self._mouse_hook_manager.stop()
                    logger.info("[CASTBAR] MouseHookManager остановлен после захвата")
                except Exception as e:
                    logger.error(f"[CASTBAR] Ошибка остановки hook: {e}", exc_info=True)
                self._mouse_hook_manager = None
            self.castbarColorCaptured.emit(f"{x},{y}", color_str)
            logger.info("[CASTBAR] Калибровка завершена, сигнал отправлен в QML")
        except Exception as e:
            logger.error(f"[CASTBAR] Ошибка захвата цвета: {e}", exc_info=True)
            self._castbar_calibration_color = "0,0,0"

    @Slot(result=str)
    def getCastbarCalibrationPoint(self):
        return self._castbar_calibration_point

    @Slot(result=str)
    def getCastbarCalibrationColor(self):
        return self._castbar_calibration_color

    @Slot(result=str)
    def getCurrentCastbarColor(self):
        try:
            color = self._settings.get("castbar_color", [94, 123, 104])
            if isinstance(color, list) and len(color) >= 3:
                return f"{int(color[0])},{int(color[1])},{int(color[2])}"
            return "94,123,104"
        except Exception as e:
            logger.error(f"Ошибка получения цвета кастбара: {e}", exc_info=True)
            return "94,123,104"

    def onCastbarPointSelected(self, x1, y1, x2, y2):
        cx = (x1 + x2) // 2
        cy = (y1 + y2) // 2
        point = f"{cx},{cy}"
        logger.info(f"[CASTBAR] Выбрана точка проверки: {point}")
        self.set_setting("castbar_point", point)
        self.notification.emit(f"Точка кастбара: {cx},{cy}", "success")

    def is_castbar_visible(self):
        if not self.castbar_enabled:
            return False
        with self._castbar_cache_lock:
            age = time.time() - self._castbar_cache['timestamp']
            if age < 0.010:
                return self._castbar_cache['visible']
        return self._check_castbar_direct()

    def _check_castbar_direct(self):
        try:
            logger.debug(f"[CASTBAR DEBUG] _check_castbar_direct: castbar_point='{self.castbar_point}', color={self.castbar_color}")
            x, y = map(int, self.castbar_point.split(','))
            logger.debug(f"[CASTBAR DEBUG] Parsed coordinates: x={x}, y={y}")
            import mss
            with mss.mss() as sct:
                left = max(0, int(x) - 2)
                top = max(0, int(y) - 2)
                width = 5
                height = 5
                monitor = {"left": left, "top": top, "width": width, "height": height}
                screenshot = sct.grab(monitor)
                target_r = self.castbar_color[0]
                target_g = self.castbar_color[1]
                target_b = self.castbar_color[2]
                threshold = self.castbar_threshold
                match_count = 0
                total_pixels = width * height
                best_diff = float('inf')
                for dy in range(height):
                    for dx in range(width):
                        idx = (dy * width + dx) * 3
                        r = screenshot.rgb[idx]
                        g = screenshot.rgb[idx + 1]
                        b = screenshot.rgb[idx + 2]
                        diff = abs(r - target_r) + abs(g - target_g) + abs(b - target_b)
                        if diff < best_diff:
                            best_diff = diff
                        if diff <= threshold:
                            match_count += 1
                match_ratio = match_count / total_pixels if total_pixels > 0 else 0
                is_visible = (match_ratio >= 0.3) or (best_diff <= threshold // 2)
                if not is_visible and best_diff < threshold * 2:
                    logger.debug(
                        f"[CASTBAR] Почти: точка=({x},{y}), match={match_count}/{total_pixels} ({match_ratio:.0%}), "
                        f"best_diff={best_diff}, порог={threshold}, match_ratio={match_ratio:.0%}"
                    )
                with self._castbar_cache_lock:
                    self._castbar_cache['visible'] = is_visible
                    self._castbar_cache['timestamp'] = time.time()
                return is_visible
        except Exception as e:
            logger.error(f"[CASTBAR] Ошибка проверки: {e}", exc_info=True)
            return False

    def apply_buff(self, buff_id, name, duration, channeling_bonus, icon):
        with self.buff_lock:
            self.active_buffs[buff_id] = {
                "name": name,
                "end_time": time.time() + duration,
                "bonus": channeling_bonus,
                "icon": icon
            }
        self.activeBuffsUpdated.emit()

    def _on_buff_expired(self, buff_id):
        logger.info(f"[BUFF] Бафф {buff_id} истёк, удалён")
        self.activeBuffsUpdated.emit()

    def get_active_buffs_snapshot(self):
        with self.buff_lock:
            return dict(self.active_buffs)

    def get_current_channeling_bonus(self):
        bonus = self._settings.get("base_channeling", 0)
        with self.buff_lock:
            for buff in self.active_buffs.values():
                bonus += buff["bonus"]
        return bonus

    def get_actual_cast_time(self, base_cast_time):
        bonus_total = self.get_current_channeling_bonus()
        if bonus_total > 0:
            actual = base_cast_time * 100.0 / (100.0 + bonus_total)
            logger.debug(f"[CAST_TIME] base={base_cast_time:.2f}с, bonus={bonus_total}%, actual={actual:.2f}с")
            return actual
        return base_cast_time

    def lock_cast(self, duration):
        self.dispatcher.cast_lock_until = time.time() + duration
        logger.debug(f"[LOCK_CAST] Блокировка установлена: cast_lock_until={self.dispatcher.cast_lock_until:.3f}, now={time.time():.3f}, duration={duration:.2f}с")

    def is_cast_locked(self):
        now = time.time()
        locked = now < self.dispatcher.cast_lock_until
        remaining = self.dispatcher.cast_lock_until - now if locked else 0
        logger.debug(f"[IS_CAST_LOCKED] cast_lock_until={self.dispatcher.cast_lock_until:.3f}, now={now:.3f}, locked={locked}, remaining={remaining:.2f}с")
        return locked
