import QtQuick 2.15
import QtQuick.Controls.Basic 2.15
import QtQuick.Layouts 1.15

Item {
    id: editSimplePage

    property var editingMacro: null
    property bool dataLoaded: false

    Component.onCompleted: {
        console.log("EditSimplePage onCompleted, editingMacro=", editingMacro ? editingMacro.name : "null")
        // Получаем макрос из backend если не установлен
        if (!editingMacro && backend.macro_for_edit) {
            console.log("EditSimplePage: получаем макрос из backend")
            editingMacro = backend.macro_for_edit
            dataLoaded = true
        }
        // Загружаем форму
        formLoader.source = "SimpleEditForm.qml"
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
                text: editingMacro ? "Редактирование: " + editingMacro.name : "Простой макрос"
                font.pointSize: 16
                font.bold: true
                color: "#c2c2c2"
                horizontalAlignment: Text.AlignHCenter
                Layout.fillWidth: true
            }
            Item { Layout.fillWidth: true }
        }

        // Загружаем форму редактирования
        Loader {
            id: formLoader
            Layout.fillWidth: true
            Layout.fillHeight: true
            // source устанавливается в Component.onCompleted
            
            onLoaded: {
                console.log("EditSimplePage: formLoader loaded, editingMacro=", editingMacro ? editingMacro.name : "null")
                if (item && editingMacro) {
                    Qt.callLater(function() {
                        console.log("EditSimplePage: устанавливаем editingMacro в форму")
                        item.editingMacro = editingMacro
                    })
                }
            }
        }
    }
}
