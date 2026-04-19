import QtQuick 2.15
import QtQuick.Controls.Basic 2.15
import QtQuick.Layouts 1.15
import QtQml 2.15

Item {
    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 20
        spacing: 15

        Text {
            text: "◈ Настройки"
            font.pointSize: 20
            font.bold: true
            color: "#c2c2c2"
        }

        TabBar {
            id: tabBar
            currentIndex: 0
            background: Rectangle { color: "#20ffffff"; radius: 4 }

            Repeater {
                model: ["⚔ Ресвап", "◑ Движение", "◈ OCR", "◈ Сеть", "◈ Прочее"]
                TabButton {
                    text: modelData
                    font.pointSize: 10
                    contentItem: RowLayout {
                        spacing: 6
                        Text { text: text; color: "#c2c2c2"; font.pointSize: 10 }
                    }
                }
            }
        }

        StackLayout {
            currentIndex: tabBar.currentIndex
            Layout.fillWidth: true
            Layout.fillHeight: true

            // Ресвап
            ScrollView {
                ScrollBar.vertical.policy: ScrollBar.AsNeeded
                ColumnLayout {
                    width: parent.width
                    spacing: 12

                    GridLayout {
                        Layout.fillWidth: true
                        columns: 2
                        columnSpacing: 15
                        rowSpacing: 10
                        
                        Label { 
                            text: "▣ Сет пения:"
                            color: "#c2c2c2"
                            font.pointSize: 10
                            Layout.fillWidth: true
                        }
                        TextField {
                            Layout.fillWidth: true
                            Layout.minimumWidth: 150
                            text: backend.settings.swap_key_chant
                            onEditingFinished: backend.set_setting("swap_key_chant", text)
                            Layout.preferredHeight: 28
                            background: Rectangle { radius: 4; color: "#40ffffff" }
                        }

                        Label { 
                            text: "◈ Сет ПА:"
                            color: "#c2c2c2"
                            font.pointSize: 10
                            Layout.fillWidth: true
                        }
                        TextField {
                            Layout.fillWidth: true
                            Layout.minimumWidth: 150
                            text: backend.settings.swap_key_pa
                            onEditingFinished: backend.set_setting("swap_key_pa", text)
                            Layout.preferredHeight: 28
                            background: Rectangle { radius: 4; color: "#40ffffff" }
                        }

                        Label { 
                            text: "◈ Бонус пения (%):"
                            color: "#c2c2c2"
                            font.pointSize: 10
                            Layout.fillWidth: true
                        }
                        TextField {
                            Layout.fillWidth: true
                            Layout.minimumWidth: 150
                            text: backend.settings.base_channeling
                            validator: IntValidator { bottom: 0; top: 200 }
                            onEditingFinished: backend.set_setting("base_channeling", text)
                            Layout.preferredHeight: 28
                            background: Rectangle { radius: 4; color: "#40ffffff" }
                        }

                        Label { 
                            text: "◈ Запас по кулдауну (мс):"
                            color: "#c2c2c2"
                            font.pointSize: 10
                            Layout.fillWidth: true
                        }
                        TextField {
                            Layout.fillWidth: true
                            Layout.minimumWidth: 150
                            text: Math.round((backend.settings.cooldown_margin || 0) * 1000)
                            validator: IntValidator { bottom: 0; top: 5000 }
                            onEditingFinished: backend.set_setting("cooldown_margin", parseFloat(text) / 1000)
                            Layout.preferredHeight: 28
                            background: Rectangle { radius: 4; color: "#40ffffff" }
                        }
                    }
                }
            }

            // Движение
            ScrollView {
                ColumnLayout {
                    width: parent.width
                    spacing: 12

                    CheckBox {
                        id: movementDelayCheckbox
                        text: "◈ Задержка после движения"
                        checked: backend.settings.movement_delay_enabled
                        onClicked: backend.set_setting("movement_delay_enabled", checked)
                        font.pointSize: 10
                        indicator: Rectangle {
                            width: 20; height: 20; radius: 4
                            color: movementDelayCheckbox.checked ? "#c0ffffff" : "#40ffffff"
                            border.color: "#60ffffff"; border.width: 1
                        }
                    }

                    GridLayout {
                        Layout.fillWidth: true
                        columns: 2
                        columnSpacing: 15
                        rowSpacing: 10

                        Label { 
                            text: "◈ Задержка (мс):"
                            color: "#c2c2c2"
                            font.pointSize: 10
                            Layout.fillWidth: true
                        }
                        TextField {
                            Layout.fillWidth: true
                            Layout.minimumWidth: 150
                            text: backend.settings.movement_delay_ms
                            validator: IntValidator { bottom: 0; top: 2000 }
                            onEditingFinished: backend.set_setting("movement_delay_ms", text)
                            Layout.preferredHeight: 28
                            background: Rectangle { radius: 4; color: "#40ffffff" }
                        }

                        Label { 
                            text: "◈ Допуск (м):"
                            color: "#c2c2c2"
                            font.pointSize: 10
                            Layout.fillWidth: true
                        }
                        TextField {
                            Layout.fillWidth: true
                            Layout.minimumWidth: 150
                            text: backend.settings.distance_tolerance
                            validator: DoubleValidator { decimals: 2; notation: DoubleValidator.StandardNotation }
                            onEditingFinished: backend.set_setting("distance_tolerance", text)
                            Layout.preferredHeight: 28
                            background: Rectangle { radius: 4; color: "#40ffffff" }
                        }

                        Label { 
                            text: "◈ Интервал обновления (сек):"
                            color: "#c2c2c2"
                            font.pointSize: 10
                            Layout.fillWidth: true
                        }
                        TextField {
                            Layout.fillWidth: true
                            Layout.minimumWidth: 150
                            text: backend.settings.target_interval
                            validator: DoubleValidator { decimals: 2; bottom: 0.1; top: 5 }
                            onEditingFinished: backend.set_setting("target_interval", text)
                            Layout.preferredHeight: 28
                            background: Rectangle { radius: 4; color: "#40ffffff" }
                        }
                    }

                    CheckBox {
                        id: checkDistanceCheckbox
                        text: "◈ Учитывать дистанцию (OCR)"
                        checked: backend.settings.check_distance
                        onClicked: backend.set_setting("check_distance", checked)
                        font.pointSize: 10
                        indicator: Rectangle {
                            width: 20; height: 20; radius: 4
                            color: checkDistanceCheckbox.checked ? "#c0ffffff" : "#40ffffff"
                            border.color: "#60ffffff"; border.width: 1
                        }
                    }
                }
            }

            // OCR
            ScrollView {
                ColumnLayout {
                    width: parent.width
                    spacing: 12

                    GridLayout {
                        Layout.fillWidth: true
                        columns: 2
                        columnSpacing: 15
                        rowSpacing: 10

                        Label { 
                            text: "◈ Масштаб:"
                            color: "#c2c2c2"
                            font.pointSize: 10
                            Layout.fillWidth: true
                        }
                        TextField {
                            Layout.fillWidth: true
                            Layout.minimumWidth: 150
                            text: backend.settings.ocr_scale
                            validator: IntValidator { bottom: 1; top: 30 }
                            onEditingFinished: backend.set_setting("ocr_scale", text)
                            Layout.preferredHeight: 28
                            background: Rectangle { radius: 4; color: "#40ffffff" }
                        }

                        Label { 
                            text: "◈ PSM:"
                            color: "#c2c2c2"
                            font.pointSize: 10
                            Layout.fillWidth: true
                        }
                        ComboBox {
                            id: psmCombo
                            Layout.fillWidth: true
                            Layout.minimumWidth: 150
                            model: ["6 (блок текста)", "7 (одна строка)", "10 (один символ)", "13 (сырой текст)"]
                            currentIndex: {
                                var val = backend.settings.ocr_psm;
                                if (val === 6) return 0;
                                else if (val === 7) return 1;
                                else if (val === 10) return 2;
                                else return 3;
                            }
                            onActivated: {
                                var newVal = [6,7,10,13][currentIndex];
                                backend.set_setting("ocr_psm", newVal);
                            }
                            Layout.preferredHeight: 28
                            background: Rectangle { radius: 4; color: "#40ffffff" }
                        }
                    }

                    CheckBox {
                        id: morphCheckbox
                        text: "◈ Морфология"
                        checked: backend.settings.ocr_use_morph
                        onClicked: backend.set_setting("ocr_use_morph", checked)
                        font.pointSize: 10
                        indicator: Rectangle {
                            width: 20; height: 20; radius: 4
                            color: morphCheckbox.checked ? "#c0ffffff" : "#40ffffff"
                            border.color: "#60ffffff"; border.width: 1
                        }
                    }

                    Rectangle { height: 1; Layout.fillWidth: true; color: "#60ffffff" }

                    Label { text: "◈ Область моба (x1,y1,x2,y2):"; color: "#c2c2c2"; font.pointSize: 10; font.bold: true }
                    RowLayout {
                        spacing: 5
                        AreaCoordinateInput {
                            areaValue: backend.settings.mob_area
                            coordinateIndex: 0
                            areaKey: "mob_area"
                            defaultValue: [1084, 271, 1545, 358]
                            text: (backend.settings.mob_area !== undefined && backend.settings.mob_area[0] !== undefined) ? backend.settings.mob_area[0] : 1084
                        }
                        AreaCoordinateInput {
                            areaValue: backend.settings.mob_area
                            coordinateIndex: 1
                            areaKey: "mob_area"
                            defaultValue: [1084, 271, 1545, 358]
                            text: (backend.settings.mob_area !== undefined && backend.settings.mob_area[1] !== undefined) ? backend.settings.mob_area[1] : 271
                        }
                        AreaCoordinateInput {
                            areaValue: backend.settings.mob_area
                            coordinateIndex: 2
                            areaKey: "mob_area"
                            defaultValue: [1084, 271, 1545, 358]
                            text: (backend.settings.mob_area !== undefined && backend.settings.mob_area[2] !== undefined) ? backend.settings.mob_area[2] : 1545
                        }
                        AreaCoordinateInput {
                            areaValue: backend.settings.mob_area
                            coordinateIndex: 3
                            areaKey: "mob_area"
                            defaultValue: [1084, 271, 1545, 358]
                            text: (backend.settings.mob_area !== undefined && backend.settings.mob_area[3] !== undefined) ? backend.settings.mob_area[3] : 358
                        }
                    }

                    Label { text: "◈ Область игрока (x1,y1,x2,y2):"; color: "#c2c2c2"; font.pointSize: 10; font.bold: true }
                    RowLayout {
                        spacing: 5
                        AreaCoordinateInput {
                            areaValue: backend.settings.player_area
                            coordinateIndex: 0
                            areaKey: "player_area"
                            defaultValue: [1271, 16, 1294, 32]
                            text: (backend.settings.player_area !== undefined && backend.settings.player_area[0] !== undefined) ? backend.settings.player_area[0] : 1271
                        }
                        AreaCoordinateInput {
                            areaValue: backend.settings.player_area
                            coordinateIndex: 1
                            areaKey: "player_area"
                            defaultValue: [1271, 16, 1294, 32]
                            text: (backend.settings.player_area !== undefined && backend.settings.player_area[1] !== undefined) ? backend.settings.player_area[1] : 16
                        }
                        AreaCoordinateInput {
                            areaValue: backend.settings.player_area
                            coordinateIndex: 2
                            areaKey: "player_area"
                            defaultValue: [1271, 16, 1294, 32]
                            text: (backend.settings.player_area !== undefined && backend.settings.player_area[2] !== undefined) ? backend.settings.player_area[2] : 1294
                        }
                        AreaCoordinateInput {
                            areaValue: backend.settings.player_area
                            coordinateIndex: 3
                            areaKey: "player_area"
                            defaultValue: [1271, 16, 1294, 32]
                            text: (backend.settings.player_area !== undefined && backend.settings.player_area[3] !== undefined) ? backend.settings.player_area[3] : 32
                        }
                    }
                }
            }

            // Сеть
            ScrollView {
                ColumnLayout {
                    width: parent.width
                    spacing: 8
                    
                    CheckBox {
                        id: pingAutoCheckbox
                        text: "◈ Автоопределение пинга"
                        checked: backend.settings.ping_auto
                        onClicked: backend.set_setting("ping_auto", checked)
                        font.pointSize: 10
                        indicator: Rectangle { 
                            width: 20; height: 20; radius: 4
                            color: pingAutoCheckbox.checked ? "#c0ffffff" : "#40ffffff"
                            border.color: "#60ffffff"; border.width: 1
                        }
                    }
                    
                    Label { text: "💻 Процесс игры:"; color: "#c2c2c2"; font.pointSize: 10 }
                    TextField {
                        text: backend.settings.process_name
                        onEditingFinished: backend.set_setting("process_name", text)
                        Layout.preferredHeight: 28
                        background: Rectangle { radius: 4; color: "#40ffffff" }
                    }
                    
                    Label { text: "🌐 IP сервера:"; color: "#c2c2c2"; font.pointSize: 10 }
                    TextField {
                        text: backend.settings.server_ip
                        onEditingFinished: backend.set_setting("server_ip", text)
                        Layout.preferredHeight: 28
                        background: Rectangle { radius: 4; color: "#40ffffff" }
                    }
                    
                    Label {
                        text: "◈ Текущий пинг: " + backend.ping + " мс"
                        color: "#c2c2c2"
                        font.pointSize: 10
                    }
                }
            }

            // Прочее
            ScrollView {
                ColumnLayout {
                    width: parent.width
                    spacing: 8

                    // Привязка к окну
                    GroupBox {
                        title: "◈ Привязка к окну"
                        Layout.fillWidth: true
                        background: Rectangle { color: "#20ffffff"; radius: 4; border.color: "#40ffffff"; border.width: 1 }
                        contentItem: ColumnLayout {
                            spacing: 8

                            CheckBox {
                                id: windowLockedCheck
                                text: "Привязываться к окну"
                                checked: backend.window_locked
                                onCheckedChanged: backend.window_locked = checked
                                font.pointSize: 10
                                indicator: Rectangle {
                                    implicitWidth: 16
                                    implicitHeight: 16
                                    radius: 4
                                    color: windowLockedCheck.checked ? "#7793a1" : "#40ffffff"
                                    border.color: "#60ffffff"
                                    border.width: 1
                                    Rectangle {
                                        width: 10; height: 10
                                        color: "#99252525"
                                        anchors.centerIn: parent
                                        visible: windowLockedCheck.checked
                                    }
                                }
                                contentItem: Text {
                                    text: windowLockedCheck.text
                                    color: "#c2c2c2"
                                    font.pointSize: 10
                                    verticalAlignment: Text.AlignVCenter
                                    leftPadding: 20
                                }
                            }

                            RowLayout {
                                Layout.fillWidth: true
                                spacing: 8

                                TextField {
                                    id: windowTitleEdit
                                    Layout.fillWidth: true
                                    text: backend.target_window_title
                                    placeholderText: "Заголовок окна (например, Asgard Perfect World)"
                                    font.pointSize: 9
                                    background: Rectangle { radius: 4; color: "#40ffffff" }
                                    onTextChanged: backend.target_window_title = text
                                }

                                BaseButton {
                                    text: "Выбрать"
                                    implicitWidth: 80
                                    implicitHeight: 28
                                    iconSize: 0
                                    textSize: 9
                                    onClicked: backend.selectWindowFromList()
                                }
                            }

                            Label {
                                text: "Макросы будут работать только когда активно указанное окно"
                                color: "#a0a0a0"
                                font.pointSize: 8
                                wrapMode: Text.WordWrap
                                Layout.fillWidth: true
                            }
                        }
                    }

                    Label { text: "◈ Глобальная задержка шага (мс):"; color: "#c2c2c2"; font.pointSize: 10 }
                    TextField {
                        text: backend.settings.global_step_delay
                        validator: DoubleValidator { bottom: 0.0; top: 500.0; decimals: 2; notation: DoubleValidator.StandardNotation; locale: Locale.c }
                        onEditingFinished: backend.set_setting("global_step_delay", text)
                        Layout.preferredHeight: 28
                        background: Rectangle { radius: 4; color: "#40ffffff" }
                    }
                }
            }
        }

        BaseButton {
            text: "◈ Сохранить настройки"
            Layout.alignment: Qt.AlignRight
            implicitWidth: 140
            implicitHeight: 36
            iconSize: 14
            textSize: 10
            onClicked: backend.save_all_settings()
        }
    }
}
