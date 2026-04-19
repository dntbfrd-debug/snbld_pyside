import QtQuick 2.15
import QtQuick.Controls.Basic 2.15
import QtQuick.Layouts 1.15

Item {
    id: settingsOCRAreasPage

    // Свойства для статусов калибровки
    property bool mobCalibrated: false
    property bool playerCalibrated: false
    property string mobStatusText: ""
    property string playerStatusText: ""

    // Подключаемся к сигналам backend
    Connections {
        target: backend
        function onOcrAreaSelected(target_type, area) {
            // Обновляем статус калибровки
            if (target_type === "mob") {
                mobCalibrated = true
                mobStatusText = "+ " + area
            } else if (target_type === "player") {
                playerCalibrated = true
                playerStatusText = "+ " + area
            }
            console.log("OCR область выбрана:", target_type, area)
        }
    }

    // Инициализация при загрузке
    Component.onCompleted: {
        // Проверяем есть ли уже сохранённые области
        var mobArea = backend.settings.mob_area
        var playerArea = backend.settings.player_area

        if (mobArea && mobArea !== "1266,32,1303,56" && mobArea !== "") {
            mobCalibrated = true
            mobStatusText = "+ " + (mobArea instanceof Array ? mobArea.join(",") : mobArea)
        }

        if (playerArea && playerArea !== "1271,16,1294,32" && playerArea !== "") {
            playerCalibrated = true
            playerStatusText = "+ " + (playerArea instanceof Array ? playerArea.join(",") : playerArea)
        }

        console.log("SettingsOCRAreasPage: mobCalibrated =", mobCalibrated, "playerCalibrated =", playerCalibrated)
    }

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 20
        anchors.bottomMargin: 70
        spacing: 15

        // Заголовок с кнопкой назад
        RowLayout {
            Layout.fillWidth: true
            BaseButton {
                text: "← Назад"
                implicitWidth: 80
                implicitHeight: 35
                iconSize: 0
                textSize: 11
                onClicked: settingsOCRAreasPage.StackView.view.pop()
            }
            Text {
                text: "▫ Области OCR"
                font.pointSize: 18
                font.bold: true
                color: "#c2c2c2"
                Layout.alignment: Qt.AlignHCenter
            }
            Item { Layout.fillWidth: true }
        }

        // Кнопки управления
        RowLayout {
            Layout.fillWidth: true
            spacing: 10

            BaseButton {
                text: "▣ Калибровка OCR"
                Layout.fillWidth: true
                implicitHeight: 45
                iconSize: 16
                textSize: 12
                accentColor: settingsOCRAreasPage.accentColor
                onClicked: {
                    backend.startOCRCalibration()
                }
            }
        }

        // Две плитки с областями
        RowLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            Layout.minimumHeight: 300
            spacing: 15

            // Плитка 1: Область моба
            Rectangle {
                id: mobTile
                Layout.fillWidth: true
                Layout.fillHeight: true
                color: "#99252525"
                radius: 10
                border.color: "#50ffffff"
                border.width: 2

                property color accentColor: backend && backend.settings ? (backend.settings.accent_color || "#7793a1") : "#7793a1"
                property color statusColor: mobCalibrated ? "#4CAF50" : "#FFC107"

                ColumnLayout {
                    anchors.fill: parent
                    anchors.margins: 20
                    spacing: 12

                    // Заголовок
                    Text {
                        text: "🎯 Область моба"
                        font.pointSize: 14
                        font.bold: true
                        color: "#c2c2c2"
                        Layout.fillWidth: true
                    }

                    // Подсказка
                    Text {
                        text: "Область экрана где отображается дистанция до моба/цели"
                        font.pointSize: 9
                        color: "#b0b0b0"
                        wrapMode: Text.WordWrap
                        Layout.fillWidth: true
                    }

                    Rectangle {
                        Layout.fillWidth: true
                        height: 1
                        color: "#50ffffff"
                    }

                    // Статус калибровки
                    Rectangle {
                        Layout.fillWidth: true
                        Layout.preferredHeight: 35
                        radius: 6
                        color: "#20000000"
                        border.color: mobTile.statusColor
                        border.width: 1

                        Text {
                            anchors.centerIn: parent
                            text: mobCalibrated ? "✅ Откалибровано" : "⚠ Не откалибровано"
                            color: mobTile.statusColor
                            font.pointSize: 10
                            font.bold: true
                        }
                    }

                    // Координаты (только для просмотра)
                    Rectangle {
                        Layout.fillWidth: true
                        Layout.preferredHeight: 40
                        radius: 6
                        color: "#30000000"
                        border.color: "#50ffffff"
                        border.width: 1

                        Text {
                            anchors.centerIn: parent
                            text: {
                                var area = backend && backend.settings ? backend.settings.mob_area : "1266,32,1303,56"
                                if (area instanceof Array) {
                                    return "X: " + area[0] + ", " + area[1] + " | X2: " + area[2] + ", " + area[3]
                                } else if (typeof area === "string") {
                                    return area
                                }
                                return "1266,32,1303,56"
                            }
                            color: "#a0a0a0"
                            font.pointSize: 9
                        }
                    }

                    Item { Layout.fillHeight: true }

                    // Кнопка выбора области
                    BaseButton {
                        text: "◈ Выбрать область"
                        Layout.fillWidth: true
                        implicitHeight: 45
                        iconSize: 14
                        textSize: 12
                        onClicked: {
                            backend.selectOCRArea("mob")
                        }
                    }
                }
            }

            // Плитка 2: Область игрока
            Rectangle {
                id: playerTile
                Layout.fillWidth: true
                Layout.fillHeight: true
                color: "#99252525"
                radius: 10
                border.color: "#50ffffff"
                border.width: 2

                property color accentColor: backend && backend.settings ? (backend.settings.accent_color || "#7793a1") : "#7793a1"
                property color statusColor: playerCalibrated ? "#4CAF50" : "#FFC107"

                ColumnLayout {
                    anchors.fill: parent
                    anchors.margins: 20
                    spacing: 12

                    // Заголовок
                    Text {
                        text: "👤 Область игрока"
                        font.pointSize: 14
                        font.bold: true
                        color: "#c2c2c2"
                        Layout.fillWidth: true
                    }

                    // Подсказка
                    Text {
                        text: "Область экрана где отображается дистанция от игрока"
                        font.pointSize: 9
                        color: "#b0b0b0"
                        wrapMode: Text.WordWrap
                        Layout.fillWidth: true
                    }

                    Rectangle {
                        Layout.fillWidth: true
                        height: 1
                        color: "#50ffffff"
                    }

                    // Статус калибровки
                    Rectangle {
                        Layout.fillWidth: true
                        Layout.preferredHeight: 35
                        radius: 6
                        color: "#20000000"
                        border.color: playerTile.statusColor
                        border.width: 1

                        Text {
                            anchors.centerIn: parent
                            text: playerCalibrated ? "✅ Откалибровано" : "⚠ Не откалибровано"
                            color: playerTile.statusColor
                            font.pointSize: 10
                            font.bold: true
                        }
                    }

                    // Координаты (только для просмотра)
                    Rectangle {
                        Layout.fillWidth: true
                        Layout.preferredHeight: 40
                        radius: 6
                        color: "#30000000"
                        border.color: "#50ffffff"
                        border.width: 1

                        Text {
                            anchors.centerIn: parent
                            text: {
                                var area = backend && backend.settings ? backend.settings.player_area : "1271,16,1294,32"
                                if (area instanceof Array) {
                                    return "X: " + area[0] + ", " + area[1] + " | X2: " + area[2] + ", " + area[3]
                                } else if (typeof area === "string") {
                                    return area
                                }
                                return "1271,16,1294,32"
                            }
                            color: "#a0a0a0"
                            font.pointSize: 9
                        }
                    }

                    Item { Layout.fillHeight: true }

                    // Кнопка выбора области
                    BaseButton {
                        text: "◈ Выбрать область"
                        Layout.fillWidth: true
                        implicitHeight: 45
                        iconSize: 14
                        textSize: 12
                        onClicked: {
                            backend.selectOCRArea("player")
                        }
                    }
                }
            }
        }

        // Кнопка сохранения внизу
        RowLayout {
            Layout.fillWidth: true
            Layout.preferredHeight: 50
            spacing: 0
            Item { Layout.fillWidth: true }
            BaseButton {
                text: "◈ Сохранить"
                implicitWidth: 160
                implicitHeight: 40
                iconSize: 14
                textSize: 11
                onClicked: backend.save_all_settings()
            }
            Item { Layout.fillWidth: true }
        }
    }
}
