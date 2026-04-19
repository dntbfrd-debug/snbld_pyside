# QML Patterns Guide — snbld resvap

> QML architecture and Python binding patterns for the Perfect World macro system.

---

## 1. QML File Structure

```
qml/
├── main.qml                      # Main window (StackView, navigation root)
│
├── Pages (pushed onto StackView)
│   ├── ActivationPage.qml        # Activation screen
│   ├── MacrosListPage.qml        # Macro list (default page)
│   ├── MacrosEditPage.qml        # Macro edit navigator
│   ├── EditSimplePage.qml        # Simple macro editor
│   ├── EditSkillPage.qml         # Skill macro editor
│   ├── EditZonePage.qml          # Zone macro editor
│   ├── EditBuffPage.qml          # Buff macro editor
│   ├── SettingsPage.qml          # Settings hub
│   ├── SettingsCastbarPage.qml   # Castbar settings
│   ├── SettingsMovementPage.qml  # Movement settings
│   ├── SettingsOCRPage.qml       # OCR settings
│   ├── SettingsOCRAreasPage.qml  # OCR areas
│   ├── SettingsOtherPage.qml     # Delays, auto-delays
│   ├── SettingsNetworkPage.qml   # Network & ping
│   ├── ProfilesPage.qml          # Profile management
│   └── ... (15+ more pages)
│
├── Dialogs
│   ├── CastBarDialog.qml         # Castbar calibration
│   ├── SimpleMacroDialog.qml     # Create simple macro
│   ├── SkillSelectionDialog.qml  # Skill picker
│   └── ZoneAreaSelector.qml      # Zone picker
│
├── Selectors
│   ├── AreaSelector.qml          # OCR area selector
│   └── SkillClassSelector.qml    # Skill class selector
│
├── Forms
│   ├── SimpleEditForm.qml        # Simple macro form
│   ├── SkillEditForm.qml         # Skill macro form
│   ├── ZoneEditForm.qml          # Zone macro form
│   └── BuffEditForm.qml          # Buff macro form
│
└── components/                   # Reusable components
    ├── FormRow.qml               # Label + input row
    ├── SettingGroup.qml          # Settings group box
    ├── MacroCard.qml             # Macro list card
    ├── StyledButton.qml          # Themed button
    ├── NumberField.qml           # Validated number input
    └── ToggleSwitch.qml          # On/off toggle
```

---

## 2. QML Architecture

### StackView Navigation

The application uses a single `StackView` in `main.qml` as the navigation root:

```qml
// main.qml
ApplicationWindow {
    StackView {
        id: stackView
        initialItem: Backend.isProgramActivated
            ? "qrc:/qml/MacrosListPage.qml"
            : "qrc:/qml/ActivationPage.qml"
    }
}
```

### Page Navigation via Signal

Python triggers page changes through a signal; QML listens and pushes the page:

```python
# Python (qml_main.py)
class Backend(QObject):
    pageChangeRequested = Signal(str)  # page filename

    def edit_macro(self, name):
        # ... set macro_for_edit ...
        self.pageChangeRequested.emit("MacrosEditPage.qml")
```

```qml
// main.qml — signal handler
Connections {
    target: Backend
    function onPageChangeRequested(page) {
        stackView.push("qrc:/qml/" + page)
    }
}

// Back navigation
function goBack() {
    stackView.pop()
}
```

### Context Properties

Three objects are registered into the QML context from Python:

| Property | Type | Purpose |
|----------|------|---------|
| `Backend` | `QObject` | All business logic, settings, macros |
| `ResourceHelper` | `QObject` | Resource path helpers |
| `Tooltips` | `QObject` | Tooltip text provider |

---

## 3. QML ↔ Python Binding Patterns

### Pattern 1: Signal → onSignalName Handler

Python signals are auto-exposed to QML as `on<SignalName>` handlers:

```python
# Python
class Backend(QObject):
    notification = Signal(str, str)  # message, type
    settingsChanged = Signal()
    pingUpdated = Signal(int)
```

```qml
// QML — direct handler syntax
Connections {
    target: Backend

    function onNotification(message, type) {
        showNotification(message, type)
    }

    function onPingUpdated(ping) {
        pingText.text = "Ping: " + ping + " ms"
    }
}
```

```qml
// QML — inline handler (for simple cases)
Connections {
    target: Backend
    function onSettingsChanged() {
        accentColor = Backend.settings.accent_color
    }
}
```

### Pattern 2: Property Binding (Backend.propertyName)

Backend `@Property` decorators expose reactive properties to QML:

```python
# Python
class Backend(QObject):
    @Property(dict, notify=settingsChanged)
    def settings(self):
        return self._settings.copy()

    @Property(bool, notify=globalStoppedChanged)
    def global_stopped(self):
        return self._global_stopped
```

```qml
// QML — direct property binding
Text {
    text: "Ping: " + Backend.settings.average_ping + " ms"
}

// QML — conditional binding
Button {
    enabled: Backend.global_stopped
    visible: Backend.window_locked
}

// QML — binding with fallback
property color accent: Backend.settings.accent_color || "#fd79a8"
```

**Key rule:** Properties notify QML when their `notify` signal is emitted. Always use `.copy()` for dicts to avoid stale references.

### Pattern 3: Slot Calls (Backend.methodName())

Python `@Slot` methods are callable directly from QML:

```python
# Python
class Backend(QObject):
    @Slot(str, str)
    def set_setting(self, key, value):
        # Validates, applies, saves, emits settingsChanged

    @Slot(str)
    def start_macro(self, name):
        self.dispatcher.request_macro(macro, priority=5)

    @Slot(str, str, list)
    def create_simple_macro_with_params(self, name, hotkey, steps):
        # ...
```

```qml
// QML — simple slot call
Button {
    text: "Start"
    onClicked: Backend.start_macro(macroData.name)
}

// QML — slot with multiple arguments
Button {
    text: "Save"
    onClicked: Backend.set_setting("castbar_enabled", checkBox.checked)
}

// QML — slot with complex arguments
Button {
    text: "Create"
    onClicked: Backend.create_simple_macro_with_params(
        nameField.text,
        hotkeyField.text,
        stepsModel
    )
}
```

### Pattern 4: ListModel Updates

Macro lists and settings lists use QML `ListModel` updated from Python:

```python
# Python — property returning list
class Backend(QObject):
    @Property(list, notify=macrosChanged)
    def macros(self):
        return [macro.to_dict() for macro in self.macros_manager.get_all_macros()]
```

```qml
// QML — ListView bound to Backend property
ListView {
    model: Backend.macros

    delegate: MacroCard {
        macroData: modelData
        onStarted: Backend.start_macro(modelData.name)
        onStopped: Backend.stop_macro(modelData.name)
        onDeleted: Backend.delete_macro(modelData.name)
    }
}
```

For dynamic models updated via signals:

```qml
// QML — model updated on signal
ListModel {
    id: skillsModel
}

Connections {
    target: Backend
    function onSettingsChanged() {
        skillsModel.clear()
        var list = Backend.skill_list
        for (var i = 0; i < list.length; i++) {
            skillsModel.append(list[i])
        }
    }
}
```

### Pattern 5: Page Navigation via Signal

Python initiates navigation; QML executes it:

```python
# Python — emit signal to request page change
def edit_macro(self, name):
    self.macro_crud.edit_macro(name)
    self.pageChangeRequested.emit("MacrosEditPage.qml")

def open_activation_page(self):
    self.pageChangeRequested.emit("ActivationPage.qml")
```

```qml
// main.qml — central navigation handler
Connections {
    target: Backend
    function onPageChangeRequested(page) {
        stackView.push("qrc:/qml/" + page)
    }
}

// Individual pages can also navigate directly
Button {
    text: "Settings"
    onClicked: stackView.push("qrc:/qml/SettingsPage.qml")
}
```

### Pattern 6: Component Delegation

Complex UI logic is split between QML components and Python managers:

```qml
// CastBarDialog.qml — UI collects calibration data
MouseArea {
    anchors.fill: parent
    onClicked: {
        // Capture coordinates from mouse click
        var color = Backend.captureCastbarColorAt(mouseX, mouseY, 1)
        colorPreview.color = "#" + rgbToHex(color)
    }
}

Button {
    text: "Save"
    onClicked: {
        Backend.set_setting("castbar_point", pointText)
        Backend.set_setting("castbar_color", colorText)
        Backend.stopCastbarCalibration()
        close()
    }
}
```

```python
# Python — backend handles the heavy lifting
@Slot(int, int, int, result=str)
def captureCastbarColorAt(self, x, y, size=1):
    # mss screenshot, pixel capture, return "R,G,B"
    color = self.castbar_detector.capture_castbar_color_at(x, y, size)
    self.castbarColorCaptured.emit(f"{x},{y}", color)
    return color

@Slot()
def stopCastbarCalibration(self):
    # Async hook stop via QTimer.singleShot
    self._calibration_active = False
    QTimer.singleShot(0, self._stop_calibration_hook)
```

---

## 4. Theme Customization

### Accent Color

The accent color is stored in settings and propagated to all components:

```python
# Python default
ALLOWED_SETTINGS["accent_color"] = {"type": str, "default": "#fd79a8"}
```

```qml
// QML — property binding with fallback
property color accentColor: Backend.settings.accent_color || "#fd79a8"

// Usage in components
Rectangle {
    color: accentColor
    radius: 4
}
```

### Dark Theme

The application uses a dark color palette:

```qml
// Common dark theme colors
property color bgPrimary: "#1a1a1a"
property color bgSecondary: "#252525"
property color bgTertiary: "#2a2a2a"
property color textPrimary: "#ffffff"
property color textSecondary: "#aaaaaa"
property color border: "#3a3a3a"

// Application window background
ApplicationWindow {
    color: bgPrimary
}
```

### Runtime Theme Updates

When `accent_color` changes in settings, all bound components update automatically:

```qml
Connections {
    target: Backend
    function onSettingsChanged() {
        // All bindings to Backend.settings.accent_color update automatically
    }
}
```

---

## 5. Reusable Components

### FormRow.qml

Label + input field row for settings forms:

```qml
RowLayout {
    property alias label: lbl.text
    property alias value: field.text
    property alias placeholder: field.placeholderText

    Label { id: lbl; color: textPrimary }
    TextField {
        id: field
        placeholderText: placeholder
        // Styled with dark theme
    }
}

// Usage
FormRow {
    label: "Ping"
    value: Backend.settings.average_ping
    onValueChanged: Backend.set_setting("average_ping", value)
}
```

### MacroCard.qml

Card displaying a single macro in the list:

```qml
Rectangle {
    property var macroData
    property bool isRunning: macroData.running

    color: isRunning ? accentColor : bgSecondary

    // Displays: name, type, hotkey, status
    // Buttons: Start/Stop, Edit, Delete
}
```

### StyledButton.qml

Themed button with accent color support:

```qml
Button {
    property color accentColor: Backend.settings.accent_color || "#fd79a8"
    property bool primary: false

    background: Rectangle {
        color: parent.primary ? accentColor : bgSecondary
        radius: 4
    }

    contentItem: Text {
        color: parent.primary ? "#000" : textPrimary
        text: parent.text
    }
}
```

### ToggleSwitch.qml

On/off switch styled with accent color:

```qml
Switch {
    property color accentColor: Backend.settings.accent_color || "#fd79a8"

    indicator: Rectangle {
        color: parent.checked ? accentColor : bgTertiary
        // Animated indicator
    }
}
```

### NumberField.qml

Validated numeric input:

```qml
TextField {
    property int minValue: 0
    property int maxValue: 9999
    property alias value: field.text

    // Validates on focus loss
    onEditingFinished: {
        var v = parseInt(text)
        if (v < minValue) text = minValue
        if (v > maxValue) text = maxValue
    }
}
```

### SettingGroup.qml

Grouped settings section with header:

```qml
Rectangle {
    property alias title: titleLabel.text
    color: bgSecondary
    radius: 8

    ColumnLayout {
        Label { id: titleLabel; font.bold: true }
        // Content slot
    }
}
```

---

## Quick Reference

| Pattern | Python Side | QML Side |
|---------|------------|----------|
| Signal → Handler | `mySignal = Signal(type)` | `function onMySignal(arg) { }` |
| Property | `@Property(type, notify=signal)` | `Backend.propertyName` |
| Slot call | `@Slot(args)` | `Backend.methodName()` |
| ListModel | `@Property(list)` | `model: Backend.macros` |
| Navigation | `pageChangeRequested.emit("Page.qml")` | `stackView.push(...)` |
| Delegation | Backend → Manager method | Component → Backend slot |
