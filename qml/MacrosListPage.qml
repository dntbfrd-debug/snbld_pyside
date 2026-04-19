import QtQuick 2.15
import QtQuick.Controls.Basic 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

Item {
    id: macrosListPage

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 5

        ScrollView {
            Layout.fillWidth: true
            Layout.fillHeight: true
            ScrollBar.vertical.policy: ScrollBar.AsNeeded
            ScrollBar.horizontal.policy: ScrollBar.AsNeeded

            Item {
                id: gridWrapper
                width: Math.max(grid.implicitWidth, macrosListPage.width - 10)
                height: grid.implicitHeight

                GridLayout {
                    id: grid
                    anchors.horizontalCenter: parent.horizontalCenter
                    columns: 6
                    columnSpacing: 8
                    rowSpacing: 8

                    Repeater {
                    id: macrosRepeater
                    model: backend.macros

                    delegate: Rectangle {
                        width: 160
                        height: 160
                        color: "#99252525"
                        radius: 12
                        border.color: "#50ffffff"
                        border.width: 2
                        clip: true

                        ColumnLayout {
                            anchors.fill: parent
                            anchors.leftMargin: 12
                            anchors.rightMargin: 12
                            anchors.topMargin: 10
                            anchors.bottomMargin: 10
                            spacing: 4

                            Image {
                                source: {
                                    if (!ResourceHelper) return ""
                                    if (modelData.type === "skill" && modelData.skill_id) {
                                        return ResourceHelper.get_skill_icon_url(modelData.skill_id)
                                    }
                                    if (modelData.type === "buff" && modelData.buff_id) {
                                        return ResourceHelper.get_skill_icon_url(modelData.buff_id)
                                    }
                                    if (modelData.type === "simple") return ResourceHelper.get_icon_url("macros1.png")
                                    if (modelData.type === "zone") return ResourceHelper.get_icon_url("zone.png")
                                    if (modelData.type === "skill") return ResourceHelper.get_icon_url("skill.png")
                                    return ResourceHelper.get_icon_url("buff.png")
                                }
                                width: 32
                                height: 32
                                fillMode: Image.PreserveAspectFit
                                Layout.alignment: Qt.AlignHCenter
                            }

                            Text {
                                text: modelData.name
                                font.bold: true
                                font.pointSize: 8
                                color: "#c2c2c2"
                                horizontalAlignment: Text.AlignHCenter
                                wrapMode: Text.Wrap
                                Layout.fillWidth: true
                                Layout.preferredHeight: 30
                                maximumLineCount: 2
                            }

                            Text {
                                text: modelData.type === "simple" ? "Простой" :
                                      modelData.type === "zone" ? "Зональный" :
                                      modelData.type === "skill" ? "Скилл" : "Бафф"
                                font.pointSize: 8
                                color: "#a0a0a0"
                                horizontalAlignment: Text.AlignHCenter
                                Layout.fillWidth: true
                            }

                            Rectangle {
                                Layout.fillWidth: true
                                height: 20
                                color: backend && !backend.global_stopped ? "#204CAF50" : "#20ffffff"
                                radius: 4

                                RowLayout {
                                    anchors.centerIn: parent
                                    spacing: 4
                                    Text {
                                        text: backend && !backend.global_stopped ? "●" : "○"
                                        color: backend && !backend.global_stopped ? "#4CAF50" : "#c2c2c2"
                                        font.pointSize: 10
                                    }
                                    Text {
                                        text: backend && !backend.global_stopped ? "Активен" : "Остановлен"
                                        color: backend && !backend.global_stopped ? "#4CAF50" : "#c2c2c2"
                                        font.pointSize: 8
                                    }
                                }
                            }

                            Item { Layout.fillHeight: true }

                            RowLayout {
                                Layout.alignment: Qt.AlignHCenter
                                spacing: 4

                                BaseButton {
                                    text: "Изменить"
                                    implicitWidth: 65
                                    implicitHeight: 28
                                    iconSize: 10
                                    textSize: 8
                                    onClicked: {
                                        console.log("Edit clicked for:", modelData.name, "type:", modelData.type)
                                        backend.set_macro_for_edit(modelData)
                                        // Открываем соответствующую страницу редактирования
                                        if (modelData.type === "simple") {
                                            backend.pageChangeRequested("EditSimplePage.qml")
                                        } else if (modelData.type === "zone") {
                                            backend.pageChangeRequested("EditZonePage.qml")
                                        } else if (modelData.type === "skill") {
                                            backend.pageChangeRequested("EditSkillPage.qml")
                                        } else if (modelData.type === "buff") {
                                            backend.pageChangeRequested("EditBuffPage.qml")
                                        } else {
                                            backend.notification("Редактирование этого типа недоступно", "warning")
                                        }
                                    }
                                }
                                BaseButton {
                                    text: "Удалить"
                                    implicitWidth: 65
                                    implicitHeight: 28
                                    iconSize: 10
                                    textSize: 8
                                    onClicked: {
                                        _pendingDeleteName = modelData.name
                                        _showDeleteConfirm = true
                                    }
                                }
                            }
                        }
                    }
                }
            }
            }
        }

        // Пустое состояние — когда макросов нет
        Item {
            Layout.fillWidth: true
            Layout.fillHeight: true
            visible: backend && backend.macros && backend.macros.length === 0

            Column {
                anchors.centerIn: parent
                spacing: 12

                Text {
                    text: "📋"
                    font.pixelSize: 48
                    anchors.horizontalCenter: parent.horizontalCenter
                    opacity: 0.3
                }
                Text {
                    text: "Нет макросов"
                    color: "#c2c2c2"
                    font.pointSize: 14
                    font.bold: true
                    anchors.horizontalCenter: parent.horizontalCenter
                }
                Text {
                    text: "Перейдите во вкладку «Создание» в меню\nчтобы добавить первый макрос"
                    color: "#666666"
                    font.pointSize: 10
                    horizontalAlignment: Text.AlignHCenter
                }
            }
        }
    }

    Connections {
        target: backend
        function onMacrosChanged() {
            macrosRepeater.model = null
            macrosRepeater.model = backend.macros
        }
        function onMacroStatusChanged() {
            // Принудительно обновляем модель
            macrosRepeater.model = null
            macrosRepeater.model = backend.macros
        }
    }

    // Диалог подтверждения удаления
    property string _pendingDeleteName: ""
    property bool _showDeleteConfirm: false

    Rectangle {
        id: confirmDeleteOverlay
        anchors.fill: parent
        color: "#80000000"
        visible: _showDeleteConfirm
        z: 100

        Rectangle {
            anchors.centerIn: parent
            width: 360
            height: 200
            radius: 12
            color: "#2d2d2d"

            ColumnLayout {
                anchors.fill: parent
                anchors.margins: 24
                spacing: 10

                Text {
                    text: "Удалить макрос?"
                    color: "white"
                    font.pointSize: 13
                    font.bold: true
                    Layout.alignment: Qt.AlignHCenter
                }
                Text {
                    text: `"${_pendingDeleteName}"`
                    color: "#ef4444"
                    font.pointSize: 11
                    font.bold: true
                    Layout.alignment: Qt.AlignHCenter
                }
                Text {
                    text: "Это действие нельзя отменить."
                    color: "#888888"
                    font.pointSize: 10
                    Layout.alignment: Qt.AlignHCenter
                }

                Item { Layout.fillHeight: true }

                Row {
                    spacing: 12
                    Layout.alignment: Qt.AlignHCenter

                    BaseButton {
                        text: "Отмена"
                        implicitWidth: 120
                        implicitHeight: 34
                        textSize: 10
                        onClicked: {
                            _showDeleteConfirm = false
                            _pendingDeleteName = ""
                        }
                    }
                    BaseButton {
                        text: "Удалить"
                        implicitWidth: 120
                        implicitHeight: 34
                        textSize: 10
                        onClicked: {
                            if (_pendingDeleteName) {
                                backend.delete_macro(_pendingDeleteName)
                            }
                            _showDeleteConfirm = false
                            _pendingDeleteName = ""
                        }
                    }
                }
            }
        }
    }
}
