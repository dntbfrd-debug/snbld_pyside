
##   Возможности

-  **Умные макросы** — проверка кулдаунов, дистанции, каста
-  **Автодобегание** — с таймаутом 3 сек
-  **Ресвап** — смена экипировки между пением и атакой
-  **OCR** — распознавание дистанции через Tesseract
-  **Детекция кастбара** — по цвету пикселя (mss)
-  **Баффы** — пересчёт времени каста от channeling_bonus
-  **Активация** — ключ + HWID (CPU+motherboard+disk)
-  **Низкоуровневый ввод** — SendInput + PostMessage через WinAPI
-  **Звуковые уведомления** — MP3 при старте/стопе макросов
-  **Современный UI** — Qt Quick/QML интерфейс (Glass тема)

---

##  Быстрый старт

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
# Windows - полная сборка (Nuitka + Inno Setup)
build.bat

# Или только компиляция через Python
python build_nuitka.py
```

---

## 📁 Структура проекта

```
snbld_pyside/
├── qml_main.py              # Главный файл входа (PySide6 + QML)
├── macros_core.py           # Базовая логика макросов
├── tesseract_reader.py      # OCR распознавание дистанции
├── threads.py               # Потоки мониторинга
├── auth.py                  # Активация + HWID
├── constants.py             # Константы проекта
├── input_blocker.py         # Блокировка ввода (WH_KEYBOARD/MOUSE_LL)
├── low_level_hook.py        # Низкоуровневый перехват мыши
├── skill_database.py        # База данных скиллов
├── raw_input_wm_detector.py # Детектор кликов (polling)
├── tooltips_qml.py          # Тултипы для QML
├── utils_qml.py             # Утилиты для QML
├── updater_main.py          # Автообновление
├── build.bat                # Скрипт сборки (Nuitka + Inno Setup)
├── build_nuitka.py          # Nuitka сборка (Python)
│
├── backend/
│   ├── __init__.py           # Re-export основных классов
│   ├── win32_api.py          # Pure ctypes обёртка WinAPI
│   ├── input_system.py       # Система ввода (SendInput/PostMessage)
│   ├── macros_dispatcher.py  # Очередь и диспетчеризация макросов
│   ├── settings_manager.py   # Менеджер настроек
│   ├── window_manager.py     # Управление окнами
│   ├── logger_manager.py     # Централизованный логгер
│   ├── qml_bridge.py         # Мост между Python и QML
│   ├── session_log.py        # Таймлайн игровой сессии
│   ├── keyboard_shim.py      # Замена keyboard library через WinAPI
│   ├── hooks_guard.py        # Страж глобальных хуков
│   ├── attach_thread.py      # Context manager AttachThreadInput
│   ├── auth_mixin.py         # Активация/подписка
│   ├── macro_mixin.py        # CRUD макросов + профили
│   ├── ocr_mixin.py          # OCR + калибровка
│   ├── castbar_mixin.py      # Детекция кастбара
│   ├── window_mixin.py       # Регистрация хоткеев + окна
│   └── settings_mixin.py     # Загрузка/сохранение настроек
│
├── macros/
│   └── steps_executor.py    # Исполнитель шагов макроса
│
├── utils/
│   ├── file_utils.py         # Работа с файлами и путями
│   ├── resource_utils.py     # Управление ресурсами
│   ├── sound_alert.py        # Звуковые уведомления (MP3/Beep)
│   └── tray_icon.py          # Иконка в системном трее
│
├── qml/
│   ├── main.qml              # Главное окно
│   ├── MacrosListPage.qml    # Список макросов
│   ├── MacrosEditPage.qml    # Редактор макросов
│   ├── Settings*.qml         # Страницы настроек
│   ├── ActivationPage.qml    # Активация
│   ├── ProfilesPage.qml      # Профили
│   ├── SubscriptionPage.qml  # Подписка
│   ├── HelpPage.qml          # Помощь
│   ├── DebugPage.qml         # Отладка
│   ├── Edit*.qml             # Формы редактирования макросов
│   ├── IconStrip.qml         # Боковая навигационная панель
│   ├── SlideMenu.qml         # Выдвижное меню
│   ├── StripIcon.qml         # Элемент навигации
│   ├── SkillClassSelector.qml / SkillSelectionDialog.qml  # Выбор скилла
│   ├── OCROptionsSelector.qml  # Панель калибровки OCR
│   ├── OCRCalibrationDialog.qml / CastBarDialog.qml / BuffCalibrationDialog.qml  # Калибровка
│   ├── AddStepDialog.qml / WindowSelectorDialog.qml  # Вспомогательные диалоги
│   └── components/           # UI компоненты (Glass тема)
│
├── icons/                    # Иконки интерфейса
├── fonts/                    # Шрифты (Rubik, Fira Code)
├── tesseract/                # Tesseract OCR бинарники + tessdata
├── onn.mp3 / off.mp3         # Звуки старта/стопа макросов
├── requirements.txt          # Python зависимости
├── version.json              # Версия приложения (для автообновления)
└── qtquickcontrols2.conf     # Стиль Qt Quick Controls
```

---

## 🔧 Технологии

- **Python 3.12**
- **PySide6 6.8** (Qt Quick/QML)
- **Tesseract OCR 5.0** + pytesseract
- **mss** — быстрый захват экрана
- **OpenCV** — обработка изображений
- **Nuitka** — компиляция в нативный EXE
- **Inno Setup 6** — установщик Windows
- **WinAPI (ctypes)** — низкоуровневый ввод, хуки, окна
- **requests / boto3** — сетевые запросы и S3

---

## 🔒 Безопасность

- ✅ Секреты хранятся только в `.env` (не в репозитории)
- ✅ Сессия зашифрована через Windows DPAPI
- ✅ Ключ активации привязан к железу (CPU+motherboard+disk)
- ✅ `.env` и пользовательские данные в `.gitignore`
- ✅ Открытый код — полная прозрачность

---

## 📞 Контакты

- **Telegram:** [@rtmnklvch](https://t.me/rtmnklvch)
- **Сайт:** [snbld.ru](https://snbld.ru)

---

## ⚖️ Лицензия

MIT License — свободное использование с сохранением уведомления об авторстве.
