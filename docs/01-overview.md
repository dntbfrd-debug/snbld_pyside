# SNBLD RESVAP — Project Overview

## Description

**snbld resvap** is a macro automation system for the MMORPG Perfect World (Asgard server, 147.45.96.78). It automates combat routines by managing skill execution with cooldown checks, distance tracking, castbar detection, and equipment swapping between chanting and physical attacks.

The application features a modern Qt Quick/QML interface with a Python backend, using Tesseract OCR for screen reading and WinAPI/SendInput for input simulation.

## Technology Stack

| Component | Technology |
|-----------|------------|
| Language | Python 3.12 |
| UI Framework | PySide6 (Qt Quick / QML) |
| OCR Engine | Tesseract 5.0 |
| Screen Capture | mss |
| Input Simulation | WinAPI / SendInput, keyboard, mouse |
| Process Monitoring | psutil |
| Image Processing | OpenCV (cv2), NumPy |

## How to Run

```bash
pip install -r requirements.txt
python qml_main.py
```

## Key Features

### Macros System

Four macro types with priority queue execution:

- **SimpleMacro** — Sequential key presses and clicks
- **ZoneMacro** — Triggers when cursor is within a screen region
- **SkillMacro** — Skill execution with cooldown, distance, cast time, and zone checks
- **BuffMacro** — Buff management with cast time recalculation from ping

The `MacroDispatcher` provides priority queues (1=critical, 5=normal, 10=background), cooldown caching (~0.05ms checks), and cast locking to prevent interrupting active casts.

### OCR (Tesseract)

- Dual-thread monitoring for mob and player distance reading
- Auto-switching between mob/player readers after 3 empty attempts
- Image preprocessing pipeline: CLAHE → Binarization (OTSU) → Erosion → Closing
- Correction of common recognition errors

### Castbar Detection

- Single-pixel color detection using mss (10-50x faster than GDI GetPixel)
- 3x3 pixel area capture around the configured castbar point
- RGB comparison against stored castbar color with configurable threshold
- Color calibration mode via mouse click capture

### Equipment Reswap (Reswap)

Automatic equipment switching between chant (magic damage) and physical attack phases:

- Step 1: Swap to chanting weapon set
- Step 2: Execute chant action
- Step 3: Swap to physical attack weapon set

Configurable keys for both swap actions with adjustable delays between steps.

### Ping Compensation

- ICMP ping monitoring to the game server
- Automatic delay compensation based on ping: `compensation = min(game_ping / 1000 * 0.7 + 0.02, 0.3)`
- Game ping multiplier of 2.0 for Perfect World server characteristics
- Toggle between fixed delays and ping-based delays

### Buff System

- Active buff tracking with duration timers
- Channeling bonus stacking for cast time reduction
- Cast time formula: `actual = base_cast_time * 100 / (100 + bonus_total)`
- Buff effects applied to macro cast time calculations

### Profile System

- Unlimited profiles stored as JSON in `profiles/` directory
- Each profile contains: settings, macros, window binding, target window title
- Auto-save on any change
- Last active profile loaded on startup

### Activation & Subscription

- Key-based activation with HWID binding (CPU + motherboard + disk SHA256 hash)
- Session persistence via Windows DPAPI encryption
- Heartbeat for automatic session validation
- Update checking from remote server

## Project Status

**Current Version:** 1.3.x (April 2026)

### Code Statistics

| Metric | Value |
|--------|-------|
| qml_main.py | ~2,924 lines (refactored from 4,424, **-34%**) |
| _macros_original.py | ~833 lines |
| tesseract_reader.py | ~630 lines |
| threads.py | ~354 lines |
| Backend modules | 13 (7 existing + 6 new) |
| QML files | ~47 |
| Macro types | 4 |

### Implemented & Working

- Macro execution through dispatcher with priority queue
- OCR with auto mob/player switching
- Castbar detection (3x3 pixel via mss)
- Auto-run to target with 3-second timeout
- Logging with 7 categories
- Settings persistence (including castbar color)
- Profile save/load system
- Cooldown caching and cast locking
- Buff effects on cast time
- Auto-delay recalculation from ping
- Mouse click blocking in macro zones
- Window selection and binding
- Hotkey support with combinations

### Architecture

The backend follows the **Delegate pattern** — `Backend(QObject)` delegates calls to specialized managers:

```
Backend (qml_main.py)
├── ActivationManager      → activation, heartbeat, subscription
├── MacroDispatcher        → priority queue, cooldowns, cast lock
├── SettingsManager        → settings load/save/validation
├── OCRManager             → OCR management
├── ProfileManager         → profiles, macro serialization
├── CastbarDetector        → castbar detection and calibration
├── MacroCrud              → macro CRUD operations
├── WindowSelector         → game window selection and binding
├── SettingsApplier        → settings application to macros
└── LoggerManager          → logging system
```

### Resources

- **Game Process:** ElementClient_x64.exe
- **API Server:** https://snbld.ru (activation, sessions, HWID)
- **Updates:** https://resvap.snbld.ru/version.json
- **Repository:** github.com/dntbfrd-debug/snbld_pyside
