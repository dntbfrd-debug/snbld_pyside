import QtQuick 2.15
import Qt5Compat.GraphicalEffects

Item {
    id: glass

    property Item sourceLayer: null
    property real blurRadius: 8
    property real glassOpacity: 0.08
    property real borderOpacity: 0.15
    property real glassRadius: 12
    property bool hoverEnabled: false
    property color accentColor: backend && backend.settings && backend.settings.accent_color !== undefined && backend.settings.accent_color !== null ? backend.settings.accent_color : "#7793a1"

    Rectangle {
        id: overlay
        anchors.fill: parent
        radius: glass.glassRadius
        color: Qt.rgba(1.0, 1.0, 1.0, glass.glassOpacity)
        border.color: mouseArea.containsMouse && glass.hoverEnabled ? glass.accentColor : Qt.rgba(1.0, 1.0, 1.0, glass.borderOpacity)
        border.width: 1
        z: 2

        Behavior on border.color {
            ColorAnimation { duration: 150; easing.type: Easing.InOutQuad }
        }
    }

    MouseArea {
        id: mouseArea
        anchors.fill: parent
        hoverEnabled: glass.hoverEnabled
        acceptedButtons: Qt.NoButton
        z: 3
    }

    ShaderEffectSource {
        id: bgCapture
        sourceItem: glass.sourceLayer
        live: true
        recursive: false
        hideSource: false
        z: 0
    }

    GaussianBlur {
        id: blurEffect
        anchors.fill: parent
        source: bgCapture
        radius: glass.blurRadius
        samples: Math.max(3, Math.round(glass.blurRadius * 2 + 1))
        z: 1
    }

    layer.enabled: true
    layer.effect: OpacityMask {
        maskSource: Rectangle {
            width: glass.width
            height: glass.height
            radius: glass.glassRadius
        }
    }
}
