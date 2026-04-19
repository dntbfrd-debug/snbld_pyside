# Backend — Windows & Hotkeys

> Hotkey system, window selection, and activation for snbld resvap

---

## Hotkey System

### Registration

```python
def register_hotkey(self, hotkey, callback,
                    check_window=True, check_global_stop=True, suppress=True):
```

Registers via `keyboard.hook_key()`. Parameters:

| Parameter | Default | Description |
|-----------|---------|-------------|
| `check_window` | `True` | Verify game window is active before firing |
| `check_global_stop` | `True` | Block if `global_stopped = True` |
| `suppress` | `True` | Suppress key passthrough to game |

**Wrapped callback:** debounce (200ms) → global stop check → window title check → execute.

```python
def unregister_hotkey(self, hotkey):   # Removes via keyboard.unhook_key()
def register_all_hotkeys(self):        # Re-registers ALL with correct suppress state
def unregister_all_hotkeys(self):      # Removes ALL registered hotkeys
```

### `register_all_hotkeys()` — Full Re-registration

Called on profile load, start/stop all, settings change:

```python
# Start/Stop — always active, never suppressed
register_hotkey(start_key, start_all_macros,
                check_window=False, check_global_stop=False, suppress=False)
register_hotkey(stop_key,  stop_all_macros,
                check_window=False, check_global_stop=False, suppress=False)

# Macros — suppress depends on running state
suppress_macros = not self._global_stopped
for macro in self._macros:
    register_hotkey(macro.hotkey, callback,
                    check_window=True, check_global_stop=True,
                    suppress=suppress_macros)
```

### Macro Callback Logic

1. **Cast lock check** — blocks if `cast_lock_until` not expired
2. **Quick stop detection** — ignores key-up within 0.3s of start
3. **Dispatch** — `dispatcher.request_macro(macro, priority=3)`
4. **Toggle** — if running, calls `macro.stop()`

### Supported Keys

`a-z`, `0-9`, `f1-f12` | `ctrl+e`, `shift+2`, `alt+f1` | `enter`, `space`, `tab`, arrows

---

## Window Selection & Binding

### Properties

| Property | Type | Description |
|----------|------|-------------|
| `window_locked` | bool | Lock macros to specific window |
| `target_window_title` | str | Title of target game window |

### Signals

`windowsListUpdated(list)` — visible windows | `openWindowSelector` — open selector dialog

### Backend Methods

```python
@Slot()
def selectWindowFromList(self):      # Opens QML WindowSelectorDialog
@Slot(str)
def set_target_window(self, title):  # Sets target window: window_locked = True
def is_game_window_active(self):     # Foreground window contains target_window_title?
def activate_game_window(self):      # Restore & bring game window to foreground
@Slot(result='QVariant')
def getWindowList(self):             # Visible windows as dicts for QML
```

### Window Check in Hotkeys

```python
if self.window_locked and self.target_window_title.strip():
    hwnd = win32gui.GetForegroundWindow()
    if self.target_window_title.lower() not in win32gui.GetWindowText(hwnd).lower():
        return
```

### WindowManager (backend/window_manager.py)

```python
class WindowManager:
    check_window() -> bool           # Is game window active
    activate_window() -> bool        # Activate game window
    get_window_list() -> list[dict]  # Visible windows
    set_window_lock(locked, title)   # Lock/unlock binding
```

### Settings

| Setting | Type | Default |
|---------|------|---------|
| `window_locked` | bool | `False` |
| `target_window_title` | str | `""` |
| `window_opacity` | float | `1.0` |
