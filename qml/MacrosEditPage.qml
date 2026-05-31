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
            Layout.preferredHeight: 100

            RowLayout {
                anchors.fill: parent
                spacing: 8

                // Левая группа: Скиллы + Баффы (приоритет)
                Rectangle {
                    radius: 14
                    color: "transparent"
                    border.color: Qt.rgba(0.2, 0.8, 0.2, 0.6)
                    border.width: 1
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

                // Правая группа: Простые + По области
                Rectangle {
                    radius: 14
                    color: "transparent"
                    border.color: Qt.rgba(0.9, 0.2, 0.2, 0.6)
                    border.width: 1
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
            setActive(skillTab)
            editStackView.push("SkillClassSelector.qml", {
                "editingMacro": null
            })
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
