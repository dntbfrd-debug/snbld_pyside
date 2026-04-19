import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

ApplicationWindow {
    id: root
    width: 800
    height: 650
    minimumWidth: 600
    minimumHeight: 500
    visible: true
    title: "Автоматические коммиты на GitHub"
    color: "#1e1e1e"

    // Цвета
    readonly property color accentColor: "#4CAF50"
    readonly property color successColor: "#4CAF50"
    readonly property color errorColor: "#F44336"
    readonly property color warningColor: "#FF9800"
    readonly property color bgColor: "#1e1e1e"
    readonly property color cardColor: "#2d2d2d"
    readonly property color textColor: "#e0e0e0"
    readonly property color textSecondary: "#888888"

    // Состояние: "idle", "running", "success", "error"
    property string currentStatus: "idle"
    property string currentMessage: "Готово к работе"
    property bool buttonsEnabled: true

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 20
        spacing: 20

        // === ЗАГОЛОВОК ===
        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: 80
            color: cardColor
            radius: 10

            ColumnLayout {
                anchors.fill: parent
                anchors.margins: 15
                spacing: 5

                Label {
                    text: "🚀 Автокоммиты на GitHub"
                    font.pixelSize: 24
                    font.bold: true
                    color: textColor
                }

                Label {
                    id: statusMessage
                    text: root.currentMessage
                    font.pixelSize: 12
                    color: {
                        if (root.currentStatus === "success") return root.successColor
                        if (root.currentStatus === "error") return root.errorColor
                        if (root.currentStatus === "running") return root.warningColor
                        return root.textSecondary
                    }
                }
            }
        }

        // === СТАТУС ИНДИКАТОР ===
        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: 50
            color: cardColor
            radius: 10

            RowLayout {
                anchors.fill: parent
                anchors.margins: 15
                spacing: 15

                // Индикатор
                Rectangle {
                    Layout.preferredWidth: 20
                    Layout.preferredHeight: 20
                    radius: 10
                    color: {
                        if (root.currentStatus === "running") return root.warningColor
                        if (root.currentStatus === "success") return root.successColor
                        if (root.currentStatus === "error") return root.errorColor
                        return root.textSecondary
                    }

                    // Анимация при работе
                    SequentialAnimation on opacity {
                        running: root.currentStatus === "running"
                        loops: Animation.Infinite
                        NumberAnimation { to: 0.3; duration: 500 }
                        NumberAnimation { to: 1.0; duration: 500 }
                    }
                }

                Label {
                    text: {
                        if (root.currentStatus === "running") return "Выполняется..."
                        if (root.currentStatus === "success") return "Успешно!"
                        if (root.currentStatus === "error") return "Ошибка!"
                        return "Ожидание"
                    }
                    font.pixelSize: 14
                    font.bold: true
                    color: {
                        if (root.currentStatus === "running") return root.warningColor
                        if (root.currentStatus === "success") return root.successColor
                        if (root.currentStatus === "error") return root.errorColor
                        return root.textSecondary
                    }
                }
            }
        }

        // === КНОПКИ УПРАВЛЕНИЯ ===
        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: 60
            color: cardColor
            radius: 10

            RowLayout {
                anchors.fill: parent
                anchors.margins: 10
                spacing: 10

                Button {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    text: "🔄 Синхронизация + Push"
                    enabled: root.buttonsEnabled
                    onClicked: backend.start_once()

                    background: Rectangle {
                        color: {
                            if (!parent.enabled) return "#444"
                            if (parent.hovered) return "#5a9a5a"
                            return root.accentColor
                        }
                        radius: 6
                    }

                    contentItem: Label {
                        text: parent.text
                        font.pixelSize: 13
                        font.bold: true
                        color: parent.enabled ? "white" : "#888"
                        horizontalAlignment: Text.AlignHCenter
                        verticalAlignment: Text.AlignVCenter
                    }
                }

                Button {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    text: "📡 Мониторинг (15 мин)"
                    enabled: root.buttonsEnabled
                    onClicked: backend.start_monitor()

                    background: Rectangle {
                        color: {
                            if (!parent.enabled) return "#444"
                            if (parent.hovered) return "#4a7a9a"
                            return "#2196F3"
                        }
                        radius: 6
                    }

                    contentItem: Label {
                        text: parent.text
                        font.pixelSize: 13
                        font.bold: true
                        color: parent.enabled ? "white" : "#888"
                        horizontalAlignment: Text.AlignHCenter
                        verticalAlignment: Text.AlignVCenter
                    }
                }

                Button {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    text: "⬆️ Только Push"
                    enabled: root.buttonsEnabled
                    onClicked: backend.start_push_only()

                    background: Rectangle {
                        color: {
                            if (!parent.enabled) return "#444"
                            if (parent.hovered) return "#7a6a4a"
                            return "#FF9800"
                        }
                        radius: 6
                    }

                    contentItem: Label {
                        text: parent.text
                        font.pixelSize: 13
                        font.bold: true
                        color: parent.enabled ? "white" : "#888"
                        horizontalAlignment: Text.AlignHCenter
                        verticalAlignment: Text.AlignVCenter
                    }
                }

                Button {
                    Layout.preferredWidth: 80
                    Layout.fillHeight: true
                    text: "⏹️ Стоп"
                    enabled: root.currentStatus === "running"
                    visible: enabled
                    onClicked: backend.stop()

                    background: Rectangle {
                        color: {
                            if (!parent.enabled) return "transparent"
                            if (parent.hovered) return "#9a4a4a"
                            return root.errorColor
                        }
                        radius: 6
                    }

                    contentItem: Label {
                        text: parent.text
                        font.pixelSize: 13
                        font.bold: true
                        color: "white"
                        horizontalAlignment: Text.AlignHCenter
                        verticalAlignment: Text.AlignVCenter
                    }
                }
            }
        }

        // === ЛОГ ОПЕРАЦИЙ ===
        Rectangle {
            Layout.fillWidth: true
            Layout.fillHeight: true
            color: cardColor
            radius: 10

            ColumnLayout {
                anchors.fill: parent
                anchors.margins: 10
                spacing: 10

                // Заголовок лога
                RowLayout {
                    Layout.fillWidth: true
                    spacing: 10

                    Label {
                        text: "📋 Лог операций"
                        font.pixelSize: 14
                        font.bold: true
                        color: textColor
                    }

                    Item { Layout.fillWidth: true }

                    Button {
                        text: "🗑️ Очистить"
                        flat: true
                        onClicked: backend.clear_log()

                        background: Rectangle {
                            color: parent.hovered ? "#3a3a3a" : "transparent"
                            radius: 4
                        }

                        contentItem: Label {
                            text: parent.text
                            font.pixelSize: 12
                            color: root.textSecondary
                            horizontalAlignment: Text.AlignHCenter
                            verticalAlignment: Text.AlignVCenter
                        }
                    }
                }

                // Область лога
                Rectangle {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    color: "#1a1a1a"
                    radius: 6
                    clip: true

                    ScrollView {
                        anchors.fill: parent
                        anchors.margins: 2
                        ScrollBar.vertical.policy: ScrollBar.AlwaysOn

                        TextArea {
                            id: logArea
                            readOnly: true
                            selectByMouse: true
                            font.family: "Consolas"
                            font.pixelSize: 12
                            color: root.textColor
                            wrapMode: Text.Wrap
                            textFormat: Text.PlainText
                            background: Rectangle {
                                color: "transparent"
                            }
                        }
                    }
                }
            }
        }
    }

    // === Connections для обновления лога ===
    Connections {
        target: backend
        function onLog_updated() {
            logArea.text = backend.get_log()
        }
        function onStatus_updated(status) {
            root.currentStatus = status
        }
        function onMessage_updated(message) {
            root.currentMessage = message
            statusMessage.text = message
        }
        function onButtons_enabled(enabled) {
            root.buttonsEnabled = enabled
        }
    }
}
