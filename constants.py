API_URL = "https://snbld.ru"

import os

SELECTEL_ACCESS_KEY = os.environ.get("SELECTEL_ACCESS_KEY", "")
SELECTEL_SECRET_KEY = os.environ.get("SELECTEL_SECRET_KEY", "")
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")

SELECTEL_BUCKET = "snbldfile"
SELECTEL_ENDPOINT = "https://s3.ru-3.storage.selcloud.ru"
SELECTEL_REGION = "ru-3"
UPDATE_BASE_URL = "https://snbld.ru"
PUBLIC_DOMAIN = "snbld.ru"

CURRENT_VERSION = "1.3.43"

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

DEFAULT_TITLE_BAR_OPACITY = 1
DEFAULT_PANEL_OPACITY = 1
DEFAULT_UI_SCALE = 1.0

DEFAULT_BG_IMAGE_MODE = "cover"
DEFAULT_BG_IMAGE_OPACITY = 1

DEFAULT_SKILL_ICON_SIZE = 36
DEFAULT_STATUS_ICON_SIZE = 36
DEFAULT_CELL_PADDING = 10
DEFAULT_ROW_HEIGHT = 100
DEFAULT_SHOW_MACRO_NAMES = True

DEFAULT_CASTBAR_THRESHOLD = 90
DEFAULT_TARGET_INTERVAL = 0.5
DEFAULT_OCR_SCALE = 10
DEFAULT_OCR_PSM = 10
DEFAULT_OCR_USE_MORPH = True

DEFAULT_PING_AUTO = True
DEFAULT_PING_CHECK_INTERVAL = 5
DEFAULT_PROCESS_NAME = "ElementClient_x64.exe"
DEFAULT_SERVER_IP = "147.45.96.78"

DEFAULT_MOB_AREA = (1084, 271, 1545, 358)
DEFAULT_PLAYER_AREA = (1271, 16, 1294, 32)

DEFAULT_COLOR_THRESHOLD = 30

MAIN_WINDOW_SIZE = "1300x750"
MIN_WINDOW_WIDTH = 1100
MIN_WINDOW_HEIGHT = 650

FONT_FAMILY = "Rubik"
FONT_SIZE_NORMAL = 10
FONT_SIZE_TITLE = 13

ICON_FILE = "123.ico"
LOGO_FILE = "logo.png"
SKILLS_JSON_FILE = "asgard_skills.json"
MACROS_JSON_FILE = "macros.json"
LOG_FILE = "debug.log"

ICONS_DIR = "icons"
SKILL_ICONS_DIR = "icons/skills"
PROFILES_DIR = "profiles"
CACHE_DIR = "cache"
TESSERACT_DIR = "tesseract"

ICON_FILES = [
    "add.png", "archer_icon.png", "buff.png", "calibrate.png",
    "cancel.png", "delete.png", "down.png", "edit.png",
    "keyboard.png", "load.png", "macros.png", "mage_icon.png",
    "mouse.png", "off.png", "ok.png", "on.png",
    "play.png", "save.png", "settings.png", "skill.png",
    "stop.png", "swap.png", "up.png"
]

DEFAULT_MACRO_STEPS = [
    ("key", "", 0),
    ("left", "", 0),
    ("wait", "", 100)
]

PING_CHECK_INTERVAL = 30
BUFF_CHECK_INTERVAL = 0.5
MOVEMENT_MONITOR_BASE_INTERVAL = 0.02
MOVEMENT_MONITOR_IDLE_INTERVAL = 0.05

PING_COMPENSATION_BASE_MS = 30
PING_COMPENSATION_FACTOR = 0.7
PING_COMPENSATION_BASE_S = 0.02
PING_COMPENSATION_MAX_S = 0.3
PING_GAME_MULTIPLIER = 2.0

DIALOG_TITLE = "snbld resvap"

ANIMATION_DURATION = 150
ANIMATION_OPACITY_START = 0
ANIMATION_OPACITY_END = 1

LOG_FORMAT = "%(asctime)s - %(levelname)s - %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
LOG_BACKUP_COUNT = 1
LOG_ROTATION_INTERVAL = 10

SSL_CERT_REQUIRED = True
SSL_VERIFY_TIMEOUT = 10

UPDATE_CHECK_ENABLED = True
UPDATE_DOWNLOAD_TIMEOUT = 30
UPDATE_CHUNK_SIZE = 8192

TELEGRAM_BOT_NAME = "snbld_bot"
TELEGRAM_WEBAPP_URL = "https://snbld.ru/webapp"
TELEGRAM_BIND_URL_TEMPLATE = f"https://t.me/{TELEGRAM_BOT_NAME}?start=bind_{{hwid}}"

VIRTUAL_KEYS = {
    'a': 0x41, 'b': 0x42, 'c': 0x43, 'd': 0x44, 'e': 0x45,
    'f': 0x46, 'g': 0x47, 'h': 0x48, 'i': 0x49, 'j': 0x4A,
    'k': 0x4B, 'l': 0x4C, 'm': 0x4D, 'n': 0x4E, 'o': 0x4F,
    'p': 0x50, 'q': 0x51, 'r': 0x52, 's': 0x53, 't': 0x54,
    'u': 0x55, 'v': 0x56, 'w': 0x57, 'x': 0x58, 'y': 0x59,
    'z': 0x5A,
    '0': 0x30, '1': 0x31, '2': 0x32, '3': 0x33, '4': 0x34,
    '5': 0x35, '6': 0x36, '7': 0x37, '8': 0x38, '9': 0x39,
    'space': 0x20, 'enter': 0x0D, 'esc': 0x1B, 'tab': 0x09,
    'shift': 0x10, 'ctrl': 0x11, 'alt': 0x12, 'caps': 0x14,
    'f1': 0x70, 'f2': 0x71, 'f3': 0x72, 'f4': 0x73, 'f5': 0x74,
    'f6': 0x75, 'f7': 0x76, 'f8': 0x77, 'f9': 0x78, 'f10': 0x79,
    'f11': 0x7A, 'f12': 0x7B,
    'up': 0x26, 'down': 0x28, 'left': 0x25, 'right': 0x27,
}

MACRO_TYPES = {
    "SIMPLE": "simple",
    "ZONE": "zone",
    "BUFF": "buff",
    "SKILL": "skill"
}

TARGET_TYPES = {
    "ENEMY": "enemy",
    "SELF": "self",
    "PARTY": "party",
    "AREA": "area"
}

OCR_PSM_MODES = {
    6: "Предположить единый блок текста",
    7: "Предположить одну строку текста",
    10: "Предположить одно символ",
    13: "Сырой текст. Найти как можно больше текста"
}

OCR_TARGET_INTERVAL = 0.2
OCR_DISTANCE_TOLERANCE = 1.0

ALLOWED_SETTINGS = {
    "swap_key_chant": (str, None, None),
    "swap_key_pa": (str, None, None),
    "base_channeling": (int, 0, 1000),
    "cooldown_margin": (float, 0.0, 5.0),
    "cast_lock_margin": (float, 0.0, 2.0),
    "cast_finish_delay": (float, 0.0, 2.0),
    "castbar_enabled": (bool, None, None),
    "castbar_point": (str, None, None),
    "castbar_threshold": (int, 1, 200),
    "castbar_color": (list, None, None),
    "castbar_size": (int, 1, 10),
    "movement_delay_enabled": (bool, None, None),
    "movement_delay_ms": (int, 0, 5000),
    "check_distance": (bool, None, None),
    "use_castbar_detection": (bool, None, None),
    "distance_tolerance": (float, 0.0, 10.0),
    "ocr_scale": (int, 1, 100),
    "ocr_psm": (int, 6, 13),
    "ocr_use_morph": (bool, None, None),
    "target_interval": (float, 0.1, 1.0),
    "process_name": (str, None, None),
    "server_ip": (str, None, None),
    "ping_auto": (bool, None, None),
    "ping_check_interval": (int, 1, 300),
    "average_ping": (int, 0, 1000),
    "global_step_delay": (int, 0, 500),
    "first_step_delay": (int, 0, 1000),
    "use_fixed_delays": (bool, None, None),
    "use_ping_delays": (bool, None, None),
    "start_all_hotkey": (str, None, None),
    "stop_all_hotkey": (str, None, None),
    "mob_area": ((str, list), None, None),
    "player_area": ((str, list), None, None),
    "window_opacity": (float, 0.1, 1.0),
    "window_locked": (bool, None, None),
    "target_window_title": (str, None, None),
    "buff_8004_click_point": (str, None, None),
    "accent_color": (str, None, None),
    "window_manager_skip_activation": (bool, None, None),
    "log_level_macros": (str, None, None),
    "log_level_errors": (str, None, None),
    "log_level_ocr": (str, None, None),
    "log_level_network": (str, None, None),
    "log_level_settings": (str, None, None),
    "log_level_debug": (str, None, None),
    "log_level_shiboken": (str, None, None),
}

class ColorScheme:
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

