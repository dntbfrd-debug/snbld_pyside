// AreaCoordinateInput.qml — поле ввода координаты области с debounce
import QtQuick 2.15
import QtQuick.Controls.Basic 2.15
import QtQuick.Layouts 1.15

TextField {
    id: root
    Layout.preferredWidth: 70
    Layout.preferredHeight: 28
    background: Rectangle { radius: 4; color: "#40ffffff" }
    validator: IntValidator { bottom: 0 }

    // Внешние свойства
    property var areaValue: []       // Текущее значение области [x1,y1,x2,y2]
    property int coordinateIndex: 0  // Индекс координаты (0-3)
    property var defaultValue: [0,0,0,0]  // Значение по умолчанию

    // Debounce таймер
    Timer {
        id: debounceTimer
        interval: 300  // 300 мс задержка
        repeat: false
        onTriggered: {
            var area = (root.areaValue !== undefined && root.areaValue.length === 4) ? [...root.areaValue] : [...root.defaultValue];
            area[root.coordinateIndex] = parseInt(root.text) || 0;
            backend.set_setting(root.areaKey, area);
        }
    }

    // Ключ настройки (устанавливается извне: "mob_area" или "player_area")
    property string areaKey: ""

    // При получении фокуса — обновляем текст из areaValue
    onFocusChanged: {
        if (focus) {
            var area = (root.areaValue !== undefined && root.areaValue.length === 4) ? root.areaValue : root.defaultValue;
            root.text = area[root.coordinateIndex];
        }
    }

    // При завершении редактирования — запускаем debounce
    onEditingFinished: {
        debounceTimer.restart();
    }
}
