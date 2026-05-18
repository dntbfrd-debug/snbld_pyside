import QtQuick 2.15
import Qt5Compat.GraphicalEffects

Item {
    id: root

    property real blurRadius: 16
    property real glassOpacity: 0.15
    property real borderOpacity: 0.12
    property real glassRadius: 12
    property bool hoverEnabled: false
    property color tintColor: Qt.rgba(0.08, 0.08, 0.12, glassOpacity)
    property color accentColor: backend && backend.settings && backend.settings.accent_color !== undefined && backend.settings.accent_color !== null ? backend.settings.accent_color : "#7793a1"

    readonly property Item __bgSource: {
        var w = Window.window
        return w && w.backgroundSource ? w.backgroundSource : null
    }

    ShaderEffectSource {
        id: bgCapture
        sourceItem: root.__bgSource
        sourceRect: {
            var pos = root.mapToItem(root.__bgSource, 0, 0)
            return Qt.rect(pos.x, pos.y, root.width, root.height)
        }
        live: true
        hideSource: false
        visible: root.__bgSource !== null
    }

    FastBlur {
        id: blurEffect
        anchors.fill: parent
        source: bgCapture
        radius: root.blurRadius
        transparentBorder: true
        visible: root.__bgSource !== null
    }

    Rectangle {
        id: tintOverlay
        anchors.fill: parent
        radius: root.glassRadius
        color: root.tintColor
        border.color: mouseArea.containsMouse && root.hoverEnabled ? root.accentColor : Qt.rgba(1.0, 1.0, 1.0, root.borderOpacity)
        border.width: 1

        Behavior on border.color {
            ColorAnimation { duration: 150; easing.type: Easing.InOutQuad }
        }
    }

    MouseArea {
        id: mouseArea
        anchors.fill: parent
        hoverEnabled: root.hoverEnabled
        acceptedButtons: Qt.NoButton
    }

    layer.enabled: true
    layer.effect: OpacityMask {
        maskSource: Rectangle {
            width: root.width
            height: root.height
            radius: root.glassRadius
        }
    }

    Rectangle {
        id: fallbackBg
        anchors.fill: parent
        radius: root.glassRadius
        color: Qt.rgba(0.1, 0.1, 0.15, 0.75)
        border.color: mouseArea.containsMouse && root.hoverEnabled ? root.accentColor : Qt.rgba(1.0, 1.0, 1.0, root.borderOpacity)
        border.width: 1
        visible: root.__bgSource === null

        Behavior on border.color {
            ColorAnimation { duration: 150; easing.type: Easing.InOutQuad }
        }
    }
}
