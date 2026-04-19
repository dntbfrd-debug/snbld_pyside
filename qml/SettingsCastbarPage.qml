import QtQuick 2.15
import QtQuick.Controls.Basic 2.15
import QtQuick.Layouts 1.15
import QtQml 2.15
import QtQuick.Window 2.15

Item {
    id: settingsCastbarPage

    // Безопасный доступ к настройкам
    property var safeSettings: (backend && backend.settings) ? backend.settings : ({})

    // Получаем акцентный цвет из настроек
    property string accentColor: safeSettings.accent_color || "#7793a1"

    // Обновление при изменении настроек
    Connections {
        target: backend
        function onSettingsChanged() {
            settingsCastbarPage.safeSettings = (backend && backend.settings) ? backend.settings : ({})
            // Обновляем слайдер порога без вызова set_setting
            if (castbarThresholdSlider && safeSettings.castbar_threshold !== undefined) {
                castbarThresholdSlider.updating = true
                castbarThresholdSlider.value = safeSettings.castbar_threshold
                castbarThresholdSlider.updating = false
            }
        }
    }

    // Инициализация при загрузке
    Component.onCompleted: {
        // Показываем текущий цвет из настроек
        var currentColor = backend.getCurrentCastbarColor()
        calibrationStatusText.text = "Откалиброванный цвет: " + currentColor
        calibrationStatusText.color = accentColor
        colorPreviewRect.color = colorStringToRgb(currentColor)
        console.log("SettingsCastbarPage: текущий цвет кастбара = " + currentColor)
    }

    // Загружаем CastBarDialog
    CastBarDialog {
        id: castbarDialog
        onCalibrationStarted: {
            console.log("SettingsCastbarPage: Калибровка запущена, вызываем backend.registerCastbarHotkeyForDialog")
            backend.registerCastbarHotkeyForDialog(castbarDialog)
        }
        onCalibrationAccepted: function(point, color, threshold) {
            console.log("SettingsCastbarPage: Калибровка принята! point=" + point + ", color=" + color)
            // Сохраняем настройки
            backend.set_setting("castbar_point", point)
            backend.set_setting("castbar_color", color)  // color уже массив [R, G, B]
            backend.set_setting("castbar_threshold", threshold)
            backend.set_setting("castbar_enabled", true)
            // Обновляем UI
            colorPreviewRect.color = colorStringToRgb(color.join(','))
            calibrationStatusText.text = "✅ Откалиброванный цвет: " + color.join(',') + " в точке " + point
            calibrationStatusText.color = accentColor
            backend.notification("Настройки кастбара сохранены!", "success")
        }
        onCalibrationCancelled: {
            console.log("SettingsCastbarPage: Калибровка отменена")
            backend.stopCastbarCalibration()
        }
    }

    // Очистка при уничтожении страницы
    Component.onDestruction: {
        console.log("SettingsCastbarPage: Уничтожение, закрываем CastBarDialog")
        if (castbarDialog) {
            castbarDialog.visible = false
            castbarDialog.close()
        }
    }

    // Подключаем backend.castbarColorCaptured к CastBarDialog
    Connections {
        target: backend
        function onCastbarColorCaptured(point, color) {
            console.log("SettingsCastbarPage: onCastbarColorCaptured вызван! point=" + point + ", color=" + color)
            if (castbarDialog) {
                castbarDialog.capturedColor = color
                castbarDialog.selectedPoint = point
                castbarDialog.calibrationState = "captured"
                castbarDialog.visible = true
                castbarDialog.raise()
                castbarDialog.requestActivate()
                console.log("SettingsCastbarPage: CastBarDialog обновлён и показан")
            } else {
                console.log("SettingsCastbarPage: castbarDialog = null!")
            }
        }
    }

    // Функция для конвертации строки цвета в RGB
    function colorStringToRgb(colorStr) {
        var parts = colorStr.split(',')
        if (parts.length === 3) {
            return Qt.rgba(parts[0]/255, parts[1]/255, parts[2]/255, 1.0)
        }
        return "#2a2a2a"
    }

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 20
        anchors.bottomMargin: 20
        spacing: 15

        // Заголовок с кнопкой назад
        RowLayout {
            Layout.fillWidth: true
            Layout.preferredHeight: 40
            BaseButton {
                text: "← Назад"
                implicitWidth: 80
                implicitHeight: 30
                iconSize: 0
                textSize: 10
                onClicked: settingsCastbarPage.StackView.view.pop()
            }
            Text {
                text: "⚡ Детекция каста"
                font.pointSize: 18
                font.bold: true
                color: "#c2c2c2"
                Layout.alignment: Qt.AlignHCenter
            }
            Item { Layout.fillWidth: true }
        }

        // Две колонки с настройками
        RowLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            spacing: 15

            // Левая колонка
            ColumnLayout {
                Layout.fillWidth: true
                Layout.fillHeight: true
                spacing: 10

                // Информация
                Rectangle {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    color: "#99252525"
                    radius: 8
                    border.color: "#50ffffff"
                    border.width: 1

                    ColumnLayout {
                        anchors.fill: parent
                        anchors.margins: 20
                        spacing: 15

                        Text {
                            text: "⚡ Детекция кастбара"
                            color: "#c2c2c2"
                            font.pointSize: 14
                            font.bold: true
                            Layout.fillWidth: true
                        }

                        Text {
                            text: "Детекция кастбара позволяет точно определить момент завершения каста и автоматически сменить сет в нужный момент."
                            color: "#b0b0b0"
                            font.pointSize: 10
                            wrapMode: Text.WordWrap
                            Layout.fillWidth: true
                        }

                        Rectangle {
                            Layout.fillWidth: true
                            height: 1
                            color: "#50ffffff"
                        }

                        // Чекбокс включения
                        CheckBox {
                            id: castbarEnabledCheck
                            checked: false
                            font.pointSize: 11
                            property string accentColor: settingsCastbarPage.accentColor
                            Component.onCompleted: {
                                checked = safeSettings.castbar_enabled
                            }
                            indicator: Rectangle {
                                implicitWidth: 18; implicitHeight: 18; radius: 4
                                color: castbarEnabledCheck.checked ? castbarEnabledCheck.accentColor : "#3a3a3a"
                                border.color: castbarEnabledCheck.checked ? "#60ffffff" : "#505050"
                                border.width: 1
                                Rectangle {
                                    width: 10; height: 10; radius: 4; color: "#99252525"
                                    anchors.centerIn: parent; visible: castbarEnabledCheck.checked
                                }
                            }
                            contentItem: RowLayout {
                                spacing: 8
                                Text {
                                    text: castbarEnabledCheck.checked ? "✓ ВКЛ" : "○ ВЫКЛ"
                                    color: castbarEnabledCheck.checked ? castbarEnabledCheck.accentColor : "#606060"
                                    font.pointSize: 9
                                    font.bold: castbarEnabledCheck.checked
                                    verticalAlignment: Text.AlignVCenter
                                    leftPadding: 24
                                }
                            }
                            onClicked: {
                                backend.set_setting("castbar_enabled", castbarEnabledCheck.checked)
                            }
                        }

                        Text {
                            text: "Включите для автоматической детекции кастбара во время выполнения макросов"
                            color: "#b0b0b0"
                            font.pointSize: 9
                            wrapMode: Text.WordWrap
                            Layout.fillWidth: true
                        }

                        Item { Layout.fillHeight: true }

                        // Порог срабатывания
                        ColumnLayout {
                            Layout.fillWidth: true
                            spacing: 8

                            RowLayout {
                                Layout.fillWidth: true
                                Label {
                                    text: "Порог совпадения:"
                                    color: "#c2c2c2"
                                    font.pointSize: 10
                                    font.bold: true
                                }
                                Text {
                                    text: Math.round(castbarThresholdSlider.value) + "%"
                                    color: settingsCastbarPage.accentColor
                                    font.pointSize: 11
                                    font.bold: true
                                }
                            }

                            Slider {
                                id: castbarThresholdSlider
                                Layout.fillWidth: true
                                from: 1
                                to: 100
                                stepSize: 1
                                value: safeSettings.castbar_threshold !== undefined ? safeSettings.castbar_threshold : 70
                                property bool updating: false
                                onValueChanged: {
                                    if (!updating && visible) {
                                        backend.set_setting("castbar_threshold", Math.round(value))
                                    }
                                }
                            }

                            Text {
                                text: "Чем меньше значение, тем точнее должно быть совпадение цвета"
                                color: "#b0b0b0"
                                font.pointSize: 9
                                wrapMode: Text.WordWrap
                                Layout.fillWidth: true
                            }
                        }

                        Item { Layout.fillHeight: true }
                    }
                }
            }

            // Правая колонка
            ColumnLayout {
                Layout.fillWidth: true
                Layout.fillHeight: true
                spacing: 10

                // Калибровка цвета
                Rectangle {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    color: "#99252525"
                    radius: 8
                    border.color: "#50ffffff"
                    border.width: 1

                    ColumnLayout {
                        anchors.fill: parent
                        anchors.margins: 20
                        spacing: 15

                        Text {
                            text: "🎨 Калибровка цвета"
                            color: "#c2c2c2"
                            font.pointSize: 14
                            font.bold: true
                            Layout.fillWidth: true
                        }

                        Text {
                            text: "Нажмите кнопку и наведите курсор на статичный элемент кастбара (ромбик). После начала калибровки нажмите ЛКМ для захвата цвета."
                            color: "#b0b0b0"
                            font.pointSize: 9
                            wrapMode: Text.WordWrap
                            Layout.fillWidth: true
                        }

                        Rectangle {
                            Layout.fillWidth: true
                            height: 1
                            color: "#50ffffff"
                        }

                        // Кнопка калибровки
                        BaseButton {
                            text: "◈ Начать калибровку"
                            Layout.fillWidth: true
                            implicitHeight: 45
                            iconSize: 14
                            textSize: 12
                            onClicked: {
                                console.log("SettingsCastbarPage: Открытие CastBarDialog")
                                castbarDialog.calibrationState = "ready"
                                castbarDialog.visible = true
                                castbarDialog.raise()
                                castbarDialog.requestActivate()
                            }
                        }

                        Item { Layout.fillHeight: true }

                        // Статус калибровки и предпросмотр цвета
                        ColumnLayout {
                            Layout.fillWidth: true
                            spacing: 10
                            visible: calibrationStatusText.text !== ""

                            Text {
                                id: calibrationStatusText
                                text: ""
                                color: settingsCastbarPage.accentColor
                                font.pointSize: 11
                                font.bold: true
                                horizontalAlignment: Text.AlignHCenter
                                Layout.fillWidth: true
                            }

                            // Предпросмотр захваченного цвета
                            Rectangle {
                                id: colorPreviewRect
                                Layout.fillWidth: true
                                Layout.preferredHeight: 60
                                radius: 8
                                border.color: "#60ffffff"
                                border.width: 2
                                color: "#99252525"
                            }
                        }
                    }
                }
            }
        }

        // Кнопка сохранения внизу
        RowLayout {
            Layout.fillWidth: true
            Layout.preferredHeight: 50
            spacing: 0
            Item { Layout.fillWidth: true }
            BaseButton {
                text: "◈ Сохранить"
                implicitWidth: 160
                implicitHeight: 40
                iconSize: 14
                textSize: 11
                onClicked: backend.save_all_settings()
            }
            Item { Layout.fillWidth: true }
        }
    }
}
