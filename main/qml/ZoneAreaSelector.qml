import QtQuick 2.15
import QtQuick.Controls.Basic 2.15
import QtQuick.Window 2.15

Window {
    id: window
    flags: Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint
    color: "#80000000"
    width: Screen.width
    height: Screen.height
    title: "Выберите область для макроса"

    property point startPoint: Qt.point(0, 0)
    property point endPoint: Qt.point(0, 0)
    property bool selecting: false

    signal zoneAreaSelected(int x1, int y1, int x2, int y2)
    signal cancelled()

    // Прямоугольник выделения
    Rectangle {
        id: selectionRect
        color: "transparent"
        border.color: "#00ff00"  // Зелёная граница
        border.width: 2
        visible: selecting
        x: Math.min(startPoint.x, endPoint.x)
        y: Math.min(startPoint.y, endPoint.y)
        width: Math.abs(endPoint.x - startPoint.x)
        height: Math.abs(endPoint.y - startPoint.y)
        z: 100

        // Полупрозрачная заливка
        Rectangle {
            anchors.fill: parent
            color: "#4000ff00"
            z: -1
        }
    }

    // Инструкция
    Rectangle {
        anchors.centerIn: parent
        width: instructionText.width + 40
        height: instructionText.height + 30
        color: "#aa000000"
        radius: 12
        z: 90

        Text {
            id: instructionText
            anchors.centerIn: parent
            text: "Зажмите ЛКМ и выделите область для макроса\nОтпустите для выбора\nESC для отмены"
            color: "white"
            font.pointSize: 16
            font.bold: true
            horizontalAlignment: Text.AlignHCenter
            wrapMode: Text.WordWrap
        }
    }

    MouseArea {
        anchors.fill: parent
        propagateComposedEvents: false
        onPressed: function(mouse) {
            selecting = true
            startPoint = Qt.point(mouse.x, mouse.y)
            endPoint = startPoint
            console.log("ZoneAreaSelector: Pressed at", mouse.x, mouse.y)
        }
        onPositionChanged: function(mouse) {
            if (selecting) {
                endPoint = Qt.point(mouse.x, mouse.y)
                console.log("ZoneAreaSelector: Moving to", mouse.x, mouse.y)
            }
        }
        onReleased: function(mouse) {
            if (selecting) {
                var x1 = Math.min(startPoint.x, endPoint.x)
                var y1 = Math.min(startPoint.y, endPoint.y)
                var x2 = Math.max(startPoint.x, endPoint.x)
                var y2 = Math.max(startPoint.y, endPoint.y)
                console.log("ZoneAreaSelector: Selected zone", x1, y1, x2, y2)

                // Отправляем сигнал в backend
                zoneAreaSelected(x1, y1, x2, y2)
                window.close()
            }
            selecting = false
        }
    }

    // Отправляем сигнал в backend при выборе области
    onZoneAreaSelected: {
        if (backend) {
            backend.onZoneAreaSelected(x1, y1, x2, y2)
        }
    }

    Shortcut {
        sequence: "Esc"
        onActivated: {
            console.log("ZoneAreaSelector: Cancelled")
            cancelled()
            window.close()
        }
    }
}
