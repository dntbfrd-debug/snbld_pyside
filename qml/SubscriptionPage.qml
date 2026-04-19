import QtQuick 2.15
import QtQuick.Controls.Basic 2.15
import QtQuick.Layouts 1.15

Item {
    id: subscriptionPage

    // Безопасный доступ к backend
    property bool backendReady: backend !== null && backend !== undefined
    property bool isActivated: backendReady ? backend.isActivated : false
    property var subInfo: backendReady ? (backend.subscription_info || {}) : {}
    property string accentColor: (backendReady && backend.settings) ? (backend.settings.accent_color || "#fd79a8") : "#fd79a8"

    // Состояние формы активации
    property string activationKey: ""
    property string activationStatus: ""
    property bool activationInProgress: false
    property bool activationSuccess: false
    property bool activationError: false

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 20
        spacing: 15

        // Заголовок
        RowLayout {
            Layout.fillWidth: true
            Text {
                text: "✦ Подписка"
                font.pointSize: 20
                font.bold: true
                color: subscriptionPage.accentColor
            }
            Item { Layout.fillWidth: true }
        }

        // ========== БЛОК: ФОРМА АКТИВАЦИИ (если НЕ активирована) ==========
        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: activationLayout.implicitHeight + 30
            color: "#99252525"
            radius: 8
            border.width: 1
            border.color: activationError ? "#f44336" : (activationSuccess ? "#4CAF50" : "#50ffffff")
            visible: !subscriptionPage.isActivated

            ColumnLayout {
                id: activationLayout
                anchors.fill: parent
                anchors.margins: 15
                spacing: 12

                Text {
                    text: "🔑 Активация программы"
                    font.pointSize: 14
                    font.bold: true
                    color: subscriptionPage.accentColor
                }

                Text {
                    text: "Введите ключ активации, полученный после покупки подписки"
                    color: "#a0a0a0"
                    font.pointSize: 10
                    wrapMode: Text.WordWrap
                    Layout.fillWidth: true
                }

                // Поле ввода ключа
                TextField {
                    id: keyInput
                    Layout.fillWidth: true
                    placeholderText: "ABCD-EFGH-IJKL-MNOP"
                    font.pointSize: 14
                    font.family: "Courier New"
                    color: "#ffffff"
                    placeholderTextColor: "#555555"
                    horizontalAlignment: TextInput.AlignHCenter
                    maximumLength: 19
                    enabled: !activationInProgress

                    background: Rectangle {
                        color: "#1d1d1d"
                        radius: 6
                        border.color: keyInput.activeFocus ? subscriptionPage.accentColor : "#444444"
                        border.width: 1
                    }

                    onTextEdited: {
                        // Форматируем ключ: XXXX-XXXX-XXXX-XXXX
                        var raw = text.replace(/-/g, '').toUpperCase()
                        var formatted = ""
                        for (var i = 0; i < raw.length && i < 16; i++) {
                            if (i > 0 && i % 4 === 0) formatted += "-"
                            formatted += raw[i]
                        }
                        if (text !== formatted) {
                            text = formatted
                            cursorPosition = text.length
                        }
                        subscriptionPage.activationKey = formatted.replace(/-/g, '')
                    }
                }

                // Статус активации
                Text {
                    text: subscriptionPage.activationStatus
                    color: subscriptionPage.activationError ? "#f44336" : "#4CAF50"
                    font.pointSize: 10
                    font.bold: true
                    visible: subscriptionPage.activationStatus !== ""
                    Layout.fillWidth: true
                    horizontalAlignment: TextInput.AlignHCenter
                }

                // Кнопка активации
                RowLayout {
                    Layout.fillWidth: true
                    spacing: 10

                    BaseButton {
                        text: "✓ Активировать"
                        Layout.fillWidth: true
                        implicitHeight: 40
                        iconSize: 14
                        textSize: 11
                        enabled: subscriptionPage.activationKey.length === 16 && !subscriptionPage.activationInProgress
                        onClicked: {
                            subscriptionPage.activationInProgress = true
                            subscriptionPage.activationStatus = "Проверка ключа..."
                            subscriptionPage.activationSuccess = false
                            subscriptionPage.activationError = false

                            var result = backend.activateWithKey(subscriptionPage.activationKey)
                            subscriptionPage.activationInProgress = false

                            if (result && result.success) {
                                subscriptionPage.activationStatus = "✓ Программа активирована!"
                                subscriptionPage.activationSuccess = true
                                subscriptionPage.activationError = false
                                keyInput.enabled = false
                            } else {
                                subscriptionPage.activationStatus = "✗ " + (result && result.error ? result.error : "Ошибка активации")
                                subscriptionPage.activationSuccess = false
                                subscriptionPage.activationError = true
                            }
                        }
                    }
                }

                Text {
                    text: "• Один ключ = одна копия программы\n• При переустановке Windows используйте тот же ключ\n• Ключ привязывается к вашему компьютеру"
                    color: "#707070"
                    font.pointSize: 9
                    wrapMode: Text.WordWrap
                    Layout.fillWidth: true
                }
            }
        }

        // ========== БЛОК: СТАТУС ПОДПИСКИ (показываем всегда) ==========
        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: 120
            color: "#99252525"
            radius: 8
            border.width: 1
            border.color: subInfo.valid ? "#4CAF50" : "#FFC107"

            ColumnLayout {
                anchors.fill: parent
                anchors.margins: 15
                spacing: 10

                RowLayout {
                    Layout.fillWidth: true
                    Text {
                        text: "◈ Статус:"
                        color: "#c2c2c2"
                        font.pointSize: 12
                    }
                    Text {
                        text: subInfo.valid ? "✓ Активна" : "⚠ Неактивна"
                        color: subInfo.valid ? "#4CAF50" : "#FFC107"
                        font.pointSize: 12
                        font.bold: true
                    }
                    Item { Layout.fillWidth: true }
                }

                Rectangle { height: 1; Layout.fillWidth: true; color: "#40ffffff" }

                RowLayout {
                    Layout.fillWidth: true
                    Text {
                        text: "◈ Действует до:"
                        color: "#c2c2c2"
                        font.pointSize: 10
                    }
                    Text {
                        id: expiresText
                        text: "подсчёт..."
                        color: "#c2c2c2"
                        font.pointSize: 10
                        Layout.fillWidth: true
                    }
                }

                Connections {
                    target: backend
                    onSubscriptionChanged: {
                        if (subInfo.expires_pretty) {
                            expiresText.text = subInfo.expires_pretty
                            expiresText.color = subInfo.expires_color || "#4CAF50"
                        } else {
                            expiresText.text = subInfo.expires_at || "неизвестно"
                            expiresText.color = "#c2c2c2"
                        }
                    }
                }

                Component.onCompleted: {
                    if (subInfo.expires_pretty) {
                        expiresText.text = subInfo.expires_pretty
                        expiresText.color = subInfo.expires_color || "#4CAF50"
                    }
                }

                Rectangle { height: 1; Layout.fillWidth: true; color: "#40ffffff" }

                RowLayout {
                    Layout.fillWidth: true
                    Text {
                        text: "◈ Тип:"
                        color: "#c2c2c2"
                        font.pointSize: 10
                    }
                    Text {
                        text: subInfo.key_type || "неизвестно"
                        color: "#a0a0a0"
                        font.pointSize: 9
                        Layout.fillWidth: true
                    }
                }
            }
        }

        // Кнопка покупки
        RowLayout {
            Layout.fillWidth: true
            spacing: 15

            BaseButton {
                text: "✦ Купить подписку"
                Layout.fillWidth: true
                implicitHeight: 40
                iconSize: 14
                textSize: 10
                onClicked: {
                    if (backend) {
                        backend.buy_subscription()
                    }
                }
            }
        }

        // Информация
        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: infoLayout.implicitHeight + 30
            color: "transparent"
            radius: 8
            border.width: 1
            border.color: subscriptionPage.accentColor

            PageBorder {
                anchors.fill: parent
                z: 1
            }

            ColumnLayout {
                id: infoLayout
                anchors.fill: parent
                anchors.margins: 15
                spacing: 8

                Label {
                    text: "◈ Информация:"
                    color: subscriptionPage.accentColor
                    font.pointSize: 11
                    font.bold: true
                }

                Text {
                    text: "• Для работы программы необходима активация\n• После покупки вы получите ключ активации\n• Введите ключ в поле выше и нажмите «Активировать»\n• Один ключ = одна копия программы\n• При переустановке Windows используйте тот же ключ"
                    color: "#a0a0a0"
                    font.pointSize: 9
                    wrapMode: Text.WordWrap
                    Layout.fillWidth: true
                }
            }
        }
    }
}
