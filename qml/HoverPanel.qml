import QtQuick 2.15
import QtQuick.Controls.Basic 2.15
import Qt5Compat.GraphicalEffects

Item {
    id: root

    property string text: ""
    property string pageFile: ""
    property bool hasSubmenu: false
    property var submenuItems: []
    property string accentColor: "#7793a1"
    property real panelY: 0
    property int panelWidth: 160
    property int panelHeight: 42
    property int panelRadius: 10

    signal panelClicked(string pf)

    width: panelWidth
    height: panelHeight
    visible: false
    z: 100

    x: 8
    y: panelY

    Rectangle {
        id: panelBg
        anchors.fill: parent
        radius: root.panelRadius
        color: "#333333"
        border.color: "#50ffffff"
        border.width: 1

        layer.enabled: true
        layer.effect: DropShadow {
            horizontalOffset: 4
            verticalOffset: 2
            radius: 14
            samples: 18
            color: "#50000000"
        }

        Button {
            id: panelBtn
            anchors.fill: parent
            anchors.margins: 2
            focusPolicy: Qt.NoFocus
            background: Rectangle {
                radius: root.panelRadius - 2
                color: panelBtn.hovered ? Qt.rgba(root.accentColor.r, root.accentColor.g, root.accentColor.b, 0.25) : "transparent"

                Behavior on color {
                    ColorAnimation { duration: 150 }
                }
            }
            contentItem: Text {
                text: root.text
                color: panelBtn.hovered ? "#ffffff" : "#d0d0d0"
                font.pointSize: 11
                font.bold: panelBtn.hovered
                horizontalAlignment: Text.AlignHCenter
                verticalAlignment: Text.AlignVCenter
            }
            onClicked: {
                root.panelClicked(root.pageFile)
            }
        }
    }
}
