import QtQuick 2.15
import QtQuick.Controls.Basic 2.15

TextField {
    id: control

    property color accentColor: backend && backend.settings && backend.settings.accent_color !== undefined && backend.settings.accent_color !== null ? backend.settings.accent_color : "#7793a1"

    font.pointSize: 10
    color: "#ffffff"
    placeholderTextColor: "#777777"
    leftPadding: 10
    rightPadding: 10
    selectByMouse: true

    background: Rectangle {
        radius: 6
        color: Qt.rgba(0, 0, 0, 0.35)
        border.color: control.activeFocus ? control.accentColor : Qt.rgba(1, 1, 1, 0.12)
        border.width: 1

        Behavior on border.color { ColorAnimation { duration: 100 } }
    }

    Connections {
        target: backend
        function onSettingsChanged() {
            control.accentColor = backend.settings.accent_color !== undefined && backend.settings.accent_color !== null ? backend.settings.accent_color : "#7793a1"
        }
    }
}
