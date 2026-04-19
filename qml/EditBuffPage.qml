import QtQuick 2.15
import QtQuick.Controls.Basic 2.15
import QtQuick.Layouts 1.15

Item {
    id: editBuffPage

    property var editingMacro: null
    property bool dataLoaded: false

    Component.onCompleted: {
        console.log("EditBuffPage onCompleted, editingMacro=", editingMacro ? editingMacro.name : "null")
        // Получаем макрос из backend если не установлен
        if (!editingMacro && backend.macro_for_edit) {
            console.log("EditBuffPage: получаем макрос из backend")
            editingMacro = backend.macro_for_edit
            dataLoaded = true
        }
        // Загружаем форму
        formLoader.source = "BuffEditForm.qml"
    }

    Rectangle {
        anchors.fill: parent
        color: "#99252525"
        radius: 12
        z: 0
    }

    // Рамка страницы с пульсацией
    PageBorder {
        z: 1
    }

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 20
        spacing: 15

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
                    backend.clear_macro_for_edit()
                    backend.pageChangeRequested("MacrosListPage.qml")
                }
            }
            Text {
                text: editingMacro ? ("✎ " + editingMacro.name) : "Бафф-макрос"
                font.pointSize: 18
                font.bold: true
                color: "#c2c2c2"
                Layout.alignment: Qt.AlignHCenter
            }
            Item { Layout.fillWidth: true }
        }

        // Форма редактирования
        Loader {
            id: formLoader
            Layout.fillWidth: true
            Layout.fillHeight: true
            onLoaded: {
                console.log("EditBuffPage: formLoader loaded")
                if (item && item.loadFromMacro && editingMacro) {
                    console.log("EditBuffPage: calling loadFromMacro")
                    item.loadFromMacro(editingMacro)
                }
            }
        }
    }
}
