import requests
import json
import subprocess
import hashlib
import platform
import ctypes
import ctypes.wintypes as wintypes
import os
import sys
import time
from pathlib import Path
from datetime import datetime
from functools import lru_cache

from backend.logger_manager import get_logger

API_URL = "https://snbld.ru"
CACHE_DIR = Path(os.environ['APPDATA']) / "snbld_resvap"
CACHE_DIR.mkdir(parents=True, exist_ok=True)
SESSION_FILE = CACHE_DIR / "session.json"
KEY_FILE = CACHE_DIR / "activation_key.txt"

logger = get_logger('auth')
CREATE_NO_WINDOW = 0x08000000


def _get_verify_param() -> bool:
    return True

class DATA_BLOB(ctypes.Structure):
    _fields_ = [("cbData", wintypes.DWORD),
                ("pbData", ctypes.POINTER(ctypes.c_char))]


def _encrypt_data(data: bytes) -> bytes:
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
        logger.error(f"[AUTH] DPAPI шифрование не удалось: {e}", exc_info=True)
        raise RuntimeError("DPAPI шифрование недоступно") from e


def _decrypt_data(data: bytes) -> bytes:
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
        logger.error(f"[AUTH] DPAPI дешифрование не удалось: {e}", exc_info=True)
        raise RuntimeError("DPAPI дешифрование недоступно") from e


def _save_encrypted(file_path: Path, data: dict):
    json_bytes = json.dumps(data, ensure_ascii=False, indent=2).encode('utf-8')
    encrypted = _encrypt_data(json_bytes)
    tmp_path = file_path.with_suffix(file_path.suffix + ".tmp")
    with open(tmp_path, 'wb') as f:
        f.write(encrypted)
    tmp_path.replace(file_path)


def _load_encrypted(file_path: Path) -> dict:
    with open(file_path, 'rb') as f:
        encrypted = f.read()
    decrypted = _decrypt_data(encrypted)
    return json.loads(decrypted.decode('utf-8'))





def save_session(session_id, key=None, expires_at=None):
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
        logger.error(f"[AUTH] Ошибка сохранения сессии: {e}", exc_info=True)
        return False


def load_session():
    try:
        if SESSION_FILE.exists():
            data = _load_encrypted(SESSION_FILE)
            logger.info(f"[AUTH] Сессия загружена (дешифровано): {data.get('session_id', '')[:8]}...")
            return data
    except Exception as e:
        logger.error(f"[AUTH] Ошибка загрузки сессии: {e}", exc_info=True)
    return None


def save_key_to_file(key):
    try:
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        file_path = CACHE_DIR / "activation_key.enc"
        data = {'key': key.strip(), 'created_at': datetime.utcnow().isoformat()}
        _save_encrypted(file_path, data)
        if file_path.exists() and file_path.stat().st_size > 0:
            logger.info(f"[AUTH] Ключ успешно сохранён (DPAPI): {key[:4]}...{key[-4:]}")
            return True
        else:
            logger.error("[AUTH] Ошибка: файл ключа пуст после записи!", exc_info=True)
            return False
    except Exception as e:
        logger.error(f"[AUTH] КРИТИЧЕСКАЯ ОШИБКА сохранения ключа: {e}", exc_info=True)
        return False


def load_key_from_file():
    try:
        file_path = CACHE_DIR / "activation_key.enc"
        if file_path.exists():
            data = _load_encrypted(file_path)
            key = data.get('key', '').strip()
            if key and len(key) >= 10:
                logger.info(f"[AUTH] Ключ загружен (DPAPI): {key[:4]}...{key[-4:]}")
                return key
            else:
                logger.warning(f"[AUTH] Файл ключа повреждён!")
                return None
    except Exception as e:
        logger.error(f"[AUTH] Ошибка чтения зашифрованного ключа: {e}", exc_info=True)
    
    try:
        old_path = CACHE_DIR / "activation_key.txt"
        if old_path.exists():
            with open(old_path, 'r', encoding='utf-8') as f:
                key = f.read().strip()
            if key and len(key) >= 10:
                logger.info(f"[AUTH] Ключ загружен из старого файла (миграция): {key[:4]}...{key[-4:]}")
                save_key_to_file(key)
                old_path.unlink(missing_ok=True)
                return key
    except Exception as e:
        logger.debug(f"[AUTH] Ошибка чтения старого файла ключа: {e}")
    
    return None



def activate_key(key):
    try:
        hwid = get_hwid()

        response = requests.post(
            f"{API_URL}/api/activate_key",
            json={'key': key, 'hwid': hwid},
            timeout=10,
            verify=_get_verify_param()
        )
        data = response.json()

        if response.status_code == 200:
            if 'session_id' in data:
                save_session(
                    session_id=data['session_id'],
                    key=key,
                    expires_at=data.get('expires_at')
                )
            logger.info(f"[AUTH] Ключ активирован: {key[:4]}...{key[-4:]} (HWID: {hwid[:8]}...)")
            return True, data
        else:
            logger.error(f"[AUTH] Ошибка активации: {data.get('error', 'Unknown')}", exc_info=True)
            return False, data

    except requests.exceptions.RequestException as e:
        logger.error(f"[AUTH] Ошибка соединения: {e}", exc_info=True)
        return False, {'error': 'Нет соединения с сервером'}
    except Exception as e:
        logger.error(f"[AUTH] Неизвестная ошибка: {e}", exc_info=True)
        return False, {'error': str(e)}


def check_key(key, hwid=None):
    try:
        payload = {'key': key}
        if hwid:
            payload['hwid'] = hwid
        
        response = requests.post(
            f"{API_URL}/api/check_key",
            json=payload,
            timeout=10,
            verify=_get_verify_param()
        )
        data = response.json()
        
        valid = data.get('valid', False)
        if valid:
            logger.info(f"[AUTH] Ключ действителен: {key[:4]}...{key[-4:]}")
        else:
            logger.warning(f"[AUTH] Ключ недействителен: {data.get('error', 'Unknown')}")
        
        return valid, data
        
    except requests.exceptions.RequestException as e:
        logger.error(f"[AUTH] Ошибка соединения: {e}", exc_info=True)
        return False, {'error': 'Нет соединения с сервером'}
    except Exception as e:
        logger.error(f"[AUTH] Неизвестная ошибка: {e}", exc_info=True)
        return False, {'error': str(e)}


def check_session(session_id):
    max_retries = 3
    retry_delay = 2
    
    for attempt in range(max_retries):
        try:
            response = requests.post(
                f"{API_URL}/api/check_session",
                json={'session_id': session_id},
                timeout=10,
                verify=_get_verify_param()
            )
            
            if response.status_code == 204 or len(response.content.strip()) == 0:
                logger.warning(f"[AUTH] Сервер вернул пустой ответ (попытка {attempt+1}/{max_retries})")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay * (attempt + 1))
                    continue
                return True, {'warning': 'Сервер вернул пустой ответ, сессия временно сохранена'}
            
            content_type = response.headers.get('Content-Type', '')
            if 'application/json' not in content_type.lower():
                logger.warning(f"[AUTH] Сервер вернул не JSON ответ, Content-Type: {content_type} (попытка {attempt+1}/{max_retries})")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay * (attempt + 1))
                    continue
                return True, {'warning': 'Временная ошибка сервера, сессия сохранена'}
            
            try:
                data = response.json()
            except json.JSONDecodeError as e:
                logger.error(f"[AUTH] Ошибка парсинга ответа: {e} (попытка {attempt+1}/{max_retries})", exc_info=True)
                logger.debug(f"[AUTH] Ответ сервера: {repr(response.text[:200])}")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay * (attempt + 1))
                    continue
                return True, {'warning': 'Ошибка ответа сервера, сессия временно сохранена'}
            
            valid = data.get('valid', False)
            if valid:
                logger.debug(f"[AUTH] Сессия активна: {session_id[:8]}...")
            else:
                logger.warning(f"[AUTH] Сессия неактивна: {data.get('error', 'Unknown')}")
            
            return valid, data
            
        except requests.exceptions.RequestException as e:
            logger.error(f"[AUTH] Ошибка соединения: {e} (попытка {attempt+1}/{max_retries})", exc_info=True)
            if attempt < max_retries - 1:
                time.sleep(retry_delay * (attempt + 1))
                continue
            logger.warning(f"[AUTH] Все попытки соединения исчерпаны, но сессия остается активной")
            return True, {'warning': 'Нет соединения с сервером, сессия временно сохранена'}
    
    return True, {'warning': 'Временная недоступность сервера'}



class HeartbeatManager:
    
    def __init__(self, check_interval=600):
        self.check_interval = check_interval
        self.last_check = None
        self.session_id = None
    
    def start(self, session_id):
        self.session_id = session_id
        self.last_check = datetime.utcnow()
        logger.info(f"[HEARTBEAT] Запущен (интервал: {self.check_interval}с)")
    
    def should_check(self):
        if not self.session_id:
            return False
        if not self.last_check:
            return True
        return (datetime.utcnow() - self.last_check).total_seconds() >= self.check_interval
    
    def check(self):
        if not self.session_id:
            return False, None

        valid, data = check_session(self.session_id)
        self.last_check = datetime.utcnow()

        if not valid:
            logger.warning(f"[HEARTBEAT] Сессия неактивна: {data.get('error', 'Unknown') if data else 'Нет данных'}")
        
        return valid, data
    
    def stop(self):
        self.session_id = None
        self.last_check = None
        logger.info("[HEARTBEAT] Остановлен")



def _run_powershell(script):
    try:
        result = subprocess.run(
            ['powershell', '-NoProfile', '-NonInteractive', '-Command', script],
            capture_output=True, text=True,
            creationflags=CREATE_NO_WINDOW,
            timeout=5
        )
        out = result.stdout.strip()
        return out if out else None
    except (OSError, subprocess.SubprocessError):
        return None


@lru_cache(maxsize=1)
def get_hwid():
    try:
        parts = []

        cpu_id = _run_powershell(
            "(Get-CimInstance Win32_Processor).ProcessorId"
        )
        if not cpu_id:
            cpu_id = _run_powershell(
                "(Get-WmiObject Win32_Processor).ProcessorId"
            )
        parts.append(cpu_id or platform.processor())

        mb_serial = _run_powershell(
            "(Get-CimInstance Win32_BaseBoard).SerialNumber"
        )
        if not mb_serial:
            mb_serial = _run_powershell(
                "(Get-WmiObject Win32_BaseBoard).SerialNumber"
            )
        parts.append(mb_serial or "unknown_mb")

        disk_serial = _run_powershell(
            "(Get-CimInstance Win32_DiskDrive | Where-Object Index -eq 0).SerialNumber"
        )
        if not disk_serial:
            disk_serial = _run_powershell(
                "(Get-WmiObject Win32_DiskDrive | Where-Object Index -eq 0).SerialNumber"
            )
        parts.append(disk_serial or "unknown_disk")

        hwid_string = "-".join(parts)
        hwid_hash = hashlib.sha256(hwid_string.encode()).hexdigest()[:24].upper()

        return "-".join([hwid_hash[i:i+4] for i in range(0, 24, 4)])

    except Exception as e:
        logger.warning(f"[HWID] Ошибка получения HWID: {e}", exc_info=True)
        return "UNKNOWN-HWID-0000"


def check_subscription_by_hwid(hwid=None):
    if hwid is None:
        hwid = get_hwid()

    try:
        response = requests.post(
            f"{API_URL}/api/check_hwid",
            json={'hwid': hwid},
            timeout=10,
            verify=_get_verify_param()
        )
        data = response.json()

        if response.status_code == 200:
            activated = data.get('valid', False)
            return activated, data
        else:
            return False, {'error': data.get('error', 'Unknown')}

    except requests.exceptions.RequestException as e:
        logger.error(f"[AUTH] Ошибка соединения: {e}", exc_info=True)
        return False, {'error': 'Нет соединения с сервером'}
    except Exception as e:
        logger.error(f"[AUTH] Неизвестная ошибка: {e}", exc_info=True)
        return False, {'error': str(e)}



def get_server_tokens(session_id: str = None, key: str = None):
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
            verify=_get_verify_param()
        )
        
        if response.status_code == 200:
            data = response.json()
            tokens = data.get('tokens', {})
            expires_in = data.get('expires_in', 3600)
            logger.info(f"[AUTH] Токены получены с сервера (expires_in={expires_in}с)")
            return {'tokens': tokens, 'expires_in': expires_in}
        else:
            logger.error(f"[AUTH] Ошибка получения токенов: {response.status_code}", exc_info=True)
            return None
            
    except requests.exceptions.RequestException as e:
        logger.error(f"[AUTH] Ошибка соединения при получении токенов: {e}", exc_info=True)
        return None
    except Exception as e:
        logger.error(f"[AUTH] Неизвестная ошибка при получении токенов: {e}", exc_info=True)
        return None
