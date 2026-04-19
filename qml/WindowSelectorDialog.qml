import QtQuick 2.15
import QtQuick.Controls.Basic 2.15
import QtQuick.Layouts 1.15
import QtQuick.Window 2.15
import Qt5Compat.GraphicalEffects

// Диалог выбора окна игры — стиль приложения
Window {
    id: windowSelectorDialog
    visible: false
    modality: Qt.WindowModal
    flags: Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Dialog
    color: "transparent"
    width: 520
    height: 450
    x: Screen.width / 2 - width / 2
    y: Screen.height / 6
    title: "Выбор окна игры"

    // Список окон
    property var windowsList: []
    property int selectedIndex: -1
    property color accentColor: backend && backend.settings && backend.settings.accent_color ? backend.settings.accent_color : "#7793a1"

    signal windowSelected(string title)
    signal dialogCancelled()

    // Основной фон
    Rectangle {
        anchors.fill: parent
        radius: 12
        color: "#2d2d2d"
        clip: true

        // Заголовок
        Rectangle {
            id: headerBar
            anchors.top: parent.top
            anchors.left: parent.left
            anchors.right: parent.right
            height: 45
            color: "#2a2a3a"

            Text {
                anchors.left: parent.left
                anchors.leftMargin: 16
                anchors.verticalCenter: parent.verticalCenter
                text: "🪟 Выберите окно игры"
                color: "white"
                font.pointSize: 13
                font.bold: true
            }

            // Кнопка закрытия
            Rectangle {
                anchors.right: parent.right
                anchors.rightMargin: 8
                anchors.verticalCenter: parent.verticalCenter
                width: 28
                height: 28
                radius: 6
                color: closeBtn.containsMouse ? "#e81123" : "transparent"

                MouseArea {
                    id: closeBtn
                    anchors.fill: parent
                    hoverEnabled: true
                    cursorShape: Qt.PointingHandCursor
                    onClicked: {
                        windowSelectorDialog.dialogCancelled()
                        windowSelectorDialog.close()
                    }
                }

                Text {
                    anchors.centerIn: parent
                    text: "✕"
                    color: closeBtn.containsMouse ? "white" : "#808080"
                    font.pointSize: 10
                    font.bold: true
                }
            }
        }

        // Разделитель
        Rectangle {
            anchors.top: headerBar.bottom
            anchors.left: parent.left
            anchors.right: parent.right
            height: 1
            color: "#3a3a4a"
        }

        // Контент
        ColumnLayout {
            anchors.top: headerBar.bottom
            anchors.topMargin: 10
            anchors.left: parent.left
            anchors.right: parent.right
            anchors.bottom: parent.bottom
            anchors.margins: 15
            spacing: 10

            // Подсказка
            Rectangle {
                Layout.fillWidth: true
                height: 70
                color: "#99252525"
                radius: 8
                border.color: "#50ffffff"
                border.width: 2

                Text {
                    anchors.fill: parent
                    anchors.margins: 10
                    text: "Выберите окно игры из списка ниже.\nПрограмма будет использовать это окно для макросов."
                    color: "#c2c2c2"
                    font.pointSize: 9
                    wrapMode: Text.WordWrap
                    verticalAlignment: Text.AlignVCenter
                    horizontalAlignment: Text.AlignHCenter
                }
            }

            // Список окон
            Rectangle {
                Layout.fillWidth: true
                Layout.fillHeight: true
                color: "#99252525"
                radius: 8
                border.color: "#50ffffff"
                border.width: 2
                clip: true

                ListView {
                    id: windowsListView
                    anchors.fill: parent
                    anchors.margins: 4
                    spacing: 4
                    clip: true

                    model: windowSelectorDialog.windowsList

                    delegate: Rectangle {
                        width: windowsListView.width - 8
                        height: 50
                        radius: 8
                        color: {
                            if (mouseArea.containsMouse) return Qt.rgba(accentColor.r, accentColor.g, accentColor.b, 0.15)
                            if (windowsListView.currentIndex === index) return Qt.rgba(accentColor.r, accentColor.g, accentColor.b, 0.25)
                            return "transparent"
                        }
                        border.color: {
                            if (windowsListView.currentIndex === index) return accentColor
                            if (mouseArea.containsMouse) return Qt.lighter(accentColor, 1.2)
                            return "transparent"
                        }
                        border.width: {
                            if (windowsListView.currentIndex === index) return 2
                            if (mouseArea.containsMouse) return 1
                            return 0
                        }

                        MouseArea {
                            id: mouseArea
                            anchors.fill: parent
                            hoverEnabled: true
                            cursorShape: Qt.PointingHandCursor
                            onClicked: {
                                windowsListView.currentIndex = index
                                windowSelectorDialog.selectedIndex = index
                            }
                            onDoubleClicked: {
                                windowsListView.currentIndex = index
                                windowSelectorDialog.selectedIndex = index
                                windowSelectorDialog.onSelectClicked()
                            }
                        }

                        ColumnLayout {
                            anchors.fill: parent
                            anchors.margins: 10
                            anchors.leftMargin: 12
                            spacing: 2

                            Text {
                                text: modelData.title || "Без имени"
                                color: "#e0e0e0"
                                font.pointSize: 10
                                font.bold: true
                                elide: Text.ElideRight
                                Layout.fillWidth: true
                            }

                            Text {
                                text: (modelData.processName || "") + (modelData.pid ? " (PID: " + modelData.pid + ")" : "")
                                color: "#808080"
                                font.pointSize: 8
                                elide: Text.ElideRight
                                Layout.fillWidth: true
                            }
                        }
                    }

                    // Сообщение если нет окон
                    Rectangle {
                        anchors.fill: parent
                        color: "transparent"
                        visible: windowsListView.count === 0

                        Text {
                            anchors.centerIn: parent
                            text: "Нет открытых окон"
                            color: "#606060"
                            font.pointSize: 12
                        }
                    }
                }
            }

            // Кнопки
            RowLayout {
                Layout.fillWidth: true
                Layout.preferredHeight: 45
                spacing: 10

                // Обновить список
                BaseButton {
                    text: "🔄 Обновить"
                    Layout.fillWidth: true
                    implicitHeight: 40
                    iconSize: 0
                    textSize: 10
                    onClicked: {
                        windowSelectorDialog.loadWindows()
                    }
                }

                // Отмена
                BaseButton {
                    text: "✕ Отмена"
                    Layout.fillWidth: true
                    implicitHeight: 40
                    iconSize: 0
                    textSize: 10
                    onClicked: {
                        windowSelectorDialog.dialogCancelled()
                        windowSelectorDialog.close()
                    }
                }

                // Выбрать
                BaseButton {
                    text: "✓ Выбрать"
                    Layout.fillWidth: true
                    implicitHeight: 40
                    iconSize: 0
                    textSize: 10
                    accentColor: windowSelectorDialog.accentColor
                    enabled: windowSelectorDialog.selectedIndex >= 0
                    opacity: enabled ? 1.0 : 0.5
                    onClicked: {
                        windowSelectorDialog.onSelectClicked()
                    }
                }
            }
        }
    }

    // Функции
    function loadWindows() {
        console.log("WindowSelectorDialog: Загрузка списка окон")
        var result = backend.getWindowList()
        if (result && result.length > 0) {
            windowSelectorDialog.windowsList = result
            windowSelectorDialog.selectedIndex = -1
            windowsListView.currentIndex = -1
            console.log("WindowSelectorDialog: Загружено " + result.length + " окон")
        } else {
            windowSelectorDialog.windowsList = []
            console.log("WindowSelectorDialog: Нет окон")
        }
    }

    function onSelectClicked() {
        if (selectedIndex >= 0 && selectedIndex < windowsList.length) {
            var win = windowsList[selectedIndex]
            var title = win.title || ""
            console.log("WindowSelectorDialog: Выбрано окно: " + title)
            windowSelectorDialog.windowSelected(title)
            windowSelectorDialog.close()
        }
    }

    // Обработка закрытия
    onClosing: {
        console.log("WindowSelectorDialog: onClosing")
        windowSelectorDialog.dialogCancelled()
    }

    // Esc
    Shortcut {
        sequence: "Esc"
        onActivated: {
            windowSelectorDialog.dialogCancelled()
            windowSelectorDialog.close()
        }
    }
}
