# Architecture Overview

> snbld resvap — Macro automation system for MMORPG Perfect World (Asgard server)

## 1. General Architecture

```
┌──────────────────────────────────────┐
│           QML UI Layer               │
│      (Qt Quick / QML — 45+ files)    │
└──────────────┬───────────────────────┘
               │ Qt Property Bindings / @Slot calls
               ▼
┌──────────────────────────────────────┐
│        Backend (QObject)             │
│     qml_main.py — ~2924 lines        │
│ Signals: macrosChanged, settings...  │
└──┬───┬───┬───┬───┬───┬───┬──────────┘
   │   │   │   │   │   │   │  Delegate
   ▼   ▼   ▼   ▼   ▼   ▼   ▼
┌──────────────────────────────────────┐
│         Backend Managers              │
├───────────────┬──────────────────────┤
│ Active        │ Not Yet Integrated   │
├───────────────┼──────────────────────┤
│ ActivationMgr │ ProfileManager       │
│ MacroDisp     │ CastbarDetector      │
│ SettingsMgr   │ WindowSelector       │
│ OCRManager    │ SettingsApplier      │
│ HotkeyMgr     │ MacroCrud            │
│ BuffManager   │                      │
│ WindowManager │                      │
│ LoggerManager │                      │
└───────┬───────┴──────────┬───────────┘
        │                  │
        ▼                  ▼
┌───────────────┐  ┌───────────────────────┐
│  threads.py   │  │  _macros_original.py  │
│ MovementMon   │  │  Macro (base)         │
│ PingMonitor   │  │  SimpleMacro          │
│ MouseClickMon │  │  ZoneMacro            │
└───────────────┘  │  SkillMacro           │
                   │  BuffMacro            │
                   └───────────────────────┘
```

## 2. Data Flow

### Application Startup

```
main()
  → Backend() init
  → SettingsManager.load_settings()
  → ActivationManager.check_activation()
  → ProfileManager.load_profile()
  → Backend._apply_settings_to_attributes()
  → register_all_hotkeys()
  → app.exec()
```

### Hotkey Press → Macro Execution

```
User presses hotkey (e.g. F1)
  → HotkeyManager intercepts
  → Check: window active? global_stopped?
  → MacroDispatcher.request_macro(macro, priority=5)
     ├─ Cast locked? → queue (pri<=3) or reject
     ├─ On cooldown? → queue (pri<=3) or reject
     ├─ Already running? → reject
     ├─ global_stopped? → reject
     ├─ Update cooldown cache
     ├─ Set cast_lock
     └─ macro.start()
```

### OCR Pipeline

```
OCRManager.start()
  → TargetReader (2 threads: mob + player)
     ├─ Capture screen (mss)
     ├─ Preprocess: CLAHE→OTSU→Erode→Close
     ├─ Tesseract OCR
     └─ Emit: data_updated(target_type, distance, numbers)
        → Backend.on_distance_updated()
           → distanceUpdated signal → QML
```

### Castbar Detection

```
Backend.is_castbar_visible()
  → Cache check (1ms TTL)
  → mss capture 3x3 at castbar_point
  → Compare RGB with castbar_color
  → Sum of diffs < threshold? → True/False
```

## 3. Delegate Pattern

Backend uses the **Delegate pattern** to forward calls to specialized managers, keeping QML bindings unchanged.

```
QML: Backend.delete_macro("my_macro")
         │
         ▼
┌──────────────┐  delegate  ┌────────────────────┐
│   Backend    ├───────────►│ MacroCrud          │
│              │  delegate  │ .delete_macro()    │
│              ├───────────►│ SettingsManager    │
│              │  delegate  │ .get()             │
│              ├───────────►│ MacroDispatcher    │
│              │            │ .request_macro()   │
└──────────────┘            └────────────────────┘
```

QML calls `Backend.method()` → Backend delegates to manager → full backward compatibility.

## 4. Code Examples — Delegation

```python
# qml_main.py — Backend delegates to managers

# === Macro CRUD delegation ===
def delete_macro(self, name):
    if self.macro_crud:
        self.macro_crud.delete_macro(name)

def save_macro(self, macro_dict):
    if self.macro_crud:
        return self.macro_crud.save_macro(macro_dict)

# === Settings delegation ===
def set_setting(self, key, value):
    # Validate and apply through SettingsManager
    if self.settings_manager:
        self.settings_manager.set(key, value)
    # Apply to running macros
    self.apply_settings_to_macros(key, value)
    # Persist to profile
    self._save_current_profile()
    # Notify QML
    self.settingsChanged.emit()

# === Castbar detection delegation ===
def is_castbar_visible(self):
    if self.castbar_detector:
        return self.castbar_detector.is_castbar_visible()
    return False

@Slot(int, int, int, result=str)
def captureCastbarColorAt(self, x, y, size=1):
    if self.castbar_detector:
        return self.castbar_detector.capture_castbar_color_at(x, y, size)

# === Window management delegation ===
def is_game_window_active(self):
    if self.window_selector:
        return self.window_selector.is_game_window_active()
    return False

# === Macro execution delegation ===
def start_macro(self, name):
    macro = self.macros_manager.get_macro_by_name(name)
    if macro:
        self.dispatcher.request_macro(macro, priority=5)

def stop_macro(self, name):
    macro = self.macros_manager.get_macro_by_name(name)
    if macro:
        macro.stop()
```

## 5. Architecture Benefits

| Benefit | Description |
|---------|-------------|
| **Backward compatibility** | QML layer unchanged — all signals/properties/slots remain the same |
| **Single responsibility** | Each manager handles one concern (150-400 lines each) |
| **Testability** | Managers can be unit-tested in isolation |
| **Maintainability** | qml_main.py reduced from 4424 to 2924 lines (-34%) |
| **Extensibility** | New features add new managers without modifying existing code |
| **Separation of concerns** | UI logic (QML) ↔ Business logic (Backend) ↔ Domain logic (Managers) |

## 6. threads.py Overview

### MovementMonitor

Monitors movement key presses via WinAPI `GetAsyncKeyState`.

```python
class MovementMonitor(threading.Thread):
    movement_keys = ['w', 'a', 's', 'd', 'up', 'down', 'left', 'right']
    state = MovementState()  # moving: bool, last_stop_time: float

    def get_movement_delay(current_time) -> float:
        """Returns time elapsed since movement stopped"""
```

Used to delay macro execution after player stops moving (prevents casting while running).

### PingMonitor

Measures ICMP ping to the game server.

```python
class PingMonitor(QThread):
    ping_updated = Signal(int)

    def __init__(self, process_name, interval=5):
        # Finds server IP by process_name
        # Pings every interval seconds
```

Ping values are used to calculate delay compensation (`getPingCompensation()`) for network latency.

### MouseClickMonitor

Monitors mouse clicks for zone-based macros.

```python
class MouseClickMonitor(QThread):
    mouse_clicked = Signal(int, int)  # x, y

    def run(self):
        while self.running:
            if mouse.is_pressed(button="left"):
                x, y = get_mouse_position()
                self.mouse_clicked.emit(x, y)
                time.sleep(0.1)  # Debounce: prevent duplicate clicks
            time.sleep(0.01)  # Poll every 10ms
```

Single thread handles all zone macros. Started/stopped together with macro execution.

---

**Key files:**
- `c:\Users\dntbf\Desktop\snbd2\snbld_pyside\qml_main.py` — Backend class
- `c:\Users\dntbf\Desktop\snbd2\snbld_pyside\threads.py` — Monitoring threads
- `c:\Users\dntbf\Desktop\snbd2\snbld_pyside\_macros_original.py` — Macro base classes
- `c:\Users\dntbf\Desktop\snbd2\snbld_pyside\backend\` — All manager modules
