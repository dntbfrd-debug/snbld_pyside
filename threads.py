import os
import re
import time
import ctypes
import logging
import threading
import subprocess
from dataclasses import dataclass
from typing import List, Optional, Tuple

from backend.win32_api import process_exists, find_processes_by_name, get_process_tcp_connections
from backend.logger_manager import get_logger

from PySide6.QtCore import QThread, Signal

from constants import VIRTUAL_KEYS, MOVEMENT_MONITOR_BASE_INTERVAL, MOVEMENT_MONITOR_IDLE_INTERVAL



try:
    USER32 = ctypes.windll.user32
except (AttributeError, OSError):
    USER32 = None


@dataclass
class MovementState:
    moving: bool = False
    last_stop_time: float = 0.0


class MovementMonitor(threading.Thread):

    def __init__(self, movement_keys: List[str] = None):
        super().__init__(daemon=True)
        self.movement_keys = movement_keys or [
            'w', 'a', 's', 'd', 'up', 'down', 'left', 'right'
        ]
        self.state = MovementState()
        self.lock = threading.Lock()
        self._stop_event = threading.Event()
        self.base_interval = MOVEMENT_MONITOR_BASE_INTERVAL
        self.idle_interval = MOVEMENT_MONITOR_IDLE_INTERVAL
        self.current_interval = self.base_interval
        self.idle_count = 0
        logging.info(
            f"[MOVEMENT] Монитор движения запущен (режим WinAPI), "
            f"отслеживаем клавиши: {self.movement_keys}"
        )

    def _is_key_pressed(self, key: str) -> bool:
        if key not in VIRTUAL_KEYS:
            return False
        if USER32 is None:
            return False
        vk_code = VIRTUAL_KEYS[key]
        return bool(USER32.GetAsyncKeyState(vk_code) & 0x8000)

    def run(self):
        logging.info("[MOVEMENT] Поток мониторинга (WinAPI) запущен")
        while not self._stop_event.is_set():
            try:
                moving = False
                for key in self.movement_keys:
                    if self._is_key_pressed(key):
                        moving = True
                        break

                with self.lock:
                    if not moving and self.state.moving:
                        self.state.last_stop_time = time.time()
                        logging.debug(
                            f"[MOVEMENT]  Остановка движения в "
                            f"{self.state.last_stop_time:.3f}"
                        )
                    elif moving and not self.state.moving:
                        logging.debug(f"[MOVEMENT]  Начало движения")
                    self.state.moving = moving

                if moving:
                    self.current_interval = self.base_interval
                    self.idle_count = 0
                else:
                    self.idle_count += 1
                    if self.idle_count > 10:
                        self.current_interval = self.idle_interval

            except Exception as e:
                logging.error(f"[MOVEMENT] Ошибка в цикле мониторинга: {e}")
            self._stop_event.wait(self.current_interval)

    def get_movement_delay(self, current_time: float = None) -> float:
        if current_time is None:
            current_time = time.time()
        with self.lock:
            if self.state.moving:
                return 0.0
            return current_time - self.state.last_stop_time

    def stop(self):
        self._stop_event.set()
        self.join(timeout=3)
        logging.info("[MOVEMENT] Монитор движения остановлен")



class FastDistanceReader(threading.Thread):
    def __init__(self, get_area_fn, get_settings_fn):
        super().__init__(daemon=True)
        self._running = False
        self._distance = None
        self._raw_distance = None
        self._lock = threading.Lock()
        self.get_area = get_area_fn
        self.get_settings = get_settings_fn
        self._history = []
        self._HISTORY_SIZE = 5
        self._last_raw_text = ""
        self._last_image = None
        self._debug_lock = threading.Lock()

    @property
    def distance(self):
        with self._lock:
            return self._distance

    @property
    def raw_distance(self):
        with self._lock:
            return self._raw_distance

    def get_last_raw_text(self):
        with self._debug_lock:
            return self._last_raw_text

    def get_last_image(self):
        with self._debug_lock:
            return self._last_image.copy() if self._last_image is not None else None

    def get_history(self):
        with self._lock:
            return list(self._history)

    def stop(self):
        self._running = False
        with self._debug_lock:
            self._last_image = None
            self._last_raw_text = ""

    def _correct_number(self, text: str) -> str:
        if not text:
            return text

        if text.isdigit():
            val = int(text)
            if 100 <= val <= 299:
                return f"{text[:-1]}.{text[-1]}"

        last_dist = None
        with self._lock:
            if self._distance is not None:
                last_dist = self._distance

        if len(text) == 2 and text.isdigit():
            if last_dist is not None:
                if last_dist < 10:
                    cand = f"{text[0]}.{text[1]}"
                    cv = float(cand)
                    if abs(cv - last_dist) < 30 and 0.5 <= cv <= 20:
                        return cand
                elif last_dist <= 50:
                    cand = f"{text}.0"
                    cv = float(cand)
                    if abs(cv - last_dist) < 30 and 0.5 <= cv <= 200:
                        return cand
            val = int(text)
            if val <= 50:
                cand = f"{text[0]}.{text[1]}"
                cv = float(cand)
                if 0.5 <= cv <= 20:
                    return cand
            else:
                cand = f"{text}.0"
                cv = float(cand)
                if 0.5 <= cv <= 200:
                    return cand

        if len(text) == 3 and text.isdigit():
            cand = f"{text[:2]}.{text[2]}"
            cv = float(cand)
            if 0.5 <= cv <= 200:
                return cand

        common = {
            '21.': '27.', '29.': '25.', '71': '77', '17': '77',
            '95': '55', '59': '55', '39': '35', '93': '53',
            '85': '85', '58': '55', '89': '85', '98': '58',
            '30.': '35.', '30': '35', '82': '8.2', '83': '8.3',
            '84': '8.4', '86': '8.6', '87': '8.7', '88': '8.8',
            '27': '2.7', '25': '2.5', '35': '3.5', '45': '4.5',
            '55': '5.5', '65': '6.5', '75': '7.5', '95': '9.5',
            '15': '1.5', '05': '0.5',
        }
        for wrong, correct in common.items():
            if wrong in text:
                return text.replace(wrong, correct)

        if '.' in text:
            parts = text.split('.')
            if len(parts) == 2 and parts[0].isdigit() and parts[1].isdigit():
                return f"{parts[0]}.{parts[1][0]}"

        return text

    def run(self):
        self._running = True
        logger = get_logger('ocr')
        while self._running:
            try:
                area = self.get_area()
                if not area:
                    time.sleep(0.1)
                    continue
                if isinstance(area, str):
                    area = tuple(int(x.strip()) for x in area.split(','))
                x1, y1, x2, y2 = area
                PADDING = 2
                monitor = {
                    "left": max(0, x1 - PADDING),
                    "top": max(0, y1 - PADDING),
                    "width": x2 - x1 + PADDING * 2,
                    "height": y2 - y1 + PADDING * 2
                }
                import mss
                with mss.mss() as sct:
                    img = sct.grab(monitor)
                    import numpy as np
                    img_np = np.array(img)
                if img_np.size == 0:
                    time.sleep(0.02)
                    continue
                h, w = img_np.shape[:2]

                import cv2
                scale = 5
                new_w = min(int(w * scale), 1000)
                new_h = min(int(h * scale), 250)
                resized = cv2.resize(img_np, (new_w, new_h), interpolation=cv2.INTER_LINEAR)

                gray = cv2.cvtColor(resized, cv2.COLOR_BGRA2GRAY)

                _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

                import pytesseract
                import re
                custom_config = '--psm 7 -c tessedit_char_whitelist=0123456789. -c preserve_interword_spaces=0'
                text = pytesseract.image_to_string(binary, config=custom_config, lang='eng', timeout=2).strip()

                if not text:
                    custom_config_alt = '--psm 6 -c tessedit_char_whitelist=0123456789.'
                    text = pytesseract.image_to_string(binary, config=custom_config_alt, lang='eng', timeout=2).strip()

                candidate = None
                if text:
                    numbers = re.findall(r'\d+\.?\d*', text)
                    for num in numbers:
                        try:
                            distance = float(num)
                            if 0.5 <= distance <= 200:
                                candidate = distance
                                break
                        except ValueError:
                            continue

                    if candidate is None and numbers:
                        corrected = self._correct_number(numbers[0])
                        if corrected != numbers[0]:
                            try:
                                distance = float(corrected)
                                if 0.5 <= distance <= 200:
                                    candidate = distance
                            except ValueError:
                                pass

                    if candidate is not None:
                        with self._lock:
                            prev = self._distance
                        if prev is not None and abs(candidate - prev) > 10:
                            with self._lock:
                                logger.debug(f"[FAST_OCR] Скачок {prev:.1f}→{candidate:.1f}м, отклонён")
                            candidate = None

                if candidate is not None:
                    with self._lock:
                        self._raw_distance = candidate
                    self._history.append(candidate)
                    if len(self._history) > self._HISTORY_SIZE:
                        self._history.pop(0)
                    sorted_hist = sorted(self._history)
                    stable = sorted_hist[len(sorted_hist) // 2]
                    with self._lock:
                        self._distance = stable
                    logger.debug(f"[FAST_OCR] {stable:.1f}м (hist={self._history})")

                with self._debug_lock:
                    self._last_raw_text = text if text else ""
                    self._last_image = binary.copy() if text else None

            except Exception as ex:
                logger.debug(f"[FAST_OCR] Ошибка OCR: {ex}")
            if candidate is not None:
                time.sleep(0.02)
            else:
                time.sleep(0.05)

class BuffCheckThread(QThread):
    buffExpired = Signal(int)

    def __init__(self, app):
        super().__init__()
        self.app = app
        self._stop_event = threading.Event()

    def run(self):
        while not self._stop_event.is_set():
            self._stop_event.wait(0.5)
            now = time.time()
            to_remove = []
            buffs_snapshot = self.app.get_active_buffs_snapshot()
            for buff_id, info in buffs_snapshot.items():
                remaining = info["end_time"] - now
                if remaining <= 0:
                    to_remove.append(buff_id)
                else:
                    with self.app.buff_lock:
                        if buff_id in self.app.active_buffs:
                            self.app.active_buffs[buff_id]["remaining"] = remaining
            for buff_id in to_remove:
                with self.app.buff_lock:
                    self.app.active_buffs.pop(buff_id, None)
                self.buffExpired.emit(buff_id)

    def stop(self):
        self._stop_event.set()
        self.wait(2000)



logger = get_logger('macros')

from mouse_detector import MouseDetector


class MouseClickMonitor(QThread):
    mouse_clicked = Signal(int, int)

    def __init__(self, target_window_title: str = ""):
        super().__init__()
        self._stop_event = threading.Event()
        self._target_window_title = target_window_title.strip().lower()
        self._inner = MouseDetector(self._target_window_title)
        try:
            inner_name = self._inner.__class__.__name__
            inner_mod = self._inner.__class__.__module__
            logger.info(f"[MOUSE] Using inner mouse monitor: {inner_name} (module={inner_mod})")
        except Exception:
            pass
        self.daemon = True
        self._paused_event = threading.Event()
        logger.info("[MOUSE] MouseClickMonitor created (WH_MOUSE_LL real-time detector)")

    def get_inner_monitor_name(self) -> str:
        try:
            return f"{self._inner.__class__.__module__}.{self._inner.__class__.__name__}"
        except Exception:
            return "unknown"

    def set_target_window(self, title: str):
        self._target_window_title = title.strip().lower()
        logger.info(f"[MOUSE] Фильтр окна установлен: '{self._target_window_title}'")

    def _on_click(self, x, y):
        if self._paused_event.is_set():
            return
        if self._target_window_title:
            try:
                from backend.win32_api import GetForegroundWindow, GetWindowTextTimeout
                hwnd = GetForegroundWindow()
                active_title = GetWindowTextTimeout(hwnd).lower()
                if self._target_window_title not in active_title:
                    logger.debug(f"[MOUSE] Клик ({x},{y}) игнорирован — окно '{active_title}' не совпадает с '{self._target_window_title}'")
                    return
            except Exception:
                pass
        self.mouse_clicked.emit(x, y)

    def run(self):
        logger.info("[MOUSE] Starting...")
        self._inner.set_target_window(self._target_window_title)
        self._inner.set_click_callback(self._on_click)
        self._inner.start()
        
        time.sleep(0.2)
        
        logger.info("[MOUSE] Running, waiting for clicks...")
        
        while not self._stop_event.is_set():
            self._stop_event.wait(0.1)
        
        self._inner.stop()
        logger.info("[MOUSE] Stopped")

    def pause(self):
        self._paused_event.set()

    def resume(self):
        self._paused_event.clear()

    def stop(self):
        self._stop_event.set()
        self.wait(2000)

    def isRunning(self):
        return self._inner.isRunning()



network_logger = get_logger('network')

class PingMonitor(QThread):
    ping_updated = Signal(int)
    server_ip_found = Signal(str)

    def __init__(self, process_name: str, interval: int = 5):
        super().__init__()
        self.process_name = process_name
        self.interval = interval
        self._stop_event = threading.Event()
        self.server_ip = None
        self._cached_pid = None
        self.daemon = True

    def find_server_ip(self) -> Optional[str]:
        try:
            pid = self._cached_pid
            if pid is None or not process_exists(pid):
                procs = find_processes_by_name(self.process_name)
                if procs:
                    pid = procs[0][0]
                    self._cached_pid = pid
            if not pid:
                return None

            try:
                for conn in get_process_tcp_connections(pid):
                    if conn['status'] == 'ESTABLISHED' and conn['raddr'] and not self._is_local_ip(conn['raddr'][0]):
                        return conn['raddr'][0]
            except Exception:
                self._cached_pid = None
            return None
        except Exception as e:
            logging.error(f"Ошибка поиска IP сервера: {e}")
            return None

    def _is_local_ip(self, ip: str) -> bool:
        if ip.startswith('127.'):
            return True
        if ip.startswith('192.168.'):
            return True
        if ip.startswith('10.'):
            return True
        if ip.startswith('172.'):
            parts = ip.split('.')
            if len(parts) >= 2:
                try:
                    second_octet = int(parts[1])
                    return 16 <= second_octet <= 31
                except ValueError:
                    pass
        return False

    def measure_ping(self, ip: str) -> Optional[int]:
        try:
            startupinfo = None
            creationflags = 0
            if os.name == 'nt':
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                startupinfo.wShowWindow = 0
                creationflags = subprocess.CREATE_NO_WINDOW

            try:
                result = subprocess.run(
                    ['ping', '-n', '2', ip],
                    capture_output=True,
                    text=True,
                    timeout=8,
                    encoding='cp866',
                    startupinfo=startupinfo,
                    creationflags=creationflags
                )
            except (LookupError, UnicodeDecodeError):
                result = subprocess.run(
                    ['ping', '-n', '2', ip],
                    capture_output=True,
                    text=True,
                    timeout=8,
                    encoding='utf-8',
                    errors='replace',
                    startupinfo=startupinfo,
                    creationflags=creationflags
                )
            match = re.search(
                r'(?:Среднее|Average|Mittelwert|Moyenne|Media|Promedio|Média|'
                r'Ortalama|Gemiddelde|Medelvärde|Średnia|Průměr|Keskiarvo|'
                r'平均|평균)\s*=\s*(\d+)',
                result.stdout,
                re.IGNORECASE
            )
            if match:
                return int(match.group(1))
        except Exception as e:
            logging.debug(f"Ошибка измерения пинга: {e}")
        return None

    def run(self):
        network_logger.info(f"PingMonitor запущен, интервал={self.interval}сек")
        check_ip_counter = 0
        while not self._stop_event.is_set():
            check_ip_counter += 1
            if check_ip_counter >= 3 or self.server_ip is None:
                check_ip_counter = 0
                ip = self.find_server_ip()
                if ip:
                    if self.server_ip != ip:
                        network_logger.info(f"IP сервера изменился: {self.server_ip} → {ip}")
                    self.server_ip = ip
                    self.server_ip_found.emit(ip)
                else:
                    network_logger.debug(f"Не удалось найти IP сервера (игра не запущена?)")
                    if self._stop_event.wait(self.interval):
                        break
                    continue

            ping = self.measure_ping(self.server_ip)
            if ping is not None:
                network_logger.info(f"Пинг до {self.server_ip}: {ping} мс")
                self.ping_updated.emit(ping)
            else:
                network_logger.debug(f"Не удалось измерить пинг")
            if self._stop_event.wait(self.interval):
                break

    def stop(self):
        self._stop_event.set()
        self.wait(2000)
