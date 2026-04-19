import QtQuick 2.15
import QtQuick.Controls.Basic 2.15

Item {
    id: root
    property var buttons: []
    property var setActiveCallback: function(activeButton) {
        for (var i = 0; i < buttons.length; ++i) {
            buttons[i].isActive = false
        }
        activeButton.isActive = true
    }
    property int leftInset: 10
    property int topInset: 10
    property int rightInset: 10
    property int bottomInset: 10
    
    property color accentColor: backend && backend.settings && backend.settings.accent_color !== undefined && backend.settings.accent_color !== null ? backend.settings.accent_color : "#7793a1"

    // Индикатор активной кнопки (статичный, без анимации)
    Rectangle {
        id: indicator
        radius: 8
        color: "#1a1a1a"
        opacity: 0
        border.width: 0
        z: 2
        enabled: false
    }

    PropertyAnimation {
        id: animX
        target: indicator
        property: "x"
        duration: 250
        easing.type: Easing.InOutQuad
    }
    PropertyAnimation {
        id: animY
        target: indicator
        property: "y"
        duration: 250
        easing.type: Easing.InOutQuad
    }
    PropertyAnimation {
        id: animWidth
        target: indicator
        property: "width"
        duration: 250
        easing.type: Easing.InOutQuad
    }
    PropertyAnimation {
        id: animHeight
        target: indicator
        property: "height"
        duration: 250
        easing.type: Easing.InOutQuad
    }

    function moveTo(targetButton) {
        var pos = targetButton.mapToItem(root, 0, 0)
        animX.to = pos.x - leftInset
        animY.to = pos.y - topInset
        animWidth.to = targetButton.width + leftInset + rightInset
        animHeight.to = targetButton.height + topInset + bottomInset
        animX.start()
        animY.start()
        animWidth.start()
        animHeight.start()
    }

    function setActive(activeButton) {
        if (setActiveCallback) setActiveCallback(activeButton)
        moveTo(activeButton)
    }

    function init() {
        if (buttons.length > 0) {
            var pos = buttons[0].mapToItem(root, 0, 0)
            indicator.x = pos.x - leftInset
            indicator.y = pos.y - topInset
            indicator.width = buttons[0].width + leftInset + rightInset
            indicator.height = buttons[0].height + topInset + bottomInset
        }
    }

    onButtonsChanged: init()
    
    // Обновление при изменении акцентного цвета
    Connections {
        target: backend
        function onSettingsChanged() {
            root.accentColor = backend.settings.accent_color !== undefined && backend.settings.accent_color !== null ? backend.settings.accent_color : "#7793a1"
        }
    }
}
