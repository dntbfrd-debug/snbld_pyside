import QtQuick 2.15
import QtQuick.Controls.Basic 2.15

// Управляет переключением isActive между кнопками с каскадной анимацией.
// Сама визуальная анимация активной кнопки уже реализована в BaseButton (8 слоёв свечения).
Item {
    id: root
    property var buttons: []
    property var setActiveCallback: function(activeButton) {
        for (var i = 0; i < buttons.length; ++i) {
            buttons[i].isActive = false
        }
        activeButton.isActive = true
    }

    // Текущий активный индекс
    property int currentIndex: 0

    // Параметры для каскадного перекатывания
    property int _stepTo: 0
    property int _stepDir: 0
    property int _stepCur: 0
    property bool _stepping: false

    // Таймер для поэтапного перекатывания через кнопки
    Timer {
        id: stepTimer
        interval: 80
        repeat: false
        onTriggered: {
            if (!root._stepping) return

            var next = root._stepCur + root._stepDir

            if (next === root._stepTo) {
                // Последний шаг — финальная кнопка
                _activateOnly(root._stepTo)
                root._stepping = false
            } else {
                // Промежуточный шаг — подсвечиваем эту кнопку
                root._stepCur = next
                _activateOnly(root._stepCur)
                stepTimer.start()
            }
        }
    }

    // Активировать только одну кнопку по индексу (остальные выключить)
    function _isValid(idx) {
        return idx >= 0 && idx < buttons.length && buttons[idx] !== undefined && buttons[idx] !== null
    }

    function _activateOnly(idx) {
        if (!_isValid(idx)) return
        var btn = buttons[idx]
        for (var i = 0; i < buttons.length; ++i) {
            if (buttons[i] !== undefined && buttons[i] !== null) {
                buttons[i].isActive = (i === idx)
            }
        }
        root.currentIndex = idx
        if (setActiveCallback) setActiveCallback(btn)
    }

    function moveTo(targetButton) {
        var gidx = -1
        for (var i = 0; i < buttons.length; ++i) {
            if (buttons[i] === targetButton) {
                gidx = i
                break
            }
        }
        if (gidx < 0) return

        if (gidx === currentIndex) {
            // Тот же индекс — просто активируем
            _activateOnly(gidx)
            return
        }

        // Останавливаем старую анимацию
        stepTimer.stop()
        _stepping = false

        // Определяем направление
        var dir = gidx > currentIndex ? 1 : -1

        // Настраиваем поэтапное перекатывание
        _stepTo = gidx
        _stepDir = dir
        _stepCur = currentIndex
        _stepping = true

        // Первый шаг — оставляем текущую активной, переключаем таймер
        // Если расстояние всего 1 шаг — финальная активация
        if (gidx === currentIndex + dir) {
            _activateOnly(gidx)
            _stepping = false
            return
        }
        stepTimer.start()
    }

    function setActive(activeButton) {
        if (!activeButton) {
            _stepping = false
            stepTimer.stop()
            for (var i = 0; i < buttons.length; ++i) {
                if (buttons[i] !== undefined && buttons[i] !== null) {
                    buttons[i].isActive = false
                }
            }
            return
        }
        moveTo(activeButton)
    }

    function clearActive() {
        _stepping = false
        stepTimer.stop()
        for (var i = 0; i < buttons.length; ++i) {
            buttons[i].isActive = false
        }
    }

    function init() {
        if (buttons.length > 0 && buttons[0] !== undefined && buttons[0] !== null) {
            _activateOnly(0)
        }
    }

    onButtonsChanged: init()
}