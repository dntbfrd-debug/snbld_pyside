# Castbar Detection

Castbar detection in snbld resvap uses pixel color matching to determine when the player is casting a skill in Perfect World. This enables macros to wait for cast completion before proceeding to the next step.

## Detection Methods

### `is_castbar_visible()`

Checks if the castbar is currently visible on screen with caching (1 ms TTL).

```python
def is_castbar_visible():
    """
    Check castbar visibility with caching (1 ms).
    Returns True if castbar is visible.
    """
```

### `_check_castbar_direct()`

Direct pixel capture and comparison via `mss`.

```python
def _check_castbar_direct():
    # mss with new instance (thread-safe)
    with mss.mss() as sct:
        # 3x3 pixel area around castbar_point
        monitor = {"left": x-1, "top": y-1, "width": 3, "height": 3}
        screenshot = sct.grab(monitor)

        # Check each pixel
        for dy in range(3):
            for dx in range(3):
                idx = (dy * 3 + dx) * 3
                r, g, b = screenshot.rgb[idx], ...
                diff = abs(r - R0) + abs(g - G0) + abs(b - B0)
                if diff <= threshold:
                    return True
    return False
```

Captures a 3x3 pixel area around `castbar_point` and compares each pixel's RGB values against the calibrated `castbar_color`. Returns `True` if any pixel's difference is below `castbar_threshold`.

### `captureCastbarColorAt(x, y, size=1)`

Captures the color of a single pixel at coordinates `(x, y)`. Returns color as `'R,G,B'` string.

```python
@Slot(int, int, int, result=str)
def captureCastbarColorAt(x, y, size=1):
    """Capture color of one pixel at (x, y). Returns 'R,G,B'."""
```

## Calibration Flow

1. User clicks "Start calibration" (`startCastbarCalibration()`)
2. Mouse hook activates to capture clicks
3. User positions cursor over the castbar diamond indicator
4. User clicks **Left Mouse Button**
5. Color is captured and saved to `castbar_color = [R, G, B]`
6. Hook stops asynchronously via `QTimer.singleShot`
7. Calibration point and color are available via:
   - `getCastbarCalibrationPoint()` — returns last calibration point
   - `getCastbarCalibrationColor()` — returns last calibration color

The calibrated color is saved to both `settings.json` and the current profile.

## MSS Pixel Capture

The detection uses `mss` library instead of GDI `GetPixel` for performance:

- **Speed**: 10-50x faster than GDI `GetPixel`
- **Thread-safe**: Uses a new `mss.mss()` instance per call
- **Single pixel capture**: Only captures a 3x3 area (9 pixels) around the castbar point
- **Minimal overhead**: Each check completes in under 1 ms with caching

```python
# Fast capture with mss (thread-safe)
with mss.mss() as sct:
    monitor = {"left": x-1, "top": y-1, "width": 3, "height": 3}
    screenshot = sct.grab(monitor)
```

## Caching and Threshold Logic

Results are cached to avoid redundant screen captures:

```python
_castbar_cache = {'visible': False, 'timestamp': 0}
_castbar_cache_lock = threading.Lock()
# Cache is valid for 1 ms
```

**Threshold comparison**: The sum of RGB differences (`|R-R0| + |G-G0| + |B-B0|`) must be below `castbar_threshold` for the castbar to be considered visible.

## castbarColorCaptured Signal

Emitted when a calibration color is captured:

```python
castbarColorCaptured = Signal(str, str)  # point, color
```

- **Parameters**: `point` (calibration coordinates), `color` (RGB string)
- **Used by**: QML UI to display the captured color and confirm calibration
- **Triggered by**: `captureCastbarColorAt()` during calibration mode
