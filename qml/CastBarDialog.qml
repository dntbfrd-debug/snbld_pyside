import QtQuick 2.15
import QtQuick.Controls.Basic 2.15
import QtQuick.Layouts 1.15
import QtQuick.Window 2.15
import Qt5Compat.GraphicalEffects

// Диалог калибровки кастбара — стиль приложения
Window {
    id: castbarDialog
    visible: false
    modality: Qt.NonModal
    flags: Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Dialog
    color: "transparent"
    width: 400
    height: 460
    x: Screen.width / 2 - width / 2
    y: Screen.height / 6
    title: "Калибровка кастбара"

    // Состояния
    property string capturedColor: "0,0,0"
    property string selectedPoint: "0,0"
    property int currentThreshold: backend && backend.settings && backend.settings.castbar_threshold !== undefined ? backend.settings.castbar_threshold : 70
    property string calibrationState: "ready"
    property color accentColor: backend && backend.settings && backend.settings.accent_color ? backend.settings.accent_color : "#7793a1"

    signal calibrationStarted()
    signal colorCaptured(string point, string color)
    signal calibrationCancelled()
    signal calibrationAccepted(string point, var color, int threshold)

    // Основной фон
    Rectangle {
        anchors.fill: parent
        radius: 12
        color: "#2d2d2d"
        clip: true

        // Заголовок
        Rectangle {
            id: headerBar
            anchors.top: parent.top
            anchors.left: parent.left
            anchors.right: parent.right
            height: 45
            color: "#2a2a3a"

            Text {
                anchors.left: parent.left
                anchors.leftMargin: 16
                anchors.verticalCenter: parent.verticalCenter
                text: "▣ Калибровка кастбара"
                color: "white"
                font.pointSize: 13
                font.bold: true
            }

            // Кнопка закрытия
            Rectangle {
                anchors.right: parent.right
                anchors.rightMargin: 8
                anchors.verticalCenter: parent.verticalCenter
                width: 28
                height: 28
                radius: 6
                color: closeBtn.containsMouse ? "#e81123" : "transparent"

                MouseArea {
                    id: closeBtn
                    anchors.fill: parent
                    hoverEnabled: true
                    cursorShape: Qt.PointingHandCursor
                    onClicked: {
                        castbarDialog.calibrationState = "ready"
                        castbarDialog.calibrationCancelled()
                        castbarDialog.close()
                    }
                }

                Text {
                    anchors.centerIn: parent
                    text: "✕"
                    color: closeBtn.containsMouse ? "white" : "#808080"
                    font.pointSize: 10
                    font.bold: true
                }
            }
        }

        // Разделитель
        Rectangle {
            anchors.top: headerBar.bottom
            anchors.left: parent.left
            anchors.right: parent.right
            height: 1
            color: "#3a3a4a"
        }

        // Контент
        ColumnLayout {
            anchors.top: headerBar.bottom
            anchors.topMargin: 10
            anchors.left: parent.left
            anchors.right: parent.right
            anchors.bottom: parent.bottom
            anchors.margins: 15
            spacing: 10

            // === СОСТОЯНИЕ: ready ===
            ColumnLayout {
                Layout.fillWidth: true
                Layout.fillHeight: true
                visible: calibrationState === "ready"
                spacing: 10

                // Что такое кастбар?
                Rectangle {
                    Layout.fillWidth: true
                    height: 70
                    color: "#99252525"
                    radius: 8
                    border.color: "#50ffffff"
                    border.width: 2

                    ColumnLayout {
                        anchors.fill: parent
                        anchors.margins: 10
                        spacing: 4

                        Text {
                            text: "💡 Что такое кастбар?"
                            color: castbarDialog.accentColor
                            font.pointSize: 10
                            font.bold: true
                        }

                        Text {
                            text: "Полоска в игре, показывающая применение скилла."
                            color: "#c2c2c2"
                            font.pointSize: 9
                            wrapMode: Text.WordWrap
                            Layout.fillWidth: true
                        }
                    }
                }

                // Зачем калибровать?
                Rectangle {
                    Layout.fillWidth: true
                    height: 55
                    color: "#99252525"
                    radius: 8
                    border.color: "#50ffffff"
                    border.width: 2

                    ColumnLayout {
                        anchors.fill: parent
                        anchors.margins: 10
                        spacing: 4

                        Text {
                            text: "🎯 Зачем калибровать?"
                            color: "#FFD54F"
                            font.pointSize: 10
                            font.bold: true
                        }

                        Text {
                            text: "Программа запомнит цвет ромбика и будет определять начало каста."
                            color: "#c2c2c2"
                            font.pointSize: 9
                            wrapMode: Text.WordWrap
                            Layout.fillWidth: true
                        }
                    }
                }

                // Как калибровать?
                Rectangle {
                    Layout.fillWidth: true
                    height: 80
                    color: "#99252525"
                    radius: 8
                    border.color: "#50ffffff"
                    border.width: 2

                    ColumnLayout {
                        anchors.fill: parent
                        anchors.margins: 10
                        spacing: 4

                        Text {
                            text: "📋 Как калибровать:"
                            color: "#4CAF50"
                            font.pointSize: 10
                            font.bold: true
                        }

                        Text {
                            text: "1. Нажмите '▶ Начать'\n2. Примените скилл в игре\n3. Кликните ЛКМ на ромбик в начале полоски"
                            color: "#c2c2c2"
                            font.pointSize: 9
                            wrapMode: Text.WordWrap
                            Layout.fillWidth: true
                        }
                    }
                }

                // Кнопка Начать
                Item { height: 10 }

                BaseButton {
                    Layout.alignment: Qt.AlignHCenter
                    text: "▶ Начать калибровку"
                    implicitWidth: 200
                    implicitHeight: 42
                    iconSize: 0
                    textSize: 11
                    accentColor: castbarDialog.accentColor
                    onClicked: {
                        console.log("CastBarDialog: Нажата кнопка 'Начать'")
                        castbarDialog.calibrationState = "waiting"
                        capturedColor = "0,0,0"
                        selectedPoint = "0,0"
                        castbarDialog.calibrationStarted()
                    }
                }

                Item { height: 10 }
            }

            // === СОСТОЯНИЕ: waiting ===
            ColumnLayout {
                Layout.fillWidth: true
                Layout.fillHeight: true
                visible: calibrationState === "waiting"
                spacing: 15

                // Индикатор ожидания
                Rectangle {
                    Layout.alignment: Qt.AlignHCenter
                    width: 220
                    height: 110
                    color: "#99252525"
                    radius: 10
                    border.color: "#4CAF50"
                    border.width: 2

                    ColumnLayout {
                        anchors.centerIn: parent
                        spacing: 10

                        Rectangle {
                            Layout.alignment: Qt.AlignHCenter
                            width: 40
                            height: 40
                            radius: 20
                            color: "#4CAF50"
                            opacity: 0.3

                            SequentialAnimation on opacity {
                                running: calibrationState === "waiting"
                                loops: Animation.Infinite
                                NumberAnimation { from: 0.2; to: 0.8; duration: 800 }
                                NumberAnimation { from: 0.8; to: 0.2; duration: 800 }
                            }
                        }

                        Text {
                            text: "⏳ Ожидание клика..."
                            color: "#4CAF50"
                            font.pointSize: 12
                            font.bold: true
                            anchors.horizontalCenter: parent.horizontalCenter
                        }
                    }
                }

                // Инструкция
                Rectangle {
                    Layout.fillWidth: true
                    height: 100
                    color: "#99252525"
                    radius: 8
                    border.color: "#50ffffff"
                    border.width: 2

                    ColumnLayout {
                        anchors.fill: parent
                        anchors.margins: 10
                        spacing: 6

                        Text {
                            text: "📌 Что делать:"
                            color: "#FFD54F"
                            font.pointSize: 10
                            font.bold: true
                        }

                        Text {
                            text: "1. Примените скилл в игре\n2. Найдите полоску каста (появится при касте)\n3. Кликните ЛКМ на ромбик в начале полоски"
                            color: "#c2c2c2"
                            font.pointSize: 9
                            wrapMode: Text.WordWrap
                            Layout.fillWidth: true
                        }

                        Text {
                            text: "💡 Ромбик обычно находится слева от полоски"
                            color: "#4CAF50"
                            font.pointSize: 9
                            font.italic: true
                            Layout.fillWidth: true
                        }
                    }
                }

                Item { Layout.fillHeight: true }

                // Кнопка Отмена
                BaseButton {
                    Layout.alignment: Qt.AlignHCenter
                    text: "✕ Отмена"
                    implicitWidth: 140
                    implicitHeight: 40
                    iconSize: 0
                    textSize: 10
                    onClicked: {
                        console.log("CastBarDialog: Отмена")
                        castbarDialog.calibrationState = "ready"
                        castbarDialog.calibrationCancelled()
                        castbarDialog.close()
                    }
                }

                Item { Layout.fillHeight: true }
            }

            // === СОСТОЯНИЕ: captured ===
            ColumnLayout {
                Layout.fillWidth: true
                Layout.fillHeight: true
                visible: calibrationState === "captured"
                spacing: 12

                // Успех
                Rectangle {
                    Layout.alignment: Qt.AlignHCenter
                    width: 220
                    height: 60
                    color: "#1a3a1a"
                    radius: 10
                    border.color: "#4CAF50"
                    border.width: 2

                    Text {
                        anchors.centerIn: parent
                        text: "✅ Цвет захвачен!"
                        color: "#4CAF50"
                        font.pointSize: 14
                        font.bold: true
                    }
                }

                // Предпросмотр цвета
                Rectangle {
                    Layout.fillWidth: true
                    height: 70
                    color: "#99252525"
                    radius: 8
                    border.color: "#50ffffff"
                    border.width: 2

                    RowLayout {
                        anchors.centerIn: parent
                        spacing: 15

                        Rectangle {
                            width: 45
                            height: 45
                            radius: 6
                            color: {
                                var parts = capturedColor.split(',')
                                if (parts.length === 3)
                                    return Qt.rgba(parts[0]/255, parts[1]/255, parts[2]/255, 1.0)
                                return "#000000"
                            }
                            border.color: "#ffffff"
                            border.width: 1
                        }

                        ColumnLayout {
                            spacing: 4

                            Text {
                                text: "RGB(" + castbarDialog.capturedColor + ")"
                                color: "#e0e0e0"
                                font.pointSize: 12
                                font.bold: true
                            }

                            Text {
                                text: "Точка: " + castbarDialog.selectedPoint
                                color: "#808080"
                                font.pointSize: 9
                            }
                        }
                    }
                }

                // Описание действий
                Rectangle {
                    Layout.fillWidth: true
                    height: 50
                    color: "#99252525"
                    radius: 8
                    border.color: "#50ffffff"
                    border.width: 2

                    Text {
                        anchors.centerIn: parent
                        text: "Выберите действие:"
                        color: "#b0b0b0"
                        font.pointSize: 10
                    }
                }

                Item { Layout.fillHeight: true }

                // Кнопки
                RowLayout {
                    Layout.alignment: Qt.AlignHCenter
                    spacing: 10

                    // OK
                    BaseButton {
                        text: "✓ OK"
                        implicitWidth: 100
                        implicitHeight: 40
                        iconSize: 0
                        textSize: 11
                        accentColor: "#4CAF50"
                        onClicked: {
                            console.log("CastBarDialog: OK")
                            var parts = capturedColor.split(',')
                            var colorArr = [parseInt(parts[0]), parseInt(parts[1]), parseInt(parts[2])]
                            castbarDialog.calibrationAccepted(castbarDialog.selectedPoint, colorArr, castbarDialog.currentThreshold)
                            castbarDialog.close()
                        }
                    }

                    // Ещё раз
                    BaseButton {
                        text: "⟲ Ещё раз"
                        implicitWidth: 120
                        implicitHeight: 40
                        iconSize: 0
                        textSize: 10
                        accentColor: "#FF9800"
                        onClicked: {
                            console.log("CastBarDialog: Ещё раз")
                            castbarDialog.calibrationState = "waiting"
                            capturedColor = "0,0,0"
                            selectedPoint = "0,0"
                            castbarDialog.calibrationStarted()
                        }
                    }

                    // Отмена
                    BaseButton {
                        text: "✕ Отмена"
                        implicitWidth: 110
                        implicitHeight: 40
                        iconSize: 0
                        textSize: 10
                        onClicked: {
                            console.log("CastBarDialog: Отмена")
                            castbarDialog.calibrationState = "ready"
                            castbarDialog.calibrationCancelled()
                            castbarDialog.close()
                        }
                    }
                }

                Item { Layout.fillHeight: true }
            }
        }
    }

    // Обработка закрытия
    onClosing: {
        console.log("CastBarDialog: onClosing, state=" + calibrationState)
        calibrationState = "ready"
        castbarDialog.calibrationCancelled()
    }

    // Esc
    Shortcut {
        sequence: "Esc"
        onActivated: {
            if (calibrationState === "waiting") {
                castbarDialog.calibrationState = "ready"
                castbarDialog.calibrationCancelled()
                castbarDialog.close()
            } else {
                castbarDialog.close()
            }
        }
    }
}
