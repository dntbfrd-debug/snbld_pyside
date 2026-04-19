import QtQuick 2.15
import QtQuick.Controls.Basic 2.15
import QtQuick.Layouts 1.15

Item {
    id: root

    property string accentColor: backend && backend.settings ? backend.settings.accent_color : "#7793a1"

    property alias macroName: nameField.text
    property alias macroHotkey: hotkeyField.text
    property string skillId: ""
    property string skillName: ""
    property double skillCooldown: 0
    property double skillRange: 0
    property double skillCastTime: 0
    property double castbarSwapDelay: 0
    property int macroType: 0  // 0 = по горячей клавише, 1 = по области
    property var selectedArea: null
    property var stepsModel: []
    property var editingMacro: null
    property var skill: null

    // Доступ к StackView из родителя
    property alias editStackView: root.parent

    Component.onCompleted: {
        console.log("SkillEditForm Component.onCompleted, editingMacro=", editingMacro ? editingMacro.name : "null", "skill=", skill ? skill.name : "null")
        if (editingMacro) {
            loadFromMacro(editingMacro)
        } else if (skill) {
            console.log("SkillEditForm Component.onCompleted: вызываю onSkillSelected для", skill.name)
            onSkillSelected(skill)
        }
    }

    onEditingMacroChanged: {
        console.log("SkillEditForm onEditingMacroChanged")
        if (editingMacro && editingMacro.name && !dataLoaded) {
            loadFromMacro(editingMacro)
            dataLoaded = true
        }
    }

    onSkillChanged: {
        console.log("SkillEditForm onSkillChanged: skill=", skill ? skill.name : "null", "dataLoaded=", dataLoaded)
        if (skill && !dataLoaded) {
            console.log("SkillEditForm: вызываю onSkillSelected для", skill.name)
            onSkillSelected(skill)
        }
    }

    property bool dataLoaded: false

    // Извлекает последнюю клавишу из комбинации (ctrl+shift+e → e)
    function getLastKey(hotkey) {
        if (!hotkey || hotkey === "") return ""
        var parts = hotkey.split("+")
        return parts[parts.length - 1]
    }

    function loadFromMacro(macro) {
        console.log("SkillEditForm.loadFromMacro:", macro.name)
        if (!macro) {
            console.log("SkillEditForm.loadFromMacro: macro is null/undefined")
            return
        }
        nameField.text = macro["name"] || ""
        hotkeyField.text = macro["hotkey"] || ""
        macroHotkey = macro["hotkey"] || ""
        skillId = macro["skill_id"] ? macro["skill_id"].toString() : ""
        skillCooldown = macro["cooldown"] || 0
        skillRange = macro["skill_range"] || 0
        skillCastTime = macro["cast_time"] || 0
        castbarSwapDelay = macro["castbar_swap_delay"] || 0

        // Определяем тип по наличию zone_rect
        if (macro["zone_rect"] && macro["zone_rect"].length > 0) {
            macroType = 1
            selectedArea = macro["zone_rect"].slice()
            zoneAreaField.text = selectedArea.join(",")
        } else {
            macroType = 0
            selectedArea = null
            zoneAreaField.text = "Не выбрана"
        }

        // Загружаем данные скилла
        if (skillId) {
            var skillData = findSkillById(skillId)
            if (skillData) {
                skillName = skillData.name
                skillCooldown = skillData.cooldown
                skillRange = skillData.range
                skillCastTime = skillData.cast_time
                if (nameField.text === "") {
                    nameField.text = skillName
                }
            }
        }

        // Загружаем шаги
        stepsModel = []
        var steps = macro["steps"]
        if (steps && steps.length > 0) {
            for (var i = 0; i < steps.length; ++i) {
                var step = steps[i]
                stepsModel.push({ action: step[0], value: step[1], delay: step[2] })
            }
        } else {
            addDefaultSteps()
        }
        stepsView.model = stepsModel

        // Обновляем поля
        skillInfoField.text = skillId ? (skillName + " (ID: " + skillId + ")") : "Не выбран"
        cooldownField.text = skillCooldown.toString()
        rangeField.text = skillRange.toString()
        castTimeField.text = skillCastTime.toString()
        castbarDelayField.text = castbarSwapDelay.toString()

        editingMacro = macro
        dataLoaded = true
    }

    function onSkillSelected(skillData) {
        console.log("SkillEditForm.onSkillSelected:", skillData.name)
        console.log("  - id:", skillData.id)
        console.log("  - cooldown:", skillData.cooldown)
        console.log("  - range:", skillData.range)
        console.log("  - cast_time:", skillData.cast_time)

        skillId = skillData.id.toString()
        skillName = skillData.name
        skillCooldown = skillData.cooldown
        skillRange = skillData.range
        skillCastTime = skillData.cast_time

        // Автоподстановка названия
        if (nameField.text === "") {
            nameField.text = skillName
        }

        // Обновляем поля
        skillInfoField.text = skillName + " (ID: " + skillId + ")"
        cooldownField.text = skillCooldown.toString()
        rangeField.text = skillRange.toString()
        castTimeField.text = skillCastTime.toString()
        castbarDelayField.text = castbarSwapDelay.toString()

        console.log("  - создаю стандартные шаги...")
        // Создаём стандартные шаги
        addDefaultSteps()
        dataLoaded = true
        console.log("  - шаги созданы, dataLoaded=", dataLoaded)
    }

    function findSkillById(id) {
        var skills = backend.skill_list
        for (var i = 0; i < skills.length; ++i) {
            if (skills[i].id.toString() === id.toString()) {
                return skills[i]
            }
        }
        return null
    }

    function setSelectedArea(x1, y1, x2, y2) {
        selectedArea = [x1, y1, x2, y2]
        zoneAreaField.text = selectedArea.join(",")
    }

    function addDefaultSteps() {
        stepsModel = []
        var swapChant = backend.settings.swap_key_chant || "e"
        var swapPa = backend.settings.swap_key_pa || "e"
        var delay = backend.settings.global_step_delay || 20
        var firstStepDelay = backend.settings.first_step_delay || 100

        stepsModel.push({ action: "key", value: swapChant, delay: firstStepDelay })

        if (macroType === 0) {
            stepsModel.push({ action: "key", value: macroHotkey || "1", delay: delay })
        } else {
            stepsModel.push({ action: "left", value: "", delay: 10 })
        }

        stepsModel.push({ action: "key", value: swapPa, delay: delay })
        stepsView.model = stepsModel
    }

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 10
        spacing: 8

        RowLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            spacing: 10

            ColumnLayout {
                Layout.fillWidth: true
                Layout.fillHeight: true
                spacing: 8

        // Верхняя строка: Название + Горячая клавиша + Тип
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
                Layout.preferredWidth: 120
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

                    Keys.onPressed: {
                        event.accepted = true

                        if (event.key === Qt.Key_Backspace) {
                            hotkeyField.text = ""
                            macroHotkey = ""
                            return
                        }

                        if (event.key === Qt.Key_Escape) {
                            return
                        }

                        var modifiers = []
                        var keyName = ""

                        if (event.modifiers & Qt.ControlModifier) modifiers.push("ctrl")
                        if (event.modifiers & Qt.AltModifier) modifiers.push("alt")
                        if (event.modifiers & Qt.ShiftModifier) modifiers.push("shift")

                        var key = event.key

                        if (key >= Qt.Key_F1 && key <= Qt.Key_F12) {
                            keyName = "f" + (key - Qt.Key_F1 + 1)
                        }
                        else if (key >= Qt.Key_A && key <= Qt.Key_Z) {
                            keyName = String.fromCharCode(key).toLowerCase()
                        }
                        else if (key >= Qt.Key_0 && key <= Qt.Key_9) {
                            keyName = String.fromCharCode(key)
                        }
                        else if (key === Qt.Key_Minus || key === Qt.Key_Hyphen) keyName = event.modifiers & Qt.ShiftModifier ? "_" : "-"
                        else if (key === Qt.Key_Equal || key === Qt.Key_Plus) keyName = event.modifiers & Qt.ShiftModifier ? "+" : "="
                        else if (key === Qt.Key_Space) keyName = "space"
                        else if (key === Qt.Key_Tab) keyName = "tab"
                        else if (key === Qt.Key_Return || key === Qt.Key_Enter) keyName = "enter"
                        else if (key === Qt.Key_Delete) keyName = "delete"
                        else if (key === Qt.Key_Up) keyName = "up"
                        else if (key === Qt.Key_Down) keyName = "down"
                        else if (key === Qt.Key_Left) keyName = "left"
                        else if (key === Qt.Key_Right) keyName = "right"
                        else {
                            keyName = "key_" + key
                        }

                        if (modifiers.length > 0) {
                            hotkeyField.text = modifiers.join("+") + "+" + keyName
                        } else {
                            hotkeyField.text = keyName
                        }
                        macroHotkey = hotkeyField.text

                        // Обновляем шаг 2 если тип "По горячей клавише"
                        // Используем getLastKey() чтобы извлечь клавишу из комбинации
                        if (macroType === 0 && stepsModel.length >= 2) {
                            stepsModel[1] = { action: "key", value: getLastKey(macroHotkey), delay: stepsModel[1].delay }
                            stepsView.model = stepsModel
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
                        if (macroType === 0) {
                            // По горячей клавише
                            if (stepsModel.length >= 2) {
                                stepsModel[1] = { action: "key", value: getLastKey(macroHotkey) || "1", delay: stepsModel[1].delay }
                                stepsView.model = stepsModel
                            }
                            selectedArea = null
                            zoneAreaField.text = "Не выбрана"
                        } else {
                            // По области
                            if (stepsModel.length >= 2) {
                                stepsModel[1] = { action: "left", value: "", delay: stepsModel[1].delay }
                                stepsView.model = stepsModel
                            }
                            zoneAreaField.forceActiveFocus()
                        }
                    }
                }
            }
        }

        // Вторая строка: Скилл + Область
        RowLayout {
            Layout.fillWidth: true
            spacing: 8

            ColumnLayout {
                Layout.fillWidth: true
                spacing: 2
                Label {
                    text: "✦ Скилл:"
                    color: "#c2c2c2"
                    font.pointSize: 9
                }
                TextField {
                    id: skillInfoField
                    Layout.fillWidth: true
                    Layout.preferredHeight: 24
                    readOnly: true
                    font.pointSize: 10
                    background: Rectangle { radius: 4; color: "#40ffffff" }
                }
            }

            ColumnLayout {
                Layout.fillWidth: macroType === 1
                Layout.preferredWidth: macroType === 0 ? 0 : -1
                visible: macroType === 1
                spacing: 2
                Label {
                    text: "📍 Область (x1,y1,x2,y2):"
                    color: "#c2c2c2"
                    font.pointSize: 9
                }
                RowLayout {
                    Layout.fillWidth: true
                    spacing: 4
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
                        onClicked: {
                            backend.selectAreaForMacro()
                        }
                    }
                }
            }
        }

        // Третья строка: Параметры скилла
        RowLayout {
            Layout.fillWidth: true
            spacing: 8

            ColumnLayout {
                Layout.fillWidth: true
                spacing: 2
                Label {
                    text: "⏱ КД (сек):"
                    color: "#c2c2c2"
                    font.pointSize: 9
                }
                TextField {
                    id: cooldownField
                    Layout.fillWidth: true
                    Layout.preferredHeight: 24
                    text: skillCooldown.toString()
                    font.pointSize: 10
                    validator: DoubleValidator { bottom: 0; decimals: 2 }
                    background: Rectangle { radius: 4; color: "#40ffffff" }
                    onTextChanged: skillCooldown = parseFloat(text) || 0
                }
            }

            ColumnLayout {
                Layout.fillWidth: true
                spacing: 2
                Label {
                    text: "📏 Дальность (м):"
                    color: "#c2c2c2"
                    font.pointSize: 9
                }
                TextField {
                    id: rangeField
                    Layout.fillWidth: true
                    Layout.preferredHeight: 24
                    text: skillRange.toString()
                    font.pointSize: 10
                    validator: DoubleValidator { bottom: 0; decimals: 2 }
                    background: Rectangle { radius: 4; color: "#40ffffff" }
                    onTextChanged: skillRange = parseFloat(text) || 0
                }
            }

            ColumnLayout {
                Layout.fillWidth: true
                spacing: 2
                Label {
                    text: "⏳ Каст (сек):"
                    color: "#c2c2c2"
                    font.pointSize: 9
                }
                TextField {
                    id: castTimeField
                    Layout.fillWidth: true
                    Layout.preferredHeight: 24
                    text: skillCastTime.toString()
                    font.pointSize: 10
                    validator: DoubleValidator { bottom: 0; decimals: 2 }
                    background: Rectangle { radius: 4; color: "#40ffffff" }
                    onTextChanged: skillCastTime = parseFloat(text) || 0
                }
            }

            ColumnLayout {
                Layout.fillWidth: true
                spacing: 2
                Label {
                    text: "Задержка (мс):"
                    color: "#c2c2c2"
                    font.pointSize: 9
                }
                TextField {
                    id: castbarDelayField
                    Layout.fillWidth: true
                    Layout.preferredHeight: 24
                    text: castbarSwapDelay.toString()
                    font.pointSize: 10
                    validator: IntValidator { bottom: 0; top: 1000 }
                    background: Rectangle { radius: 4; color: "#40ffffff" }
                }
            }
        }

        // Список шагов
        ColumnLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            spacing: 4

            Label {
                text: "📋 Шаги макроса:"
                color: "#c2c2c2"
                font.pointSize: 9
            }

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
                        Text {
                            text: (index + 1) + "."
                            color: "#7793a1"
                            width: 20
                        }
                        Text {
                            text: modelData.action === "key" ? "Клавиша" :
                                  modelData.action === "left" ? "ЛКМ" :
                                  modelData.action === "right" ? "ПКМ" :
                                  "Пауза"
                            color: "#c2c2c2"
                            width: 80
                        }
                        Text {
                            text: modelData.value || ""
                            color: "#c2c2c2"
                            width: 60
                        }
                        Text {
                            text: (modelData.delay !== undefined ? modelData.delay : 0) + " мс"
                            color: "#a0a0a0"
                        }
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
                            text: "Выберите скилл из списка класса.\n\nУкажите КД, дальность и время каста — значения из базы можно поправить вручную.\n\n«По горячей клавише» — запуск по клавише; «По области» — клик в выделенной зоне экрана.\n\nТри шага ресвапа: смена пения → скилл или ЛКМ → смена ПА. Поле «Задержка (мс)» — пауза после кастбара перед сменой сета."
                            color: "#d8d8d8"
                            font.pointSize: 9
                            wrapMode: Text.WordWrap
                            Layout.fillWidth: true
                        }
                    }
                }
            }
        }

        // Кнопка сохранения
        RowLayout {
            Layout.fillWidth: true
            Layout.preferredHeight: 40
            spacing: 8
            Item { Layout.fillWidth: true }
            BaseButton {
                text: "💾 Сохранить"
                implicitWidth: 140
                implicitHeight: 35
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

                    if (editingMacro) {
                        backend.update_skill_macro(
                            editingMacro["name"], nameField.text, macroHotkey,
                            skillId, stepsList, macroHotkey,
                            skillCooldown,
                            skillRange,
                            skillCastTime,
                            parseFloat(castbarDelayField.text) || 0,
                            zoneRect
                        )
                    } else {
                        backend.create_skill_macro_with_params(
                            nameField.text, macroHotkey, skillId, stepsList, macroHotkey,
                            skillCooldown,
                            skillRange,
                            skillCastTime,
                            parseFloat(castbarDelayField.text) || 0,
                            zoneRect
                        )
                    }
                    backend.clear_macro_for_edit()
                    backend.pageChangeRequested("MacrosListPage.qml")
                    backend.notification("Скилл-макрос '" + nameField.text + "' сохранён", "success")
                }
            }
            Item { Layout.fillWidth: true }
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

    // Обработка выбора области
    Connections {
        target: backend
        function onZoneAreaSelectedSignal(zoneRect) {
            if (zoneRect && zoneRect.length === 4) {
                setSelectedArea(zoneRect[0], zoneRect[1], zoneRect[2], zoneRect[3])
            }
        }
    }
}
