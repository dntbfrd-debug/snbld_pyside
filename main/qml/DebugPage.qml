import QtQuick 2.15
import QtQuick.Controls.Basic 2.15
import QtQuick.Layouts 1.15

Item {
    id: debugPage
    
    property color accentColor: backend && backend.settings && backend.settings.accent_color ? backend.settings.accent_color : "#7793a1"

    StackView {
        id: debugPageStackView
        anchors.fill: parent
        clip: true
        
        pushEnter: Transition {
            PropertyAnimation { property: "x"; from: debugPageStackView.width; to: 0; duration: 300; easing.type: Easing.OutCubic }
            PropertyAnimation { property: "opacity"; from: 0; to: 1; duration: 300; easing.type: Easing.OutCubic }
        }
        pushExit: Transition {
            PropertyAnimation { property: "x"; from: 0; to: -debugPageStackView.width * 0.5; duration: 300; easing.type: Easing.InCubic }
            PropertyAnimation { property: "opacity"; from: 1; to: 0; duration: 300; easing.type: Easing.InCubic }
        }
        
        initialItem: Item {
            anchors.fill: parent
            
            Loader {
                id: debugLoader
                anchors.fill: parent
                source: "SettingsDebugPage.qml"
            }
        }
    }
}