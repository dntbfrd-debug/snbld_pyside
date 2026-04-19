import QtQuick 2.15
import QtQuick.Controls.Basic 2.15
import QtQuick.Layouts 1.15

Item {
    id: editSkillPage

    property var editingMacro: null
    property bool dataLoaded: false

    Component.onCompleted: {
        console.log("EditSkillPage onCompleted, editingMacro=", editingMacro ? editingMacro.name : "null")
        
        // Сначала загружаем форму
        formLoader.source = "SkillEditForm.qml"
        
        // Потом получаем макрос из backend
        loadMacroFromBackend()
    }

    function loadMacroFromBackend() {
        if (!editingMacro && backend.macro_for_edit && backend.macro_for_edit.name) {
            console.log("EditSkillPage: получаем макрос из backend:", backend.macro_for_edit.name)
            editingMacro = backend.macro_for_edit
            dataLoaded = true
        }
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
                text: editingMacro ? "Редактирование: " + editingMacro.name : "Макрос скилла"
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
                console.log("EditSkillPage: formLoader loaded")
                // Загружаем макрос из backend
                loadMacroFromBackend()

                // Передаём editingMacro в форму сразу
                if (item && editingMacro) {
                    console.log("EditSkillPage: устанавливаем editingMacro в форму:", editingMacro.name)
                    item.editingMacro = editingMacro
                    item.skill = null
                    item.dataLoaded = false
                }
            }
        }
    }

    // Отслеживаем изменения macro_for_edit
    Connections {
        target: backend
        function onMacrosChanged() {
            // Если форма ещё не загрузила макрос, пробуем снова
            if (!dataLoaded && formLoader.item) {
                loadMacroFromBackend()
                if (editingMacro && formLoader.item) {
                    formLoader.item.editingMacro = editingMacro
                    formLoader.item.skill = null
                    formLoader.item.dataLoaded = false
                }
            }
        }
    }
}
