# Backend — Macro Management

> Macro management API for the snbld resvap project (Perfect World MMORPG macro system).

## Overview

The `Backend` class delegates macro operations to `MacroCrud` (backend/macro_crud.py) and `MacroDispatcher` (backend/macros_dispatcher.py). QML calls Backend slots — full backward compatibility is maintained.

---

## Starting and Stopping Macros

### Single Macro

```python
@Slot(str)
def start_macro(name):
    """Start a macro via the dispatcher (priority 5)."""

@Slot(str)
def stop_macro(name):
    """Stop a running macro."""
```

### All Macros

```python
@Slot()
def start_all_macros():
    """
    Unlock ALL macros — enable hotkeys.
    - Sets global_stopped = False
    - Starts OCR if areas are configured
    - Re-registers all hotkeys with suppress=True
    - Does NOT start macros immediately — they wait for hotkey press
    """

@Slot()
def stop_all_macros():
    """
    Stop ALL macros.
    - Stops OCR
    - Stops all macros (join timeout 3s)
    - Re-registers all hotkeys with suppress=False
    """
```

---

## Deleting and Opening for Edit

```python
@Slot(str)
def delete_macro(name):
    """Delete a macro by name. Delegated to MacroCrud."""

@Slot(str)
def edit_macro(name):
    """Open a macro for editing. Loads it into macro_for_edit property."""
```

---

## Creating Macros

All creation methods are `@Slot` decorated and delegate to `MacroCrud`.

### Simple Macro

```python
@Slot(str, str, list)
def create_simple_macro_with_params(name, hotkey, steps):
    """
    Create a simple macro — sequential key presses/clicks.

    Args:
        name: Macro name (unique identifier)
        hotkey: Hotkey string (e.g. "ctrl+e", "f1")
        steps: List of step dicts (keys, clicks, delays)
    """
```

### Zone Macro

```python
@Slot(str, str, list, list, str, int)
def create_zone_macro_with_params(name, hotkey, zone_rect, steps, trigger, poll_interval_ms):
    """
    Create a zone macro — triggers when mouse clicks inside a screen area.

    Args:
        name: Macro name
        hotkey: Hotkey string
        zone_rect: [x1, y1, x2, y2] — screen rectangle
        steps: List of step dicts
        trigger: Trigger type (e.g. "click")
        poll_interval_ms: Mouse check interval in milliseconds
    """
```

### Skill Macro

```python
@Slot(str, str, str, list, str, float, float, float, float, list)
def create_skill_macro_with_params(name, hotkey, skill_id, steps, skill_hotkey,
                                    cooldown, skill_range, cast_time, castbar_swap_delay, zone_rect):
    """
    Create a skill macro — skill casting with cooldown, distance, and castbar checks.

    Args:
        name: Macro name
        hotkey: Hotkey string
        skill_id: Skill identifier from database
        steps: List of step dicts
        skill_hotkey: In-game skill hotkey
        cooldown: Skill cooldown in seconds
        skill_range: Maximum cast distance
        cast_time: Base cast time in seconds
        castbar_swap_delay: Delay after castbar detection for reswap
        zone_rect: Optional [x1, y1, x2, y2] for zone restriction
    """
```

### Buff Macro

```python
@Slot(str, str, str, list, float, int, list)
def create_buff_macro_with_params(name, hotkey, buff_id, steps, duration, channeling_bonus, zone_rect):
    """
    Create a buff macro — periodic buff application with channeling bonus.

    Args:
        name: Macro name
        hotkey: Hotkey string
        buff_id: Buff identifier from database
        steps: List of step dicts
        duration: Buff duration in seconds
        channeling_bonus: Channeling bonus percentage
        zone_rect: Optional [x1, y1, x2, y2] for zone restriction
    """
```

---

## Updating Macros

Each update method takes `old_name` and `new_name` to support renaming.

```python
@Slot(str, str, str, list)
def update_simple_macro(old_name, new_name, hotkey, steps):
    """Update a simple macro."""

@Slot(str, str, str, list, list, str, int)
def update_zone_macro(old_name, new_name, hotkey, zone_rect, steps, trigger, poll_interval_ms):
    """Update a zone macro."""

@Slot(str, str, str, list, str, float, float, float, float, list)
def update_skill_macro(old_name, new_name, hotkey, skill_id, steps, skill_hotkey,
                       cooldown, skill_range, cast_time, castbar_swap_delay, zone_rect):
    """Update a skill macro."""

@Slot(str, str, str, list, float, int, list)
def update_buff_macro(old_name, new_name, hotkey, buff_id, steps, duration, channeling_bonus, zone_rect):
    """Update a buff macro."""
```

---

## Edit Workflow (set / get / clear / save)

The edit workflow uses a temporary `macro_for_edit` property bound to QML.

```python
@Slot(dict)
def set_macro_for_edit(macro_dict):
    """Set a macro dictionary for editing. Populates macro_for_edit property."""

@Property(dict, notify=macrosChanged)
def macro_for_edit():
    """Get the macro dictionary currently being edited. Readable from QML."""

@Slot()
def clear_macro_for_edit():
    """Clear the macro_for_edit property after editing is complete."""

@Slot(dict)
def save_macro(macro_dict):
    """
    Save a macro from a dictionary (after editing).
    Creates a new macro or updates an existing one.
    Delegated to MacroCrud for type-specific handling.
    """
```

### Typical Edit Flow

1. User clicks "Edit" → `edit_macro(name)` loads macro into `macro_for_edit`
2. QML form binds to `Backend.macro_for_edit` for display
3. User modifies fields in QML
4. User clicks "Save" → QML calls `Backend.save_macro(modified_dict)`
5. Backend clears the edit state → `clear_macro_for_edit()`

---

## Architecture Note

All macro operations follow the **delegation pattern**:

```
QML → Backend.start_macro("attack") → MacroDispatcher.request_macro(macro)
QML → Backend.delete_macro("old")   → MacroCrud.delete_macro("old")
QML → Backend.save_macro(data)      → MacroCrud.save_macro(data)
```

QML code remains unchanged — full backward compatibility is preserved after refactoring.
