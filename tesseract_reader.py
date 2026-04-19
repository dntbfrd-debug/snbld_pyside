# tesseract_reader.py
import time
import logging
import os
import sys
import shutil
import re
import threading
from typing import Optional, Tuple, List, Callable, Dict, Any
from collections import deque  # ← ДОБАВЛЕНО: для эффективной истории

import mss
import numpy as np
import cv2
import pytesseract
from PySide6.QtCore import QObject, Signal, QThread, Slot

# Отключаем логи pytesseract
logging.getLogger('pytesseract').setLevel(logging.WARNING)

# Отложенный импорт логгера для избежания циклической зависимости
_logger = None

def _get_logger():
    global _logger
    if _logger is None:
        from backend.logger_manager import get_logger
        _logger = get_logger('ocr')
    return _logger

# ==================== НАСТРОЙКА TESSERACT ====================
def ensure_tesseract():
    """
    Копирует Tesseract из временной папки PyInstaller в папку рядом с exe
    (или в папку проекта при разработке) и настраивает pytesseract.
    Также устанавливает TESSDATA_PREFIX для корректного поиска tessdata.
    """
    if getattr(sys, 'frozen', False):
        base_dir = os.path.dirname(sys.executable)
        dest = os.path.join(base_dir, 'tesseract')
        src = os.path.join(sys._MEIPASS, 'tesseract')
    else:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        dest = os.path.join(base_dir, 'tesseract')
        src = dest

    if not os.path.exists(dest) and os.path.exists(src):
        try:
            shutil.copytree(src, dest)
            _get_logger().info(f"Tesseract скопирован в {dest}")
        except Exception as e:
            _get_logger().error(f"Ошибка копирования Tesseract: {e}")
            dest = src

    # Устанавливаем TESSDATA_PREFIX для корректного поиска tessdata
    tessdata_dir = os.path.join(dest, 'tessdata')
    if os.path.exists(tessdata_dir):
        os.environ['TESSDATA_PREFIX'] = tessdata_dir
        _get_logger().info(f"TESSDATA_PREFIX установлен: {tessdata_dir}")
    else:
        _get_logger().warning(f"tessdata не найден в {tessdata_dir}")

    tesseract_exe = os.path.join(dest, 'tesseract.exe')
    if os.path.exists(tesseract_exe):
        pytesseract.pytesseract.tesseract_cmd = tesseract_exe
        _get_logger().info(f"Tesseract найден: {tesseract_exe}")
    else:
        possible_paths = [
            r'C:\Program Files\Tesseract-OCR\tesseract.exe',
            r'C:\Program Files (x86)\Tesseract-OCR\tesseract.exe'
        ]
        for path in possible_paths:
            if os.path.exists(path):
                pytesseract.pytesseract.tesseract_cmd = path
                _get_logger().info(f"Tesseract найден (системный): {path}")
                # Также устанавливаем TESSDATA_PREFIX для системного tesseract
                tessdata_sys = os.path.join(os.path.dirname(path), 'tessdata')
                if os.path.exists(tessdata_sys):
                    os.environ['TESSDATA_PREFIX'] = tessdata_sys
                    _get_logger().info(f"TESSDATA_PREFIX (системный) установлен: {tessdata_sys}")
                return
        _get_logger().error("Tesseract не найден! OCR будет недоступен.")

# ==================== WORKER ДЛЯ OCR (ОДИН АКТИВНЫЙ РИДЕР) ====================
class TargetWorker(QObject):
    """
    OCR worker с ОДНИМ активным ридером.
    Переключение между mob/player при 10 пустых попытках.
    """
    data_updated = Signal(str, float, list)  # target_type, distance, numbers
    finished = Signal()

    def __init__(self, areas: Dict[str, Tuple[int, int, int, int]],
                 interval: float = 0.1,  # Увеличил частоту: 10 раз в секунду
                 scale: int = 10,
                 psm: int = 7,
                 use_morph: bool = True,
                 check_window: Callable[[], bool] = None,
                 activate_window_title: str = None,
                 skip_activate_window: bool = False):
        super().__init__()
        self.areas = areas
        self.interval = interval
        self.scale = scale
        self.psm = psm
        self.use_morph = use_morph
        self._running = True
        self._stopped = False
        self.check_window = check_window
        
        # ОДИН активный ридер
        self.active_target = "mob"  # Активный таргет
        self.inactive_target = "player"  # Неактивный
        self.empty_attempts = 0  # Счётчик пустых попыток
        self.MAX_EMPTY_ATTEMPTS = 10  # Переключение после 10 пустых попыток (2 сек при interval=0.2)
        self.consecutive_switches = 0  # Счётчик последовательных переключений (защита от бесконечного цикла)
        self.last_switch_time = 0  # Время последнего переключения
        self.MIN_SWITCH_INTERVAL = 5.0  # Минимальный интервал между переключениями (сек)
        
        # Данные для обоих таргетов
        self.last_distance = {}
        self.last_success_time = {}
        self.empty_count = {}
        self.distance_history = {}
        
        # Поток
        self.ocr_thread = None

    def _check_active_target(self):
        """
        Проверка АКТИВНОГО таргета в цикле.
        Переключение при 10 пустых попытках.
        """
        _get_logger().info(f"[OCR] Поток запущен, активный таргет: {self.active_target}, интервал={self.interval}с")

        # Создаём один экземпляр mss на весь цикл (экономия ресурсов)
        with mss.mss() as sct:
            while self._running and not self._stopped:
                try:
                    # Проверка активного окна
                    if self.check_window and not self.check_window():
                        time.sleep(0.5)
                        continue

                    # Распознавание АКТИВНОГО таргета
                    area = self.areas.get(self.active_target)
                    if not area:
                        time.sleep(0.5)
                        continue

                    # Преобразование области из строки в кортеж
                    if isinstance(area, str):
                        area = tuple(int(x.strip()) for x in area.split(','))

                    # Захват изображения С ОТСТУПАМИ (padding) чтобы цифры не обрезались
                    # Tesseract часто теряет крайние символы если они на границе
                    PADDING = 5  # пиксели отступа с каждой стороны
                    monitor = {
                        "left": max(0, int(area[0]) - PADDING),
                        "top": max(0, int(area[1]) - PADDING),
                        "width": int(area[2]) - int(area[0]) + PADDING * 2,
                        "height": int(area[3]) - int(area[1]) + PADDING * 2
                    }
                    img = sct.grab(monitor)
                    img_np = np.array(img)

                    if img_np.size == 0:
                        self.empty_attempts += 1
                        _get_logger().debug(f"[OCR] {self.active_target}: пустое изображение ({self.empty_attempts}/{self.MAX_EMPTY_ATTEMPTS})")
                        time.sleep(self.interval)
                        continue

                    # Предобработка
                    processed = self.preprocess_image(img_np)

                    # Распознавание
                    numbers = self.recognize_numbers(processed)
                    distance = self.numbers_to_distance(numbers, self.active_target)

                    # Обработка результата
                    if distance is not None and distance > 0:
                        # Успех - сброс счётчика
                        self.empty_attempts = 0
                        self.consecutive_switches = 0  # Успешное распознавание — сброс счётчика переключений
                        self.last_distance[self.active_target] = distance
                        self.last_success_time[self.active_target] = time.time()
                        _get_logger().debug(f"[OCR] {self.active_target}: {distance:.1f}м (numbers={numbers})")

                        # Отправляем в backend
                        if self._running and not self._stopped:
                            self.data_updated.emit(self.active_target, distance, numbers)
                    else:
                        # Не распознано
                        self.empty_attempts += 1
                        _get_logger().debug(f"[OCR] {self.active_target}: не распознано ({self.empty_attempts}/{self.MAX_EMPTY_ATTEMPTS})")

                        # Переключение после N пустых попыток с защитой от бесконечного цикла
                        if self.empty_attempts >= self.MAX_EMPTY_ATTEMPTS:
                            now = time.time()
                            if now - self.last_switch_time < self.MIN_SWITCH_INTERVAL:
                                # Слишком частые переключения — просто сбрасываем счётчик
                                _get_logger().debug(f"[OCR] Защита от частых переключений, ждём")
                                self.empty_attempts = 0
                            elif self.consecutive_switches >= 3:
                                # Оба таргета не работают — останавливаем OCR
                                _get_logger().error(f"[OCR] Оба таргета не работают ({self.consecutive_switches} переключений), OCR остановлен")
                                self._stopped = True
                                break
                            else:
                                _get_logger().info(f"[OCR] {self.empty_attempts} пустых попыток → переключение на {self.inactive_target}")
                                self._switch_target()

                    # Пауза перед следующей проверкой
                    time.sleep(self.interval)

                except Exception as e:
                    _get_logger().error(f"[OCR] Ошибка: {e}", exc_info=True)
                    time.sleep(0.5)

        _get_logger().info(f"[OCR] Поток остановлен")

    def _switch_target(self):
        """Переключение на другой таргет"""
        import time
        # СБРОС last_distance неактивного ридера!
        self.last_distance[self.active_target] = None
        self.last_success_time[self.active_target] = 0

        self.active_target, self.inactive_target = self.inactive_target, self.active_target
        self.empty_attempts = 0
        self.last_switch_time = time.time()
        self.consecutive_switches += 1
        _get_logger().info(f"[OCR] Активный таргет: {self.active_target} (переключений подряд: {self.consecutive_switches})")

    def test_area(self, screenshot_np: np.ndarray, target_type: str) -> dict:
        """
        Тестирование области OCR без запуска потока.
        Возвращает dict: {success, distance, numbers, image, area}
        """
        area = self.areas.get(target_type)
        if not area:
            return {"success": False, "distance": None, "numbers": [], "image": None, "area": None}

        try:
            # Преобразование области
            if isinstance(area, str):
                area = tuple(int(x.strip()) for x in area.split(','))

            # Вырезаем область из скриншота
            x1, y1, x2, y2 = area
            cropped = screenshot_np[y1:y2, x1:x2]

            if cropped.size == 0:
                return {"success": False, "distance": None, "numbers": [], "image": None, "area": area}

            # Предобработка
            processed = self.preprocess_image(cropped)

            # Распознавание
            numbers = self.recognize_numbers(processed)
            distance = self.numbers_to_distance(numbers, target_type)

            # Конвертируем processed в RGB для передачи в QML
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
            _get_logger().error(f"[OCR] Ошибка test_area для {target_type}: {e}")
            return {"success": False, "distance": None, "numbers": [], "image": None, "area": area}

    def preprocess_image(self, img: np.ndarray) -> np.ndarray:
        """
        Предобработка изображения для OCR.
        Уменьшение толщины цифр для предотвращения склеивания.
        """
        h, w = img.shape[:2]

        # Увеличение изображения в self.scale раз
        new_w = int(w * self.scale)
        new_h = int(h * self.scale)

        # Ограничиваем максимальные размеры для производительности
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

        # INTER_CUBIC для лучшего качества текста
        resized = cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_CUBIC)

        # Конвертация в оттенки серого
        gray = cv2.cvtColor(resized, cv2.COLOR_BGRA2GRAY)

        # Увеличение контраста через CLAHE (адаптивная эквализация гистограммы)
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(gray)

        # Бинаризация с порогом OTSU
        _, binary = cv2.threshold(enhanced, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

        # Морфологическая обработка - ЭРОЗИЯ для уменьшения толщины цифр
        if self.use_morph:
            # Эрозия для РАЗДЕЛЕНИЯ слипшихся цифр
            # Используем крестообразное ядро для эрозии со всех сторон
            kernel = cv2.getStructuringElement(cv2.MORPH_CROSS, (3, 3))
            binary = cv2.erode(binary, kernel, iterations=1)  # Одна итерация

            # Лёгкое закрытие для удаления мелких точек шума
            kernel_close = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
            binary = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel_close)

        return binary

    def recognize_numbers(self, img: np.ndarray) -> List[str]:
        """
        Распознавание чисел на изображении.
        Улучшенная постобработка для фильтрации мусора и исправления ошибок.
        """
        try:
            # PSM 10 = один символ, PSM 7 = один текст
            if self.psm == 10:
                # Для одного символа используем более простой конфиг
                custom_config = f'--psm {self.psm} -c tessedit_char_whitelist=0123456789.'
            else:
                # PSM 7 - используем более точный режим
                custom_config = f'--psm {self.psm} -c tessedit_char_whitelist=0123456789. -c preserve_interword_spaces=0'

            # Пробуем распознать с основными настройками
            try:
                text = pytesseract.image_to_string(img, config=custom_config, lang='eng', timeout=2)
            except UnicodeDecodeError as e:
                _get_logger().warning(f"Ошибка кодировки OCR: {e}, пробуем с latin-1")
                text = pytesseract.image_to_string(img, config=custom_config, lang='eng', timeout=2)
                if isinstance(text, bytes):
                    text = text.decode('latin-1', errors='replace')
            text = text.strip()
            
            # Если ничего не нашли - пробуем с PSM 6 (uniform block of text)
            if not text or len(text) < 1:
                custom_config_alt = f'--psm 6 -c tessedit_char_whitelist=0123456789.'
                try:
                    text = pytesseract.image_to_string(img, config=custom_config_alt, lang='eng', timeout=2)
                except UnicodeDecodeError as e:
                    _get_logger().warning(f"Ошибка кодировки OCR (alt): {e}, пробуем с latin-1")
                    text = pytesseract.image_to_string(img, config=custom_config_alt, lang='eng', timeout=2)
                    if isinstance(text, bytes):
                        text = text.decode('latin-1', errors='replace')
                text = text.strip()

            # Извлекаем все числа из текста
            raw_numbers = re.findall(r'\d+\.?\d*', text)

            # Фильтрация результатов
            filtered = []
            for num in raw_numbers:
                # Пропускаем пустые
                if not num:
                    continue
                # Пропускаем числа с несколькими точками
                if num.count('.') > 1:
                    continue
                # Для чисел с точкой - проверяем формат XX.Y (2 цифры в целой, 1 в дробной)
                if '.' in num:
                    parts = num.split('.')
                    # Должно быть XX.Y где X - 1-2 цифры, Y - 1 цифра
                    if len(parts) == 2 and 1 <= len(parts[0]) <= 2 and len(parts[1]) >= 1:
                        try:
                            val = float(num)
                            # Проверяем реалистичность для дистанции (0-999м)
                            if 0 <= val <= 999:
                                # Нормализуем до формата X.Y или XX.Y (одна цифра после точки)
                                normalized = f"{parts[0]}.{parts[1][0]}"
                                filtered.append(normalized)
                        except ValueError:
                            continue
                else:
                    # Для чисел без точки - проверяем длину (1-3 цифры)
                    if 1 <= len(num) <= 3:
                        try:
                            val = float(num)
                            if 0 <= val <= 999:
                                filtered.append(num)
                        except ValueError:
                            continue

            # Если нашли валидные числа - возвращаем
            if filtered:
                _get_logger().debug(f"[OCR] Распознано: {filtered}")
                return filtered

            # Если ничего не нашли - пробуем исправить ошибки в raw_numbers
            if raw_numbers:
                candidate = raw_numbers[0]
                _get_logger().debug(f"[OCR] Сырые числа: {raw_numbers}, пробуем исправить...")
                corrected = self._correct_ocr_errors(candidate)
                if corrected:
                    _get_logger().debug(f"[OCR] Исправлено: {candidate} → {corrected}")
                    return [corrected]
                # Возвращаем оригинал если исправление не помогло
                return raw_numbers

            _get_logger().debug(f"[OCR] Ничего не распознано")
            return []

        except Exception as e:
            _get_logger().error(f"Ошибка распознавания: {e}")
            return []

    def _correct_ocr_errors(self, text: str) -> str:
        """
        Исправляет типичные ошибки OCR для цифр.
        2↔7, 5↔9, 1↔7 и т.д.
        А также восстанавливает потерянную точку (83 → 8.3).
        """
        if not text:
            return text

        # === ШАГ 1: Восстановление потерянной точки ===
        # Tesseract часто теряет точку: 8.3 → 83, 2.5 → 25
        # Используем last_distance для интеллектуального восстановления
        for target_type in ('mob', 'player'):
            last_dist = self.last_distance.get(target_type)
            if last_dist is not None:
                # Если текст — это 2 цифры без точки, пробуем вставить точку
                if len(text) == 2 and text.isdigit():
                    # Вариант A: X.Y (последнее было < 10)
                    if last_dist < 10:
                        candidate = f"{text[0]}.{text[1]}"
                        cand_val = float(candidate)
                        # Проверяем что новое значение близко к последнему (в пределах 30м)
                        if abs(cand_val - last_dist) < 30 and 0.5 <= cand_val <= 20:
                            _get_logger().debug(f"[OCR] Восстановлена точка: {text} → {candidate} (было {last_dist:.1f}м)")
                            return candidate
                    # Вариант B: XY.0 (последнее было >= 10)
                    elif last_dist >= 10:
                        candidate = f"{text}.0"
                        cand_val = float(candidate)
                        if abs(cand_val - last_dist) < 30 and 0.5 <= cand_val <= 200:
                            _get_logger().debug(f"[OCR] Восстановлена точка: {text} → {candidate} (было {last_dist:.1f}м)")
                            return candidate

        # Если last_distance неизвестен — используем эвристику по диапазону
        if len(text) == 2 and text.isdigit():
            val = int(text)
            # Числа 10-99 без точки — скорее всего X.Y (1.0-9.9) для близких дистанций
            # Но если число > 50 — скорее всего это XX.0 (50-99м)
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

        # 3 цифры без точки → XX.Y
        if len(text) == 3 and text.isdigit():
            candidate = f"{text[:2]}.{text[2]}"
            cand_val = float(candidate)
            if 0.5 <= cand_val <= 200:
                _get_logger().debug(f"[OCR] Восстановлена точка: {text} → {candidate}")
                return candidate

        # === ШАГ 2: Словарь типичных замен ===
        common_corrections = {
            # Исправления для X.Y формата
            '21.': '27.',  # 27.5 → 21.9 (Tesseract путает 7 и 1)
            '29.': '25.',  # 25.7 → 29.1 (Tesseract путает 5 и 9)
            '71': '77',    # 77 → 71
            '17': '77',    # 77 → 17
            '95': '55',    # 55 → 95
            '59': '55',    # 55 → 59
            '39': '35',    # 35 → 39
            '93': '53',    # 53 → 93
            '85': '85',    # 85 → 85 (оставляем)
            '58': '55',    # 55 → 58
            '89': '85',    # 85 → 89
            '98': '58',    # 58 → 98
            # ИСПРАВЛЕНИЕ: 30 → 35 (Tesseract путает 5 и 0)
            '30.': '35.',  # 35.7 → 30.7
            '30': '35',    # 35 → 30
            # Типичные потери точки + ошибки цифр
            '82': '8.2',   # 8.2 → 82
            '83': '8.3',   # 8.3 → 83
            '84': '8.4',   # 8.4 → 84
            '86': '8.6',   # 8.6 → 86
            '87': '8.7',   # 8.7 → 87
            '88': '8.8',   # 8.8 → 88
            '27': '2.7',   # 2.7 → 27 (если нет last_distance — эвристика)
            '25': '2.5',   # 2.5 → 25
            '35': '3.5',   # 3.5 → 35
            '45': '4.5',   # 4.5 → 45
            '55': '5.5',   # 5.5 → 55
            '65': '6.5',   # 6.5 → 65
            '75': '7.5',   # 7.5 → 75
            '95': '9.5',   # 9.5 → 95 (перезаписываем 95→55 выше — но 9.5 более вероятно)
            '15': '1.5',   # 1.5 → 15
            '05': '0.5',   # 0.5 → 05
            # Дополнительные исправления
            '4.': '4.',    # 4. → 4.
            '7.': '7.',    # 7. → 7.
            '1.': '1.',    # 1. → 1.
            '0.': '0.',    # 0. → 0.
            '6.': '6.',    # 6. → 6.
            '8.': '8.',    # 8. → 8.
            '3.': '3.',    # 3. → 3.
            '9.': '9.',    # 9. → 9.
            '2.': '2.',    # 2. → 2.
            '5.': '5.',    # 5. → 5.
            # Целые числа (оставляем как есть)
            '27': '27',    # 27 → 27
            '55': '55',    # 55 → 55
            '77': '77',    # 77 → 77
            '35': '35',    # 35 → 35
            '53': '53',    # 53 → 53
            '85': '85',    # 85 → 85
        }

        # Проверяем типичные ошибки
        for wrong, correct in common_corrections.items():
            if wrong in text:
                corrected = text.replace(wrong, correct)
                if corrected != text:
                    _get_logger().debug(f"Исправление OCR: {text} → {corrected}")
                    return corrected

        # Если число выглядит как расстояние (X.Y где X и Y цифры)
        # Проверяем что после точки одна цифра
        if '.' in text:
            parts = text.split('.')
            if len(parts) == 2:
                # Проверяем что части состоят только из цифр
                if parts[0].isdigit() and parts[1].isdigit():
                    if len(parts[1]) == 1:
                        # Это валидное расстояние вида X.Y
                        return text
                    elif len(parts[1]) > 1:
                        # Обрезаем до одной цифры после точки
                        return f"{parts[0]}.{parts[1][0]}"

        # Удаляем нецифровые символы кроме точки
        cleaned = re.sub(r'[^\d.]', '', text)
        if cleaned and cleaned != text:
            _get_logger().debug(f"Очистка OCR: {text} → {cleaned}")
            return cleaned

        return text

    def numbers_to_distance(self, numbers: List[str], target_type: str) -> Optional[float]:
        """
        Преобразует распознанные числа в дистанцию.
        ПРОСТАЯ ЛОГИКА - без фильтрации!
        Улучшенное распознавание формата X.X или XX.X
        
        Формат расстояния в игре: X.X или XX.X (например: 5.0, 36.2, 99.9)
        """
        if not numbers:
            return None

        # Ищем число с точкой (расстояние X.Y)
        for num in numbers:
            try:
                new_distance = float(num)
                
                # Отбрасываем ТОЛЬКО явный мусор (< 0.5м или > 200м)
                if new_distance < 0.5 or new_distance > 200:
                    _get_logger().debug(f"[OCR] Отброшен мусор: {new_distance}")
                    continue
                
                # Принимаем ЛЮБОЕ реалистичное значение!
                self.last_distance[target_type] = new_distance
                self.last_success_time[target_type] = time.time()
                _get_logger().debug(f"[OCR] {target_type}: {new_distance:.1f}м (numbers={numbers})")
                return new_distance
                
            except ValueError:
                continue
        
        # Если нет числа с точкой - пробуем исправить числа БЕЗ точки
        # Формат игры: X.X или XX.X (например: 5.0, 36.2, 99.9)
        last_dist = self.last_distance.get(target_type)

        for num in numbers:
            try:
                # Удаляем нецифровые символы кроме точки
                cleaned = re.sub(r'[^\d.]', '', num)

                if cleaned and '.' not in cleaned:
                    # Число без точки - пробуем исправить
                    if len(cleaned) == 3:
                        # 3 цифры → XX.X (например: 424 → 42.4)
                        fixed = f"{cleaned[:2]}.{cleaned[2]}"
                        new_distance = float(fixed)
                        if 0.5 <= new_distance <= 200:
                            _get_logger().debug(f"[OCR] Исправлено: {num} → {fixed}")
                            self.last_distance[target_type] = new_distance
                            self.last_success_time[target_type] = time.time()
                            return new_distance

                    elif len(cleaned) == 2:
                        # 2 цифры — ТЕРЯЕТСЯ ТОЧКА: 83 → 8.3
                        # Интеллектуальное восстановление на основе last_distance
                        if last_dist is not None:
                            if last_dist < 10:
                                # Было < 10м → скорее всего X.Y
                                fixed = f"{cleaned[0]}.{cleaned[1]}"
                                new_distance = float(fixed)
                                if 0.5 <= new_distance <= 20:
                                    _get_logger().debug(f"[OCR] Восстановлена точка: {num} → {fixed} (было {last_dist:.1f}м)")
                                    self.last_distance[target_type] = new_distance
                                    self.last_success_time[target_type] = time.time()
                                    return new_distance
                            elif last_dist >= 10:
                                # Было >= 10м → скорее всего XX.0
                                if last_dist <= 50:
                                    fixed = f"{cleaned}.0"
                                    new_distance = float(fixed)
                                    if 0.5 <= new_distance <= 200:
                                        _get_logger().debug(f"[OCR] Восстановлена точка: {num} → {fixed} (было {last_dist:.1f}м)")
                                        self.last_distance[target_type] = new_distance
                                        self.last_success_time[target_type] = time.time()
                                        return new_distance
                        else:
                            # last_distance неизвестен — эвристика по диапазону
                            val = int(cleaned)
                            if val <= 50:
                                # Скорее всего X.Y
                                fixed = f"{cleaned[0]}.{cleaned[1]}"
                                new_distance = float(fixed)
                                if 0.5 <= new_distance <= 20:
                                    _get_logger().debug(f"[OCR] Восстановлена точка (эвристика): {num} → {fixed}")
                                    self.last_distance[target_type] = new_distance
                                    self.last_success_time[target_type] = time.time()
                                    return new_distance
                            else:
                                # Скорее всего XX.0
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
        """Запуск ОДНОГО активного ридера."""
        _get_logger().info(f"[OCR] Запуск: active={self.active_target}, interval={self.interval}с")
        
        # ✅ Исправление утечки потоков: сначала останавливаем старый поток если он есть
        if self.ocr_thread is not None and self.ocr_thread.is_alive():
            _get_logger().warning("[OCR] Предыдущий поток OCR всё ещё работает, принудительная остановка")
            self.stop()
        
        # СБРОС кэша
        self.last_distance.clear()
        self.empty_attempts = 0
        _get_logger().debug("[OCR] Кэш дистанции сброшен")
        
        self._stopped = False
        self._running = True
        
        # Запуск потока
        self.ocr_thread = threading.Thread(
            target=self._check_active_target,
            daemon=True,
            name=f"OCR-{self.active_target}"
        )
        self.ocr_thread.start()
        
        _get_logger().info(f"[OCR] Поток запущен")
        self.finished.emit()

    def stop(self):
        """Остановка OCR."""
        _get_logger().info("[OCR] Остановка...")
        self._stopped = True
        self._running = False
        
        # ✅ Исправление deadlock: ждём максимум 1 секунду, никогда не блокируем навсегда
        if self.ocr_thread and self.ocr_thread.is_alive():
            try:
                self.ocr_thread.join(timeout=1.0)
                if self.ocr_thread.is_alive():
                    _get_logger().warning("[OCR] Поток не завершился за 1 секунду, оставляем работать как демон")
                else:
                    _get_logger().debug("[OCR] Поток остановлен")
            except Exception as e:
                _get_logger().error(f"[OCR] Ошибка при ожидании завершения потока: {e}")
        
        # НЕ СБРАСЫВАЕМ флаги! Оставляем _stopped = True для полной остановки
        
        _get_logger().info("[OCR] Остановлено")
        self.finished.emit()

    def get_active_target(self) -> str:
        """Возвращает активный таргет."""
        return self.active_target

    def get_last_processed(self, target_type: str = None):
        """Возвращает последнее распознанное расстояние."""
        if target_type:
            return self.last_distance.get(target_type)
        return self.last_distance


# ==================== ОСНОВНОЙ КЛАСС ЧТЕНИЯ ЦЕЛИ (QThread) ====================
class TargetReader(QThread):
    data_updated = Signal(str, float, list)

    def __init__(self, areas: Dict[str, Tuple[int, int, int, int]],
                 interval_per_area: float = 0.1,  # Увеличил частоту: 10 раз в секунду
                 scale: int = 10,
                 psm: int = 7,
                 use_morph: bool = True,
                 parent=None,
                 check_window: Callable[[], bool] = None,
                 activate_window_title: str = None,
                 skip_activate_window: bool = False):
        super().__init__(parent)
        self.worker = TargetWorker(areas, interval_per_area, scale, psm, use_morph, check_window, activate_window_title, skip_activate_window)
        # НЕ используем moveToThread — worker создаёт свой threading.Thread внутри start_work()
        self.worker.data_updated.connect(self._forward_data_updated)
        self.started.connect(self.worker.start_work)
        self.worker.finished.connect(self.quit)

    def _forward_data_updated(self, target_type, distance, numbers):
        """Пересылает сигнал от worker к внешним слушателям"""
        self.data_updated.emit(target_type, distance, numbers)

    def run(self):
        """Запуск потока - запускаем worker"""
        try:
            self.worker.start_work()
        except Exception as e:
            _get_logger().error(f"Ошибка в TargetReader.run(): {e}", exc_info=True)
        finally:
            self.worker.finished.emit()

    def stop(self):
        """Остановка TargetReader"""
        if self.worker:
            try:
                self.worker.stop()
            except RuntimeError:
                pass  # Qt C++ объект уже удалён
            try:
                self.worker.data_updated.disconnect(self._forward_data_updated)
            except (RuntimeError, TypeError):
                pass
        try:
            self.quit()
            self.wait(500)
        except RuntimeError:
            pass  # C++ объект уже удалён
        if self.worker:
            try:
                self.worker.deleteLater()
            except RuntimeError:
                pass
            self.worker = None

    def get_last_processed(self, target_type: str = None):
        """Возвращает последнее распознанное расстояние."""
        if self.worker:
            return self.worker.get_last_processed(target_type)
        return None


# ==================== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ====================
def draw_numbers_on_image(image: np.ndarray, numbers: List[str], position=(10, 30)):
    result = image.copy()
    if len(result.shape) == 2:
        result = cv2.cvtColor(result, cv2.COLOR_GRAY2BGR)
    text = " ".join(numbers)
    cv2.putText(result, text, position, cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
    return result

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    ensure_tesseract()
    print("Tesseract версия:", pytesseract.get_tesseract_version())
