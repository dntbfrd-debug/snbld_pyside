import QtQuick 2.15
import QtQuick.Controls.Basic 2.15
import QtQuick.Layouts 1.15
import QtQml 2.15
import "components"

Item {
    id: settingsMovementPage

    // Безопасный доступ к настройкам
    property var safeSettings: (backend && backend.settings) ? backend.settings : ({})

    // Получаем акцентный цвет
    property string accentColor: safeSettings.accent_color || "#7793a1"

    // Обновление при изменении настроек
    Connections {
        target: backend
        function onSettingsChanged() {
            // Перезагружаем safeSettings — Qt автоматически обновит привязки
            settingsMovementPage.safeSettings = (backend && backend.settings) ? backend.settings : ({})
        }
    }

    // Инициализация при загрузке страницы
    Component.onCompleted: {
        // Убеждаемся что только один чекбокс включён при загрузке
        var movementEnabled = safeSettings.movement_delay_enabled || false
        var castbarEnabled = safeSettings.use_castbar_detection || false
        
        // Если оба включены - выключаем оба
        if (movementEnabled && castbarEnabled) {
            backend.set_setting("use_castbar_detection", false)
            castbarEnabled = false
        }
        
        // Устанавливаем начальные состояния
        movementDelayCheck.checked = safeSettings.movement_delay_enabled || false
        castbarDetectionCheck.checked = safeSettings.use_castbar_detection || false
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
                implicitHeight: 30
                iconSize: 0
                textSize: 10
                onClicked: settingsMovementPage.StackView.view.pop()
            }
            Text {
                text: "◑ Движение"
                font.pointSize: 18
                font.bold: true
                color: "#c2c2c2"
                Layout.alignment: Qt.AlignHCenter
            }
            Item { Layout.fillWidth: true }
        }

        // Две плитки рядом по горизонтали
        RowLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            spacing: 15

            // Плитка 1: Методы обнаружения после движения (взаимоисключающие)
            GroupBox {
                title: "◑ Обнаружение после движения"
                Layout.fillWidth: true
                Layout.fillHeight: true
                background: Rectangle { color: "#99252525"; radius: 8; border.color: "#50ffffff"; border.width: 1 }
                contentItem: ColumnLayout {
                    spacing: 12

                    // Опция 1: Фиксированная задержка
                    Rectangle {
                        Layout.fillWidth: true
                        height: 140
                        radius: 8
                        color: "#20ffffff"
                        border.color: movementDelayCheck.checked ? accentColor : "#40ffffff"
                        border.width: movementDelayCheck.checked ? 2 : 1

                        ColumnLayout {
                            anchors.fill: parent
                            anchors.margins: 12
                            spacing: 8

                            RowLayout {
                                Layout.fillWidth: true
                                spacing: 10

                                CheckBox {
                                    id: movementDelayCheck
                                    checked: safeSettings.movement_delay_enabled || false
                                    font.pointSize: 11
                                    property string accentColor: settingsMovementPage.accentColor
                                    indicator: Rectangle {
                                        implicitWidth: 20; implicitHeight: 20; radius: 4
                                        color: movementDelayCheck.checked ? movementDelayCheck.accentColor : "#3a3a3a"
                                        border.color: movementDelayCheck.checked ? "#60ffffff" : "#505050"
                                        border.width: 1
                                        Rectangle {
                                            width: 12; height: 12; radius: 4; color: "#99252525"
                                            anchors.centerIn: parent; visible: movementDelayCheck.checked
                                        }
                                    }
                                    contentItem: RowLayout {
                                        spacing: 8
                                        Text {
                                            text: "⏱ Задержка"
                                            color: movementDelayCheck.checked ? movementDelayCheck.accentColor : "#c0c0c0"
                                            font.pointSize: 12
                                            font.bold: movementDelayCheck.checked
                                            verticalAlignment: Text.AlignVCenter
                                            leftPadding: 24
                                        }
                                    }
                                    onCheckStateChanged: {
                                        if (checked) {
                                            // Включаем задержку, выключаем детекцию каста
                                            castbarDetectionCheck.checked = false
                                            backend.set_setting("movement_delay_enabled", true)
                                            backend.set_setting("use_castbar_detection", false)
                                        }
                                    }
                                }

                                Item { Layout.fillWidth: true }
                            }

                            RowLayout {
                                Layout.fillWidth: true
                                visible: movementDelayCheck.checked
                                opacity: movementDelayCheck.checked ? 1.0 : 0.3

                                Label {
                                    text: "Задержка (мс):"
                                    color: "#c2c2c2"
                                    font.pointSize: 10
                                    font.bold: true
                                }
                                TextField {
                                    Layout.fillWidth: true
                                    text: safeSettings.movement_delay_ms || 300
                                    font.pointSize: 11
                                    horizontalAlignment: Text.AlignHCenter
                                    enabled: movementDelayCheck.checked
                                    validator: IntValidator { bottom: 0; top: 5000 }
                                    background: Rectangle { radius: 6; color: "#40ffffff" }
                                    onEditingFinished: backend.set_setting("movement_delay_ms", text)
                                }
                            }

                            Text {
                                text: "⚠ Фиксированная задержка после нажатия WASD"
                                color: "#c0c0c0"
                                font.pointSize: 10
                                font.italic: true
                                wrapMode: Text.WordWrap
                                Layout.fillWidth: true
                            }
                        }
                    }

                    // Разделитель
                    Rectangle {
                        Layout.fillWidth: true
                        height: 1
                        color: "#40ffffff"
                    }

                    // Опция 2: Детекция каста
                    Rectangle {
                        Layout.fillWidth: true
                        height: 120
                        radius: 8
                        color: "#20ffffff"
                        border.color: castbarDetectionCheck.checked ? accentColor : "#40ffffff"
                        border.width: castbarDetectionCheck.checked ? 2 : 1

                        ColumnLayout {
                            anchors.fill: parent
                            anchors.margins: 12
                            spacing: 8

                            RowLayout {
                                Layout.fillWidth: true
                                spacing: 10

                                CheckBox {
                                    id: castbarDetectionCheck
                                    checked: safeSettings.use_castbar_detection || false
                                    font.pointSize: 11
                                    property string accentColor: settingsMovementPage.accentColor
                                    indicator: Rectangle {
                                        implicitWidth: 20; implicitHeight: 20; radius: 4
                                        color: castbarDetectionCheck.checked ? castbarDetectionCheck.accentColor : "#3a3a3a"
                                        border.color: castbarDetectionCheck.checked ? "#60ffffff" : "#505050"
                                        border.width: 1
                                        Rectangle {
                                            width: 12; height: 12; radius: 4; color: "#99252525"
                                            anchors.centerIn: parent; visible: castbarDetectionCheck.checked
                                        }
                                    }
                                    contentItem: RowLayout {
                                        spacing: 8
                                        Text {
                                            text: "▣ Детекция каста"
                                            color: castbarDetectionCheck.checked ? castbarDetectionCheck.accentColor : "#c0c0c0"
                                            font.pointSize: 12
                                            font.bold: castbarDetectionCheck.checked
                                            verticalAlignment: Text.AlignVCenter
                                            leftPadding: 24
                                        }
                                    }
                                    onCheckStateChanged: {
                                        if (checked) {
                                            // Включаем детекцию каста, выключаем задержку
                                            movementDelayCheck.checked = false
                                            backend.set_setting("use_castbar_detection", true)
                                            backend.set_setting("movement_delay_enabled", false)
                                        }
                                    }
                                }

                                Item { Layout.fillWidth: true }
                            }

                            Text {
                                text: castbarDetectionCheck.checked ? 
                                      "✓ Детекция кастбара вместо задержки (надёжнее)" :
                                      "⚠ Фиксированная задержка (менее надёжно)"
                                color: castbarDetectionCheck.checked ? "#4CAF50" : "#FFA500"
                                font.pointSize: 9
                                font.bold: true
                                wrapMode: Text.WordWrap
                                Layout.fillWidth: true
                            }
                        }
                    }

                    // Подсказка о взаимном исключении
                    Text {
                        text: "• Можно выбрать только один метод обнаружения"
                        color: "#a0a0a0"
                        font.pointSize: 10
                        font.italic: true
                        Layout.fillWidth: true
                        horizontalAlignment: Text.AlignHCenter
                    }
                }
            }

            // Плитка 2: Проверка дистанции OCR
            GroupBox {
                title: "▫ Проверка дистанции (OCR)"
                Layout.fillWidth: true
                Layout.fillHeight: true
                background: Rectangle { color: "#99252525"; radius: 8; border.color: "#50ffffff"; border.width: 1 }
                contentItem: ColumnLayout {
                    spacing: 12

                    CheckBox {
                        id: checkDistanceCheck
                        checked: safeSettings.check_distance
                        font.pointSize: 11
                        property string accentColor: settingsMovementPage.accentColor
                        indicator: Rectangle {
                            implicitWidth: 20; implicitHeight: 20; radius: 4
                            color: checkDistanceCheck.checked ? checkDistanceCheck.accentColor : "#3a3a3a"
                            border.color: checkDistanceCheck.checked ? "#60ffffff" : "#505050"
                            border.width: 1
                            Rectangle {
                                width: 12; height: 12; radius: 4; color: "#99252525"
                                anchors.centerIn: parent; visible: checkDistanceCheck.checked
                            }
                        }
                        contentItem: RowLayout {
                            spacing: 8
                            Text {
                                text: checkDistanceCheck.checked ? "✓ ВКЛ" : "○ ВЫКЛ"
                                color: checkDistanceCheck.checked ? checkDistanceCheck.accentColor : "#606060"
                                font.pointSize: 9
                                font.bold: checkDistanceCheck.checked
                                verticalAlignment: Text.AlignVCenter
                                leftPadding: 24
                            }
                        }
                        onCheckStateChanged: {
                            backend.set_setting("check_distance", checked)
                        }
                    }

                    // Информационный блок
                    Rectangle {
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        radius: 8
                        color: "#15ffffff"
                        border.color: "#30ffffff"
                        border.width: 1

                        ColumnLayout {
                            anchors.fill: parent
                            anchors.margins: 12
                            spacing: 10

                            Text {
                                text: "▣ Автодобег"
                                color: accentColor
                                font.pointSize: 12
                                font.bold: true
                            }

                            Text {
                                text: "Включение функции позволяет:\n" +
                                      "• Программа измеряет дистанцию до цели\n" +
                                      "• Если дистанция больше дальности скилла — подбегает\n" +
                                      "• Только после этого запускает макрос с ресвапом"
                                color: "#d0d0d0"
                                font.pointSize: 10
                                wrapMode: Text.WordWrap
                                Layout.fillWidth: true
                            }

                            Rectangle {
                                Layout.fillWidth: true
                                height: 1
                                color: "#30ffffff"
                            }

                            Text {
                                text: "Пример работы:"
                                color: "#b0b0b0"
                                font.pointSize: 10
                                font.bold: true
                            }

                            Text {
                                text: "Скилл с дальностью 3м → бот подбежит на 2м → применит скилл"
                                color: "#c5c5c5"
                                font.pointSize: 10
                                wrapMode: Text.WordWrap
                                Layout.fillWidth: true
                            }
                        }
                    }
                }
            }
        }
    }
}
