# -*- coding: utf-8 -*-
"""
backend/
Пакет менеджеров для snbld resvap QML версии
Разделение ответственности основного приложения
"""

from .logger_manager import LoggerManager, get_logger, log_error
from .settings_manager import SettingsManager
from .macros_dispatcher import MacroDispatcher
from .window_manager import WindowManager

__all__ = [
    "LoggerManager",
    "get_logger",
    "log_error",
    "SettingsManager",
    "MacroDispatcher",
    "WindowManager",
]
