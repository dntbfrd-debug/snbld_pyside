import QtQuick 2.15
import QtQuick.Controls.Basic 2.15
import QtQuick.Layouts 1.15

Item {
    id: settingsReswapPage

    // Принудительное обновление привязок при изменении настроек
    property var forceUpdate: backend && backend.settings ? backend.settings : ({})
    Connections {
        target: backend
        function onSettingsChanged() {
            settingsReswapPage.forceUpdate = backend.settings
        }
    }

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 20
        anchors.bottomMargin: 70  // Место для кнопки
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
                onClicked: settingsReswapPage.StackView.view.pop()
            }
            Text {
                text: "⚔ Ресвап"
                font.pointSize: 18
                font.bold: true
                color: "#c2c2c2"
                Layout.alignment: Qt.AlignHCenter
            }
            Item { Layout.fillWidth: true }
        }

        // Содержимое - без прокрутки
        ColumnLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            Layout.alignment: Qt.AlignHCenter | Qt.AlignTop
            spacing: 15

            GroupBox {
                title: "Кнопки смены сетов"
                Layout.fillWidth: true
                Layout.alignment: Qt.AlignHCenter
                background: Rectangle { color: "#99252525"; radius: 8; border.color: "#50ffffff"; border.width: 1 }
                contentItem: ColumnLayout {
                    spacing: 12

                    GridLayout {
                        Layout.fillWidth: true
                        columns: 2
                        columnSpacing: 15
                        rowSpacing: 10

                        Label {
                            text: "Сет пения:"
                            color: "#c2c2c2"
                            font.pointSize: 10
                            font.bold: true
                            Layout.fillWidth: true
                        }
                        TextField {
                            Layout.fillWidth: true
                            Layout.minimumWidth: 150
                            text: backend.settings.swap_key_chant || "e"
                            font.pointSize: 11
                            horizontalAlignment: Text.AlignHCenter
                            background: Rectangle { radius: 6; color: "#40ffffff" }
                            onEditingFinished: backend.set_setting("swap_key_chant", text)
                        }

                        Label {
                            text: "Сет ПА:"
                            color: "#c2c2c2"
                            font.pointSize: 10
                            font.bold: true
                            Layout.fillWidth: true
                        }
                        TextField {
                            Layout.fillWidth: true
                            Layout.minimumWidth: 150
                            text: backend.settings.swap_key_pa || "e"
                            font.pointSize: 11
                            horizontalAlignment: Text.AlignHCenter
                            background: Rectangle { radius: 6; color: "#40ffffff" }
                            onEditingFinished: backend.set_setting("swap_key_pa", text)
                        }

                        Label {
                            text: "Бонус пения (%):"
                            color: "#c2c2c2"
                            font.pointSize: 10
                            font.bold: true
                            Layout.fillWidth: true
                        }
                        TextField {
                            Layout.fillWidth: true
                            Layout.minimumWidth: 150
                            text: backend.settings.base_channeling || 91
                            font.pointSize: 11
                            horizontalAlignment: Text.AlignHCenter
                            validator: IntValidator { bottom: 0; top: 500 }
                            background: Rectangle { radius: 6; color: "#40ffffff" }
                            onEditingFinished: backend.set_setting("base_channeling", text)
                        }
                    }
                }
            }

            // Кнопка сохранения внизу по центру
            RowLayout {
                Layout.fillWidth: true
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
}
