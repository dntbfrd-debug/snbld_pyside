import QtQuick 2.15
import QtQuick.Controls.Basic 2.15
import QtQuick.Layouts 1.15

Item {
    id: root
    visible: true
    clip: true

    signal classSelected(string className)

    // Доступ к StackView из родителя
    property alias editStackView: root.parent

    // Свойства для редактирования
    property var editingMacro: null
    property bool editMode: false
    
    // Функция для открытия списка скиллов и последующего открытия формы
    function openSkillSelection(className) {
        if (editStackView) {
            editStackView.push("SkillSelectionDialog.qml", {
                "className": className
            })
        }
    }
    
    // Функция для открытия формы редактирования скилла
    function openSkillForm(skill) {
        if (editStackView) {
            editStackView.push("SkillEditForm.qml", {
                "skill": skill,
                "editingMacro": editingMacro
            })
        }
    }

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 20
        spacing: 20

        RowLayout {
            Layout.fillWidth: true
            BaseButton {
                text: "← Назад"
                implicitWidth: 100
                implicitHeight: 40
                iconSize: 14
                textSize: 11
                onClicked: {
                    if (editStackView) {
                        editStackView.pop()
                    }
                }
            }
            Item { Layout.fillWidth: true }
        }

        Text {
            text: "Выберите класс вашего персонажа:"
            color: "#c2c2c2"
            font.pointSize: 16
            font.bold: true
            horizontalAlignment: Text.AlignHCenter
            Layout.fillWidth: true
        }

        RowLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            spacing: 20

            // Маг
            Rectangle {
                id: mageClass
                Layout.fillWidth: true
                Layout.fillHeight: true
                color: "#99252525"
                radius: 10
                border.color: "#50ffffff"
                border.width: 2

                property color accentColor: backend && backend.settings && backend.settings.accent_color !== undefined && backend.settings.accent_color !== null ? backend.settings.accent_color : "#7793a1"

                // Эффект свечения при наведении
                Rectangle {
                    id: mageGlow1
                    anchors.centerIn: parent
                    width: parent.width + 40
                    height: parent.height + 40
                    radius: 10 + 20
                    color: Qt.rgba(mageClass.accentColor.r, mageClass.accentColor.g, mageClass.accentColor.b, mageMouseArea.containsMouse ? 0.005 : 0)
                    z: 0
                }
                Rectangle {
                    id: mageGlow2
                    anchors.centerIn: parent
                    width: parent.width + 35
                    height: parent.height + 35
                    radius: 10 + 17
                    color: Qt.rgba(mageClass.accentColor.r, mageClass.accentColor.g, mageClass.accentColor.b, mageMouseArea.containsMouse ? 0.01 : 0)
                    z: 0
                }
                Rectangle {
                    id: mageGlow3
                    anchors.centerIn: parent
                    width: parent.width + 30
                    height: parent.height + 30
                    radius: 10 + 15
                    color: Qt.rgba(mageClass.accentColor.r, mageClass.accentColor.g, mageClass.accentColor.b, mageMouseArea.containsMouse ? 0.015 : 0)
                    z: 0
                }
                Rectangle {
                    id: mageGlow4
                    anchors.centerIn: parent
                    width: parent.width + 25
                    height: parent.height + 25
                    radius: 10 + 12
                    color: Qt.rgba(mageClass.accentColor.r, mageClass.accentColor.g, mageClass.accentColor.b, mageMouseArea.containsMouse ? 0.02 : 0)
                    z: 0
                }
                Rectangle {
                    id: mageGlow5
                    anchors.centerIn: parent
                    width: parent.width + 20
                    height: parent.height + 20
                    radius: 10 + 10
                    color: Qt.rgba(mageClass.accentColor.r, mageClass.accentColor.g, mageClass.accentColor.b, mageMouseArea.containsMouse ? 0.03 : 0)
                    z: 0
                }
                Rectangle {
                    id: mageGlow6
                    anchors.centerIn: parent
                    width: parent.width + 15
                    height: parent.height + 15
                    radius: 10 + 7
                    color: Qt.rgba(mageClass.accentColor.r, mageClass.accentColor.g, mageClass.accentColor.b, mageMouseArea.containsMouse ? 0.04 : 0)
                    z: 0
                }
                Rectangle {
                    id: mageGlow7
                    anchors.centerIn: parent
                    width: parent.width + 10
                    height: parent.height + 10
                    radius: 10 + 5
                    color: Qt.rgba(mageClass.accentColor.r, mageClass.accentColor.g, mageClass.accentColor.b, mageMouseArea.containsMouse ? 0.05 : 0)
                    z: 0
                }
                Rectangle {
                    id: mageGlow8
                    anchors.centerIn: parent
                    width: parent.width + 6
                    height: parent.height + 6
                    radius: 10 + 3
                    color: Qt.rgba(mageClass.accentColor.r, mageClass.accentColor.g, mageClass.accentColor.b, mageMouseArea.containsMouse ? 0.06 : 0)
                    z: 0
                }

                MouseArea {
                    id: mageMouseArea
                    anchors.fill: parent
                    hoverEnabled: true
                    cursorShape: Qt.PointingHandCursor
                    onClicked: {
                        openSkillSelection("маг")
                    }
                }

                ColumnLayout {
                    anchors.centerIn: parent
                    spacing: 8

                    Image {
                        source: "../icons/mage_icon.png"
                        width: 48
                        height: 48
                        fillMode: Image.PreserveAspectFit
                        Layout.alignment: Qt.AlignHCenter
                    }

                    Text {
                        text: "Маг"
                        font.pointSize: 14
                        font.bold: true
                        color: "#c2c2c2"
                        horizontalAlignment: Text.AlignHCenter
                        Layout.alignment: Qt.AlignHCenter
                    }
                }
            }

            // Лучник
            Rectangle {
                id: archerClass
                Layout.fillWidth: true
                Layout.fillHeight: true
                color: "#99252525"
                radius: 10
                border.color: "#50ffffff"
                border.width: 2

                property color accentColor: backend && backend.settings && backend.settings.accent_color !== undefined && backend.settings.accent_color !== null ? backend.settings.accent_color : "#7793a1"

                // Эффект свечения при наведении
                Rectangle {
                    id: archerGlow1
                    anchors.centerIn: parent
                    width: parent.width + 40
                    height: parent.height + 40
                    radius: 10 + 20
                    color: Qt.rgba(archerClass.accentColor.r, archerClass.accentColor.g, archerClass.accentColor.b, archerMouseArea.containsMouse ? 0.005 : 0)
                    z: 0
                }
                Rectangle {
                    id: archerGlow2
                    anchors.centerIn: parent
                    width: parent.width + 35
                    height: parent.height + 35
                    radius: 10 + 17
                    color: Qt.rgba(archerClass.accentColor.r, archerClass.accentColor.g, archerClass.accentColor.b, archerMouseArea.containsMouse ? 0.01 : 0)
                    z: 0
                }
                Rectangle {
                    id: archerGlow3
                    anchors.centerIn: parent
                    width: parent.width + 30
                    height: parent.height + 30
                    radius: 10 + 15
                    color: Qt.rgba(archerClass.accentColor.r, archerClass.accentColor.g, archerClass.accentColor.b, archerMouseArea.containsMouse ? 0.015 : 0)
                    z: 0
                }
                Rectangle {
                    id: archerGlow4
                    anchors.centerIn: parent
                    width: parent.width + 25
                    height: parent.height + 25
                    radius: 10 + 12
                    color: Qt.rgba(archerClass.accentColor.r, archerClass.accentColor.g, archerClass.accentColor.b, archerMouseArea.containsMouse ? 0.02 : 0)
                    z: 0
                }
                Rectangle {
                    id: archerGlow5
                    anchors.centerIn: parent
                    width: parent.width + 20
                    height: parent.height + 20
                    radius: 10 + 10
                    color: Qt.rgba(archerClass.accentColor.r, archerClass.accentColor.g, archerClass.accentColor.b, archerMouseArea.containsMouse ? 0.03 : 0)
                    z: 0
                }
                Rectangle {
                    id: archerGlow6
                    anchors.centerIn: parent
                    width: parent.width + 15
                    height: parent.height + 15
                    radius: 10 + 7
                    color: Qt.rgba(archerClass.accentColor.r, archerClass.accentColor.g, archerClass.accentColor.b, archerMouseArea.containsMouse ? 0.04 : 0)
                    z: 0
                }
                Rectangle {
                    id: archerGlow7
                    anchors.centerIn: parent
                    width: parent.width + 10
                    height: parent.height + 10
                    radius: 10 + 5
                    color: Qt.rgba(archerClass.accentColor.r, archerClass.accentColor.g, archerClass.accentColor.b, archerMouseArea.containsMouse ? 0.05 : 0)
                    z: 0
                }
                Rectangle {
                    id: archerGlow8
                    anchors.centerIn: parent
                    width: parent.width + 6
                    height: parent.height + 6
                    radius: 10 + 3
                    color: Qt.rgba(archerClass.accentColor.r, archerClass.accentColor.g, archerClass.accentColor.b, archerMouseArea.containsMouse ? 0.06 : 0)
                    z: 0
                }

                MouseArea {
                    id: archerMouseArea
                    anchors.fill: parent
                    hoverEnabled: true
                    cursorShape: Qt.PointingHandCursor
                    onClicked: {
                        openSkillSelection("лучник")
                    }
                }

                ColumnLayout {
                    anchors.centerIn: parent
                    spacing: 8

                    Image {
                        source: "../icons/archer_icon.png"
                        width: 48
                        height: 48
                        fillMode: Image.PreserveAspectFit
                        Layout.alignment: Qt.AlignHCenter
                    }

                    Text {
                        text: "Лучник"
                        font.pointSize: 14
                        font.bold: true
                        color: "#c2c2c2"
                        horizontalAlignment: Text.AlignHCenter
                        Layout.alignment: Qt.AlignHCenter
                    }
                }
            }

            // Жрец
            Rectangle {
                id: priestClass
                Layout.fillWidth: true
                Layout.fillHeight: true
                color: "#99252525"
                radius: 10
                border.color: "#50ffffff"
                border.width: 2

                property color accentColor: backend && backend.settings && backend.settings.accent_color !== undefined && backend.settings.accent_color !== null ? backend.settings.accent_color : "#7793a1"

                // Эффект свечения при наведении
                Rectangle {
                    id: priestGlow1
                    anchors.centerIn: parent
                    width: parent.width + 40
                    height: parent.height + 40
                    radius: 10 + 20
                    color: Qt.rgba(priestClass.accentColor.r, priestClass.accentColor.g, priestClass.accentColor.b, priestMouseArea.containsMouse ? 0.005 : 0)
                    z: 0
                }
                Rectangle {
                    id: priestGlow2
                    anchors.centerIn: parent
                    width: parent.width + 35
                    height: parent.height + 35
                    radius: 10 + 17
                    color: Qt.rgba(priestClass.accentColor.r, priestClass.accentColor.g, priestClass.accentColor.b, priestMouseArea.containsMouse ? 0.01 : 0)
                    z: 0
                }
                Rectangle {
                    id: priestGlow3
                    anchors.centerIn: parent
                    width: parent.width + 30
                    height: parent.height + 30
                    radius: 10 + 15
                    color: Qt.rgba(priestClass.accentColor.r, priestClass.accentColor.g, priestClass.accentColor.b, priestMouseArea.containsMouse ? 0.015 : 0)
                    z: 0
                }
                Rectangle {
                    id: priestGlow4
                    anchors.centerIn: parent
                    width: parent.width + 25
                    height: parent.height + 25
                    radius: 10 + 12
                    color: Qt.rgba(priestClass.accentColor.r, priestClass.accentColor.g, priestClass.accentColor.b, priestMouseArea.containsMouse ? 0.02 : 0)
                    z: 0
                }
                Rectangle {
                    id: priestGlow5
                    anchors.centerIn: parent
                    width: parent.width + 20
                    height: parent.height + 20
                    radius: 10 + 10
                    color: Qt.rgba(priestClass.accentColor.r, priestClass.accentColor.g, priestClass.accentColor.b, priestMouseArea.containsMouse ? 0.03 : 0)
                    z: 0
                }
                Rectangle {
                    id: priestGlow6
                    anchors.centerIn: parent
                    width: parent.width + 15
                    height: parent.height + 15
                    radius: 10 + 7
                    color: Qt.rgba(priestClass.accentColor.r, priestClass.accentColor.g, priestClass.accentColor.b, priestMouseArea.containsMouse ? 0.04 : 0)
                    z: 0
                }
                Rectangle {
                    id: priestGlow7
                    anchors.centerIn: parent
                    width: parent.width + 10
                    height: parent.height + 10
                    radius: 10 + 5
                    color: Qt.rgba(priestClass.accentColor.r, priestClass.accentColor.g, priestClass.accentColor.b, priestMouseArea.containsMouse ? 0.05 : 0)
                    z: 0
                }
                Rectangle {
                    id: priestGlow8
                    anchors.centerIn: parent
                    width: parent.width + 6
                    height: parent.height + 6
                    radius: 10 + 3
                    color: Qt.rgba(priestClass.accentColor.r, priestClass.accentColor.g, priestClass.accentColor.b, priestMouseArea.containsMouse ? 0.06 : 0)
                    z: 0
                }

                MouseArea {
                    id: priestMouseArea
                    anchors.fill: parent
                    hoverEnabled: true
                    cursorShape: Qt.PointingHandCursor
                    onClicked: {
                        openSkillSelection("жрец")
                    }
                }

                ColumnLayout {
                    anchors.centerIn: parent
                    spacing: 8

                    Image {
                        source: "../icons/priest_icon.png"
                        width: 48
                        height: 48
                        fillMode: Image.PreserveAspectFit
                        Layout.alignment: Qt.AlignHCenter
                    }

                    Text {
                        text: "Жрец"
                        font.pointSize: 14
                        font.bold: true
                        color: "#c2c2c2"
                        horizontalAlignment: Text.AlignHCenter
                        Layout.alignment: Qt.AlignHCenter
                    }
                }
            }
        }
    }

    Component.onCompleted: {
        if (editMode && editingMacro && editingMacro.type === "skill") {
            // Если редактируем скилл-макрос, сразу открываем форму редактирования
            editStackView.push("SkillEditForm.qml", {
                "editingMacro": editingMacro,
                "skill": null
            })
        }
    }
}
