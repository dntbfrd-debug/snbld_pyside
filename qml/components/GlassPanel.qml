import QtQuick 2.15

Rectangle {
    id: glass

    property real glassOpacity: 0.35
    property real borderOpacity: 0.12
    radius: 12
    property bool hoverEnabled: false
    property color accentColor: backend && backend.settings && backend.settings.accent_color !== undefined && backend.settings.accent_color !== null ? backend.settings.accent_color : "#7793a1"
    color: Qt.rgba(0.0, 0.0, 0.0, glassOpacity)
    border.color: mouseArea.containsMouse && hoverEnabled ? accentColor : Qt.rgba(1.0, 1.0, 1.0, borderOpacity)
    border.width: 1

    Behavior on border.color {
        ColorAnimation { duration: 150; easing.type: Easing.InOutQuad }
    }

    MouseArea {
        id: mouseArea
        anchors.fill: parent
        hoverEnabled: glass.hoverEnabled
        acceptedButtons: Qt.NoButton
    }
}
