API_URL = "https://snbld.ru"

import os

SELECTEL_ACCESS_KEY = os.environ.get("SELECTEL_ACCESS_KEY", "")
SELECTEL_SECRET_KEY = os.environ.get("SELECTEL_SECRET_KEY", "")
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")

CURRENT_VERSION = "1.3.56"

DEFAULT_CASTBAR_SWAP_DELAY = 10
DEFAULT_COOLDOWN_MARGIN = 0.45
DEFAULT_CAST_LOCK_MARGIN = 0.45
DEFAULT_CASTBAR_THRESHOLD = 90

DEFAULT_MOB_AREA = (1084, 271, 1545, 358)
DEFAULT_PLAYER_AREA = (1271, 16, 1294, 32)

MAIN_WINDOW_SIZE = "1300x750"
MIN_WINDOW_WIDTH = 1100
MIN_WINDOW_HEIGHT = 650

SKILLS_JSON_FILE = "asgard_skills.json"
MACROS_JSON_FILE = "macros.json"


MOVEMENT_MONITOR_BASE_INTERVAL = 0.02
MOVEMENT_MONITOR_IDLE_INTERVAL = 0.05





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
    '-': 0xBD, '=': 0xBB, ',': 0xBC, '.': 0xBE,
    '[': 0xDB, ']': 0xDD, '\\': 0xDC, ';': 0xBA, "'": 0xDE,
    '/': 0xBF, '`': 0xC0,
}

MOD_CONTROL = 0x0002
MOD_SHIFT = 0x0004
MOD_ALT = 0x0001
MOD_WIN = 0x0008


def parse_hotkey(hotkey_str: str):
    if not hotkey_str:
        return 0, 0
    parts = hotkey_str.lower().split('+')
    vk_name = parts[-1]
    vk = VIRTUAL_KEYS.get(vk_name)
    if vk is None and len(vk_name) == 1:
        vk = ord(vk_name.upper())
    if vk is None:
        vk = 0
    mods = 0
    for p in parts[:-1]:
        if p == 'ctrl':
            mods |= MOD_CONTROL
        elif p == 'alt':
            mods |= MOD_ALT
        elif p == 'shift':
            mods |= MOD_SHIFT
        elif p == 'win':
            mods |= MOD_WIN
    return vk, mods


OCR_TARGET_INTERVAL = 0.2

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
    "force_sendinput": (bool, None, None),
    "log_level_macros": (str, None, None),
    "log_level_errors": (str, None, None),
    "log_level_ocr": (str, None, None),
    "log_level_network": (str, None, None),
    "log_level_settings": (str, None, None),
    "log_level_debug": (str, None, None),
    "log_level_shiboken": (str, None, None),
}

# Калиброванные баффы: для них требуется клик по сохранённым координатам
# ПЕРЕД выполнением шагов. Ключ — buff_id, значение — настройка с координатами "x,y".
CALIBRATED_BUFF_CLICKS = {
    8004: "buff_8004_click_point",
}



