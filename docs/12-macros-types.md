# Macros Types — snbld resvap

System of macros for MMORPG Perfect World (Asgard server).

---

## 1. Macro Types

### SimpleMacro
A simple sequence of key presses and/or mouse clicks executed in order.

```python
SimpleMacro(name, steps, app, hotkey)
# steps: [("key", "e", 100), ("left", "", 20), ("key", "e", 20)]
```

### ZoneMacro
Triggers when the user clicks inside a defined screen rectangle. Continuously polls for clicks in the zone.

```python
ZoneMacro(name, zone_rect, steps, app, trigger, poll_interval, hotkey, ...)
# zone_rect: (x1, y1, x2, y2)
# trigger: "left_click"
# poll_interval: 0.01 (10 ms)
```

### SkillMacro
Executes a skill with cooldown check, distance check, and cast-bar detection. Supports auto-approach to target and equipment reswap.

```python
SkillMacro(name, steps, app, hotkey, skill_id, skill_hotkey,
           cooldown, skill_range, cast_time, castbar_swap_delay, zone_rect, ...)
```

### BuffMacro
Applies a buff with ping-compensated delays and channeling bonus that reduces cast time.

```python
BuffMacro(name, steps, app, buff_id, duration, channeling_bonus, hotkey, icon, zone_rect)
# channeling_bonus: casting speed bonus (%)
# duration: buff duration (seconds)
# zone_rect: optional activation zone
```

#### Buff Click Calibration (Светлая опека духов — ID 8004)

Before executing macro steps, BuffMacro can perform a click at calibrated coordinates:

```python
# In BuffMacro._run():
# 1. Check buff_8004_click_point setting
# 2. If set (not "0,0"), click at coordinates BEFORE macro steps
# 3. Small delay (0.1s) after click
# 4. Continue with normal macro steps
```

**Calibration flow:**
1. User opens BuffEditForm.qml for a buff macro
2. Clicks "Калибровать" button → `backend.startBuffCalibration()`
3. `BuffCalibrationDialog` opens, user clicks on screen point
4. Coordinates saved to `buff_8004_click_point` setting (format: "x,y")
5. On next macro execution, click is performed at these coordinates

**Backend API:**
- `startBuffCalibration()` — opens calibration dialog
- `onBuffPointCaptured(point)` — saves point and emits signal
- `getBuffClickPoint()` — returns current calibration point
- `performBuffClick()` — test click at calibrated coordinates

---

## 2. Base Class Structure

All macro types inherit from the base `Macro` class (`_macros_original.py`):

```
Macro (base)
├── name, hotkey, steps, app, running, stop_event
├── zone_rect          # optional activation zone
├── _check_window()    # verify game window is active
├── _press_key()       # send key via SendInput
├── _click_mouse()     # send mouse click via SendInput
├── _run_loop()        # main execution loop
└── stop()             # signal macro to stop
    │
    ├── SimpleMacro — inherits _run_loop as-is
    ├── ZoneMacro — adds MouseClickMonitor integration
    ├── SkillMacro — overrides _run_loop with distance/cast/CD checks
    └── BuffMacro — overrides _run_loop with channeling_bonus and duration tracking
```

---

## 3. Auto-Run Loop (`_run_loop`)

```
while self.running and not self.stop_event.is_set():
    1. _check_window() — abort if game window lost
    2. Execute each step in self.steps:
       ├─ ("key", key_name, delay) → press key, sleep(delay)
       ├─ ("left", "", delay) → left click, sleep(delay)
       └─ ("right", "", delay) → right click, sleep(delay)
    3. If SkillMacro:
       ├─ Check distance → auto-approach if needed
       ├─ Wait for castbar or movement_delay
       └─ Apply cast lock
    4. Reset and repeat (for persistent macros)
```

---

## 4. Auto-Approach Logic

When target distance exceeds `skill_range`, SkillMacro performs auto-approach:

```python
if current_distance > target_range:
    kb.press('w')                        # hold W to move forward
    approach_start = time.time()

    while self.running and not stop_event:
        if not _check_window():
            kb.release('w')              # ALWAYS release W on exit
            break
        current = app.target_distance
        if current is not None and current <= target_range:
            break
        if time.time() - approach_start > 3.0:   # 3s timeout
            break
        time.sleep(0.05)

    kb.release('w')                      # ALWAYS release W
    time.sleep(0.2)
```

Key safety rules:
- `kb.release('w')` is called on every exit path
- 3-second timeout prevents infinite loops
- `self.running` is checked every iteration

---

## 5. Equipment Reswap (Reswap)

SkillMacro swaps equipment between chanting (singing) and physical attack (PA) phases:

```
Step 1: Press swap_key_chant (default "e") → switch to chant gear
        Delay: first_step_delay (or 30 + ping_compensation)
Step 2: Press skill_hotkey (e.g. "3") or left-click (for zone skills)
        Delay: global_step_delay (or ping_compensation)
Step 3: Press swap_key_pa (default "e") → switch to PA gear
        Delay: global_step_delay
```

Reswap keys are configured via `swap_key_chant` and `swap_key_pa` settings.

---

## 6. Sequence Diagrams

### SkillMacro Execution Flow

```
User presses hotkey
    │
    ▼
HotkeyManager → dispatcher.request_macro(skill_macro, priority=5)
    │
    ▼
MacroDispatcher.request_macro()
    ├── Check cast_lock → if locked, queue (priority ≤ 3)
    ├── Check cooldown_cache → if in CD, queue (priority ≤ 3)
    ├── Check running → if running, reject
    ├── Update cooldown_cache
    ├── Set cast_lock (actual_cast_time + cast_lock_margin)
    └── Launch macro thread
    │
    ▼
SkillMacro._run_loop()
    ├── _check_window() → abort if inactive
    ├── Check distance (if check_distance=True)
    │   ├── Far → auto-approach (hold W, wait ≤ 3s)
    │   └── Near → continue
    ├── Wait for castbar appearance (if use_castbar_detection=True, max 2s)
    │   OR wait movement_delay_ms (if use_castbar_detection=False)
    ├── Record cooldown time
    ├── Step 1: swap_key_chant ("e")
    ├── Step 2: skill_hotkey ("3" or left-click)
    ├── Castbar detection (if auto-approach was used)
    └── Step 3: swap_key_pa ("e")
```

### Castbar Detection Flow

```
is_castbar_visible() called
    │
    ▼
Check cache (valid for 1 ms)
    ├── Cache hit → return cached value
    └── Cache miss → _check_castbar_direct()
    │
    ▼
_check_castbar_direct()
    ├── mss.mss().grab() — capture 3×3 pixel area around castbar_point
    ├── For each pixel in 3×3 grid:
    │   diff = |R-R₀| + |G-G₀| + |B-B₀|
    │   if diff ≤ castbar_threshold → return True
    └── Return False if no pixel matches
    │
    ▼
Update cache: {'visible': bool, 'timestamp': now()}
```

### Profile Loading Flow

```
Backend.load_profile(name)
    │
    ▼
1. Save current profile (if different profile was active)
    │
    ▼
2. Load profile JSON: {settings: {...}, macros: [...], window_locked, target_window_title}
    │
    ▼
3. Apply settings to Backend._settings
    │
    ▼
4. _apply_settings_to_attributes()
    ├── castbar_enabled, castbar_point, castbar_color, castbar_threshold
    ├── mob_area, player_area
    ├── window_locked, target_window_title
    ├── ping, target_distance
    │
    ▼
5. Load macros from profile via _create_macro_from_dict()
    │
    ▼
6. Apply window lock settings
    │
    ▼
7. Save settings.json
    │
    ▼
8. Emit settingsChanged, macrosChanged, profileChanged
    │
    ▼
9. Re-register all hotkeys (register_all_hotkeys)
```
