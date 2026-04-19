import QtQuick 2.15
import QtQuick.Controls.Basic 2.15
import QtQuick.Layouts 1.15

Item {
    id: macrosEditPage

    property bool editMode: false
    property var editingMacro: null

    Rectangle {
        anchors.fill: parent
        color: "#99252525"
        radius: 12
    }

    // Верхняя панель с плитками
    ColumnLayout {
        anchors.top: parent.top
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.margins: 20
        spacing: 15
        height: tilesRow.implicitHeight

        RowLayout {
            id: tilesRow
            spacing: 8
            Layout.fillWidth: true
            Layout.preferredHeight: 100

            // Плитка: Простые
            CustomTabButton {
                id: simpleTab
                text: "Простые"
                iconSource: "../icons/macros1.png"
                isActive: false
                Layout.fillWidth: true
                Layout.preferredWidth: tilesRow.width > 0 ? (tilesRow.width - 24) / 4 : 100
                Layout.preferredHeight: 100
                iconSize: 18
                textSize: 10
                onClicked: {
                    tabIndicator.setActive(this)
                    editStackView.push("SimpleEditForm.qml", {
                        "editingMacro": editMode ? editingMacro : null
                    })
                }
            }

            // Плитка: По области
            CustomTabButton {
                id: zoneTab
                text: "По области"
                iconSource: "../icons/zone.png"
                isActive: false
                Layout.fillWidth: true
                Layout.preferredWidth: tilesRow.width > 0 ? (tilesRow.width - 24) / 4 : 100
                Layout.preferredHeight: 100
                iconSize: 18
                textSize: 10
                onClicked: {
                    tabIndicator.setActive(zoneTab)
                    editStackView.push("ZoneEditForm.qml", {
                        "editingMacro": editMode ? editingMacro : null
                    })
                }
            }

            // Плитка: Скиллы
            CustomTabButton {
                id: skillTab
                text: "Скиллы"
                iconSource: "../icons/skill.png"
                isActive: false
                Layout.fillWidth: true
                Layout.preferredWidth: tilesRow.width > 0 ? (tilesRow.width - 24) / 4 : 100
                Layout.preferredHeight: 100
                iconSize: 18
                textSize: 10
                onClicked: {
                    tabIndicator.setActive(skillTab)
                    editStackView.push("SkillClassSelector.qml", {
                        "editingMacro": editMode ? editingMacro : null
                    })
                }
            }

            // Плитка: Баффы
            CustomTabButton {
                id: buffTab
                text: "Баффы"
                iconSource: "../icons/buff.png"
                isActive: false
                Layout.fillWidth: true
                Layout.preferredWidth: tilesRow.width > 0 ? (tilesRow.width - 24) / 4 : 100
                Layout.preferredHeight: 100
                iconSize: 18
                textSize: 10
                onClicked: {
                    tabIndicator.setActive(buffTab)
                    editStackView.push("BuffListPage.qml")
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
        anchors.topMargin: 140
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
    }

    Text {
        id: invitationText
        text: "Выберите тип макроса для создания"
        color: "#c2c2c2"
        font.pointSize: 16
        horizontalAlignment: Text.AlignHCenter
        anchors.centerIn: parent
        visible: editStackView.depth === 0
        z: 1
    }

    ButtonGroupWithIndicator {
        id: tabIndicator
        buttons: [simpleTab, zoneTab, skillTab, buffTab]
        leftInset: 10
        topInset: 10
        rightInset: 10
        bottomInset: 10
        setActiveCallback: function(activeButton) {
            simpleTab.isActive = false
            zoneTab.isActive = false
            skillTab.isActive = false
            buffTab.isActive = false
            activeButton.isActive = true
        }
        Component.onCompleted: {
            init()
            setActive(simpleTab)
        }
    }

    onVisibleChanged: {
        if (visible) {
            console.log("MacrosEditPage visible")
            // Для создания новых макросов - просто показываем плитки
            editMode = false
            editingMacro = null
        }
    }

    Component.onCompleted: {
        console.log("MacrosEditPage onCompleted")
    }
}
