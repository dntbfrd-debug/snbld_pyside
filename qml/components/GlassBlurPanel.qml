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
    property color tintColor: Qt.rgba(0.08, 0.08, 0.12, glassOpacity)
    property color accentColor: backend && backend.settings && backend.settings.accent_color !== undefined && backend.settings.accent_color !== null ? backend.settings.accent_color : "#7793a1"
    property bool useBgCapture: true
    property Item customBgSource: null

    // Источник для захвата фона.
    // Приоритет: customBgSource > Window.window.backgroundSource > null
    // Динамический биндинг — срабатывает когда Window.window становится доступен
    // (важно для Loader-загруженных страниц, где onCompleted вызывается ДО установки window)
    property Item __bgSource: root.customBgSource ? root.customBgSource : (root.useBgCapture && Window.window && Window.window.backgroundSource ? Window.window.backgroundSource : null)

    // Авто-детект Flickable для корректного sourceRect при скролле
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
            // Принудительная зависимость от contentY/contentX Flickable
            // чтобы биндинг пересчитывался при скролле
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
        color: Qt.rgba(0.1, 0.1, 0.15, root.__bgSource === null ? root.glassOpacity : 0.0)
        border.color: tintOverlay.border.color
        border.width: tintOverlay.border.width
        visible: root.__bgSource === null
    }
}
