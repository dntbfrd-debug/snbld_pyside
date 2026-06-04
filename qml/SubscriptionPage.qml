import QtQuick 2.15
import QtQuick.Controls.Basic 2.15
import QtQuick.Layouts 1.15
import "components"

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



        // ========== БЛОК: ФОРМА АКТИВАЦИИ (если НЕ активирована) ==========
        GlassBlurPanel {
            id: activationPanel
            Layout.fillWidth: true
            Layout.preferredHeight: activationLayout.implicitHeight + 30
            visible: !subscriptionPage.isActivated

            // Волна — полная линия + серый градиент слева направо
            Rectangle {
                anchors.top: parent.top
                width: parent.width
                height: 3
                radius: parent.radius
                clip: true
                visible: subscriptionPage.activationInProgress
                z: 2

                Rectangle {
                    anchors.fill: parent
                    color: subscriptionPage.accentColor
                }

                Rectangle {
                    id: subWaveBar
                    width: 300
                    height: 3
                    color: "transparent"
                    gradient: Gradient {
                        orientation: Gradient.Horizontal
                        GradientStop { position: 0.0; color: "transparent" }
                        GradientStop { position: 0.25; color: "#AA444444" }
                        GradientStop { position: 0.5; color: "#DD000000" }
                        GradientStop { position: 0.75; color: "#AA444444" }
                        GradientStop { position: 1.0; color: "transparent" }
                    }

                    SequentialAnimation on x {
                        running: subWaveBar.visible
                        loops: Animation.Infinite
                        PropertyAction { value: -subWaveBar.width }
                        NumberAnimation {
                            to: subWaveBar.parent.width
                            duration: 2500
                            easing.type: Easing.Linear
                        }
                    }
                }
            }

            ColumnLayout {
                id: activationLayout
                anchors.fill: parent
                anchors.margins: 15
                spacing: 12

                Text {
                    text: "Активация программы"
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
                    font.family: "Fira Code"
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
                        text: "Активировать"
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
                            backend.activateWithKey(subscriptionPage.activationKey)
                        }
                    }
                }

                // Слушаем результат асинхронной активации
                Connections {
                    target: backend
                    function onActivationResult(status, message) {
                        subscriptionPage.activationInProgress = false
                        if (status === "success") {
                            subscriptionPage.activationStatus = "✓ Программа активирована!"
                            subscriptionPage.activationSuccess = true
                            subscriptionPage.activationError = false
                            keyInput.enabled = false
                        } else {
                            subscriptionPage.activationStatus = "✗ " + message
                            subscriptionPage.activationSuccess = false
                            subscriptionPage.activationError = true
                        }
                    }
                }

                Text {
                    text: " Ключ привязывается к вашему компьютеру"
                    color: "#707070"
                    font.pointSize: 9
                    wrapMode: Text.WordWrap
                    Layout.fillWidth: true
                }
            }
        }

        // ========== БЛОК: СТАТУС ПОДПИСКИ (показываем всегда) ==========
        GlassBlurPanel {
            Layout.fillWidth: true
            Layout.preferredHeight: 120
            border.color: subInfo.valid ? "#4CAF50" : "#e74c3c"

            ColumnLayout {
                anchors.fill: parent
                anchors.margins: 15
                spacing: 10

                RowLayout {
                    Layout.fillWidth: true
                    Text {
                        text: "Статус:"
                        color: "#a2a2a2"
                        font.pointSize: 12
                    }
                    Text {
                        text: subInfo.valid ? " Активна" : " Неактивна"
                        color: subInfo.valid ? "#4CAF50" : "#e74c3c"
                        font.pointSize: 12
                        font.bold: true
                    }
                    Item { Layout.fillWidth: true }
                }

                Rectangle { height: 1; Layout.fillWidth: true; color: "#40ffffff" }

                RowLayout {
                    Layout.fillWidth: true
                    Text {
                        text: "Действует до:"
                        color: "#a2a2a2"
                        font.pointSize: 10
                    }
                    Text {
                        id: expiresText
                        text: "подсчёт..."
                        color: "#a2a2a2"
                        font.pointSize: 10
                        Layout.fillWidth: true
                    }
                }

                Connections {
                    target: backend
                    function onSubscriptionChanged(subInfo) {
                        if (subInfo.expires_pretty) {
                            expiresText.text = subInfo.expires_pretty
                            expiresText.color = subInfo.expires_color || "#4CAF50"
                        } else {
                            expiresText.text = subInfo.expires_at || "неизвестно"
                            expiresText.color = "#a2a2a2"
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
                        text: "Тип:"
                        color: "#a2a2a2"
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


        // Информация
        GlassBlurPanel {
            Layout.fillWidth: true
            Layout.preferredHeight: infoLayout.implicitHeight + 30
            glassOpacity: 0

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
                    text: "Информация:"
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
