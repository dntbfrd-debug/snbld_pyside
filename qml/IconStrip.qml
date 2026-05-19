import QtQuick 2.15
import QtQuick.Controls.Basic 2.15
import QtQuick.Layouts 1.15
import Qt5Compat.GraphicalEffects

Item {
    id: root

    property var menuItems: []
    property int iconSize: 28
    property int stripWidth: 52
    property int itemTopMargin: 15
    property int itemSpacing: 15
    property int itemHeight: 50
    property color stripColor: "#2a2a2a"
    property color accentColor: "#7793a1"
    property string currentActiveButtonId: ""
    property real submenuOffset: 0

    // --- Каскадная анимация ---
    property string _activeId: ""
    property int _cascadeFromIdx: -1
    property int _cascadeToIdx: -1
    property int _cascadeCurIdx: -1
    property int _cascadeDir: 0
    property bool _cascading: false
    property bool _cascadeReady: false

    Component.onCompleted: {
        root._activeId = root.currentActiveButtonId
        root._cascadeReady = true
    }

    onCurrentActiveButtonIdChanged: {
        if (!root._cascadeReady) return
        if (root.currentActiveButtonId === root._activeId) return
        _startCascade(root._activeId, root.currentActiveButtonId)
    }

    Timer {
        id: cascadeTimer
        interval: 80
        repeat: false
        onTriggered: {
            if (!root._cascading) return
            var ids = ["macros", "settings", "profiles", "subscription", "help", "debug"]
            root._cascadeCurIdx += root._cascadeDir
            root._activeId = ids[root._cascadeCurIdx]
            if (root._cascadeCurIdx !== root._cascadeToIdx) {
                cascadeTimer.start()
            } else {
                root._cascading = false
            }
        }
    }

    function _startCascade(fromId, toId) {
        var ids = ["macros", "settings", "profiles", "subscription", "help", "debug"]
        root._cascadeFromIdx = ids.indexOf(fromId)
        root._cascadeToIdx = ids.indexOf(toId)
        if (root._cascadeFromIdx < 0 || root._cascadeToIdx < 0) {
            root._activeId = toId
            return
        }
        if (root._cascadeFromIdx === root._cascadeToIdx) return
        root._cascadeDir = root._cascadeToIdx > root._cascadeFromIdx ? 1 : -1
        root._cascadeCurIdx = root._cascadeFromIdx
        root._cascading = true
        cascadeTimer.start()
    }

    signal showMenu(bool show)

    width: stripWidth
    height: parent ? parent.height : 600

    DropShadow {
        id: stripShadow
        anchors.fill: stripBg
        horizontalOffset: 8
        verticalOffset: 0
        radius: 16
        samples: 33
        color: "#a0000000"
        source: stripBg
        z: -1
    }

    Rectangle {
        id: stripBg
        anchors.fill: parent
        radius: 12
        color: root.stripColor
        z: 0
    }

    Item {
        anchors.fill: parent
        clip: true

        ColumnLayout {
            id: iconColumn
            anchors.left: parent.left
            anchors.right: parent.right
            anchors.leftMargin: 8
            anchors.rightMargin: 8
            spacing: root.itemSpacing

            // === Кнопка "Макросы" ===
            Item {
                id: macrosIcon
                Layout.fillWidth: true
                Layout.preferredHeight: root.itemHeight
                Layout.topMargin: root.itemTopMargin

                property bool isActive: root._activeId === "macros"

                Rectangle {
                    anchors.fill: parent
                    radius: 10
                    color: root.accentColor
                    opacity: parent.isActive ? 0.2 : 0.0
                    border.color: parent.isActive ? root.accentColor : "transparent"
                    border.width: parent.isActive ? 2 : 0
                    Behavior on opacity { NumberAnimation { duration: 200 } }
                    Behavior on border.color { ColorAnimation { duration: 200 } }
                }
                Image {
                    anchors.centerIn: parent
                    width: root.iconSize
                    height: root.iconSize
                    source: "../icons/macros.png"
                    fillMode: Image.PreserveAspectFit
                    opacity: parent.isActive ? 1.0 : (backend && backend.isActivated ? 0.7 : 0.35)
                    Behavior on opacity { NumberAnimation { duration: 200 } }
                }
            }

            Item {
                Layout.fillWidth: true
                Layout.preferredHeight: root.submenuOffset
                visible: root.submenuOffset > 0
                clip: true

                Rectangle {
                    width: 4; height: 4; radius: 2
                    color: root.accentColor
                    opacity: 0.5
                    anchors.horizontalCenter: parent.horizontalCenter
                    y: 10 + 45 / 2 - 2
                }
                Rectangle {
                    width: 4; height: 4; radius: 2
                    color: root.accentColor
                    opacity: 0.5
                    anchors.horizontalCenter: parent.horizontalCenter
                    y: 10 + 45 + 5 + 45 / 2 - 2
                }
            }

            Repeater {
                id: iconRepeater
                model: [
                    { btnId: "settings", icon: "../icons/settings.png" },
                    { btnId: "profiles", icon: "../icons/profiles.png" },
                    { btnId: "subscription", icon: "../icons/subscription.png" },
                    { btnId: "help", icon: "../icons/help.png" },
                    { btnId: "debug", icon: "../icons/calibrate.png" }
                ]

                delegate: Item {
                    Layout.fillWidth: true
                    Layout.preferredHeight: root.itemHeight

                    property bool isActive: root._activeId === modelData.btnId
                    property bool _blocked: modelData.btnId !== "subscription" && modelData.btnId !== "help" && modelData.btnId !== "debug" && (!backend || !backend.isActivated)

                    Rectangle {
                        anchors.fill: parent
                        radius: 10
                        color: root.accentColor
                        opacity: parent.isActive ? 0.2 : 0.0
                        border.color: parent.isActive ? root.accentColor : "transparent"
                        border.width: parent.isActive ? 2 : 0
                        Behavior on opacity { NumberAnimation { duration: 200 } }
                        Behavior on border.color { ColorAnimation { duration: 200 } }
                    }
                    Image {
                        anchors.centerIn: parent
                        width: root.iconSize
                        height: root.iconSize
                        source: modelData.icon
                        fillMode: Image.PreserveAspectFit
                        opacity: parent.isActive ? 1.0 : (parent._blocked ? 0.35 : 0.7)
                        Behavior on opacity { NumberAnimation { duration: 200 } }
                    }
                }
            }

            Item { Layout.fillWidth: true; Layout.preferredHeight: root.itemTopMargin }
            Item { Layout.fillHeight: true }
        }
    }

    // MouseArea на всю полоску — с задержкой для плавного показа
    MouseArea {
        anchors.fill: parent
        hoverEnabled: true
        acceptedButtons: Qt.NoButton
        z: 2
        onEntered: { showTimer.start() }
        onExited: {
            showTimer.stop()
            root.showMenu(false)
        }

        Timer {
            id: showTimer
            interval: 80
            onTriggered: { root.showMenu(true) }
        }
    }
}
