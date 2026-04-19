import QtQuick 2.15
import QtQuick.Controls.Basic 2.15
import QtQuick.Layouts 1.15
import Qt5Compat.GraphicalEffects

Button {
    id: control
    property string iconSource: ""
    property int iconSize: 24
    property int textSize: 12
    property int buttonRadius: 8
    property real pressScale: 0.9
    property color accentColor: backend && backend.settings && backend.settings.accent_color !== undefined && backend.settings.accent_color !== null ? backend.settings.accent_color : "#7793a1"

    property real currentScale: 1.0
    Behavior on currentScale {
        NumberAnimation { duration: 100; easing.type: Easing.InOutQuad }
    }

    // Эффект свечения для АКТИВНОЙ кнопки (ПОД кнопкой) - очень мягкий
    Rectangle {
        id: activeGlow1
        anchors.centerIn: parent
        width: parent.width + 40
        height: parent.height + 40
        radius: control.buttonRadius + 20
        color: Qt.rgba(control.accentColor.r, control.accentColor.g, control.accentColor.b, 0.008)
        opacity: control.isActive ? 0.3 : 0.0
        z: 0
        Behavior on opacity {
            NumberAnimation { duration: 200; easing.type: Easing.InOutQuad }
        }
    }

    Rectangle {
        id: activeGlow2
        anchors.centerIn: parent
        width: parent.width + 35
        height: parent.height + 35
        radius: control.buttonRadius + 17
        color: Qt.rgba(control.accentColor.r, control.accentColor.g, control.accentColor.b, 0.015)
        opacity: control.isActive ? 0.4 : 0.0
        z: 0
        Behavior on opacity {
            NumberAnimation { duration: 200; easing.type: Easing.InOutQuad }
        }
    }

    Rectangle {
        id: activeGlow3
        anchors.centerIn: parent
        width: parent.width + 30
        height: parent.height + 30
        radius: control.buttonRadius + 15
        color: Qt.rgba(control.accentColor.r, control.accentColor.g, control.accentColor.b, 0.022)
        opacity: control.isActive ? 0.5 : 0.0
        z: 0
        Behavior on opacity {
            NumberAnimation { duration: 200; easing.type: Easing.InOutQuad }
        }
    }

    Rectangle {
        id: activeGlow4
        anchors.centerIn: parent
        width: parent.width + 25
        height: parent.height + 25
        radius: control.buttonRadius + 12
        color: Qt.rgba(control.accentColor.r, control.accentColor.g, control.accentColor.b, 0.03)
        opacity: control.isActive ? 0.6 : 0.0
        z: 0
        Behavior on opacity {
            NumberAnimation { duration: 200; easing.type: Easing.InOutQuad }
        }
    }

    Rectangle {
        id: activeGlow5
        anchors.centerIn: parent
        width: parent.width + 20
        height: parent.height + 20
        radius: control.buttonRadius + 10
        color: Qt.rgba(control.accentColor.r, control.accentColor.g, control.accentColor.b, 0.045)
        opacity: control.isActive ? 0.7 : 0.0
        z: 0
        Behavior on opacity {
            NumberAnimation { duration: 200; easing.type: Easing.InOutQuad }
        }
    }

    Rectangle {
        id: activeGlow6
        anchors.centerIn: parent
        width: parent.width + 15
        height: parent.height + 15
        radius: control.buttonRadius + 7
        color: Qt.rgba(control.accentColor.r, control.accentColor.g, control.accentColor.b, 0.065)
        opacity: control.isActive ? 0.8 : 0.0
        z: 0
        Behavior on opacity {
            NumberAnimation { duration: 200; easing.type: Easing.InOutQuad }
        }
    }

    Rectangle {
        id: activeGlow7
        anchors.centerIn: parent
        width: parent.width + 10
        height: parent.height + 10
        radius: control.buttonRadius + 5
        color: Qt.rgba(control.accentColor.r, control.accentColor.g, control.accentColor.b, 0.09)
        opacity: control.isActive ? 0.9 : 0.0
        z: 0
        Behavior on opacity {
            NumberAnimation { duration: 200; easing.type: Easing.InOutQuad }
        }
    }

    Rectangle {
        id: activeGlow8
        anchors.centerIn: parent
        width: parent.width + 6
        height: parent.height + 6
        radius: control.buttonRadius + 3
        color: Qt.rgba(control.accentColor.r, control.accentColor.g, control.accentColor.b, 0.12)
        opacity: control.isActive ? 1.0 : 0.0
        z: 0
    }

    // Эффект свечения при наведении (ПОД кнопкой) - очень мягкий
    Rectangle {
        id: glow1
        anchors.centerIn: parent
        width: parent.width + 40
        height: parent.height + 40
        radius: control.buttonRadius + 20
        color: Qt.rgba(control.accentColor.r, control.accentColor.g, control.accentColor.b, 0.008)
        opacity: (control.hovered && !control.isActive) ? 0.3 : 0.0
        z: 0
        Behavior on opacity {
            NumberAnimation { duration: 300; easing.type: Easing.InOutQuad }
        }
    }

    Rectangle {
        id: glow2
        anchors.centerIn: parent
        width: parent.width + 35
        height: parent.height + 35
        radius: control.buttonRadius + 17
        color: Qt.rgba(control.accentColor.r, control.accentColor.g, control.accentColor.b, 0.015)
        opacity: (control.hovered && !control.isActive) ? 0.4 : 0.0
        z: 0
        Behavior on opacity {
            NumberAnimation { duration: 350; easing.type: Easing.InOutQuad }
        }
    }

    Rectangle {
        id: glow3
        anchors.centerIn: parent
        width: parent.width + 30
        height: parent.height + 30
        radius: control.buttonRadius + 15
        color: Qt.rgba(control.accentColor.r, control.accentColor.g, control.accentColor.b, 0.022)
        opacity: (control.hovered && !control.isActive) ? 0.5 : 0.0
        z: 0
        Behavior on opacity {
            NumberAnimation { duration: 400; easing.type: Easing.InOutQuad }
        }
    }

    Rectangle {
        id: glow4
        anchors.centerIn: parent
        width: parent.width + 25
        height: parent.height + 25
        radius: control.buttonRadius + 12
        color: Qt.rgba(control.accentColor.r, control.accentColor.g, control.accentColor.b, 0.03)
        opacity: (control.hovered && !control.isActive) ? 0.6 : 0.0
        z: 0
        Behavior on opacity {
            NumberAnimation { duration: 450; easing.type: Easing.InOutQuad }
        }
    }

    Rectangle {
        id: glow5
        anchors.centerIn: parent
        width: parent.width + 20
        height: parent.height + 20
        radius: control.buttonRadius + 10
        color: Qt.rgba(control.accentColor.r, control.accentColor.g, control.accentColor.b, 0.045)
        opacity: (control.hovered && !control.isActive) ? 0.7 : 0.0
        z: 0
        Behavior on opacity {
            NumberAnimation { duration: 500; easing.type: Easing.InOutQuad }
        }
    }

    Rectangle {
        id: glow6
        anchors.centerIn: parent
        width: parent.width + 15
        height: parent.height + 15
        radius: control.buttonRadius + 7
        color: Qt.rgba(control.accentColor.r, control.accentColor.g, control.accentColor.b, 0.065)
        opacity: (control.hovered && !control.isActive) ? 0.8 : 0.0
        z: 0
        Behavior on opacity {
            NumberAnimation { duration: 550; easing.type: Easing.InOutQuad }
        }
    }

    Rectangle {
        id: glow7
        anchors.centerIn: parent
        width: parent.width + 10
        height: parent.height + 10
        radius: control.buttonRadius + 5
        color: Qt.rgba(control.accentColor.r, control.accentColor.g, control.accentColor.b, 0.09)
        opacity: (control.hovered && !control.isActive) ? 0.9 : 0.0
        z: 0
        Behavior on opacity {
            NumberAnimation { duration: 600; easing.type: Easing.InOutQuad }
        }
    }

    Rectangle {
        id: glow8
        anchors.centerIn: parent
        width: parent.width + 6
        height: parent.height + 6
        radius: control.buttonRadius + 3
        color: Qt.rgba(control.accentColor.r, control.accentColor.g, control.accentColor.b, 0.12)
        opacity: (control.hovered && !control.isActive) ? 1.0 : 0.0
        z: 0
    }

    background: Item {
        transform: Scale { origin.x: width/2; origin.y: height/2; xScale: control.currentScale; yScale: control.currentScale }
        z: 1  // Кнопка поверх свечения

        // Базовый фон кнопки
        Rectangle {
            id: btnBase
            anchors.fill: parent
            radius: control.buttonRadius
            color: "#252525"
            border.color: "#3a3a3a"
            border.width: 1
        }

        // InnerShadow — эффект "впалой" кнопки (внутренняя тень всегда видна)
        InnerShadow {
            anchors.fill: btnBase
            source: btnBase
            visible: true  // Всегда показываем (кнопка всегда выглядит "впалой")
            color: "#a0000000"  // Более насыщенный чёрный (было #80000000)
            radius: 12.0  // Увеличил размытие (было 8.0)
            samples: 24  // Увеличил качество (было 16)
            horizontalOffset: 3  // Увеличил смещение (было 2)
            verticalOffset: 3  // Увеличил смещение (было 2)
            spread: 0.5  // Усилил края (было 0.4)
            cached: true  // Кэшировать для производительности
        }
    }

    contentItem: RowLayout {
        anchors.fill: parent
        anchors.leftMargin: 12
        anchors.rightMargin: 12
        spacing: 8
        z: 2  // Текст и иконка поверх всего

        // Иконка
        Image {
            width: control.iconSize
            height: control.iconSize
            source: control.iconSource
            fillMode: Image.PreserveAspectFit
            opacity: control.isActive ? 1.0 : 0.7
            visible: control.iconSource !== ""
            Layout.alignment: Qt.AlignVCenter
        }

        Text {
            text: control.text
            color: control.hovered || control.isActive ? "#ffffff" : "#c2c2c2"
            font.pointSize: control.textSize
            horizontalAlignment: Text.AlignHCenter
            Layout.fillWidth: true
            Layout.alignment: Qt.AlignVCenter
        }
    }

    onPressed: currentScale = pressScale
    onReleased: currentScale = 1.0
    onCanceled: currentScale = 1.0

    // Обновление при изменении акцентного цвета
    Connections {
        target: backend
        function onSettingsChanged() {
            control.accentColor = backend.settings.accent_color !== undefined && backend.settings.accent_color !== null ? backend.settings.accent_color : "#7793a1"
        }
    }
}
