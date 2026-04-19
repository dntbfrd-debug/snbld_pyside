import QtQuick 2.15
import QtQuick.Controls.Basic 2.15
import QtQuick.Layouts 1.15
import QtMultimedia 5.15
import Qt5Compat.GraphicalEffects

ApplicationWindow {
    id: root
    width: 1300
    height: 700
    minimumWidth: 400
    minimumHeight: 300
    visible: true
    title: "snbld resvap"
    color: "#1e1e2f"
    flags: Qt.FramelessWindowHint | Qt.Window
    // Иконка устанавливается программно в qml_main.py

    // Закруглённые края окна
    property int windowRadius: 12
    // Ширина левой колонки (меню + левая часть заголовка)
    property int leftColumnWidth: 260

    // Получаем акцентный цвет
    property string accentColor: backend && backend.settings && backend.settings.accent_color !== undefined && backend.settings.accent_color !== null ? backend.settings.accent_color : "#7793a1"

    // Убираем titleTextColor — используем градиент titleBar

    property var mainMenuButtons: [macrosExpandBtn, settingsBtn, profilesBtn, subscriptionBtn, helpBtn, debugBtn]
    property Item currentActiveButton: helpBtn
    property bool submenuVisible: false

    // Функции для работы с подменю (должны быть определены ДО использования)
    function openSubmenu() {
        submenuVisible = true
    }

    function closeSubmenu() {
        submenuVisible = false
    }

    function changeActivePage(pageFile) {
        if (pageFile === "SettingsPage.qml" || pageFile === "SettingsMainPage.qml") {
            stackView.replace("SettingsMainPage.qml")
            mainMenuIndicator.setActive(settingsBtn)
        } else if (pageFile === "SettingsAppearancePage.qml") {
            // Страница внешнего вида - открывается через push из SettingsMainPage
            stackView.push(pageFile)
        } else if (pageFile === "MacrosListPage.qml") {
            mainMenuIndicator.setActive(macrosExpandBtn)
            stackView.replace("MacrosListPage.qml")
        } else if (pageFile === "MacrosEditPage.qml") {
            mainMenuIndicator.setActive(macrosExpandBtn)
            stackView.replace("MacrosEditPage.qml")
        } else if (pageFile === "EditSimplePage.qml" || pageFile === "EditZonePage.qml" || pageFile === "EditSkillPage.qml" || pageFile === "EditBuffPage.qml") {
            // Страницы редактирования - используем push
            mainMenuIndicator.setActive(macrosExpandBtn)
            stackView.push(pageFile)
        } else if (pageFile === "BuffListPage.qml" || pageFile === "BuffEditForm.qml") {
            // Страницы баффов - используем push
            mainMenuIndicator.setActive(macrosExpandBtn)
            stackView.push(pageFile)
        } else if (pageFile === "ProfilesPage.qml") {
            mainMenuIndicator.setActive(profilesBtn)
            stackView.replace(pageFile)
        } else if (pageFile === "SubscriptionPage.qml") {
            mainMenuIndicator.setActive(subscriptionBtn)
            stackView.replace(pageFile)
        } else if (pageFile === "HelpPage.qml") {
            mainMenuIndicator.setActive(helpBtn)
            stackView.replace(pageFile)
        } else if (pageFile === "DebugPage.qml") {
            mainMenuIndicator.setActive(debugBtn)
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
        color: "#1e1e2f"
        clip: true

        // Правая колонка: видео/градиент на всю высоту окна (включая заголовок)
        Item {
            id: rightColumnBackground
            anchors.left: parent.left
            anchors.leftMargin: root.leftColumnWidth
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

        // Одна тень на границе меню/контента на всю высоту окна (совпадает с leftMenu.right и правым краем title)
        LinearGradient {
            id: menuContentDividerShadow
            anchors.left: parent.left
            anchors.leftMargin: root.leftColumnWidth
            anchors.top: parent.top
            anchors.bottom: parent.bottom
            width: 6
            start: Qt.point(0, 0)
            end: Qt.point(width, 0)
            gradient: Gradient {
                GradientStop { position: 0.0; color: "#60000000" }
                GradientStop { position: 1.0; color: "#00000000" }
            }
            z: 2
        }

        Item {
            id: titleBar
            anchors.left: parent.left
            anchors.right: parent.right
            anchors.top: parent.top
            height: 40
            z: 10

            RowLayout {
                id: titleBarRow
                anchors.fill: parent
                spacing: 0

                Rectangle {
                    Layout.preferredWidth: root.leftColumnWidth
                    Layout.fillHeight: true
                    color: "#262626"

                    Text {
                        id: titleText
                        x: 85
                        anchors.verticalCenter: parent.verticalCenter
                        text: "snbld resvap"
                        color: "#c0c0c0"
                        font.pointSize: 12
                        font.bold: true
                    }
                }
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
                    text: "✕"
                    background: Rectangle { color: closeButton.hovered ? "#e81123" : "#252525"; radius: 4 }
                    contentItem: Text { text: parent.text; color: "#909090"; horizontalAlignment: Text.AlignHCenter; verticalAlignment: Text.AlignVCenter; font.pixelSize: 12 }
                    onClicked: backend.closeWindow()
                }
            }
        }

    Item {
        id: contentArea
        anchors.top: titleBar.bottom
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.bottom: parent.bottom
        z: 1

        Rectangle {
            id: leftMenu
            width: root.leftColumnWidth
            anchors.left: parent.left
            anchors.top: parent.top
            anchors.bottom: parent.bottom

            gradient: Gradient {
                GradientStop { position: 0.0; color: Qt.rgba(0.15, 0.15, 0.15, 1) }
                GradientStop { position: 0.5; color: Qt.rgba(0.23, 0.23, 0.23, 1) }
                GradientStop { position: 1.0; color: Qt.rgba(0.16, 0.16, 0.16, 1) }
            }

            ColumnLayout {
                id: menuLayout
                anchors.fill: parent
                anchors.margins: 15
                spacing: 15

                // Кнопка "Макросы" с подменю
                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: 0

                    MenuButton {
                        id: macrosExpandBtn
                        text: "Макросы"
                        iconSource: "../icons/macros.png"
                        Layout.fillWidth: true
                        Layout.preferredHeight: 50
                        isActive: true
                        enabled: backend && backend.isActivated
                        opacity: enabled ? 1.0 : 0.3
                        onClicked: {
                            if (!enabled) return
                            if (submenuVisible) closeSubmenu()
                            else openSubmenu()
                            mainMenuIndicator.setActive(macrosExpandBtn)
                        }
                    }

                    // Подменю
                    ColumnLayout {
                        id: submenu
                        Layout.fillWidth: true
                        Layout.preferredHeight: submenuVisible ? 100 : 0
                        clip: true
                        visible: submenuVisible
                        spacing: 0
                        Behavior on Layout.preferredHeight {
                            PropertyAnimation { duration: 200; easing.type: Easing.InOutQuad }
                        }

                        Item {
                            Layout.fillWidth: true
                            height: 10
                        }

                        Item {
                            Layout.fillWidth: true
                            Layout.preferredHeight: 50
                            MenuButton {
                                anchors.horizontalCenter: parent.horizontalCenter
                                width: 220
                                text: "Список макросов"
                                iconSource: "../icons/list.png"
                                height: 45
                                isActive: false
                                enabled: backend && backend.isActivated
                                opacity: enabled ? 1.0 : 0.3
                                iconSize: 16
                                textSize: 10
                                onClicked: {
                                    if (!enabled) return
                                    changeActivePage("MacrosListPage.qml")
                                    closeSubmenu()
                                }
                            }
                        }
                        Item {
                            Layout.fillWidth: true
                            Layout.preferredHeight: 50
                            MenuButton {
                                anchors.horizontalCenter: parent.horizontalCenter
                                width: 220
                                text: "Создание"
                                iconSource: "../icons/edit.png"
                                height: 45
                                isActive: false
                                enabled: backend && backend.isActivated
                                opacity: enabled ? 1.0 : 0.3
                                iconSize: 16
                                textSize: 10
                                onClicked: {
                                    if (!enabled) return
                                    changeActivePage("MacrosEditPage.qml")
                                    closeSubmenu()
                                }
                            }
                        }
                    }
                }

                MenuButton {
                    id: settingsBtn
                    text: "Настройки"
                    iconSource: "../icons/settings.png"
                    Layout.fillWidth: true
                    Layout.preferredHeight: 50
                    isActive: false
                    enabled: backend && backend.isActivated
                    opacity: enabled ? 1.0 : 0.3
                    onClicked: {
                        if (!enabled) return
                        closeSubmenu()
                        mainMenuIndicator.setActive(settingsBtn)
                        changeActivePage("SettingsMainPage.qml")
                    }
                }
                MenuButton {
                    id: profilesBtn
                    text: "Профили"
                    iconSource: "../icons/profiles.png"
                    Layout.fillWidth: true
                    Layout.preferredHeight: 50
                    isActive: false
                    enabled: backend && backend.isActivated
                    opacity: enabled ? 1.0 : 0.3
                    onClicked: {
                        if (!enabled) return
                        closeSubmenu()
                        mainMenuIndicator.setActive(profilesBtn)
                        changeActivePage("ProfilesPage.qml")
                    }
                }
                MenuButton {
                    id: subscriptionBtn
                    text: "Подписка"
                    iconSource: "../icons/subscription.png"
                    Layout.fillWidth: true
                    Layout.preferredHeight: 50
                    isActive: false
                    onClicked: {
                        closeSubmenu()
                        mainMenuIndicator.setActive(subscriptionBtn)
                        changeActivePage("SubscriptionPage.qml")
                    }
                }
                MenuButton {
                    id: helpBtn
                    text: "Помощь"
                    iconSource: "../icons/help.png"
                    Layout.fillWidth: true
                    Layout.preferredHeight: 50
                    isActive: true
                    onClicked: {
                        closeSubmenu()
                        mainMenuIndicator.setActive(helpBtn)
                        changeActivePage("HelpPage.qml")
                    }
                }
                MenuButton {
                    id: debugBtn
                    text: "Диагностика"
                    iconSource: "../icons/calibrate.png"
                    Layout.fillWidth: true
                    Layout.preferredHeight: 50
                    isActive: false
                    onClicked: {
                        closeSubmenu()
                        mainMenuIndicator.setActive(debugBtn)
                        changeActivePage("DebugPage.qml")
                    }
                }

                Item { Layout.fillHeight: true }

                Item {
                    Layout.fillWidth: true
                    Layout.preferredHeight: 50
                    id: actionsContainer
                    RowLayout {
                        anchors.fill: parent
                        spacing: 12
                        ActionButton {
                            id: startAllBtn
                            text: "Старт"
                            iconSource: "../icons/play.png"
                            isActive: backend.global_stopped
                            enabled: backend && backend.isActivated
                            opacity: enabled ? 1.0 : 0.3
                            Layout.fillWidth: true
                            Layout.preferredHeight: 50
                            onClicked: {
                                if (!enabled) return
                                backend.start_all_macros()
                                actionButtonsIndicator.setActive(startAllBtn)
                            }
                        }
                        ActionButton {
                            id: stopAllBtn
                            text: "Стоп"
                            iconSource: "../icons/stop.png"
                            isActive: !backend.global_stopped
                            enabled: backend && backend.isActivated
                            opacity: enabled ? 1.0 : 0.3
                            Layout.fillWidth: true
                            Layout.preferredHeight: 50
                            onClicked: {
                                if (!enabled) return
                                backend.stop_all_macros()
                                actionButtonsIndicator.setActive(stopAllBtn)
                            }
                        }
                    }
                }
            }
        }

        // StackView
        StackView {
            id: stackView
            anchors.left: leftMenu.right
            anchors.right: parent.right
            anchors.top: parent.top
            anchors.bottom: parent.bottom
            initialItem: "HelpPage.qml"
            clip: true
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
        id: mainMenuIndicator
        buttons: [macrosExpandBtn, settingsBtn, profilesBtn, subscriptionBtn, helpBtn, debugBtn]
        leftInset: 10
        topInset: 10
        rightInset: 10
        bottomInset: 10
        setActiveCallback: function(activeButton) {
            for (var i = 0; i < mainMenuButtons.length; ++i) {
                mainMenuButtons[i].isActive = false
            }
            activeButton.isActive = true
            currentActiveButton = activeButton
        }
        Component.onCompleted: {
            helpBtn.isActive = true
            init()
            setActive(helpBtn)
        }
    }

    ButtonGroupWithIndicator {
        id: actionButtonsIndicator
        buttons: [startAllBtn, stopAllBtn]
        leftInset: 10
        topInset: 10
        rightInset: 10
        bottomInset: 10
        setActiveCallback: function(activeButton) {
            startAllBtn.isActive = false
            stopAllBtn.isActive = false
            activeButton.isActive = true
        }
        Component.onCompleted: {
            init()
            setActive(stopAllBtn)
        }
        
        // Реакция на изменение global_stopped (горячие клавиши)
        Connections {
            target: backend
            function on_globalStoppedChanged() {
                if (backend.global_stopped) {
                    actionButtonsIndicator.setActive(stopAllBtn)
                } else {
                    actionButtonsIndicator.setActive(startAllBtn)
                }
            }
        }
        
        // Реакция на нажатие кнопок старт/стоп (в том числе по горячим клавишам)
        Connections {
            target: backend
            function onStartAllPressed() {
                actionButtonsIndicator.setActive(startAllBtn)
            }
            function onStopAllPressed() {
                actionButtonsIndicator.setActive(stopAllBtn)
            }
            // Обновление статуса макросов (когда макрос запущен по горячей клавише)
            function onMacroStatusChanged() {
                // Обновляем список макросов
                macrosList.model = backend.macros
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
            color: "#1a1a1a"
            radius: 10
            
            // Градиентный фон
            gradient: Gradient {
                orientation: Gradient.Horizontal
                GradientStop { position: 0.0; color: "#252525" }
                GradientStop { position: 1.0; color: "#1a1a1a" }
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
                
                // 8 слоёв свечения рамки (как в BaseButton activeGlow)
                Rectangle {
                    anchors.centerIn: parent
                    width: parent.width + 40
                    height: parent.height + 40
                    radius: 10 + 20
                    color: Qt.rgba(notificationBorder.accentColor.r, notificationBorder.accentColor.g, notificationBorder.accentColor.b, 0.005)
                    z: 0
                }
                Rectangle {
                    anchors.centerIn: parent
                    width: parent.width + 35
                    height: parent.height + 35
                    radius: 10 + 17
                    color: Qt.rgba(notificationBorder.accentColor.r, notificationBorder.accentColor.g, notificationBorder.accentColor.b, 0.01)
                    z: 0
                }
                Rectangle {
                    anchors.centerIn: parent
                    width: parent.width + 30
                    height: parent.height + 30
                    radius: 10 + 15
                    color: Qt.rgba(notificationBorder.accentColor.r, notificationBorder.accentColor.g, notificationBorder.accentColor.b, 0.015)
                    z: 0
                }
                Rectangle {
                    anchors.centerIn: parent
                    width: parent.width + 25
                    height: parent.height + 25
                    radius: 10 + 12
                    color: Qt.rgba(notificationBorder.accentColor.r, notificationBorder.accentColor.g, notificationBorder.accentColor.b, 0.02)
                    z: 0
                }
                Rectangle {
                    anchors.centerIn: parent
                    width: parent.width + 20
                    height: parent.height + 20
                    radius: 10 + 10
                    color: Qt.rgba(notificationBorder.accentColor.r, notificationBorder.accentColor.g, notificationBorder.accentColor.b, 0.03)
                    z: 0
                }
                Rectangle {
                    anchors.centerIn: parent
                    width: parent.width + 15
                    height: parent.height + 15
                    radius: 10 + 7
                    color: Qt.rgba(notificationBorder.accentColor.r, notificationBorder.accentColor.g, notificationBorder.accentColor.b, 0.04)
                    z: 0
                }
                Rectangle {
                    anchors.centerIn: parent
                    width: parent.width + 10
                    height: parent.height + 10
                    radius: 10 + 5
                    color: Qt.rgba(notificationBorder.accentColor.r, notificationBorder.accentColor.g, notificationBorder.accentColor.b, 0.05)
                    z: 0
                }
                Rectangle {
                    anchors.centerIn: parent
                    width: parent.width + 6
                    height: parent.height + 6
                    radius: 10 + 3
                    color: Qt.rgba(notificationBorder.accentColor.r, notificationBorder.accentColor.g, notificationBorder.accentColor.b, 0.06)
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
                text: ""
                color: "#c2c2c2"
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
        function onPageChangeRequested(pageFile) {
            changeActivePage(pageFile)
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

    // ====== ДИАЛОГ ОБНОВЛЕНИЯ ======
    Dialog {
        id: updateDialog
        modal: true
        anchors.centerIn: parent
        width: 420
        height: 280
        closePolicy: Popup.NoAutoClose
        background: Rectangle {
            color: "#2a2a3d"
            radius: 12
            border.color: "#40ffffff"
            border.width: 1
        }

        property string filePath: ""
        property string version: ""
        property int progressPercent: 0
        property bool downloading: false

        contentItem: ColumnLayout {
            spacing: 12

            Text {
                text: updateDialog.downloading ? "⬇️ Загрузка обновления..." : "✅ Обновление загружено!"
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
                color: "#1e1e2f"
                border.color: "#50ffffff"
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
                    text: "🔄 Установить"
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
                    text: "✖ Позже"
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

    // Очистка при закрытии
    Component.onDestruction: {
        if (backend) {
            backend.stop_all_macros()
        }
    }
    }
}
