# SNBLD RESVAP — Developer Checklists & Rules

> Quick reference for the snbld resvap project — a macro system for MMORPG Perfect World (Asgard server).

---

## 1. Post-Change Checklists

### Minimal Checklist

- [ ] Program starts: `python qml_main.py` without crash
- [ ] QML works: main window opens, navigation works
- [ ] Settings persist: change → restart → setting preserved
- [ ] Macros work: create simple macro → run → executes

### Extended Checklist

- [ ] Macro creation (all types: simple, skill, zone, buff)
- [ ] Macro edit and save
- [ ] Macro deletion
- [ ] Profiles: create, load, switch, delete
- [ ] Hotkeys: assign and verify
- [ ] Castbar: calibration, visibility
- [ ] OCR: area selection, recognition
- [ ] Ping: manual test, auto-measurement
- [ ] Buffs: add, verify cast time impact
- [ ] Window: select, lock, verify
- [ ] Logging: check `logs/`

### QML Checklist

- [ ] All pages open
- [ ] Settings display values from `Backend.settings`
- [ ] Buttons call Backend methods
- [ ] No UI flickering/freezing
- [ ] Accent color applied

```qml
CheckBox {
    checked: Backend.settings.castbar_enabled
    onCheckedChanged: Backend.set_setting("castbar_enabled", checked)
}
```

---

## 2. Development Rules

### General

1. Comments in Russian, code in English
2. PEP 8, no unnecessary comments
3. No emoji in code
4. Do NOT commit without user request
5. Do NOT modify git config

### Python

1. Do not change Backend signatures (bound to QML)
2. Use `Signal(type)` from `PySide6.QtCore`
3. Use `threading.Lock` for shared data
4. Log via `from backend.logger_manager import get_logger`
5. Settings only via `set_setting()` (auto-save)
6. WinAPI via pywin32, not ctypes

### QML

1. Reuse `qml/components/`
2. Dark theme, accent from `settings.accent_color`
3. Use `Backend.settingsChanged` for UI updates
4. Frameless dialogs (`Qt.FramelessWindowHint`)
5. `anchors.fill: parent` or explicit coords

### Tests

1. Framework: unittest
2. File: `tests/test_backend_managers.py`
3. Run: `python -m unittest tests/test_backend_managers.py`

---

## 3. Frequent Tasks

### Add a Setting

1. Add to `ALLOWED_SETTINGS` in `qml_main.py` (key, type, min, max)
2. Add to `DEFAULTS` in `backend/settings_manager.py`
3. Add UI in corresponding `Settings*Page.qml`
4. Bind via `Backend.set_setting()`
5. Add to `apply_settings_to_macros()` if needed

### Add a Macro Type

1. Create class in `_macros_original.py` (inherit from base)
2. Add create/update methods to MacrosManager
3. Create `Edit*Page.qml`
4. Add Backend methods (`create_*_macro_with_params`, `update_*_macro`)
5. Update `_create_macro_from_dict()` / `_macro_to_dict()`

### Add a QML Component

1. Create file in `qml/components/`
2. Follow existing style
3. Use accent color from settings
4. Document in component README

---

## 4. What NOT to Do

1. **Do NOT delete** `_macros_original.py`
2. **Do NOT change** Backend signal signatures
3. **Do NOT use** GDI GetPixel (only mss)
4. **Do NOT delete** log files manually (use `cleanup_old_logs`)
5. **Do NOT hardcode** paths (use `utils/resource_utils.py`)
6. **Do NOT commit** `settings.json`, `macros.json`, `profiles/`
7. **Do NOT add** dependencies without updating `requirements.txt`
8. **Do NOT delete** entire file content — keep the rest
9. **NEVER delete** an entire file — backup to `_archive/` first

---

## 5. Critical Places

### Auto-approach (`_macros_original.py`)
- Always `kb.release('w')` on loop exit
- 3-second timeout
- Check `self.running` in loop

### Castbar Detection (`qml_main.py`)
- Uses `mss` (not GDI) — 10-50x faster
- Captures 3x3 pixel area
- RGB sum < threshold, 1ms cache

### MouseHookManager (`low_level_hook.py`)
- WinAPI low-level hook
- Blocks ONLY clicks in macro zones
- One thread for all zone macros

### Cast Lock (dispatcher)
- Set BEFORE cast via `dispatcher.request_macro()`
- Accounts for buffs
- Priority 1-3 queued when blocked

### CastBarDialog
- Hook stops via `QTimer.singleShot`
- `onClosing` guarantees stop
- `daemon=True` for hook thread
- Color saved to `settings.json` AND profile

---

## 6. Quick Start for New AI

1. **Understand architecture (5 min)**
   `qml_main.py (Backend) ←→ QML UI → _macro_original.py → threads.py, tesseract_reader.py → backend/`

2. **Find file via File Map (1 min)** — see `DOCUMENTATION.md`

3. **Read file COMPLETELY** — never assume content

4. **Make changes** — follow existing style, reuse components, do not delete code

5. **Verify via checklist** — see Section 1

6. **Ask clarifying questions** — what to change, expected result, alternatives, impact

---

## 7. Rule for AI Assistants

> **After any user request, ask clarifying questions about the change** so the user better understands the program. Do not assume user intent — ask.

### Mandatory AI Actions:

1. **Always use this file as instruction** when working on the project
2. **Use MCP context7** for unfamiliar APIs/libraries (PySide6, Tesseract, WinAPI, mss)
3. **Use MCP sequential-thinking** for complex logic/architecture analysis
4. **Ask clarifying questions** after completing any request:
   - What exactly needs to be changed?
   - What is the expected result?
   - Are there alternative approaches?
   - How will this affect other parts of the program?

---

*Generated from DOCUMENTATION.md — April 2026*
