import QtQuick 2.15
import QtQuick.Controls.Basic 2.15
import QtQuick.Layouts 1.15
import Qt5Compat.GraphicalEffects
import "components"

Window {
    id: overlay
    visible: false
    modality: Qt.NonModal
    flags: Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Dialog
    color: "transparent"
    width: 280
    height: 340
    x: Screen.width - width - 20
    y: 80
    title: "Fast OCR Debug"

    property var debugData: ({})
    property color accentColor: backend && backend.settings && backend.settings.accent_color ? backend.settings.accent_color : "#7793a1"

    Timer {
        interval: 200
        running: overlay.visible
        repeat: true
        onTriggered: {
            var raw = backend.getFastOCRDict()
            if (raw) {
                try {
                    debugData = JSON.parse(raw)
                } catch(e) {}
            }
        }
    }

    // Основной фон
    Rectangle {
        anchors.fill: parent
        radius: 12
        color: "#a01c1c1c"
        border.color: "#70454545"
        border.width: 1
        clip: true

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

        // Заголовок (только он перетаскивается)
        Rectangle {
            id: headerBar
            anchors.top: parent.top
            anchors.left: parent.left
            anchors.right: parent.right
            height: 36
            color: "#50000000"
            radius: 12

            Text {
                anchors.left: parent.left
                anchors.leftMargin: 12
                anchors.verticalCenter: parent.verticalCenter
                text: "Fast OCR"
                color: "white"
                font.pointSize: 11
                font.bold: true
            }

            // Кнопка закрытия
            Rectangle {
                anchors.right: parent.right
                anchors.rightMargin: 6
                anchors.verticalCenter: parent.verticalCenter
                width: 24
                height: 24
                radius: 5
                color: closeBtn.containsMouse ? "#e81123" : "transparent"

                MouseArea {
                    id: closeBtn
                    anchors.fill: parent
                    hoverEnabled: true
                    cursorShape: Qt.PointingHandCursor
                    onClicked: overlay.close()
                }

                Text {
                    anchors.centerIn: parent
                    text: "X"
                    color: closeBtn.containsMouse ? "white" : "#808080"
                    font.pointSize: 10
                    font.bold: true
                }
            }

            // Drag header
            MouseArea {
                anchors.fill: parent
                anchors.rightMargin: 34
                acceptedButtons: Qt.LeftButton
                property int startX: 0
                property int startY: 0
                onPressed: function(m) { startX = m.x; startY = m.y; }
                onPositionChanged: function(m) {
                    overlay.x += m.x - startX
                    overlay.y += m.y - startY
                }
            }
        }

        // Контент
        ColumnLayout {
            anchors.top: headerBar.bottom
            anchors.topMargin: 8
            anchors.left: parent.left
            anchors.right: parent.right
            anchors.bottom: parent.bottom
            anchors.margins: 12
            spacing: 6

            RowLayout {
                Layout.fillWidth: true
                spacing: 8
                ColumnLayout {
                    spacing: 1
                    Text {
                        text: "Дистанция"
                        color: "#aaaaaa"
                        font.pointSize: 8
                    }
                    Text {
                        text: (debugData.distance || 0).toFixed(1) + " м"
                        color: "#00ff88"
                        font.pointSize: 26
                        font.bold: true
                    }
                }
                Item { Layout.fillWidth: true }
                ColumnLayout {
                    spacing: 1
                    Text {
                        text: "Raw"
                        color: "#aaaaaa"
                        font.pointSize: 8
                    }
                    Text {
                        text: debugData.raw_text || ""
                        color: debugData.raw_text ? "#ffcc44" : "#666666"
                        font.pointSize: 14
                        font.bold: true
                    }
                }
            }

            Rectangle {
                Layout.fillWidth: true
                height: 1
                color: "#70454545"
            }

            Text {
                text: "История (последние 5):"
                color: "#aaaaaa"
                font.pointSize: 8
            }

            RowLayout {
                Layout.fillWidth: true
                spacing: 3
                Repeater {
                    model: debugData.history || []
                    Rectangle {
                        width: 36
                        height: 26
                        radius: 4
                        color: {
                            var cur = debugData.distance || 0
                            var diff = Math.abs(modelData - cur)
                            if (modelData <= 0) return "#333333"
                            if (diff < 0.5) return "#1a6633"
                            if (diff < 2) return "#665500"
                            return "#662222"
                        }
                        Text {
                            anchors.centerIn: parent
                            text: modelData > 0 ? modelData.toFixed(1) : "-"
                            color: "#cccccc"
                            font.pointSize: 8
                        }
                    }
                }
            }

            Rectangle {
                Layout.fillWidth: true
                height: 1
                color: "#70454545"
            }

            Text {
                text: "Обработанное изображение:"
                color: "#aaaaaa"
                font.pointSize: 8
            }

            Rectangle {
                Layout.fillWidth: true
                Layout.preferredHeight: 55
                radius: 4
                color: "#111111"
                border.color: "#40333333"
                border.width: 1
                Image {
                    anchors.fill: parent
                    anchors.margins: 2
                    fillMode: Image.PreserveAspectFit
                    source: debugData.image ? "data:image/png;base64," + debugData.image : ""
                }
                Text {
                    anchors.centerIn: parent
                    text: debugData.image ? "" : "Нет данных"
                    color: "#555555"
                    font.pointSize: 9
                }
            }
        }
    }

    function open() {
        visible = true
        raise()
        requestActivate()
    }

    function close() {
        visible = false
    }
}
