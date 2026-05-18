import QtQuick 2.15
import QtQuick.Controls.Basic 2.15
import QtQuick.Layouts 1.15

Item {
    id: root
    visible: false
    clip: true

    property string currentType: "simple"
    property var editingMacro: null
    property bool editMode: false

    // Для скиллов
    property string selectedSkillClass: ""
    property var selectedSkill: null

    signal saveRequested()
    signal cancelRequested()

    function open(type, macro) {
        console.log("EditPanel.open:", type, macro ? macro.name : "null")
        currentType = type
        editingMacro = macro
        editMode = (macro !== null)
        visible = true

        if (type === "skill") {
            if (macro) {
                // Редактирование: сразу переходим к форме редактирования
                selectedSkill = {
                    id: macro.skill_id,
                    name: macro.name,
                    cooldown: macro.cooldown,
                    range: macro.skill_range,
                    cast_time: macro.cast_time,
                    class: ""
                }
                selectedSkillClass = macro.skill_class || ""
                // Очищаем стек и показываем страницу редактирования
                if (skillMainLoader.item && skillMainLoader.item.skillStackView) {
                    var stack = skillMainLoader.item.skillStackView
                    stack.clear()
                    stack.push(skillEditPageComponent, { skill: selectedSkill, macro: macro })
                }
            } else {
                // Новый макрос: начинаем с выбора класса
                selectedSkillClass = ""
                selectedSkill = null
                if (skillMainLoader.item && skillMainLoader.item.skillStackView) {
                    var stack = skillMainLoader.item.skillStackView
                    stack.clear()
                    stack.push(skillClassPageComponent)
                }
            }
        }

        loadDataTimer.start()
    }

    function close() {
        visible = false
    }

    Timer {
        id: loadDataTimer
        interval: 100
        repeat: false
        onTriggered: {
            loadData()
        }
    }

    function loadData() {
        var loader = null
        if (currentType === "simple") loader = simpleLoader
        else if (currentType === "zone") loader = zoneLoader
        else if (currentType === "skill") {
            // Для скиллов загрузка данных происходит через страницы
            return
        }
        else if (currentType === "buff") loader = buffLoader

        if (loader && loader.active && loader.item && loader.item.loadFromMacro && editMode && editingMacro) {
            console.log("loadData: calling loadFromMacro for", editingMacro.name)
            loader.item.loadFromMacro(editingMacro)
        } else {
            console.log("loadData: conditions not met, loader=", loader,
                        "active=", loader ? loader.active : false,
                        "item=", loader ? loader.item : null,
                        "hasLoadFromMacro=", loader && loader.item ? !!loader.item.loadFromMacro : false,
                        "editMode=", editMode, "editingMacro=", editingMacro ? editingMacro.name : "null")
            if (editMode && editingMacro && (currentType !== "skill" || (currentType === "skill"))) {
                retryTimer.start()
            }
        }
    }

    Timer {
        id: retryTimer
        interval: 300
        repeat: false
        onTriggered: {
            loadData()
        }
    }

    Loader {
        id: simpleLoader
        active: currentType === "simple"
        sourceComponent: simpleEditForm
        onLoaded: {
            console.log("simpleLoader loaded")
            if (item) {
                item.saveRequested.connect(root.saveRequested)
                item.cancelRequested.connect(root.cancelRequested)
                if (root.editMode && root.editingMacro && root.editingMacro.type === "simple") {
                    item.loadFromMacro(root.editingMacro)
                }
            }
        }
    }

    Loader {
        id: zoneLoader
        active: currentType === "zone"
        sourceComponent: zoneEditFormComponent
        onLoaded: {
            console.log("zoneLoader loaded")
            if (item) {
                item.saveRequested.connect(root.saveRequested)
                item.cancelRequested.connect(root.cancelRequested)
                if (root.editMode && root.editingMacro && root.editingMacro.type === "zone") {
                    item.loadFromMacro(root.editingMacro)
                }
            }
        }
    }

    Loader {
        id: skillMainLoader
        active: currentType === "skill"
        sourceComponent: skillMainComponent
    }

    Loader {
        id: buffLoader
        active: currentType === "buff"
        sourceComponent: buffEditFormComponent
        onLoaded: {
            console.log("buffLoader loaded")
            if (item) {
                item.saveRequested.connect(root.saveRequested)
                item.cancelRequested.connect(root.cancelRequested)
                if (root.editMode && root.editingMacro && root.editingMacro.type === "buff") {
                    item.loadFromMacro(root.editingMacro)
                }
            }
        }
    }

    Component {
        id: simpleEditForm
        SimpleEditForm {
            onSaveRequested: root.saveRequested()
            onCancelRequested: root.cancelRequested()
        }
    }

    Component {
        id: zoneEditFormComponent
        ZoneEditForm {
            onSaveRequested: root.saveRequested()
            onCancelRequested: root.cancelRequested()
        }
    }

    Component {
        id: skillMainComponent
        Item {
            id: skillMainItem
            anchors.fill: parent

            property alias skillStackView: skillStackView

            StackView {
                id: skillStackView
                anchors.fill: parent
                initialItem: skillClassPageComponent
                pushEnter: Transition {
                    PropertyAnimation {
                        property: "x"
                        from: skillStackView.width
                        to: 0
                        duration: 300
                        easing.type: Easing.OutCubic
                    }
                    PropertyAnimation {
                        property: "opacity"
                        from: 0
                        to: 1
                        duration: 300
                        easing.type: Easing.OutCubic
                    }
                }
                pushExit: Transition {
                    PropertyAnimation {
                        property: "x"
                        from: 0
                        to: -skillStackView.width * 0.5
                        duration: 300
                        easing.type: Easing.InCubic
                    }
                    PropertyAnimation {
                        property: "opacity"
                        from: 1
                        to: 0
                        duration: 300
                        easing.type: Easing.InCubic
                    }
                }
                popEnter: Transition {
                    PropertyAnimation {
                        property: "x"
                        from: -skillStackView.width * 0.5
                        to: 0
                        duration: 300
                        easing.type: Easing.OutCubic
                    }
                    PropertyAnimation {
                        property: "opacity"
                        from: 0
                        to: 1
                        duration: 300
                        easing.type: Easing.OutCubic
                    }
                }
                popExit: Transition {
                    PropertyAnimation {
                        property: "x"
                        from: 0
                        to: skillStackView.width
                        duration: 300
                        easing.type: Easing.InCubic
                    }
                    PropertyAnimation {
                        property: "opacity"
                        from: 1
                        to: 0
                        duration: 300
                        easing.type: Easing.InCubic
                    }
                }
            }
        }
    }

    Component {
        id: skillClassPageComponent
        SkillClassSelector {
            onClassSelected: function(className) {
                root.selectedSkillClass = className
                if (skillMainLoader.item && skillMainLoader.item.skillStackView) {
                    skillMainLoader.item.skillStackView.push(skillSelectionPageComponent, { className: className })
                }
            }
        }
    }

    Component {
        id: skillSelectionPageComponent
        SkillSelectionDialog {
            property string className: ""
            function loadSkills() {
                if (className) loadSkillsByClass(className)
            }
            Component.onCompleted: loadSkills()
            onSkillSelected: function(skill) {
                root.selectedSkill = skill
                if (skillMainLoader.item && skillMainLoader.item.skillStackView) {
                    skillMainLoader.item.skillStackView.push(skillEditPageComponent, { skill: skill, macro: null })
                }
            }
        }
    }

    Component {
        id: skillEditPageComponent
        SkillEditForm {
            property var skill: null
            property var macro: null
            onSaveRequested: {
                root.saveRequested()
                if (skillMainLoader.item && skillMainLoader.item.skillStackView) {
                    skillMainLoader.item.skillStackView.pop()
                }
            }
            onCancelRequested: {
                root.cancelRequested()
                if (skillMainLoader.item && skillMainLoader.item.skillStackView) {
                    skillMainLoader.item.skillStackView.pop()
                }
            }
            Component.onCompleted: {
                if (macro) {
                    // Режим редактирования
                    loadFromMacro(macro)
                } else if (skill) {
                    // Режим создания
                    onSkillSelected(skill)
                }
            }
        }
    }

    Component {
        id: buffEditFormComponent
        BuffEditForm {
            id: buffEditForm
            anchors.fill: parent
            
            onSaveRequested: {
                root.saveRequested()
            }
            onCancelRequested: {
                backend.clear_macro_for_edit()
                backend.pageChangeRequested("MacrosListPage.qml")
            }
        }
    }
}
