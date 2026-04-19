# -*- coding: utf-8 -*-
"""
threads.py
Потоки и мониторинг для snbld resvap
"""

import os
import re
import time
import ctypes
import logging
import threading
import subprocess
from dataclasses import dataclass
from typing import List, Optional, Tuple

import psutil

from PySide6.QtCore import QThread, Signal

from constants import VIRTUAL_KEYS, MOVEMENT_MONITOR_BASE_INTERVAL, MOVEMENT_MONITOR_IDLE_INTERVAL


# ==================== МОНИТОРИНГ ДВИЖЕНИЯ ====================

# Безопасная инициализация USER32 (защита от ImportError на non-Windows)
try:
    USER32 = ctypes.windll.user32
except (AttributeError, OSError):
    USER32 = None


@dataclass
class MovementState:
    """Состояние мониторинга движения"""
    moving: bool = False
    last_stop_time: float = 0.0


class MovementMonitor(threading.Thread):
    """Поток мониторинга нажатия клавиш движения"""

    def __init__(self, movement_keys: List[str] = None):
        super().__init__(daemon=True)
        self.movement_keys = movement_keys or [
            'w', 'a', 's', 'd', 'up', 'down', 'left', 'right'
        ]
        self.state = MovementState()
        self.lock = threading.Lock()
        self._stop_event = threading.Event()  # Graceful shutdown
        self.base_interval = MOVEMENT_MONITOR_BASE_INTERVAL
        self.idle_interval = MOVEMENT_MONITOR_IDLE_INTERVAL
        self.current_interval = self.base_interval
        self.idle_count = 0
        logging.info(
            f"[MOVEMENT] Монитор движения запущен (режим WinAPI), "
            f"отслеживаем клавиши: {self.movement_keys}"
        )

    def _is_key_pressed(self, key: str) -> bool:
        """Проверяет, нажата ли клавиша через WinAPI"""
        if key not in VIRTUAL_KEYS:
            return False
        vk_code = VIRTUAL_KEYS[key]
        return bool(USER32.GetAsyncKeyState(vk_code) & 0x8000)

    def run(self):
        """Основной цикл мониторинга"""
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
                            f"[MOVEMENT] ⏹️ Остановка движения в "
                            f"{self.state.last_stop_time:.3f}"
                        )
                    elif moving and not self.state.moving:
                        logging.debug(f"[MOVEMENT] ▶️ Начало движения")
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
        """Возвращает время с момента последней остановки движения"""
        if current_time is None:
            current_time = time.time()
        with self.lock:
            if self.state.moving:
                return 0.0
            return current_time - self.state.last_stop_time

    def stop(self):
        """Останавливает монитор (graceful shutdown)"""
        self._stop_event.set()
        self.join(timeout=2)
        logging.info("[MOVEMENT] Монитор движения остановлен")


# ==================== ПРОВЕРКА БАФФОВ ====================

class BuffCheckThread(QThread):
    """Поток проверки активных баффов"""
    buffExpired = Signal(int)

    def __init__(self, app):
        super().__init__()
        self.app = app
        self._stop_event = threading.Event()  # Graceful shutdown

    def run(self):
        """Основной цикл проверки баффов (безопасное чтение через snapshot)"""
        while not self._stop_event.is_set():
            self._stop_event.wait(0.5)
            now = time.time()
            to_remove = []
            # Безопасное чтение через snapshot (защита от race condition)
            buffs_snapshot = self.app.get_active_buffs_snapshot()
            for buff_id, info in buffs_snapshot.items():
                remaining = info["end_time"] - now
                if remaining <= 0:
                    to_remove.append(buff_id)
                else:
                    # Обновляем remaining в оригинальном словаре под замком
                    with self.app.buff_lock:
                        if buff_id in self.app.active_buffs:
                            self.app.active_buffs[buff_id]["remaining"] = remaining
            for buff_id in to_remove:
                # Удаляем истёкший бафф из словаря под замком
                with self.app.buff_lock:
                    self.app.active_buffs.pop(buff_id, None)
                self.buffExpired.emit(buff_id)

    def stop(self):
        """Останавливает поток (graceful shutdown)"""
        self._stop_event.set()
        self.wait(2000)


# ==================== МОНИТОРИНГ КЛИКОВ МЫШИ ====================

logger = logging.getLogger('macros')

import mouse
import win32api

class MouseClickMonitor(QThread):
    """
    Мониторинг кликов мыши для зональных макросов.
    Использует событийный подход (mouse.hook) вместо polling — надёжнее и быстрее.
    """
    mouse_clicked = Signal(int, int)  # x, y координаты клика

    def __init__(self):
        super().__init__()
        self._stop_event = threading.Event()  # Graceful shutdown
        self.daemon = True
        self._last_click_time = 0.0
        self._debounce_ms = 100  # Защита от повторных кликов
        self._hook_handle = None  # Сохраняем хук для надёжного unhook
        logger.info("[MOUSE] MouseClickMonitor создан (событийный режим)")

    def _on_mouse_event(self, event):
        """Обработчик событий мыши"""
        if self._stop_event.is_set():
            return

        # Проверяем наличие атрибута event_type (новая версия mouse library может отправлять MoveEvent)
        if not hasattr(event, 'event_type'):
            return

        # Проверяем: левый клик вниз
        if event.event_type == 'down' and event.button == 'left':
            import time
            current_time = time.time()

            # Защита от повторных кликов (debounce)
            if current_time - self._last_click_time < self._debounce_ms / 1000.0:
                return

            # Получаем позицию мыши
            point = win32api.GetCursorPos()
            x, y = point[0], point[1]

            # Отправляем сигнал
            self.mouse_clicked.emit(x, y)
            self._last_click_time = current_time

            logger.info(f"[MOUSE] Клик: ({x},{y})")

    def run(self):
        """Основной цикл — блокируется на mouse.hook"""
        logger.info("[MOUSE] MouseClickMonitor запущен (событийный режим)")

        try:
            # mouse.hook() блокирует поток и вызывает callback при каждом событии
            self._hook_handle = mouse.hook(self._on_mouse_event)
            # Ждём сигнала остановки
            while not self._stop_event.is_set():
                self._stop_event.wait(0.1)
        except Exception as e:
            logger.error(f"[MOUSE] Ошибка в hook: {e}")
        finally:
            # Гарантированная очистка хука
            self._remove_hook()

        logger.info("[MOUSE] MouseClickMonitor остановлен")

    def _remove_hook(self):
        """Надёжное удаление хука с фиктивным событием для разблокировки"""
        try:
            if self._hook_handle is not None:
                mouse.unhook(self._hook_handle)
                self._hook_handle = None
        except Exception:
            pass
        # Посылаем фиктивное событие чтобы разблокировать hook если он ещё внутри C-расширения
        try:
            mouse.move(0, 0, absolute=False, duration=0.0)
        except Exception:
            pass

    def stop(self):
        """Останавливает поток (graceful shutdown)"""
        self._stop_event.set()
        self._remove_hook()
        self.wait(2000)


# ==================== МОНИТОРИНГ ПИНГА ====================

logger = logging.getLogger('network')

class PingMonitor(QThread):
    """Поток измерения пинга до игрового сервера"""
    ping_updated = Signal(int)
    server_ip_found = Signal(str)

    def __init__(self, process_name: str, interval: int = 5):
        super().__init__()
        self.process_name = process_name
        self.interval = interval  # 5 секунд вместо 30
        self._stop_event = threading.Event()  # Graceful shutdown
        self.server_ip = None
        self._cached_pid = None  # Кэш PID для оптимизации
        self.daemon = True  # Автоматическая остановка при выходе

    def find_server_ip(self) -> Optional[str]:
        """Находит IP игрового сервера через анализ соединений (с кэшированием PID)"""
        try:
            # Проверяем кэш PID
            pid = self._cached_pid
            if pid is None or not psutil.pid_exists(pid):
                # Ищем процесс заново
                for proc in psutil.process_iter(['pid', 'name']):
                    if proc.info['name'] and \
                       self.process_name.lower() in proc.info['name'].lower():
                        pid = proc.info['pid']
                        self._cached_pid = pid
                        break
            if not pid:
                return None

            # Проверяем только соединения этого процесса (быстрее чем psutil.net_connections())
            try:
                proc = psutil.Process(pid)
                for conn in proc.connections(kind='tcp'):
                    if conn.status == 'ESTABLISHED' and conn.raddr and not self._is_local_ip(conn.raddr.ip):
                        return conn.raddr.ip
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                self._cached_pid = None  # Сброс кэша при ошибке
            return None
        except Exception as e:
            logging.error(f"Ошибка поиска IP сервера: {e}")
            return None

    def _is_local_ip(self, ip: str) -> bool:
        """Проверяет, является ли IP локальным"""
        return (
            ip.startswith('127.') or
            ip.startswith('192.168.') or
            ip.startswith('10.') or
            ip.startswith('172.16.')
        )

    def measure_ping(self, ip: str) -> Optional[int]:
        """Измеряет пинг до IP через ping"""
        try:
            startupinfo = None
            creationflags = 0
            if os.name == 'nt':
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                startupinfo.wShowWindow = 0
                creationflags = subprocess.CREATE_NO_WINDOW

            result = subprocess.run(
                ['ping', '-n', '4', ip],
                capture_output=True,
                text=True,
                timeout=10,
                encoding='cp866',
                startupinfo=startupinfo,
                creationflags=creationflags
            )
            match = re.search(
                r'Среднее\s*=\s*(\d+)',
                result.stdout,
                re.IGNORECASE
            )
            if not match:
                match = re.search(
                    r'Average\s*=\s*(\d+)',
                    result.stdout,
                    re.IGNORECASE
                )
            if match:
                return int(match.group(1))
        except Exception as e:
            logging.debug(f"Ошибка измерения пинга: {e}")
        return None

    def run(self):
        """Основной цикл мониторинга пинга (graceful shutdown)"""
        logger.info(f"PingMonitor запущен, интервал={self.interval}сек")
        check_ip_counter = 0

        # Ждём 5 секунд перед первым измерением (игра должна подключиться)
        logger.debug(f"Ожидание подключения игры...")
        if self._stop_event.wait(5):
            return  # Были остановлены во время ожидания

        while not self._stop_event.is_set():
            # Каждые 3 измерения проверяем актуальный IP сервера
            check_ip_counter += 1
            if check_ip_counter >= 3 or self.server_ip is None:
                check_ip_counter = 0
                ip = self.find_server_ip()
                if ip:
                    if self.server_ip != ip:
                        logger.info(f"IP сервера изменился: {self.server_ip} → {ip}")
                    self.server_ip = ip
                    self.server_ip_found.emit(ip)
                else:
                    logger.debug(f"Не удалось найти IP сервера (игра не запущена?)")
                    if self._stop_event.wait(self.interval):
                        break  # Были остановлены
                    continue

            ping = self.measure_ping(self.server_ip)
            if ping is not None:
                logger.info(f"Пинг до {self.server_ip}: {ping} мс")
                self.ping_updated.emit(ping)
            else:
                logger.debug(f"Не удалось измерить пинг")
            if self._stop_event.wait(self.interval):
                break  # Были остановлены

    def stop(self):
        """Останавливает поток (graceful shutdown)"""
        self._stop_event.set()
        self.wait(2000)
