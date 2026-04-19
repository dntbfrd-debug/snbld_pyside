import QtQuick 2.15
import QtQuick.Controls.Basic 2.15
import QtQuick.Layouts 1.15
import QtQml 2.15

Item {
    id: settingsNetworkPage

    // Безопасный доступ к настройкам
    property var safeSettings: (backend && backend.settings) ? backend.settings : ({})

    // Обновление при изменении настроек
    Connections {
        target: backend
        function onSettingsChanged() {
            settingsNetworkPage.safeSettings = (backend && backend.settings) ? backend.settings : ({})
        }
    }

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 20
        anchors.bottomMargin: 70
        spacing: 15

        RowLayout {
            Layout.fillWidth: true
            BaseButton {
                text: "← Назад"
                implicitWidth: 80
                implicitHeight: 30
                iconSize: 0
                textSize: 10
                onClicked: settingsNetworkPage.StackView.view.pop()
            }
            Text {
                text: "◈ Сеть"
                font.pointSize: 18
                font.bold: true
                color: "#c2c2c2"
                Layout.alignment: Qt.AlignHCenter
            }
            Item { Layout.fillWidth: true }
        }

        ColumnLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            Layout.alignment: Qt.AlignHCenter | Qt.AlignTop
            spacing: 15

            GroupBox {
                title: "Мониторинг"
                Layout.fillWidth: true
                Layout.alignment: Qt.AlignHCenter
                background: Rectangle { color: "#99252525"; radius: 8; border.color: "#50ffffff"; border.width: 1 }
                contentItem: ColumnLayout {
                    spacing: 12

                    CheckBox {
                        id: pingAutoCheck
                        checked: safeSettings.ping_auto || false
                        font.pointSize: 11
                        property string accentColor: safeSettings.accent_color || "#7793a1"
                        indicator: Rectangle {
                            implicitWidth: 18; implicitHeight: 18; radius: 4
                            color: pingAutoCheck.checked ? pingAutoCheck.accentColor : "#3a3a3a"
                            border.color: pingAutoCheck.checked ? "#60ffffff" : "#505050"
                            border.width: 1
                            Rectangle {
                                width: 10; height: 10; radius: 4; color: "#99252525"
                                anchors.centerIn: parent; visible: pingAutoCheck.checked
                            }
                        }
                        contentItem: RowLayout {
                            spacing: 8
                            Text {
                                text: pingAutoCheck.checked ? "✓ ВКЛ" : "○ ВЫКЛ"
                                color: pingAutoCheck.checked ? pingAutoCheck.accentColor : "#606060"
                                font.pointSize: 9
                                font.bold: pingAutoCheck.checked
                                verticalAlignment: Text.AlignVCenter
                                leftPadding: 24
                            }
                        }
                        onCheckStateChanged: {
                            backend.set_setting("ping_auto", checked)
                        }
                    }

                    // Сетка для выравнивания полей ввода
                    GridLayout {
                        Layout.fillWidth: true
                        columns: 2
                        columnSpacing: 15
                        rowSpacing: 12
                        
                        Label {
                            text: "Средний пинг (мс):"
                            color: "#c2c2c2"
                            font.pointSize: 10
                            font.bold: true
                            Layout.fillWidth: true
                        }
                        TextField {
                            Layout.fillWidth: true
                            Layout.minimumWidth: 150
                            text: safeSettings.average_ping || 0
                            font.pointSize: 11
                            horizontalAlignment: Text.AlignHCenter
                            background: Rectangle { radius: 6; color: "#40ffffff" }
                            onEditingFinished: backend.set_setting("average_ping", text)
                        }

                        Label {
                            text: "Интервал проверки (сек):"
                            color: "#c2c2c2"
                            font.pointSize: 10
                            font.bold: true
                            Layout.fillWidth: true
                        }
                        TextField {
                            Layout.fillWidth: true
                            Layout.minimumWidth: 150
                            text: safeSettings.ping_check_interval || 5
                            font.pointSize: 11
                            horizontalAlignment: Text.AlignHCenter
                            validator: IntValidator { bottom: 1; top: 60 }
                            background: Rectangle { radius: 6; color: "#40ffffff" }
                            onEditingFinished: backend.set_setting("ping_check_interval", parseInt(text) || 5)
                        }

                        Label {
                            text: "Процесс игры:"
                            color: "#c2c2c2"
                            font.pointSize: 10
                            font.bold: true
                            Layout.fillWidth: true
                        }
                        TextField {
                            Layout.fillWidth: true
                            Layout.minimumWidth: 150
                            text: safeSettings.process_name || ""
                            font.pointSize: 11
                            horizontalAlignment: Text.AlignHCenter
                            background: Rectangle { radius: 6; color: "#40ffffff" }
                            onEditingFinished: backend.set_setting("process_name", text)
                        }

                        Label {
                            text: "IP сервера:"
                            color: "#c2c2c2"
                            font.pointSize: 10
                            font.bold: true
                            Layout.fillWidth: true
                        }
                        TextField {
                            Layout.fillWidth: true
                            Layout.minimumWidth: 150
                            text: safeSettings.server_ip || ""
                            font.pointSize: 11
                            horizontalAlignment: Text.AlignHCenter
                            background: Rectangle { radius: 6; color: "#40ffffff" }
                            onEditingFinished: backend.set_setting("server_ip", text)
                        }
                    }

                    RowLayout {
                        Layout.fillWidth: true
                        spacing: 10

                        Label {
                            text: "Текущий пинг:"
                            color: "#c2c2c2"
                            font.pointSize: 10
                            font.bold: true
                        }
                        Text {
                            id: pingValueText
                            text: backend.ping + " мс"
                            color: backend.ping < 50 ? "#4CAF50" : (backend.ping < 100 ? "#FFC107" : "#F44336")
                            font.pointSize: 14
                            font.bold: true
                        }

                        Item { Layout.fillWidth: true }

                        BaseButton {
                            text: pingAutoCheck.checked ? "⟳ Тест" : "⚠ ВКЛ авто"
                            implicitWidth: pingAutoCheck.checked ? 80 : 100
                            implicitHeight: 35
                            iconSize: 0
                            textSize: 10
                            enabled: pingAutoCheck.checked
                            onClicked: {
                                if (pingAutoCheck.checked) {
                                    // Запустить тест пинга
                                    backend.testPing()
                                    pingValueText.text = "..."
                                }
                            }
                        }
                    }
                }
            }

            RowLayout {
                Layout.fillWidth: true
                Layout.preferredHeight: 50
                spacing: 10
                Item { Layout.fillWidth: true }
                Text {
                    text: "⚠ Экспериментальная функция"
                    color: backend && safeSettings ? safeSettings.accent_color : "#7793a1"
                    font.pointSize: 10
                    font.bold: true
                    font.italic: true
                    visible: true
                }
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
