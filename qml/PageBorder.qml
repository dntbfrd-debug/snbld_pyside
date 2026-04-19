import QtQuick 2.15

// Пустой компонент (рамки удалены)
Item {
    id: pageBorder
    property color accentColor: backend && backend.settings && backend.settings.accent_color !== undefined && backend.settings.accent_color !== null ? backend.settings.accent_color : "#7793a1"
    anchors.fill: parent
}
