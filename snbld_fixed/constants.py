# -*- coding: utf-8 -*-
"""
constants.py
Все константы проекта snbld resvap
Цвета, пути, настройки по умолчанию, API эндпоинты
"""

# ИЗМЕНЕНИЕ: Добавлен комментарий для проверки возможности редактирования файлов (AI-Assistant Test)

# ==================== API И СЕРВЕР ====================
API_URL = "https://snbld.ru"

# СЕКРЕТЫ — загружаются динамически с сервера после активации
# Для обратной совместимости оставляем переменные окружения (могут использоваться при разработке)
import os

SELECTEL_ACCESS_KEY = os.environ.get("SELECTEL_ACCESS_KEY", "")
SELECTEL_SECRET_KEY = os.environ.get("SELECTEL_SECRET_KEY", "")
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")

SELECTEL_BUCKET = "snbldfile"
SELECTEL_ENDPOINT = "https://s3.ru-3.storage.selcloud.ru"
SELECTEL_REGION = "ru-3"
UPDATE_BASE_URL = f"https://{SELECTEL_BUCKET}.{SELECTEL_ENDPOINT.replace('https://', '')}"
PUBLIC_DOMAIN = "resvap.snbld.ru"

# Версия приложения
CURRENT_VERSION = "1.3.43"

# ==================== НАСТРОЙКИ ПО УМОЛЧАНИЮ ====================
# Макросы и скиллы
DEFAULT_SWAP_KEY_CHANT = "e"
DEFAULT_SWAP_KEY_PA = "e"
DEFAULT_BASE_CHANNELING = 91
DEFAULT_CASTBAR_SWAP_DELAY = 10
DEFAULT_COOLDOWN_MARGIN = 0.45
DEFAULT_CAST_LOCK_MARGIN = 0.45
DEFAULT_MOVEMENT_DELAY_ENABLED = True
DEFAULT_MOVEMENT_DELAY_MS = 500
DEFAULT_CHECK_DISTANCE = False
DEFAULT_DISTANCE_TOLERANCE = 1.0
DEFAULT_TARGET_INTERVAL = 0.5
DEFAULT_WINDOW_OPACITY = 1.0

# Тема и цвета (тёмная тема)
DEFAULT_THEME = "glass"
DEFAULT_ACCENT_COLOR = "#495d68"
DEFAULT_BG_COLOR = "#3d3d3d"
DEFAULT_SECONDARY_BG = "#000000"
DEFAULT_FG_COLOR = "#7793a1"
DEFAULT_HOVER_COLOR = "#313f46"
DEFAULT_SELECTION_BG = "#4b626e"
DEFAULT_SELECTION_FG = "#515151"
DEFAULT_BORDER_COLOR = "#4b626e"
DEFAULT_TITLE_BAR_COLOR = "#3a3a3a"
DEFAULT_GROUP_TITLE_COLOR = "#babbbb"
DEFAULT_SELECTION_BORDER_COLOR = "#cccccc"

# Прозрачность и масштаб UI
DEFAULT_WINDOW_OPACITY = 1
DEFAULT_TITLE_BAR_OPACITY = 1
DEFAULT_PANEL_OPACITY = 1
DEFAULT_UI_SCALE = 1.0

# Фоновое изображение (не используется)
DEFAULT_BG_IMAGE_MODE = "cover"
DEFAULT_BG_IMAGE_OPACITY = 1

# Размеры элементов UI
DEFAULT_SKILL_ICON_SIZE = 36
DEFAULT_STATUS_ICON_SIZE = 36
DEFAULT_CELL_PADDING = 10
DEFAULT_ROW_HEIGHT = 100
DEFAULT_SHOW_MACRO_NAMES = True

# OCR и чтение цели
DEFAULT_CASTBAR_THRESHOLD = 90
DEFAULT_DISTANCE_TOLERANCE = 0.0
DEFAULT_TARGET_INTERVAL = 0.5
DEFAULT_OCR_SCALE = 10
DEFAULT_OCR_PSM = 10
DEFAULT_OCR_USE_MORPH = True

# Сеть и пинг
DEFAULT_PING_AUTO = True
DEFAULT_PING_CHECK_INTERVAL = 5  # 5 секунд вместо 30
DEFAULT_PROCESS_NAME = "ElementClient_x64.exe"
DEFAULT_SERVER_IP = "147.45.96.78"

# Области для OCR (по умолчанию)
DEFAULT_MOB_AREA = (1084, 271, 1545, 358)
DEFAULT_PLAYER_AREA = (1271, 16, 1294, 32)

# Задержки
DEFAULT_COLOR_THRESHOLD = 30

# ==================== РАЗМЕРЫ ОКНА ====================
MAIN_WINDOW_SIZE = "1300x750"
MIN_WINDOW_WIDTH = 1100
MIN_WINDOW_HEIGHT = 650

# ==================== ШРИФТЫ ====================
FONT_FAMILY = "Segoe UI"
FONT_SIZE_NORMAL = 10
FONT_SIZE_TITLE = 13
FONT_SIZE_MONO = 10

# ==================== ПУТИ К РЕСУРСАМ ====================
ICON_FILE = "123.ico"
LOGO_FILE = "logo.png"
SKILLS_JSON_FILE = "asgard_skills.json"
MACROS_JSON_FILE = "macros.json"
BUILD_NUMBER_FILE = "build_number.txt"
LOG_FILE = "debug.log"

# Папки
ICONS_DIR = "icons"
SKILL_ICONS_DIR = "icons/skills"
PROFILES_DIR = "profiles"
TEMPLATES_DIR = "templates"
STATIC_DIR = "static"
CACHE_DIR = "cache"
RELEASES_DIR = "releases"
TESSERACT_DIR = "tesseract"

# ==================== ИКОНКИ ====================
ICON_FILES = [
    "add.png", "archer_icon.png", "buff.png", "calibrate.png",
    "cancel.png", "delete.png", "down.png", "edit.png",
    "keyboard.png", "load.png", "macros.png", "mage_icon.png",
    "mouse.png", "off.png", "ok.png", "on.png",
    "play.png", "save.png", "settings.png", "skill.png",
    "stop.png", "swap.png", "up.png"
]

# ==================== ШАБЛОНЫ МАКРОСОВ ====================
DEFAULT_MACRO_STEPS = [
    ("key", "", 0),
    ("left", "", 0),
    ("wait", "", 100)
]

ACTION_TYPES = ["key", "left", "right", "wait"]

# ==================== СТАТУСЫ ПОДПИСКИ ====================
SUBSCRIPTION_STATUS = {
    "ACTIVE": "active",
    "EXPIRED": "expired",
    "NOT_FOUND": "not_found",
    "BANNED": "banned"
}

# ==================== ТАЙМЕРЫ ====================
SUBSCRIPTION_CHECK_INTERVAL = 1800  # 30 минут (в секундах)
PING_CHECK_INTERVAL = 30  # 30 секунд
BUFF_CHECK_INTERVAL = 0.5  # 0.5 секунды
MOVEMENT_MONITOR_BASE_INTERVAL = 0.01  # 10 мс
MOVEMENT_MONITOR_IDLE_INTERVAL = 0.05  # 50 мс

# ==================== КОМПЕНСАЦИЯ ПИНГА ====================
PING_COMPENSATION_BASE_MS = 30  # Базовая задержка в мс
PING_COMPENSATION_FACTOR = 0.7  # Множитель компенсации
PING_COMPENSATION_BASE_S = 0.02  # Базовая добавка в секундах
PING_COMPENSATION_MAX_S = 0.3  # Максимальная компенсация (сек)
PING_GAME_MULTIPLIER = 2.0  # ICMP → Игровой пинг

# ==================== ОКНА И ДИАЛОГИ ====================
DIALOG_TITLE = "snbld resvap"
DIALOG_DELETE_ON_CLOSE = True
DIALOG_SHOW_CLOSE = True
DIALOG_SHOW_MINIMIZE = True
TITLE_BAR_HEIGHT = 55
TITLE_BAR_BUTTON_SIZE = 50

# ==================== АНИМАЦИИ ====================
ANIMATION_DURATION = 150  # мс
ANIMATION_OPACITY_START = 0
ANIMATION_OPACITY_END = 1

# ==================== ОШИБКИ И ИСКЛЮЧЕНИЯ ====================
ERROR_CONNECTION = "Ошибка соединения с сервером"
ERROR_INVALID_KEY = "Неверный ключ активации"
ERROR_SUBSCRIPTION_EXPIRED = "Подписка истекла"
ERROR_HWID_MISMATCH = "HWID не совпадает"
ERROR_RESOURCE_NOT_FOUND = "Ресурс не найден"

# ==================== ЛОГИРОВАНИЕ ====================
LOG_FORMAT = "%(asctime)s - %(levelname)s - %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
LOG_BACKUP_COUNT = 1
LOG_ROTATION_INTERVAL = 10  # минут

# ==================== БЕЗОПАСНОСТЬ ====================
SSL_CERT_REQUIRED = True
SSL_VERIFY_TIMEOUT = 10

# ==================== ОБНОВЛЕНИЯ ====================
UPDATE_CHECK_ENABLED = True
UPDATE_DOWNLOAD_TIMEOUT = 30
UPDATE_CHUNK_SIZE = 8192

# ==================== СБОРКА ====================
PYINSTALLER_SPEC_TEMPLATE = """# -*- mode: python ; coding: utf-8 -*-

import certifi

a = Analysis(
    ['{main_py}'],
    pathex=['{project_path}'],
    binaries=[],
    datas=[
        ('{icons_path}', 'icons'),
        ('{fonts_path}', 'fonts'),
        {tesseract_line}
        ('{icon_path}', '.'),
        ('{bg_path}', '.'),
        ('{logo_path}', '.'),
        ('{hotkeys_path}', '.'),
        ('{macros_path}', '.'),
        ('{skill_db_path}', '.'),
        ('{asgard_path}', '.'),
        ('{auth_path}', '.'),
        ('{tesseract_reader_path}', '.'),
        ('{ocr_overlay_path}', '.'),
    ],
    hiddenimports=[
        'hotkeys', 'macros', 'skill_database', 'auth',
        'boto3', 'botocore', 'requests', 'packaging', 'psutil',
        'cv2', 'pytesseract',
        'certifi'
    ],
    hookspath=[],
    hooksconfig={{}},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

a.datas += [('certifi/cacert.pem', '{certifi_path}', 'DATA')]

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='{exe_name}',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='{icon_path}'
)
"""

# ==================== TELEGRAM ====================
TELEGRAM_BOT_NAME = "snbld_bot"
TELEGRAM_WEBAPP_URL = "https://snbld.ru/webapp"
TELEGRAM_BIND_URL_TEMPLATE = f"https://t.me/{TELEGRAM_BOT_NAME}?start=bind_{{hwid}}"

# ==================== ВИРТУАЛЬНЫЕ КЛАВИШИ (WinAPI) ====================
VIRTUAL_KEYS = {
    'w': 0x57, 'a': 0x41, 's': 0x53, 'd': 0x44,
    'up': 0x26, 'down': 0x28, 'left': 0x25, 'right': 0x27
}

# ==================== КЛАССЫ ПЕРСОНАЖЕЙ ====================
CHARACTER_CLASSES = [
    "воин", "маг", "жрец", "убийца", "варвар",
    "venomancer", "лучник", "мистик"
]

# ==================== СТИХИИ ====================
ELEMENTS = [
    "огонь", "вода", "земля", "ветер", "дерево",
    "металл", "тьма", "свет", "физический", "нейтральный"
]

# ==================== ТИПЫ МАКРОСОВ ====================
MACRO_TYPES = {
    "SIMPLE": "simple",
    "ZONE": "zone",
    "BUFF": "buff",
    "SKILL": "skill"
}

# ==================== ТИПЫ ЦЕЛЕЙ ====================
TARGET_TYPES = {
    "ENEMY": "enemy",
    "SELF": "self",
    "PARTY": "party",
    "AREA": "area"
}

# ==================== PSM TESSERACT ====================
OCR_PSM_MODES = {
    6: "Предположить единый блок текста",
    7: "Предположить одну строку текста",
    10: "Предположить одно символ",
    13: "Сырой текст. Найти как можно больше текста"
}

# ==================== ЦВЕТОВАЯ СХЕМА (тёмная тема) ====================
class ColorScheme:
    """Цветовая схема по умолчанию"""
    BG_PRIMARY = "#2b2b2b"
    BG_SECONDARY = "#3a3a3a"
    FG_PRIMARY = "#f0f0f0"
    FG_SECONDARY = "#c2c2c2"
    ACCENT = "#4a6a8a"
    ACCENT_AREA = "#ff6b6b"
    SELECTION_BG = "#4a6a8a"
    SELECTION_FG = "#ffffff"
    ROW_EVEN_BG = "#353535"
    ROW_ODD_BG = "#2f2f2f"
    HOVER_BG = "#4f4f4f"
    BORDER_COLOR = "#5a5a5a"
    DISABLED_BG = "#3a3a3a"
    DISABLED_FG = "#777777"
    ERROR_BG = "#8b3a3a"
    WARNING_BG = "#b8860b"
    SUCCESS_BG = "#2e7d32"

# ==================== RELEASE NOTES ШАБЛОН ====================
RELEASE_NOTES_TEMPLATE = """Версия {version}

Новые возможности:
- Умные макросы с учётом пения и смены сетов
- Поддержка баффов, увеличивающих скорость каста
- Авторизация с привязкой к HWID
- Автоматическое обновление через Selectel

Исправления:
- Оптимизация использования памяти
- Улучшена стабильность программы"""