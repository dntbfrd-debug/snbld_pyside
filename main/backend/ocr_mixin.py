import time
import threading

from PySide6.QtCore import Slot

from backend.logger_manager import get_logger
from constants import OCR_TARGET_INTERVAL

logger = get_logger('ocr')


class OCRMixin:
    def start_ocr(self):
        if self._ocr_running and self.target_reader:
            return
        self._ocr_running = True
        self._ocr_enabled = True
        import constants
        import tesseract_reader
        areas = {
            "mob": self._settings.get("mob_area", constants.DEFAULT_MOB_AREA),
            "player": self._settings.get("player_area", constants.DEFAULT_PLAYER_AREA)
        }
        self.target_reader = tesseract_reader.TargetReader(
            areas,
            interval_per_area=OCR_TARGET_INTERVAL,
            scale=self._settings.get("ocr_scale", 10),
            psm=self._settings.get("ocr_psm", 7),
            use_morph=self._settings.get("ocr_use_morph", True),
            check_window=lambda: self.is_game_window_active(),
        )
        self.target_reader.data_updated.connect(self.on_distance_updated)
        self.target_reader.start()
        logger.info("[OCR] OCR запущен (Tesseract)")

    def stop_ocr(self):
        if self.target_reader:
            try:
                self.target_reader.stop()
            except RuntimeError as e:
                logger.debug(f"[OCR] TargetReader уже удалён: {e}")
            except Exception as e:
                logger.error(f"[OCR] Ошибка остановки OCR: {e}", exc_info=True)
            finally:
                self.target_reader = None
                self._ocr_running = False
        logger.info("[OCR] OCR остановлен")

    @Slot(str)
    def selectOCRArea(self, target_type):
        logger.info(f"selectOCRArea: запуск для {target_type}")
        self._ocr_area_target = target_type
        self.ocrAreaSelectorRequested.emit(target_type)
        self.notification.emit(f"Выберите область для '{target_type}' на экране", "info")

    @Slot()
    def startOCRCalibration(self):
        logger.info("[OCR] Запуск комплексной калибровки OCR")
        self.ocrCalibrationDialogRequested.emit()

    @Slot(str, int, int, int, int)
    def onOCRAreaSelected(self, target_type, x1, y1, x2, y2):
        area = f"{x1},{y1},{x2},{y2}"
        logger.info(f"[OCR] Выбрана область OCR для {target_type}: {area}")
        if target_type == "mob":
            self.set_setting("mob_area", f"{x1},{y1},{x2},{y2}")
        elif target_type == "player":
            self.set_setting("player_area", f"{x1},{y1},{x2},{y2}")
        if self.target_reader and self.target_reader.worker:
            self.target_reader.worker.areas[target_type] = (x1, y1, x2, y2)
        self.ocrAreaSelected.emit(target_type, area)
        self.notification.emit(f"[+] Область для '{target_type}' сохранена: {area}", "success")

    @Slot(str)
    def testOCRArea(self, target_type):
        logger.debug(f"testOCRArea: вызов для {target_type}")
        try:
            from backend.win32_api import IsWindowVisible, GetWindowTextTimeout, EnumWindows, SetForegroundWindow
            window_title = self._settings.get("target_window_title", "")
            if window_title:
                def find_window(hwnd, result):
                    if IsWindowVisible(hwnd):
                        title = GetWindowTextTimeout(hwnd)
                        if title and window_title.lower() in title.lower():
                            result.append(hwnd)
            else:
                def find_window(hwnd, result):
                    if IsWindowVisible(hwnd):
                        title = GetWindowTextTimeout(hwnd)
                        if title:
                            result.append(hwnd)
            hwnds = []
            EnumWindows(lambda h, _: find_window(h, hwnds))
            if hwnds:
                SetForegroundWindow(hwnds[0])
                time.sleep(0.15)
                logger.debug(f"[testOCRArea] Окно активировано: {window_title}")
        except Exception as e:
            logger.debug(f"[testOCRArea] Не удалось активировать окно: {e}")
        import mss
        import numpy as np
        try:
            with mss.mss() as sct:
                mon = sct.monitors[1] if len(sct.monitors) > 1 else sct.monitors[0]
                screenshot = sct.grab(mon)
                screenshot_np = np.array(screenshot)
            if self.target_reader and self.target_reader.worker:
                result = self.target_reader.worker.test_area(screenshot_np, target_type)
            else:
                import tesseract_reader
                from tesseract_reader import TargetWorker
                import constants
                areas = {
                    target_type: self._settings.get(f"{target_type}_area", (0, 0, 0, 0))
                }
                worker = TargetWorker(
                    areas,
                    interval=OCR_TARGET_INTERVAL,
                    scale=self._settings.get("ocr_scale", 10),
                    psm=self._settings.get("ocr_psm", 7),
                    use_morph=self._settings.get("ocr_use_morph", True)
                )
                result = worker.test_area(screenshot_np, target_type)
            logger.info(f"[OCR] Тест OCR для {target_type}: {result}")
            image_source = None
            if result.get("image") is not None:
                import io
                import base64
                from PIL import Image
                img = Image.fromarray(result["image"])
                buffered = io.BytesIO()
                img.save(buffered, format="PNG")
                image_source = "data:image/png;base64," + base64.b64encode(buffered.getvalue()).decode()
            self.ocrTestResult.emit(target_type, {
                "success": result.get("success", False),
                "distance": result.get("distance"),
                "numbers": result.get("numbers", []),
                "image": image_source,
                "area": result.get("area"),
                "engine": "Tesseract"
            })
            if result.get("distance"):
                self.notification.emit(f"Распознано: {result['distance']} м (Tesseract)", "success")
            else:
                self.notification.emit("Не распознано. Попробуйте другую область.", "warning")
        except Exception as e:
            logger.error(f"Ошибка тестирования OCR: {e}", exc_info=True)
            self.notification.emit(f"Ошибка: {e}", "error")

    def on_distance_updated(self, target_type, distance, numbers):
        if distance is not None:
            if 0.5 <= distance <= 200:
                should_emit = False
                with self._distance_lock:
                    if self._target_distance != distance:
                        self._target_distance = distance
                        self._last_ocr_numbers = numbers if numbers is not None else []
                        should_emit = True
                if should_emit:
                    self.distanceUpdated.emit(target_type, distance, self._last_ocr_numbers)
                logger.debug(f"[DIST] {target_type}: {distance:.1f}м")
            else:
                logger.debug(f"[DIST] {target_type}: нереальное {distance:.1f}м - игнорируем")

    def on_ping_updated(self, ping):
        self._ping = ping
        self.pingUpdated.emit(ping)
        self._settings["average_ping"] = ping
        if self._settings.get("use_ping_delays", False):
            self.recalculate_macro_delays()
        if self._settings.get("ping_auto", True):
            self.save_settings()

    @Slot()
    def testPing(self):
        import threads
        logger.info(f"[PING] Ручной тест пинга...")
        self._stop_ping_monitor()
        interval = self._settings.get("ping_check_interval", 5)
        self.ping_monitor = threads.PingMonitor(self._settings.get("process_name", "elementclient.exe"), interval)
        self.ping_monitor.ping_updated.connect(self.on_ping_updated)
        self.ping_monitor.start()
        self.notification.emit("Запуск теста пинга...", "info")

    def _stop_ping_monitor(self):
        if self.ping_monitor:
            try:
                try:
                    self.ping_monitor.ping_updated.disconnect(self.on_ping_updated)
                except (RuntimeError, TypeError):
                    pass
                if self.ping_monitor.isRunning():
                    self.ping_monitor.stop()
                    self.ping_monitor.wait(2000)
                self.ping_monitor.deleteLater()
            except Exception as e:
                logger.error(f"[PING] Ошибка при остановке PingMonitor: {e}", exc_info=True)

    @Slot(result=float)
    def getPingCompensation(self):
        icmp_ping = self._settings.get("average_ping", 30)
        GAME_PING_MULTIPLIER = 2.0
        game_ping = icmp_ping * GAME_PING_MULTIPLIER
        compensation = min(game_ping / 1000.0 * 0.7 + 0.02, 0.3)
        return compensation

    def get_ping_compensation(self):
        icmp_ping = self._settings.get("average_ping", 30)
        GAME_PING_MULTIPLIER = 2.0
        game_ping = icmp_ping * GAME_PING_MULTIPLIER
        return game_ping / 1000.0
