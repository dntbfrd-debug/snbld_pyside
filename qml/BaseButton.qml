import QtQuick 2.15
import QtQuick.Controls.Basic 2.15
import QtQuick.Layouts 1.15
import Qt5Compat.GraphicalEffects

Button {
    id: control
    focusPolicy: Qt.NoFocus
    property string iconSource: ""
    property int iconSize: 24
    property int textSize: 12
    property int buttonRadius: 8
    property real pressScale: 0.98
    property color accentColor: backend && backend.settings && backend.settings.accent_color !== undefined && backend.settings.accent_color !== null ? backend.settings.accent_color : "#7793a1"
    property bool isActive: false
    property bool iconOnly: false

    property real currentScale: 1.0
    Behavior on currentScale {
        NumberAnimation { duration: 100; easing.type: Easing.InOutQuad }
    }

    // Фаза пульсации для hover и active (0..2π)
    property real hoverPulse: 0.0
    SequentialAnimation on hoverPulse {
        running: control.hovered || control.isActive
        loops: Animation.Infinite
        NumberAnimation { from: 0; to: Math.PI * 2; duration: 2500; easing.type: Easing.Linear }
    }

    // Вспомогательная функция: переливчатая прозрачность
    function waveOpacity(base, layerIndex, phase, speed) {
        var wave = 0.6 + 0.4 * Math.sin(phase + layerIndex * speed)
        return base * Math.max(0.4, wave)
    }

    // --- 8 СЛОЁВ СВЕЧЕНИЯ (HOVER / ACTIVE) с пульсацией, как на сайте ---
    Rectangle {
        anchors.centerIn: parent
        width: parent.width + 40
        height: parent.height + 40
        radius: control.buttonRadius + 20
        color: control.accentColor
        opacity: (control.hovered || control.isActive) ? waveOpacity(0.02, 0, control.hoverPulse, 0.6) : 0.0
        z: 0
        Behavior on opacity {
            NumberAnimation { duration: 300; easing.type: Easing.InOutQuad }
        }
    }

    Rectangle {
        anchors.centerIn: parent
        width: parent.width + 35
        height: parent.height + 35
        radius: control.buttonRadius + 17
        color: control.accentColor
        opacity: (control.hovered || control.isActive) ? waveOpacity(0.04, 1, control.hoverPulse, 0.6) : 0.0
        z: 0
        Behavior on opacity {
            NumberAnimation { duration: 350; easing.type: Easing.InOutQuad }
        }
    }

    Rectangle {
        anchors.centerIn: parent
        width: parent.width + 30
        height: parent.height + 30
        radius: control.buttonRadius + 15
        color: control.accentColor
        opacity: (control.hovered || control.isActive) ? waveOpacity(0.06, 2, control.hoverPulse, 0.6) : 0.0
        z: 0
        Behavior on opacity {
            NumberAnimation { duration: 400; easing.type: Easing.InOutQuad }
        }
    }

    Rectangle {
        anchors.centerIn: parent
        width: parent.width + 25
        height: parent.height + 25
        radius: control.buttonRadius + 12
        color: control.accentColor
        opacity: (control.hovered || control.isActive) ? waveOpacity(0.09, 3, control.hoverPulse, 0.6) : 0.0
        z: 0
        Behavior on opacity {
            NumberAnimation { duration: 450; easing.type: Easing.InOutQuad }
        }
    }

    Rectangle {
        anchors.centerIn: parent
        width: parent.width + 20
        height: parent.height + 20
        radius: control.buttonRadius + 10
        color: control.accentColor
        opacity: (control.hovered || control.isActive) ? waveOpacity(0.13, 4, control.hoverPulse, 0.6) : 0.0
        z: 0
        Behavior on opacity {
            NumberAnimation { duration: 500; easing.type: Easing.InOutQuad }
        }
    }

    Rectangle {
        anchors.centerIn: parent
        width: parent.width + 15
        height: parent.height + 15
        radius: control.buttonRadius + 7
        color: control.accentColor
        opacity: (control.hovered || control.isActive) ? waveOpacity(0.18, 5, control.hoverPulse, 0.6) : 0.0
        z: 0
        Behavior on opacity {
            NumberAnimation { duration: 550; easing.type: Easing.InOutQuad }
        }
    }

    Rectangle {
        anchors.centerIn: parent
        width: parent.width + 10
        height: parent.height + 10
        radius: control.buttonRadius + 5
        color: control.accentColor
        opacity: (control.hovered || control.isActive) ? waveOpacity(0.25, 6, control.hoverPulse, 0.6) : 0.0
        z: 0
        Behavior on opacity {
            NumberAnimation { duration: 600; easing.type: Easing.InOutQuad }
        }
    }

    Rectangle {
        anchors.centerIn: parent
        width: parent.width + 6
        height: parent.height + 6
        radius: control.buttonRadius + 3
        color: control.accentColor
        opacity: (control.hovered || control.isActive) ? waveOpacity(0.35, 7, control.hoverPulse, 0.6) : 0.0
        z: 0
    }

    background: Rectangle {
        id: btnBg
        radius: control.buttonRadius
        color: control.down ? "#2a1c1c1c" : control.hovered ? "#cc262626" : "#a01c1c1c"
        border.color: "#70454545"
        border.width: 1

        transform: Scale { origin.x: width/2; origin.y: height/2; xScale: control.currentScale; yScale: control.currentScale }
        z: 1

        Behavior on color {
            ColorAnimation { duration: 80; easing.type: Easing.InOutQuad }
        }

        Rectangle {
            anchors.fill: parent
            radius: control.buttonRadius
            gradient: Gradient {
                GradientStop { position: 0.0; color: "#60000000" }
                GradientStop { position: 0.35; color: "#30000000" }
                GradientStop { position: 0.7; color: "#10000000" }
                GradientStop { position: 1.0; color: "#00000000" }
            }
        }
    }

    contentItem: RowLayout {
        anchors.fill: parent
        anchors.leftMargin: control.iconOnly ? 0 : 12
        anchors.rightMargin: control.iconOnly ? 0 : 12
        spacing: control.iconOnly ? 0 : 8
        z: 2

        Item {
            Layout.fillWidth: control.iconOnly
            Layout.fillHeight: control.iconOnly
            Layout.alignment: Qt.AlignVCenter
            Layout.preferredWidth: control.iconOnly ? parent.height - 8 : control.iconSize
            Layout.preferredHeight: control.iconOnly ? parent.height - 8 : control.iconSize
            visible: control.iconSource !== ""

            Image {
                anchors.centerIn: parent
                width: Math.min(parent.width, parent.height)
                height: Math.min(parent.width, parent.height)
                source: control.iconSource
                fillMode: Image.PreserveAspectFit
                opacity: control.isActive ? 1.0 : 0.7
            }
        }

        Text {
            text: control.text
            color: control.hovered || control.isActive ? "#ffffff" : "#c2c2c2"
            font.pointSize: control.textSize
            horizontalAlignment: Text.AlignHCenter
            Layout.fillWidth: true
            Layout.alignment: Qt.AlignVCenter
            visible: !control.iconOnly
        }
    }

    onPressed: currentScale = pressScale
    onReleased: currentScale = 1.0
    onCanceled: currentScale = 1.0

    Connections {
        target: backend
        function onSettingsChanged() {
            control.accentColor = backend.settings.accent_color !== undefined && backend.settings.accent_color !== null ? backend.settings.accent_color : "#7793a1"
        }
    }
}