import QtQuick 2.15
import QtQuick.Controls.Basic 2.15
import QtQuick.Layouts 1.15

BaseButton {
    id: control
    property bool isActive: false

    buttonRadius: 12          // для плиток делаем радиус 12
    iconSize: 24
    textSize: 12
}
