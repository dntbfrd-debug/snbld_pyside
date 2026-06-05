import time
import logging
import os
import sys
import re
import threading
from typing import Optional, Tuple, List, Callable, Dict

import mss
import numpy as np
import cv2
import pytesseract
from PySide6.QtCore import QObject, Signal, QThread, Slot

logging.getLogger('pytesseract').setLevel(logging.WARNING)

from backend.logger_manager import get_logger as _get_logger

def ensure_tesseract():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    search_paths = []
    
    if getattr(sys, 'frozen', False):
        try:
            from utils.file_utils import get_data_dir
            data_dir = get_data_dir()
            search_paths.append(os.path.join(data_dir, 'tesseract'))
        except Exception:
            pass
    
    if getattr(sys, 'frozen', False):
        exe_dir = os.path.dirname(sys.executable)
        search_paths.append(os.path.join(exe_dir, 'tesseract'))
    
    if hasattr(sys, '_MEIPASS'):
        search_paths.append(os.path.join(sys._MEIPASS, 'tesseract'))
    
    search_paths.append(os.path.join(base_dir, 'tesseract'))
    
    search_paths.extend([
        r'C:\Program Files\Tesseract-OCR',
        r'C:\Program Files (x86)\Tesseract-OCR'
    ])
    
    tesseract_root = None
    for path in search_paths:
        if os.path.exists(path) and os.path.isdir(path):
            tesseract_exe = os.path.join(path, 'tesseract.exe')
            if os.path.exists(tesseract_exe):
                tesseract_root = path
                break
    
    if not tesseract_root:
        _get_logger().error("Tesseract не найден ни в одном из путей!", exc_info=True)
        _get_logger().error("Поиск производился в:", exc_info=True)
        for p in search_paths:
            _get_logger().error(f"  - {p}", exc_info=True)
        return
    
    tesseract_exe = os.path.join(tesseract_root, 'tesseract.exe')
    tessdata_dir = os.path.join(tesseract_root, 'tessdata')
    
    pytesseract.pytesseract.tesseract_cmd = tesseract_exe
    os.environ['TESSDATA_PREFIX'] = tessdata_dir
    
    os.environ['PATH'] = tesseract_root + os.pathsep + os.environ['PATH']
    
    _get_logger().info(f" Tesseract найден: {tesseract_exe}")
    _get_logger().info(f" TESSDATA_PREFIX: {tessdata_dir}")
    _get_logger().info(f" Добавлен в PATH: {tesseract_root}")
    
    try:
        version = pytesseract.get_tesseract_version()
        _get_logger().info(f" Tesseract версия: {version}")
    except Exception as e:
        _get_logger().error(f" Ошибка проверки версии Tesseract: {e}", exc_info=True)

class TargetWorker(QObject):
    data_updated = Signal(str, float, list)
    finished = Signal()

    def __init__(self, areas: Dict[str, Tuple[int, int, int, int]],
                  interval: float = 0.2,
                 scale: int = 10,
                 psm: int = 7,
                 use_morph: bool = True,
                 check_window: Callable[[], bool] = None):
        super().__init__()
        self.areas = areas
        self.interval = interval
        self.scale = scale
        self.psm = psm
        self.use_morph = use_morph
        self._running = True
        self._stopped = False
        self.check_window = check_window
        
        self.active_target = "mob"
        self.inactive_target = "player"
        self.empty_attempts = 0
        self.MAX_EMPTY_ATTEMPTS = 10
        self.consecutive_switches = 0
        self.last_switch_time = 0
        self.MIN_SWITCH_INTERVAL = 5.0
        
        self.last_distance = {}
        self.last_success_time = {}
        self.empty_count = {}
        self.distance_history = {}
        
        self.ocr_thread = None

    def _check_active_target(self):
        _get_logger().info(f"[OCR] Поток запущен, активный таргет: {self.active_target}, интервал={self.interval}с")

        with mss.mss() as sct:
            while self._running and not self._stopped:
                try:
                    if self.check_window and not self.check_window():
                        time.sleep(0.1)
                        continue

                    area = self.areas.get(self.active_target)
                    if not area:
                        time.sleep(0.5)
                        continue

                    if isinstance(area, str):
                        area = tuple(int(x.strip()) for x in area.split(','))

                    PADDING = 5
                    monitor = {
                        "left": max(0, int(area[0]) - PADDING),
                        "top": max(0, int(area[1]) - PADDING),
                        "width": int(area[2]) - int(area[0]) + PADDING * 2,
                        "height": int(area[3]) - int(area[1]) + PADDING * 2
                    }
                    img = sct.grab(monitor)
                    img_np = np.array(img)
                    del img

                    if img_np.size == 0:
                        self.empty_attempts += 1
                        _get_logger().debug(f"[OCR] {self.active_target}: пустое изображение ({self.empty_attempts}/{self.MAX_EMPTY_ATTEMPTS})")
                        time.sleep(self.interval)
                        continue

                    processed = self.preprocess_image(img_np)
                    del img_np

                    numbers = self.recognize_numbers(processed)
                    del processed
                    distance = self.numbers_to_distance(numbers, self.active_target)

                    if distance is not None and distance > 0:
                        self.empty_attempts = 0
                        self.consecutive_switches = 0
                        self.last_distance[self.active_target] = distance
                        self.last_success_time[self.active_target] = time.time()
                        _get_logger().debug(f"[OCR] {self.active_target}: {distance:.1f}м (numbers={numbers})")

                        if self._running and not self._stopped:
                            self.data_updated.emit(self.active_target, distance, numbers)
                    else:
                        self.empty_attempts += 1
                        _get_logger().debug(f"[OCR] {self.active_target}: не распознано ({self.empty_attempts}/{self.MAX_EMPTY_ATTEMPTS})")

                        if self.empty_attempts >= self.MAX_EMPTY_ATTEMPTS:
                            now = time.time()
                            if now - self.last_switch_time < self.MIN_SWITCH_INTERVAL:
                                _get_logger().debug(f"[OCR] Защита от частых переключений, ждём")
                                self.empty_attempts = 0
                            elif self.consecutive_switches >= 3:
                                _get_logger().error(f"[OCR] Оба таргета не работают ({self.consecutive_switches} переключений), OCR остановлен", exc_info=True)
                                self._stopped = True
                                break
                            else:
                                _get_logger().info(f"[OCR] {self.empty_attempts} пустых попыток → переключение на {self.inactive_target}")
                                self._switch_target()

                    time.sleep(self.interval)

                except Exception as e:
                    _get_logger().error(f"[OCR] Ошибка: {e}", exc_info=True)
                    time.sleep(0.5)

        _get_logger().info(f"[OCR] Поток остановлен")

    def _switch_target(self):
        import time
        self.last_distance[self.inactive_target] = None
        self.last_success_time[self.inactive_target] = 0

        self.active_target, self.inactive_target = self.inactive_target, self.active_target
        self.empty_attempts = 0
        self.last_switch_time = time.time()
        self.consecutive_switches += 1
        _get_logger().info(f"[OCR] Активный таргет: {self.active_target} (переключений подряд: {self.consecutive_switches})")

    def test_area(self, screenshot_np: np.ndarray, target_type: str) -> dict:
        area = self.areas.get(target_type)
        if not area:
            return {"success": False, "distance": None, "numbers": [], "image": None, "area": None}

        try:
            if isinstance(area, str):
                area = tuple(int(x.strip()) for x in area.split(','))

            x1, y1, x2, y2 = area
            cropped = screenshot_np[y1:y2, x1:x2]

            if cropped.size == 0:
                return {"success": False, "distance": None, "numbers": [], "image": None, "area": area}

            processed = self.preprocess_image(cropped)

            numbers = self.recognize_numbers(processed)
            distance = self.numbers_to_distance(numbers, target_type)

            import cv2
            if len(processed.shape) == 2:
                preview = cv2.cvtColor(processed, cv2.COLOR_GRAY2RGB)
            else:
                preview = cv2.cvtColor(processed, cv2.COLOR_BGRA2RGB)

            return {
                "success": distance is not None and distance > 0,
                "distance": distance,
                "numbers": numbers,
                "image": preview,
                "area": area
            }
        except Exception as e:
            _get_logger().error(f"[OCR] Ошибка test_area для {target_type}: {e}", exc_info=True)
            return {"success": False, "distance": None, "numbers": [], "image": None, "area": area}

    def sync_read(self, target_type: str = "mob") -> Optional[float]:
        area = self.areas.get(target_type)
        if not area:
            return None
        if isinstance(area, str):
            area = tuple(int(x.strip()) for x in area.split(','))
        try:
            with mss.mss() as sct:
                PADDING = 5
                monitor = {
                    "left": max(0, int(area[0]) - PADDING),
                    "top": max(0, int(area[1]) - PADDING),
                    "width": int(area[2]) - int(area[0]) + PADDING * 2,
                    "height": int(area[3]) - int(area[1]) + PADDING * 2
                }
                img = sct.grab(monitor)
                img_np = np.array(img)
            if img_np.size == 0:
                return None
            processed = self._preprocess_fast(img_np)
            numbers = self.recognize_numbers(processed)
            distance = self.numbers_to_distance(numbers, target_type)
            if distance is not None and distance > 0:
                _get_logger().debug(f"[OCR] sync_read {target_type}: {distance:.1f}м")
                return distance
            return None
        except Exception as e:
            _get_logger().error(f"[OCR] sync_read error: {e}", exc_info=True)
            return None

    @staticmethod
    def _preprocess_fast(img: np.ndarray) -> np.ndarray:
        h, w = img.shape[:2]
        scale = 3
        new_w = min(int(w * scale), 600)
        new_h = min(int(h * scale), 150)
        resized = cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_LINEAR)
        gray = cv2.cvtColor(resized, cv2.COLOR_BGRA2GRAY)
        _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        return binary

    def preprocess_image(self, img: np.ndarray) -> np.ndarray:
        h, w = img.shape[:2]

        new_w = int(w * self.scale)
        new_h = int(h * self.scale)

        max_w = 2000
        max_h = 500
        if new_w > max_w:
            ratio = max_w / new_w
            new_w = max_w
            new_h = int(new_h * ratio)
        if new_h > max_h:
            ratio = max_h / new_h
            new_h = max_h
            new_w = int(new_w * ratio)

        resized = cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_CUBIC)

        gray = cv2.cvtColor(resized, cv2.COLOR_BGRA2GRAY)
        del resized

        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(gray)
        del gray

        _, binary = cv2.threshold(enhanced, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        del enhanced

        if self.use_morph:
            kernel = cv2.getStructuringElement(cv2.MORPH_CROSS, (3, 3))
            binary = cv2.erode(binary, kernel, iterations=2)

            del kernel

        return binary

    def recognize_numbers(self, img: np.ndarray) -> List[str]:
        try:
            if self.psm == 10:
                custom_config = f'--psm {self.psm} -c tessedit_char_whitelist=0123456789.'
            else:
                custom_config = f'--psm {self.psm} -c tessedit_char_whitelist=0123456789. -c preserve_interword_spaces=0'

            try:
                text = pytesseract.image_to_string(img, config=custom_config, lang='eng', timeout=2)
            except UnicodeDecodeError as e:
                _get_logger().warning(f"Ошибка кодировки OCR: {e}, пробуем с latin-1", exc_info=True)
                text = pytesseract.image_to_string(img, config=custom_config, lang='eng', timeout=2)
                if isinstance(text, bytes):
                    text = text.decode('latin-1', errors='replace')
            text = text.strip()
            
            if not text or len(text) < 1:
                custom_config_alt = f'--psm 6 -c tessedit_char_whitelist=0123456789.'
                try:
                    text = pytesseract.image_to_string(img, config=custom_config_alt, lang='eng', timeout=2)
                except UnicodeDecodeError as e:
                    _get_logger().warning(f"Ошибка кодировки OCR (alt): {e}, пробуем с latin-1", exc_info=True)
                    text = pytesseract.image_to_string(img, config=custom_config_alt, lang='eng', timeout=2)
                    if isinstance(text, bytes):
                        text = text.decode('latin-1', errors='replace')
                text = text.strip()

            raw_numbers = re.findall(r'\d+\.?\d*', text)

            filtered = []
            for num in raw_numbers:
                if not num:
                    continue
                if num.count('.') > 1:
                    continue
                if '.' in num:
                    parts = num.split('.')
                    if len(parts) == 2 and 1 <= len(parts[0]) <= 2 and len(parts[1]) >= 1:
                        try:
                            val = float(num)
                            if 0 <= val <= 999:
                                normalized = f"{parts[0]}.{parts[1][0]}"
                                filtered.append(normalized)
                        except ValueError:
                            continue
                else:
                    if 1 <= len(num) <= 3:
                        try:
                            val = float(num)
                            if 0 <= val <= 999:
                                filtered.append(num)
                        except ValueError:
                            continue

            if filtered:
                _get_logger().debug(f"[OCR] Распознано: {filtered}")
                return filtered

            if raw_numbers:
                candidate = raw_numbers[0]
                _get_logger().debug(f"[OCR] Сырые числа: {raw_numbers}, пробуем исправить...")
                corrected = self._correct_ocr_errors(candidate)
                if corrected:
                    _get_logger().debug(f"[OCR] Исправлено: {candidate} → {corrected}")
                    return [corrected]
                return raw_numbers

            _get_logger().debug(f"[OCR] Ничего не распознано")
            return []

        except Exception as e:
            _get_logger().error(f"Ошибка распознавания: {e}", exc_info=True)
            return []

    def _correct_ocr_errors(self, text: str) -> str:
        if not text:
            return text

        if text.isdigit():
            val = int(text)
            if 100 <= val <= 299:
                corrected = f"{text[:-1]}.{text[-1]}"
                _get_logger().debug(f"[OCR] Исправление магического диапазона: {text} → {corrected}")
                return corrected

        for target_type in ('mob', 'player'):
            last_dist = self.last_distance.get(target_type)
            if last_dist is not None:
                if len(text) == 2 and text.isdigit():
                    if last_dist < 10:
                        candidate = f"{text[0]}.{text[1]}"
                        cand_val = float(candidate)
                        if abs(cand_val - last_dist) < 30 and 0.5 <= cand_val <= 20:
                            _get_logger().debug(f"[OCR] Восстановлена точка: {text} → {candidate} (было {last_dist:.1f}м)")
                            return candidate
                    elif last_dist >= 10:
                        candidate = f"{text}.0"
                        cand_val = float(candidate)
                        if abs(cand_val - last_dist) < 30 and 0.5 <= cand_val <= 200:
                            _get_logger().debug(f"[OCR] Восстановлена точка: {text} → {candidate} (было {last_dist:.1f}м)")
                            return candidate

        if len(text) == 2 and text.isdigit():
            val = int(text)
            if val <= 50:
                candidate = f"{text[0]}.{text[1]}"
                cand_val = float(candidate)
                if 0.5 <= cand_val <= 20:
                    _get_logger().debug(f"[OCR] Восстановлена точка (эвристика): {text} → {candidate}")
                    return candidate
            else:
                candidate = f"{text}.0"
                cand_val = float(candidate)
                if 0.5 <= cand_val <= 200:
                    _get_logger().debug(f"[OCR] Восстановлена точка (эвристика): {text} → {candidate}")
                    return candidate

        if len(text) == 3 and text.isdigit():
            candidate = f"{text[:2]}.{text[2]}"
            cand_val = float(candidate)
            if 0.5 <= cand_val <= 200:
                _get_logger().debug(f"[OCR] Восстановлена точка: {text} → {candidate}")
                return candidate

        common_corrections = {
            '21.': '27.',
            '29.': '25.',
            '71': '77',
            '17': '77',
            '95': '55',
            '59': '55',
            '39': '35',
            '93': '53',
            '85': '85',
            '58': '55',
            '89': '85',
            '98': '58',
            '30.': '35.',
            '30': '35',
            '82': '8.2',
            '83': '8.3',
            '84': '8.4',
            '86': '8.6',
            '87': '8.7',
            '88': '8.8',
            '27': '2.7',
            '25': '2.5',
            '35': '3.5',
            '45': '4.5',
            '55': '5.5',
            '65': '6.5',
            '75': '7.5',
            '95': '9.5',
            '15': '1.5',
            '05': '0.5',
            '4.': '4.',
            '7.': '7.',
            '1.': '1.',
            '0.': '0.',
            '6.': '6.',
            '8.': '8.',
            '3.': '3.',
            '9.': '9.',
            '2.': '2.',
            '5.': '5.',
        }

        for wrong, correct in common_corrections.items():
            if wrong in text:
                corrected = text.replace(wrong, correct)
                if corrected != text:
                    _get_logger().debug(f"Исправление OCR: {text} → {corrected}")
                    return corrected

        if '.' in text:
            parts = text.split('.')
            if len(parts) == 2:
                if parts[0].isdigit() and parts[1].isdigit():
                    if len(parts[1]) == 1:
                        return text
                    elif len(parts[1]) > 1:
                        return f"{parts[0]}.{parts[1][0]}"

        cleaned = re.sub(r'[^\d.]', '', text)
        if cleaned and cleaned != text:
            _get_logger().debug(f"Очистка OCR: {text} → {cleaned}")
            return cleaned

        return text

    def numbers_to_distance(self, numbers: List[str], target_type: str) -> Optional[float]:
        if not numbers:
            return None

        for num in numbers:
            try:
                new_distance = float(num)
                
                if new_distance < 0.5 or new_distance >= 100:
                    _get_logger().debug(f"[OCR] Отброшен мусор: {new_distance}")
                    continue

                if new_distance >= 100:
                    fixed = new_distance / 10
                    _get_logger().debug(f"[OCR] Автоматическое исправление: {new_distance} → {fixed:.1f}м (потеряна точка)")
                    new_distance = fixed

                self.last_distance[target_type] = new_distance
                self.last_success_time[target_type] = time.time()
                _get_logger().debug(f"[OCR] {target_type}: {new_distance:.1f}м (numbers={numbers})")
                return new_distance
                
            except ValueError:
                continue
        
        last_dist = self.last_distance.get(target_type)

        for num in numbers:
            try:
                cleaned = re.sub(r'[^\d.]', '', num)

                if cleaned and '.' not in cleaned:
                    if len(cleaned) == 3:
                        fixed = f"{cleaned[:2]}.{cleaned[2]}"
                        new_distance = float(fixed)
                        if 0.5 <= new_distance <= 200:
                            _get_logger().debug(f"[OCR] Исправлено: {num} → {fixed}")
                            self.last_distance[target_type] = new_distance
                            self.last_success_time[target_type] = time.time()
                            return new_distance

                    elif len(cleaned) == 2:
                        if last_dist is not None:
                            if last_dist < 10:
                                fixed = f"{cleaned[0]}.{cleaned[1]}"
                                new_distance = float(fixed)
                                if 0.5 <= new_distance <= 20:
                                    _get_logger().debug(f"[OCR] Восстановлена точка: {num} → {fixed} (было {last_dist:.1f}м)")
                                    self.last_distance[target_type] = new_distance
                                    self.last_success_time[target_type] = time.time()
                                    return new_distance
                            elif last_dist >= 10:
                                if last_dist <= 50:
                                    fixed = f"{cleaned}.0"
                                    new_distance = float(fixed)
                                    if 0.5 <= new_distance <= 200:
                                        _get_logger().debug(f"[OCR] Восстановлена точка: {num} → {fixed} (было {last_dist:.1f}м)")
                                        self.last_distance[target_type] = new_distance
                                        self.last_success_time[target_type] = time.time()
                                        return new_distance
                        else:
                            val = int(cleaned)
                            if val <= 50:
                                fixed = f"{cleaned[0]}.{cleaned[1]}"
                                new_distance = float(fixed)
                                if 0.5 <= new_distance <= 20:
                                    _get_logger().debug(f"[OCR] Восстановлена точка (эвристика): {num} → {fixed}")
                                    self.last_distance[target_type] = new_distance
                                    self.last_success_time[target_type] = time.time()
                                    return new_distance
                            else:
                                fixed = f"{cleaned}.0"
                                new_distance = float(fixed)
                                if 0.5 <= new_distance <= 200:
                                    _get_logger().debug(f"[OCR] Восстановлена точка (эвристика): {num} → {fixed}")
                                    self.last_distance[target_type] = new_distance
                                    self.last_success_time[target_type] = time.time()
                                    return new_distance

            except ValueError:
                continue

        return None

    @Slot()
    def start_work(self):
        _get_logger().info(f"[OCR] Запуск: active={self.active_target}, interval={self.interval}с")
        
        if self.ocr_thread is not None and self.ocr_thread.is_alive():
            _get_logger().warning("[OCR] Предыдущий поток OCR всё ещё работает, принудительная остановка")
            self.stop()
        
        self.last_distance.clear()
        self.empty_attempts = 0
        _get_logger().debug("[OCR] Кэш дистанции сброшен")
        
        self._stopped = False
        self._running = True
        
        self.ocr_thread = threading.Thread(
            target=self._check_active_target,
            daemon=True,
            name=f"OCR-{self.active_target}"
        )
        self.ocr_thread.start()
        
        _get_logger().info(f"[OCR] Поток запущен")
        self.finished.emit()

    def stop(self):
        _get_logger().info("[OCR] Остановка...")
        self._stopped = True
        self._running = False
        
        if self.ocr_thread and self.ocr_thread.is_alive():
            try:
                self.ocr_thread.join(timeout=1.0)
                if self.ocr_thread.is_alive():
                    _get_logger().warning("[OCR] Поток не завершился за 1 секунду, оставляем работать как демон")
                else:
                    _get_logger().debug("[OCR] Поток остановлен")
            except Exception as e:
                _get_logger().error(f"[OCR] Ошибка при ожидании завершения потока: {e}", exc_info=True)
        
        
        _get_logger().info("[OCR] Остановлено")
        self.finished.emit()

    def get_active_target(self) -> str:
        return self.active_target

    def get_last_processed(self, target_type: str = None):
        if target_type:
            return self.last_distance.get(target_type)
        return self.last_distance


class TargetReader(QThread):
    data_updated = Signal(str, float, list)

    def __init__(self, areas: Dict[str, Tuple[int, int, int, int]],
                  interval_per_area: float = 0.2,
                 scale: int = 10,
                 psm: int = 7,
                 use_morph: bool = True,
                 parent=None,
                 check_window: Callable[[], bool] = None):
        super().__init__(parent)
        self.worker = TargetWorker(areas, interval_per_area, scale, psm, use_morph, check_window)
        self.worker.data_updated.connect(self._forward_data_updated)
        self.started.connect(self.worker.start_work)
        self.worker.finished.connect(self.quit)

    def _forward_data_updated(self, target_type, distance, numbers):
        self.data_updated.emit(target_type, distance, numbers)

    def run(self):
        try:
            self.worker.start_work()
        except Exception as e:
            _get_logger().error(f"Ошибка в TargetReader.run(): {e}", exc_info=True)
        finally:
            self.worker.finished.emit()

    def stop(self):
        if self.worker:
            try:
                self.worker.stop()
            except RuntimeError:
                pass
            try:
                self.worker.data_updated.disconnect(self._forward_data_updated)
            except (RuntimeError, TypeError):
                pass
        try:
            self.quit()
            self.wait(500)
        except RuntimeError:
            pass
        if self.worker:
            try:
                self.worker.deleteLater()
            except RuntimeError:
                pass
            self.worker = None

    def get_last_processed(self, target_type: str = None):
        if self.worker:
            return self.worker.get_last_processed(target_type)
        return None


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    ensure_tesseract()
    print("Tesseract версия:", pytesseract.get_tesseract_version())
