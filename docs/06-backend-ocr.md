# Backend OCR System

## TargetReader Class

The `TargetReader` class (defined in `tesseract_reader.py`) is a dual-thread OCR engine that monitors distance to both **mob** and **player** targets simultaneously.

```python
class TargetReader(QThread):
    data_updated = Signal(str, float, list)  # target_type, distance, numbers

    def __init__(self, areas, interval_per_area, scale, psm, use_morph, check_window):
        # Thread 1: mob distance reading
        # Thread 2: player distance reading
        # Auto-switching on 3 consecutive empty attempts
```

Each thread independently captures screenshots and runs Tesseract OCR on its assigned area. Results are emitted via the `data_updated` signal.

## Backend OCR Control

The `Backend` class provides simple start/stop methods that delegate to the `OCRManager`:

```python
def start_ocr():
    """Start OCR monitoring (Tesseract TargetReader)"""

def stop_ocr():
    """Stop OCR monitoring"""
```

Additional slot methods for UI interaction:

| Method | Description |
|--------|-------------|
| `toggle_ocr_overlay()` | Toggle OCR overlay visibility |
| `selectOCRArea(target_type)` | Launch AreaSelector for the given target |
| `onOCRAreaSelected(target_type, x1, y1, x2, y2)` | Handle area selection |
| `testOCRArea(target_type)` | Test OCR area (screenshot + recognition) |

## Auto-Switching Logic

When one target returns empty results, the system tracks consecutive failures and switches after a threshold:

```python
SWITCH_THRESHOLD = 3  # consecutive empty attempts
SWITCH_TIMEOUT = 5.0  # seconds without success

# Selection priority in _select_active_target():
# 1. If mob_dist > 0          → use mob
# 2. If player_dist > 0       → use player
# 3. If mob_idle > 5 sec      → switch to player
# 4. If player_idle > 5 sec   → switch to mob
# 5. If both unsuccessful     → alternate between them
```

This ensures the system always reads from the most reliable target without manual intervention.

## Preprocessing Pipeline

Before Tesseract processes the image, a four-stage pipeline improves accuracy:

```
1. CLAHE (Contrast Limited Adaptive Histogram Equalization)
   → Enhances local contrast for better digit separation

2. Binarization (OTSU thresholding)
   → Converts grayscale to black-and-white

3. Erosion (MORPH_CROSS, iterations=1)
   → Separates touching digits

4. Closing (MORPH_RECT)
   → Removes noise and fills gaps in characters
```

The pipeline is controlled by the `use_morph` setting — when disabled, only CLAHE and binarization are applied.

## OCR Error Corrections

Tesseract commonly misreads certain digit patterns in the game font. The system applies deterministic corrections:

```python
common_corrections = {
    '21.': '27.',  # 27.5 → misread as 21.9
    '29.': '25.',  # 25.7 → misread as 29.1
    '71':  '77',   # 77   → misread as 71
    '17':  '77',   # 77   → misread as 17
    '95':  '55',   # 55   → misread as 95
    '59':  '55',   # 55   → misread as 59
    '39':  '35',   # 35   → misread as 39
    '93':  '53',   # 53   → misread as 93
}
```

These corrections are applied after Tesseract returns a result, before the value is emitted to the backend.

## distanceUpdated Signal

The `TargetReader.data_updated` signal is connected to `Backend.on_distance_updated`, which emits the Qt signal:

```python
distanceUpdated = Signal(str, float, list)  # target_type, distance, numbers
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `target_type` | `str` | `"mob"` or `"player"` — which source provided the reading |
| `distance` | `float` | Parsed distance value (e.g., `27.5`) |
| `numbers` | `list` | Raw list of all numbers detected in the OCR area |

The signal updates `Backend.target_distance`, which is exposed to QML as a property. The UI can bind to this value to display real-time distance information.

```python
def on_distance_updated(target_type, distance, numbers):
    """Update distance from Tesseract reading"""
    self.target_distance = distance
    self.distanceUpdated.emit(target_type, distance, numbers)
```
