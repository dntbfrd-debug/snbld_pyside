import QtQuick 2.15
import QtQuick.Controls.Basic 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import "components"

Item {
    id: macrosListPage

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 5

        ScrollView {
            Layout.fillWidth: true
            Layout.fillHeight: true
            Layout.topMargin: 10
            ScrollBar.vertical: GlassScrollBar {}
            ScrollBar.horizontal: GlassScrollBar { policy: ScrollBar.AlwaysOff }

                Item {
                    id: gridWrapper
                    width: Math.max(grid.implicitWidth, macrosListPage.width - 10)
                    height: grid.implicitHeight + 10

                    GridLayout {
                        id: grid
                        anchors.horizontalCenter: parent.horizontalCenter
                        anchors.top: parent.top
                        anchors.topMargin: 10
                        columns: 6
                        columnSpacing: 8
                        rowSpacing: 8

                        Repeater {
                            id: macrosRepeater
                            model: backend.macros

                            delegate: Item {
                                id: tileWrapper
                                implicitWidth: 160
                                implicitHeight: 160

                                property bool _tileHovered: tileRoot.hovered || btnEdit.hovered || btnDelete.hovered

                                BaseButton {
                                    id: tileRoot
                                    anchors.fill: parent
                                    buttonRadius: 12
                                    iconSource: ""
                                    text: ""

                                    onClicked: {
                                        backend.set_macro_for_edit(modelData)
                                        if (modelData.type === "simple")
                                            backend.pageChangeRequested("EditSimplePage.qml")
                                        else if (modelData.type === "zone")
                                            backend.pageChangeRequested("EditZonePage.qml")
                                        else if (modelData.type === "skill")
                                            backend.pageChangeRequested("EditSkillPage.qml")
                                        else if (modelData.type === "buff")
                                            backend.pageChangeRequested("EditBuffPage.qml")
                                    }

                                    contentItem: ColumnLayout {
                                        anchors.fill: parent
                                        anchors.leftMargin: 12
                                        anchors.rightMargin: 12
                                        anchors.topMargin: 10
                                        anchors.bottomMargin: 10
                                        spacing: 4
                                        z: 2

                                        Image {
                                            source: {
                                                if (!ResourceHelper) return ""
                                                if (modelData.type === "skill" && modelData.skill_id)
                                                    return ResourceHelper.get_skill_icon_url(modelData.skill_id)
                                                if (modelData.type === "buff" && modelData.buff_id)
                                                    return ResourceHelper.get_skill_icon_url(modelData.buff_id)
                                                if (modelData.type === "simple") return ResourceHelper.get_icon_url("macros1.png")
                                                if (modelData.type === "zone") return ResourceHelper.get_icon_url("zone.png")
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
                                            color: "#a2a2a2"
                                            horizontalAlignment: Text.AlignHCenter
                                            wrapMode: Text.Wrap
                                            Layout.fillWidth: true
                                            Layout.preferredHeight: 30
                                            maximumLineCount: 2
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
                                                    text: backend && !backend.global_stopped ? "\u25cf" : "\u25cb"
                                                    color: backend && !backend.global_stopped ? "#4CAF50" : "#a2a2a2"
                                                    font.pointSize: 10
                                                }
                                                Text {
                                                    text: backend && !backend.global_stopped ? "Активен" : "Остановлен"
                                                    color: backend && !backend.global_stopped ? "#4CAF50" : "#a2a2a2"
                                                    font.pointSize: 8
                                                }
                                            }
                                        }

                                        Item { Layout.fillHeight: true }

                                        RowLayout {
                                            Layout.fillWidth: true
                                            spacing: 4
                                            opacity: _tileHovered ? 1 : 0
                                            Behavior on opacity { NumberAnimation { duration: 150 } }

                                            BaseButton {
                                                id: btnEdit
                                                text: "Изменить"
                                                Layout.fillWidth: true
                                                implicitHeight: 28
                                                iconSize: 10
                                                textSize: 8
                                                onClicked: {
                                                    backend.set_macro_for_edit(modelData)
                                                    if (modelData.type === "simple")
                                                        backend.pageChangeRequested("EditSimplePage.qml")
                                                    else if (modelData.type === "zone")
                                                        backend.pageChangeRequested("EditZonePage.qml")
                                                    else if (modelData.type === "skill")
                                                        backend.pageChangeRequested("EditSkillPage.qml")
                                                    else if (modelData.type === "buff")
                                                        backend.pageChangeRequested("EditBuffPage.qml")
                                                }
                                            }
                                            BaseButton {
                                                id: btnDelete
                                                text: "Удалить"
                                                Layout.fillWidth: true
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
                    text: ""
                    font.pixelSize: 48
                    anchors.horizontalCenter: parent.horizontalCenter
                    opacity: 0.3
                }
                Text {
                    text: "Нет макросов"
                    color: "#a2a2a2"
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

    property var _macrosModel: []
    property bool _modelDirty: false

    Connections {
        target: backend
        function onMacrosChanged() {
            _macrosModel = backend.macros
            _modelDirty = true
        }
        function onMacroStatusChanged() {
            _macrosModel = backend.macros
            _modelDirty = true
        }
    }

    Timer {
        interval: 100
        repeat: false
        running: _modelDirty
        onTriggered: {
            macrosRepeater.model = null
            macrosRepeater.model = _macrosModel
            _modelDirty = false
        }
    }

    // Диалог подтверждения удаления
    property string _pendingDeleteName: ""
    property bool _showDeleteConfirm: false

    Rectangle {
        id: confirmDeleteOverlay
        anchors.fill: parent
        color: "#40000000"
        visible: _showDeleteConfirm
        anchors.topMargin: -40
        anchors.leftMargin: -52
        anchors.rightMargin: -52
        opacity: _showDeleteConfirm ? 1 : 0
        z: 100

        Behavior on opacity { NumberAnimation { duration: 200 } }

        Rectangle {
            anchors.centerIn: parent
            width: 360
            height: 200
            radius: 12
            color: "#a01c1c1c"
            border.color: "#70454545"
            border.width: 1

            Rectangle {
                anchors.fill: parent
                radius: parent.radius
                gradient: Gradient {
                    GradientStop { position: 0.0; color: "#60000000" }
                    GradientStop { position: 0.35; color: "#30000000" }
                    GradientStop { position: 0.7; color: "#10000000" }
                    GradientStop { position: 1.0; color: "#00000000" }
                }
            }

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
