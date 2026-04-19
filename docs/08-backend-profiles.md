# Backend: Profiles System

## Overview

The profiles system allows users to save and load complete configurations including settings, macros, and window binding. Managed by `ProfileManager` in `backend/profile_manager_ext.py`.

## Profile Storage

Profiles are stored as JSON files in the `profiles/` directory:

```
profiles/
  Default.json
  PvP.json
  Farming.json
```

### Profile Format

```json
{
  "settings": { ... },
  "macros": [ ... ],
  "window_locked": false,
  "target_window_title": ""
}
```

| Field | Type | Description |
|-------|------|-------------|
| `settings` | dict | All application settings (ALLOWED_SETTINGS keys) |
| `macros` | list | Serialized macro objects with type, steps, hotkeys, etc. |
| `window_locked` | bool | Whether the window is locked to the game |
| `target_window_title` | str | Title of the target game window |

## API Reference

### load_profile(name)

Loads a profile with full state restoration:

```python
def load_profile(self, name: str) -> bool
```

**Flow:**
1. Saves current profile if different from target
2. Loads settings from profile into `backend._settings`
3. Applies settings to all backend attributes via `_apply_settings_to_attributes()`
4. Deserializes macros from profile into `backend._macros`
5. Loads window binding (`window_locked`, `target_window_title`)
6. Updates `backend._current_profile` and `last_active_profile` in settings
7. Saves `settings.json`
8. Emits signals: `profileChanged`, `profilesChanged`, `settingsChanged`
9. Re-registers all hotkeys via `register_all_hotkeys()`

### _apply_settings_to_attributes()

Applies settings from `backend._settings` to backend attributes:

```python
def _apply_settings_to_attributes(self):
    # Castbar
    self.backend.castbar_enabled = self.backend._settings.get("castbar_enabled", False)
    self.backend.castbar_point = self.backend._settings.get("castbar_point", "1273,1005")
    self.backend.castbar_color = self.backend._load_castbar_color(...)
    self.backend.castbar_threshold = int(self.backend._settings.get("castbar_threshold", 70))

    # OCR Areas
    self.backend.mob_area = self.backend._settings.get("mob_area", ...)
    self.backend.player_area = self.backend._settings.get("player_area", ...)

    # Window
    self.backend._window_locked = self.backend._settings.get("window_locked", False)
    self.backend._target_window_title = self.backend._settings.get("target_window_title", "")

    # Ping
    self.backend._ping = self.backend._settings.get("average_ping", 30)

    # Distance
    self.backend._target_distance = None  # Updated from OCR
```

Emits `settingsChanged` and `pingUpdated` after applying.

### create_profile(name)

Creates a new profile with current settings but empty macros:

```python
def create_profile(self, name: str) -> bool
```

- Cleans name using `_clean_name()` (removes invalid Windows characters)
- Checks for duplicates
- Creates profile with current settings, empty macros list
- Switches to the new profile immediately
- Emits `profileChanged`, `profilesChanged`, `settingsChanged`

### save_profile(name=None)

Saves the current profile:

```python
def save_profile(self, name: str = None) -> bool
```

- If `name` is None, uses `backend._current_profile`
- Serializes all macros via `_macro_to_dict()`
- Saves settings, macros, window_locked, target_window_title
- Updates `backend._current_profile`

### rename_profile(old_name, new_name)

Renames a profile file:

```python
def rename_profile(self, old_name: str, new_name: str) -> bool
```

- Cleans new name, checks for duplicates
- Renames file on disk via `os.rename()`
- Updates `backend._current_profile` if it was the renamed profile

### delete_profile(name=None)

Deletes a profile:

```python
def delete_profile(self, name: str = None) -> bool
```

- If `name` is None, uses `backend._current_profile`
- Removes file from disk
- Clears `backend._current_profile` if it was the deleted profile

### get_profile_list()

Returns list of all profile names:

```python
def get_profile_list(self) -> list[str]
```

- Scans `profiles/` directory for `*.json` files
- Returns list of names (without `.json` extension)

## Auto-Save

Profiles are automatically saved on any change:

- **Settings change** → `set_setting()` saves to both `settings.json` and current profile
- **Macro change** → Current profile is saved
- **Profile switch** → Previous profile is auto-saved before loading new one
- **App shutdown** → Last active profile is saved

## Startup Loading

On application start:
1. Loads `settings.json`
2. Reads `last_active_profile` from settings
3. Loads the profile via `load_profile()`
4. All settings, macros, and window binding are restored

## Signals

| Signal | Emitted When |
|--------|-------------|
| `profileChanged` | Profile is loaded, created, renamed, or deleted |
| `profilesChanged` | Profile list changes (create, rename, delete) |

## Properties

| Property | Type | Description |
|----------|------|-------------|
| `current_profile` | str | Name of the currently active profile |
| `profiles_list` | list | List of all available profile names |
