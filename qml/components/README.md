# QML Компоненты

Папка `components/` содержит переиспользуемые QML компоненты.

## Список компонентов

### MacroCard.qml
Карточка макроса для отображения в списке.

**Свойства:**
- `macroName` - Название макроса
- `macroType` - Тип (simple/zone/skill/buff)
- `macroIcon` - Путь к иконке
- `macroHotkey` - Горячая клавиша
- `isRunning` - Статус выполнения
- `cooldown`, `skillRange` - Параметры скилла

**Сигналы:**
- `editClicked()`
- `deleteClicked()`
- `startClicked()`
- `stopClicked()`

**Пример:**
```qml
MacroCard {
    macroName: "Огненный шар"
    macroType: "skill"
    macroIcon: "icons/skills/123.png"
    isRunning: false
    onEditClicked: openEditDialog()
}
```

---

### AreaCoordinateInput.qml
Поле ввода координаты области с debounce (300 мс).

**Свойства:**
- `areaValue` - Текущее значение области [x1,y1,x2,y2]
- `coordinateIndex` - Индекс координаты (0-3)
- `defaultValue` - Значение по умолчанию [0,0,0,0]
- `areaKey` - Ключ настройки ("mob_area" или "player_area")

**Пример:**
```qml
AreaCoordinateInput {
    areaValue: backend.settings.mob_area
    coordinateIndex: 0
    areaKey: "mob_area"
    defaultValue: [1084, 271, 1545, 358]
}
```

---

## Использование в проекте

1. **Импорт компонентов:**
```qml
import "../components"
```

2. **Комбинирование компонентов:**
```qml
ColumnLayout {
    RowLayout {
        AreaCoordinateInput { areaKey: "mob_area"; coordinateIndex: 0; ... }
        AreaCoordinateInput { areaKey: "mob_area"; coordinateIndex: 1; ... }
    }
}
```

## Преимущества

- **Единый стиль** - все компоненты используют общую цветовую схему
- **Переиспользование** - один компонент используется в разных местах
- **Debounce** - AreaCoordinateInput предотвращает race conditions при быстром вводе
- **Поддержка** - изменение стиля в одном месте обновляет все компоненты
