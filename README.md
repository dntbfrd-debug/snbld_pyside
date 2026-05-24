
## Возможности

- **Умные макросы** — проверка кулдаунов, дистанции, каста (SkillMacro, ZoneMacro, BuffMacro, SimpleMacro)
- **Автодобегание** — с таймаутом 3 сек и детекцией кастбара
- **Ресвап** — смена экипировки между пением и атакой
- **OCR** — распознавание дистанции через Tesseract (с поддержкой калибровки)
- **Детекция кастбара** — по цвету пикселя (mss DXGI), с калибровкой
- **Баффы** — пересчёт времени каста от channeling_bonus, автоматическое применение
- **Зональные макросы** — привязка к области экрана, срабатывание по клику
- **Активация** — ключ + HWID (CPU+motherboard+disk), с шифрованием через Windows DPAPI
- **Низкоуровневый ввод** — SendInput + PostMessage через WinAPI, AttachThreadInput fallback
- **Менеджер окон** — автоматическая активация окна игры, поддержка DPI
- **Профили** — сохранение/загрузка/переименование наборов макросов и настроек
- **Звуковые уведомления** — MP3 при старте/стопе макросов
- **Современный UI** — Qt Quick/QML интерфейс (Glass тема)

---

## Быстрый старт

### Установка

```bash
# 1. Клонируй репозиторий
git clone https://github.com/dntbfrd-debug/snbld_pyside.git
cd snbld_pyside

# 2. Установи зависимости
pip install -r requirements.txt

# 3. Запусти
python qml_main.py
```

### Сборка EXE (Nuitka)

```bash
# Компиляция через Python
python build_nuitka.py
```

---

## Структура проекта

```
snbld_pyside/
├── qml_main.py                 # Главный файл входа (PySide6 + QML)
├── macros_core.py              # Базовая логика макросов
├── tesseract_reader.py         # OCR распознавание дистанции
├── threads.py                  # Потоки мониторинга (PingMonitor, MouseClickMonitor, BuffCheck)
├── auth.py                     # Активация + HWID (+ Windows DPAPI шифрование)
├── constants.py                # Константы проекта
├── input_blocker.py            # Блокировка ввода (WH_KEYBOARD/MOUSE_LL)
├── low_level_hook.py           # Низкоуровневый перехват мыши
├── skill_database.py           # База данных скиллов (из asgard_skills.json)
├── tooltips_qml.py             # Тултипы для QML
├── utils_qml.py                # Утилиты для QML
├── updater_main.py             # Автообновление
├── build_nuitka.py             # Сборка через Nuitka
├── release_tool.py             # Инструмент для создания релизов
├── deploy_update.bat           # Деплой обновлений на S3
├── app.manifest                # Windows манифест (DPI awareness, admin)
├── asgard_skills.json          # База скиллов (данные)
├── snbld_resvap.iss            # Inno Setup скрипт установщика
├── requirements.txt            # Python зависимости
├── version.json                # Версия приложения (для автообновления)
├── qtquickcontrols2.conf       # Стиль Qt Quick Controls
├── run.pyw                     # Альтернативный вход (без консоли)
│
├── backend/
│   ├── __init__.py             # Re-export основных классов
│   ├── win32_api.py            # Pure ctypes обёртка WinAPI
│   ├── input_system.py         # Система ввода (SendInput/PostMessage)
│   ├── macros_dispatcher.py    # Очередь и диспетчеризация макросов (с приоритетами)
│   ├── settings_manager.py     # Менеджер настроек (JSON + debounced save)
│   ├── window_manager.py       # Управление окнами (активация, DPI, Enumerate)
│   ├── logger_manager.py       # Централизованный логгер (по категориям)
│   ├── qml_bridge.py           # Мост между Python и QML (слоты/сигналы)
│   ├── session_log.py          # Таймлайн игровой сессии (JSONL)
│   ├── keyboard_shim.py        # Замена keyboard library через WinAPI
│   ├── hooks_guard.py          # Страж глобальных хуков (восстановление)
│   ├── attach_thread.py        # Context manager AttachThreadInput (с UIPI fallback)
│   ├── auth_mixin.py           # Активация/подписка/ heartbeat
│   ├── macro_mixin.py          # CRUD макросов + профили
│   ├── ocr_mixin.py            # OCR + калибровка + тестирование
│   ├── castbar_mixin.py        # Детекция кастбара (mss singleton)
│   ├── window_mixin.py         # Регистрация хоткеев + управление окнами
│   └── settings_mixin.py       # Загрузка/сохранение настроек
│
├── macros/
│   ├── __init__.py             # SimpleMacro, SkillMacro, ZoneMacro, BuffMacro
│   └── steps_executor.py       # Исполнитель шагов макроса
│
├── utils/
│   ├── file_utils.py           # Работа с файлами и путями
│   ├── resource_utils.py       # Управление ресурсами (пути, иконки)
│   ├── sound_alert.py          # Звуковые уведомления (MP3/Beep)
│   └── tray_icon.py            # Иконка в системном трее
│
├── qml/
│   ├── main.qml                # Главное окно
│   ├── MacrosListPage.qml      # Список макросов
│   ├── MacrosEditPage.qml      # Редактор макросов
│   ├── SettingsPage.qml        # Главная страница настроек
│   ├── SettingsMainPage.qml    # Основные настройки
│   ├── SettingsAppearancePage.qml # Внешний вид
│   ├── SettingsCastbarPage.qml # Настройки кастбара
│   ├── SettingsMovementPage.qml # Настройки движения
│   ├── SettingsWindowPage.qml  # Настройки окна
│   ├── SettingsReswapPage.qml  # Настройки ресвапа
│   ├── SettingsNetworkPage.qml # Настройки сети/пинга
│   ├── SettingsOCRPage.qml     # Настройки OCR
│   ├── SettingsOCRAreasPage.qml # Выбор областей OCR
│   ├── SettingsDebugPage.qml   # Отладка
│   ├── SettingsOtherPage.qml   # Прочие настройки
│   ├── ActivationPage.qml      # Активация
│   ├── ProfilesPage.qml        # Профили
│   ├── SubscriptionPage.qml    # Подписка
│   ├── HelpPage.qml            # Помощь
│   ├── DebugPage.qml           # Отладка
│   ├── BuffListPage.qml        # Список баффов
│   ├── EditSimplePage.qml      # Редактор простого макроса
│   ├── EditSkillPage.qml       # Редактор скилл-макроса
│   ├── EditZonePage.qml        # Редактор зонального макроса
│   ├── EditBuffPage.qml        # Редактор бафф-макроса
│   ├── SimpleEditForm.qml      # Форма простого макроса
│   ├── SkillEditForm.qml       # Форма скилл-макроса
│   ├── ZoneEditForm.qml        # Форма зонального макроса
│   ├── BuffEditForm.qml        # Форма бафф-макроса
│   ├── EditPanel.qml           # Панель редактирования
│   ├── IconStrip.qml           # Боковая навигационная панель
│   ├── SlideMenu.qml           # Выдвижное меню
│   ├── StripIcon.qml           # Элемент навигации
│   ├── MenuButton.qml          # Кнопка меню
│   ├── BaseButton.qml          # Базовая кнопка
│   ├── ActionButton.qml        # Кнопка действия
│   ├── CustomTabButton.qml     # Кастомная таб-кнопка
│   ├── ButtonGroupWithIndicator.qml # Группа кнопок с индикатором
│   ├── HoverPanel.qml          # Панель с hover-эффектом
│   ├── PageBorder.qml          # Граница страницы
│   ├── SkillClassSelector.qml  # Выбор класса скиллов
│   ├── SkillSelectionDialog.qml # Диалог выбора скилла
│   ├── OCROptionsSelector.qml  # Панель калибровки OCR
│   ├── OCRCalibrationDialog.qml # Диалог калибровки OCR
│   ├── FastOCRDebugOverlay.qml # Оверлей отладки OCR
├── CastBarDialog.qml       # Диалог калибровки кастбара
│   ├── BuffCalibrationDialog.qml # Диалог калибровки баффа
│   ├── AddStepDialog.qml       # Диалог добавления шага
│   ├── WindowSelectorDialog.qml # Диалог выбора окна
│   ├── ZoneAreaSelector.qml    # Выбор зональной области
│   ├── AreaSelector.qml        # Выбор области на экране
│   └── components/             # UI компоненты (Glass тема)
│       ├── GlassBlurPanel.qml
│       ├── GlassPanel.qml
│       ├── GlassRect.qml
│       ├── GlassScrollBar.qml
│       ├── GlassTextField.qml
│       └── AreaCoordinateInput.qml
│
├── icons/                      # Иконки интерфейса
├── fonts/                      # Шрифты (Rubik, Fira Code)
├── tesseract/                  # Tesseract OCR бинарники 5.5 + tessdata (rus, eng)
├── onn.mp3 / off.mp3 / exit.mp3 # Звуки старта/стопа/выхода макросов
├── 12.mp4                      # Фоновое видео главного окна
├── 123.ico                     # Иконка приложения
├── logo.png                    # Логотип
└── cache/icons/skills/         # Кэш иконок скиллов (PNG)
```

---

## Технологии

- **Python 3.12**
- **PySide6 6.8** (Qt Quick/QML)
- **Tesseract OCR 5.5** + pytesseract
- **mss** — быстрый захват экрана (DXGI)
- **OpenCV / numpy** — обработка изображений
- **Nuitka** — компиляция в нативный EXE
- **Inno Setup 6** — установщик Windows
- **WinAPI (ctypes)** — низкоуровневый ввод, хуки, окна, DPAPI
- **requests / boto3** — сетевые запросы и S3


## Контакты

- **Telegram:** [@rtmnklvch](https://t.me/rtmnklvch)
- **Сайт:** [snbld.ru](https://snbld.ru)

---

## Лицензия

MIT License — свободное использование с сохранением уведомления об авторстве.
