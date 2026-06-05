import QtQuick 2.15
import QtQuick.Controls 2.15

Item {
    id: stripRoot
    width: parent ? parent.width : 55
    height: 50

    property string iconSource: ""
    property bool isActive: false
    property color accentColor: "#7793a1"

    Rectangle {
        anchors.centerIn: parent
        width: 58; height: 58; radius: 19
        color: stripRoot.accentColor
        opacity: stripRoot.isActive ? Window.window.waveOpacity(0.02, 0, Window.window.hoverPulse, 0.6) : 0.0
        z: 0
        Behavior on opacity { NumberAnimation { duration: 300; easing.type: Easing.InOutQuad } }
    }
    Rectangle {
        anchors.centerIn: parent
        width: 54; height: 54; radius: 17
        color: stripRoot.accentColor
        opacity: stripRoot.isActive ? Window.window.waveOpacity(0.04, 1, Window.window.hoverPulse, 0.6) : 0.0
        z: 0
        Behavior on opacity { NumberAnimation { duration: 350; easing.type: Easing.InOutQuad } }
    }
    Rectangle {
        anchors.centerIn: parent
        width: 50; height: 50; radius: 15
        color: stripRoot.accentColor
        opacity: stripRoot.isActive ? Window.window.waveOpacity(0.06, 2, Window.window.hoverPulse, 0.6) : 0.0
        z: 0
        Behavior on opacity { NumberAnimation { duration: 400; easing.type: Easing.InOutQuad } }
    }
    Rectangle {
        anchors.centerIn: parent
        width: 47; height: 47; radius: 13
        color: stripRoot.accentColor
        opacity: stripRoot.isActive ? Window.window.waveOpacity(0.09, 3, Window.window.hoverPulse, 0.6) : 0.0
        z: 0
        Behavior on opacity { NumberAnimation { duration: 450; easing.type: Easing.InOutQuad } }
    }
    Rectangle {
        anchors.centerIn: parent
        width: 44; height: 44; radius: 11
        color: stripRoot.accentColor
        opacity: stripRoot.isActive ? Window.window.waveOpacity(0.13, 4, Window.window.hoverPulse, 0.6) : 0.0
        z: 0
        Behavior on opacity { NumberAnimation { duration: 500; easing.type: Easing.InOutQuad } }
    }
    Rectangle {
        anchors.centerIn: parent
        width: 41; height: 41; radius: 10
        color: stripRoot.accentColor
        opacity: stripRoot.isActive ? Window.window.waveOpacity(0.18, 5, Window.window.hoverPulse, 0.6) : 0.0
        z: 0
        Behavior on opacity { NumberAnimation { duration: 550; easing.type: Easing.InOutQuad } }
    }
    Rectangle {
        anchors.centerIn: parent
        width: 39; height: 39; radius: 9
        color: stripRoot.accentColor
        opacity: stripRoot.isActive ? Window.window.waveOpacity(0.25, 6, Window.window.hoverPulse, 0.6) : 0.0
        z: 0
        Behavior on opacity { NumberAnimation { duration: 600; easing.type: Easing.InOutQuad } }
    }
    Rectangle {
        anchors.centerIn: parent
        width: 37; height: 37; radius: 8
        color: stripRoot.accentColor
        opacity: stripRoot.isActive ? Window.window.waveOpacity(0.35, 7, Window.window.hoverPulse, 0.6) : 0.0
        z: 0
    }

    Rectangle {
        anchors.centerIn: parent
        width: 36; height: 36
        radius: 8
        color: stripRoot.isActive ? Qt.rgba(stripRoot.accentColor.r, stripRoot.accentColor.g, stripRoot.accentColor.b, 0.25) : "transparent"
        z: 1
        Behavior on color { ColorAnimation { duration: 100; easing.type: Easing.InOutQuad } }
    }

    Image {
        anchors.centerIn: parent
        width: 24; height: 24
        source: stripRoot.iconSource
        opacity: stripRoot.isActive ? 1.0 : 0.6
        z: 2
        Behavior on opacity { NumberAnimation { duration: 100; easing.type: Easing.InOutQuad } }
    }
}
