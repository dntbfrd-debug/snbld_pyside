# -*- coding: utf-8 -*-
"""
utils/tray_icon.py
Менеджер системного трея — показывает статус программы в трее Windows
Зелёный = работает, Жёлтый = остановлен, Красный = ошибка
"""

import os
import sys

from PySide6.QtWidgets import QSystemTrayIcon, QMenu
from PySide6.QtGui import QIcon, QAction, QPainter, QPixmap, QColor, QCursor
from PySide6.QtCore import Qt, QCoreApplication, QTimer


# Статусы
STATUS_RUNNING = "running"     # Зелёный
STATUS_STOPPED = "stopped"     # Жёлтый
STATUS_ERROR = "error"         # Красный

# Цвета индикаторов (RGB)
_STATUS_COLORS = {
    STATUS_RUNNING: "#22c55e",  # Зелёный
    STATUS_STOPPED:  "#eab308",  # Жёлтый
    STATUS_ERROR:    "#ef4444",  # Красный
}


def _create_indicator_pixmap(status, size=16):
    """
    Создаёт иконку-индикатор: кружок с цветом статуса.
    Используем QPixmap без внешних файлов.
    """
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.transparent)

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)

    color = _STATUS_COLORS.get(status, "#888888")
    painter.setBrush(QColor(color))
    painter.setPen(Qt.NoPen)
    painter.drawEllipse(2, 2, size - 4, size - 4)
    painter.end()

    return pixmap


class TrayIconManager:
    """
    Менеджер системного трея.
    Показывает статус программы и позволяет быстро управлять.
    """

    def __init__(self, backend, app):
        """
        Args:
            backend: экземпляр Backend
            app: экземпляр QApplication
        """
        self.backend = backend
        self.app = app
        self._tray = None
        self._current_status = STATUS_STOPPED
        self._menu = None

    def _create_menu(self):
        """Создаёт стилизованное контекстное меню"""
        menu = QMenu()
        menu.setStyleSheet("""
            QMenu {
                background-color: #2d2d2d;
                border: 1px solid #50ffffff;
                border-radius: 6px;
                padding: 4px;
            }
            QMenu::item {
                color: #c2c2c2;
                padding: 8px 30px 8px 20px;
                border-radius: 4px;
                margin: 1px;
            }
            QMenu::item:selected {
                background-color: #404040;
                color: #ffffff;
            }
            QMenu::separator {
                height: 1px;
                background-color: #50ffffff;
                margin: 4px 10px;
            }
        """)

        action_show = QAction("Показать окно", menu)
        action_show.triggered.connect(self._on_show_window)
        menu.addAction(action_show)

        menu.addSeparator()

        action_start = QAction("▶ Старт макросов", menu)
        action_start.triggered.connect(self._on_start_all)
        menu.addAction(action_start)

        action_stop = QAction("■ Стоп макросов", menu)
        action_stop.triggered.connect(self._on_stop_all)
        menu.addAction(action_stop)

        menu.addSeparator()

        action_quit = QAction("Выход", menu)
        action_quit.triggered.connect(self._on_quit)
        menu.addAction(action_quit)

        return menu

    def init_tray(self):
        """Инициализирует tray-иконку"""
        if not QSystemTrayIcon.isSystemTrayAvailable():
            return

        self._tray = QSystemTrayIcon()

        # Создаём иконку
        pixmap = _create_indicator_pixmap(STATUS_STOPPED)
        icon = QIcon(pixmap)
        self._tray.setIcon(icon)
        self._tray.setToolTip("snbld resvap — Остановлен")

        # Создаём меню заранее
        self._menu = self._create_menu()

        # Правый клик — показываем наше меню вручную
        self._tray.setContextMenu(None)
        self._tray.activated.connect(self._on_tray_clicked)

        # Таймер для показа меню (нужно для асинхронности)
        self._show_menu_timer = QTimer()
        self._show_menu_timer.setSingleShot(True)
        self._show_menu_timer.timeout.connect(self._show_context_menu)

        self._tray.show()

    def update_status(self, status, message=None):
        """
        Обновляет статус в трее.

        Args:
            status: STATUS_RUNNING / STATUS_STOPPED / STATUS_ERROR
            message: Текст для тултипа (опционально)
        """
        if not self._tray:
            return

        self._current_status = status
        pixmap = _create_indicator_pixmap(status)
        self._tray.setIcon(QIcon(pixmap))

        if message:
            self._tray.setToolTip(f"snbld resvap — {message}")
        else:
            labels = {
                STATUS_RUNNING: "Работает",
                STATUS_STOPPED: "Остановлен",
                STATUS_ERROR: "Ошибка",
            }
            self._tray.setToolTip(f"snbld resvap — {labels.get(status, 'Неизвестно')}")

    def show_notification(self, title, message, icon=QSystemTrayIcon.Information):
        """Показывает всплывающее уведомление из трея"""
        if self._tray:
            self._tray.showMessage(title, message, icon, 3000)

    def show_window(self):
        """Показать главное окно"""
        window = getattr(self.backend, '_main_window', None)
        if window:
            window.setVisible(True)
            window.showNormal()
            window.raise_()
            try:
                window.requestActivate()
            except Exception:
                pass

    def _on_tray_clicked(self, reason):
        """Обработка клика по tray"""
        if reason == QSystemTrayIcon.Context:
            # Показываем меню вручную в позиции курсора
            self._show_menu_timer.start(10)
        elif reason == QSystemTrayIcon.DoubleClick:
            self._on_show_window()

    def _show_context_menu(self):
        """Показывает контекстное меню в позиции курсора"""
        if self._menu:
            pos = QCursor.pos()
            self._menu.popup(pos)

    def _on_show_window(self):
        """Показать главное окно"""
        window = getattr(self.backend, '_main_window', None)
        if window:
            window.setVisible(True)
            window.showNormal()
            window.raise_()
            try:
                window.requestActivate()
            except Exception:
                pass

    def _on_start_all(self):
        """Старт всех макросов из трея"""
        self.backend.start_all_macros()
        self.update_status(STATUS_RUNNING, "Макросы запущены")

    def _on_stop_all(self):
        """Стоп всех макросов из трея"""
        self.backend.stop_all_macros()
        self.update_status(STATUS_STOPPED, "Макросы остановлены")

    def _on_quit(self):
        """Выход из программы"""
        window = getattr(self.backend, '_main_window', None)
        if window:
            window.close()
        else:
            QCoreApplication.quit()
