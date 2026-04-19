# Settings Reference Table

> **Project:** snbld resvap — MMORPG Perfect World macro system (Asgard server)
> **Source:** `ALLOWED_SETTINGS` in `qml_main.py`, `DEFAULTS` in `backend/settings_manager.py`

---

## ALLOWED_SETTINGS

All settings are defined in `ALLOWED_SETTINGS` in `qml_main.py` as `(type, min, max)` tuples. Values come from QML as strings and are converted by `SettingsManager._convert_settings_types()`.

### Reswap Settings

| Key | Type | Min | Max | Default | Description |
|-----|------|-----|-----|---------|-------------|
| `swap_key_chant` | str | — | — | `"e"` | Key for swapping to chant equipment |
| `swap_key_pa` | str | — | — | `"e"` | Key for swapping to physical attack equipment |

### Cast Settings

| Key | Type | Min | Max | Default | Description |
|-----|------|-----|-----|---------|-------------|
| `base_channeling` | int | 0 | 1000 | `91` | Base channeling bonus percentage |
| `cooldown_margin` | float | 0.0 | 5.0 | `0.3` | Extra margin added after cooldown expiry (seconds) |
| `cast_lock_margin` | float | 0.0 | 2.0 | `0.45` | Margin added to cast lock duration (seconds) |
| `castbar_enabled` | bool | — | — | `False` | Enable cast bar detection by pixel color |
| `castbar_point` | str | — | — | `"1081,1337"` | Screen coordinates of cast bar detection point (x,y) |
| `castbar_threshold` | int | 1 | 100 | `70` | Color difference threshold for cast bar detection (RGB sum) |
| `castbar_color` | list | — | — | `[94, 123, 104]` | Reference RGB color of the cast bar |
| `castbar_size` | int | 1 | 10 | `5` | Size of pixel capture area around castbar_point (NxN) |

### Movement Settings

| Key | Type | Min | Max | Default | Description |
|-----|------|-----|-----|---------|-------------|
| `movement_delay_enabled` | bool | — | — | `True` | Enable delay after movement stops before casting |
| `movement_delay_ms` | int | 0 | 5000 | `300` | Delay after movement stops (milliseconds) |
| `check_distance` | bool | — | — | `True` | Enable distance checking via OCR before casting |
| `use_castbar_detection` | bool | — | — | `False` | Use cast bar detection instead of fixed delay after approach |
| `distance_tolerance` | float | 0.0 | 10.0 | `1.0` | Acceptable distance deviation from target (meters) |

### OCR Settings

| Key | Type | Min | Max | Default | Description |
|-----|------|-----|-----|---------|-------------|
| `ocr_scale` | int | 1 | 100 | `10` | Image scale factor for OCR preprocessing |
| `ocr_psm` | int | 6 | 13 | `10` | Tesseract page segmentation mode |
| `ocr_use_morph` | bool | — | — | `True` | Use morphological preprocessing (erosion + closing) |
| `target_interval` | float | 0.1 | 1.0 | `0.2` | Interval between OCR reads per area (seconds) |

### Network Settings

| Key | Type | Min | Max | Default | Description |
|-----|------|-----|-----|---------|-------------|
| `process_name` | str | — | — | `"ElementClient_x64.exe"` | Game client process name for ping detection |
| `server_ip` | str | — | — | `"147.45.96.78"` | Game server IP address for ICMP ping |
| `ping_auto` | bool | — | — | `True` | Automatically measure ping via PingMonitor thread |
| `ping_check_interval` | int | 1 | 300 | `5` | Interval between ping checks (seconds) |
| `average_ping` | int | 0 | 1000 | `29` | Cached average ping value (used when ping_auto is off) |

### Delays Settings

| Key | Type | Min | Max | Default | Description |
|-----|------|-----|-----|---------|-------------|
| `global_step_delay` | float | 0 | 500 | `15.0` | Default delay between macro steps (ms, used when use_ping_delays=False) |
| `first_step_delay` | int | 0 | 1000 | `90` | Delay before the first macro step (ms) |
| `use_fixed_delays` | bool | — | — | `True` | Use fixed delay values instead of ping-based delays |
| `use_ping_delays` | bool | — | — | `False` | Calculate delays dynamically based on current ping |

### Hotkeys Settings

| Key | Type | Min | Max | Default | Description |
|-----|------|-----|-----|---------|-------------|
| `start_all_hotkey` | str | — | — | `"-"` | Hotkey to start/unlock all macros |
| `stop_all_hotkey` | str | — | — | `"="` | Hotkey to stop/lock all macros |

### OCR Areas Settings

| Key | Type | Min | Max | Default | Description |
|-----|------|-----|-----|---------|-------------|
| `mob_area` | str/list | — | — | `"1266,32,1303,56"` | Screen region for mob target OCR (x1,y1,x2,y2) |
| `player_area` | str/list | — | — | `[1271, 16, 1294, 32]` | Screen region for player target OCR (x1,y1,x2,y2) |

### Window Settings

| Key | Type | Min | Max | Default | Description |
|-----|------|-----|-----|---------|-------------|
| `window_opacity` | float | 0.1 | 1.0 | `1.0` | Application window opacity (transparency) |
| `window_locked` | bool | — | — | `False` | Lock macro execution to specific game window |
| `target_window_title` | str | — | — | `""` | Title of the target game window to bind to |

### Appearance Settings

| Key | Type | Min | Max | Default | Description |
|-----|------|-----|-----|---------|-------------|
| `accent_color` | str | — | — | `"#fd79a8"` | UI accent color (hex format) |

### Buff 8004 Settings

| Key | Type | Min | Max | Default | Description |
|-----|------|-----|-----|---------|-------------|
| `buff_8004_click_point` | str | — | — | `"0,0"` | Click coordinates for buff ID 8004 (x,y) |

### Logging Settings

| Key | Type | Min | Max | Default | Description |
|-----|------|-----|-----|---------|-------------|
| `log_level_macros` | str | — | — | `"INFO"` | Log level for macro execution logs |
| `log_level_errors` | str | — | — | `"ERROR"` | Log level for error logs |
| `log_level_ocr` | str | — | — | `"DEBUG"` | Log level for OCR logs |
| `log_level_network` | str | — | — | `"INFO"` | Log level for network/ping logs |
| `log_level_settings` | str | — | — | `"INFO"` | Log level for settings change logs |
| `log_level_debug` | str | — | — | `"DEBUG"` | Log level for debug logs |
| `log_level_shiboken` | str | — | — | `"WARNING"` | Log level for PySide6/Shiboken warnings |

---

## Type Conversion Rules

Values arrive from QML as **strings**. `SettingsManager._convert_settings_types()` converts them:

| Setting Type | Conversion Logic |
|--------------|-----------------|
| **int** | `int(value)` — fallback to default on `ValueError`/`TypeError` |
| **float** | `float(value)` — fallback to default on `ValueError`/`TypeError` |
| **bool** | `value.lower() in ("true", "1", "yes")` — fallback to `bool(value)` |
| **str** | No conversion, used as-is |
| **list** (castbar_color) | `"R,G,B"` → `[int(R), int(G), int(B)]` — fallback to default on failure |
| **str/list** (mob_area, player_area) | Accepted as either `"x1,y1,x2,y2"` string or `[x1, y1, x2, y2]` list |

**Settings converted to int:** `base_channeling`, `movement_delay_ms`, `ocr_scale`, `first_step_delay`, `castbar_threshold`

**Settings converted to float:** `cooldown_margin`, `cast_lock_margin`, `castbar_swap_delay`, `global_step_delay`

**Settings converted to bool:** `use_castbar_detection`, `castbar_enabled`, `movement_delay_enabled`, `check_distance`, `ocr_use_morph`, `ping_auto`

---

## Validation Flow

```
QML calls Backend.set_setting(key, value)
    │
    ├─ 1. Check key exists in ALLOWED_SETTINGS
    │      └─ Unknown key → reject
    │
    ├─ 2. Convert type (int/float/bool/str/list)
    │      └─ Conversion failure → fallback to DEFAULTS value
    │
    ├─ 3. Validate range (min, max from ALLOWED_SETTINGS)
    │      └─ Out of range → reject
    │
    ├─ 4. Special warnings (e.g. ocr_scale < 5, castbar_threshold < 50)
    │
    ├─ 5. Apply to macros via SettingsApplier.apply_setting()
    │      ├─ swap_key_chant → update step 1 in all macros
    │      ├─ swap_key_pa → update step 3 in all macros
    │      ├─ global_step_delay → update step 2/3 delays
    │      ├─ first_step_delay → update step 1 delay
    │      ├─ ocr_scale/psm/use_morph → restart OCR thread
    │      └─ window_locked/target_window_title → update all macros
    │
    ├─ 6. Save to settings.json AND current profile
    │
    └─ 7. Emit settingsChanged signal → QML UI updates
```

**Atomicity:** The operation is atomic — either all steps succeed or nothing changes.

**Ping-based delay recalculation:** When `use_ping_delays=True` and ping updates, `recalculate_macro_delays()` is called:
- `first_step = 30 + ping_compensation`
- `step_delay = ping_compensation`
- `ping_compensation = min(game_ping / 1000 * 0.7 + 0.02, 0.3)`
- where `game_ping = average_ping * 2.0` (Perfect World multiplier)
