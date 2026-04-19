# Backend Signals & Properties

> **snbld resvap** — Macro system for MMORPG Perfect World (Asgard server)

## Backend Class Overview

The `Backend(QObject)` class is the central bridge between Python and QML. It inherits from `QObject` and is registered in the QML context as `backend`, enabling direct method calls and property bindings from QML components.

**Key responsibilities:**
- Delegates operations to specialized manager modules
- Exposes settings, macros, and state as QML-accessible properties
- Emits signals to notify QML of state changes
- Provides slots for QML to trigger backend actions

---

## Signals

| Signal | Parameters | Description |
|--------|------------|-------------|
| `macrosChanged` | — | Macro list changed |
| `settingsChanged` | — | Settings changed |
| `subscriptionChanged` | — | Subscription status changed |
| `activationStatusChanged` | — | Activation status changed |
| `updateAvailable` | `dict` | Update available (update info) |
| `pingUpdated` | `int` | Ping updated (ping value in ms) |
| `distanceUpdated` | `str, float, list` | target_type, distance, numbers |
| `profileChanged` | — | Current profile changed |
| `profilesChanged` | — | Profile list changed |
| `notification` | `str, str` | message, type (info/success/warning/error) |
| `pageChangeRequested` | `str` | Request QML page navigation |
| `globalStoppedChanged` | — | Global stopped state changed |
| `activeBuffsUpdated` | — | Active buffs list updated |
| `minimizeRequested` | — | Minimize window requested |
| `closeRequested` | — | Close window requested |
| `startAllPressed` | — | Start All button indicator updated |
| `stopAllPressed` | — | Stop All button indicator updated |
| `macroStatusChanged` | — | Macro status changed |
| `castbarColorCaptured` | `str, str` | point, color |
| `buffPointCaptured` | `int, int` | x, y |
| `areaSelected` | `int, int, int, int` | x1, y1, x2, y2 |
| `zoneAreaSelectedSignal` | `list` | [x1, y1, x2, y2] |
| `ocrAreaSelected` | `str, str` | target_type, area |
| `ocrTestResult` | `str, dict` | target_type, result |
| `windowsListUpdated` | `list` | Window list updated |
| `openWindowSelector` | — | Open window selector dialog |

---

## Properties

| Property | Type | Notify Signal | Description |
|----------|------|---------------|-------------|
| `macros` | `list` | `macrosChanged` | List of macros (dict format) |
| `global_stopped` | `bool` | `globalStoppedChanged` | All macros stopped flag |
| `window_locked` | `bool` | `macrosChanged` | Window lock enabled |
| `target_window_title` | `str` | `macrosChanged` | Target window title |
| `settings` | `dict` | `settingsChanged` | All settings (copy) |
| `subscription_info` | `dict` | `subscriptionChanged` | Subscription information |
| `isActivated` | `bool` | `activationStatusChanged` | Program activation status |
| `current_profile` | `str` | `profileChanged` | Current profile name |
| `profiles_list` | `list` | `profilesChanged` | List of all profiles |
| `ping` | `int` | `pingUpdated` | Current ping value |
| `target_distance` | `float` | `distanceUpdated` | Distance to target |
| `skill_list` | `list` | constant | All skills from database |
| `buff_list` | `list` | constant | All buffs from database |
| `active_buffs_list` | `list` | `activeBuffsUpdated` | Currently active buffs |
