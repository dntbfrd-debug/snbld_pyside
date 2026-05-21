import QtQuick 2.15
import QtQuick.Controls.Basic 2.15
import QtQuick.Layouts 1.15
import Qt5Compat.GraphicalEffects

Item {
    id: root

    property var menuItems: []
    property var iconYPositions: []
    property string accentColor: "#7793a1"
    property string currentActiveButtonId: ""
    property int iconStripWidth: 56
    property int menuWidth: 220
    property int itemTopMargin: 15
    property int itemSpacing: 15
    property int itemHeight: 50
    property int submenuHeight: 110

    signal itemClicked(string pageFile)

    anchors.top: parent.top
    anchors.bottom: parent.bottom
    width: menuWidth
    x: -menuWidth
    opacity: 0
    z: 15

    property bool menuHovered: false
    property bool stripHovered: false
    property bool menuVisible: false
    property bool macrosSubmenuOpen: false
    property bool submenuLock: false
    property bool anyBtnHovered: false
    property real submenuOffset: _submenuAnimHeight
    property real _submenuAnimHeight: 0

    states: [
        State {
            name: "visible"
            when: root.menuVisible
            PropertyChanges { target: root; x: iconStripWidth; opacity: 1 }
        },
        State {
            name: "hidden"
            when: !root.menuVisible
            PropertyChanges { target: root; x: -menuWidth; opacity: 0 }
        }
    ]

    transitions: Transition {
        NumberAnimation { properties: "x,opacity"; duration: 200; easing.type: Easing.OutCubic }
    }

    // Фон меню — градиент + скруглённые углы + тень
    Rectangle {
        id: menuBg
        anchors.fill: parent
        radius: 12
        gradient: Gradient {
            GradientStop { position: 0.0;  color: Qt.rgba(0.18, 0.18, 0.18, 1) }
            GradientStop { position: 0.25; color: Qt.rgba(0.18, 0.18, 0.18, 1) }
            GradientStop { position: 0.5;  color: Qt.rgba(0.23, 0.23, 0.23, 1) }
            GradientStop { position: 0.75; color: Qt.rgba(0.18, 0.18, 0.18, 1) }
            GradientStop { position: 1.0;  color: Qt.rgba(0.18, 0.18, 0.18, 1) }
        }

        layer.enabled: true
        layer.effect: DropShadow {
            horizontalOffset: 8
            verticalOffset: 4
            radius: 16
            samples: 33
            color: "#a0000000"
        }
    }

    // MouseArea для удержания меню открытым (расширена на 15px влево для плавного перехода)
    MouseArea {
        id: menuHoverArea
        anchors.fill: parent
        anchors.leftMargin: -15
        hoverEnabled: true
        acceptedButtons: Qt.NoButton
        onEntered: { root.menuHovered = true; closeTimer.stop() }
        onExited: { root.menuHovered = false; updateCloseTimer() }
    }

    // Ловушка справа: если курсор уходит правее панели → закрыть (даже с submenuLock)
    MouseArea {
        anchors.left: parent.right
        anchors.top: parent.top
        anchors.bottom: parent.bottom
        width: 5
        hoverEnabled: true
        acceptedButtons: Qt.NoButton
        onEntered: root.forceClose()
    }

    function updateCloseTimer() {
        if (!stripHovered && !menuHovered && !anyBtnHovered) {
            closeTimer.restart()
        } else {
            closeTimer.stop()
        }
    }

    function _updateAnyBtnHovered() {
        var hov = macrosBtn.hovered
        if (!hov) { hov = subBtn1.hovered }
        if (!hov) { hov = subBtn2.hovered }
        if (!hov) {
            for (var i = 0; i < menuRepeater.count; i++) {
                var item = menuRepeater.itemAt(i)
                if (item && item.hovered) { hov = true; break }
            }
        }
        root.anyBtnHovered = hov
        updateCloseTimer()
    }

    Item {
        id: menuLayout
        anchors.fill: menuBg
        anchors.leftMargin: 15
        anchors.rightMargin: 15
        anchors.topMargin: root.itemTopMargin
        anchors.bottomMargin: root.itemTopMargin

        // Кнопка "Макросы"
        Button {
            id: macrosBtn
            y: 0
            anchors.left: parent.left
            anchors.right: parent.right
            height: root.itemHeight
            focusPolicy: Qt.NoFocus
            enabled: backend && backend.isActivated
            opacity: enabled ? 1.0 : 0.35
            Behavior on opacity { NumberAnimation { duration: 300 } }
            property bool isActive: root.currentActiveButtonId === "macros"
            property real hoverPulse: 0.0
            SequentialAnimation on hoverPulse {
                running: macrosBtn.hovered || macrosBtn.isActive
                loops: Animation.Infinite
                NumberAnimation { from: 0; to: Math.PI * 2; duration: 2500; easing.type: Easing.Linear }
            }
            function waveOpacity(base, layerIndex) {
                var wave = 0.6 + 0.4 * Math.sin(macrosBtn.hoverPulse + layerIndex * 0.6)
                return base * Math.max(0.4, wave)
            }
            Rectangle { anchors.centerIn: parent; width: parent.width + 40; height: parent.height + 40; radius: 28; color: root.accentColor; opacity: (macrosBtn.hovered || macrosBtn.isActive) ? macrosBtn.waveOpacity(0.02, 0) : 0.0; z: -1
                Behavior on opacity { NumberAnimation { duration: 300; easing.type: Easing.InOutQuad } } }
            Rectangle { anchors.centerIn: parent; width: parent.width + 35; height: parent.height + 35; radius: 25; color: root.accentColor; opacity: (macrosBtn.hovered || macrosBtn.isActive) ? macrosBtn.waveOpacity(0.04, 1) : 0.0; z: -1
                Behavior on opacity { NumberAnimation { duration: 350; easing.type: Easing.InOutQuad } } }
            Rectangle { anchors.centerIn: parent; width: parent.width + 30; height: parent.height + 30; radius: 23; color: root.accentColor; opacity: (macrosBtn.hovered || macrosBtn.isActive) ? macrosBtn.waveOpacity(0.06, 2) : 0.0; z: -1
                Behavior on opacity { NumberAnimation { duration: 400; easing.type: Easing.InOutQuad } } }
            Rectangle { anchors.centerIn: parent; width: parent.width + 25; height: parent.height + 25; radius: 20; color: root.accentColor; opacity: (macrosBtn.hovered || macrosBtn.isActive) ? macrosBtn.waveOpacity(0.09, 3) : 0.0; z: -1
                Behavior on opacity { NumberAnimation { duration: 450; easing.type: Easing.InOutQuad } } }
            Rectangle { anchors.centerIn: parent; width: parent.width + 20; height: parent.height + 20; radius: 18; color: root.accentColor; opacity: (macrosBtn.hovered || macrosBtn.isActive) ? macrosBtn.waveOpacity(0.13, 4) : 0.0; z: -1
                Behavior on opacity { NumberAnimation { duration: 500; easing.type: Easing.InOutQuad } } }
            Rectangle { anchors.centerIn: parent; width: parent.width + 15; height: parent.height + 15; radius: 15; color: root.accentColor; opacity: (macrosBtn.hovered || macrosBtn.isActive) ? macrosBtn.waveOpacity(0.18, 5) : 0.0; z: -1
                Behavior on opacity { NumberAnimation { duration: 550; easing.type: Easing.InOutQuad } } }
            Rectangle { anchors.centerIn: parent; width: parent.width + 10; height: parent.height + 10; radius: 13; color: root.accentColor; opacity: (macrosBtn.hovered || macrosBtn.isActive) ? macrosBtn.waveOpacity(0.25, 6) : 0.0; z: -1
                Behavior on opacity { NumberAnimation { duration: 600; easing.type: Easing.InOutQuad } } }
            Rectangle { anchors.centerIn: parent; width: parent.width + 6; height: parent.height + 6; radius: 11; color: root.accentColor; opacity: (macrosBtn.hovered || macrosBtn.isActive) ? macrosBtn.waveOpacity(0.35, 7) : 0.0; z: -1 }
            background: Rectangle {
                radius: 8
                color: macrosBtn.down ? "#2a1c1c1c" : macrosBtn.hovered ? "#cc262626" : "#a01c1c1c"
                border.color: "#70454545"
                border.width: 1
                Behavior on color { ColorAnimation { duration: 80; easing.type: Easing.InOutQuad } }
                Rectangle {
                    anchors.fill: parent; radius: parent.radius
                    gradient: Gradient {
                        GradientStop { position: 0.0; color: "#60000000" }
                        GradientStop { position: 0.35; color: "#30000000" }
                        GradientStop { position: 0.7; color: "#10000000" }
                        GradientStop { position: 1.0; color: "#00000000" }
                    }
                }
            }
            contentItem: Text {
                text: "Макросы"
                color: macrosBtn.hovered || macrosBtn.isActive ? "#ffffff" : "#a2a2a2"
                font.pointSize: 12
                horizontalAlignment: Text.AlignHCenter
                verticalAlignment: Text.AlignVCenter
            }
            onClicked: {
                root.macrosSubmenuOpen = !root.macrosSubmenuOpen
                root.submenuLock = true
                if (root.macrosSubmenuOpen) {
                    staggerEntryAnim.restart()
                } else {
                    staggerExitAnim.restart()
                }
            }
            onHoveredChanged: root._updateAnyBtnHovered()

            SequentialAnimation {
                id: staggerEntryAnim
                running: false
                ParallelAnimation {
                    NumberAnimation { target: root; property: "_submenuAnimHeight"; to: 65; duration: 280; easing.type: Easing.OutCubic }
                    NumberAnimation { target: subBtn1; property: "_entryOpacity"; to: 1; duration: 200 }
                    NumberAnimation { target: subBtn1; property: "_entryOffset"; to: 0; duration: 250; easing.type: Easing.OutCubic }
                }
                PauseAnimation { duration: 30 }
                ParallelAnimation {
                    NumberAnimation { target: root; property: "_submenuAnimHeight"; to: root.submenuHeight; duration: 280; easing.type: Easing.OutCubic }
                    NumberAnimation { target: subBtn2; property: "_entryOpacity"; to: 1; duration: 200 }
                    NumberAnimation { target: subBtn2; property: "_entryOffset"; to: 0; duration: 250; easing.type: Easing.OutCubic }
                }
            }

            ParallelAnimation {
                id: staggerExitAnim
                running: false
                NumberAnimation { target: subBtn1; property: "_entryOpacity"; to: 0; duration: 150 }
                NumberAnimation { target: subBtn1; property: "_entryOffset"; to: 20; duration: 200 }
                NumberAnimation { target: subBtn2; property: "_entryOpacity"; to: 0; duration: 150 }
                NumberAnimation { target: subBtn2; property: "_entryOffset"; to: 20; duration: 200 }
                NumberAnimation { target: root; property: "_submenuAnimHeight"; to: 0; duration: 250; easing.type: Easing.OutCubic }
            }
        }

        // Подменю макросов
        Item {
            id: macrosSubmenu
            anchors.left: parent.left
            anchors.right: parent.right
            y: root.itemHeight + root.itemSpacing
            height: root._submenuAnimHeight
            clip: false

            Column {
                anchors.fill: parent
                spacing: 5
                Item { width: parent.width; height: 10 }

                Button {
                    id: subBtn1
                    width: parent.width
                    height: 45
                    focusPolicy: Qt.NoFocus
                    enabled: backend && backend.isActivated
                    opacity: (enabled ? 1.0 : 0.35) * subBtn1._entryOpacity
                    property real _entryOpacity: 0
                    property real _entryOffset: 20
                    transform: Translate { y: subBtn1._entryOffset }
                    Behavior on _entryOpacity { NumberAnimation { duration: 220; easing.type: Easing.OutCubic } }
                    Behavior on _entryOffset { NumberAnimation { duration: 280; easing.type: Easing.OutCubic } }
                    property real hoverPulse: 0.0
                    SequentialAnimation on hoverPulse {
                        running: subBtn1.hovered
                        loops: Animation.Infinite
                        NumberAnimation { from: 0; to: Math.PI * 2; duration: 2500; easing.type: Easing.Linear }
                    }
                    function waveOpacity(base, layerIndex) {
                        var wave = 0.6 + 0.4 * Math.sin(subBtn1.hoverPulse + layerIndex * 0.6)
                        return base * Math.max(0.4, wave)
                    }
                    Rectangle { anchors.centerIn: parent; width: parent.width + 40; height: parent.height + 40; radius: 28; color: root.accentColor; opacity: subBtn1.hovered ? subBtn1.waveOpacity(0.02, 0) : 0.0; z: -1
                        Behavior on opacity { NumberAnimation { duration: 300; easing.type: Easing.InOutQuad } } }
                    Rectangle { anchors.centerIn: parent; width: parent.width + 35; height: parent.height + 35; radius: 25; color: root.accentColor; opacity: subBtn1.hovered ? subBtn1.waveOpacity(0.04, 1) : 0.0; z: -1
                        Behavior on opacity { NumberAnimation { duration: 350; easing.type: Easing.InOutQuad } } }
                    Rectangle { anchors.centerIn: parent; width: parent.width + 30; height: parent.height + 30; radius: 23; color: root.accentColor; opacity: subBtn1.hovered ? subBtn1.waveOpacity(0.06, 2) : 0.0; z: -1
                        Behavior on opacity { NumberAnimation { duration: 400; easing.type: Easing.InOutQuad } } }
                    Rectangle { anchors.centerIn: parent; width: parent.width + 25; height: parent.height + 25; radius: 20; color: root.accentColor; opacity: subBtn1.hovered ? subBtn1.waveOpacity(0.09, 3) : 0.0; z: -1
                        Behavior on opacity { NumberAnimation { duration: 450; easing.type: Easing.InOutQuad } } }
                    Rectangle { anchors.centerIn: parent; width: parent.width + 20; height: parent.height + 20; radius: 18; color: root.accentColor; opacity: subBtn1.hovered ? subBtn1.waveOpacity(0.13, 4) : 0.0; z: -1
                        Behavior on opacity { NumberAnimation { duration: 500; easing.type: Easing.InOutQuad } } }
                    Rectangle { anchors.centerIn: parent; width: parent.width + 15; height: parent.height + 15; radius: 15; color: root.accentColor; opacity: subBtn1.hovered ? subBtn1.waveOpacity(0.18, 5) : 0.0; z: -1
                        Behavior on opacity { NumberAnimation { duration: 550; easing.type: Easing.InOutQuad } } }
                    Rectangle { anchors.centerIn: parent; width: parent.width + 10; height: parent.height + 10; radius: 13; color: root.accentColor; opacity: subBtn1.hovered ? subBtn1.waveOpacity(0.25, 6) : 0.0; z: -1
                        Behavior on opacity { NumberAnimation { duration: 600; easing.type: Easing.InOutQuad } } }
                    Rectangle { anchors.centerIn: parent; width: parent.width + 6; height: parent.height + 6; radius: 11; color: root.accentColor; opacity: subBtn1.hovered ? subBtn1.waveOpacity(0.35, 7) : 0.0; z: -1 }
                background: Rectangle {
                    radius: 8
                    color: parent.down ? "#2a1c1c1c" : parent.hovered ? "#cc262626" : "#a01c1c1c"
                    border.color: "#70454545"
                    border.width: 1
                    Behavior on color { ColorAnimation { duration: 80; easing.type: Easing.InOutQuad } }
                    Rectangle {
                        anchors.fill: parent; radius: parent.radius
                        gradient: Gradient {
                            GradientStop { position: 0.0; color: "#60000000" }
                            GradientStop { position: 0.35; color: "#30000000" }
                            GradientStop { position: 0.7; color: "#10000000" }
                            GradientStop { position: 1.0; color: "#00000000" }
                        }
                    }
                }
                contentItem: Text {
                    text: "Список макросов"
                    color: parent.hovered ? "#ffffff" : "#a2a2a2"
                    font.pointSize: 10
                    horizontalAlignment: Text.AlignHCenter
                    verticalAlignment: Text.AlignVCenter
                }
                onHoveredChanged: root._updateAnyBtnHovered()
                onClicked: root.itemClicked("MacrosListPage.qml")
            }

            Button {
                id: subBtn2
                width: parent.width
                height: 45
                focusPolicy: Qt.NoFocus
                enabled: backend && backend.isActivated
                opacity: (enabled ? 1.0 : 0.35) * subBtn2._entryOpacity
                property real _entryOpacity: 0
                property real _entryOffset: 20
                transform: Translate { y: subBtn2._entryOffset }
                Behavior on _entryOpacity { NumberAnimation { duration: 220; easing.type: Easing.OutCubic } }
                Behavior on _entryOffset { NumberAnimation { duration: 280; easing.type: Easing.OutCubic } }
                property real hoverPulse: 0.0
                SequentialAnimation on hoverPulse {
                    running: subBtn2.hovered
                    loops: Animation.Infinite
                    NumberAnimation { from: 0; to: Math.PI * 2; duration: 2500; easing.type: Easing.Linear }
                }
                function waveOpacity(base, layerIndex) {
                    var wave = 0.6 + 0.4 * Math.sin(subBtn2.hoverPulse + layerIndex * 0.6)
                    return base * Math.max(0.4, wave)
                }
                Rectangle { anchors.centerIn: parent; width: parent.width + 40; height: parent.height + 40; radius: 28; color: root.accentColor; opacity: subBtn2.hovered ? subBtn2.waveOpacity(0.02, 0) : 0.0; z: -1
                    Behavior on opacity { NumberAnimation { duration: 300; easing.type: Easing.InOutQuad } } }
                Rectangle { anchors.centerIn: parent; width: parent.width + 35; height: parent.height + 35; radius: 25; color: root.accentColor; opacity: subBtn2.hovered ? subBtn2.waveOpacity(0.04, 1) : 0.0; z: -1
                    Behavior on opacity { NumberAnimation { duration: 350; easing.type: Easing.InOutQuad } } }
                Rectangle { anchors.centerIn: parent; width: parent.width + 30; height: parent.height + 30; radius: 23; color: root.accentColor; opacity: subBtn2.hovered ? subBtn2.waveOpacity(0.06, 2) : 0.0; z: -1
                    Behavior on opacity { NumberAnimation { duration: 400; easing.type: Easing.InOutQuad } } }
                Rectangle { anchors.centerIn: parent; width: parent.width + 25; height: parent.height + 25; radius: 20; color: root.accentColor; opacity: subBtn2.hovered ? subBtn2.waveOpacity(0.09, 3) : 0.0; z: -1
                    Behavior on opacity { NumberAnimation { duration: 450; easing.type: Easing.InOutQuad } } }
                Rectangle { anchors.centerIn: parent; width: parent.width + 20; height: parent.height + 20; radius: 18; color: root.accentColor; opacity: subBtn2.hovered ? subBtn2.waveOpacity(0.13, 4) : 0.0; z: -1
                    Behavior on opacity { NumberAnimation { duration: 500; easing.type: Easing.InOutQuad } } }
                Rectangle { anchors.centerIn: parent; width: parent.width + 15; height: parent.height + 15; radius: 15; color: root.accentColor; opacity: subBtn2.hovered ? subBtn2.waveOpacity(0.18, 5) : 0.0; z: -1
                    Behavior on opacity { NumberAnimation { duration: 550; easing.type: Easing.InOutQuad } } }
                Rectangle { anchors.centerIn: parent; width: parent.width + 10; height: parent.height + 10; radius: 13; color: root.accentColor; opacity: subBtn2.hovered ? subBtn2.waveOpacity(0.25, 6) : 0.0; z: -1
                    Behavior on opacity { NumberAnimation { duration: 600; easing.type: Easing.InOutQuad } } }
                Rectangle { anchors.centerIn: parent; width: parent.width + 6; height: parent.height + 6; radius: 11; color: root.accentColor; opacity: subBtn2.hovered ? subBtn2.waveOpacity(0.35, 7) : 0.0; z: -1 }
                background: Rectangle {
                    radius: 8
                    color: parent.down ? "#2a1c1c1c" : parent.hovered ? "#cc262626" : "#a01c1c1c"
                    border.color: "#70454545"
                    border.width: 1
                    Behavior on color { ColorAnimation { duration: 80; easing.type: Easing.InOutQuad } }
                    Rectangle {
                        anchors.fill: parent; radius: parent.radius
                        gradient: Gradient {
                            GradientStop { position: 0.0; color: "#60000000" }
                            GradientStop { position: 0.35; color: "#30000000" }
                            GradientStop { position: 0.7; color: "#10000000" }
                            GradientStop { position: 1.0; color: "#00000000" }
                        }
                    }
                }
                contentItem: Text {
                    text: "Создание"
                    color: parent.hovered ? "#ffffff" : "#a2a2a2"
                    font.pointSize: 10
                    horizontalAlignment: Text.AlignHCenter
                    verticalAlignment: Text.AlignVCenter
                }
                onHoveredChanged: root._updateAnyBtnHovered()
                onClicked: root.itemClicked("MacrosEditPage.qml")
            }
            }
        }

        // Остальные кнопки
        Column {
            id: belowCol
            x: 0
            y: root.itemHeight + root.itemSpacing + root._submenuAnimHeight + root.itemSpacing
            width: parent.width
            spacing: root.itemSpacing
            // y обновляется синхронно через _submenuAnimHeight — Behavior не нужен

            Repeater {
                id: menuRepeater
                model: [
                    { btnId: "settings", text: "Настройки", pageFile: "SettingsMainPage.qml" },
                    { btnId: "profiles", text: "Профили", pageFile: "ProfilesPage.qml" },
                    { btnId: "subscription", text: "Подписка", pageFile: "SubscriptionPage.qml" },
                    { btnId: "help", text: "Помощь", pageFile: "HelpPage.qml" },
                    { btnId: "debug", text: "Диагностика", pageFile: "DebugPage.qml" }
                ]

                Button {
                    id: menuBtn
                    width: parent.width
                    height: root.itemHeight
                    focusPolicy: Qt.NoFocus
                    enabled: modelData.btnId === "subscription" || modelData.btnId === "help" || modelData.btnId === "debug" || (backend && backend.isActivated)
                    opacity: enabled ? 1.0 : 0.35
                    Behavior on opacity { NumberAnimation { duration: 300 } }
                    property bool isActive: root.currentActiveButtonId === modelData.btnId
                    property real hoverPulse: 0.0
                    SequentialAnimation on hoverPulse {
                        running: menuBtn.hovered || menuBtn.isActive
                        loops: Animation.Infinite
                        NumberAnimation { from: 0; to: Math.PI * 2; duration: 2500; easing.type: Easing.Linear }
                    }
                    function waveOpacity(base, layerIndex) {
                        var wave = 0.6 + 0.4 * Math.sin(menuBtn.hoverPulse + layerIndex * 0.6)
                        return base * Math.max(0.4, wave)
                    }
                    Rectangle { anchors.centerIn: parent; width: parent.width + 40; height: parent.height + 40; radius: 28; color: root.accentColor; opacity: (menuBtn.hovered || menuBtn.isActive) ? menuBtn.waveOpacity(0.02, 0) : 0.0; z: -1
                        Behavior on opacity { NumberAnimation { duration: 300; easing.type: Easing.InOutQuad } } }
                    Rectangle { anchors.centerIn: parent; width: parent.width + 35; height: parent.height + 35; radius: 25; color: root.accentColor; opacity: (menuBtn.hovered || menuBtn.isActive) ? menuBtn.waveOpacity(0.04, 1) : 0.0; z: -1
                        Behavior on opacity { NumberAnimation { duration: 350; easing.type: Easing.InOutQuad } } }
                    Rectangle { anchors.centerIn: parent; width: parent.width + 30; height: parent.height + 30; radius: 23; color: root.accentColor; opacity: (menuBtn.hovered || menuBtn.isActive) ? menuBtn.waveOpacity(0.06, 2) : 0.0; z: -1
                        Behavior on opacity { NumberAnimation { duration: 400; easing.type: Easing.InOutQuad } } }
                    Rectangle { anchors.centerIn: parent; width: parent.width + 25; height: parent.height + 25; radius: 20; color: root.accentColor; opacity: (menuBtn.hovered || menuBtn.isActive) ? menuBtn.waveOpacity(0.09, 3) : 0.0; z: -1
                        Behavior on opacity { NumberAnimation { duration: 450; easing.type: Easing.InOutQuad } } }
                    Rectangle { anchors.centerIn: parent; width: parent.width + 20; height: parent.height + 20; radius: 18; color: root.accentColor; opacity: (menuBtn.hovered || menuBtn.isActive) ? menuBtn.waveOpacity(0.13, 4) : 0.0; z: -1
                        Behavior on opacity { NumberAnimation { duration: 500; easing.type: Easing.InOutQuad } } }
                    Rectangle { anchors.centerIn: parent; width: parent.width + 15; height: parent.height + 15; radius: 15; color: root.accentColor; opacity: (menuBtn.hovered || menuBtn.isActive) ? menuBtn.waveOpacity(0.18, 5) : 0.0; z: -1
                        Behavior on opacity { NumberAnimation { duration: 550; easing.type: Easing.InOutQuad } } }
                    Rectangle { anchors.centerIn: parent; width: parent.width + 10; height: parent.height + 10; radius: 13; color: root.accentColor; opacity: (menuBtn.hovered || menuBtn.isActive) ? menuBtn.waveOpacity(0.25, 6) : 0.0; z: -1
                        Behavior on opacity { NumberAnimation { duration: 600; easing.type: Easing.InOutQuad } } }
                    Rectangle { anchors.centerIn: parent; width: parent.width + 6; height: parent.height + 6; radius: 11; color: root.accentColor; opacity: (menuBtn.hovered || menuBtn.isActive) ? menuBtn.waveOpacity(0.35, 7) : 0.0; z: -1 }
                    background: Rectangle {
                        radius: 8
                        color: menuBtn.down ? "#2a1c1c1c" : menuBtn.hovered ? "#cc262626" : "#a01c1c1c"
                        border.color: "#70454545"
                        border.width: 1
                        Behavior on color { ColorAnimation { duration: 80; easing.type: Easing.InOutQuad } }
                        Rectangle {
                            anchors.fill: parent; radius: parent.radius
                            gradient: Gradient {
                                GradientStop { position: 0.0; color: "#60000000" }
                                GradientStop { position: 0.35; color: "#30000000" }
                                GradientStop { position: 0.7; color: "#10000000" }
                                GradientStop { position: 1.0; color: "#00000000" }
                            }
                        }
                    }
                    contentItem: Text {
                        text: modelData.text
                        color: menuBtn.hovered || menuBtn.isActive ? "#ffffff" : "#a2a2a2"
                        font.pointSize: 12
                        horizontalAlignment: Text.AlignHCenter
                        verticalAlignment: Text.AlignVCenter
                    }
                    onHoveredChanged: root._updateAnyBtnHovered()
                    onClicked: root.itemClicked(modelData.pageFile)
                }
            }
        }
    }

    // Мгновенное переключение активной кнопки (isActive реактивно через currentActiveButtonId)
    function setActiveById(btnId) {
        // isActive обновляется автоматически через привязку к root.currentActiveButtonId
    }

    // Логика закрытия с задержкой для плавности
    Timer {
        id: closeTimer
        interval: 300
        onTriggered: {
            if (!root.stripHovered && !root.menuHovered && !root.anyBtnHovered && !root.submenuLock) {
                root.menuVisible = false
                root.submenuLock = false
                if (root.macrosSubmenuOpen) {
                    root.macrosSubmenuOpen = false
                    staggerExitAnim.restart()
                }
            }
        }
    }

    function onStripHoverChanged(isHovered) {
        root.stripHovered = isHovered
        if (isHovered) {
            closeTimer.stop()
            root.menuVisible = true
        } else {
            updateCloseTimer()
        }
    }

    function forceClose() {
        closeTimer.stop()
        root.submenuLock = false
        root.menuVisible = false
        if (root.macrosSubmenuOpen) {
            root.macrosSubmenuOpen = false
            staggerExitAnim.restart()
        }
    }

    Keys.onEscapePressed: {
        if (root.menuVisible) {
            root.forceClose()
        }
    }

    onMenuVisibleChanged: {
        focus = root.menuVisible
    }
}
