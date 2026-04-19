import QtQuick 2.15
import QtQuick.Controls.Basic 2.15
import QtQuick.Layouts 1.15

Item {
    id: settingsDebugPage
    
    property color accentColor: backend && backend.settings && backend.settings.accent_color ? backend.settings.accent_color : "#7793a1"

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 20
        anchors.bottomMargin: 70
        spacing: 10

        // ========== ПЛИТКА: КОНСОЛЬ ==========
        GroupBox {
            title: "💻 Консоль"
            Layout.fillWidth: true
            Layout.preferredHeight: 100
            background: Rectangle { color: "#99252525"; radius: 8; border.color: "#50ffffff"; border.width: 1 }

            contentItem: ColumnLayout {
                spacing: 8

                CheckBox {
                    id: showConsoleCheck
                    font.pointSize: 10
                    property string accentColor: backend && backend.settings ? (backend.settings.accent_color || "#7793a1") : "#7793a1"

                    // При запуске консоль ВИДИМА (--windows-console-mode=force)
                    //checked: false
                    checked: backend.console_visible

                    indicator: Rectangle {
                        implicitWidth: 18; implicitHeight: 18; radius: 4
                        color: showConsoleCheck.checked ? showConsoleCheck.accentColor : "#3a3a3a"
                        border.color: showConsoleCheck.checked ? "#60ffffff" : "#505050"
                        border.width: 1
                        Rectangle {
                            width: 10; height: 10; radius: 4; color: "#99252525"
                            anchors.centerIn: parent
                            visible: showConsoleCheck.checked
                        }
                    }

                    contentItem: RowLayout {
                        spacing: 8
                        Text {
                            // Инвертированный текст: если checked=true (консоль видима) → "Скрыть"
                            text: showConsoleCheck.checked ? "✓ Консоль видна" : "○ Консоль скрыта"
                            color: showConsoleCheck.checked ? showConsoleCheck.accentColor : "#606060"
                            font.pointSize: 11
                            font.bold: showConsoleCheck.checked
                            verticalAlignment: Text.AlignVCenter
                            leftPadding: 24
                        }
                    }

                    onCheckStateChanged: {
                        backend.toggle_console()
                    }
                }

                Text {
                    text: "⚠ Работает только в EXE-версии (при запуске из Python консоль всегда видна)"
                    color: "#a0a0a0"
                    font.pointSize: 8
                    font.italic: true
                    Layout.fillWidth: true
                }
            }
        }

        // ========== ПЛИТКА: ЛОГИ ==========
        GroupBox {
            title: "📋 Логи"
            Layout.fillWidth: true
            Layout.preferredHeight: 150
            background: Rectangle { color: "#99252525"; radius: 8; border.color: "#50ffffff"; border.width: 1 }

            contentItem: ColumnLayout {
                spacing: 8

                Text {
                    text: "Отправить все логи разработчику для анализа"
                    color: "#a0a0a0"
                    font.pointSize: 9
                    Layout.fillWidth: true
                }

                Text {
                    text: "Вы не отправляете мне никаких своих личных данных, вы можете сами проверить все логи в папке logs"
                    color: "#70a070"
                    font.pointSize: 10
                    font.italic: true
                    wrapMode: Text.WordWrap
                    Layout.fillWidth: true
                }

                BaseButton {
                    text: "✈ Отправить логи"
                    implicitWidth: 140
                    implicitHeight: 32
                    iconSize: 12
                    textSize: 9
                    onClicked: backend.send_logs_to_telegram()
                }
            }
        }

        // ========== ПЛИТКА: ОБНОВЛЕНИЯ ==========
        GroupBox {
            title: "🔄 Обновления"
            Layout.fillWidth: true
            Layout.preferredHeight: 150
            background: Rectangle { color: "#99252525"; radius: 8; border.color: "#50ffffff"; border.width: 1 }

            contentItem: ColumnLayout {
                spacing: 8

                RowLayout {
                    Layout.fillWidth: true
                    Text {
                        text: "Текущая версия:"
                        color: "#a0a0a0"
                        font.pointSize: 10
                    }
                    Text {
                        id: currentVersionText
                        text: backend.get_current_version()
                        color: "#c2c2c2"
                        font.pointSize: 10
                        font.bold: true
                    }
                    Item { Layout.fillWidth: true }
                }

                RowLayout {
                    Layout.fillWidth: true
                    Text {
                        text: "Доступная версия:"
                        color: "#a0a0a0"
                        font.pointSize: 10
                    }
                    Text {
                        id: latestVersionText
                        text: "-"
                        color: "#4CAF50"
                        font.pointSize: 10
                        font.bold: true
                    }
                    Item { Layout.fillWidth: true }
                }

                RowLayout {
                    Layout.fillWidth: true
                    BaseButton {
                        text: "🔄 Проверить"
                        implicitWidth: 140
                        implicitHeight: 28
                        iconSize: 10
                        textSize: 9
                        onClicked: {
                            var result = backend.check_for_updates()
                            if (result.success) {
                                latestVersionText.text = result.latest_version
                                if (result.available) {
                                    installBtn.visible = true
                                    installBtn.enabled = true
                                    installBtn.downloadUrl = result.download_url
                                    installBtn.version = result.latest_version
                                    downloadBtn.visible = true
                                    downloadBtn.enabled = true
                                    downloadBtn.downloadUrl = result.download_url
                                    latestVersionText.color = "#4CAF50"
                                } else {
                                    installBtn.visible = false
                                    installBtn.enabled = false
                                    downloadBtn.visible = false
                                    downloadBtn.enabled = false
                                    latestVersionText.text = "Нет обновлений"
                                    latestVersionText.color = "#a0a0a0"
                                }
                            } else {
                                latestVersionText.text = "Ошибка проверки"
                                latestVersionText.color = "#f44336"
                                installBtn.visible = false
                                downloadBtn.visible = false
                            }
                        }
                    }
                    BaseButton {
                        id: installBtn
                        property string downloadUrl: ""
                        property string version: ""
                        text: "⬇ Установить"
                        implicitWidth: 140
                        implicitHeight: 28
                        iconSize: 10
                        textSize: 9
                        visible: false
                        enabled: false
                        onClicked: {
                            if (downloadUrl !== "" && version !== "") {
                                backend.download_update_async(downloadUrl, version)
                            }
                        }
                    }
                    BaseButton {
                        id: downloadBtn
                        property string downloadUrl: ""
                        text: "🌐 Браузер"
                        implicitWidth: 120
                        implicitHeight: 28
                        iconSize: 10
                        textSize: 9
                        visible: false
                        enabled: false
                        onClicked: {
                            if (downloadUrl !== "") {
                                backend.open_url(downloadUrl)
                            }
                        }
                    }
                    Item { Layout.fillWidth: true }
                }
            }
        }

        // Кнопка сохранения внизу по центру
        RowLayout {
            Layout.fillWidth: true
            Layout.preferredHeight: 55
            spacing: 0
            Item { Layout.fillWidth: true }
            BaseButton {
                text: "◈ Сохранить"
                implicitWidth: 160
                implicitHeight: 38
                iconSize: 14
                textSize: 10
                onClicked: backend.save_all_settings()
            }
            Item { Layout.fillWidth: true }
        }
    }

    // Обновление акцентного цвета при изменении настроек
    Connections {
        target: backend
        function onSettingsChanged() {
            settingsDebugPage.accentColor = backend.settings.accent_color !== undefined && backend.settings.accent_color !== null ? backend.settings.accent_color : "#7793a1"
        }
    }
}
