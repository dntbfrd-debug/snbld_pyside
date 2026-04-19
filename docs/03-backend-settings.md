# Backend Settings — snbld resvap

Settings management in the QML version of snbld resvap, a macro system for MMORPG Perfect World (Asgard server).

## 1. `set_setting(key, value)` — Full Validation Flow

Sets a setting value with complete validation. Atomic operation: either everything applies or nothing.

```python
@Slot(str, str)
def set_setting(self, key, value):
```

### Validation Pipeline

| Step | Check | Action on Failure |
|------|-------|-------------------|
| 1 | Key exists in `ALLOWED_SETTINGS` | Warning notification, return |
| 2 | Type conversion (`int`, `float`, `bool`, `list`, `str`) | Warning notification, return |
| 3 | Range check (`min_val`, `max_val`) | Clamp to nearest valid value |
| 4 | Special warnings (`ocr_scale < 5`, `castbar_threshold < 50`) | Warning notification, continue |

### Type Conversion Rules

```python
int:     value = int(float(value))    # "10.0" -> 10
float:   value = float(value)
bool:    value = value.lower() in ("true", "1", "yes")
list:    value = [int(x) for x in value.split(',')]   # "255,128,0" -> [255, 128, 0]
str:     no conversion
```

### Apply Flow

After validation, settings are applied differently based on key:

```python
# castbar_color / castbar_threshold -> direct attribute + macros
elif key in (bool, toggle keys) -> _settings + PingMonitor control + recalculate
elif key in (use_ping_delays, use_fixed_delays) -> recalculate_macro_delays()
else -> _settings + apply_settings_to_macros()

# Single save at the end
self.save_settings()  # settings.json + current profile
```

## 2. `apply_settings_to_macros(key, value)` — How Settings Affect Macros

Applies setting changes to all existing macros in `self._macros`.

```python
def apply_settings_to_macros(self, key, value):
```

### Key-to-Macro Mappings

| Setting Key | Affected Step | What Changes |
|---|---|---|
| `swap_key_chant` | Step 1 | Keyboard key for chant swap (delay preserved) |
| `swap_key_pa` | Step 3 | Keyboard key for PA swap (delay preserved) |
| `global_step_delay` | Steps 2, 3 | Delay value for skill and PA swap steps |
| `first_step_delay` | Step 1 | Delay value for chant swap step |
| `cooldown_margin` | Runtime | Read from settings at execution time |
| `movement_delay_enabled` | Runtime | Applied at macro execution |
| `movement_delay_ms` | Runtime | Applied at macro execution |
| `check_distance` | Runtime | Applied at macro execution |
| `ocr_scale / ocr_psm / ocr_use_morph` | OCR | Restart OCR thread with new settings |
| `window_locked` | All macros | Update `self._window_locked` |
| `target_window_title` | All macros | Update `self._target_window_title` |
| `ping_auto / process_name` | Ping | Restart PingMonitor |
| `start_all_hotkey / stop_all_hotkey` | Hotkeys | Re-register all hotkeys |

### Step Update Example

```python
# swap_key_chant: update only the key, preserve delay
if step[0] == "key":
    delay = step[2] if len(step) > 2 else 100
    macro.steps[0] = ["key", value, delay]

# global_step_delay: update delay for steps 2 and 3
macro.steps[1] = [step[0], step[1], float(value)]
macro.steps[2] = [step3[0], step3[1], float(value)]
```

After changes, `self.macrosChanged.emit()` signals QML to update.

## 3. `recalculate_macro_delays()` — Ping-Based Delay Recalculation

Recalculates delays in macro steps when switching modes or ping updates.

```python
def recalculate_macro_delays(self):
```

### Delay Calculation Modes

```python
# Auto mode (use_ping_delays=True)
ping_comp = self.get_ping_compensation() * 1000  # convert to ms
first_step_delay = round(30 + ping_comp)          # base 30ms + compensation
step_delay = round(ping_comp)                      # compensation only

# Fixed mode (use_ping_delays=False)
first_step_delay = self._settings.get("first_step_delay", 100)
step_delay = self._settings.get("global_step_delay", 20)
```

### Ping Compensation Formula

```python
icmp_ping = self._settings.get("average_ping", 30)
game_ping = icmp_ping * 2.0                        # ICMP -> game multiplier
compensation = min(game_ping / 1000 * 0.7 + 0.02, 0.3)  # capped at 0.3s
```

**Example (ping 37ms):**
- Game ping: 37 x 2.0 = 74ms
- Compensation: 74 / 1000 x 0.7 + 0.02 = 0.072s = 72ms
- Step 1: 30 + 72 = **102ms**
- Steps 2-3: **72ms**

### Step Update Logic

Only macros with 3+ steps are updated:

```python
for macro in self._macros:
    if hasattr(macro, 'steps') and len(macro.steps) >= 3:
        # Step 1: chant swap
        if macro.steps[0][0] == "key":
            macro.steps[0] = ["key", macro.steps[0][1], first_step_delay]
        # Step 2: skill
        if macro.steps[1][0] in ("key", "left", "right"):
            macro.steps[1] = [macro.steps[1][0], macro.steps[1][1], step_delay]
        # Step 3: PA swap
        if macro.steps[2][0] == "key":
            macro.steps[2] = ["key", macro.steps[2][1], step_delay]

self._update_macros_dicts()
```

### When Recalculation is Triggered

- `use_ping_delays` setting changed
- `use_fixed_delays` setting changed
- Ping updated (via `on_ping_updated` when `use_ping_delays=True`)
