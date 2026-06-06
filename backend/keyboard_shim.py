from backend.logger_manager import get_logger

_log = get_logger('keyboard_shim')


def hook_key(hotkey_str, callback, suppress=True, **kwargs):
    try:
        from input_blocker import register_hotkey_callback
        register_hotkey_callback(hotkey_str, callback, suppress=suppress)
        _log.debug(f"Registered hotkey via InputBlocker: {hotkey_str}, suppress={suppress}")
    except Exception as e:
        _log.warning(f"Failed to register hotkey '{hotkey_str}': {e}")


def unhook_key(hotkey_str):
    try:
        from input_blocker import unregister_hotkey_callback
        unregister_hotkey_callback(hotkey_str)
    except Exception as e:
        _log.warning(f"Failed to unregister hotkey '{hotkey_str}': {e}")


def unhook_all():
    try:
        from input_blocker import get_global_blocker
        blocker = get_global_blocker()
        if blocker is not None:
            blocker.unregister_all_hotkey_callbacks()
            _log.debug("All hotkeys unregistered via InputBlocker")
    except Exception as e:
        _log.warning(f"Failed to unregister all hotkeys: {e}")


def add_hotkey(hotkey_str, callback, suppress=True, **kwargs):
    hook_key(hotkey_str, callback, suppress=suppress)


def remove_hotkey(hotkey_str):
    unhook_key(hotkey_str)
