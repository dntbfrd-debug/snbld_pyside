import QtQuick 2.15
import QtQuick.Controls 2.15

ScrollBar {
    id: control

    property color accentColor: backend && backend.settings && backend.settings.accent_color !== undefined && backend.settings.accent_color !== null ? backend.settings.accent_color : "#7793a1"

    padding: 2
    policy: ScrollBar.AsNeeded

    contentItem: Rectangle {
        implicitWidth: control.interactive ? 6 : 3
        implicitHeight: control.interactive ? 6 : 3
        radius: 3
        color: control.pressed ? control.accentColor : (control.hovered ? Qt.rgba(1, 1, 1, 0.35) : Qt.rgba(1, 1, 1, 0.15))
        opacity: control.pressed ? 1.0 : (control.hovered ? 0.9 : (control.size < 1.0 ? 0.5 : 0.0))

        Behavior on color { ColorAnimation { duration: 100 } }
        Behavior on opacity { NumberAnimation { duration: 150 } }
    }

    background: Rectangle {
        implicitWidth: control.interactive ? 10 : 4
        implicitHeight: control.interactive ? 10 : 4
        radius: 5
        color: "transparent"
        opacity: 0.0
    }
}
