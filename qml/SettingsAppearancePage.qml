import QtQuick 2.15
import QtQuick.Controls.Basic 2.15
import QtQuick.Layouts 1.15

Item {
    id: settingsAppearancePage

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 20
        spacing: 15

        // Заголовок
        RowLayout {
            Layout.fillWidth: true
            BaseButton {
                text: "← Назад"
                implicitWidth: 80
                implicitHeight: 30
                iconSize: 0
                textSize: 10
                onClicked: {
                    settingsAppearancePage.StackView.view.pop()
                }
            }
            Item { Layout.fillWidth: true }
            Text {
                text: "▫ Внешний вид"
                font.pointSize: 20
                font.bold: true
                color: "#c2c2c2"
            }
            Item { Layout.fillWidth: true }
        }

        RowLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            spacing: 20

            // Левая колонка - Цветовая палитра
            ColumnLayout {
                Layout.fillWidth: true
                Layout.fillHeight: true
                spacing: 15

                // Заголовок
                Label {
                    text: "◈ Цветовая палитра"
                    color: backend && backend.settings ? backend.settings.accent_color : "#7793a1"
                    font.pointSize: 14
                    font.bold: true
                }

                // Цветовая сетка
                Rectangle {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    color: "#99252525"
                    radius: 8
                    border.width: 1
                    border.color: "#50ffffff"

                    GridLayout {
                        anchors.fill: parent
                        anchors.margins: 10
                        columns: 8
                        rowSpacing: 8
                        columnSpacing: 8

                        Repeater {
                            model: [
                                "#000000", "#2d3436", "#636e72", "#b2bec3",
                                "#e74c3c", "#e67e22", "#f39c12", "#f1c40f",
                                "#2ecc71", "#1abc9c", "#16a085", "#3498db",
                                "#2980b9", "#34495e", "#9b59b6", "#8e44ad",
                                "#e91e63", "#e84393", "#d63031", "#d35400",
                                "#27ae60", "#00b894", "#0984e3", "#6c5ce7",
                                "#fd79a8", "#dfe6e9"
                            ]

                            delegate: Rectangle {
                                width: 40
                                height: 40
                                color: modelData
                                radius: 6
                                border.width: colorPicker.currentColor === modelData ? 3 : 1
                                border.color: "#ffffff"

                                MouseArea {
                                    anchors.fill: parent
                                    cursorShape: Qt.PointingHandCursor
                                    onClicked: {
                                        colorPicker.currentColor = modelData
                                        colorPreview.color = modelData
                                    }
                                }
                            }
                        }
                    }
                }
            }

            // Правая колонка - Предпросмотр и применение
            ColumnLayout {
                Layout.preferredWidth: 250
                Layout.fillHeight: true
                spacing: 15

                // Заголовок
                Label {
                    text: "◈ Предпросмотр"
                    color: backend && backend.settings ? backend.settings.accent_color : "#7793a1"
                    font.pointSize: 14
                    font.bold: true
                }

                // Окно предпросмотра
                Rectangle {
                    Layout.fillWidth: true
                    Layout.preferredHeight: 240
                    color: "#99252525"
                    radius: 8
                    border.width: 1
                    border.color: "#50ffffff"

                    ColumnLayout {
                        anchors.fill: parent
                        anchors.margins: 15
                        spacing: 15

                        // Текущий цвет
                        Rectangle {
                            id: colorPreview
                            Layout.fillWidth: true
                            Layout.preferredHeight: 80
                            color: backend.settings.accent_color || "#7793a1"
                            radius: 6
                            border.width: 2
                            border.color: "#ffffff"

                            Text {
                                anchors.centerIn: parent
                                text: colorPreview.color
                                color: "#ffffff"
                                font.pointSize: 14
                                font.bold: true
                                style: Text.Outline
                                styleColor: "#000000"
                            }
                        }

                        // Значение цвета
                        TextField {
                            id: colorInput
                            Layout.fillWidth: true
                            text: colorPreview.color
                            placeholderText: "#7793a1"
                            background: Rectangle {
                                color: "#1a1a1a"
                                radius: 4
                                border.color: "#40ffffff"
                            }
                            color: "#c2c2c2"
                            font.family: "Consolas"
                            font.pointSize: 11
                            horizontalAlignment: TextInput.AlignHCenter

                            onAccepted: {
                                if (/^#[0-9A-Fa-f]{6}$/.test(text)) {
                                    colorPreview.color = text
                                }
                            }
                        }

                        // Кнопка применить
                        BaseButton {
                            text: "✓ Применить"
                            Layout.fillWidth: true
                            implicitHeight: 45
                            iconSize: 16
                            textSize: 12
                            onClicked: {
                                if (/^#[0-9A-Fa-f]{6}$/.test(colorPreview.color)) {
                                    backend.set_setting("accent_color", colorPreview.color)
                                    backend.notification("Цвет применён", "success")
                                } else {
                                    backend.notification("Неверный формат цвета", "warning")
                                }
                            }
                        }
                    }
                }

                // Информация
                Rectangle {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    color: "#99252525"
                    radius: 8
                    border.width: 1
                    border.color: "#50ffffff"

                    ColumnLayout {
                        anchors.fill: parent
                        anchors.leftMargin: 12
                        anchors.rightMargin: 12
                        anchors.bottomMargin: 12
                        anchors.topMargin: 8
                        spacing: 4

                        Label {
                            text: "◈ Информация:"
                            color: backend && backend.settings ? backend.settings.accent_color : "#7793a1"
                            font.pointSize: 11
                            font.bold: true
                        }

                        Text {
                            text: "Акцентный цвет меняет:\n" +
                                  "• Рамки кнопок и элементов\n" +
                                  "• Цвет иконок в меню\n" +
                                  "• Анимацию перекатывания\n" +
                                  "• Цвет чекбоксов и слайдеров"
                            color: "#a0a0a0"
                            font.pointSize: 9
                            wrapMode: Text.WordWrap
                            Layout.fillWidth: true
                        }
                    }
                }
            }
        }
    }

    // Компонент для хранения текущего выбранного цвета
    QtObject {
        id: colorPicker
        property color currentColor: backend && backend.settings ? (backend.settings.accent_color || "#7793a1") : "#7793a1"
    }

    // Инициализация
    Component.onCompleted: {
        colorPreview.color = backend && backend.settings ? (backend.settings.accent_color || "#7793a1") : "#7793a1"
        colorInput.text = colorPreview.color
    }

    // Обновление при изменении настроек
    Connections {
        target: backend
        function onSettingsChanged() {
            colorPreview.color = backend && backend.settings ? (backend.settings.accent_color || "#7793a1") : "#7793a1"
            colorInput.text = colorPreview.color
        }
    }
}
