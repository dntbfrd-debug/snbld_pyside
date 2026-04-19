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

            // Плитка: Ресвап
            CustomTabButton {
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

            // Плитка: Движение
            CustomTabButton {
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

            // Плитка: OCR
            CustomTabButton {
                text: "OCR"
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

            // Плитка: Окно
            CustomTabButton {
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

            // Плитка: Редактор задержек
            CustomTabButton {
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

    // Индикатор для плиток
    ButtonGroupWithIndicator {
        id: settingsTabIndicator
        buttons: [tilesRow.children[0], tilesRow.children[1], tilesRow.children[2],
                  tilesRow.children[3], tilesRow.children[4], tilesRow.children[5],
                  tilesRow.children[6], tilesRow.children[7]]
        leftInset: 10
        topInset: 10
        rightInset: 10
        bottomInset: 10
        setActiveCallback: function(activeButton) {
            for (var i = 0; i < tilesRow.children.length; i++) {
                tilesRow.children[i].isActive = false
            }
            activeButton.isActive = true
        }
        Component.onCompleted: {
            init()
            setActive(tilesRow.children[0])
        }
    }
}
