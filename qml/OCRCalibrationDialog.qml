import QtQuick 2.15
import QtQuick.Controls.Basic 2.15
import QtQuick.Layouts 1.15
import QtQuick.Window 2.15
import Qt5Compat.GraphicalEffects

// Диалог комплексной калибровки OCR
// Пошаговый визард: выбор области моба → тест → выбор области игрока → тест → готово
Window {
    id: ocrCalibDialog
    visible: false
    modality: Qt.NonModal
    flags: Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Dialog
    color: "transparent"
    width: 520
    height: 600
    x: Screen.width / 2 - width / 2
    y: Screen.height / 10
    title: "Калибровка OCR"

    // Состояния: ready → select_mob → test_mob → test_mob_result → select_player → test_player → test_player_result → done
    property string calibrationState: "ready"
    property color accentColor: backend && backend.settings && backend.settings.accent_color ? backend.settings.accent_color : "#7793a1"

    // Данные тестирования
    property var mobTestResult: null
    property var playerTestResult: null
    property string mobPreviewImage: ""
    property string playerPreviewImage: ""

    // Подключение сигналов backend
    Connections {
        target: backend
        function onOcrTestResult(targetType, result) {
            if (targetType === "mob") {
                mobTestResult = result
                mobPreviewImage = result.image || ""
                ocrCalibDialog.calibrationState = "test_mob_result"
            } else if (targetType === "player") {
                playerTestResult = result
                playerPreviewImage = result.image || ""
                ocrCalibDialog.calibrationState = "test_player_result"
            }
        }
    }

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
                text: "▣ Калибровка OCR"
                color: "white"
                font.pointSize: 13
                font.bold: true
            }

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
                        ocrCalibDialog.calibrationState = "ready"
                        ocrCalibDialog.calibrationCancelled()
                        ocrCalibDialog.close()
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

        Rectangle {
            anchors.top: headerBar.bottom
            anchors.left: parent.left
            anchors.right: parent.right
            height: 1
            color: "#3a3a4a"
        }

        // Прогресс-бар
        Rectangle {
            anchors.top: headerBar.bottom
            anchors.left: parent.left
            anchors.right: parent.right
            height: 3
            color: "#1a1a2e"

            Rectangle {
                width: parent.width * {
                    "ready": 0.0, "select_mob": 0.1, "test_mob": 0.2, "test_mob_result": 0.35,
                    "select_player": 0.5, "test_player": 0.6, "test_player_result": 0.85, "done": 1.0
                }[ocrCalibDialog.calibrationState] || 0
                height: parent.height
                color: ocrCalibDialog.accentColor
                radius: 2

                Behavior on width {
                    NumberAnimation { duration: 300; easing.type: Easing.OutCubic }
                }
            }
        }

        // Контент
        ColumnLayout {
            anchors.top: headerBar.bottom
            anchors.topMargin: 15
            anchors.left: parent.left
            anchors.right: parent.right
            anchors.bottom: parent.bottom
            anchors.margins: 18
            spacing: 12

            // === ready ===
            ColumnLayout {
                Layout.fillWidth: true
                Layout.fillHeight: true
                visible: calibrationState === "ready"
                spacing: 12

                Rectangle {
                    Layout.fillWidth: true
                    Layout.preferredHeight: infoLayout.implicitHeight + 20
                    color: "#99252525"
                    radius: 8
                    border.color: "#50ffffff"
                    border.width: 2

                    ColumnLayout {
                        id: infoLayout
                        anchors.fill: parent
                        anchors.margins: 12
                        spacing: 6

                        Text {
                            text: "💡 Что такое OCR?"
                            color: ocrCalibDialog.accentColor
                            font.pointSize: 10
                            font.bold: true
                        }

                        Text {
                            text: "OCR (Optical Character Recognition) — технология распознавания текста. Программа «видит» числа дистанции в интерфейсе игры так же, как вы."
                            color: "#c2c2c2"
                            font.pointSize: 9
                            wrapMode: Text.WordWrap
                            Layout.fillWidth: true
                        }
                    }
                }

                Rectangle {
                    Layout.fillWidth: true
                    Layout.preferredHeight: stepsLayout.implicitHeight + 20
                    color: "#99252525"
                    radius: 8
                    border.color: "#50ffffff"
                    border.width: 2

                    ColumnLayout {
                        id: stepsLayout
                        anchors.fill: parent
                        anchors.margins: 12
                        spacing: 6

                        Text {
                            text: "📋 Пошаговая инструкция:"
                            color: "#4CAF50"
                            font.pointSize: 10
                            font.bold: true
                        }

                        Text {
                            text: "Шаг 1: Выберите область моба — выделите прямоугольник вокруг числа дистанции до цели (верхний таргет в интерфейсе игры)"
                            color: "#c2c2c2"
                            font.pointSize: 9
                            wrapMode: Text.WordWrap
                            Layout.fillWidth: true
                        }

                        Text {
                            text: "Шаг 2: Проверьте результат — программа распознаёт число и покажет превью. Если верно — нажмите «Далее»"
                            color: "#c2c2c2"
                            font.pointSize: 9
                            wrapMode: Text.WordWrap
                            Layout.fillWidth: true
                        }

                        Text {
                            text: "Шаг 3: Выберите область игрока — выделите область дистанции от вас до цели (нижний таргет)"
                            color: "#c2c2c2"
                            font.pointSize: 9
                            wrapMode: Text.WordWrap
                            Layout.fillWidth: true
                        }

                        Text {
                            text: "Шаг 4: Проверьте результат и нажмите «Готово»"
                            color: "#c2c2c2"
                            font.pointSize: 9
                            wrapMode: Text.WordWrap
                            Layout.fillWidth: true
                        }
                    }
                }

                Rectangle {
                    Layout.fillWidth: true
                    height: 50
                    color: "#99252525"
                    radius: 8
                    border.color: "#50ffffff"
                    border.width: 2

                    RowLayout {
                        anchors.centerIn: parent
                        spacing: 15

                        Rectangle {
                            width: 30; height: 30; radius: 6
                            color: {
                                var area = backend && backend.settings ? backend.settings.mob_area : ""
                                return (area && area !== "") ? "#4CAF50" : "#555555"
                            }
                            Text {
                                anchors.centerIn: parent
                                text: "1"
                                color: "white"
                                font.pointSize: 12
                                font.bold: true
                                horizontalAlignment: Text.AlignHCenter
                                verticalAlignment: Text.AlignVCenter
                            }
                        }
                        Text { text: "Моб"; color: "#c2c2c2"; font.pointSize: 10 }

                        Rectangle {
                            width: 30; height: 30; radius: 6
                            color: {
                                var area = backend && backend.settings ? backend.settings.player_area : ""
                                return (area && area !== "") ? "#4CAF50" : "#555555"
                            }
                            Text {
                                anchors.centerIn: parent
                                text: "2"
                                color: "white"
                                font.pointSize: 12
                                font.bold: true
                                horizontalAlignment: Text.AlignHCenter
                                verticalAlignment: Text.AlignVCenter
                            }
                        }
                        Text { text: "Игрок"; color: "#c2c2c2"; font.pointSize: 10 }
                    }
                }

                Item { Layout.fillHeight: true }

                BaseButton {
                    Layout.alignment: Qt.AlignHCenter
                    text: "▶ Начать калибровку"
                    implicitWidth: 220
                    implicitHeight: 42
                    iconSize: 0
                    textSize: 11
                    accentColor: ocrCalibDialog.accentColor
                    onClicked: {
                        ocrCalibDialog.calibrationState = "select_mob"
                        backend.selectOCRArea("mob")
                    }
                }

                Item { Layout.fillHeight: true }
            }

            // === select_mob ===
            ColumnLayout {
                Layout.fillWidth: true
                Layout.fillHeight: true
                visible: calibrationState === "select_mob"
                spacing: 14

                Rectangle {
                    Layout.alignment: Qt.AlignHCenter
                    width: 260
                    height: 80
                    color: "#99252525"
                    radius: 10
                    border.color: "#FFD54F"
                    border.width: 2

                    ColumnLayout {
                        anchors.centerIn: parent
                        spacing: 6

                        Text {
                            text: "🎯 Шаг 1: Область моба"
                            color: "#FFD54F"
                            font.pointSize: 13
                            font.bold: true
                            Layout.alignment: Qt.AlignHCenter
                        }

                        Text {
                            text: "Откроется прозрачное окно — выделите область"
                            color: "#c2c2c2"
                            font.pointSize: 9
                            Layout.alignment: Qt.AlignHCenter
                        }
                    }
                }

                Rectangle {
                    Layout.fillWidth: true
                    Layout.preferredHeight: hintLayout.implicitHeight + 20
                    color: "#99252525"
                    radius: 8
                    border.color: "#50ffffff"
                    border.width: 2

                    ColumnLayout {
                        id: hintLayout
                        anchors.fill: parent
                        anchors.margins: 12
                        spacing: 6

                        Text {
                            text: "📌 Как выбрать область:"
                            color: "#FFD54F"
                            font.pointSize: 10
                            font.bold: true
                        }

                        Text {
                            text: "• Откроется прозрачное окно поверх всех окон\n• Зажмите ЛКМ и потяните, чтобы выделить прямоугольник\n• Выделите ТОЛЬКО число дистанции (без текста «м», «моб» и т.д.)\n• Отпустите ЛКМ для сохранения"
                            color: "#c2c2c2"
                            font.pointSize: 9
                            wrapMode: Text.WordWrap
                            Layout.fillWidth: true
                        }

                        Text {
                            text: "💡 Совет: область должна быть минимальной — только цифры, без лишних элементов"
                            color: ocrCalibDialog.accentColor
                            font.pointSize: 9
                            font.italic: true
                            wrapMode: Text.WordWrap
                            Layout.fillWidth: true
                        }
                    }
                }

                Item { Layout.fillHeight: true }

                RowLayout {
                    Layout.alignment: Qt.AlignHCenter
                    spacing: 10

                    BaseButton {
                        text: "⟳ Выбрать снова"
                        implicitWidth: 150
                        implicitHeight: 40
                        iconSize: 0
                        textSize: 10
                        onClicked: backend.selectOCRArea("mob")
                    }

                    BaseButton {
                        text: "Далее →"
                        implicitWidth: 120
                        implicitHeight: 40
                        iconSize: 0
                        textSize: 11
                        accentColor: "#4CAF50"
                        onClicked: {
                            ocrCalibDialog.calibrationState = "test_mob"
                            backend.testOCRArea("mob")
                        }
                    }

                    BaseButton {
                        text: "✕ Отмена"
                        implicitWidth: 100
                        implicitHeight: 40
                        iconSize: 0
                        textSize: 10
                        onClicked: {
                            ocrCalibDialog.calibrationState = "ready"
                            ocrCalibDialog.calibrationCancelled()
                            ocrCalibDialog.close()
                        }
                    }
                }

                Item { Layout.fillHeight: true }
            }

            // === test_mob ===
            ColumnLayout {
                Layout.fillWidth: true
                Layout.fillHeight: true
                visible: calibrationState === "test_mob"
                spacing: 15

                Rectangle {
                    Layout.alignment: Qt.AlignHCenter
                    width: 220
                    height: 100
                    color: "#99252525"
                    radius: 10
                    border.color: ocrCalibDialog.accentColor
                    border.width: 2

                    ColumnLayout {
                        anchors.centerIn: parent
                        spacing: 10

                        Rectangle {
                            Layout.alignment: Qt.AlignHCenter
                            width: 36; height: 36; radius: 18
                            color: ocrCalibDialog.accentColor
                            opacity: 0.3

                            SequentialAnimation on opacity {
                                running: calibrationState === "test_mob"
                                loops: Animation.Infinite
                                NumberAnimation { from: 0.2; to: 0.8; duration: 800 }
                                NumberAnimation { from: 0.8; to: 0.2; duration: 800 }
                            }
                        }

                        Text {
                            text: "⏳ Тестирование..."
                            color: ocrCalibDialog.accentColor
                            font.pointSize: 12
                            font.bold: true
                            Layout.alignment: Qt.AlignHCenter
                        }
                    }
                }

                Rectangle {
                    Layout.fillWidth: true
                    height: 60
                    color: "#99252525"
                    radius: 8
                    border.color: "#50ffffff"
                    border.width: 2

                    Text {
                        anchors.centerIn: parent
                        text: "Распознаём область и проверяем результат..."
                        color: "#c2c2c2"
                        font.pointSize: 10
                        horizontalAlignment: Text.AlignHCenter
                        verticalAlignment: Text.AlignVCenter
                    }
                }

                Item { Layout.fillHeight: true }
            }

            // === test_mob_result ===
            ColumnLayout {
                Layout.fillWidth: true
                Layout.fillHeight: true
                visible: calibrationState === "test_mob_result"
                spacing: 12

                Rectangle {
                    Layout.alignment: Qt.AlignHCenter
                    width: 240
                    height: 50
                    color: mobTestResult && mobTestResult.success ? "#1a3a1a" : "#3a2a1a"
                    radius: 10
                    border.color: mobTestResult && mobTestResult.success ? "#4CAF50" : "#FF9800"
                    border.width: 2

                    Text {
                        anchors.centerIn: parent
                        text: mobTestResult && mobTestResult.success ? "✅ Распознано!" : "⚠ Не распознано"
                        color: mobTestResult && mobTestResult.success ? "#4CAF50" : "#FF9800"
                        font.pointSize: 14
                        font.bold: true
                        horizontalAlignment: Text.AlignHCenter
                        verticalAlignment: Text.AlignVCenter
                    }
                }

                // Превью
                Rectangle {
                    Layout.fillWidth: true
                    Layout.preferredHeight: 160
                    color: "#99252525"
                    radius: 8
                    border.color: "#50ffffff"
                    border.width: 2

                    ColumnLayout {
                        anchors.fill: parent
                        anchors.margins: 12
                        spacing: 8

                        Text {
                            text: "Захваченная область (превью):"
                            color: "#b0b0b0"
                            font.pointSize: 9
                            Layout.alignment: Qt.AlignHCenter
                        }

                        Rectangle {
                            Layout.alignment: Qt.AlignHCenter
                            Layout.fillWidth: true
                            Layout.preferredHeight: 80
                            color: "#1a1a2e"
                            radius: 6
                            border.color: "#50ffffff"
                            border.width: 1

                            Image {
                                source: mobPreviewImage
                                width: Math.min(parent.width - 10, 450)
                                height: Math.min(parent.height - 10, 70)
                                fillMode: Image.PreserveAspectFit
                                anchors.centerIn: parent
                                visible: mobPreviewImage !== ""
                            }

                            Text {
                                text: "Нет превью"
                                color: "#555555"
                                font.pointSize: 10
                                anchors.centerIn: parent
                                visible: mobPreviewImage === ""
                                horizontalAlignment: Text.AlignHCenter
                                verticalAlignment: Text.AlignVCenter
                            }
                        }

                        Text {
                            text: {
                                if (!mobTestResult) return "Нет данных"
                                if (mobTestResult.distance) return "Расстояние: " + mobTestResult.distance + " м"
                                return "Число не распознано — попробуйте другую область"
                            }
                            color: mobTestResult && mobTestResult.distance ? "#4CAF50" : "#FF5252"
                            font.pointSize: 16
                            font.bold: true
                            Layout.alignment: Qt.AlignHCenter
                        }
                    }
                }

                // Подсказка
                Rectangle {
                    Layout.fillWidth: true
                    Layout.preferredHeight: hintMobLayout.implicitHeight + 24
                    color: "#99252525"
                    radius: 8
                    border.color: "#50ffffff"
                    border.width: 2

                    ColumnLayout {
                        id: hintMobLayout
                        anchors.fill: parent
                        anchors.margins: 12
                        spacing: 6

                        Text {
                            text: "📌 Что делать:"
                            color: "#FFD54F"
                            font.pointSize: 10
                            font.bold: true
                        }

                        Text {
                            text: "Если число верное — нажмите «Далее» для настройки области игрока.\nЕсли число неверное или не распознано — нажмите «Переделать» и выделите другую область."
                            color: "#c2c2c2"
                            font.pointSize: 9
                            wrapMode: Text.WordWrap
                            Layout.fillWidth: true
                        }
                    }
                }

                Item { Layout.fillHeight: true }

                RowLayout {
                    Layout.alignment: Qt.AlignHCenter
                    spacing: 10

                    BaseButton {
                        text: "⟳ Переделать"
                        implicitWidth: 130
                        implicitHeight: 40
                        iconSize: 0
                        textSize: 10
                        accentColor: "#FF9800"
                        onClicked: {
                            ocrCalibDialog.calibrationState = "select_mob"
                            mobTestResult = null
                            backend.selectOCRArea("mob")
                        }
                    }

                    BaseButton {
                        text: "Далее →"
                        implicitWidth: 120
                        implicitHeight: 40
                        iconSize: 0
                        textSize: 11
                        accentColor: "#4CAF50"
                        onClicked: {
                            ocrCalibDialog.calibrationState = "select_player"
                            backend.selectOCRArea("player")
                        }
                    }
                }
            }

            // === select_player ===
            ColumnLayout {
                Layout.fillWidth: true
                Layout.fillHeight: true
                visible: calibrationState === "select_player"
                spacing: 14

                Rectangle {
                    Layout.alignment: Qt.AlignHCenter
                    width: 260
                    height: 80
                    color: "#99252525"
                    radius: 10
                    border.color: "#4FC3F7"
                    border.width: 2

                    ColumnLayout {
                        anchors.centerIn: parent
                        spacing: 6

                        Text {
                            text: "👤 Шаг 2: Область игрока"
                            color: "#4FC3F7"
                            font.pointSize: 13
                            font.bold: true
                            Layout.alignment: Qt.AlignHCenter
                        }

                        Text {
                            text: "Теперь выберите область дистанции от игрока"
                            color: "#c2c2c2"
                            font.pointSize: 9
                            Layout.alignment: Qt.AlignHCenter
                        }
                    }
                }

                Rectangle {
                    Layout.fillWidth: true
                    Layout.preferredHeight: playerHintLayout.implicitHeight + 20
                    color: "#99252525"
                    radius: 8
                    border.color: "#50ffffff"
                    border.width: 2

                    ColumnLayout {
                        id: playerHintLayout
                        anchors.fill: parent
                        anchors.margins: 12
                        spacing: 6

                        Text {
                            text: "📌 Где находится область игрока:"
                            color: "#4FC3F7"
                            font.pointSize: 10
                            font.bold: true
                        }

                        Text {
                            text: "• Обычно расположена НИЖЕ области моба\n• Показывает дистанцию ОТ ВАС до цели\n• Выглядит так же — число с буквой «м»\n• В интерфейсе игры это нижний таргет"
                            color: "#c2c2c2"
                            font.pointSize: 9
                            wrapMode: Text.WordWrap
                            Layout.fillWidth: true
                        }

                        Text {
                            text: "💡 Если в игре нет отдельной области игрока — пропустите этот шаг и нажмите «Далее»"
                            color: ocrCalibDialog.accentColor
                            font.pointSize: 9
                            font.italic: true
                            wrapMode: Text.WordWrap
                            Layout.fillWidth: true
                        }
                    }
                }

                Item { Layout.fillHeight: true }

                RowLayout {
                    Layout.alignment: Qt.AlignHCenter
                    spacing: 10

                    BaseButton {
                        text: "⟳ Выбрать снова"
                        implicitWidth: 150
                        implicitHeight: 40
                        iconSize: 0
                        textSize: 10
                        onClicked: backend.selectOCRArea("player")
                    }

                    BaseButton {
                        text: "Далее →"
                        implicitWidth: 120
                        implicitHeight: 40
                        iconSize: 0
                        textSize: 11
                        accentColor: "#4CAF50"
                        onClicked: {
                            ocrCalibDialog.calibrationState = "test_player"
                            backend.testOCRArea("player")
                        }
                    }

                    BaseButton {
                        text: "✕ Отмена"
                        implicitWidth: 100
                        implicitHeight: 40
                        iconSize: 0
                        textSize: 10
                        onClicked: {
                            ocrCalibDialog.calibrationState = "ready"
                            ocrCalibDialog.calibrationCancelled()
                            ocrCalibDialog.close()
                        }
                    }
                }

                Item { Layout.fillHeight: true }
            }

            // === test_player ===
            ColumnLayout {
                Layout.fillWidth: true
                Layout.fillHeight: true
                visible: calibrationState === "test_player"
                spacing: 15

                Rectangle {
                    Layout.alignment: Qt.AlignHCenter
                    width: 220
                    height: 100
                    color: "#99252525"
                    radius: 10
                    border.color: ocrCalibDialog.accentColor
                    border.width: 2

                    ColumnLayout {
                        anchors.centerIn: parent
                        spacing: 10

                        Rectangle {
                            Layout.alignment: Qt.AlignHCenter
                            width: 36; height: 36; radius: 18
                            color: ocrCalibDialog.accentColor
                            opacity: 0.3

                            SequentialAnimation on opacity {
                                running: calibrationState === "test_player"
                                loops: Animation.Infinite
                                NumberAnimation { from: 0.2; to: 0.8; duration: 800 }
                                NumberAnimation { from: 0.8; to: 0.2; duration: 800 }
                            }
                        }

                        Text {
                            text: "⏳ Тестирование..."
                            color: ocrCalibDialog.accentColor
                            font.pointSize: 12
                            font.bold: true
                            Layout.alignment: Qt.AlignHCenter
                        }
                    }
                }

                Rectangle {
                    Layout.fillWidth: true
                    height: 60
                    color: "#99252525"
                    radius: 8
                    border.color: "#50ffffff"
                    border.width: 2

                    Text {
                        anchors.centerIn: parent
                        text: "Распознаём область игрока..."
                        color: "#c2c2c2"
                        font.pointSize: 10
                        horizontalAlignment: Text.AlignHCenter
                        verticalAlignment: Text.AlignVCenter
                    }
                }

                Item { Layout.fillHeight: true }
            }

            // === test_player_result ===
            ColumnLayout {
                Layout.fillWidth: true
                Layout.fillHeight: true
                visible: calibrationState === "test_player_result"
                spacing: 12

                Rectangle {
                    Layout.alignment: Qt.AlignHCenter
                    width: 240
                    height: 50
                    color: playerTestResult && playerTestResult.success ? "#1a3a1a" : "#3a2a1a"
                    radius: 10
                    border.color: playerTestResult && playerTestResult.success ? "#4CAF50" : "#FF9800"
                    border.width: 2

                    Text {
                        anchors.centerIn: parent
                        text: playerTestResult && playerTestResult.success ? "✅ Распознано!" : "⚠ Не распознано"
                        color: playerTestResult && playerTestResult.success ? "#4CAF50" : "#FF9800"
                        font.pointSize: 14
                        font.bold: true
                        horizontalAlignment: Text.AlignHCenter
                        verticalAlignment: Text.AlignVCenter
                    }
                }

                // Превью
                Rectangle {
                    Layout.fillWidth: true
                    Layout.preferredHeight: 160
                    color: "#99252525"
                    radius: 8
                    border.color: "#50ffffff"
                    border.width: 2

                    ColumnLayout {
                        anchors.fill: parent
                        anchors.margins: 12
                        spacing: 8

                        Text {
                            text: "Захваченная область (превью):"
                            color: "#b0b0b0"
                            font.pointSize: 9
                            Layout.alignment: Qt.AlignHCenter
                        }

                        Rectangle {
                            Layout.alignment: Qt.AlignHCenter
                            Layout.fillWidth: true
                            Layout.preferredHeight: 80
                            color: "#1a1a2e"
                            radius: 6
                            border.color: "#50ffffff"
                            border.width: 1

                            Image {
                                source: playerPreviewImage
                                width: Math.min(parent.width - 10, 450)
                                height: Math.min(parent.height - 10, 70)
                                fillMode: Image.PreserveAspectFit
                                anchors.centerIn: parent
                                visible: playerPreviewImage !== ""
                            }

                            Text {
                                text: "Нет превью"
                                color: "#555555"
                                font.pointSize: 10
                                anchors.centerIn: parent
                                visible: playerPreviewImage === ""
                                horizontalAlignment: Text.AlignHCenter
                                verticalAlignment: Text.AlignVCenter
                            }
                        }

                        Text {
                            text: {
                                if (!playerTestResult) return "Нет данных"
                                if (playerTestResult.distance) return "Расстояние: " + playerTestResult.distance + " м"
                                return "Число не распознано — попробуйте другую область"
                            }
                            color: playerTestResult && playerTestResult.distance ? "#4CAF50" : "#FF5252"
                            font.pointSize: 16
                            font.bold: true
                            Layout.alignment: Qt.AlignHCenter
                        }
                    }
                }

                Rectangle {
                    Layout.fillWidth: true
                    Layout.preferredHeight: hintPlayerLayout.implicitHeight + 24
                    color: "#99252525"
                    radius: 8
                    border.color: "#50ffffff"
                    border.width: 2

                    ColumnLayout {
                        id: hintPlayerLayout
                        anchors.fill: parent
                        anchors.margins: 12
                        spacing: 6

                        Text {
                            text: "📌 Обе области настроены!"
                            color: "#4CAF50"
                            font.pointSize: 10
                            font.bold: true
                        }

                        Text {
                            text: "Области моба и игрока сохранены. Нажмите «Готово» для завершения калибровки.\nЕсли результат не верный — нажмите «Переделать»."
                            color: "#c2c2c2"
                            font.pointSize: 9
                            wrapMode: Text.WordWrap
                            Layout.fillWidth: true
                        }
                    }
                }

                Item { Layout.fillHeight: true }

                RowLayout {
                    Layout.alignment: Qt.AlignHCenter
                    spacing: 10

                    BaseButton {
                        text: "⟳ Переделать"
                        implicitWidth: 130
                        implicitHeight: 40
                        iconSize: 0
                        textSize: 10
                        accentColor: "#FF9800"
                        onClicked: {
                            ocrCalibDialog.calibrationState = "select_player"
                            playerTestResult = null
                            backend.selectOCRArea("player")
                        }
                    }

                    BaseButton {
                        text: "✓ Готово"
                        implicitWidth: 120
                        implicitHeight: 40
                        iconSize: 0
                        textSize: 11
                        accentColor: "#4CAF50"
                        onClicked: {
                            ocrCalibDialog.calibrationState = "done"
                            ocrCalibDialog.calibrationCompleted()
                            ocrCalibDialog.close()
                        }
                    }
                }
            }

            // === done ===
            ColumnLayout {
                Layout.fillWidth: true
                Layout.fillHeight: true
                visible: calibrationState === "done"
                spacing: 15

                Rectangle {
                    Layout.alignment: Qt.AlignHCenter
                    width: 260
                    height: 130
                    color: "#1a3a1a"
                    radius: 12
                    border.color: "#4CAF50"
                    border.width: 2

                    ColumnLayout {
                        anchors.centerIn: parent
                        spacing: 10

                        Rectangle {
                            Layout.alignment: Qt.AlignHCenter
                            width: 50; height: 50; radius: 25
                            color: "#4CAF50"
                            opacity: 0.3

                            Text {
                                anchors.centerIn: parent
                                text: "✓"
                                color: "#4CAF50"
                                font.pointSize: 28
                                font.bold: true
                                horizontalAlignment: Text.AlignHCenter
                                verticalAlignment: Text.AlignVCenter
                            }
                        }

                        Text {
                            text: "✅ Калибровка завершена!"
                            color: "#4CAF50"
                            font.pointSize: 14
                            font.bold: true
                            Layout.alignment: Qt.AlignHCenter
                        }
                    }
                }

                // Итог
                Rectangle {
                    Layout.fillWidth: true
                    Layout.preferredHeight: resultLayout.implicitHeight + 20
                    color: "#99252525"
                    radius: 8
                    border.color: "#50ffffff"
                    border.width: 2

                    ColumnLayout {
                        id: resultLayout
                        anchors.fill: parent
                        anchors.margins: 12
                        spacing: 6

                        Text {
                            text: "📊 Итог калибровки:"
                            color: ocrCalibDialog.accentColor
                            font.pointSize: 10
                            font.bold: true
                        }

                        Text {
                            text: {
                                var mobOk = mobTestResult && mobTestResult.success ? "✅" : "⚠"
                                var mobDist = mobTestResult && mobTestResult.distance ? mobTestResult.distance + " м" : "не распознано"
                                var playerOk = playerTestResult && playerTestResult.success ? "✅" : "⚠"
                                var playerDist = playerTestResult && playerTestResult.distance ? playerTestResult.distance + " м" : "не распознано"
                                return "Моб: " + mobOk + " (" + mobDist + ")\n" +
                                       "Игрок: " + playerOk + " (" + playerDist + ")"
                            }
                            color: "#c2c2c2"
                            font.pointSize: 10
                            wrapMode: Text.WordWrap
                            Layout.fillWidth: true
                        }

                        Text {
                            text: "Области сохранены в настройках. Нажмите кнопку СТАРТ для запуска OCR."
                            color: "#808080"
                            font.pointSize: 9
                            wrapMode: Text.WordWrap
                            Layout.fillWidth: true
                        }
                    }
                }

                Item { Layout.fillHeight: true }

                BaseButton {
                    Layout.alignment: Qt.AlignHCenter
                    text: "✓ Закрыть"
                    implicitWidth: 140
                    implicitHeight: 42
                    iconSize: 0
                    textSize: 11
                    accentColor: "#4CAF50"
                    onClicked: {
                        ocrCalibDialog.calibrationState = "ready"
                        ocrCalibDialog.close()
                    }
                }

                Item { Layout.fillHeight: true }
            }
        }
    }

    // Сигналы
    signal calibrationCompleted()
    signal calibrationCancelled()

    onClosing: {
        calibrationState = "ready"
        calibrationCancelled()
    }

    Shortcut {
        sequence: "Esc"
        onActivated: {
            if (calibrationState !== "ready") {
                calibrationState = "ready"
                calibrationCancelled()
            }
            close()
        }
    }
}
