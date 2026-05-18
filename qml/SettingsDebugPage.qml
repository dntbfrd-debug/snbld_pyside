import QtQuick 2.15
import QtQuick.Controls.Basic 2.15
import QtQuick.Layouts 1.15
import "components"

ScrollView {
    id: settingsDebugPage
    clip: true
    ScrollBar.vertical: GlassScrollBar { policy: ScrollBar.AlwaysOff }
    contentWidth: width
    contentHeight: mainColumn.height

    property color accentColor: backend && backend.settings && backend.settings.accent_color ? backend.settings.accent_color : "#7793a1"

    ColumnLayout {
        id: mainColumn
        width: settingsDebugPage.width - 40
        anchors.horizontalCenter: parent.horizontalCenter
        spacing: 15
        anchors.top: parent.top
        anchors.topMargin: 15

        // ========== ПЛИТКА: ГОРЯЧИЕ КЛАВИШИ СТАРТ/СТОП ==========
        GroupBox {
            title: "Горячие клавиши Старт / Стоп"
            Layout.fillWidth: true
            Layout.preferredHeight: 100
            background: GlassBlurPanel {}

            contentItem: RowLayout {
                anchors.margins: 10
                anchors.leftMargin: 15
                anchors.rightMargin: 15
                spacing: 20

                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: 5

                    Text { text: "Запуск макросов:"; color: "#a0a0a0"; font.pointSize: 9 }
                    TextField {
                        id: startHotkeyField
                        Layout.fillWidth: true
                        Layout.preferredHeight: 28
                        placeholderText: "Нажмите клавишу"
                        font.pointSize: 10
                        horizontalAlignment: Text.AlignHCenter
                        background: Rectangle { radius: 4; color: "#40ffffff" }
                        text: backend && backend.settings ? (backend.settings.start_all_hotkey || "") : ""
                        Keys.onPressed: {
                            event.accepted = true
                            if (event.key === Qt.Key_Backspace) { text = ""; backend.set_setting("start_all_hotkey", ""); return }
                            if (event.key === Qt.Key_Escape) { return }
                            var modifiers = []
                            var keyName = ""
                            if (event.modifiers & Qt.ControlModifier) modifiers.push("ctrl")
                            if (event.modifiers & Qt.AltModifier) modifiers.push("alt")
                            if (event.modifiers & Qt.ShiftModifier) modifiers.push("shift")
                            var key = event.key
                            if (key >= Qt.Key_F1 && key <= Qt.Key_F12) { keyName = "f" + (key - Qt.Key_F1 + 1) }
                            else if (key >= Qt.Key_A && key <= Qt.Key_Z) { keyName = String.fromCharCode(key).toLowerCase() }
                            else if (key >= Qt.Key_0 && key <= Qt.Key_9) {
                                keyName = (event.modifiers & Qt.ShiftModifier) ? ["!", "@", "#", "$", "%", "^", "&", "*", "(", ")"][key - Qt.Key_0] : String.fromCharCode(key)
                            }
                            else if (key === Qt.Key_Minus || key === Qt.Key_Hyphen) keyName = event.modifiers & Qt.ShiftModifier ? "_" : "-"
                            else if (key === Qt.Key_Equal || key === Qt.Key_Plus) keyName = event.modifiers & Qt.ShiftModifier ? "+" : "="
                            else if (key === Qt.Key_BracketLeft) keyName = event.modifiers & Qt.ShiftModifier ? "{" : "["
                            else if (key === Qt.Key_BracketRight) keyName = event.modifiers & Qt.ShiftModifier ? "}" : "]"
                            else if (key === Qt.Key_Backslash) keyName = event.modifiers & Qt.ShiftModifier ? "|" : "\\"
                            else if (key === Qt.Key_Semicolon) keyName = event.modifiers & Qt.ShiftModifier ? ":" : ";"
                            else if (key === Qt.Key_Apostrophe) keyName = event.modifiers & Qt.ShiftModifier ? '"' : "'"
                            else if (key === Qt.Key_Comma) keyName = event.modifiers & Qt.ShiftModifier ? "<" : ","
                            else if (key === Qt.Key_Period) keyName = event.modifiers & Qt.ShiftModifier ? ">" : "."
                            else if (key === Qt.Key_Slash) keyName = event.modifiers & Qt.ShiftModifier ? "?" : "/"
                            else if (key === Qt.Key_QuoteLeft) keyName = event.modifiers & Qt.ShiftModifier ? "~" : "`"
                            else if (key === Qt.Key_Space) keyName = "space"
                            else if (key === Qt.Key_Tab) keyName = "tab"
                            else if (key === Qt.Key_Return || key === Qt.Key_Enter) keyName = "enter"
                            else if (key === Qt.Key_Delete) keyName = "delete"
                            else if (key === Qt.Key_Up) keyName = "up"
                            else if (key === Qt.Key_Down) keyName = "down"
                            else if (key === Qt.Key_Left) keyName = "left"
                            else if (key === Qt.Key_Right) keyName = "right"
                            else if (key === Qt.Key_Home) keyName = "home"
                            else if (key === Qt.Key_End) keyName = "end"
                            else if (key === Qt.Key_PageUp) keyName = "page up"
                            else if (key === Qt.Key_PageDown) keyName = "page down"
                            else if (key === Qt.Key_Insert) keyName = "insert"
                            else if (key === Qt.Key_CapsLock) keyName = "caps lock"
                            else { keyName = "key_" + key; return }
                            text = modifiers.length > 0 ? modifiers.join("+") + "+" + keyName : keyName
                            backend.set_setting("start_all_hotkey", text)
                        }
                    }
                }

                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: 5

                    Text { text: "Остановка макросов:"; color: "#a0a0a0"; font.pointSize: 9 }
                    TextField {
                        id: stopHotkeyField
                        Layout.fillWidth: true
                        Layout.preferredHeight: 28
                        placeholderText: "Нажмите клавишу"
                        font.pointSize: 10
                        horizontalAlignment: Text.AlignHCenter
                        background: Rectangle { radius: 4; color: "#40ffffff" }
                        text: backend && backend.settings ? (backend.settings.stop_all_hotkey || "") : ""
                        Keys.onPressed: {
                            event.accepted = true
                            if (event.key === Qt.Key_Backspace) { text = ""; backend.set_setting("stop_all_hotkey", ""); return }
                            if (event.key === Qt.Key_Escape) { return }
                            var modifiers = []
                            var keyName = ""
                            if (event.modifiers & Qt.ControlModifier) modifiers.push("ctrl")
                            if (event.modifiers & Qt.AltModifier) modifiers.push("alt")
                            if (event.modifiers & Qt.ShiftModifier) modifiers.push("shift")
                            var key = event.key
                            if (key >= Qt.Key_F1 && key <= Qt.Key_F12) { keyName = "f" + (key - Qt.Key_F1 + 1) }
                            else if (key >= Qt.Key_A && key <= Qt.Key_Z) { keyName = String.fromCharCode(key).toLowerCase() }
                            else if (key >= Qt.Key_0 && key <= Qt.Key_9) {
                                keyName = (event.modifiers & Qt.ShiftModifier) ? ["!", "@", "#", "$", "%", "^", "&", "*", "(", ")"][key - Qt.Key_0] : String.fromCharCode(key)
                            }
                            else if (key === Qt.Key_Minus || key === Qt.Key_Hyphen) keyName = event.modifiers & Qt.ShiftModifier ? "_" : "-"
                            else if (key === Qt.Key_Equal || key === Qt.Key_Plus) keyName = event.modifiers & Qt.ShiftModifier ? "+" : "="
                            else if (key === Qt.Key_BracketLeft) keyName = event.modifiers & Qt.ShiftModifier ? "{" : "["
                            else if (key === Qt.Key_BracketRight) keyName = event.modifiers & Qt.ShiftModifier ? "}" : "]"
                            else if (key === Qt.Key_Backslash) keyName = event.modifiers & Qt.ShiftModifier ? "|" : "\\"
                            else if (key === Qt.Key_Semicolon) keyName = event.modifiers & Qt.ShiftModifier ? ":" : ";"
                            else if (key === Qt.Key_Apostrophe) keyName = event.modifiers & Qt.ShiftModifier ? '"' : "'"
                            else if (key === Qt.Key_Comma) keyName = event.modifiers & Qt.ShiftModifier ? "<" : ","
                            else if (key === Qt.Key_Period) keyName = event.modifiers & Qt.ShiftModifier ? ">" : "."
                            else if (key === Qt.Key_Slash) keyName = event.modifiers & Qt.ShiftModifier ? "?" : "/"
                            else if (key === Qt.Key_QuoteLeft) keyName = event.modifiers & Qt.ShiftModifier ? "~" : "`"
                            else if (key === Qt.Key_Space) keyName = "space"
                            else if (key === Qt.Key_Tab) keyName = "tab"
                            else if (key === Qt.Key_Return || key === Qt.Key_Enter) keyName = "enter"
                            else if (key === Qt.Key_Delete) keyName = "delete"
                            else if (key === Qt.Key_Up) keyName = "up"
                            else if (key === Qt.Key_Down) keyName = "down"
                            else if (key === Qt.Key_Left) keyName = "left"
                            else if (key === Qt.Key_Right) keyName = "right"
                            else if (key === Qt.Key_Home) keyName = "home"
                            else if (key === Qt.Key_End) keyName = "end"
                            else if (key === Qt.Key_PageUp) keyName = "page up"
                            else if (key === Qt.Key_PageDown) keyName = "page down"
                            else if (key === Qt.Key_Insert) keyName = "insert"
                            else if (key === Qt.Key_CapsLock) keyName = "caps lock"
                            else { keyName = "key_" + key; return }
                            text = modifiers.length > 0 ? modifiers.join("+") + "+" + keyName : keyName
                            backend.set_setting("stop_all_hotkey", text)
                        }
                    }
                }
            }
        }

        // ========== ПЛИТКА: ДИАГНОСТИКА МОНИТОРОВ ==========
        GroupBox {
            title: "Диагностика мониторов и окон"
            Layout.fillWidth: true
            Layout.preferredHeight: 155
            background: GlassBlurPanel {}

            contentItem: ColumnLayout {
                spacing: 5
                anchors.margins: 10
                anchors.leftMargin: 15
                anchors.rightMargin: 15

                GridLayout {
                    columns: 4
                    Layout.fillWidth: true
                    columnSpacing: 12
                    rowSpacing: 3

                    Text { text: "Мониторы:"; color: "#a0a0a0"; font.pointSize: 9; Layout.preferredWidth: 70 }
                    Text { id: monitorsCount; text: "-"; color: "#c2c2c2"; font.pointSize: 9; font.bold: true; Layout.preferredWidth: 60 }

                    Text { text: "DPI:"; color: "#a0a0a0"; font.pointSize: 9; Layout.preferredWidth: 70 }
                    Text { id: currentDpi; text: "-"; color: "#c2c2c2"; font.pointSize: 9; font.bold: true; Layout.preferredWidth: 60 }

                    Text { text: "Разрешение:"; color: "#a0a0a0"; font.pointSize: 9; Layout.preferredWidth: 70 }
                    Text { id: monitorResolution; text: "-"; color: "#c2c2c2"; font.pointSize: 9; font.bold: true; Layout.preferredWidth: 60 }

                    Text { text: "Последняя:"; color: "#a0a0a0"; font.pointSize: 9; Layout.preferredWidth: 70 }
                    Text { id: lastActivation; text: "-"; color: "#c2c2c2"; font.pointSize: 9; Layout.preferredWidth: 60 }

                    Text { text: "Активное:"; color: "#a0a0a0"; font.pointSize: 9; Layout.preferredWidth: 70 }
                    Text { id: activeWindowTitle; text: "-"; color: "#c2c2c2"; font.pointSize: 9; elide: Text.ElideRight; Layout.columnSpan: 3; Layout.fillWidth: true }

                    Text { text: "Целевое:"; color: "#a0a0a0"; font.pointSize: 9; Layout.preferredWidth: 70 }
                    Text { id: targetWindowTitle; text: "-"; color: "#c2c2c2"; font.pointSize: 9; elide: Text.ElideRight; Layout.columnSpan: 3; Layout.fillWidth: true }
                }

                BaseButton {
                    text: "Обновить"
                    implicitWidth: 120
                    implicitHeight: 26
                    iconSize: 10
                    textSize: 9
                    Layout.alignment: Qt.AlignHCenter
                    Layout.topMargin: 7
                    onClicked: {
                        var info = backend.get_window_manager_diagnostic()
                        monitorsCount.text = info.monitors_count
                        currentDpi.text = info.current_dpi + " DPI"
                        monitorResolution.text = (info.monitor_right - info.monitor_left) + "x" + (info.monitor_bottom - info.monitor_top)
                        activeWindowTitle.text = info.foreground_title
                        
                        // Если из диагностики не пришло целевое окно — берём напрямую из настроек
                        if (info.target_title && info.target_title != "") {
                            targetWindowTitle.text = info.target_title
                        } else {
                            targetWindowTitle.text = backend.settings.target_window_title || "Не выбрано"
                        }
                        
                        lastActivation.text = info.last_activation > 0 ? Math.round((Date.now() / 1000 - info.last_activation)) + " сек назад" : "Никогда"
                    }
                }
            }
        }

        // ========== ПЛИТКА: ЛОГИ ==========
        // Бегущая волна по верхней границе плитки (при отправке)
        Item {
            anchors.top: logsGroupBox.top
            anchors.left: logsGroupBox.left
            anchors.right: logsGroupBox.right
            height: 3
            clip: true
            visible: backend.isSendingLogs
            z: 10

            Rectangle {
                id: logWave1
                x: -120
                width: 120
                height: 3
                radius: 1.5

                gradient: Gradient {
                    orientation: Gradient.Horizontal
                    GradientStop { position: 0.0; color: "transparent" }
                    GradientStop { position: 0.3; color: settingsDebugPage.accentColor }
                    GradientStop { position: 0.5; color: Qt.lighter(settingsDebugPage.accentColor, 1.5) }
                    GradientStop { position: 0.7; color: settingsDebugPage.accentColor }
                    GradientStop { position: 1.0; color: "transparent" }
                }

                SequentialAnimation on x {
                    running: backend.isSendingLogs
                    loops: Animation.Infinite
                    NumberAnimation {
                        from: -120
                        to: parent.width
                        duration: 2000
                        easing.type: Easing.Linear
                    }
                }
            }

            Rectangle {
                id: logWave2
                x: -120
                width: 120
                height: 3
                radius: 1.5

                gradient: Gradient {
                    orientation: Gradient.Horizontal
                    GradientStop { position: 0.0; color: "transparent" }
                    GradientStop { position: 0.3; color: settingsDebugPage.accentColor }
                    GradientStop { position: 0.5; color: Qt.lighter(settingsDebugPage.accentColor, 1.5) }
                    GradientStop { position: 0.7; color: settingsDebugPage.accentColor }
                    GradientStop { position: 1.0; color: "transparent" }
                }

                SequentialAnimation on x {
                    running: backend.isSendingLogs
                    loops: Animation.Infinite
                    PauseAnimation { duration: 1000 }
                    NumberAnimation {
                        from: -120
                        to: parent.width
                        duration: 2000
                        easing.type: Easing.Linear
                    }
                }
            }
        }

        GroupBox {
            id: logsGroupBox
            title: "Логи"
            Layout.fillWidth: true
            Layout.preferredHeight: 115
            background: GlassBlurPanel { id: logsBg }

            contentItem: ColumnLayout {
                spacing: 6
                anchors.margins: 10

                Text {
                    text: "Отправить все логи разработчику для анализа"
                    color: "#a0a0a0"
                    font.pointSize: 9
                    Layout.fillWidth: true
                }

                Text {
                    text: "Вы не отправляете мне никаких своих личных данных, вы можете сами проверить все логи в папке logs"
                    color: "#70a070"
                    font.pointSize: 9
                    font.italic: true
                    wrapMode: Text.WordWrap
                    Layout.fillWidth: true
                }

                BaseButton {
                    text: backend.isSendingLogs ? "Отправка..." : "Отправить логи"
                    implicitWidth: 160
                    implicitHeight: 30
                    iconSize: 12
                    textSize: 9
                    enabled: !backend.isSendingLogs
                    opacity: enabled ? 1.0 : 0.5
                    onClicked: backend.send_logs_to_telegram()
                }
            }
        }

        // ========== ПЛИТКА: ОБНОВЛЕНИЯ ==========
        GroupBox {
            id: updateGroup
            title: "Обновления"
            Layout.fillWidth: true
            Layout.preferredHeight: updateProgressBar.visible ? 175 : 140
            background: GlassBlurPanel {}

            contentItem: ColumnLayout {
                spacing: 6
                anchors.margins: 10

                RowLayout {
                    Layout.fillWidth: true
                    Text {
                        text: "Текущая версия:"
                        color: "#a0a0a0"
                        font.pointSize: 10
                    }
                    Text {
                        id: currentVersionText
                        text: backend.get_current_version()
                        color: "#c2c2c2"
                        font.pointSize: 10
                        font.bold: true
                    }
                    Item { Layout.fillWidth: true }
                }

                RowLayout {
                    Layout.fillWidth: true
                    Text {
                        text: "Доступная версия:"
                        color: "#a0a0a0"
                        font.pointSize: 10
                    }
                    Text {
                        id: latestVersionText
                        text: "-"
                        color: "#4CAF50"
                        font.pointSize: 10
                        font.bold: true
                    }
                    Item { Layout.fillWidth: true }
                }

                // Прогресс-бар загрузки
                ProgressBar {
                    id: updateProgressBar
                    Layout.fillWidth: true
                    Layout.preferredHeight: 6
                    visible: false
                    from: 0
                    to: 100
                    value: 0
                    background: Rectangle {
                        radius: 3
                        color: "#40ffffff"
                    }
                    contentItem: Rectangle {
                        radius: 3
                        color: updateGroup.accentColor
                        width: updateProgressBar.visualPosition * parent.width
                        height: parent.height
                    }
                }

                Text {
                    id: updateStatusText
                    visible: false
                    color: "#a0a0a0"
                    font.pointSize: 9
                    font.italic: true
                    Layout.fillWidth: true
                    horizontalAlignment: Text.AlignHCenter
                }

                RowLayout {
                    Layout.fillWidth: true
                    BaseButton {
                        id: checkBtn
                        text: "Проверить"
                        implicitWidth: 140
                        implicitHeight: 28
                        iconSize: 10
                        textSize: 9
                        onClicked: {
                            checkBtn.enabled = false
                            latestVersionText.text = "Проверка..."
                            updateProgressBar.visible = false
                            updateStatusText.visible = false
                            var result = backend.check_for_updates()
                            checkBtn.enabled = true
                            if (result.success) {
                                latestVersionText.text = result.latest_version
                                if (result.available) {
                                    installBtn.visible = true
                                    installBtn.enabled = true
                                    installBtn.downloadUrl = result.download_url
                                    installBtn.version = result.latest_version
                                    downloadBtn.visible = true
                                    downloadBtn.enabled = true
                                    downloadBtn.downloadUrl = result.download_url
                                    latestVersionText.color = "#4CAF50"
                                    updateStatusText.text = "Доступно обновление"
                                    updateStatusText.visible = true
                                    updateStatusText.color = "#4CAF50"
                                } else {
                                    installBtn.visible = false
                                    installBtn.enabled = false
                                    downloadBtn.visible = false
                                    downloadBtn.enabled = false
                                    latestVersionText.text = "Нет обновлений"
                                    latestVersionText.color = "#a0a0a0"
                                    updateStatusText.text = ""
                                    updateStatusText.visible = false
                                }
                            } else {
                                latestVersionText.text = "Ошибка проверки"
                                latestVersionText.color = "#f44336"
                                installBtn.visible = false
                                downloadBtn.visible = false
                                updateStatusText.text = result.error || "Сервер не ответил"
                                updateStatusText.visible = true
                                updateStatusText.color = "#f44336"
                            }
                        }
                    }
                    BaseButton {
                        id: installBtn
                        property string downloadUrl: ""
                        property string version: ""
                        text: "Скачать и установить"
                        implicitWidth: 180
                        implicitHeight: 28
                        iconSize: 10
                        textSize: 9
                        visible: false
                        enabled: true
                        onClicked: {
                            if (downloadUrl !== "" && version !== "") {
                                installBtn.enabled = false
                                checkBtn.enabled = false
                                downloadBtn.enabled = false
                                updateProgressBar.visible = true
                                updateProgressBar.value = 0
                                updateStatusText.text = "Загрузка обновления..."
                                updateStatusText.visible = true
                                updateStatusText.color = "#a0a0a0"
                                backend.download_update_async(downloadUrl, version)
                            }
                        }
                    }
                    BaseButton {
                        id: downloadBtn
                        property string downloadUrl: ""
                        text: "Браузер"
                        implicitWidth: 100
                        implicitHeight: 28
                        iconSize: 10
                        textSize: 9
                        visible: false
                        enabled: true
                        onClicked: {
                            if (downloadUrl !== "") {
                                backend.open_url(downloadUrl)
                            }
                        }
                    }
                    Item { Layout.fillWidth: true }
                }
            }
        }

        // Обработка сигналов обновления
        Connections {
            target: backend
            function onUpdateDownloadProgress(downloaded, total) {
                if (total > 0) {
                    updateProgressBar.value = Math.min(100, (downloaded / total) * 100)
                    var downloadedMb = (downloaded / 1048576).toFixed(1)
                    var totalMb = (total / 1048576).toFixed(1)
                    updateStatusText.text = "Загрузка: " + downloadedMb + " / " + totalMb + " MB"
                } else {
                    updateStatusText.text = "Загрузка..."
                }
            }
            function onUpdateDownloadComplete(filepath, version) {
                updateProgressBar.value = 100
                updateStatusText.text = "Обновление загружено! Установка..."
                updateStatusText.color = "#4CAF50"
            }
            function onNotification(message, type) {
                if (type === "error" && !checkBtn.enabled) {
                    installBtn.enabled = true
                    checkBtn.enabled = true
                    downloadBtn.enabled = true
                    updateProgressBar.visible = false
                    updateStatusText.text = message
                    updateStatusText.color = "#f44336"
                    updateStatusText.visible = true
                }
            }
        }

        RowLayout {
            Layout.fillWidth: true
            Layout.topMargin: 5
            spacing: 0
            Item { Layout.fillWidth: true }
            BaseButton {
                text: "Сохранить"
                implicitWidth: 160
                implicitHeight: 34
                iconSize: 14
                textSize: 10
                onClicked: backend.save_all_settings()
            }
            Item { Layout.fillWidth: true }
        }
    }

    // Обновление информации при открытии страницы
    Component.onCompleted: {
        // Автоматически заполняем целевой заголовок сразу при открытии
        if (backend && backend.settings) {
            targetWindowTitle.text = backend.settings.target_window_title || "Не выбрано"
            startHotkeyField.text = backend.settings.start_all_hotkey || ""
            stopHotkeyField.text = backend.settings.stop_all_hotkey || ""
        }
    }

    // Обновление акцентного цвета при изменении настроек
    Connections {
        target: backend
        function onSettingsChanged() {
            settingsDebugPage.accentColor = backend.settings.accent_color !== undefined && backend.settings.accent_color !== null ? backend.settings.accent_color : "#7793a1"
            
            // Обновляем целевой заголовок если изменились настройки
            if (targetWindowTitle) {
                targetWindowTitle.text = backend.settings.target_window_title || "Не выбрано"
            }
            // Синхронизируем поля горячих клавиш
            if (startHotkeyField) {
                startHotkeyField.text = backend.settings.start_all_hotkey || ""
            }
            if (stopHotkeyField) {
                stopHotkeyField.text = backend.settings.stop_all_hotkey || ""
            }
        }
    }
}