import QtQuick 2.15
import QtQuick.Controls.Basic 2.15
import QtQuick.Layouts 1.15

Item {
    id: root
    visible: true
    clip: true

    property alias settingsStackView: root.parent

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 20
        spacing: 20

        // Заголовок с кнопкой назад
        RowLayout {
            Layout.fillWidth: true
            BaseButton {
                text: "← Назад"
                implicitWidth: 80
                implicitHeight: 30
                iconSize: 0
                textSize: 10
                onClicked: {
                    if (settingsStackView) {
                        settingsStackView.pop()
                    }
                }
            }
            Item { Layout.fillWidth: true }
        }

        Text {
            text: "Распознавание и детекция"
            color: "#c2c2c2"
            font.pointSize: 20
            font.bold: true
            horizontalAlignment: Text.AlignHCenter
            Layout.fillWidth: true
        }

        Text {
            text: "Настройте распознавание дистанции и детекцию каста"
            color: "#a0a0a0"
            font.pointSize: 13
            horizontalAlignment: Text.AlignHCenter
            Layout.fillWidth: true
        }

        // Две плитки в колонки
        RowLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            spacing: 20

            // === Плитка 1: Калибровка OCR ===
            Rectangle {
                id: ocrTile
                Layout.fillWidth: true
                Layout.fillHeight: true
                color: "#99252525"
                radius: 12
                border.color: "#50ffffff"
                border.width: 2

                property color accentColor: backend && backend.settings && backend.settings.accent_color !== undefined && backend.settings.accent_color !== null ? backend.settings.accent_color : "#7793a1"

                // Эффект свечения при наведении (8 слоёв, как в SkillClassSelector)
                Rectangle {
                    id: ocrGlow1
                    anchors.centerIn: parent
                    width: parent.width + 40; height: parent.height + 40
                    radius: 10 + 20
                    color: Qt.rgba(ocrTile.accentColor.r, ocrTile.accentColor.g, ocrTile.accentColor.b, ocrMouseArea.containsMouse ? 0.005 : 0)
                    z: 0
                }
                Rectangle {
                    id: ocrGlow2
                    anchors.centerIn: parent
                    width: parent.width + 35; height: parent.height + 35
                    radius: 10 + 17
                    color: Qt.rgba(ocrTile.accentColor.r, ocrTile.accentColor.g, ocrTile.accentColor.b, ocrMouseArea.containsMouse ? 0.01 : 0)
                    z: 0
                }
                Rectangle {
                    id: ocrGlow3
                    anchors.centerIn: parent
                    width: parent.width + 30; height: parent.height + 30
                    radius: 10 + 15
                    color: Qt.rgba(ocrTile.accentColor.r, ocrTile.accentColor.g, ocrTile.accentColor.b, ocrMouseArea.containsMouse ? 0.015 : 0)
                    z: 0
                }
                Rectangle {
                    id: ocrGlow4
                    anchors.centerIn: parent
                    width: parent.width + 25; height: parent.height + 25
                    radius: 10 + 12
                    color: Qt.rgba(ocrTile.accentColor.r, ocrTile.accentColor.g, ocrTile.accentColor.b, ocrMouseArea.containsMouse ? 0.02 : 0)
                    z: 0
                }
                Rectangle {
                    id: ocrGlow5
                    anchors.centerIn: parent
                    width: parent.width + 20; height: parent.height + 20
                    radius: 10 + 10
                    color: Qt.rgba(ocrTile.accentColor.r, ocrTile.accentColor.g, ocrTile.accentColor.b, ocrMouseArea.containsMouse ? 0.03 : 0)
                    z: 0
                }
                Rectangle {
                    id: ocrGlow6
                    anchors.centerIn: parent
                    width: parent.width + 15; height: parent.height + 15
                    radius: 10 + 7
                    color: Qt.rgba(ocrTile.accentColor.r, ocrTile.accentColor.g, ocrTile.accentColor.b, ocrMouseArea.containsMouse ? 0.04 : 0)
                    z: 0
                }
                Rectangle {
                    id: ocrGlow7
                    anchors.centerIn: parent
                    width: parent.width + 10; height: parent.height + 10
                    radius: 10 + 5
                    color: Qt.rgba(ocrTile.accentColor.r, ocrTile.accentColor.g, ocrTile.accentColor.b, ocrMouseArea.containsMouse ? 0.05 : 0)
                    z: 0
                }
                Rectangle {
                    id: ocrGlow8
                    anchors.centerIn: parent
                    width: parent.width + 6; height: parent.height + 6
                    radius: 10 + 3
                    color: Qt.rgba(ocrTile.accentColor.r, ocrTile.accentColor.g, ocrTile.accentColor.b, ocrMouseArea.containsMouse ? 0.06 : 0)
                    z: 0
                }

                MouseArea {
                    id: ocrMouseArea
                    anchors.fill: parent
                    hoverEnabled: true
                    cursorShape: Qt.PointingHandCursor
                    onClicked: backend.startOCRCalibration()
                }

                ColumnLayout {
                    anchors.centerIn: parent
                    spacing: 8

                    Image {
                        source: "../icons/ocr.png"
                        width: 56
                        height: 56
                        fillMode: Image.PreserveAspectFit
                        Layout.alignment: Qt.AlignHCenter
                    }

                    Text {
                        text: "Калибровка OCR"
                        font.pointSize: 16
                        font.bold: true
                        color: "#c2c2c2"
                        horizontalAlignment: Text.AlignHCenter
                        Layout.alignment: Qt.AlignHCenter
                    }

                    Text {
                        text: "Распознавание дистанции"
                        font.pointSize: 10
                        color: "#808080"
                        horizontalAlignment: Text.AlignHCenter
                        Layout.fillWidth: true
                    }

                    // Статус калибровки
                    RowLayout {
                        spacing: 8
                        Layout.alignment: Qt.AlignHCenter

                        Rectangle {
                            width: 18; height: 18; radius: 9
                            color: {
                                var area = backend && backend.settings ? backend.settings.mob_area : ""
                                return (area && area !== "") ? "#4CAF50" : "#555555"
                            }
                            Text {
                                anchors.centerIn: parent
                                text: "✓"
                                color: "white"
                                font.pointSize: 9
                                font.bold: true
                                visible: {
                                    var area = backend && backend.settings ? backend.settings.mob_area : ""
                                    return area && area !== ""
                                }
                            }
                        }
                        Text { text: "Моб"; color: "#c2c2c2"; font.pointSize: 9 }

                        Rectangle {
                            width: 18; height: 18; radius: 9
                            color: {
                                var area = backend && backend.settings ? backend.settings.player_area : ""
                                return (area && area !== "") ? "#4CAF50" : "#555555"
                            }
                            Text {
                                anchors.centerIn: parent
                                text: "✓"
                                color: "white"
                                font.pointSize: 9
                                font.bold: true
                                visible: {
                                    var area = backend && backend.settings ? backend.settings.player_area : ""
                                    return area && area !== ""
                                }
                            }
                        }
                        Text { text: "Игрок"; color: "#c2c2c2"; font.pointSize: 9 }
                    }
                }
            }

            // === Плитка 2: Детекция каста ===
            Rectangle {
                id: castbarTile
                Layout.fillWidth: true
                Layout.fillHeight: true
                color: "#99252525"
                radius: 10
                border.color: "#50ffffff"
                border.width: 2

                property color accentColor: backend && backend.settings && backend.settings.accent_color !== undefined && backend.settings.accent_color !== null ? backend.settings.accent_color : "#7793a1"

                // Эффект свечения при наведении (8 слоёв)
                Rectangle {
                    id: castGlow1
                    anchors.centerIn: parent
                    width: parent.width + 40; height: parent.height + 40
                    radius: 10 + 20
                    color: Qt.rgba(castbarTile.accentColor.r, castbarTile.accentColor.g, castbarTile.accentColor.b, castMouseArea.containsMouse ? 0.005 : 0)
                    z: 0
                }
                Rectangle {
                    id: castGlow2
                    anchors.centerIn: parent
                    width: parent.width + 35; height: parent.height + 35
                    radius: 10 + 17
                    color: Qt.rgba(castbarTile.accentColor.r, castbarTile.accentColor.g, castbarTile.accentColor.b, castMouseArea.containsMouse ? 0.01 : 0)
                    z: 0
                }
                Rectangle {
                    id: castGlow3
                    anchors.centerIn: parent
                    width: parent.width + 30; height: parent.height + 30
                    radius: 10 + 15
                    color: Qt.rgba(castbarTile.accentColor.r, castbarTile.accentColor.g, castbarTile.accentColor.b, castMouseArea.containsMouse ? 0.015 : 0)
                    z: 0
                }
                Rectangle {
                    id: castGlow4
                    anchors.centerIn: parent
                    width: parent.width + 25; height: parent.height + 25
                    radius: 10 + 12
                    color: Qt.rgba(castbarTile.accentColor.r, castbarTile.accentColor.g, castbarTile.accentColor.b, castMouseArea.containsMouse ? 0.02 : 0)
                    z: 0
                }
                Rectangle {
                    id: castGlow5
                    anchors.centerIn: parent
                    width: parent.width + 20; height: parent.height + 20
                    radius: 10 + 10
                    color: Qt.rgba(castbarTile.accentColor.r, castbarTile.accentColor.g, castbarTile.accentColor.b, castMouseArea.containsMouse ? 0.03 : 0)
                    z: 0
                }
                Rectangle {
                    id: castGlow6
                    anchors.centerIn: parent
                    width: parent.width + 15; height: parent.height + 15
                    radius: 10 + 7
                    color: Qt.rgba(castbarTile.accentColor.r, castbarTile.accentColor.g, castbarTile.accentColor.b, castMouseArea.containsMouse ? 0.04 : 0)
                    z: 0
                }
                Rectangle {
                    id: castGlow7
                    anchors.centerIn: parent
                    width: parent.width + 10; height: parent.height + 10
                    radius: 10 + 5
                    color: Qt.rgba(castbarTile.accentColor.r, castbarTile.accentColor.g, castbarTile.accentColor.b, castMouseArea.containsMouse ? 0.05 : 0)
                    z: 0
                }
                Rectangle {
                    id: castGlow8
                    anchors.centerIn: parent
                    width: parent.width + 6; height: parent.height + 6
                    radius: 10 + 3
                    color: Qt.rgba(castbarTile.accentColor.r, castbarTile.accentColor.g, castbarTile.accentColor.b, castMouseArea.containsMouse ? 0.06 : 0)
                    z: 0
                }

                MouseArea {
                    id: castMouseArea
                    anchors.fill: parent
                    hoverEnabled: true
                    cursorShape: Qt.PointingHandCursor
                    onClicked: {
                        if (settingsStackView) {
                            settingsStackView.push(Qt.resolvedUrl("SettingsCastbarPage.qml"))
                        }
                    }
                }

                ColumnLayout {
                    anchors.centerIn: parent
                    spacing: 8

                    Image {
                        source: "../icons/calibrate.png"
                        width: 56
                        height: 56
                        fillMode: Image.PreserveAspectFit
                        Layout.alignment: Qt.AlignHCenter
                    }

                    Text {
                        text: "Детекция каста"
                        font.pointSize: 16
                        font.bold: true
                        color: "#c2c2c2"
                        horizontalAlignment: Text.AlignHCenter
                        Layout.alignment: Qt.AlignHCenter
                    }

                    Text {
                        text: "Калибровка кастбара"
                        font.pointSize: 10
                        color: "#808080"
                        horizontalAlignment: Text.AlignHCenter
                        Layout.fillWidth: true
                    }

                    // Статус кастбара
                    RowLayout {
                        spacing: 8
                        Layout.alignment: Qt.AlignHCenter

                        Rectangle {
                            width: 18; height: 18; radius: 9
                            color: {
                                var enabled = backend && backend.settings ? backend.settings.castbar_enabled : false
                                return enabled ? "#4CAF50" : "#555555"
                            }
                            Text {
                                anchors.centerIn: parent
                                text: "✓"
                                color: "white"
                                font.pointSize: 9
                                font.bold: true
                                visible: {
                                    var enabled = backend && backend.settings ? backend.settings.castbar_enabled : false
                                    return enabled
                                }
                            }
                        }
                        Text {
                            text: {
                                var enabled = backend && backend.settings ? backend.settings.castbar_enabled : false
                                return enabled ? "Включено" : "Не настроено"
                            }
                            color: "#c2c2c2"
                            font.pointSize: 9
                        }
                    }
                }
            }
        }
    }
}
