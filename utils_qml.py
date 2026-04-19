# -*- coding: utf-8 -*-
"""
utils_qml.py
Утилиты для работы с ресурсами в QML
"""

import os
import sys
from PySide6.QtCore import QObject, Slot, Property


class QMLResourceHelper(QObject):
    """Помощник для получения путей к ресурсам из QML."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._base_path = self._get_base_path()

    def _get_base_path(self) -> str:
        """Получает базовый путь к ресурсам"""
        if getattr(sys, 'frozen', False):
            return os.path.dirname(sys.executable)
        else:
            return os.path.dirname(os.path.abspath(__file__))

    @Slot(str, result=str)
    def get_resource_path(self, relative_path: str) -> str:
        """Возвращает полный путь к ресурсу."""
        full_path = os.path.join(self._base_path, relative_path)
        if os.path.exists(full_path):
            return full_path

        script_dir = os.path.dirname(os.path.abspath(__file__))
        full_path = os.path.join(script_dir, relative_path)
        if os.path.exists(full_path):
            return full_path

        return relative_path

    @Slot(str, result=str)
    def get_resource_url(self, relative_path: str) -> str:
        """Возвращает file:// URL к ресурсу для QML."""
        full_path = self.get_resource_path(relative_path)
        full_path = full_path.replace('\\', '/')
        return f"file:///{full_path}"

    @Slot(str, result=str)
    def get_icon_url(self, icon_name: str) -> str:
        """Возвращает URL к иконке в папке icons/."""
        return self.get_resource_url(os.path.join("icons", icon_name))

    @Slot(int, result=str)
    def get_skill_icon_url(self, skill_id: int) -> str:
        """Возвращает URL к иконке скилла."""
        return self.get_resource_url(os.path.join("icons", "skills", f"{skill_id}.png"))

    @Property(str, constant=True)
    def base_path(self) -> str:
        """Базовый путь к ресурсам (для отладки)"""
        return self._base_path
