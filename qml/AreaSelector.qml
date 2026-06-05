import QtQuick 2.15
import QtQuick.Controls.Basic 2.15
import QtQuick.Window 2.15

Window {
    id: window
    flags: Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint
    color: "#80000000"
    width: Screen.width
    height: Screen.height
    title: "Выберите область"

    property point startPoint: Qt.point(0, 0)
    property point endPoint: Qt.point(0, 0)
    property bool selecting: false
    property string targetType: "mob"

    signal areaSelected(int x1, int y1, int x2, int y2)
    signal cancelled()

    // Метод для открытия с указанием типа цели
    function open(target_type) {
        targetType = target_type
        window.show()
        window.requestActivate()
        window.raise()
    }

    // Прямоугольник выделения – тонкая зелёная граница
    Rectangle {
        id: selectionRect
        color: "transparent"
        border.color: "lime"
        border.width: 1
        visible: selecting
        x: Math.min(startPoint.x, endPoint.x)
        y: Math.min(startPoint.y, endPoint.y)
        width: Math.abs(endPoint.x - startPoint.x)
        height: Math.abs(endPoint.y - startPoint.y)
        z: 100
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
            text: "Зажмите левую кнопку мыши и выделите область\nДля отмены нажмите ESC"
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
            console.log("AreaSelector: Pressed at", mouse.x, mouse.y)
        }
        onPositionChanged: function(mouse) {
            if (selecting) {
                endPoint = Qt.point(mouse.x, mouse.y)
                console.log("AreaSelector: Moving to", mouse.x, mouse.y)
            }
        }
        onReleased: function(mouse) {
            if (selecting) {
                var x1 = Math.min(startPoint.x, endPoint.x)
                var y1 = Math.min(startPoint.y, endPoint.y)
                var x2 = Math.max(startPoint.x, endPoint.x)
                var y2 = Math.max(startPoint.y, endPoint.y)
                console.log("AreaSelector: Selected area", x1, y1, x2, y2, "for", targetType)
                
                // Отправляем сигнал в backend
                areaSelected(x1, y1, x2, y2)
                window.close()
            }
            selecting = false
        }
    }

    // Отправляем сигнал в backend при выборе области
    onAreaSelected: {
        if (backend) {
            // Проверяем тип выбора по targetType
            if (targetType === "macro") {
                // Выбор зоны для макроса
                backend.onAreaSelected(x1, y1, x2, y2)
            } else {
                // Выбор области OCR (mob, player)
                backend.onOCRAreaSelected(targetType, x1, y1, x2, y2)
            }
        }
    }

    Shortcut {
        sequence: "Esc"
        onActivated: {
            console.log("AreaSelector: Cancelled")
            cancelled()
            window.close()
        }
    }
}
