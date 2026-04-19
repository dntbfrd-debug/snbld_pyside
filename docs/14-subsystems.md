# Subsystems — Tesseract, Castbar, Threads, Logging

Technical details for core subsystems not covered in the Backend API docs.

---

## TesseractReader — OCR Engine

Located in `tesseract_reader.py`. Reads distance values from the game UI using Tesseract OCR.

### Architecture

`TargetWorker` — a single-threaded worker that alternates between two target areas (`mob` and `player`). It uses **one active reader** at a time and switches after `MAX_EMPTY_ATTEMPTS` (10) consecutive failed recognitions.

```python
class TargetWorker(QObject):
    data_updated = Signal(str, float, list)  # target_type, distance, numbers

    active_target = "mob"       # Currently active reader
    inactive_target = "player"  # Standby reader
    empty_attempts = 0
    MAX_EMPTY_ATTEMPTS = 10
    consecutive_switches = 0    # Protection against infinite switching
    MIN_SWITCH_INTERVAL = 5.0   # Seconds between switches
```

### Target Switching Logic

1. If `mob_dist > 0` → use mob
2. If `player_dist > 0` → use player
3. After 10 empty attempts → switch to inactive target
4. If both targets fail 3 consecutive switches → OCR stops entirely
5. Minimum switch interval: 5 seconds (prevents rapid toggling)

### Image Preprocessing Pipeline

```
1. Resize (scale x N, INTER_CUBIC, cap 2000x500)
2. Grayscale (BGRA -> GRAY)
3. CLAHE (clipLimit=3.0, tileGridSize=8x8)
4. Binarization (THRESH_BINARY + THRESH_OTSU)
5. Erosion (MORPH_CROSS, 3x3, iter=1) — thins digits
6. Closing (MORPH_RECT, 2x2) — removes noise
```

```python
def preprocess_image(self, img):
    resized = cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_CUBIC)
    gray = cv2.cvtColor(resized, cv2.COLOR_BGRA2GRAY)
    enhanced = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8)).apply(gray)
    _, binary = cv2.threshold(enhanced, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    if self.use_morph:
        binary = cv2.erode(binary, cv2.getStructuringElement(cv2.MORPH_CROSS, (3, 3)), iterations=1)
        binary = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2)))
    return binary
```

### Recognition

- **Primary config**: `--psm 7` (single text line) with digit whitelist
- **Fallback**: `--psm 6` (uniform block) if primary returns empty
- **Timeout**: 2 seconds per call
- **Whitelist**: `0123456789.`

### Error Correction

Common Tesseract misreadings corrected via lookup:

```python
common_corrections = {
    '21.': '27.', '29.': '25.', '71': '77', '17': '77',
    '95': '55', '30.': '35.', '30': '35',
}
```

### Distance Parsing

Accepts `0.5` to `200` meters. Auto-formats raw digit strings: `424` -> `42.4`, `47` with last_distance < 10 -> `4.7`, `47` with last_distance >= 10 -> `47.0`.

---

## CastbarDetector — Color-Based Cast Detection

Located in `backend/castbar_detector.py`. Detects the cast bar by comparing pixel color at a calibrated screen coordinate.

### Algorithm

```python
def _check_castbar_direct():
    # 1. Parse calibration point "x,y"
    x, y = map(int, self.backend.castbar_point.split(','))

    # 2. Capture 5×5 region with mss (thread-safe cached instance)
    sct = self._get_mss()
    monitor = {"left": x-2, "top": y-2, "width": 5, "height": 5}
    screenshot = sct.grab(monitor)

    # 3. For each pixel, compute Manhattan RGB distance
    diff = abs(r - R_target) + abs(g - G_target) + abs(b - B_target)

    # 4. Castbar visible if:
    #    a) >= 30% of pixels match (diff <= threshold), OR
    #    b) best pixel match is very close (diff < threshold/2)
    is_visible = (match_ratio >= 0.3) or (best_diff <= threshold // 2)
```

### Caching

Results are cached for 16 ms (~1 frame at 60 FPS):

```python
_castbar_cache = {'visible': False, 'timestamp': 0}
# Cache valid if: time.time() - timestamp < 0.016
```

### Color Capture (Calibration)

Uses `win32gui.GetPixel` (not mss) during calibration because it runs from the mouse hook thread:

```python
def capture_castbar_color_at(x, y, size=1):
    hdc = win32gui.GetWindowDC(0)
    color = win32gui.GetPixel(hdc, x, y)  # Returns 0x00BBGGRR
    win32gui.ReleaseDC(0, hdc)
    r = color & 0xFF
    g = (color >> 8) & 0xFF
    b = (color >> 16) & 0xFF
    return f"{r},{g},{b}"
```

### Calibration Flow

1. User clicks "Start calibration" → `MouseHookManager` starts
2. All left clicks are intercepted while `_calibration_active = True`
3. On click: capture cursor position + pixel color → emit `castbarColorCaptured`
4. Hook stopped asynchronously via `QTimer.singleShot(0, ...)` to avoid `join()` from hook thread

---

## Threads (threads.py)

### MovementMonitor

Polls WASD/arrow keys via WinAPI `GetAsyncKeyState`.

```python
class MovementMonitor(threading.Thread):
    movement_keys = ['w', 'a', 's', 'd', 'up', 'down', 'left', 'right']
    state = MovementState()  # moving: bool, last_stop_time: float
    base_interval = 0.01     # 10ms while moving
    idle_interval = 0.1      # 100ms while idle (after 10 idle polls)
```

`get_movement_delay()` returns time since movement stopped (0.0 if still moving). Used by SkillMacro to wait after player stops moving.

### PingMonitor

ICMP ping to game server via `QThread`. Finds server IP by scanning game process TCP connections for `ESTABLISHED` non-local IPs. Caches PID. Runs `ping -n 4 <ip>`, parses `Average = Xms`. Initial 5s delay before first measurement.

### MouseClickMonitor

Event-based via `mouse.hook()` (not polling). Debounce: 100ms between clicks. Graceful shutdown sends fake `mouse.move(0, 0)` to unblock the C extension hook.

---

## LoggerManager — Logging System

Singleton with category-based loggers (`backend/logger_manager.py`).

### Categories

| Category | File | Default | Purpose |
|----------|------|---------|---------|
| `macros` | `macros.log` | INFO | Macro execution |
| `errors` | `errors.log` | ERROR | Errors |
| `ocr` | `ocr.log` | DEBUG | OCR details |
| `network` | `network.log` | INFO | Ping, server IP |
| `settings` | `settings.log` | INFO | Settings changes |
| `debug` | `debug.log` | DEBUG | General debugging |
| `shiboken` | `shiboken.log` | WARNING | PySide6 warnings |

```python
from backend.logger_manager import get_logger
logger = get_logger('macros')
logger.info('Macro started')
```

### Rotation and Cleanup

- **Handler**: `TimedRotatingFileHandler`, rotation every 10 minutes, 3 backups
- **Format**: `2026-04-14 12:00:00 - snbld.macros - INFO - message`
- **Console**: `ocr` capped at WARNING (file still gets DEBUG); others at default level
- **Directory**: `<exe_dir>/logs/` (frozen) or `<project_root>/logs/` (dev)
- **Cleanup**: `LoggerManager.cleanup_old_logs(days=7)` removes files older than N days; also called at startup to remove rotated files (`*.log.*`)

---

## Technical Notes

### mss Thread Safety

`mss` is not thread-safe. Each subsystem uses its own instance or a lock-protected cached one:

```python
def _get_mss(self):
    with self._mss_lock:
        if self._mss_instance is None:
            self._mss_instance = mss.mss()
        return self._mss_instance
```

### Tesseract Location

`ensure_tesseract()` copies Tesseract from PyInstaller temp dir (`sys._MEIPASS`) to `tesseract/` next to the exe. Falls back to `C:\Program Files\Tesseract-OCR\`.

### Graceful Shutdown Pattern

All threads use `_stop_event.wait(timeout)` instead of `time.sleep()` for instant interruptible termination:

```python
while not self._stop_event.is_set():
    # ... work ...
    self._stop_event.wait(self.interval)
```
