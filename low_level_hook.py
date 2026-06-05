"""
Замена старого low_level_hook.py.
Содержит re-export MouseDetector под именем MouseHookManager для обратной совместимости
и функцию unhook_all(), которая используется в qml_main.py и input_blocker.py.
"""
from mouse_detector import MouseDetector as MouseHookManager
from backend.logger_manager import get_logger

logger = get_logger('mouse')


def unhook_all():
    """
    Заглушка для обратной совместимости.
    Раньше использовалась для очистки глобальных хуков (WH_KEYBOARD_LL, WH_MOUSE_LL).
    Теперь MouseDetector сам управляет своим хук-дескриптором.
    Если в будущем понадобится глобальная очистка — сюда можно добавить.
    """
    logger.debug("[low_level_hook] unhook_all() вызван — все хуки управляются через MouseDetector")

# Re-export для обратной совместимости
__all__ = ['MouseHookManager', 'unhook_all']