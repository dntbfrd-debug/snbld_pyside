import QtQuick 2.15
import QtQuick.Controls.Basic 2.15
import QtQuick.Layouts 1.15
import QtQuick.Window 2.15

// Диалог калибровки точки клика для баффа 8004
// Стиль统一 с CastBarDialog и OCRCalibrationDialog
Window {
    id: buffCalibDialog
    visible: false
    modality: Qt.NonModal
    flags: Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Dialog
    color: "transparent"
    width: 400
    height: 500
    x: Screen.width / 2 - width / 2
    y: Screen.height / 6
    title: "Калибровка точки клика"

    // Состояния: ready → waiting → captured
    property string calibrationState: "ready"
    property string selectedPoint: "0,0"
    property color accentColor: backend && backend.settings && backend.settings.accent_color ? backend.settings.accent_color : "#7793a1"

    signal pointCaptured(string point)
    signal calibrationCancelled()

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
                text: "▣ Калибровка точки клика"
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
                        buffCalibDialog.calibrationState = "ready"
                        buffCalibDialog.calibrationCancelled()
                        buffCalibDialog.close()
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

                // Что такое точка клика?
                Rectangle {
                    Layout.fillWidth: true
                    Layout.preferredHeight: whatPointLayout.implicitHeight + 20
                    color: "#99252525"
                    radius: 8
                    border.color: "#50ffffff"
                    border.width: 2

                    ColumnLayout {
                        id: whatPointLayout
                        anchors.fill: parent
                        anchors.margins: 10
                        spacing: 4

                        Text {
                            text: "💡 Зачем нужна точка клика?"
                            color: buffCalibDialog.accentColor
                            font.pointSize: 10
                            font.bold: true
                        }

                        Text {
                            text: "Бафф «Светлая опека духов» требует выбора цели. Эта функция автоматически кликает по вашему персонажу в игре, чтобы он стал целью для баффа."
                            color: "#c2c2c2"
                            font.pointSize: 9
                            wrapMode: Text.WordWrap
                            Layout.fillWidth: true
                        }
                    }
                }

                // Где выбирать точку?
                Rectangle {
                    Layout.fillWidth: true
                    Layout.preferredHeight: wherePointLayout.implicitHeight + 20
                    color: "#99252525"
                    radius: 8
                    border.color: "#50ffffff"
                    border.width: 2

                    ColumnLayout {
                        id: wherePointLayout
                        anchors.fill: parent
                        anchors.margins: 10
                        spacing: 4

                        Text {
                            text: "🎯 Куда кликать?"
                            color: "#FFD54F"
                            font.pointSize: 10
                            font.bold: true
                        }

                        Text {
                            text: "Выберите точку на верхнем таргете (иконка персонажа в интерфейсе игры). Это точка, по которой программа будет кликать, чтобы выбрать вашего персонажа как цель."
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
                    Layout.preferredHeight: howCalibrateLayout.implicitHeight + 20
                    color: "#99252525"
                    radius: 8
                    border.color: "#50ffffff"
                    border.width: 2

                    ColumnLayout {
                        id: howCalibrateLayout
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
                            text: "1. Нажмите '▶ Начать калибровку'\n2. Кликните ЛКМ на верхний таргет вашего персонажа\n3. Координаты будут сохранены автоматически"
                            color: "#c2c2c2"
                            font.pointSize: 9
                            wrapMode: Text.WordWrap
                            Layout.fillWidth: true
                        }
                    }
                }

                // Текущая точка
                Rectangle {
                    Layout.fillWidth: true
                    height: 40
                    color: "#99252525"
                    radius: 8
                    border.color: "#50ffffff"
                    border.width: 2

                    RowLayout {
                        anchors.centerIn: parent
                        spacing: 10

                        Text {
                            text: "Текущая точка:"
                            color: "#808080"
                            font.pointSize: 9
                        }

                        Text {
                            text: selectedPoint
                            color: selectedPoint !== "0,0" ? "#4CAF50" : "#F44336"
                            font.pointSize: 11
                            font.bold: true
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
                    accentColor: buffCalibDialog.accentColor
                    onClicked: {
                        console.log("BuffCalibrationDialog: Нажата кнопка 'Начать'")
                        buffCalibDialog.calibrationState = "waiting"
                        selectedPoint = "0,0"
                        pointOverlay.visible = true
                        pointOverlay.raise()
                        pointOverlay.requestActivate()
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
                            Layout.alignment: Qt.AlignHCenter
                        }
                    }
                }

                // Инструкция
                Rectangle {
                    Layout.fillWidth: true
                    Layout.preferredHeight: waitingHintLayout.implicitHeight + 20
                    color: "#99252525"
                    radius: 8
                    border.color: "#50ffffff"
                    border.width: 2

                    ColumnLayout {
                        id: waitingHintLayout
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
                            text: "Кликните ЛКМ на верхний таргет вашего персонажа.\nКоординаты будут сохранены.\nESC для отмены."
                            color: "#c2c2c2"
                            font.pointSize: 9
                            wrapMode: Text.WordWrap
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
                        console.log("BuffCalibrationDialog: Отмена")
                        buffCalibDialog.calibrationState = "ready"
                        buffCalibDialog.calibrationCancelled()
                        buffCalibDialog.close()
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
                        text: "✅ Точка захвачена!"
                        color: "#4CAF50"
                        font.pointSize: 14
                        font.bold: true
                        horizontalAlignment: Text.AlignHCenter
                        verticalAlignment: Text.AlignVCenter
                    }
                }

                // Предпросмотр координат
                Rectangle {
                    Layout.fillWidth: true
                    height: 70
                    color: "#99252525"
                    radius: 8
                    border.color: "#50ffffff"
                    border.width: 2

                    ColumnLayout {
                        anchors.centerIn: parent
                        spacing: 4

                        Text {
                            text: "Координаты: " + buffCalibDialog.selectedPoint
                            color: "#e0e0e0"
                            font.pointSize: 14
                            font.bold: true
                            Layout.alignment: Qt.AlignHCenter
                        }

                        Text {
                            text: "Клик будет выполнен в эту точку"
                            color: "#808080"
                            font.pointSize: 9
                            Layout.alignment: Qt.AlignHCenter
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
                        horizontalAlignment: Text.AlignHCenter
                        verticalAlignment: Text.AlignVCenter
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
                            console.log("BuffCalibrationDialog: OK")
                            buffCalibDialog.pointCaptured(buffCalibDialog.selectedPoint)
                            buffCalibDialog.close()
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
                            console.log("BuffCalibrationDialog: Ещё раз")
                            buffCalibDialog.calibrationState = "waiting"
                            selectedPoint = "0,0"
                            pointOverlay.visible = true
                            pointOverlay.raise()
                            pointOverlay.requestActivate()
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
                            console.log("BuffCalibrationDialog: Отмена")
                            buffCalibDialog.calibrationState = "ready"
                            buffCalibDialog.calibrationCancelled()
                            buffCalibDialog.close()
                        }
                    }
                }

                Item { Layout.fillHeight: true }
            }
        }
    }

    // Оверлей для выбора точки (полноэкранный)
    Window {
        id: pointOverlay
        flags: Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint
        color: "#60000000"
        width: Screen.width
        height: Screen.height
        visible: false
        title: "Выберите точку"

        MouseArea {
            anchors.fill: parent
            propagateComposedEvents: false
            onClicked: function(mouse) {
                var globalPos = mapToGlobal(Qt.point(mouse.x, mouse.y))
                console.log("BuffCalibration: Point selected at", globalPos.x, globalPos.y)
                selectedPoint = globalPos.x + "," + globalPos.y
                pointOverlay.visible = false
                pointOverlay.close()
                buffCalibDialog.calibrationState = "captured"
                buffCalibDialog.show()
                buffCalibDialog.raise()
                buffCalibDialog.requestActivate()
            }
        }

        // Инструкция в центре
        Rectangle {
            anchors.centerIn: parent
            width: instructionText.width + 40
            height: instructionText.height + 30
            color: "#aa000000"
            radius: 12
            z: 90

            Text {
                id: instructionText
                anchors.centerIn: parent
                text: "Кликните на верхний таргет\nвашего персонажа\nESC для отмены"
                color: "white"
                font.pointSize: 16
                font.bold: true
                horizontalAlignment: Text.AlignHCenter
                wrapMode: Text.WordWrap
            }
        }

        Shortcut {
            sequence: "Esc"
            onActivated: {
                pointOverlay.visible = false
                pointOverlay.close()
                buffCalibDialog.calibrationState = "ready"
                buffCalibDialog.calibrationCancelled()
                buffCalibDialog.show()
                buffCalibDialog.raise()
                buffCalibDialog.requestActivate()
            }
        }
    }

    // Обработка закрытия
    onClosing: {
        console.log("BuffCalibrationDialog: onClosing, state=" + calibrationState)
        calibrationState = "ready"
        pointOverlay.visible = false
    }

    // Esc
    Shortcut {
        sequence: "Esc"
        onActivated: {
            if (calibrationState === "waiting") {
                pointOverlay.visible = false
                buffCalibDialog.calibrationState = "ready"
                buffCalibDialog.calibrationCancelled()
                buffCalibDialog.close()
            } else {
                buffCalibDialog.close()
            }
        }
    }
}
