# -*- coding: utf-8 -*-
"""
macros/
Пакет макросов для snbld resvap
Разделение логики выполнения и проверок
"""

import sys
import os

# Добавляем родительскую директорию в path для импорта
_parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _parent_dir not in sys.path:
    sys.path.insert(0, _parent_dir)

# Импортируем классы макросов из macros_core.py
import importlib.util
import sys
import os

# Nuitka/PyInstaller: ищем macros_core.py
_macro_path = None

# 1. Nuitka _MEIPASS - ищем в корне распаковки
if hasattr(sys, '_MEIPASS'):
    _test = os.path.join(sys._MEIPASS, "macros_core.py")
    if os.path.exists(_test):
        _macro_path = _test
        print(f"[macros] Found macros_core.py in _MEIPASS: {_macro_path}")

# 2. Nuitka _MEIPASS - ищем в подпапке macros
if not _macro_path and hasattr(sys, '_MEIPASS'):
    _test = os.path.join(sys._MEIPASS, "macros", "macros_core.py")
    if os.path.exists(_test):
        _macro_path = _test
        print(f"[macros] Found macros_core.py in _MEIPASS/macros: {_macro_path}")

# 3. Рядом с exe
if not _macro_path and getattr(sys, 'frozen', False):
    _exe_dir = os.path.dirname(sys.executable)
    _test = os.path.join(_exe_dir, "macros_core.py")
    if os.path.exists(_test):
        _macro_path = _test
        print(f"[macros] Found macros_core.py next to exe: {_macro_path}")

# 4. Рядом с исходным скриптом
if not _macro_path:
    _test = os.path.join(_parent_dir, "macros_core.py")
    if os.path.exists(_test):
        _macro_path = _test
        print(f"[macros] Found macros_core.py in source: {_macro_path}")

# 5. Fallback - в подпапке macros рядом с exe
if not _macro_path and getattr(sys, 'frozen', False):
    _exe_dir = os.path.dirname(sys.executable)
    _test = os.path.join(_exe_dir, "macros", "macros_core.py")
    if os.path.exists(_test):
        _macro_path = _test
        print(f"[macros] Found macros_core.py in exe/macros: {_macro_path}")

if not _macro_path:
    print(f"[macros] ERROR: macros_core.py not found!")
    print(f"[macros] _MEIPASS: {getattr(sys, '_MEIPASS', 'N/A')}")
    print(f"[macros] frozen: {getattr(sys, 'frozen', False)}")
    print(f"[macros] exe: {getattr(sys, 'executable', 'N/A')}")
    raise FileNotFoundError(f"macros_core.py not found!")

spec = importlib.util.spec_from_file_location("macros_core", _macro_path)
_macros_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(_macros_module)

Macro = _macros_module.Macro
SimpleMacro = _macros_module.SimpleMacro
ZoneMacro = _macros_module.ZoneMacro
SkillMacro = _macros_module.SkillMacro
BuffMacro = _macros_module.BuffMacro
send_key = _macros_module.send_key

# Импортируем новые компоненты
from .steps_executor import StepsExecutor
from .checks import (
    WindowChecker,
    CooldownChecker,
    DistanceChecker,
    CastLockChecker,
    MovementDelayChecker
)

__all__ = [
    # Классы макросов
    "Macro",
    "SimpleMacro",
    "ZoneMacro",
    "SkillMacro",
    "BuffMacro",
    "send_key",

    # Новые компоненты
    "StepsExecutor",
    "WindowChecker",
    "CooldownChecker",
    "DistanceChecker",
    "CastLockChecker",
    "MovementDelayChecker",
]
