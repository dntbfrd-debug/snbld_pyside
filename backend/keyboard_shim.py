# backend/keyboard_shim.py — Replacement for `keyboard` library using WinAPI
# Использует глобальный InputBlocker (если доступен) — не создаёт дублирующий WH_KEYBOARD_LL хук
# Если InputBlocker недоступен, использует собственный HotkeyManager
from backend.logger_manager import get_logger

_log = get_logger('keyboard_shim')


def _use_input_blocker():
    try:
        from input_blocker import get_global_blocker
        blocker = get_global_blocker()
        return blocker is not None
    except Exception:
        return False


def _hkm():
    from backend.win32_api import HotkeyManager
    hkm = HotkeyManager()
    hkm.start()
    return hkm


def hook_key(hotkey_str, callback, suppress=True, **kwargs):
    if _use_input_blocker():
        from input_blocker import register_hotkey_callback
        register_hotkey_callback(hotkey_str, callback, suppress=suppress)
        _log.debug(f"Registered hotkey via InputBlocker: {hotkey_str}, suppress={suppress}")
    else:
        _hkm().register(hotkey_str, callback, suppress=suppress)
        _log.debug(f"Registered hotkey via HotkeyManager: {hotkey_str}, suppress={suppress}")


def unhook_key(hotkey_str):
    if _use_input_blocker():
        from input_blocker import unregister_hotkey_callback
        unregister_hotkey_callback(hotkey_str)
    else:
        _hkm().unregister(hotkey_str)
    _log.debug(f"Unregistered hotkey: {hotkey_str}")


def unhook_all():
    try:
        from input_blocker import get_global_blocker
        blocker = get_global_blocker()
        if blocker is not None:
            blocker.unregister_all_hotkey_callbacks()
            _log.debug("All hotkeys unregistered via InputBlocker")
            return
    except Exception:
        pass
    _hkm().unregister_all()
    _log.debug("All hotkeys unregistered via HotkeyManager")


def add_hotkey(hotkey_str, callback, suppress=True, **kwargs):
    hook_key(hotkey_str, callback, suppress=suppress)


def remove_hotkey(hotkey_str):
    unhook_key(hotkey_str)
