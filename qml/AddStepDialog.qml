import QtQuick 2.15
import QtQuick.Controls.Basic 2.15
import QtQuick.Layouts 1.15

Dialog {
    id: dialog
    modal: true
    title: ""
    standardButtons: Dialog.NoButton
    width: 320
    height: contentCol.implicitHeight + footer.implicitHeight + 40
    background: Rectangle {
        color: "#3a3a3a"
        radius: 8
    }

    property string currentType: ""
    property string keyValue: ""
    property int delayValue: 100

    signal stepAdded(string type, string value, int delay)

    function openFor(type) {
        currentType = type
        if (type === "key") {
            keyField.text = ""
            keyValue = ""
            delayField.text = "100"
            delayValue = 100
        } else {
            delayField.text = "100"
            delayValue = 100
        }
        open()
        Qt.callLater(function() {
            if (dialog.parent) {
                dialog.x = (dialog.parent.width - dialog.width) / 2
                dialog.y = (dialog.parent.height - dialog.height) / 2
            }
        })
    }

    ColumnLayout {
        id: contentCol
        anchors.fill: parent
        anchors.margins: 15
        spacing: 12

        TextField {
            id: keyField
            Layout.fillWidth: true
            visible: dialog.currentType === "key"
            placeholderText: "Клавиша (например: 1, a, ctrl+f)"
            background: Rectangle { radius: 4; color: "#40ffffff" }
            onTextChanged: dialog.keyValue = text
        }

        RowLayout {
            spacing: 8
            Label { text: "Задержка (мс):"; color: "#c2c2c2"; Layout.preferredWidth: 90 }
            TextField {
                id: delayField
                Layout.fillWidth: true
                text: "100"
                validator: IntValidator { bottom: 0; top: 10000 }
                background: Rectangle { radius: 4; color: "#40ffffff" }
                onTextChanged: dialog.delayValue = parseInt(text) || 0
            }
        }

        Item { Layout.fillHeight: true; height: 10 }
    }

    footer: Item {
        implicitHeight: 50
        width: parent.width
        RowLayout {
            anchors.centerIn: parent
            spacing: 20
            BaseButton {
                text: "ОК"
                implicitWidth: 80
                implicitHeight: 32
                onClicked: {
                    if (dialog.currentType === "key") {
                        if (dialog.keyValue.trim() !== "") {
                            stepAdded("key", dialog.keyValue.trim(), dialog.delayValue)
                        }
                    } else if (dialog.currentType === "pause") {
                        stepAdded("wait", "", dialog.delayValue)
                    }
                    dialog.close()
                }
            }
            BaseButton {
                text: "Отмена"
                implicitWidth: 80
                implicitHeight: 32
                onClicked: dialog.close()
            }
        }
    }
}
