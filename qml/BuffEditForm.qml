import QtQuick 2.15
import QtQuick.Controls.Basic 2.15
import QtQuick.Layouts 1.15

Item {
    id: root

    property string accentColor: backend && backend.settings ? backend.settings.accent_color : "#7793a1"

    property var editingMacro: null
    property var buff: null
    property string buffId: ""
    property string buffName: ""
    property double buffDuration: 0
    property int channelingBonus: 0
    property string buffHotkey: "1"
    property int macroType: 0
    property var selectedArea: null
    property var stepsModel: []

    property alias editStackView: root.parent
    property bool dataLoaded: false

    // Точка клика баффа
    property string buffClickPoint: backend ? backend.getBuffClickPoint() : "0,0"

    // Извлекает последнюю клавишу из комбинации (ctrl+shift+e → e)
    function getLastKey(hotkey) {
        if (!hotkey || hotkey === "") return ""
        var parts = hotkey.split("+")
        return parts[parts.length - 1]
    }

    signal saveRequested()

    function loadFromMacro(macro) {
        console.log("BuffEditForm.loadFromMacro:", macro.name, "zone_rect=", macro["zone_rect"])
        nameField.text = macro["name"]
        buffHotkey = macro["hotkey"] || "1"
        buffHotkeyField.text = buffHotkey
        buffId = macro["buff_id"] ? macro["buff_id"].toString() : ""
        buffDuration = macro["duration"] || 0
        channelingBonus = macro["channeling_bonus"] || 0

        // Загружаем точку клика
        buffClickPoint = backend ? backend.getBuffClickPoint() : "0,0"
        if (buffClickPointField) {
            buffClickPointField.text = buffClickPoint
        }

        if (buffId) {
            var foundBuff = findBuffById(buffId)
            if (foundBuff) {
                buffName = foundBuff.name
                buffDuration = foundBuff.duration
                channelingBonus = foundBuff.channeling_bonus
                // ✅ Автоподстановка названия баффа если имя пустое
                if (nameField.text === "") {
                    nameField.text = buffName
                }
            }
        }

        stepsModel = []
        var steps = macro["steps"]
        if (steps && steps.length > 0) {
            for (var i = 0; i < steps.length; ++i) {
                var step = steps[i]
                stepsModel.push({ action: step[0], value: step[1], delay: step[2] })
            }
        } else {
            // ✅ Если шагов нет - создаём 3 стандартных
            addDefaultSteps()
        }
        
        Qt.callLater(function() {
            stepsView.model = stepsModel
        })
        editingMacro = macro

        // ✅ Определяем тип по наличию zone_rect
        if (macro["zone_rect"] && macro["zone_rect"].length > 0) {
            macroType = 1
            selectedArea = []
            for (var i = 0; i < macro["zone_rect"].length; i++) {
                selectedArea.push(macro["zone_rect"][i])
            }
            zoneAreaField.text = selectedArea.join(",")
        } else {
            macroType = 0
            selectedArea = null
            zoneAreaField.text = "Не выбрана"
        }
        console.log("BuffEditForm: macroType =", macroType, "selectedArea=", selectedArea)

        // ✅ Обновляем ComboBox типа макроса
        typeCombo.currentIndex = macroType

        buffInfoField.text = buffId ? (buffName + " (ID: " + buffId + ")") : "Не выбран"
        durationField.text = buffDuration.toString()
        channelingField.text = channelingBonus.toString()
    }

    function findBuffById(id) {
        var skills = backend.skill_list
        for (var i = 0; i < skills.length; ++i) {
            if (skills[i].id.toString() === id.toString()) {
                return skills[i]
            }
        }
        return null
    }

    function onBuffSelected(buffData) {
        console.log("BuffEditForm.onBuffSelected:", buffData.name)
        buffId = buffData.id.toString()
        buffName = buffData.name
        buffDuration = buffData.duration
        channelingBonus = buffData.channeling_bonus || 0
        buffInfoField.text = buffName + " (ID: " + buffId + ")"
        durationField.text = buffDuration.toString()
        channelingField.text = channelingBonus.toString()
        if (!editingMacro) {
            nameField.text = buffName
        }
        // ✅ Создаём 3 стандартных шага если их нет
        if (stepsModel.length === 0) {
            addDefaultSteps()
        }
        // ✅ Обновляем ComboBox типа макроса
        typeCombo.currentIndex = macroType
    }

    function setSelectedArea(x1, y1, x2, y2) {
        console.log("BuffEditForm.setSelectedArea:", x1, y1, x2, y2)
        selectedArea = [x1, y1, x2, y2]
        zoneAreaField.text = x1 + "," + y1 + "," + x2 + "," + y2
    }

    function updateStepForType() {
        if (stepsModel.length < 3) {
            addDefaultSteps()
            return
        }

        var usePingDelays = backend.settings.use_ping_delays || false
        var stepDelay = usePingDelays ? Math.round(backend.getPingCompensation() * 1000) : (backend.settings.global_step_delay || 20)

        if (macroType === 0) {
            var key = getLastKey(buffHotkey) || "1"
            stepsModel[1] = { action: "key", value: key, delay: stepDelay }
            selectedArea = null
            zoneAreaField.text = "Не выбрана"
        } else {
            stepsModel[1] = { action: "left", value: "", delay: stepDelay }
        }
        
        Qt.callLater(function() {
            stepsView.model = stepsModel
        })
    }

    function addDefaultSteps() {
        stepsModel = []
        var swapChant = backend.settings.swap_key_chant || "e"
        var swapPa = backend.settings.swap_key_pa || "e"
        var delay = backend.settings.global_step_delay || 20
        var firstStepDelay = backend.settings.first_step_delay || 100
        var hk = buffHotkey || "1"

        stepsModel.push({ action: "key", value: swapChant, delay: firstStepDelay })

        if (macroType === 0) {
            var key = getLastKey(hk) || "1"
            stepsModel.push({ action: "key", value: key, delay: delay })
        } else {
            stepsModel.push({ action: "left", value: "", delay: 10 })
        }

        stepsModel.push({ action: "key", value: swapPa, delay: delay })
        
        // Обновляем модель через Qt.callLater для корректной реактивности
        Qt.callLater(function() {
            stepsView.model = stepsModel
        })
    }

    function syncBuffHotkey() {
        if (stepsModel.length >= 2 && stepsModel[1].action === "key") {
            // Используем getLastKey() чтобы извлечь клавишу из комбинации
            stepsModel[1].value = getLastKey(buffHotkeyField.text)
            Qt.callLater(function() {
                stepsView.model = stepsModel
            })
        }
    }

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 20
        spacing: 15

        RowLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            spacing: 10

            ColumnLayout {
                Layout.fillWidth: true
                Layout.fillHeight: true
                spacing: 15

        // Название + Горячая клавиша + Тип + Бафф
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
                    font.pointSize: 10
                    background: Rectangle { radius: 4; color: "#40ffffff" }
                }
            }

            ColumnLayout {
                Layout.preferredWidth: 120
                spacing: 2
                Label {
                    text: "◈ Горячая клавиша:"
                    color: "#c2c2c2"
                    font.pointSize: 9
                }
                TextField {
                    id: buffHotkeyField
                    Layout.fillWidth: true
                    Layout.preferredHeight: 24
                    text: buffHotkey
                    font.pointSize: 10
                    background: Rectangle { radius: 4; color: "#40ffffff" }
                    Keys.onPressed: {
                        event.accepted = true
                        if (event.key === Qt.Key_Backspace) {
                            buffHotkeyField.text = ""
                            buffHotkey = ""
                            return
                        }
                        if (event.key === Qt.Key_Escape) return

                        var modifiers = []
                        if (event.modifiers & Qt.ControlModifier) modifiers.push("ctrl")
                        if (event.modifiers & Qt.AltModifier) modifiers.push("alt")
                        if (event.modifiers & Qt.ShiftModifier) modifiers.push("shift")

                        var keyName = ""
                        var key = event.key
                        if (key >= Qt.Key_F1 && key <= Qt.Key_F12) keyName = "f" + (key - Qt.Key_F1 + 1)
                        else if (key >= Qt.Key_A && key <= Qt.Key_Z) keyName = String.fromCharCode(key).toLowerCase()
                        else if (key >= Qt.Key_0 && key <= Qt.Key_9) keyName = String.fromCharCode(key)
                        else keyName = "key_" + key

                        if (modifiers.length > 0) {
                            buffHotkeyField.text = modifiers.join("+") + "+" + keyName
                        } else {
                            buffHotkeyField.text = keyName
                        }
                        buffHotkey = buffHotkeyField.text

                        if (macroType === 0 && stepsModel.length >= 2) {
                            syncBuffHotkey()
                        }
                    }
                }
            }

            ColumnLayout {
                Layout.preferredWidth: 150
                spacing: 2
                Label {
                    text: "◈ Тип макроса:"
                    color: "#c2c2c2"
                    font.pointSize: 9
                }
                ComboBox {
                    id: typeCombo
                    Layout.fillWidth: true
                    Layout.preferredHeight: 28
                    model: ListModel {
                        ListElement { text: "По горячей клавише" }
                        ListElement { text: "По области" }
                    }
                    currentIndex: macroType
                    font.pointSize: 9
                    popup.background: Rectangle {
                        color: "#2a2a2a"
                        radius: 4
                    }
                    delegate: ItemDelegate {
                        id: delegateItem
                        width: parent.width
                        height: 30
                        contentItem: Text {
                            text: model.text
                            color: "#c2c2c2"
                            font.pointSize: 9
                            verticalAlignment: Text.AlignVCenter
                        }
                        background: Rectangle {
                            radius: 4
                            color: "#30ffffff"
                            Rectangle {
                                anchors.fill: parent
                                radius: 4
                                gradient: Gradient {
                                    GradientStop { position: 0.0; color: Qt.rgba(backend.settings.accent_color.r, backend.settings.accent_color.g, backend.settings.accent_color.b, delegateItem.hovered ? 0.5 : 0) }
                                    GradientStop { position: 1.0; color: Qt.rgba(backend.settings.accent_color.r, backend.settings.accent_color.g, backend.settings.accent_color.b, delegateItem.hovered ? 0.3 : 0) }
                                }
                                Behavior on opacity {
                                    NumberAnimation { duration: 150; easing.type: Easing.InOutQuad }
                                }
                                opacity: delegateItem.hovered ? 1 : 0
                            }
                        }
                    }
                    background: Rectangle {
                        color: "#40ffffff"
                        radius: 4
                        border.color: "#50ffffff"
                        border.width: 1
                    }
                    onCurrentIndexChanged: {
                        macroType = currentIndex
                        updateStepForType()
                    }
                }
            }

            ColumnLayout {
                Layout.fillWidth: true
                spacing: 2
                Label {
                    text: "✦ Бафф:"
                    color: "#c2c2c2"
                    font.pointSize: 9
                }
                TextField {
                    id: buffInfoField
                    Layout.fillWidth: true
                    Layout.preferredHeight: 24
                    readOnly: true
                    font.pointSize: 10
                    background: Rectangle { radius: 4; color: "#40ffffff" }
                }
            }
        }

        // Область (только для типа "По области")
        RowLayout {
            Layout.fillWidth: true
            spacing: 8
            visible: macroType === 1

            Label {
                text: "📍 Область:"
                color: "#c2c2c2"
                font.pointSize: 9
                Layout.preferredWidth: 60
            }
            TextField {
                id: zoneAreaField
                Layout.fillWidth: true
                Layout.preferredHeight: 24
                readOnly: true
                text: selectedArea ? selectedArea.join(",") : "Не выбрана"
                font.pointSize: 8
                background: Rectangle {
                    radius: 3
                    color: zoneAreaField.text !== "Не выбрана" ? "#404CAF50" : "#40ffffff"
                }
            }
            BaseButton {
                text: "Выбрать"
                Layout.preferredWidth: 70
                implicitHeight: 24
                iconSize: 0
                textSize: 8
                onClicked: backend.selectAreaForMacro()
            }
        }

        // Параметры баффа
        RowLayout {
            Layout.fillWidth: true
            spacing: 8

            ColumnLayout {
                Layout.fillWidth: true
                spacing: 2
                Label { text: "⏱ Длительность (сек):"; color: "#c2c2c2"; font.pointSize: 9 }
                TextField {
                    id: durationField
                    Layout.fillWidth: true
                    Layout.preferredHeight: 24
                    text: buffDuration.toString()
                    font.pointSize: 10
                    validator: DoubleValidator { bottom: 0; decimals: 1 }
                    background: Rectangle { radius: 4; color: "#40ffffff" }
                    onTextChanged: buffDuration = parseFloat(text) || 0
                }
            }

            ColumnLayout {
                Layout.fillWidth: true
                spacing: 2
                Label { text: "🚀 Бонус пения (%):"; color: "#c2c2c2"; font.pointSize: 9 }
                TextField {
                    id: channelingField
                    Layout.fillWidth: true
                    Layout.preferredHeight: 24
                    text: channelingBonus.toString()
                    font.pointSize: 10
                    validator: IntValidator { bottom: 0; top: 100 }
                    background: Rectangle { radius: 4; color: "#40ffffff" }
                    onTextChanged: channelingBonus = parseInt(text) || 0
                }
            }
        }

        // Точка клика для баффа (Светлая опека)
        Rectangle {
            Layout.fillWidth: true
            height: 40
            color: "#15ffffff"
            radius: 6
            border.color: "#30ffffff"
            border.width: 1

            RowLayout {
                anchors.fill: parent
                anchors.margins: 8
                spacing: 8

                Text {
                    text: "🎯 Точка клика:"
                    color: "#c2c2c2"
                    font.pointSize: 9
                    font.bold: true
                }

                TextField {
                    id: buffClickPointField
                    Layout.fillWidth: true
                    Layout.preferredHeight: 24
                    readOnly: true
                    text: buffClickPoint
                    font.pointSize: 9
                    color: buffClickPoint !== "0,0" ? "#4CAF50" : "#808080"
                    background: Rectangle {
                        radius: 4
                        color: buffClickPoint !== "0,0" ? "#204CAF50" : "#20ffffff"
                    }
                }

                BaseButton {
                    text: buffClickPoint !== "0,0" ? "⟲ Калибровать" : "◈ Калибровать"
                    implicitWidth: 100
                    implicitHeight: 28
                    iconSize: 0
                    textSize: 9
                    accentColor: buffClickPoint !== "0,0" ? "#4CAF50" : backend.settings.accent_color
                    onClicked: {
                        console.log("BuffEditForm: Запуск калибровки точки клика")
                        buffCalibDialog.calibrationState = "ready"
                        buffCalibDialog.selectedPoint = buffClickPoint
                        buffCalibDialog.visible = true
                        buffCalibDialog.raise()
                        buffCalibDialog.requestActivate()
                    }
                }

                BaseButton {
                    text: "⚡ Тест"
                    implicitWidth: 70
                    implicitHeight: 28
                    iconSize: 0
                    textSize: 9
                    visible: buffClickPoint !== "0,0"
                    accentColor: "#FF9800"
                    onClicked: {
                        console.log("BuffEditForm: Тест клика в точку", buffClickPoint)
                        backend.performBuffClick()
                        backend.notification("Тестовый клик выполнен в точке " + buffClickPoint, "info")
                    }
                }
            }
        }

        // Список шагов
        ColumnLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            spacing: 4

            Label { text: "📋 Шаги макроса:"; color: "#c2c2c2"; font.pointSize: 9 }

            ListView {
                id: stepsView
                Layout.fillWidth: true
                Layout.fillHeight: true
                model: stepsModel
                clip: true
                delegate: Rectangle {
                    width: stepsView.width
                    height: 28
                    color: index % 2 === 0 ? "#20ffffff" : "#10ffffff"
                    RowLayout {
                        anchors.fill: parent
                        anchors.margins: 4
                        spacing: 4
                        Text { text: (index + 1) + "."; color: "#7793a1"; width: 20 }
                        Text {
                            text: modelData.action === "key" ? "Клавиша" :
                                  modelData.action === "left" ? "ЛКМ" :
                                  modelData.action === "right" ? "ПКМ" :
                                  "Пауза"
                            color: "#c2c2c2"
                            width: 80
                        }
                        Text { text: modelData.value || ""; color: "#c2c2c2"; width: 60 }
                        Text { text: (modelData.delay !== undefined ? modelData.delay : 0) + " мс"; color: "#a0a0a0" }
                        Item { Layout.fillWidth: true }
                        BaseButton {
                            text: "✕"
                            implicitWidth: 24
                            implicitHeight: 24
                            iconSize: 0
                            textSize: 10
                            onClicked: {
                                stepsModel.splice(index, 1)
                                stepsView.model = stepsModel
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

            }

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
                            text: "Выберите бафф из списка — подставятся длительность и бонус пения.\n\n«По горячей клавише» — запуск по клавише; «По области» — клик в выделенной зоне экрана (ЛКМ/ПКМ).\n\nКалибровка «Точки клика» нужна, если макрос должен кликать по иконке баффа.\n\nШаги по умолчанию: смена пения → клавиша баффа или ЛКМ в зоне → смена ПА."
                            color: "#d8d8d8"
                            font.pointSize: 9
                            wrapMode: Text.WordWrap
                            Layout.fillWidth: true
                        }
                    }
                }
            }
        }

        // Кнопки
        RowLayout {
            Layout.fillWidth: true
            Layout.preferredHeight: 55
            spacing: 0
            Item { Layout.fillWidth: true }
            BaseButton {
                text: "💾 Сохранить"
                implicitWidth: 160
                implicitHeight: 38
                iconSize: 14
                textSize: 10
                onClicked: {
                    var stepsList = []
                    for (var i = 0; i < stepsModel.length; ++i) {
                        var step = stepsModel[i]
                        stepsList.push([step.action, step.value, step.delay])
                    }
                    if (stepsList.length === 0) {
                        backend.notification("Добавьте хотя бы один шаг", "warning")
                        return
                    }

                    var zoneRect = []
                    if (selectedArea && selectedArea.length) {
                        for (var i = 0; i < selectedArea.length; i++) {
                            zoneRect.push(selectedArea[i])
                        }
                    }
                    console.log("BuffEditForm.save: zoneRect=", zoneRect)

                    if (editingMacro) {
                        backend.update_buff_macro(
                            editingMacro["name"], nameField.text, buffHotkey,
                            buffId, stepsList, buffDuration, channelingBonus, zoneRect
                        )
                    } else {
                        backend.create_buff_macro_with_params(
                            nameField.text, buffHotkey,
                            buffId, stepsList, buffDuration, channelingBonus, zoneRect
                        )
                    }
                    backend.clear_macro_for_edit()
                    backend.pageChangeRequested("MacrosListPage.qml")
                    backend.notification("Бафф-макрос '" + nameField.text + "' сохранён", "success")
                    saveRequested()
                }
            }
            Item { Layout.fillWidth: true }
        }
    }

    Connections {
        target: backend
        function onZoneAreaSelectedSignal(zoneRect) {
            console.log("BuffEditForm: onZoneAreaSelectedSignal, zoneRect=", zoneRect)
            if (zoneRect && zoneRect.length === 4) {
                setSelectedArea(zoneRect[0], zoneRect[1], zoneRect[2], zoneRect[3])
            }
        }
    }

    // Диалог калибровки точки клика
    BuffCalibrationDialog {
        id: buffCalibDialog
        onPointCaptured: function(point) {
            console.log("BuffEditForm: Точка захвачена:", point)
            buffClickPoint = point
            backend.onBuffPointCaptured(point)
            buffClickPointField.text = point
        }
        onCalibrationCancelled: {
            console.log("BuffEditForm: Калибровка отменена")
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

    Component.onCompleted: {
        console.log("BuffEditForm Component.onCompleted, buff=", buff ? buff.name : "null")
        
        if (editingMacro) {
            loadFromMacro(editingMacro)
            dataLoaded = true
        } else if (buff) {
            onBuffSelected(buff)
            dataLoaded = true
        } else {
            macroType = 0
            selectedArea = null
            addDefaultSteps()
        }
    }

    onEditingMacroChanged: {
        console.log("BuffEditForm onEditingMacroChanged")
        if (editingMacro && !dataLoaded) {
            loadFromMacro(editingMacro)
            dataLoaded = true
        }
    }

    onBuffChanged: {
        console.log("BuffEditForm onBuffChanged: buff=", buff ? buff.name : "null")
        if (buff && !dataLoaded) {
            onBuffSelected(buff)
            dataLoaded = true
        }
    }
}
