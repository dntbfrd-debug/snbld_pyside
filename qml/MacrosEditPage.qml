import QtQuick 2.15
import QtQuick.Controls.Basic 2.15
import QtQuick.Layouts 1.15
import "components"

Item {
    id: macrosEditPage

    property bool editMode: false
    property var editingMacro: null



    // Верхняя панель с плитками
    ColumnLayout {
        anchors.top: parent.top
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.margins: 20
        spacing: 15
        height: tilesRow.implicitHeight

        Item {
            id: tilesRow
            Layout.fillWidth: true
            Layout.preferredHeight: 130

            RowLayout {
                anchors.fill: parent
                spacing: 8

                // Левая группа: Скиллы + Баффы (рекомендуемые)
                ColumnLayout {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    spacing: 2

                    // Скобка + надпись "Рекомендуемые"
                    Item {
                        Layout.fillWidth: true
                        Layout.preferredHeight: 28
                        clip: true

                        Canvas {
                            anchors.fill: parent
                            onPaint: {
                                var ctx = getContext("2d")
                                ctx.reset()
                                ctx.strokeStyle = "#4CAF50"
                                ctx.lineWidth = 1.5
                                ctx.globalAlpha = 0.6
                                ctx.beginPath()
                                var w = width, h = height, r = 8
                                ctx.moveTo(0, h)
                                ctx.lineTo(0, r)
                                ctx.quadraticCurveTo(0, 0, r, 0)
                                ctx.lineTo(w - r, 0)
                                ctx.quadraticCurveTo(w, 0, w, r)
                                ctx.lineTo(w, h)
                                ctx.stroke()
                            }
                            onWidthChanged: requestPaint()
                        }

                        Text {
                            anchors.centerIn: parent
                            text: "Рекомендуемые"
                            color: "#4CAF50"
                            font.pointSize: 10
                            font.bold: true
                        }
                    }

                    Rectangle {
                        radius: 14
                        color: "transparent"
                        Layout.fillWidth: true
                        Layout.fillHeight: true

                        RowLayout {
                            anchors.fill: parent
                            anchors.margins: 4
                            spacing: 8

                            CustomTabButton {
                                id: skillTab
                                text: "Скиллы"
                                iconSource: "../icons/skill.png"
                                isActive: false
                                Layout.fillWidth: true
                                Layout.fillHeight: true
                                iconSize: 18
                                textSize: 10
                                onClicked: {
                                    tabIndicator.setActive(skillTab)
                                    editStackView.replace("SkillClassSelector.qml", {
                                        "editingMacro": editMode ? editingMacro : null
                                    })
                                }
                            }

                            CustomTabButton {
                                id: buffTab
                                text: "Баффы"
                                iconSource: "../icons/buff.png"
                                isActive: false
                                Layout.fillWidth: true
                                Layout.fillHeight: true
                                iconSize: 18
                                textSize: 10
                                onClicked: {
                                    tabIndicator.setActive(buffTab)
                                    editStackView.replace("BuffListPage.qml")
                                }
                            }
                        }
                    }
                }

                // Правая группа: Простые + По области
                ColumnLayout {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    spacing: 2

                    Item {
                        Layout.fillWidth: true
                        Layout.preferredHeight: 28
                    }

                    Rectangle {
                        radius: 14
                        color: "transparent"
                        Layout.fillWidth: true
                        Layout.fillHeight: true

                        RowLayout {
                            anchors.fill: parent
                            anchors.margins: 4
                            spacing: 8

                            CustomTabButton {
                                id: simpleTab
                                text: "Простые"
                                iconSource: "../icons/macros1.png"
                                isActive: false
                                Layout.fillWidth: true
                                Layout.fillHeight: true
                                iconSize: 18
                                textSize: 10
                                onClicked: {
                                    tabIndicator.setActive(this)
                                    editStackView.replace("SimpleEditForm.qml", {
                                        "editingMacro": editMode ? editingMacro : null
                                    })
                                }
                            }

                            CustomTabButton {
                                id: zoneTab
                                text: "По области"
                                iconSource: "../icons/zone.png"
                                isActive: false
                                Layout.fillWidth: true
                                Layout.fillHeight: true
                                iconSize: 18
                                textSize: 10
                                onClicked: {
                                    tabIndicator.setActive(zoneTab)
                                    editStackView.replace("ZoneEditForm.qml", {
                                        "editingMacro": editMode ? editingMacro : null
                                    })
                                }
                            }
                        }
                    }
                }
            }
        }
    }

    // StackView для страниц
    StackView {
        id: editStackView
        anchors.top: parent.top
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.bottom: parent.bottom
        anchors.topMargin: 170
        anchors.leftMargin: 20
        anchors.rightMargin: 20
        anchors.bottomMargin: 20
        clip: true
        initialItem: Rectangle {
            color: "transparent"
        }
        pushEnter: Transition {
            PropertyAnimation {
                property: "x"
                from: editStackView.width
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
                to: -editStackView.width * 0.5
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
                from: -editStackView.width * 0.5
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
                to: editStackView.width
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
        replaceEnter: Transition {
            PropertyAnimation { property: "x"; from: editStackView.width; to: 0; duration: 300; easing.type: Easing.OutCubic }
            PropertyAnimation { property: "opacity"; from: 0; to: 1; duration: 300; easing.type: Easing.OutCubic }
        }
        replaceExit: Transition {
            PropertyAnimation { property: "x"; from: 0; to: -editStackView.width; duration: 300; easing.type: Easing.InCubic }
            PropertyAnimation { property: "opacity"; from: 1; to: 0; duration: 300; easing.type: Easing.InCubic }
        }
    }

    Text {
        id: invitationText
        text: "Выберите тип макроса для создания"
        color: "#a2a2a2"
        font.pointSize: 16
        horizontalAlignment: Text.AlignHCenter
        anchors.centerIn: parent
        visible: editStackView.depth === 0
        z: 1
    }

    ButtonGroupWithIndicator {
        id: tabIndicator
        buttons: [skillTab, buffTab, simpleTab, zoneTab]
        setActiveCallback: function(activeButton) {
            skillTab.isActive = false
            buffTab.isActive = false
            simpleTab.isActive = false
            zoneTab.isActive = false
            activeButton.isActive = true
        }
        Component.onCompleted: {
            init()
        }
    }

    property bool _initialized: false

    function _initPage() {
        if (_initialized) return
        _initialized = true

        // Берём данные из backend.macro_for_edit (гарантированно синхронны),
        // если editingMacro не установлен через свойства StackView
        var macroData = editingMacro
        if (!macroData && backend && backend.macro_for_edit && backend.macro_for_edit.name) {
            macroData = backend.macro_for_edit
        }

        if (backend) {
            backend.qmlLog("MacrosEditPage _initPage: name=" + (macroData ? macroData.name : "null") + ", type=" + (macroData ? macroData.type : "null"))
        }

        if (macroData && macroData.type) {
            editMode = true
            editingMacro = macroData
            backend.clear_macro_for_edit()
            var page = null
            var activeTab = null
            if (macroData.type === "skill") { page = "SkillEditForm.qml"; activeTab = skillTab }
            else if (macroData.type === "buff") { page = "BuffListPage.qml"; activeTab = buffTab }
            else if (macroData.type === "simple") { page = "SimpleEditForm.qml"; activeTab = simpleTab }
            else if (macroData.type === "zone") { page = "ZoneEditForm.qml"; activeTab = zoneTab }
            if (page) {
                if (activeTab) tabIndicator.setActive(activeTab)
                editStackView.clear()
                editStackView.push(page, { "editingMacro": macroData })
                if (backend) backend.qmlLog("MacrosEditPage: opened edit form for " + macroData.type + " — " + page)
            }
        } else {
            editMode = false
            editingMacro = null
            tabIndicator.setActive(skillTab)
            editStackView.clear()
            editStackView.push("SkillClassSelector.qml", { "editingMacro": null })
            if (backend) backend.qmlLog("MacrosEditPage: opened create mode (SkillClassSelector)")
        }
    }

    Component.onCompleted: {
        // Qt.callLater — deferred на следующий цикл событий, чтобы
        // внешний StackView полностью завершил replace() до работы с вложенным editStackView
        Qt.callLater(_initPage)
    }

    onVisibleChanged: {
        if (visible && !_initialized) {
            // Защита: если Component.onCompleted ещё не сработал (редкий случай),
            // запускаем инициализацию
            Qt.callLater(_initPage)
        }
    }
}
