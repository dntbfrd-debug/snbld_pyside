import QtQuick 2.15
import QtQuick.Controls.Basic 2.15
import QtQuick.Layouts 1.15

Item {
    id: root
    visible: true
    clip: true

    property string className: ""
    property var selectedSkill: null

    // Доступ к StackView из родителя
    property alias editStackView: root.parent

    Component.onCompleted: {
        if (className) {
            loadSkillsByClass(className)
        }
    }

    function loadSkillsByClass(className) {
        console.log("SkillSelectionDialog.loadSkillsByClass: класс=", className)
        var skills = backend.skill_list
        console.log("  - всего скиллов в БД:", skills.length)
        skillsModel.clear()
        var count = 0
        for (var i = 0; i < skills.length; ++i) {
            // Исключаем баффы: у баффов есть channeling_bonus но нет cast_time
            var item = skills[i]
            var isBuff = item.hasOwnProperty('channeling_bonus') && !item.hasOwnProperty('cast_time')
            if (!isBuff && item.class === className) {
                skillsModel.append(item)
                count++
            }
        }
        console.log("  - найдено скиллов для класса", className, ":", count)
        console.log("  - skillsModel.count:", skillsModel.count)
    }
    
    // Функция для открытия формы редактирования скилла
    function openSkillForm(skill) {
        if (!skill) {
            console.log("SkillSelectionDialog.openSkillForm: skill не выбран!")
            return
        }
        console.log("SkillSelectionDialog.openSkillForm:", skill.name)
        if (editStackView) {
            editStackView.push("SkillEditForm.qml", {
                "skill": skill
            })
        }
    }

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 20
        spacing: 15

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
        }

        // Сетка скиллов
        Item {
            Layout.fillWidth: true
            Layout.fillHeight: true
            Layout.margins: 20

            GridView {
                id: skillsGrid
                anchors.centerIn: parent
                width: {
                    // Вычисляем ширину чтобы вместить все элементы в ряд
                    var cols = Math.floor(parent.width / 180)
                    if (cols < 1) cols = 1
                    if (cols > 5) cols = 5  // Максимум 5 в ряд
                    return cols * 180
                }
                height: parent.height
                model: skillsModel
                cellWidth: 180
                cellHeight: 100
                flow: GridView.FlowLeftToRight
                layoutDirection: Qt.LeftToRight
                clip: false

                delegate: Rectangle {
                    id: skillDelegate
                    width: 170
                    height: 90
                    color: "#99252525"
                    radius: 8
                    border.color: "#50ffffff"
                    border.width: 2

                    property color accentColor: backend && backend.settings && backend.settings.accent_color !== undefined && backend.settings.accent_color !== null ? backend.settings.accent_color : "#7793a1"

                    // Эффект свечения при наведении (8 слоёв)
                    Rectangle {
                        id: skillGlow1
                        anchors.centerIn: parent
                        width: parent.width + 40
                        height: parent.height + 40
                        radius: 8 + 20
                        color: Qt.rgba(skillDelegate.accentColor.r, skillDelegate.accentColor.g, skillDelegate.accentColor.b, skillMouseArea.containsMouse ? 0.008 : 0)
                        z: 0
                    }
                    Rectangle {
                        id: skillGlow2
                        anchors.centerIn: parent
                        width: parent.width + 35
                        height: parent.height + 35
                        radius: 8 + 17
                        color: Qt.rgba(skillDelegate.accentColor.r, skillDelegate.accentColor.g, skillDelegate.accentColor.b, skillMouseArea.containsMouse ? 0.015 : 0)
                        z: 0
                    }
                    Rectangle {
                        id: skillGlow3
                        anchors.centerIn: parent
                        width: parent.width + 30
                        height: parent.height + 30
                        radius: 8 + 15
                        color: Qt.rgba(skillDelegate.accentColor.r, skillDelegate.accentColor.g, skillDelegate.accentColor.b, skillMouseArea.containsMouse ? 0.022 : 0)
                        z: 0
                    }
                    Rectangle {
                        id: skillGlow4
                        anchors.centerIn: parent
                        width: parent.width + 25
                        height: parent.height + 25
                        radius: 8 + 12
                        color: Qt.rgba(skillDelegate.accentColor.r, skillDelegate.accentColor.g, skillDelegate.accentColor.b, skillMouseArea.containsMouse ? 0.03 : 0)
                        z: 0
                    }
                    Rectangle {
                        id: skillGlow5
                        anchors.centerIn: parent
                        width: parent.width + 20
                        height: parent.height + 20
                        radius: 8 + 10
                        color: Qt.rgba(skillDelegate.accentColor.r, skillDelegate.accentColor.g, skillDelegate.accentColor.b, skillMouseArea.containsMouse ? 0.045 : 0)
                        z: 0
                    }
                    Rectangle {
                        id: skillGlow6
                        anchors.centerIn: parent
                        width: parent.width + 15
                        height: parent.height + 15
                        radius: 8 + 7
                        color: Qt.rgba(skillDelegate.accentColor.r, skillDelegate.accentColor.g, skillDelegate.accentColor.b, skillMouseArea.containsMouse ? 0.065 : 0)
                        z: 0
                    }
                    Rectangle {
                        id: skillGlow7
                        anchors.centerIn: parent
                        width: parent.width + 10
                        height: parent.height + 10
                        radius: 8 + 5
                        color: Qt.rgba(skillDelegate.accentColor.r, skillDelegate.accentColor.g, skillDelegate.accentColor.b, skillMouseArea.containsMouse ? 0.09 : 0)
                        z: 0
                    }
                    Rectangle {
                        id: skillGlow8
                        anchors.centerIn: parent
                        width: parent.width + 6
                        height: parent.height + 6
                        radius: 8 + 3
                        color: Qt.rgba(skillDelegate.accentColor.r, skillDelegate.accentColor.g, skillDelegate.accentColor.b, skillMouseArea.containsMouse ? 0.12 : 0)
                        z: 0
                    }

                    MouseArea {
                        id: skillMouseArea
                        anchors.fill: parent
                        hoverEnabled: true
                        cursorShape: Qt.PointingHandCursor
                        onClicked: {
                            console.log("SkillSelectionDialog: клик по скиллу index=", index)
                            var clickedSkill = skillsModel.get(index)
                            console.log("  - clickedSkill:", clickedSkill)
                            console.log("  - name:", clickedSkill ? clickedSkill.name : "null")
                            
                            if (!clickedSkill) {
                                console.log("SkillSelectionDialog: clickedSkill пустой!")
                                return
                            }
                            
                            selectedSkill = clickedSkill
                            console.log("Выбран скилл:", clickedSkill.name, "id:", clickedSkill.id)
                            // Открываем форму редактирования
                            openSkillForm(selectedSkill)
                        }
                    }

                    ColumnLayout {
                        anchors.fill: parent
                        anchors.margins: 8
                        spacing: 4

                        // Иконка скилла
                        Image {
                            Layout.preferredWidth: 32
                            Layout.preferredHeight: 32
                            Layout.alignment: Qt.AlignHCenter | Qt.AlignTop
                            source: "file:///C:/Users/dntbf/Desktop/snbd2/snbld_pyside/icons/skills/" + id + ".png"
                            fillMode: Image.PreserveAspectFit
                            visible: status === Image.Ready
                        }

                        // Название скилла
                        Text {
                            text: name
                            color: "#ffffff"
                            font.pointSize: 9
                            font.bold: true
                            horizontalAlignment: Text.AlignHCenter
                            wrapMode: Text.WordWrap
                            Layout.fillWidth: true
                            Layout.fillHeight: true
                            elide: Text.ElideRight
                        }
                    }
                }
        }

        ListModel {
            id: skillsModel
        }
        }
    }

    // Рамка страницы с пульсацией
    PageBorder {
        anchors.fill: parent
        z: 1
    }
}
