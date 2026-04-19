import QtQuick 2.15
import QtQuick.Controls.Basic 2.15
import QtQuick.Layouts 1.15

Item {
    id: buffListPage
    
    property Item formPage: null

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 20
        spacing: 15
        visible: formPage ? !formPage.visible : true

        // Заголовок
        RowLayout {
            Layout.fillWidth: true
            BaseButton {
                text: "← Назад"
                implicitWidth: 100
                implicitHeight: 40
                iconSize: 14
                textSize: 11
                onClicked: {
                    if (editStackView) {
                        editStackView.pop()
                    }
                }
            }
            Item { Layout.fillWidth: true }
            Text {
                text: "✦ Баффы"
                font.pointSize: 16
                font.bold: true
                color: "#c2c2c2"
            }
            Item { Layout.fillWidth: true }
            Text {
                text: "◈ Всего: " + buffListModel.count
                color: "#7793a1"
                font.pointSize: 12
            }
        }

        // Сетка баффов
        Item {
            Layout.fillWidth: true
            Layout.fillHeight: true
            Layout.margins: 20

            GridView {
                anchors.centerIn: parent
                width: {
                    var cols = Math.floor(parent.width / 180)
                    if (cols < 1) cols = 1
                    if (cols > 5) cols = 5
                    return cols * 180
                }
                height: parent.height
                model: buffListModel
                cellWidth: 180
                cellHeight: 100
                flow: GridView.FlowLeftToRight
                layoutDirection: Qt.LeftToRight
                clip: false

                delegate: Rectangle {
                    id: buffDelegate
                    width: 170
                    height: 90
                    color: "#99252525"
                    radius: 12
                    border.color: "#50ffffff"
                    border.width: 2

                    property color accentColor: backend && backend.settings && backend.settings.accent_color !== undefined && backend.settings.accent_color !== null ? backend.settings.accent_color : "#7793a1"

                    // Эффект свечения при наведении (8 слоёв)
                    Rectangle {
                        id: buffGlow1
                        anchors.centerIn: parent
                        width: parent.width + 40
                        height: parent.height + 40
                        radius: 8 + 20
                        color: Qt.rgba(buffDelegate.accentColor.r, buffDelegate.accentColor.g, buffDelegate.accentColor.b, buffMouseArea.containsMouse ? 0.008 : 0)
                        z: 0
                    }
                    Rectangle {
                        id: buffGlow2
                        anchors.centerIn: parent
                        width: parent.width + 35
                        height: parent.height + 35
                        radius: 8 + 17
                        color: Qt.rgba(buffDelegate.accentColor.r, buffDelegate.accentColor.g, buffDelegate.accentColor.b, buffMouseArea.containsMouse ? 0.015 : 0)
                        z: 0
                    }
                    Rectangle {
                        id: buffGlow3
                        anchors.centerIn: parent
                        width: parent.width + 30
                        height: parent.height + 30
                        radius: 8 + 15
                        color: Qt.rgba(buffDelegate.accentColor.r, buffDelegate.accentColor.g, buffDelegate.accentColor.b, buffMouseArea.containsMouse ? 0.022 : 0)
                        z: 0
                    }
                    Rectangle {
                        id: buffGlow4
                        anchors.centerIn: parent
                        width: parent.width + 25
                        height: parent.height + 25
                        radius: 8 + 12
                        color: Qt.rgba(buffDelegate.accentColor.r, buffDelegate.accentColor.g, buffDelegate.accentColor.b, buffMouseArea.containsMouse ? 0.03 : 0)
                        z: 0
                    }
                    Rectangle {
                        id: buffGlow5
                        anchors.centerIn: parent
                        width: parent.width + 20
                        height: parent.height + 20
                        radius: 8 + 10
                        color: Qt.rgba(buffDelegate.accentColor.r, buffDelegate.accentColor.g, buffDelegate.accentColor.b, buffMouseArea.containsMouse ? 0.045 : 0)
                        z: 0
                    }
                    Rectangle {
                        id: buffGlow6
                        anchors.centerIn: parent
                        width: parent.width + 15
                        height: parent.height + 15
                        radius: 8 + 7
                        color: Qt.rgba(buffDelegate.accentColor.r, buffDelegate.accentColor.g, buffDelegate.accentColor.b, buffMouseArea.containsMouse ? 0.065 : 0)
                        z: 0
                    }
                    Rectangle {
                        id: buffGlow7
                        anchors.centerIn: parent
                        width: parent.width + 10
                        height: parent.height + 10
                        radius: 8 + 5
                        color: Qt.rgba(buffDelegate.accentColor.r, buffDelegate.accentColor.g, buffDelegate.accentColor.b, buffMouseArea.containsMouse ? 0.09 : 0)
                        z: 0
                    }
                    Rectangle {
                        id: buffGlow8
                        anchors.centerIn: parent
                        width: parent.width + 6
                        height: parent.height + 6
                        radius: 8 + 3
                        color: Qt.rgba(buffDelegate.accentColor.r, buffDelegate.accentColor.g, buffDelegate.accentColor.b, buffMouseArea.containsMouse ? 0.12 : 0)
                        z: 0
                    }

                    MouseArea {
                        id: buffMouseArea
                        anchors.fill: parent
                        hoverEnabled: true
                        cursorShape: Qt.PointingHandCursor
                        onClicked: {
                            console.log("BuffListPage: clicked buff index=", index)
                            if (buffListModel.get(index)) {
                                var clickedBuff = buffListModel.get(index)
                                console.log("BuffListPage: buff name=", clickedBuff.name)
                                openBuffForm(clickedBuff)
                            }
                        }
                    }

                    RowLayout {
                        anchors.fill: parent
                        anchors.margins: 8
                        spacing: 8

                        Image {
                            source: {
                                var item = buffListModel.get(index)
                                if (item && item.id) {
                                    // Используем абсолютный путь
                                    return "file:///C:/Users/dntbf/Desktop/snbd2/snbld_pyside/icons/skills/" + item.id + ".png"
                                }
                                return "file:///C:/Users/dntbf/Desktop/snbd2/snbld_pyside/icons/buff.png"
                            }
                            width: 50
                            height: 50
                            fillMode: Image.PreserveAspectFit
                        }

                        ColumnLayout {
                            Layout.fillWidth: true
                            spacing: 2

                            Text {
                                text: model.name || ""
                                font.pointSize: 9
                                font.bold: true
                                color: "#c2c2c2"
                                wrapMode: Text.WordWrap
                                maximumLineCount: 2
                                elide: Text.ElideRight
                                Layout.fillWidth: true
                            }

                            Text {
                                text: (model.channeling_bonus > 0) ? 
                                      ("+" + model.channeling_bonus + "% пение | " + model.duration + "с") : 
                                      (model.duration + "с")
                                font.pointSize: 7
                                color: (model.channeling_bonus > 0) ? "#4CAF50" : "#a0a0a0"
                            }
                        }
                    }
                }
        }
        }
    }

    // Доступ к StackView из родителя
    property alias editStackView: buffListPage.parent

    ListModel {
        id: buffListModel
    }

    Component.onCompleted: {
        loadBuffs()
    }

    function loadBuffs() {
        buffListModel.clear()
        var allSkills = backend.skill_list
        console.log("BuffListPage: всего объектов в skill_list=", allSkills.length)
        for (var i = 0; i < allSkills.length; ++i) {
            var item = allSkills[i]
            // Баффы имеют channeling_bonus но не имеют cast_time
            if (item.hasOwnProperty('channeling_bonus') && !item.hasOwnProperty('cast_time')) {
                console.log("BuffListPage: найден бафф id=", item.id, "name=", item.name)
                buffListModel.append(item)
            }
        }
        console.log("BuffListPage: загружено", buffListModel.count, "баффов")
    }

    // Открытие формы редактирования баффа
    function openBuffForm(buff) {
        if (editStackView) {
            editStackView.push("BuffEditForm.qml", {
                "buff": buff,
                "editingMacro": null
            })
        }
    }
    
    // Рамка страницы с пульсацией
    PageBorder {
        anchors.fill: parent
        z: 1
    }
}
