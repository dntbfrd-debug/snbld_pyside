import QtQuick 2.15
import QtQuick.Controls.Basic 2.15
import QtQuick.Layouts 1.15
import QtMultimedia 5.15
import Qt5Compat.GraphicalEffects
import "components"

ApplicationWindow {
    id: root

    FontLoader { id: mainFont; source: "../fonts/Rubik.ttf" }
    FontLoader { id: firaCodeFont; source: "../fonts/FiraCode-Regular.ttf" }
    font.family: "Rubik"
    width: 1300
    height: 700
    minimumWidth: 400
    minimumHeight: 300
    visible: true
    title: "snbld resvap"
    color: "#151515"
    flags: Qt.FramelessWindowHint | Qt.Window
    // Иконка устанавливается программно в qml_main.py

    // Закруглённые края окна
    property int windowRadius: 12
    // Ширина левой полосы с иконками
    property int iconStripWidth: 52

    // Получаем акцентный цвет
    property string accentColor: backend && backend.settings && backend.settings.accent_color !== undefined && backend.settings.accent_color !== null ? backend.settings.accent_color : "#7793a1"
    property Item backgroundSource: rightColumnBackground

    // Убираем titleTextColor — используем градиент titleBar

    property string currentActiveButtonId: "help"
    property bool submenuVisible: false

    // Функции для работы с подменю (должны быть определены ДО использования)
    function openSubmenu() {
        submenuVisible = true
    }

    function closeSubmenu() {
        submenuVisible = false
    }

    function changeActivePage(pageFile) {
        closeSubmenu()
        slideMenu.forceClose()
        if (pageFile === "SettingsPage.qml" || pageFile === "SettingsMainPage.qml") {
            stackView.replace("SettingsMainPage.qml")
            currentActiveButtonId = "settings"
            slideMenu.setActiveById("settings")
        } else if (pageFile === "SettingsAppearancePage.qml") {
            stackView.replace("SettingsAppearancePage.qml")
        } else if (pageFile === "MacrosListPage.qml") {
            currentActiveButtonId = "macros"
            slideMenu.setActiveById("macros")
            stackView.replace("MacrosListPage.qml")
        } else if (pageFile === "MacrosEditPage.qml") {
            currentActiveButtonId = "macros"
            slideMenu.setActiveById("macros")
            stackView.replace("MacrosEditPage.qml")
        } else if (pageFile === "EditSimplePage.qml" || pageFile === "EditZonePage.qml" || pageFile === "EditSkillPage.qml" || pageFile === "EditBuffPage.qml") {
            // EditXxxPage открывается напрямую с уже установленным editingMacro из backend
            currentActiveButtonId = "macros"
            slideMenu.setActiveById("macros")
            var editProps = {}
            if (backend && backend.macro_for_edit && backend.macro_for_edit.name) {
                editProps.editingMacro = backend.macro_for_edit
            }
            if (backend) backend.qmlLog("changeActivePage EditXxxPage, editProps.keys=" + JSON.stringify(Object.keys(editProps)) + ", macro_for_edit=" + (backend.macro_for_edit ? JSON.stringify(backend.macro_for_edit) : "null"))
            stackView.replace("MacrosEditPage.qml", editProps)
            return
        } else if (pageFile === "MacrosEditPage.qml") {
            currentActiveButtonId = "macros"
            slideMenu.setActiveById("macros")
            var editProps2 = {}
            if (backend && backend.macro_for_edit && backend.macro_for_edit.name) {
                editProps2.editingMacro = backend.macro_for_edit
            }
            if (backend) backend.qmlLog("changeActivePage MacrosEditPage, editProps.keys=" + JSON.stringify(Object.keys(editProps2)) + ", macro_for_edit=" + (backend.macro_for_edit ? JSON.stringify(backend.macro_for_edit) : "null"))
            stackView.replace("MacrosEditPage.qml", editProps2)
            return
        } else if (pageFile === "BuffListPage.qml" || pageFile === "BuffEditForm.qml") {
            pageFile = "MacrosEditPage.qml"
        } else if (pageFile === "ProfilesPage.qml") {
            currentActiveButtonId = "profiles"
            slideMenu.setActiveById("profiles")
            stackView.replace(pageFile)
        } else if (pageFile === "SubscriptionPage.qml") {
            currentActiveButtonId = "subscription"
            slideMenu.setActiveById("subscription")
            stackView.replace(pageFile)
        } else if (pageFile === "HelpPage.qml") {
            currentActiveButtonId = "help"
            slideMenu.setActiveById("help")
            stackView.replace(pageFile)
        } else if (pageFile === "DebugPage.qml") {
            currentActiveButtonId = "debug"
            slideMenu.setActiveById("debug")
            stackView.replace(pageFile)
        }
    }

    // Обновление цветов при изменении настроек
    Connections {
        target: backend
        function onSettingsChanged() {
            root.accentColor = backend.settings.accent_color !== undefined && backend.settings.accent_color !== null ? backend.settings.accent_color : "#7793a1"
        }
    }

    // Обёртка окна с закруглёнными краями
    Rectangle {
        id: windowFrame
        anchors.fill: parent
        radius: root.windowRadius
        color: "#151515"
        // clip: true удалён — чтобы не обрезать IconStrip. Клиппинг только на rightColumnBackground

        // Правая колонка: видео/градиент на всю высоту окна (включая заголовок)
        Item {
            id: rightColumnBackground
            clip: true
            anchors.left: parent.left
            anchors.leftMargin: root.iconStripWidth
            anchors.top: parent.top
            anchors.bottom: parent.bottom
            anchors.right: parent.right
            z: 0

            Video {
                id: backgroundVideo
                anchors.fill: parent
                source: backend ? backend.backgroundVideoUrl : ""
                fillMode: 0  // Stretch
                muted: true
                loops: -1
                z: 0
                Component.onCompleted: {
                    if (backend && backend.backgroundVideoUrl !== "") {
                        play()
                    }
                }
            }

            Rectangle {
                anchors.fill: parent
                visible: !backgroundVideo.visible || (backend && backend.backgroundVideoUrl === "")
                gradient: Gradient {
                    GradientStop { position: 0.0; color: "#1a1a2e" }
                    GradientStop { position: 0.5; color: "#16213e" }
                    GradientStop { position: 1.0; color: "#0f3460" }
                }
                z: 0
            }
        }

        // Тень на границе полосы/контента — удалена, используем DropShadow из IconStrip

        Item {
            id: titleBar
            anchors.left: parent.left
            anchors.leftMargin: root.iconStripWidth
            anchors.right: parent.right
            anchors.top: parent.top
            height: 40
            z: 10

            RowLayout {
                id: titleBarRow
                anchors.fill: parent
                spacing: 0

                Rectangle {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    color: "transparent"
                }
            }

            MouseArea {
                anchors.fill: parent
                onPressed: root.startSystemMove()
            }

            Row {
                anchors.right: parent.right
                anchors.rightMargin: 12
                anchors.verticalCenter: parent.verticalCenter
                spacing: 8
                Button {
                    id: startAllBtn
                    implicitWidth: 90
                    implicitHeight: 32
                    focusPolicy: Qt.NoFocus
                    property bool isActive: (backend && !backend.global_stopped)
                    background: Rectangle {
                        radius: 6
                        border.color: "#70454545"
                        border.width: 1
                        color: "#a01c1c1c"
                        Rectangle {
                            anchors.fill: parent
                            radius: parent.radius
                            color: "#4CAF50"
                            opacity: startAllBtn.isActive ? 0.25 : 0.0
                            border.color: startAllBtn.isActive ? "#4CAF50" : "transparent"
                            border.width: startAllBtn.isActive ? 2 : 0
                            Behavior on opacity { NumberAnimation { duration: 200 } }
                            Behavior on border.color { ColorAnimation { duration: 200 } }
                        }
                        Rectangle {
                            anchors.fill: parent
                            radius: parent.radius
                            color: "#cc262626"
                            opacity: startAllBtn.hovered ? 1.0 : 0.0
                            Behavior on opacity { NumberAnimation { duration: 150 } }
                            z: -1
                        }
                    }
                    contentItem: Item {
                        Row {
                            spacing: 6
                            anchors.centerIn: parent
                            anchors.horizontalCenterOffset: -6
                            Image {
                                source: "../icons/play.png"
                                width: 16
                                height: 16
                                sourceSize.width: 16
                                sourceSize.height: 16
                                fillMode: Image.PreserveAspectFit
                                anchors.verticalCenter: parent.verticalCenter
                            }
                            Text {
                                text: "Старт"
                                color: startAllBtn.isActive ? "#ffffff" : "#a2a2a2"
                                font.pointSize: 11
                                Behavior on color { ColorAnimation { duration: 200 } }
                            }
                        }
                    }
                    enabled: backend && backend.isActivated
                    onClicked: { if (!enabled) return; backend.start_all_macros() }
                }
                Button {
                    id: stopAllBtn
                    implicitWidth: 90
                    implicitHeight: 32
                    focusPolicy: Qt.NoFocus
                    property bool isActive: (backend && backend.global_stopped)
                    background: Rectangle {
                        radius: 6
                        border.color: "#70454545"
                        border.width: 1
                        color: "#a01c1c1c"
                        Rectangle {
                            anchors.fill: parent
                            radius: parent.radius
                            color: "#F44336"
                            opacity: stopAllBtn.isActive ? 0.25 : 0.0
                            border.color: stopAllBtn.isActive ? "#F44336" : "transparent"
                            border.width: stopAllBtn.isActive ? 2 : 0
                            Behavior on opacity { NumberAnimation { duration: 200 } }
                            Behavior on border.color { ColorAnimation { duration: 200 } }
                        }
                        Rectangle {
                            anchors.fill: parent
                            radius: parent.radius
                            color: "#cc262626"
                            opacity: stopAllBtn.hovered ? 1.0 : 0.0
                            Behavior on opacity { NumberAnimation { duration: 150 } }
                            z: -1
                        }
                    }
                    contentItem: Item {
                        Row {
                            spacing: 6
                            anchors.centerIn: parent
                            anchors.horizontalCenterOffset: -6
                            Image {
                                source: "../icons/stop.png"
                                width: 16
                                height: 16
                                sourceSize.width: 16
                                sourceSize.height: 16
                                fillMode: Image.PreserveAspectFit
                                anchors.verticalCenter: parent.verticalCenter
                            }
                            Text {
                                text: "Стоп"
                                color: stopAllBtn.isActive ? "#ffffff" : "#a2a2a2"
                                font.pointSize: 11
                                Behavior on color { ColorAnimation { duration: 200 } }
                            }
                        }
                    }
                    enabled: backend && backend.isActivated
                    onClicked: { if (!enabled) return; backend.stop_all_macros() }
                }
                Item { width: 4; height: 1 }
                Button {
                    id: minimizeButton
                    width: 30
                    height: 30
                    text: "_"
                    background: Rectangle { color: minimizeButton.hovered ? "#3a3a3a" : "#252525"; radius: 4 }
                    contentItem: Text { text: parent.text; color: "#909090"; horizontalAlignment: Text.AlignHCenter; verticalAlignment: Text.AlignVCenter; font.pixelSize: 14 }
                    onClicked: backend.minimizeWindow()
                }
                Button {
                    id: closeButton
                    width: 30
                    height: 30
                    text: "X"
                    background: Rectangle { color: closeButton.hovered ? "#e81123" : "#252525"; radius: 4 }
                    contentItem: Text { text: parent.text; color: "#909090"; horizontalAlignment: Text.AlignHCenter; verticalAlignment: Text.AlignVCenter; font.pixelSize: 12 }
                    onClicked: backend.closeWindow()
                }
            }
        }

    // Вертикальная полоса с иконками — на всю высоту окна
    IconStrip {
        id: iconStrip
        anchors.left: parent.left
        anchors.top: parent.top
        anchors.bottom: parent.bottom
        z: 20
        accentColor: root.accentColor
        currentActiveButtonId: root.currentActiveButtonId

        menuItems: [
            {
                btnId: "macros",
                text: "Макросы",
                icon: "../icons/macros.png",
                pageFile: "MacrosListPage.qml",
                hasSubmenu: true,
                submenuItems: [
                    { text: "Список макросов", pageFile: "MacrosListPage.qml" },
                    { text: "Создание", pageFile: "MacrosEditPage.qml" }
                ]
            },
            {
                btnId: "settings",
                text: "Настройки",
                icon: "../icons/settings.png",
                pageFile: "SettingsMainPage.qml",
                hasSubmenu: false
            },
            {
                btnId: "profiles",
                text: "Профили",
                icon: "../icons/profiles.png",
                pageFile: "ProfilesPage.qml",
                hasSubmenu: false
            },
            {
                btnId: "subscription",
                text: "Подписка",
                icon: "../icons/subscription.png",
                pageFile: "SubscriptionPage.qml",
                hasSubmenu: false
            },
            {
                btnId: "help",
                text: "Помощь",
                icon: "../icons/help.png",
                pageFile: "HelpPage.qml",
                hasSubmenu: false
            },
            {
                btnId: "debug",
                text: "Диагностика",
                icon: "../icons/calibrate.png",
                pageFile: "DebugPage.qml",
                hasSubmenu: false
            }
        ]

        onShowMenu: function(show) {
            slideMenu.onStripHoverChanged(show)
        }
    }

    // Выезжающее меню
    SlideMenu {
        id: slideMenu
        anchors.top: parent.top
        anchors.bottom: parent.bottom
        z: 15
        accentColor: root.accentColor
        currentActiveButtonId: root.currentActiveButtonId
        iconStripWidth: root.iconStripWidth
        iconYPositions: iconStrip.iconYPositions

        menuItems: [
            { btnId: "macros", text: "Макросы", pageFile: "MacrosListPage.qml" },
            { btnId: "settings", text: "Настройки", pageFile: "SettingsMainPage.qml" },
            { btnId: "profiles", text: "Профили", pageFile: "ProfilesPage.qml" },
            { btnId: "subscription", text: "Подписка", pageFile: "SubscriptionPage.qml" },
            { btnId: "help", text: "Помощь", pageFile: "HelpPage.qml" },
            { btnId: "debug", text: "Диагностика", pageFile: "DebugPage.qml" }
        ]

        onItemClicked: function(pageFile) {
            changeActivePage(pageFile)
        }
    }

    Binding {
        target: iconStrip
        property: "submenuOffset"
        value: slideMenu.submenuOffset
    }

    Item {
        id: contentArea
        objectName: "contentArea"
        anchors.top: titleBar.bottom
        anchors.left: parent.left
        anchors.leftMargin: root.iconStripWidth
        anchors.right: parent.right
        anchors.bottom: parent.bottom
        z: 1

        // StackView
        StackView {
            id: stackView
            anchors.left: parent.left
            anchors.leftMargin: root.iconStripWidth
            anchors.right: parent.right
            anchors.rightMargin: root.iconStripWidth
            anchors.top: parent.top
            anchors.bottom: parent.bottom
            initialItem: "HelpPage.qml"
            clip: false
            background: null
            z: 1
            pushEnter: Transition {
                PropertyAnimation { property: "x"; from: stackView.width; to: 0; duration: 300; easing.type: Easing.OutCubic }
                PropertyAnimation { property: "opacity"; from: 0; to: 1; duration: 300; easing.type: Easing.OutCubic }
            }
            pushExit: Transition {
                PropertyAnimation { property: "x"; from: 0; to: -stackView.width * 0.5; duration: 300; easing.type: Easing.InCubic }
                PropertyAnimation { property: "opacity"; from: 1; to: 0; duration: 300; easing.type: Easing.InCubic }
            }
            popEnter: Transition {
                PropertyAnimation { property: "x"; from: -stackView.width * 0.5; to: 0; duration: 300; easing.type: Easing.OutCubic }
                PropertyAnimation { property: "opacity"; from: 0; to: 1; duration: 300; easing.type: Easing.OutCubic }
            }
            popExit: Transition {
                PropertyAnimation { property: "x"; from: 0; to: stackView.width; duration: 300; easing.type: Easing.InCubic }
                PropertyAnimation { property: "opacity"; from: 1; to: 0; duration: 300; easing.type: Easing.InCubic }
            }
            replaceEnter: Transition {
                PropertyAnimation { property: "x"; from: stackView.width; to: 0; duration: 300; easing.type: Easing.OutCubic }
                PropertyAnimation { property: "opacity"; from: 0; to: 1; duration: 300; easing.type: Easing.OutCubic }
            }
            replaceExit: Transition {
                PropertyAnimation { property: "x"; from: 0; to: -stackView.width; duration: 300; easing.type: Easing.InCubic }
                PropertyAnimation { property: "opacity"; from: 1; to: 0; duration: 300; easing.type: Easing.InCubic }
            }
        }
    }



    ButtonGroupWithIndicator {
        id: actionButtonsIndicator
        buttons: [startAllBtn, stopAllBtn]
        setActiveCallback: function(activeButton) {
            startAllBtn.isActive = false
            stopAllBtn.isActive = false
            activeButton.isActive = true
        }
        Component.onCompleted: {
            init()
            setActive(stopAllBtn)
        }
        
        // Реакция на изменение global_stopped через Connections
        Connections {
            target: backend
            function onGlobalStoppedChanged() {
                var stopped = backend.global_stopped
                console.log("[QML] global_stopped =", stopped)
                startAllBtn.isActive = !stopped
                stopAllBtn.isActive = stopped
            }
        }
        
        // Реакция на нажатие кнопок старт/стоп
        Connections {
            target: backend
            // Обновление статуса макросов (когда макрос запущен по горячей клавише)
            function onMacroStatusChanged() {
                // Список макросов обновляется внутри MacrosListPage.qml
            }
        }
    }

    // Уведомление (справа снизу) с анимированной рамкой и градиентом
    Popup {
        id: notificationPopup
        x: parent.width - width - 20
        y: parent.height - height - 20
        width: 320
        height: 60
        padding: 0
        background: Rectangle {
            color: "#a01c1c1c"
            radius: 10
            border.color: "#70454545"
            border.width: 1

            Rectangle {
                anchors.fill: parent
                radius: parent.radius
                gradient: Gradient {
                    GradientStop { position: 0.0; color: "#60000000" }
                    GradientStop { position: 0.35; color: "#30000000" }
                    GradientStop { position: 0.7; color: "#10000000" }
                    GradientStop { position: 1.0; color: "#00000000" }
                }
            }
            
            // Анимированная рамка с акцентным цветом (как у активной плитки)
            Rectangle {
                id: notificationBorder
                anchors.fill: parent
                color: "transparent"
                radius: 10
                border.width: 0
                z: 1
                
                property color accentColor: backend && backend.settings && backend.settings.accent_color ? backend.settings.accent_color : "#7793a1"

                // Переливчатая анимация свечения уведомления
                property real shimmerPhase: 0.0
                SequentialAnimation on shimmerPhase {
                    running: notificationPopup.visible
                    loops: Animation.Infinite
                    NumberAnimation { from: 0; to: Math.PI * 2; duration: 3000; easing.type: Easing.Linear }
                }

                function waveOpacity(base, idx) {
                    var wave = 0.5 + 0.5 * Math.sin(notificationBorder.shimmerPhase + idx * 0.8)
                    return base * Math.max(0.5, wave)
                }

                // 8 слоёв свечения рамки с переливом
                Rectangle {
                    anchors.centerIn: parent
                    width: parent.width + 40
                    height: parent.height + 40
                    radius: 10 + 20
                    color: Qt.rgba(notificationBorder.accentColor.r, notificationBorder.accentColor.g, notificationBorder.accentColor.b, notificationBorder.waveOpacity(0.01, 0))
                    z: 0
                }
                Rectangle {
                    anchors.centerIn: parent
                    width: parent.width + 35
                    height: parent.height + 35
                    radius: 10 + 17
                    color: Qt.rgba(notificationBorder.accentColor.r, notificationBorder.accentColor.g, notificationBorder.accentColor.b, notificationBorder.waveOpacity(0.02, 1))
                    z: 0
                }
                Rectangle {
                    anchors.centerIn: parent
                    width: parent.width + 30
                    height: parent.height + 30
                    radius: 10 + 15
                    color: Qt.rgba(notificationBorder.accentColor.r, notificationBorder.accentColor.g, notificationBorder.accentColor.b, notificationBorder.waveOpacity(0.035, 2))
                    z: 0
                }
                Rectangle {
                    anchors.centerIn: parent
                    width: parent.width + 25
                    height: parent.height + 25
                    radius: 10 + 12
                    color: Qt.rgba(notificationBorder.accentColor.r, notificationBorder.accentColor.g, notificationBorder.accentColor.b, notificationBorder.waveOpacity(0.05, 3))
                    z: 0
                }
                Rectangle {
                    anchors.centerIn: parent
                    width: parent.width + 20
                    height: parent.height + 20
                    radius: 10 + 10
                    color: Qt.rgba(notificationBorder.accentColor.r, notificationBorder.accentColor.g, notificationBorder.accentColor.b, notificationBorder.waveOpacity(0.07, 4))
                    z: 0
                }
                Rectangle {
                    anchors.centerIn: parent
                    width: parent.width + 15
                    height: parent.height + 15
                    radius: 10 + 7
                    color: Qt.rgba(notificationBorder.accentColor.r, notificationBorder.accentColor.g, notificationBorder.accentColor.b, notificationBorder.waveOpacity(0.09, 5))
                    z: 0
                }
                Rectangle {
                    anchors.centerIn: parent
                    width: parent.width + 10
                    height: parent.height + 10
                    radius: 10 + 5
                    color: Qt.rgba(notificationBorder.accentColor.r, notificationBorder.accentColor.g, notificationBorder.accentColor.b, notificationBorder.waveOpacity(0.12, 6))
                    z: 0
                }
                Rectangle {
                    anchors.centerIn: parent
                    width: parent.width + 6
                    height: parent.height + 6
                    radius: 10 + 3
                    color: Qt.rgba(notificationBorder.accentColor.r, notificationBorder.accentColor.g, notificationBorder.accentColor.b, notificationBorder.waveOpacity(0.15, 7))
                    z: 0
                }
                
                // Анимация появления/исчезновения рамки
                PropertyAnimation {
                    id: borderShowAnim
                    target: notificationBorder
                    property: "border.width"
                    from: 0
                    to: 2
                    duration: 200
                    easing.type: Easing.InOutQuad
                }
                PropertyAnimation {
                    id: borderHideAnim
                    target: notificationBorder
                    property: "border.width"
                    from: 2
                    to: 0
                    duration: 200
                    easing.type: Easing.InOutQuad
                }
                
                // Обновление акцентного цвета
                Connections {
                    target: backend
                    function onSettingsChanged() {
                        notificationBorder.accentColor = backend.settings.accent_color !== undefined && backend.settings.accent_color !== null ? backend.settings.accent_color : "#7793a1"
                    }
                }
            }
        }
        contentItem: RowLayout {
            anchors.fill: parent
            anchors.leftMargin: 16
            anchors.rightMargin: 16
            spacing: 12
            
            // Индикатор типа уведомления
            Rectangle {
                id: typeIndicator
                width: 4
                height: 40
                radius: 2
                color: notificationPopup.notificationType === "success" ? "#4CAF50" :
                       notificationPopup.notificationType === "warning" ? "#FF9800" :
                       notificationPopup.notificationType === "error" ? "#F44336" :
                       "#7793a1"
                Layout.alignment: Qt.AlignVCenter
            }
            
            Text {
                id: notificationText
                text: "X"
                color: "#a2a2a2"
                font.pointSize: 10
                wrapMode: Text.WordWrap
                horizontalAlignment: Text.AlignLeft
                verticalAlignment: Text.AlignVCenter
                Layout.fillWidth: true
                Layout.alignment: Qt.AlignVCenter
            }
        }
        
        property string notificationType: "info"
        
        function show(msg, msgType) {
            notificationText.text = msg
            notificationType = msgType
            borderShowAnim.start()
            open()
            closeTimer.restart()
        }
        
        Timer {
            id: closeTimer
            interval: 3000
            onTriggered: {
                borderHideAnim.start()
                notificationPopup.close()
            }
        }
        
        onVisibleChanged: {
            if (!visible) {
                borderHideAnim.stop()
                notificationBorder.border.width = 0
            }
        }
    }

    Connections {
        target: backend
        function onNotification(message, type) {
            notificationPopup.show(message, type)
        }
        function onMacrosChanged() {
            backend.qmlLog("main.qml onMacrosChanged, macro_for_edit=" + (backend && backend.macro_for_edit ? JSON.stringify(backend.macro_for_edit) : "null"))
        }
        function onPageChangeRequested(pageFile) {
            changeActivePage(pageFile)
        }
        function onEditMacroRequested(pageFile, macroDict) {
            // Сигнал с данными напрямую — 100% надёжно, минует Property binding timing
            backend.qmlLog("main.qml onEditMacroRequested: page=" + pageFile + ", name=" + (macroDict && macroDict.name ? macroDict.name : "null") + ", type=" + (macroDict && macroDict.type ? macroDict.type : "null"))
            currentActiveButtonId = "macros"
            slideMenu.setActiveById("macros")
            stackView.replace(pageFile, { "editingMacro": macroDict })
        }
        function onOcrAreaSelectorRequested(target_type) {
            // Открываем AreaSelector для выбора области OCR
            areaSelector.open(target_type)
        }
    }

    // AreaSelector для выбора области OCR
    AreaSelector {
        id: areaSelector
        onAreaSelected: function(x1, y1, x2, y2) {
            // Сигнал уже обработан в AreaSelector
        }
    }

    // Диалог комплексной калибровки OCR (глобальный)
    OCRCalibrationDialog {
        id: ocrCalibrationDialog
        onCalibrationCompleted: {
            // Обновляем UI после завершения калибровки
            backend.notification("Калибровка OCR завершена! Нажмите СТАРТ для запуска.", "success")
        }
        onCalibrationCancelled: {
            backend.notification("Калибровка OCR отменена", "info")
        }
    }

    // Подключение сигнала открытия диалога калибровки OCR
    Connections {
        target: backend
        function onOcrCalibrationDialogRequested() {
            ocrCalibrationDialog.visible = true
            ocrCalibrationDialog.raise()
            ocrCalibrationDialog.requestActivate()
        }
    }

    // Плавающий оверлей отладки Fast OCR
    FastOCRDebugOverlay {
        id: fastOCROverlay
    }

    Connections {
        target: backend
        function onFastOCROverlayRequested() {
            fastOCROverlay.open()
        }
    }

    // ====== ДИАЛОГ ОБНОВЛЕНИЯ ======
    Dialog {
        id: updateDialog
        modal: true
        anchors.centerIn: parent
        width: 420
        height: 280
        closePolicy: Popup.NoAutoClose
        background: Rectangle {
            color: "#a01c1c1c"
            radius: 12
            border.color: "#70454545"
            border.width: 1

            Rectangle {
                anchors.fill: parent
                radius: parent.radius
                gradient: Gradient {
                    GradientStop { position: 0.0; color: "#60000000" }
                    GradientStop { position: 0.35; color: "#30000000" }
                    GradientStop { position: 0.7; color: "#10000000" }
                    GradientStop { position: 1.0; color: "#00000000" }
                }
            }
        }

        property string filePath: ""
        property string version: ""
        property int progressPercent: 0
        property bool downloading: false

        contentItem: ColumnLayout {
            spacing: 12

            Text {
                text: updateDialog.downloading ? " Загрузка обновления..." : " Обновление загружено!"
                color: updateDialog.downloading ? "#7793a1" : "#4CAF50"
                font.pointSize: 13
                font.bold: true
                Layout.alignment: Qt.AlignHCenter
            }

            // Прогресс-бар
            Rectangle {
                Layout.fillWidth: true
                Layout.preferredHeight: 24
                radius: 12
                color: "#151515"
                border.color: "#70454545"
                border.width: 1

                Rectangle {
                    width: parent.width * (updateDialog.progressPercent / 100)
                    height: parent.height
                    radius: 12
                    color: "#7793a1"

                    Behavior on width {
                        NumberAnimation { duration: 150 }
                    }
                }

                Text {
                    anchors.centerIn: parent
                    text: updateDialog.downloading ? updateDialog.progressPercent + "%" : "100%"
                    color: "#ffffff"
                    font.pointSize: 10
                    font.bold: true
                }
            }

            Text {
                id: updateStatusText
                text: updateDialog.downloading ? "Загрузка..." : "Версия " + updateDialog.version + " готова к установке"
                color: "#a0a0a0"
                font.pointSize: 10
                Layout.alignment: Qt.AlignHCenter
            }

            RowLayout {
                Layout.alignment: Qt.AlignHCenter
                spacing: 12
                visible: !updateDialog.downloading

                BaseButton {
                    text: "Установить"
                    implicitWidth: 140
                    implicitHeight: 34
                    iconSize: 12
                    textSize: 10
                    onClicked: {
                        backend.install_update(updateDialog.filePath, updateDialog.version)
                        updateDialog.visible = false
                    }
                }

                BaseButton {
                    text: "X Позже"
                    implicitWidth: 100
                    implicitHeight: 34
                    iconSize: 10
                    textSize: 10
                    onClicked: {
                        updateDialog.visible = false
                    }
                }
            }
        }
    }

    // Подключение сигналов загрузки обновления
    Connections {
        target: backend
        function onUpdateDownloadProgress(downloaded, total) {
            if (total > 0) {
                var pct = Math.round(downloaded / total * 100)
                updateDialog.progressPercent = pct
                updateDialog.downloading = true
                if (!updateDialog.visible) {
                    updateDialog.visible = true
                }
            }
        }
        function onUpdateDownloadComplete(filepath, version) {
            updateDialog.filePath = filepath
            updateDialog.version = version
            updateDialog.progressPercent = 100
            updateDialog.downloading = false
            if (!updateDialog.visible) {
                updateDialog.visible = true
            }
        }
    }

    // Оверлей проверки лицензии (показывается при старте, пока не подтверждена активация)
    Rectangle {
        id: licenseOverlay
        anchors.fill: parent
        color: "#40000000"
        visible: backend && !backend.isActivated
        z: 100
        Behavior on opacity { PropertyAnimation { duration: 300 } }

        // Блокировка всех кликов под оверлеем (карточка сверху перехватывает свои)
        MouseArea {
            anchors.fill: parent
            onPressed: function(mouse) { mouse.accepted = true }
        }

        // Центральная карточка
        Rectangle {
            id: licenseCard
            anchors.centerIn: parent
            width: 360
            height: 180
            radius: 12
            color: "#a01c1c1c"
            border.color: "#70454545"
            border.width: 1

            Rectangle {
                anchors.fill: parent
                radius: parent.radius
                gradient: Gradient {
                    GradientStop { position: 0.0; color: "#60000000" }
                    GradientStop { position: 0.35; color: "#30000000" }
                    GradientStop { position: 0.7; color: "#10000000" }
                    GradientStop { position: 1.0; color: "#00000000" }
                }
            }

            // Волна — полная линия + серый градиент слева направо
            Rectangle {
                anchors.top: parent.top
                width: parent.width
                height: 3
                radius: licenseCard.radius
                clip: true

                Rectangle {
                    anchors.fill: parent
                    color: root.accentColor
                }

                Rectangle {
                    id: licenseWaveBar
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
                        running: licenseOverlay.visible
                        loops: Animation.Infinite
                        PropertyAction { value: -licenseWaveBar.width }
                        NumberAnimation {
                            to: licenseWaveBar.parent.width
                            duration: 2500
                            easing.type: Easing.Linear
                        }
                    }
                }
            }

            // Статичная тонкая линия-трек
            Rectangle {
                anchors.top: parent.top
                anchors.left: parent.left
                anchors.right: parent.right
                height: 1
                color: Qt.rgba(root.accentColor.r, root.accentColor.g, root.accentColor.b, 0.15)
                z: 1
            }

            Column {
                anchors.centerIn: parent
                width: 312
                spacing: 16

                // Основной статус
                Text {
                    anchors.horizontalCenter: parent.horizontalCenter
                    width: parent.width
                    text: backend && backend.activationStatus === "checking" ? "Проверка лицензии..." :
                          backend && backend.activationStatus === "error" ? "Лицензия не найдена" :
                          "Инициализация..."
                    color: "#ffffff"
                    font.pointSize: 16
                    font.bold: true
                    horizontalAlignment: Text.AlignHCenter
                    wrapMode: Text.WordWrap
                }

                // Дополнительный текст
                Text {
                    anchors.horizontalCenter: parent.horizontalCenter
                    width: parent.width
                    text: "Пожалуйста, подождите..."
                    color: "#909090"
                    font.pointSize: 11
                    visible: backend && backend.activationStatus === "checking"
                    horizontalAlignment: Text.AlignHCenter
                    wrapMode: Text.WordWrap
                }

                Text {
                    anchors.horizontalCenter: parent.horizontalCenter
                    width: parent.width
                    text: "Перейдите в раздел «Подписка» для активации"
                    color: "#ef4444"
                    font.pointSize: 11
                    visible: backend && backend.activationStatus === "error"
                    horizontalAlignment: Text.AlignHCenter
                    wrapMode: Text.WordWrap
                }

                // Кнопка перехода к подписке
                BaseButton {
                    anchors.horizontalCenter: parent.horizontalCenter
                    text: "Перейти к подписке"
                    visible: backend && backend.activationStatus === "error"
                    implicitWidth: 200
                    implicitHeight: 40
                    onClicked: {
                        licenseOverlay.visible = false
                        changeActivePage("SubscriptionPage.qml")
                    }
                }
            }
        }

    }

    }

}
