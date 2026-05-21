import QtQuick 2.15
import Qt5Compat.GraphicalEffects

Item {
    id: root

    property real blurRadius: 16
    property real glassOpacity: 0.15
    property real borderOpacity: 0.12
    property real radius: 12
    property bool hoverEnabled: false
    property bool clip: false
    property alias border: tintOverlay.border
    property color tintColor: "#a01c1c1c"
    property color accentColor: backend && backend.settings && backend.settings.accent_color !== undefined && backend.settings.accent_color !== null ? backend.settings.accent_color : "#7793a1"
    property bool useBgCapture: true
    property Item customBgSource: null

    property Item __bgSource: root.customBgSource ? root.customBgSource : (root.useBgCapture && Window.window && Window.window.backgroundSource ? Window.window.backgroundSource : null)

    property Item __flickable: {
        var p = root.parent
        while (p) {
            if (p.contentY !== undefined) return p
            p = p.parent
        }
        return null
    }

    ShaderEffectSource {
        id: bgCapture
        sourceItem: root.__bgSource
        sourceRect: {
            var _fy = root.__flickable ? root.__flickable.contentY : 0
            var _ = _fy
            var pos = root.__bgSource ? root.mapToItem(root.__bgSource, 0, 0) : Qt.point(0, 0)
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
        radius: root.radius
        color: root.tintColor
        border.color: mouseArea.containsMouse && root.hoverEnabled ? root.accentColor : Qt.rgba(1.0, 1.0, 1.0, root.borderOpacity)
        border.width: 1

        Behavior on border.color {
            ColorAnimation { duration: 150; easing.type: Easing.InOutQuad }
        }

        Rectangle {
            anchors.fill: parent
            radius: parent.radius
            gradient: Gradient {
                GradientStop { position: 0.0; color: "#60000000" }
                GradientStop { position: 0.35; color: "#30000000" }
                GradientStop { position: 0.7; color: "#10000000" }
                GradientStop { position: 1.0; color: "#00000000" }
            }
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
            radius: root.radius
        }
    }

    Rectangle {
        id: fallbackBg
        anchors.fill: parent
        radius: root.radius
        color: root.tintColor
        border.color: tintOverlay.border.color
        border.width: tintOverlay.border.width
        visible: root.__bgSource === null

        Rectangle {
            anchors.fill: parent
            radius: parent.radius
            gradient: Gradient {
                GradientStop { position: 0.0; color: "#60000000" }
                GradientStop { position: 0.35; color: "#30000000" }
                GradientStop { position: 0.7; color: "#10000000" }
                GradientStop { position: 1.0; color: "#00000000" }
            }
        }
    }
}
