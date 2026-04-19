import QtQuick 2.15
import QtQuick.Controls.Basic 2.15
import QtQuick.Layouts 1.15

Item {
    id: settingsDelayPage
    
    property color accentColor: backend && backend.settings && backend.settings.accent_color ? backend.settings.accent_color : "#7793a1"

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 20
        anchors.bottomMargin: 70
        spacing: 10

        // Заголовок с кнопкой назад
        RowLayout {
            Layout.fillWidth: true
            BaseButton {
                text: "← Назад"
                implicitWidth: 80
                implicitHeight: 30
                iconSize: 0
                textSize: 10
                onClicked: settingsDelayPage.StackView.view.pop()
            }
            Text {
                text: "◈ Редактор задержек"
                font.pointSize: 18
                font.bold: true
                color: "#c2c2c2"
                Layout.alignment: Qt.AlignHCenter
            }
            Item { Layout.fillWidth: true }
        }

        // Две плитки рядом (горизонтально)
        RowLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            Layout.minimumHeight: 220
            spacing: 12

            // ========== ПЛИТКА 1: ФИКСИРОВАННЫЕ ЗАДЕРЖКИ ==========
            GroupBox {
                title: "🔧 Фиксированные задержки"
                Layout.fillWidth: true
                Layout.fillHeight: true
                background: Rectangle { color: "#99252525"; radius: 8; border.color: "#50ffffff"; border.width: 1 }
                
                contentItem: ColumnLayout {
                    spacing: 8

                    // Чекбокс ВКЛ/ВЫКЛ
                    CheckBox {
                        id: fixedDelaysCheck
                        checked: backend && backend.settings ? (backend.settings.use_fixed_delays || true) : true
                        font.pointSize: 10
                        property string accentColor: backend && backend.settings ? (backend.settings.accent_color || "#7793a1") : "#7793a1"
                        
                        indicator: Rectangle {
                            implicitWidth: 18; implicitHeight: 18; radius: 4
                            color: fixedDelaysCheck.checked ? fixedDelaysCheck.accentColor : "#3a3a3a"
                            border.color: fixedDelaysCheck.checked ? "#60ffffff" : "#505050"
                            border.width: 1
                            Rectangle {
                                width: 10; height: 10; radius: 4; color: "#99252525"
                                anchors.centerIn: parent
                                visible: fixedDelaysCheck.checked
                            }
                        }
                        
                        contentItem: RowLayout {
                            spacing: 8
                            Text {
                                text: fixedDelaysCheck.checked ? "✓ ВКЛ" : "○ ВЫКЛ"
                                color: fixedDelaysCheck.checked ? fixedDelaysCheck.accentColor : "#606060"
                                font.pointSize: 11
                                font.bold: fixedDelaysCheck.checked
                                verticalAlignment: Text.AlignVCenter
                                leftPadding: 24
                            }
                        }
                        
                        onCheckStateChanged: {
                            if (checked) {
                                backend.set_setting("use_fixed_delays", true)
                                backend.set_setting("use_ping_delays", false)
                                pingDelaysCheck.checked = false
                            }
                        }
                    }

                    // Поля ввода задержек
                    GridLayout {
                        Layout.fillWidth: true
                        columns: 2
                        columnSpacing: 15
                        rowSpacing: 10

                        Label {
                            text: "Задержка 1 шага (мс):"
                            color: "#c2c2c2"
                            font.pointSize: 9
                            font.bold: true
                            Layout.fillWidth: true
                        }
                        TextField {
                            Layout.fillWidth: true
                            Layout.minimumWidth: 150
                            text: backend && backend.settings ? (backend.settings.first_step_delay || 90) : 90
                            font.pointSize: 10
                            horizontalAlignment: Text.AlignHCenter
                            validator: IntValidator { bottom: 0; top: 1000 }
                            background: Rectangle { radius: 6; color: "#40ffffff" }
                            onEditingFinished: backend.set_setting("first_step_delay", parseInt(text) || 90)
                        }

                        Label {
                            text: "Задержка 2-3 шага (мс):"
                            color: "#c2c2c2"
                            font.pointSize: 9
                            font.bold: true
                            Layout.fillWidth: true
                        }
                        TextField {
                            Layout.fillWidth: true
                            Layout.minimumWidth: 150
                            text: backend && backend.settings ? (backend.settings.global_step_delay || 15) : 15
                            font.pointSize: 10
                            horizontalAlignment: Text.AlignHCenter
                            validator: IntValidator { bottom: 0; top: 500 }
                            background: Rectangle { radius: 6; color: "#40ffffff" }
                            onEditingFinished: backend.set_setting("global_step_delay", parseInt(text) || 15)
                        }
                    }

                    Text {
                        text: "⚠ Фиксированные задержки"
                        color: "#a0a0a0"
                        font.pointSize: 8
                        font.italic: true
                        Layout.fillWidth: true
                    }
                }
            }

            // ========== ПЛИТКА 2: АВТО ЗАДЕРЖКИ (ПИНГ) ==========
            GroupBox {
                title: "📡 Авто задержки (пинг)"
                Layout.fillWidth: true
                Layout.fillHeight: true
                background: Rectangle { color: "#99252525"; radius: 8; border.color: "#50ffffff"; border.width: 1 }
                
                contentItem: ColumnLayout {
                    spacing: 8

                    // Чекбокс ВКЛ/ВЫКЛ
                    CheckBox {
                        id: pingDelaysCheck
                        checked: backend && backend.settings ? (backend.settings.use_ping_delays || false) : false
                        enabled: backend && backend.settings ? (backend.settings.ping_auto || false) : false  // Заблокирован если ping_auto выключен
                        font.pointSize: 10
                        property string accentColor: backend && backend.settings ? (backend.settings.accent_color || "#7793a1") : "#7793a1"

                        indicator: Rectangle {
                            implicitWidth: 18; implicitHeight: 18; radius: 4
                            color: !pingDelaysCheck.enabled ? "#505050" : (pingDelaysCheck.checked ? pingDelaysCheck.accentColor : "#3a3a3a")
                            border.color: !pingDelaysCheck.enabled ? "#404040" : (pingDelaysCheck.checked ? "#60ffffff" : "#505050")
                            border.width: 1
                            Rectangle {
                                width: 10; height: 10; radius: 4; color: "#99252525"
                                anchors.centerIn: parent
                                visible: pingDelaysCheck.checked
                            }
                        }

                        contentItem: RowLayout {
                            spacing: 8
                            Text {
                                text: pingDelaysCheck.checked ? "✓ ВКЛ" : "○ ВЫКЛ"
                                color: !pingDelaysCheck.enabled ? "#606060" : (pingDelaysCheck.checked ? pingDelaysCheck.accentColor : "#606060")
                                font.pointSize: 11
                                font.bold: pingDelaysCheck.checked
                                verticalAlignment: Text.AlignVCenter
                                leftPadding: 24
                            }
                        }

                        onCheckStateChanged: {
                            if (checked) {
                                backend.set_setting("use_ping_delays", true)
                                backend.set_setting("use_fixed_delays", false)
                                fixedDelaysCheck.checked = false
                            }
                        }
                    }

                    // Подсказка если ping_auto выключен
                    Text {
                        text: "⚠ Включите автоизмерение пинга в настройках Сеть"
                        color: "#FFA500"
                        font.pointSize: 10
                        font.bold: true
                        font.italic: true
                        visible: !pingDelaysCheck.enabled
                        Layout.fillWidth: true
                        horizontalAlignment: Text.AlignHCenter
                    }

                    // Информация о пинге
                    ColumnLayout {
                        Layout.fillWidth: true
                        spacing: 6

                        RowLayout {
                            Layout.fillWidth: true
                            Text {
                                text: "ICMP:"
                                color: "#c2c2c2"
                                font.pointSize: 10
                            }
                            Text {
                                text: (backend && backend.ping !== undefined) ? (backend.ping + " мс") : "0 мс"
                                color: backend && backend.settings ? backend.settings.accent_color : "#7793a1"
                                font.pointSize: 14
                                font.bold: true
                            }
                            Item { Layout.fillWidth: true }
                            Text {
                                text: "Игровой:"
                                color: "#c2c2c2"
                                font.pointSize: 10
                            }
                            Text {
                                text: (backend && backend.ping !== undefined) ? (Math.round(backend.ping * 3) + " мс") : "0 мс"
                                color: backend && backend.settings ? backend.settings.accent_color : "#7793a1"
                                font.pointSize: 14
                                font.bold: true
                            }
                        }

                        Rectangle {
                            Layout.fillWidth: true
                            height: 1
                            color: "#40ffffff"
                        }

                        RowLayout {
                            Layout.fillWidth: true
                            Text {
                                text: "Компенсация:"
                                color: "#c2c2c2"
                                font.pointSize: 10
                            }
                            Item { Layout.fillWidth: true }
                            Text {
                                text: (backend && typeof backend.getPingCompensation === 'function') ? ("+" + Math.round(backend.getPingCompensation() * 1000) + " мс") : "+0 мс"
                                color: "#4CAF50"
                                font.pointSize: 14
                                font.bold: true
                            }
                        }

                        Rectangle {
                            Layout.fillWidth: true
                            height: 1
                            color: "#40ffffff"
                        }

                        Text {
                            text: "✓ Включите если у вас высокий пинг в игре"
                            color: "#a0a0a0"
                            font.pointSize: 9
                            font.italic: true
                            horizontalAlignment: Text.AlignHCenter
                        }
                    }
                }
            }
        }

        // ========== ПЛИТКА 3: ЗАПАС ПО КУЛДАУНУ (под ними) ==========
        GroupBox {
            title: "🛡️ Защита от быстрых и случайных нажатий"
            Layout.fillWidth: true
            Layout.preferredHeight: 160
            background: Rectangle { color: "#99252525"; radius: 8; border.color: "#50ffffff"; border.width: 1 }

            contentItem: ColumnLayout {
                spacing: 8

                // Поправка отката скилла на пинг сервера (мс)
                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: 6

                    RowLayout {
                        Layout.fillWidth: true
                        Label {
                            text: "Поправка отката скилла на пинг сервера:"
                            color: "#c2c2c2"
                            font.pointSize: 10
                            font.bold: true
                        }
                        Text {
                            text: Math.round(cooldownMarginSlider.value).toFixed(0) + " мс"
                            color: settingsDelayPage.accentColor || "#7793a1"
                            font.pointSize: 11
                            font.bold: true
                        }
                    }

                    Slider {
                        id: cooldownMarginSlider
                        Layout.fillWidth: true
                        Layout.preferredHeight: 25
                        from: 0
                        to: 1000
                        stepSize: 50
                        value: 300
                        enabled: true
                        visible: true
                        Component.onCompleted: {
                            var margin = backend.settings.cooldown_margin
                            if (margin !== undefined && margin > 0) {
                                value = margin * 1000
                            } else {
                                value = 300
                            }
                            console.log("Cooldown margin slider initialized to:", value, "ms (setting:", backend.settings.cooldown_margin, ")")
                        }
                        onMoved: {
                            console.log("Cooldown margin slider moved to:", value, "ms, setting value:", value / 1000)
                            backend.set_setting("cooldown_margin", value / 1000)
                            console.log("Cooldown margin setting called, current value in backend:", backend.settings.cooldown_margin)
                        }
                    }
                }

                // Блокировка одновременного запуска макросов (мс)
                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: 6

                    RowLayout {
                        Layout.fillWidth: true
                        Label {
                            text: "Блокировка одновременного запуска макросов:"
                            color: "#c2c2c2"
                            font.pointSize: 10
                            font.bold: true
                        }
                        Text {
                            text: Math.round(castLockMarginSlider.value).toFixed(0) + " мс"
                            color: settingsDelayPage.accentColor || "#7793a1"
                            font.pointSize: 11
                            font.bold: true
                        }
                    }

                    Slider {
                        id: castLockMarginSlider
                        Layout.fillWidth: true
                        Layout.preferredHeight: 25
                        from: 0
                        to: 500
                        stepSize: 50
                        value: 450
                        enabled: true
                        visible: true
                        Component.onCompleted: {
                            var margin = backend.settings.cast_lock_margin
                            if (margin !== undefined && margin > 0) {
                                value = margin * 1000
                            } else {
                                value = 450
                            }
                            console.log("Cast lock margin slider initialized to:", value, "ms (setting:", backend.settings.cast_lock_margin, ")")
                        }
                        onMoved: {
                            console.log("Cast lock margin slider moved to:", value, "ms, setting value:", value / 1000)
                            backend.set_setting("cast_lock_margin", value / 1000)
                            console.log("Cast lock margin setting called, current value in backend:", backend.settings.cast_lock_margin)
                        }
                    }
                }
            }
        }

        // Кнопка сохранения внизу по центру
        RowLayout {
            Layout.fillWidth: true
            Layout.preferredHeight: 55
            spacing: 0
            Item { Layout.fillWidth: true }
            BaseButton {
                text: "◈ Сохранить"
                implicitWidth: 160
                implicitHeight: 38
                iconSize: 14
                textSize: 10
                onClicked: backend.save_all_settings()
            }
            Item { Layout.fillWidth: true }
        }
    }

    // Инициализация при загрузке
    Component.onCompleted: {
        // Устанавливаем начальные значения чекбоксов
        fixedDelaysCheck.checked = backend.settings.use_fixed_delays !== undefined ? backend.settings.use_fixed_delays : true
        pingDelaysCheck.checked = backend.settings.use_ping_delays !== undefined ? backend.settings.use_ping_delays : false
        pingDelaysCheck.enabled = backend.settings.ping_auto !== undefined ? backend.settings.ping_auto : false
    }
    
    // Обновление акцентного цвета при изменении настроек
    Connections {
        target: backend
        function onSettingsChanged() {
            settingsDelayPage.accentColor = backend.settings.accent_color !== undefined && backend.settings.accent_color !== null ? backend.settings.accent_color : "#7793a1"
        }
    }
}
