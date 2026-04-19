# Backend Managers — snbld resvap

> English reference for all 13 backend managers in the snbld resvap project (MMORPG Perfect World macro system)

---

## Architecture Overview

Backend uses the **Delegate pattern** — all `Backend` method calls delegate to corresponding managers:

```python
# Backend delegates to MacroCrud
def delete_macro(self, name):
    if self.macro_crud:
        self.macro_crud.delete_macro(name)
```

This ensures QML remains unchanged while backend logic is modularized.

---

## New Modules (Integrated)

### 1. ActivationManager

**File:** `backend/activation_manager.py`

**Purpose:** Manages program activation, heartbeat, subscription, and copy protection.

**Key Methods:**

| Method | Description |
|--------|-------------|
| `check_activation_on_startup()` | Validates activation key on app start |
| `start_heartbeat()` | Starts periodic heartbeat to server |
| `activate_with_key(key)` | Activates program with subscription key |
| `verify_copy_protection()` | Prevents unauthorized copying |
| `check_updates_async()` | Checks for updates in background |

**Backend Delegation:**

```python
def activateProgram(self, key):
    return self.activation_manager.activate_with_key(key)

def isProgramActivated(self):
    return self.activation_manager.is_activated
```

### 2. MacroDispatcher

**File:** `backend/macros_dispatcher.py`

**Purpose:** Single entry point for macro validation and execution. Manages priority queue, cooldown cache, and cast locking.

**Key Components:**

| Component | Description |
|-----------|-------------|
| `cast_lock_until` | Timestamp until cast is locked |
| `macro_queue` | Priority queue (deque) |
| `cooldown_cache` | Cache {name: end_time}, TTL 30s |
| `macro_stats` | Per-macro launch statistics |

**Key Methods:**

| Method | Description |
|--------|-------------|
| `request_macro(macro, priority=5)` | Validates and queues/launches macro |
| `_process_queue()` | Background thread processing queue |
| `_check_cooldown_cached(name)` | Fast cooldown check (~0.05ms) |
| `_lock_cast(duration)` | Blocks new casts for duration |

**Priority Levels:**
- 1-3: Critical (shields, healing) — added to queue when blocked
- 5: Normal (attacks)
- 10: Background (buffs)

**Backend Delegation:**

```python
def request_macro(self, macro, priority=5):
    return self.dispatcher.request_macro(macro, priority)
```

### 3. SettingsManager

**File:** `backend/settings_manager.py`

**Purpose:** Loads, saves, and validates all application settings.

**Key Methods:**

| Method | Description |
|--------|-------------|
| `get(key, default)` | Get setting value |
| `set(key, value)` | Set setting with validation |
| `save()` | Persist to settings.json |
| `add_listener(key, callback)` | Register change listener |
| `_convert_settings_types()` | Type conversion on load |

**Backend Delegation:**

```python
def set_setting(self, key, value):
    # Validates via ALLOWED_SETTINGS
    self.settings_manager.set(key, value)
    self.settings_applier.apply_setting(key, value)
    self.settingsChanged.emit()
```

### 4. OCRManager

**File:** `backend/ocr_manager.py`

**Purpose:** Manages Tesseract OCR recognition for distance monitoring (mob/player targets).

**Signals:**
- `data_updated(target_type, distance, numbers)` — distance recognized
- `area_selected(target_type, area)` — area selected
- `test_result(target_type, result)` — test result

**Key Methods:**

| Method | Description |
|--------|-------------|
| `set_area(target_type, area)` | Set OCR region |
| `get_area(target_type)` | Get current OCR region |
| `test_area(target_type)` | Test area recognition |
| `start()` | Start OCR monitoring |
| `stop()` | Stop OCR monitoring |

**Backend Delegation:**

```python
def start_ocr(self):
    self.ocr_manager.start()

def stop_ocr(self):
    self.ocr_manager.stop()
```

### 5. LoggerManager

**File:** `backend/logger_manager.py`

**Purpose:** Singleton logging system with categorized loggers.

**Categories:** `macros`, `errors`, `ocr`, `network`, `settings`, `debug`, `shiboken`

**Key Methods:**

| Method | Description |
|--------|-------------|
| `get_logger(category)` | Get logger by category |

**Usage:**

```python
from backend.logger_manager import get_logger
log = get_logger('macros')
log.info("Macro started: %s", name)
```

---

## Existing Modules

### 6. ProfileManagerExt

**File:** `backend/profile_manager_ext.py`

**Purpose:** Manages profiles, macro serialization, and profile operations.

**Key Methods:**

| Method | Description |
|--------|-------------|
| `load_profile(name)` | Load profile from JSON |
| `save_profile(name)` | Save profile to JSON |
| `create_profile(name)` | Create new profile |
| `rename_profile(old, new)` | Rename profile |
| `delete_profile(name)` | Delete profile |
| `get_profile_list()` | List all profiles |
| `_create_macro_from_dict(data)` | Deserialize macro |
| `_macro_to_dict(macro)` | Serialize macro |

### 7. CastbarDetector

**File:** `backend/castbar_detector.py`

**Purpose:** Detects and calibrates castbar visibility by pixel color using `mss`.

**Key Methods:**

| Method | Description |
|--------|-------------|
| `is_castbar_visible()` | Check if castbar is visible |
| `capture_castbar_color_at(x, y, size)` | Capture pixel color at point |
| `start_calibration()` | Start calibration mode |
| `stop_calibration()` | Stop calibration mode |

**Implementation:**
- Captures 3x3 pixel area around `castbar_point`
- Compares RGB sum difference against `castbar_threshold`
- Uses `mss` (not GDI GetPixel) — 10-50x faster
- Caching with 1ms TTL

### 8. WindowSelector

**File:** `backend/window_selector.py`

**Purpose:** Window selection and game window binding.

**Key Methods:**

| Method | Description |
|--------|-------------|
| `select_window_from_list()` | Open window selection dialog |
| `set_target_window(title)` | Set target window title |
| `activate_game_window()` | Activate/restore game window |
| `is_game_window_active()` | Check if game window is active |
| `save_window_position(x, y)` | Save window position |
| `get_window_position()` | Get saved window position |

### 9. SettingsApplier

**File:** `backend/settings_applier.py`

**Purpose:** Applies setting changes to macros and subsystems.

**Key Methods:**

| Method | Description |
|--------|-------------|
| `recalculate_macro_delays()` | Recalculate step delays based on ping |
| `apply_setting(key, value)` | Apply single setting to macros |
| `apply_console_visibility(show)` | Show/hide console |

**Settings Applied to Macros:**
- `swap_key_chant` → Step 1 (swap to chant gear)
- `swap_key_pa` → Step 3 (swap to PA gear)
- `global_step_delay` → Steps 2-3 delay
- `first_step_delay` → Step 1 delay
- `ocr_scale/psm/use_morph` → Restart OCR
- `window_locked/target_window_title` → Update all macros

### 10. BuffManager

**File:** `backend/buff_manager.py`

**Purpose:** Manages active buffs and cast time recalculation.

**Key Methods:**

| Method | Description |
|--------|-------------|
| `add_buff(buff_id, name, duration, channeling_bonus, icon)` | Add active buff |
| `remove_buff(buff_id)` | Remove buff |
| `get_buff(buff_id)` | Get buff by ID |
| `get_all_buffs()` | Get all buffs |
| `get_active_buffs_list()` | Get list for UI |
| `cleanup_expired()` | Remove expired buffs |

**Cast Time Calculation:**

```python
def get_actual_cast_time(base_cast_time):
    bonus_total = self.get_current_channeling_bonus()
    if bonus_total > 0:
        return base_cast_time * 100.0 / (100.0 + bonus_total)
    return base_cast_time
```

### 11. HotkeyManager

**File:** `backend/hotkey_manager.py`

**Purpose:** Hotkey registration and unregistration.

**Key Methods:**

| Method | Description |
|--------|-------------|
| `register(hotkey, callback, check_window, check_global_stop, suppress)` | Register hotkey |
| `unregister(hotkey)` | Unregister hotkey |
| `unregister_all()` | Unregister all hotkeys |
| `is_registered(hotkey)` | Check if hotkey is registered |

**Backend Delegation:**

```python
def register_hotkey(self, hotkey, callback, check_window=True, 
                    check_global_stop=True, suppress=True):
    self.hotkey_manager.register(hotkey, callback, check_window, 
                                  check_global_stop, suppress)
```

### 12. WindowManager

**File:** `backend/window_manager.py`

**Purpose:** Window validation and activation.

**Key Methods:**

| Method | Description |
|--------|-------------|
| `check_window()` | Check if game window is active |
| `activate_window()` | Activate game window |
| `get_window_list()` | Get list of visible windows |
| `set_window_lock(locked, title)` | Lock/unlock window binding |

### 13. MacroCrud (Legacy from MacrosManager)

**File:** `backend/macro_crud.py`

**Purpose:** CRUD operations for all macro types.

**Key Methods:**

| Method | Description |
|--------|-------------|
| `delete_macro(name)` | Delete macro |
| `edit_macro(name)` | Open macro for editing |
| `create_simple_macro(name, hotkey, steps)` | Create simple macro |
| `create_zone_macro(name, hotkey, zone_rect, ...)` | Create zone macro |
| `create_skill_macro(name, hotkey, skill_id, ...)` | Create skill macro |
| `create_buff_macro(name, hotkey, buff_id, ...)` | Create buff macro |
| `update_*_macro(old, new, ...)` | Update any macro type |
| `save_macro(macro_dict)` | Universal save method |
| `get_macro_for_edit()` | Get macro dict for editing |
| `set_macro_for_edit(macro_dict)` | Set macro for editing |

**Backend Delegation:**

```python
def create_simple_macro_with_params(self, name, hotkey, steps):
    if self.macro_crud:
        return self.macro_crud.create_simple_macro(name, hotkey, steps)

def delete_macro(self, name):
    if self.macro_crud:
        self.macro_crud.delete_macro(name)
```

---

## Summary Table

| Manager | File | Purpose |
|---------|------|---------|
| ActivationManager | `backend/activation_manager.py` | Activation, heartbeat, subscription |
| MacroDispatcher | `backend/macros_dispatcher.py` | Priority queue, cooldowns, cast lock |
| SettingsManager | `backend/settings_manager.py` | Settings load/save/validation |
| OCRManager | `backend/ocr_manager.py` | OCR management |
| LoggerManager | `backend/logger_manager.py` | Logging system |
| ProfileManagerExt | `backend/profile_manager_ext.py` | Profiles, serialization |
| CastbarDetector | `backend/castbar_detector.py` | Castbar detection |
| WindowSelector | `backend/window_selector.py` | Window selection |
| SettingsApplier | `backend/settings_applier.py` | Applying settings to macros |
| BuffManager | `backend/buff_manager.py` | Buffs management |
| HotkeyManager | `backend/hotkey_manager.py` | Hotkey management |
| WindowManager | `backend/window_manager.py` | Window management |
| MacroCrud | `backend/macro_crud.py` | CRUD operations |
