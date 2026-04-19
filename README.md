# 🎮 snbld resvap — Универсальная система макросов для Perfect World

> Мощная и прозрачная система автоматизации скиллов для любых серверов Perfect World. Открытый код, полная прозрачность, никаких скрытых функций.

**🔓 Репозиторий:** [github.com/dntbfrd-debug/snbld_pyside](https://github.com/dntbfrd-debug/snbld_pyside)

---

## ✨ Возможности

- 🎯 **Умные макросы** — проверка кулдаунов, дистанции, каста
- 🏃 **Автодобегание** — с таймаутом 3 сек
- 🔄 **Ресвап** — смена экипировки между пением и атакой
- 👁️ **OCR** — распознавание дистанции через Tesseract
- 🎨 **Детекция кастбара** — по цвету пикселя (mss)
- 💊 **Баффы** — пересчёт времени каста от channeling_bonus
- 🔐 **Активация** — ключ + HWID (CPU+motherboard+disk)

---

## 🚀 Быстрый старт

### Установка

```bash
# 1. Клонируй репозиторий
git clone https://github.com/dntbfrd-debug/snbld_pyside.git
cd snbld_pyside

# 2. Установи зависимости
pip install -r requirements.txt

# 3. Настрой .env (если нужны токены)
copy .env.example .env
# Вставь реальные токены в .env

# 4. Запусти
python qml_main.py
```

### Сборка EXE

```bash
# Windows
build.bat
```

---

## 📁 Структура проекта

```
snbld_pyside/
├── qml_main.py              # Главный файл входа
├── macros_core.py           # Базовая логика макросов
├── tesseract_reader.py      # OCR распознавание
├── threads.py               # Потоки мониторинга
├── auth.py                  # Активация + HWID
├── constants.py             # Константы проекта
│
├── backend/
│   ├── macros_dispatcher.py       # Очередь макросов
│   ├── settings_manager.py        # Менеджер настроек
│   ├── window_manager.py          # Управление окнами
│   ├── session_log.py             # Логирование сессий
│   └── ... (другие менеджеры)
│
├── qml/
│   ├── main.qml             # Главное окно
│   ├── MacrosListPage.qml   # Список макросов
│   ├── SettingsPage.qml     # Настройки
│   └── components/          # UI компоненты
│
├── docs/                    # Документация
├── icons/                   # Иконки
└── profiles/                # Пользовательские профили
```

---

## 🔧 Технологии

- **Python 3.12**
- **PySide6 6.11.0** (Qt Quick/QML)
- **Tesseract OCR 5.0**
- **mss** — быстрый захват экрана
- **WinAPI / SendInput** — низкоуровневый ввод
- **psutil** — мониторинг процессов

---

## 📖 Документация

Полная документация находится в папке `/docs/`:
- 📄 `docs/01-overview.md` — Обзор системы
- 📄 `docs/10-architecture.md` — Архитектура
- 📄 `docs/12-macros-types.md` — Типы макросов
- 📄 `docs/17-reference.md` — Справочник API

---

## 🔒 Безопасность

- ✅ Секреты хранятся только в `.env`
- ✅ Сессия зашифрована через Windows DPAPI
- ✅ Ключ активации привязан к железу
- ✅ `.env` никогда не попадает в репозиторий

---

## 📞 Контакты

- **Telegram:** [@rtmnklvch](https://t.me/rtmnklvch)
- **Сайт:** [snbld.ru](https://snbld.ru)

---

## ⚖️ Лицензия

MIT License — свободное использование с сохранением уведомления об авторстве.