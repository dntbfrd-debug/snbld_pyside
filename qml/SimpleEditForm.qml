import QtQuick 2.15
import QtQuick.Controls.Basic 2.15
import QtQuick.Layouts 1.15

Item {
    id: root

    property string accentColor: backend && backend.settings ? backend.settings.accent_color : "#7793a1"

    property alias macroName: nameField.text
    property alias macroHotkey: hotkeyField.text
    property var stepsModel: []
    property var editingMacro: null

    // Доступ к StackView из родителя
    property alias editStackView: root.parent

    Component.onCompleted: {
        console.log("SimpleEditForm Component.onCompleted, editingMacro=", editingMacro ? editingMacro.name : "null")
        if (editingMacro) {
            loadFromMacro(editingMacro)
        }
    }
    
    onEditingMacroChanged: {
        console.log("SimpleEditForm onEditingMacroChanged, editingMacro=", editingMacro ? editingMacro.name : "null")
        if (editingMacro && !dataLoaded) {
            loadFromMacro(editingMacro)
            dataLoaded = true
        }
    }
    
    property bool dataLoaded: false

    function loadFromMacro(macro) {
        if (!macro) {
            console.log("SimpleEditForm.loadFromMacro: macro is null/undefined")
            return
        }
        nameField.text = macro["name"] || ""
        hotkeyField.text = macro["hotkey"] || ""
        stepsModel = []
        var steps = macro["steps"]
        if (steps) {
            for (var i = 0; i < steps.length; ++i) {
                var step = steps[i]
                stepsModel.push({ action: step[0], value: step[1], delay: step[2] })
            }
        }
        stepsView.model = stepsModel
        editingMacro = macro
    }

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 10
        spacing: 8

        // Верхняя строка: Название + Горячая клавиша
        RowLayout {
            Layout.fillWidth: true
            spacing: 8

            ColumnLayout {
                Layout.fillWidth: true
                spacing: 2
                Label { 
                    text: "💀 Название:"
                    color: "#c2c2c2"
                    font.pointSize: 9
                }
                TextField {
                    id: nameField
                    Layout.fillWidth: true
                    Layout.preferredHeight: 24
                    placeholderText: "Название макроса"
                    font.pointSize: 10
                    background: Rectangle { radius: 4; color: "#40ffffff" }
                }
            }

            ColumnLayout {
                Layout.preferredWidth: 150
                spacing: 2
                Label {
                    text: "◈ Горячая клавиша:"
                    color: "#c2c2c2"
                    font.pointSize: 9
                }
                TextField {
                    id: hotkeyField
                    Layout.fillWidth: true
                    Layout.preferredHeight: 24
                    placeholderText: "Нажмите клавишу"
                    font.pointSize: 10
                    background: Rectangle { radius: 4; color: "#40ffffff" }
                    
                    // Перехват нажатий клавиш
                    Keys.onPressed: {
                        event.accepted = true
                        
                        // Backspace - очистка поля
                        if (event.key === Qt.Key_Backspace) {
                            hotkeyField.text = ""
                            return
                        }
                        
                        // Escape - отмена
                        if (event.key === Qt.Key_Escape) {
                            return
                        }
                        
                        var modifiers = []
                        var keyName = ""
                        
                        // Собираем модификаторы
                        if (event.modifiers & Qt.ControlModifier) modifiers.push("ctrl")
                        if (event.modifiers & Qt.AltModifier) modifiers.push("alt")
                        if (event.modifiers & Qt.ShiftModifier) modifiers.push("shift")
                        
                        // Определяем клавишу
                        var key = event.key
                        
                        // Функциональные клавиши
                        if (key >= Qt.Key_F1 && key <= Qt.Key_F12) {
                            keyName = "f" + (key - Qt.Key_F1 + 1)
                        }
                        // Буквы
                        else if (key >= Qt.Key_A && key <= Qt.Key_Z) {
                            keyName = String.fromCharCode(key).toLowerCase()
                        }
                        // Цифры (основной ряд) - обрабатываем с учётом Shift
                        else if (key >= Qt.Key_0 && key <= Qt.Key_9) {
                            // Если нажат Shift, то показываем символы с верхней клавиатуры
                            if (event.modifiers & Qt.ShiftModifier) {
                                var shiftSymbols = ["!", "@", "#", "$", "%", "^", "&", "*", "(", ")"]
                                keyName = shiftSymbols[key - Qt.Key_0]
                            } else {
                                keyName = String.fromCharCode(key)
                            }
                        }
                        // Цифровая клавиатура
                        else if (key >= Qt.Key_0 && key <= Qt.Key_9) {
                            keyName = String.fromCharCode(key)
                        }
                        // Спецклавиши
                        else if (key === Qt.Key_Minus || key === Qt.Key_Hyphen) keyName = event.modifiers & Qt.ShiftModifier ? "_" : "-"
                        else if (key === Qt.Key_Equal || key === Qt.Key_Plus) keyName = event.modifiers & Qt.ShiftModifier ? "+" : "="
                        else if (key === Qt.Key_BracketLeft) keyName = event.modifiers & Qt.ShiftModifier ? "{" : "["
                        else if (key === Qt.Key_BracketRight) keyName = event.modifiers & Qt.ShiftModifier ? "}" : "]"
                        else if (key === Qt.Key_Backslash) keyName = event.modifiers & Qt.ShiftModifier ? "|" : "\\"
                        else if (key === Qt.Key_Semicolon) keyName = event.modifiers & Qt.ShiftModifier ? ":" : ";"
                        else if (key === Qt.Key_Apostrophe) keyName = event.modifiers & Qt.ShiftModifier ? '"' : "'"
                        else if (key === Qt.Key_Comma) keyName = event.modifiers & Qt.ShiftModifier ? "<" : ","
                        else if (key === Qt.Key_Period) keyName = event.modifiers & Qt.ShiftModifier ? ">" : "."
                        else if (key === Qt.Key_Slash) keyName = event.modifiers & Qt.ShiftModifier ? "?" : "/"
                        else if (key === Qt.Key_QuoteLeft) keyName = event.modifiers & Qt.ShiftModifier ? "~" : "`"
                        else if (key === Qt.Key_Space) keyName = "space"
                        else if (key === Qt.Key_Tab) keyName = "tab"
                        else if (key === Qt.Key_Return || key === Qt.Key_Enter) keyName = "enter"
                        else if (key === Qt.Key_Delete) keyName = "delete"
                        else if (key === Qt.Key_Up) keyName = "up"
                        else if (key === Qt.Key_Down) keyName = "down"
                        else if (key === Qt.Key_Left) keyName = "left"
                        else if (key === Qt.Key_Right) keyName = "right"
                        else if (key === Qt.Key_Home) keyName = "home"
                        else if (key === Qt.Key_End) keyName = "end"
                        else if (key === Qt.Key_PageUp) keyName = "page up"
                        else if (key === Qt.Key_PageDown) keyName = "page down"
                        else if (key === Qt.Key_Insert) keyName = "insert"
                        else if (key === Qt.Key_CapsLock) keyName = "caps lock"
                        else {
                            // Неизвестная клавиша - показываем код
                            keyName = "key_" + key
                        }
                        
                        // Собираем комбинацию
                        if (modifiers.length > 0) {
                            hotkeyField.text = modifiers.join("+") + "+" + keyName
                        } else {
                            hotkeyField.text = keyName
                        }
                    }
                }
            }
        }

        // Вторая строка: Список шагов + Кнопки
        RowLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            spacing: 10

            // Левая часть - Список шагов
            ColumnLayout {
                Layout.fillWidth: true
                Layout.fillHeight: true
                spacing: 4

                RowLayout {
                    Layout.fillWidth: true
                    Label {
                        text: "☠ Шаги макроса:"
                        color: "#c2c2c2"
                        font.pointSize: 10
                    }
                    Label {
                        text: stepsModel.length + " шаг(ов)"
                        color: "#7793a1"
                        font.pointSize: 9
                        Layout.alignment: Qt.AlignRight
                        Layout.fillWidth: true
                        horizontalAlignment: Text.AlignRight
                    }
                }

                Rectangle {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    color: "#20000000"
                    radius: 4
                    border.color: "#40ffffff"
                    border.width: 1
                    clip: true

                    ListView {
                        id: stepsView
                        anchors.fill: parent
                        anchors.margins: 4
                        model: stepsModel
                        clip: true
                        ScrollBar.vertical: ScrollBar {
                            policy: ScrollBar.AsNeeded
                            width: 8
                        }

                        delegate: Rectangle {
                            width: stepsView.width - 10
                            height: 26
                            color: index % 2 ? "#25ffffff" : "#15ffffff"
                            radius: 3
                            RowLayout {
                                anchors.fill: parent
                                anchors.margins: 3
                                spacing: 4
                                Text {
                                    text: modelData.action === "key" ? "◈ " + modelData.value :
                                          modelData.action === "left" ? "◈ ЛКМ" :
                                          modelData.action === "right" ? "◈ ПКМ" :
                                          "◈ Пауза"
                                    color: "#c2c2c2"
                                    font.pointSize: 9
                                    Layout.fillWidth: true
                                    elide: Text.ElideRight
                                }
                                Text {
                                    text: modelData.delay + " мс"
                                    color: "#a0a0a0"
                                    font.pointSize: 8
                                    Layout.preferredWidth: 45
                                    horizontalAlignment: Text.AlignRight
                                }
                                Rectangle {
                                    id: deleteBtn
                                    implicitWidth: 18
                                    implicitHeight: 18
                                    radius: 9
                                    color: deleteArea.containsMouse ? "#c74646" : "#50ffffff"
                                    border.color: "#70ffffff"
                                    border.width: 1

                                    Text {
                                        text: "×"
                                        font.pointSize: 14
                                        font.bold: true
                                        color: "#ffffff"
                                        anchors.centerIn: parent
                                        renderType: Text.NativeRendering
                                    }

                                    MouseArea {
                                        id: deleteArea
                                        anchors.fill: parent
                                        hoverEnabled: true
                                        cursorShape: Qt.PointingHandCursor
                                        onClicked: {
                                            stepsModel.splice(index, 1)
                                            stepsView.model = stepsModel
                                        }
                                    }
                                }
                            }
                        }
                    }
                }

                // Кнопки добавления шагов - 2 строки
                RowLayout {
                    Layout.fillWidth: true
                    spacing: 4
                    BaseButton {
                        text: "◈ Клавиша"
                        Layout.fillWidth: true
                        implicitHeight: 24
                        iconSize: 10
                        textSize: 8
                        onClicked: addDialog.openFor("key")
                    }
                    BaseButton {
                        text: "◈ ЛКМ"
                        Layout.fillWidth: true
                        implicitHeight: 24
                        iconSize: 10
                        textSize: 8
                        onClicked: addStep("left", "", 10)
                    }
                    BaseButton {
                        text: "◈ ПКМ"
                        Layout.fillWidth: true
                        implicitHeight: 24
                        iconSize: 10
                        textSize: 8
                        onClicked: addStep("right", "", 10)
                    }
                }
                RowLayout {
                    Layout.fillWidth: true
                    spacing: 4
                    BaseButton {
                        text: "◈ Пауза"
                        Layout.fillWidth: true
                        implicitHeight: 24
                        iconSize: 10
                        textSize: 8
                        onClicked: addDialog.openFor("pause")
                    }
                }
            }

            // Правая часть — подсказки (тот же стиль, что и у скилл-формы)
            ColumnLayout {
                Layout.preferredWidth: 200
                Layout.fillHeight: true
                spacing: 6

                Rectangle {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    color: "#99252525"
                    radius: 8
                    border.color: "#50ffffff"
                    border.width: 2

                    ColumnLayout {
                        anchors.fill: parent
                        anchors.margins: 10
                        spacing: 8

                        Label {
                            text: "◈ Подсказки"
                            color: root.accentColor
                            font.pointSize: 10
                            font.bold: true
                        }
                        Rectangle {
                            width: parent.width
                            height: 1
                            color: "#45ffffff"
                        }
                        Text {
                            text: "Введите название и горячую клавишу.\n\nДобавьте шаги: клавиша, ЛКМ, ПКМ или пауза — для каждого шага задаётся задержка в миллисекундах.\n\nШаги выполняются по порядку сверху вниз. Нажмите «Сохранить», когда всё готово."
                            color: "#d8d8d8"
                            font.pointSize: 9
                            wrapMode: Text.WordWrap
                            Layout.fillWidth: true
                        }
                    }
                }
            }
        }

        // Кнопки Сохранить / Отмена
        RowLayout {
            Layout.alignment: Qt.AlignHCenter
            Layout.preferredHeight: 40
            spacing: 30

            BaseButton {
                text: "◈ Сохранить"
                implicitWidth: 120
                implicitHeight: 36
                iconSize: 14
                textSize: 10
                onClicked: {
                    if (nameField.text.trim() === "") {
                        backend.notification("Введите название макроса", "warning")
                        return
                    }
                    var stepsList = []
                    for (var i = 0; i < stepsModel.length; ++i) {
                        var step = stepsModel[i]
                        stepsList.push([step.action, step.value, step.delay])
                    }
                    if (stepsList.length === 0) {
                        backend.notification("Добавьте хотя бы один шаг", "warning")
                        return
                    }

                    if (editingMacro) {
                        backend.update_simple_macro(editingMacro["name"], nameField.text, hotkeyField.text, stepsList)
                    } else {
                        backend.create_simple_macro_with_params(nameField.text, hotkeyField.text, stepsList)
                    }
                    backend.clear_macro_for_edit()
                    backend.pageChangeRequested("MacrosListPage.qml")
                }
            }
            BaseButton {
                text: "☠ Отмена"
                implicitWidth: 120
                implicitHeight: 36
                iconSize: 14
                textSize: 10
                onClicked: {
                    backend.clear_macro_for_edit()
                    backend.pageChangeRequested("MacrosListPage.qml")
                }
            }
        }
    }

    AddStepDialog {
        id: addDialog
        onStepAdded: function(type, value, delay) {
            addStep(type, value, delay)
        }
    }

    function addStep(type, value, delay) {
        stepsModel.push({ action: type, value: value, delay: delay })
        stepsView.model = stepsModel
    }
}
