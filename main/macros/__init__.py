import sys
import os

_parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _parent_dir not in sys.path:
    sys.path.insert(0, _parent_dir)

import macros_core

Macro = macros_core.Macro
SimpleMacro = macros_core.SimpleMacro
ZoneMacro = macros_core.ZoneMacro
SkillMacro = macros_core.SkillMacro
BuffMacro = macros_core.BuffMacro
send_key = macros_core.send_key

from .steps_executor import StepsExecutor

__all__ = [
    "Macro",
    "SimpleMacro",
    "ZoneMacro",
    "SkillMacro",
    "BuffMacro",
    "send_key",

    "StepsExecutor",
]
