import QtQuick 2.15
import QtQuick.Controls.Basic 2.15
import QtQuick.Layouts 1.15

Item {
    id: settingsWindowPage

    // Безопасный доступ к настройкам
    property var safeSettings: (backend && backend.settings) ? backend.settings : ({})

    // Обновление при изменении настроек
    Connections {
        target: backend
        function onSettingsChanged() {
            settingsWindowPage.safeSettings = (backend && backend.settings) ? backend.settings : ({})
            // Обновляем поле заголовка окна если оно существует
            if (windowTitleEdit && backend.settings.target_window_title !== undefined) {
                windowTitleEdit.text = backend.settings.target_window_title || ""
            }
        }
    }

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 20
        anchors.bottomMargin: 70  // Место для кнопки
        spacing: 15

        RowLayout {
            Layout.fillWidth: true
            BaseButton {
                text: "← Назад"
                implicitWidth: 80
                implicitHeight: 30
                iconSize: 0
                textSize: 10
                onClicked: settingsWindowPage.StackView.view.pop()
            }
            Text {
                text: "◈ Окно"
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
                title: "Привязка к окну"
                Layout.fillWidth: true
                Layout.alignment: Qt.AlignHCenter
                background: Rectangle { color: "#99252525"; radius: 8; border.color: "#50ffffff"; border.width: 1 }
                contentItem: ColumnLayout {
                    spacing: 12

                    CheckBox {
                        id: windowLockedCheck
                        text: "◈ Привязка к окну"
                        font.pointSize: 11
                        property string accentColor: safeSettings.accent_color || "#7793a1"
                        indicator: Rectangle {
                            implicitWidth: 18; implicitHeight: 18; radius: 4
                            color: windowLockedCheck.checked ? windowLockedCheck.accentColor : "#3a3a3a"
                            border.color: windowLockedCheck.checked ? "#60ffffff" : "#505050"
                            border.width: 1
                            Rectangle {
                                width: 10; height: 10; radius: 4; color: "#99252525"
                                anchors.centerIn: parent; visible: windowLockedCheck.checked
                            }
                        }
                        contentItem: RowLayout {
                            spacing: 8
                            Text {
                                text: windowLockedCheck.checked ? "✓ ВКЛ" : "○ ВЫКЛ"
                                color: windowLockedCheck.checked ? windowLockedCheck.accentColor : "#606060"
                                font.pointSize: 9
                                font.bold: windowLockedCheck.checked
                                verticalAlignment: Text.AlignVCenter
                                leftPadding: 24
                            }
                        }
                        Component.onCompleted: checked = backend.window_locked
                        onCheckStateChanged: {
                            backend.window_locked = checked
                        }
                    }

                    RowLayout {
                        Layout.fillWidth: true
                        spacing: 10

                        TextField {
                            id: windowTitleEdit
                            Layout.fillWidth: true
                            text: safeSettings.target_window_title || ""
                            placeholderText: "Заголовок окна"
                            font.pointSize: 11
                            horizontalAlignment: Text.AlignHCenter
                            background: Rectangle { radius: 6; color: "#40ffffff" }
                            onEditingFinished: {
                                backend.set_setting("target_window_title", text)
                            }
                        }

                        BaseButton {
                            text: "Выбрать"
                            implicitWidth: 90
                            implicitHeight: 32
                            iconSize: 0
                            textSize: 10
                            onClicked: backend.selectWindowFromList()
                        }
                    }

                    Label {
                        text: "Макросы работают только в активном окне"
                        color: "#a0a0a0"
                        font.pointSize: 9
                        wrapMode: Text.WordWrap
                        horizontalAlignment: Text.AlignHCenter
                        Layout.fillWidth: true
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
