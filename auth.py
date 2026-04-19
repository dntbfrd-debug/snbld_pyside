# auth.py
# Новая система активации (БЕЗ HWID)
# Ключ активации + сессии

import requests
import urllib3
import json
import logging
import os
import sys
import hashlib
import ctypes
from pathlib import Path
from datetime import datetime, timedelta

# Отключаем предупреждения SSL (сертификат просрочен на сервере)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

API_URL = "https://snbld.ru"
CACHE_DIR = Path(os.environ.get('APPDATA', '.')) / "snbld_resvap"
CACHE_DIR.mkdir(parents=True, exist_ok=True)
SESSION_FILE = CACHE_DIR / "session.json"
KEY_FILE = CACHE_DIR / "activation_key.txt"

logger = logging.getLogger(__name__)


# ==================== DPAPI ШИФРОВАНИЕ ====================
import ctypes
import ctypes.wintypes as wintypes

class DATA_BLOB(ctypes.Structure):
    _fields_ = [("cbData", wintypes.DWORD),
                ("pbData", ctypes.POINTER(ctypes.c_char))]


def _encrypt_data(data: bytes) -> bytes:
    """Шифрует данные через Windows DPAPI (привязка к пользователю)"""
    try:
        CRYPTPROTECT_UI = 0x01

        blob_in = DATA_BLOB(len(data), ctypes.cast(
            ctypes.create_string_buffer(data),
            ctypes.POINTER(ctypes.c_char)
        ))
        blob_out = DATA_BLOB()

        result = ctypes.windll.crypt32.CryptProtectData(
            ctypes.byref(blob_in),
            None,
            None,
            None,
            None,
            CRYPTPROTECT_UI,
            ctypes.byref(blob_out)
        )

        if result:
            encrypted = ctypes.string_at(blob_out.pbData, blob_out.cbData)
            ctypes.windll.kernel32.LocalFree(blob_out.pbData)
            return encrypted
        else:
            raise ctypes.WinError()
    except Exception as e:
        logger.error(f"[AUTH] DPAPI шифрование не удалось: {e}")
        return data


def _decrypt_data(data: bytes) -> bytes:
    """Дешифрует данные через Windows DPAPI"""
    try:
        CRYPTPROTECT_UI = 0x01

        blob_in = DATA_BLOB(len(data), ctypes.cast(
            ctypes.create_string_buffer(data),
            ctypes.POINTER(ctypes.c_char)
        ))
        blob_out = DATA_BLOB()

        result = ctypes.windll.crypt32.CryptUnprotectData(
            ctypes.byref(blob_in),
            None,
            None,
            None,
            None,
            CRYPTPROTECT_UI,
            ctypes.byref(blob_out)
        )

        if result:
            decrypted = ctypes.string_at(blob_out.pbData, blob_out.cbData)
            ctypes.windll.kernel32.LocalFree(blob_out.pbData)
            return decrypted
        else:
            raise ctypes.WinError()
    except Exception as e:
        logger.error(f"[AUTH] DPAPI дешифрование не удалось: {e}")
        return data


def _save_encrypted(file_path: Path, data: dict):
    """Сохраняет JSON файл в зашифрованном виде"""
    json_bytes = json.dumps(data, ensure_ascii=False, indent=2).encode('utf-8')
    encrypted = _encrypt_data(json_bytes)
    with open(file_path, 'wb') as f:
        f.write(encrypted)


def _load_encrypted(file_path: Path) -> dict:
    """Загружает и дешифрует JSON файл"""
    with open(file_path, 'rb') as f:
        encrypted = f.read()
    decrypted = _decrypt_data(encrypted)
    return json.loads(decrypted.decode('utf-8'))


# ==================== ИЗВЛЕЧЕНИЕ КЛЮЧА ИЗ .EXE ====================

def extract_key_from_exe():
    """
    Извлекает ключ активации из собственного .exe файла.
    Ключ добавляется в конец файла при сборке на сервере.
    Формат: b'\n__KEY__:ABCD1234\n__END_KEY__\n'
    """
    try:
        # Путь к исполняемому файлу
        if getattr(sys, 'frozen', False):
            exe_path = sys.executable
        else:
            return None  # В режиме разработки ключа нет
        
        # Читаем последние 200 байт (там должен быть ключ)
        with open(exe_path, 'rb') as f:
            f.seek(-200, 2)  # Последние 200 байт
            content = f.read()
        
        # Ищем маркер с ключом
        start_marker = b'__KEY__:'
        end_marker = b'__END_KEY__'
        
        if start_marker in content and end_marker in content:
            start_idx = content.find(start_marker) + len(start_marker)
            end_idx = content.find(end_marker)
            key_bytes = content[start_idx:end_idx].strip()
            
            # Декодируем и очищаем
            key = key_bytes.decode('utf-8', errors='ignore').strip()
            
            # Проверяем что ключ похож на настоящий (16 символов, буквы+цифры)
            if len(key) == 16 and key.isalnum():
                logger.info(f"[AUTH] Ключ извлечён из .exe: {key[:4]}...{key[-4:]}")
                return key
            else:
                logger.warning(f"[AUTH] Неверный формат ключа: {repr(key)}")
        
    except Exception as e:
        logger.error(f"[AUTH] Ошибка извлечения ключа: {e}")
    
    return None


# ==================== СОХРАНЕНИЕ СЕССИИ ====================

def save_session(session_id, key=None, expires_at=None):
    """Сохраняет сессию в кэш (зашифровано через DPAPI)"""
    try:
        data = {
            'session_id': session_id,
            'key': key,
            'expires_at': expires_at,
            'created_at': datetime.utcnow().isoformat()
        }
        _save_encrypted(SESSION_FILE, data)
        logger.info(f"[AUTH] Сессия сохранена (зашифровано): {session_id[:8]}...")
        return True
    except Exception as e:
        logger.error(f"[AUTH] Ошибка сохранения сессии: {e}")
        return False


def load_session():
    """Загружает сессию из кэша (дешифрует через DPAPI)"""
    try:
        if SESSION_FILE.exists():
            data = _load_encrypted(SESSION_FILE)
            logger.info(f"[AUTH] Сессия загружена (дешифровано): {data.get('session_id', '')[:8]}...")
            return data
    except Exception as e:
        logger.error(f"[AUTH] Ошибка загрузки сессии: {e}")
    return None


def save_key_to_file(key):
    """Сохраняет ключ в файл (открытый текст)."""
    try:
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        file_path = CACHE_DIR / "activation_key.txt"
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(key.strip())
        # Проверка что файл действительно записался
        if file_path.exists() and file_path.stat().st_size > 0:
            logger.info(f"[AUTH] Ключ успешно сохранён: {key[:4]}...{key[-4:]}")
            return True
        else:
            logger.error("[AUTH] Ошибка: файл ключа пуст после записи!")
            return False
    except Exception as e:
        logger.error(f"[AUTH] КРИТИЧЕСКАЯ ОШИБКА сохранения ключа: {e}")
        return False


def load_key_from_file():
    """Загружает ключ из файла (сначала из папки с exe, потом из AppData)."""
    # Сначала проверяем файл activation.key рядом с exe
    try:
        import sys
        import os
        
        # Определяем папку с exe
        if hasattr(sys, '_MEIPASS'):
            exe_dir = os.path.dirname(sys.executable)
        elif getattr(sys, 'frozen', False):
            exe_dir = os.path.dirname(sys.executable)
        else:
            exe_dir = os.getcwd()
        
        # Проверяем activation.key рядом с exe
        exe_key_path = os.path.join(exe_dir, 'activation.key')
        logger.debug(f"[AUTH] Поиск ключа в: {exe_key_path}")
        if os.path.exists(exe_key_path):
            with open(exe_key_path, 'r', encoding='utf-8') as f:
                key = f.read().strip()
            if key and len(key) >= 10:
                logger.info(f"[AUTH] Ключ загружен из activation.key (рядом с exe): {key[:4]}...{key[-4:]}")
                return key
            else:
                logger.warning(f"[AUTH] Файл activation.key пуст или повреждён!")
    except Exception as e:
        logger.debug(f"[AUTH] Ошибка чтения activation.key: {e}")
    
    # Fallback: проверяем файл в AppData
    try:
        file_path = CACHE_DIR / "activation_key.txt"
        if file_path.exists():
            with open(file_path, 'r', encoding='utf-8') as f:
                key = f.read().strip()
            if key and len(key) >= 10:
                logger.info(f"[AUTH] Ключ загружен из файла: {key[:4]}...{key[-4:]}")
                return key
            else:
                logger.warning(f"[AUTH] Файл ключа повреждён или пуст! Размер: {len(key)}")
                return None
        else:
            logger.debug("[AUTH] Файл ключа не найден")
            return None
    except Exception as e:
        logger.error(f"[AUTH] Ошибка чтения ключа: {e}")
        return None


# ==================== API ЗАПРОСЫ ====================

def activate_key(key):
    """
    Активирует ключ на сервере с привязкой к HWID.
    Возвращает: (success: bool, data: dict)
    """
    try:
        # Получаем HWID для привязки
        from auth import get_hwid
        hwid = get_hwid()

        response = requests.post(
            f"{API_URL}/api/activate_key",
            json={'key': key, 'hwid': hwid},
            timeout=10,
            verify=True
        )
        data = response.json()

        if response.status_code == 200:
            # Сохраняем сессию
            if 'session_id' in data:
                save_session(
                    session_id=data['session_id'],
                    key=key,
                    expires_at=data.get('expires_at')
                )
            logger.info(f"[AUTH] Ключ активирован: {key[:4]}...{key[-4:]} (HWID: {hwid[:8]}...)")
            return True, data
        else:
            logger.error(f"[AUTH] Ошибка активации: {data.get('error', 'Unknown')}")
            return False, data

    except requests.exceptions.RequestException as e:
        logger.error(f"[AUTH] Ошибка соединения: {e}")
        return False, {'error': 'Нет соединения с сервером'}
    except Exception as e:
        logger.error(f"[AUTH] Неизвестная ошибка: {e}")
        return False, {'error': str(e)}


def check_key(key, hwid=None):
    """
    Проверяет ключ на сервере.
    Возвращает: (valid: bool, data: dict)
    """
    try:
        payload = {'key': key}
        if hwid:
            payload['hwid'] = hwid
        
        response = requests.post(
            f"{API_URL}/api/check_key",
            json=payload,
            timeout=10,
            verify=True
        )
        data = response.json()
        
        valid = data.get('valid', False)
        if valid:
            logger.info(f"[AUTH] Ключ действителен: {key[:4]}...{key[-4:]}")
        else:
            logger.warning(f"[AUTH] Ключ недействителен: {data.get('error', 'Unknown')}")
        
        return valid, data
        
    except requests.exceptions.RequestException as e:
        logger.error(f"[AUTH] Ошибка соединения: {e}")
        return False, {'error': 'Нет соединения с сервером'}
    except Exception as e:
        logger.error(f"[AUTH] Неизвестная ошибка: {e}")
        return False, {'error': str(e)}


def check_session(session_id):
    """
    Проверяет сессию (heartbeat).
    Возвращает: (valid: bool, data: dict)
    """
    try:
        response = requests.post(
            f"{API_URL}/api/check_session",
            json={'session_id': session_id},
            timeout=10,
            verify=True
        )
        data = response.json()
        
        valid = data.get('valid', False)
        if valid:
            logger.debug(f"[AUTH] Сессия активна: {session_id[:8]}...")
        else:
            logger.warning(f"[AUTH] Сессия неактивна: {data.get('error', 'Unknown')}")
        
        return valid, data
        
    except requests.exceptions.RequestException as e:
        logger.error(f"[AUTH] Ошибка соединения: {e}")
        return False, {'error': 'Нет соединения с сервером'}
    except Exception as e:
        logger.error(f"[AUTH] Неизвестная ошибка: {e}")
        return False, {'error': str(e)}


# ==================== HEARTBEAT (АВТОПРОВЕРКА) ====================

class HeartbeatManager:
    """Менеджер автоматической проверки сессии"""
    
    def __init__(self, check_interval=600):  # 10 минут
        self.check_interval = check_interval
        self.last_check = None
        self.session_id = None
    
    def start(self, session_id):
        """Запускает heartbeat"""
        self.session_id = session_id
        self.last_check = datetime.utcnow()
        logger.info(f"[HEARTBEAT] Запущен (интервал: {self.check_interval}с)")
    
    def should_check(self):
        """Проверяет, пора ли делать heartbeat"""
        if not self.session_id:
            return False
        if not self.last_check:
            return True
        return (datetime.utcnow() - self.last_check).total_seconds() >= self.check_interval
    
    def check(self):
        """Делает проверку сессии. Возвращает: (valid: bool, data: dict|None)"""
        if not self.session_id:
            return False, None

        valid, data = check_session(self.session_id)
        self.last_check = datetime.utcnow()

        if not valid:
            logger.warning(f"[HEARTBEAT] Сессия неактивна: {data.get('error', 'Unknown') if data else 'Нет данных'}")
            # НЕ очищаем сессию — пусть клиент сам решит что делать
        
        return valid, data
    
    def stop(self):
        """Останавливает heartbeat"""
        self.session_id = None
        self.last_check = None
        logger.info("[HEARTBEAT] Остановлен")


# ==================== УТИЛИТЫ ====================

def get_hwid():
    """
    Получает уникальный ID машины (для привязки ключа).
    Использует комбинацию CPU, motherboard и disk serial.
    """
    try:
        import hashlib
        import subprocess
        import platform

        parts = []

        # CPU Info
        try:
            cmd = 'wmic cpu get processorid'
            output = subprocess.check_output(cmd, shell=True, stderr=subprocess.DEVNULL).decode()
            for line in output.split('\n'):
                line = line.strip()
                if line and 'ProcessorId' not in line:
                    parts.append(line)
                    break
        except OSError:
            parts.append(platform.processor())

        # Motherboard Info
        try:
            cmd = 'wmic baseboard get serialnumber'
            output = subprocess.check_output(cmd, shell=True, stderr=subprocess.DEVNULL).decode()
            for line in output.split('\n'):
                line = line.strip()
                if line and 'SerialNumber' not in line:
                    parts.append(line)
                    break
        except OSError:
            parts.append("unknown_mb")

        # Disk Info
        try:
            cmd = 'wmic diskdrive where index=0 get serialnumber'
            output = subprocess.check_output(cmd, shell=True, stderr=subprocess.DEVNULL).decode()
            for line in output.split('\n'):
                line = line.strip()
                if line and 'SerialNumber' not in line:
                    parts.append(line)
                    break
        except OSError:
            parts.append("unknown_disk")

        # Создаём хэш из комбинации
        hwid_string = "-".join(parts)
        hwid_hash = hashlib.sha256(hwid_string.encode()).hexdigest()[:24].upper()

        # Форматируем как XXXX-XXXX-XXXX-XXXX-XXXX-XXXX
        return "-".join([hwid_hash[i:i+4] for i in range(0, 24, 4)])

    except Exception as e:
        logger.warning(f"[HWID] Ошибка получения HWID: {e}")
        return "UNKNOWN-HWID-0000"


def check_subscription_by_hwid(hwid=None):
    """
    Проверяет подписку по HWID.
    Возвращает: (activated: bool, data: dict)
    """
    if hwid is None:
        hwid = get_hwid()

    try:
        response = requests.post(
            f"{API_URL}/api/check_hwid",
            json={'hwid': hwid},
            timeout=10,
            verify=True
        )
        data = response.json()

        if response.status_code == 200:
            activated = data.get('activated', False)
            return activated, data
        else:
            return False, {'error': data.get('error', 'Unknown')}

    except requests.exceptions.RequestException as e:
        logger.error(f"[AUTH] Ошибка соединения: {e}")
        return False, {'error': 'Нет соединения с сервером'}
    except Exception as e:
        logger.error(f"[AUTH] Неизвестная ошибка: {e}")
        return False, {'error': str(e)}


# ==================== ПОЛУЧЕНИЕ ТОКЕНОВ С СЕРВЕРА ====================

def get_server_tokens(session_id: str = None, key: str = None):
    """
    Запрашивает токены с сервера.
    Используется в portable версии вместо .env файла.
    
    Args:
        session_id: ID сессии (если уже активирован)
        key: Ключ активации (если ещё не активирован)
    
    Returns:
        dict: {tokens: {TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, SELECTEL_ACCESS_KEY, SELECTEL_SECRET_KEY}, expires_in}
              или None при ошибке
    """
    try:
        payload = {}
        if session_id:
            payload['session_id'] = session_id
        elif key:
            payload['key'] = key
        else:
            logger.warning("[AUTH] Нет session_id или key для получения токенов")
            return None
        
        response = requests.post(
            f"{API_URL}/api/get_tokens",
            json=payload,
            timeout=15,
            verify=True
        )
        
        if response.status_code == 200:
            data = response.json()
            tokens = data.get('tokens', {})
            expires_in = data.get('expires_in', 3600)
            logger.info(f"[AUTH] Токены получены с сервера (expires_in={expires_in}с)")
            return {'tokens': tokens, 'expires_in': expires_in}
        else:
            logger.error(f"[AUTH] Ошибка получения токенов: {response.status_code}")
            return None
            
    except requests.exceptions.RequestException as e:
        logger.error(f"[AUTH] Ошибка соединения при получении токенов: {e}")
        return None
    except Exception as e:
        logger.error(f"[AUTH] Неизвестная ошибка при получении токенов: {e}")
        return None




