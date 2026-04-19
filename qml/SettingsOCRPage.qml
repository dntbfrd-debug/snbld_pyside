import QtQuick 2.15
import QtQuick.Controls.Basic 2.15
import QtQuick.Layouts 1.15

Item {
    id: settingsOCRPage

    // Принудительное обновление привязок при изменении настроек
    property var forceUpdate: backend && backend.settings ? backend.settings : ({})
    Connections {
        target: backend
        function onSettingsChanged() {
            settingsOCRPage.forceUpdate = backend.settings
        }
    }

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 20
        anchors.bottomMargin: 70
        spacing: 15

        // Заголовок с кнопкой назад
        RowLayout {
            Layout.fillWidth: true
            BaseButton {
                text: "← Назад"
                implicitWidth: 80
                implicitHeight: 30
                iconSize: 0
                textSize: 10
                onClicked: settingsOCRPage.StackView.view.pop()
            }
            Text {
                text: "▫ OCR — Настройки"
                font.pointSize: 18
                font.bold: true
                color: "#c2c2c2"
                Layout.alignment: Qt.AlignHCenter
            }
            Item { Layout.fillWidth: true }
        }

        ColumnLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            Layout.alignment: Qt.AlignHCenter | Qt.AlignTop
            spacing: 15

            GroupBox {
                title: "Масштаб распознавания"
                Layout.fillWidth: true
                background: Rectangle { color: "#99252525"; radius: 8; border.color: "#50ffffff"; border.width: 1 }
                contentItem: ColumnLayout {
                    spacing: 12

                    GridLayout {
                        Layout.fillWidth: true
                        columns: 2
                        columnSpacing: 15
                        rowSpacing: 10

                        Label {
                            text: "Масштаб:"
                            color: "#c2c2c2"
                            font.pointSize: 10
                            font.bold: true
                            Layout.fillWidth: true
                        }
                        TextField {
                            Layout.fillWidth: true
                            Layout.minimumWidth: 150
                            text: backend.settings.ocr_scale || 10
                            font.pointSize: 11
                            horizontalAlignment: Text.AlignHCenter
                            background: Rectangle { radius: 6; color: "#40ffffff" }
                            onEditingFinished: backend.set_setting("ocr_scale", text)
                        }
                    }

                    Text {
                        text: "Масштабирование изображения для распознавания (10 = 1000%)"
                        color: "#808080"
                        font.pointSize: 9
                        wrapMode: Text.WordWrap
                        Layout.fillWidth: true
                    }
                }
            }

            GroupBox {
                title: "Режим сегментации (PSM)"
                Layout.fillWidth: true
                background: Rectangle { color: "#99252525"; radius: 8; border.color: "#50ffffff"; border.width: 1 }
                contentItem: ColumnLayout {
                    spacing: 12

                    GridLayout {
                        Layout.fillWidth: true
                        columns: 2
                        columnSpacing: 15
                        rowSpacing: 10

                        Label {
                            text: "PSM:"
                            color: "#c2c2c2"
                            font.pointSize: 10
                            font.bold: true
                            Layout.fillWidth: true
                        }
                        TextField {
                            Layout.fillWidth: true
                            Layout.minimumWidth: 150
                            text: backend.settings.ocr_psm || 10
                            font.pointSize: 11
                            horizontalAlignment: Text.AlignHCenter
                            background: Rectangle { radius: 6; color: "#40ffffff" }
                            onEditingFinished: backend.set_setting("ocr_psm", text)
                        }
                    }

                    Text {
                        text: "Режим Tesseract: 6 = блок текста, 7 = строка, 10 = символ, 13 = сырой текст"
                        color: "#808080"
                        font.pointSize: 9
                        wrapMode: Text.WordWrap
                        Layout.fillWidth: true
                    }
                }
            }

            GroupBox {
                title: "Морфологическая обработка"
                Layout.fillWidth: true
                background: Rectangle { color: "#99252525"; radius: 8; border.color: "#50ffffff"; border.width: 1 }
                contentItem: ColumnLayout {
                    spacing: 12

                    CheckBox {
                        id: useMorphCheck
                        checked: backend.settings.ocr_use_morph || false
                        font.pointSize: 11
                        property string accentColor: backend.settings.accent_color || "#7793a1"
                        indicator: Rectangle {
                            implicitWidth: 18; implicitHeight: 18; radius: 4
                            color: useMorphCheck.checked ? useMorphCheck.accentColor : "#3a3a3a"
                            border.color: useMorphCheck.checked ? "#60ffffff" : "#505050"
                            border.width: 1
                            Rectangle {
                                width: 10; height: 10; radius: 4; color: "#99252525"
                                anchors.centerIn: parent; visible: useMorphCheck.checked
                            }
                        }
                        contentItem: RowLayout {
                            spacing: 8
                            Text {
                                text: useMorphCheck.checked ? "✓ ВКЛ" : "○ ВЫКЛ"
                                color: useMorphCheck.checked ? useMorphCheck.accentColor : "#606060"
                                font.pointSize: 9
                                font.bold: useMorphCheck.checked
                                verticalAlignment: Text.AlignVCenter
                                leftPadding: 24
                            }
                        }
                        onCheckStateChanged: {
                            backend.set_setting("ocr_use_morph", checked)
                        }
                    }

                    Text {
                        text: "Использовать морфологическую обработку для улучшения распознавания"
                        color: "#808080"
                        font.pointSize: 9
                        wrapMode: Text.WordWrap
                        Layout.fillWidth: true
                    }
                }
            }

            // Кнопка сохранения
            RowLayout {
                Layout.fillWidth: true
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
}
