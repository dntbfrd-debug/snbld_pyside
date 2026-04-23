# -*- coding: utf-8 -*-
"""
backend/window_manager.py
Менеджер управления окном
Проверка активного окна, активация окна игры, проверка живости процесса
"""

import win32gui
import win32process
import psutil
from typing import Optional, Tuple

from .logger_manager import get_logger

logger = get_logger('macros')


class WindowManager:
    """
    Менеджер управления окном.
    Отвечает за проверку и активацию окон.
    """

    def __init__(self):
        self._window_locked = False
        self._target_window_title = ""
        self._window_position: Optional[Tuple[int, int]] = None

    @property
    def window_locked(self) -> bool:
        """Проверяет, заблокировано ли окно"""
        return self._window_locked

    @window_locked.setter
    def window_locked(self, value: bool) -> None:
        """Устанавливает режим блокировки окна"""
        self._window_locked = bool(value)
        logger.debug(f"Window locked: {self._window_locked}")

    @property
    def target_window_title(self) -> str:
        """Возвращает целевой заголовок окна"""
        return self._target_window_title

    @target_window_title.setter
    def target_window_title(self, value: str) -> None:
        """Устанавливает целевой заголовок окна"""
        self._target_window_title = str(value).strip()
        logger.debug(f"Target window title: {self._target_window_title}")

    def set_window_lock(self, locked: bool, title: str = "") -> None:
        """
        Устанавливает блокировку окна.

        Args:
            locked: Режим блокировки
            title: Заголовок целевого окна
        """
        self._window_locked = locked
        self._target_window_title = title.strip()
        logger.info(f"Блокировка окна: locked={locked}, title='{self._target_window_title}'")

    def check_window(self) -> bool:
        """
        Проверяет, активно ли целевое окно.

        Returns:
            True если окно активно или блокировка отключена
        """
        if not self._window_locked:
            return True
        
        target = self._target_window_title.strip().lower()
        if not target:
            return True
        
        try:
            hwnd = win32gui.GetForegroundWindow()
            active_title = win32gui.GetWindowText(hwnd).lower()
            result = target in active_title
            
            if not result:
                logger.debug(f"Окно неактивно: '{active_title}' != '{target}'")
            
            return result
        except Exception as e:
            logger.error(f"Ошибка проверки окна: {e}")
            return True  # В случае ошибки разрешаем выполнение

    def activate_window(self) -> bool:
        """
        Активирует окно с указанным заголовком.

        Returns:
            True если окно активировано
        """
        if not self._target_window_title:
            return False

        def enum_callback(hwnd, hwnds):
            try:
                if win32gui.IsWindowVisible(hwnd):
                    title = win32gui.GetWindowText(hwnd)
                    if self._target_window_title.lower() in title.lower():
                        hwnds.append(hwnd)
            except Exception:
                pass
            return True

        hwnds = []
        win32gui.EnumWindows(enum_callback, hwnds)
        
        if hwnds:
            try:
                win32gui.SetForegroundWindow(hwnds[0])
                logger.debug(f"Окно активировано: {hwnds[0]}")
                return True
            except Exception as e:
                logger.error(f"Ошибка активации окна: {e}")
        
        return False

    def find_window(self, title_substring: str) -> Optional[int]:
        """
        Ищет окно по подстроке заголовка.

        Args:
            title_substring: Подстрока для поиска

        Returns:
            HWND окна или None
        """
        def enum_callback(hwnd, hwnds):
            try:
                if win32gui.IsWindowVisible(hwnd):
                    title = win32gui.GetWindowText(hwnd)
                    if title_substring.lower() in title.lower():
                        hwnds.append(hwnd)
            except Exception:
                pass
            return True

        hwnds = []
        win32gui.EnumWindows(enum_callback, hwnds)
        return hwnds[0] if hwnds else None

    def get_window_list(self) -> list:
        """
        Возвращает список видимых окон.

        Returns:
            Список кортежей (hwnd, title)
        """
        windows = []
        
        def enum_callback(hwnd, _):
            try:
                if win32gui.IsWindowVisible(hwnd):
                    title = win32gui.GetWindowText(hwnd)
                    if title:  # Только окна с заголовком
                        windows.append((hwnd, title))
            except Exception:
                pass
            return True

        win32gui.EnumWindows(enum_callback, None)
        return windows

    def save_window_position(self, x: int, y: int) -> None:
        """Сохраняет позицию окна"""
        self._window_position = (x, y)
        logger.debug(f"Позиция окна сохранена: ({x}, {y})")

    def get_window_position(self) -> Optional[Tuple[int, int]]:
        """Возвращает сохранённую позицию окна"""
        return self._window_position

    def is_valid_title(self, title: str) -> bool:
        """Проверяет, существует ли окно с таким заголовком"""
        return self.find_window(title) is not None

    def is_game_process_alive(self, process_name="ElementClient_x64.exe") -> bool:
        """
        Проверяет, запущен ли процесс игры (не просто окно, а сам процесс).
        Это позволяет отличить 'окно свёрнуто' от 'игра упала'.

        Args:
            process_name: Имя процесса игры

        Returns:
            True если процесс существует и отвечает
        """
        try:
            for proc in psutil.process_iter(['pid', 'name']):
                if proc.info['name'] and proc.info['name'].lower() == process_name.lower():
                    # Проверяем что процесс не заморожен
                    if proc.status() in (psutil.STATUS_ZOMBIE, psutil.STATUS_DEAD):
                        logger.warning(f"Процесс игры {process_name} в состоянии {proc.status()}")
                        return False
                    return True
            return False
        except Exception as e:
            logger.error(f"Ошибка проверки процесса игры: {e}")
            return True  # В случае ошибки разрешаем выполнение (safe fallback)

    def get_game_process_info(self, process_name="ElementClient_x64.exe") -> Optional[dict]:
        """
        Возвращает информацию о процессе игры.

        Args:
            process_name: Имя процесса

        Returns:
            dict с pid, name, cpu_percent, memory_info или None
        """
        try:
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_info']):
                if proc.info['name'] and proc.info['name'].lower() == process_name.lower():
                    return {
                        'pid': proc.info['pid'],
                        'name': proc.info['name'],
                        'cpu_percent': proc.cpu_percent(),
                        'memory_mb': proc.info['memory_info'].rss / (1024 * 1024) if proc.info['memory_info'] else 0,
                    }
            return None
        except Exception as e:
            logger.error(f"Ошибка получения информации о процессе: {e}")
            return None
