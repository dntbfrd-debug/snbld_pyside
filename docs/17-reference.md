# SNBLD RESVAP — Quick Reference

> Macro system for MMORPG Perfect World (Asgard server, 147.45.96.78)
> QML version: PySide6 Widgets ported to Qt Quick / QML

---

## 1. FILE MAP

### Python Files (Root)

| File | Lines | Description |
|------|-------|-------------|
| `qml_main.py` | ~2924 (**-34%**) | **Backend** — everything exposed to QML: signals, slots, properties, settings, macros, profiles, castbar, OCR, ping, activation. Delegates to managers. |
| `_macros_original.py` | ~833 | **Macro classes** — Macro, SimpleMacro, ZoneMacro, SkillMacro, BuffMacro. Execution logic. |
| `tesseract_reader.py` | ~630 | **OCR** — TargetReader, TargetWorker. Distance recognition. |
| `threads.py` | ~354 | **Threads** — MovementMonitor, PingMonitor, MouseClickMonitor. |
| `skill_database.py` | ~200 | **Skill database** — SkillDatabase, loads from JSON. |
| `low_level_hook.py` | ~150 | **WinAPI mouse hook** — MouseHookManager, click interception. |
| `constants.py` | ~100 | **Constants** — paths, default values. |
| `auth.py` | ~300 | **Authorization** — subscription check, HWID, heartbeat. |
| `ocr_overlay.py` | ~200 | **OCR overlay** — widget displayed over the game. |

### Backend Managers (13 total)

| File | Description |
|------|-------------|
| `backend/__init__.py` | Manager exports |
| `backend/activation_manager.py` | Activation, heartbeat, subscription |
| `backend/profile_manager_ext.py` | Profiles, macro serialization |
| `backend/castbar_detector.py` | Castbar detection and calibration |
| `backend/macro_crud.py` | Macro CRUD (create/edit/delete) |
| `backend/window_selector.py` | Window selection and binding |
| `backend/settings_applier.py` | Applying settings to macros |
| `backend/macros_dispatcher.py` | Macro queue, cooldown cache, cast lock |
| `backend/settings_manager.py` | Settings load/save |
| `backend/ocr_manager.py` | OCR management |
| `backend/hotkey_manager.py` | Hotkey registration |
| `backend/buff_manager.py` | Active buffs management |
| `backend/window_manager.py` | Window check and activation |
| `backend/logger_manager.py` | Logging system (Singleton) |

### QML Files

**Pages:**

| File | Description |
|------|-------------|
| `qml/main.qml` | Main window, StackView, navigation |
| `qml/MacrosListPage.qml` | Macro list |
| `qml/MacrosEditPage.qml` | Edit navigation |
| `qml/EditSimplePage.qml` | Simple macro editor |
| `qml/EditSkillPage.qml` | Skill macro editor |
| `qml/EditZonePage.qml` | Zone macro editor |
| `qml/EditBuffPage.qml` | Buff macro editor |
| `qml/SettingsPage.qml` | Settings hub |
| `qml/SettingsCastbarPage.qml` | Castbar settings |
| `qml/SettingsMovementPage.qml` | Movement settings |
| `qml/SettingsOCRPage.qml` | OCR settings |
| `qml/SettingsOCRAreasPage.qml` | OCR areas |
| `qml/SettingsOtherPage.qml` | Delays, auto-delays |
| `qml/SettingsNetworkPage.qml` | Network and ping |
| `qml/SettingsReswapPage.qml` | Reswap settings |
| `qml/SettingsWindowPage.qml` | Window settings |
| `qml/SettingsAppearancePage.qml` | Appearance / theme / color |
| `qml/ProfilesPage.qml` | Profile management |

**Dialogs and Selectors:**

| File | Description |
|------|-------------|
| `qml/CastBarDialog.qml` | Castbar calibration dialog |
| `qml/AreaSelector.qml` | OCR area selector |
| `qml/ZoneAreaSelector.qml` | Zone area selector for macros |

**Reusable Components:**

| File | Description |
|------|-------------|
| `qml/components/FormRow.qml` | Form row |
| `qml/components/StyledButton.qml` | Styled button |
| `qml/components/ToggleSwitch.qml` | Toggle switch |
| `qml/components/MacroCard.qml` | Macro card |
| `qml/components/NumberField.qml` | Number field |
| `qml/components/SettingGroup.qml` | Settings group |

### Utils

| File | Description |
|------|-------------|
| `utils/file_utils.py` | File utilities |
| `utils/network_utils.py` | Network utilities |
| `utils/resource_utils.py` | Resource utilities (paths, icons) |

### Data Files

| File | Description |
|------|-------------|
| `123.ico` | Application icon |
| `logo.png` | Logo |
| `asgard_skills.json` | Skill database source |
| `tesseract/` | Tesseract OCR engine binaries |
| `profiles/` | User profiles (JSON) — **do not commit** |

### Config Files (Do Not Commit)

| File | Description |
|------|-------------|
| `settings.json` | User settings |
| `macros.json` | Legacy macros (now stored in profiles) |
| `logs/` | Log files — auto-cleaned on startup |

---

## 2. KNOWN LSP ERRORS (IGNORE)

> These are false positives from the type checker. Do NOT attempt to fix them.

### qml_main.py

| Error | Reason |
|-------|--------|
| `"QQuickStyle" is unknown import symbol` | Works at runtime, PySide6 typing is incomplete |
| `Cannot access attribute "get" for class "Property"` | `self._settings` is a dict, type checker confuses it with Property |
| `Operator "<" not supported for types "int \| float \| bool \| list \| str"` | `value` in set_setting has a union type, validation works correctly |
| `Cannot assign to attribute "zone_rect" for class "SkillMacro"` | zone_rect is added dynamically after creation |
| `Cannot assign to attribute "window_locked" — "Literal[True]" is not assignable to "Property"` | Property decorator, setter works correctly |
| `"e" is possibly unbound` | lambda e=None — e is always defined |
| `Cannot access attribute "LeftButton" for class "type[Qt]"` | Works at runtime, imported from Qt |
| `Cannot access attribute "FramelessWindowHint" for class "type[Qt]"` | Works at runtime |
| `Cannot assign to attribute "window_data" for class "QListWidget"` | Dynamic attribute |
| `No overloads for "__init__" match the provided arguments` | Dynamic Qt typing |

### _macros_original.py

| Error | Reason |
|-------|--------|
| `Cannot access attribute "cooldown_lock" for class "Macro*"` | Attributes are added in subclasses |
| `Cannot access attribute "cooldown" for class "Macro*"` | Attributes are added in subclasses |
| `"Never" is not iterable` | Type checker does not understand dynamic attributes |

### tesseract_reader.py

| Error | Reason |
|-------|--------|
| `Expression of type "None" cannot be assigned to parameter` | Optional parameters with default=None |
| `"start_work" is not a known attribute of "None"` | Worker is initialized later |

### threads.py

| Error | Reason |
|-------|--------|
| `Expression of type "None" cannot be assigned to parameter of type "List[str]"` | Optional parameters |
| `Cannot access attribute "receivers" for class "SignalInstance"` | Internal PySide6 API |

### skill_database.py

| Error | Reason |
|-------|--------|
| `Argument of type "str" cannot be assigned to parameter "skill_class" of type "SkillClass"` | String is converted to Enum |

### All QML Files

| Error | Reason |
|-------|--------|
| Implicit type inference warnings | QML type inference is intentional, not an error |

---

## 3. CONTEXT: WHAT WAS ALREADY FIXED

### Fixed Bugs

| Bug | Fix | File |
|-----|-----|------|
| GDI GetPixel was slow | Replaced with mss (10-50x faster) | qml_main.py |
| Macros did not stop on close | cleanup() in on_about_to_quit | qml_main.py |
| Settings not saved to profile | Auto-save on set_setting | qml_main.py |
| ZoneMacro did not start automatically | macro.start() on load | qml_main.py |
| Hotkeys not re-registered | register_all_hotkeys() on stop_all | qml_main.py |
| castbar_color not saved | Saved as list in settings.json | qml_main.py |
| OCR did not restart on settings change | stop_ocr() + start_ocr() in apply_settings | qml_main.py |
| Buffs did not affect cast lock | get_actual_cast_time() in lock_cast | qml_main.py |
| Profile not loaded on startup | load_profile(last_active_profile) in main | qml_main.py |
| Mouse clicks passed through to game with zone macros | MouseHookManager blocks clicks in zone | qml_main.py, low_level_hook.py |
| Fast macro stop (< 0.3s) | Age check in callback | qml_main.py |
| Hook did not stop during calibration | QTimer.singleShot for async stop | qml_main.py |
| Auto-approach did not release 'w' | kb.release('w') ALWAYS on exit | _macros_original.py |
| Logging broken in packaged version | UTF-8 for stdout/stderr | qml_main.py |
| Macros duplicated on profile load | Clear _macros before load | qml_main.py |
| **Modularity refactoring** | **6 modules extracted, qml_main.py 4424 to 2924 (-34%)** | **backend/*.py** |

### Known Peculiarities (NOT Bugs)

| Peculiarity | Description |
|-------------|-------------|
| LSP type checking errors | False positives — see section 2 above |
| settings.json and profiles/ not in git | Intentional — each user has their own settings |
| macros.json is legacy | Macros are now stored in profiles |
| castbar_color as list in JSON | Converted from string on load |
| zone_rect is optional for SkillMacro/BuffMacro | Added dynamically |
| PingMonitor does not start if ping_auto=False | Intentional behavior |
| OCR does not start automatically | Started by the START button |

---

## 4. KEY RESOURCE LOCATIONS

| Resource | Location |
|----------|----------|
| Main entry point | `c:\Users\dntbf\Desktop\snbd2\snbld_pyside\qml_main.py` |
| Full documentation | `c:\Users\dntbf\Desktop\snbd2\snbld_pyside\DOCUMENTATION.md` |
| AI instructions | `c:\Users\dntbf\Desktop\snbd2\snbld_pyside\AGENTS.md` |
| Backend managers | `c:\Users\dntbf\Desktop\snbd2\snbld_pyside\backend\` |
| QML files | `c:\Users\dntbf\Desktop\snbd2\snbld_pyside\qml\` |
| Components | `c:\Users\dntbf\Desktop\snbd2\snbld_pyside\qml\components\` |
| Utilities | `c:\Users\dntbf\Desktop\snbd2\snbld_pyside\utils\` |
| Tests | `c:\Users\dntbf\Desktop\snbd2\snbld_pyside\tests\test_backend_managers.py` |
| User profiles | `c:\Users\dntbf\Desktop\snbd2\snbld_pyside\profiles\` |
| Log files | `c:\Users\dntbf\Desktop\snbd2\snbld_pyside\logs\` |
| Tesseract OCR | `c:\Users\dntbf\Desktop\snbd2\snbld_pyside\tesseract\` |
| Requirements | `c:\Users\dntbf\Desktop\snbd2\snbld_pyside\requirements.txt` |
| Build script | `c:\Users\dntbf\Desktop\snbd2\snbld_pyside\build.bat` |
| Skill database | `c:\Users\dntbf\Desktop\snbd2\snbld_pyside\asgard_skills.json` |
| Legacy Widgets version | `C:\Users\dntbf\Desktop\snbld_pyside` |

---

*Generated from DOCUMENTATION.md on 2026-04-14*
