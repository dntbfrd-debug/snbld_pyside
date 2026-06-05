import threading
from backend.logger_manager import get_logger

logger = get_logger('hooks_guard')

_active_hooks: dict = {}
_lock = threading.Lock()


def try_register_hook(name: str, hook_type: str) -> bool:
    global _active_hooks

    with _lock:
        if hook_type in _active_hooks:
            existing = _active_hooks[hook_type]
            logger.warning(
                f"[HOOKS] Конфликт: {name} пытается установить {hook_type}, "
                f"но уже активен от {existing}"
            )
            return False

        _active_hooks[hook_type] = name
        logger.debug(f"[HOOKS] {name} зарегистрировал {hook_type}")
        return True


def unregister_hook(hook_type: str):
    global _active_hooks
    with _lock:
        if hook_type in _active_hooks:
            del _active_hooks[hook_type]
            logger.debug(f"[HOOKS] {hook_type} снят с регистрации")
