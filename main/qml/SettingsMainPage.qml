import QtQuick 2.15
import QtQuick.Controls.Basic 2.15
import QtQuick.Layouts 1.15
import QtQml 2.15

Item {
    id: settingsMainPage

    // Верхняя панель с плитками
    ColumnLayout {
        anchors.top: parent.top
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.margins: 20
        spacing: 15
        height: tilesRow.implicitHeight

        RowLayout {
            id: tilesRow
            spacing: 8
            Layout.fillWidth: true
            Layout.preferredHeight: 100

            // Плитка: Окно
            CustomTabButton {
                id: windowTile
                text: "Окно"
                iconSource: "../icons/window.png"
                isActive: false
                Layout.fillWidth: true
                Layout.preferredWidth: tilesRow.width > 0 ? (tilesRow.width - 48) / 7 : 100
                Layout.preferredHeight: 100
                iconSize: 18
                textSize: 10
                onClicked: {
                    settingsTabIndicator.setActive(this)
                    settingsStackView.push(Qt.resolvedUrl("SettingsWindowPage.qml"))
                }
            }

            // Плитка: Движение
            CustomTabButton {
                id: movementTile
                text: "Движение"
                iconSource: "../icons/go.png"
                isActive: false
                Layout.fillWidth: true
                Layout.preferredWidth: tilesRow.width > 0 ? (tilesRow.width - 48) / 7 : 100
                Layout.preferredHeight: 100
                iconSize: 18
                textSize: 10
                onClicked: {
                    settingsTabIndicator.setActive(this)
                    settingsStackView.push(Qt.resolvedUrl("SettingsMovementPage.qml"))
                }
            }

            // Плитка: Калибровка
            CustomTabButton {
                id: ocrTile
                text: "Калибровка"
                iconSource: "../icons/ocr.png"
                isActive: false
                Layout.fillWidth: true
                Layout.preferredWidth: tilesRow.width > 0 ? (tilesRow.width - 48) / 7 : 100
                Layout.preferredHeight: 100
                iconSize: 18
                textSize: 10
                onClicked: {
                    settingsTabIndicator.setActive(this)
                    settingsStackView.push(Qt.resolvedUrl("OCROptionsSelector.qml"))
                }
            }

            // Плитка: Сеть
            CustomTabButton {
                id: networkTile
                text: "Сеть"
                iconSource: "../icons/set.png"
                isActive: false
                Layout.fillWidth: true
                Layout.preferredWidth: tilesRow.width > 0 ? (tilesRow.width - 48) / 7 : 100
                Layout.preferredHeight: 100
                iconSize: 18
                textSize: 10
                onClicked: {
                    settingsTabIndicator.setActive(this)
                    settingsStackView.push(Qt.resolvedUrl("SettingsNetworkPage.qml"))
                }
            }

            // Плитка: Ресвап
            CustomTabButton {
                id: reswapTile
                text: "Ресвап"
                iconSource: "../icons/swap.png"
                isActive: false
                Layout.fillWidth: true
                Layout.preferredWidth: tilesRow.width > 0 ? (tilesRow.width - 48) / 7 : 100
                Layout.preferredHeight: 100
                iconSize: 18
                textSize: 10
                onClicked: {
                    settingsTabIndicator.setActive(this)
                    settingsStackView.push(Qt.resolvedUrl("SettingsReswapPage.qml"))
                }
            }

            // Плитка: Редактор задержек
            CustomTabButton {
                id: delaysTile
                text: "Задержки"
                iconSource: "../icons/any.png"
                isActive: false
                Layout.fillWidth: true
                Layout.preferredWidth: tilesRow.width > 0 ? (tilesRow.width - 48) / 7 : 100
                Layout.preferredHeight: 100
                iconSize: 18
                textSize: 10
                onClicked: {
                    settingsTabIndicator.setActive(this)
                    settingsStackView.push(Qt.resolvedUrl("SettingsOtherPage.qml"))
                }
            }

            // Плитка: Внешний вид
            CustomTabButton {
                id: appearanceTile
                text: "Внеш. вид"
                iconSource: "../icons/edit.png"
                isActive: false
                Layout.fillWidth: true
                Layout.preferredWidth: tilesRow.width > 0 ? (tilesRow.width - 48) / 7 : 100
                Layout.preferredHeight: 100
                iconSize: 18
                textSize: 10
                onClicked: {
                    settingsTabIndicator.setActive(this)
                    settingsStackView.push(Qt.resolvedUrl("SettingsAppearancePage.qml"))
                }
            }
        }
    }

    // StackView для страниц
    StackView {
        id: settingsStackView
        anchors.top: parent.top
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.bottom: parent.bottom
        anchors.topMargin: 140
        anchors.leftMargin: 20
        anchors.rightMargin: 20
        anchors.bottomMargin: 20
        clip: true
        initialItem: Rectangle {
            color: "transparent"
        }
        pushEnter: Transition {
            PropertyAnimation {
                property: "x"
                from: settingsStackView.width
                to: 0
                duration: 300
                easing.type: Easing.OutCubic
            }
            PropertyAnimation {
                property: "opacity"
                from: 0
                to: 1
                duration: 300
                easing.type: Easing.OutCubic
            }
        }
        pushExit: Transition {
            PropertyAnimation {
                property: "x"
                from: 0
                to: -settingsStackView.width * 0.5
                duration: 300
                easing.type: Easing.InCubic
            }
            PropertyAnimation {
                property: "opacity"
                from: 1
                to: 0
                duration: 300
                easing.type: Easing.InCubic
            }
        }
        popEnter: Transition {
            PropertyAnimation {
                property: "x"
                from: -settingsStackView.width * 0.5
                to: 0
                duration: 300
                easing.type: Easing.OutCubic
            }
            PropertyAnimation {
                property: "opacity"
                from: 0
                to: 1
                duration: 300
                easing.type: Easing.OutCubic
            }
        }
        popExit: Transition {
            PropertyAnimation {
                property: "x"
                from: 0
                to: settingsStackView.width
                duration: 300
                easing.type: Easing.InCubic
            }
            PropertyAnimation {
                property: "opacity"
                from: 1
                to: 0
                duration: 300
                easing.type: Easing.InCubic
            }
        }
    }

    // Индикатор для плиток — явный массив только CustomTabButton
    ButtonGroupWithIndicator {
        id: settingsTabIndicator
        buttons: [windowTile, movementTile, ocrTile, networkTile, reswapTile, delaysTile, appearanceTile]
        setActiveCallback: function(activeButton) {
            for (var i = 0; i < buttons.length; i++) {
                if (buttons[i]) buttons[i].isActive = false
            }
            if (activeButton) activeButton.isActive = true
        }
        Component.onCompleted: {
            currentIndex = 0
            init()
            setActive(windowTile)
            settingsStackView.push(Qt.resolvedUrl("SettingsWindowPage.qml"))
        }
    }
}
