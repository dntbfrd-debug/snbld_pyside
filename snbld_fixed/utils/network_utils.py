# -*- coding: utf-8 -*-
"""
utils/network_utils.py
Сетевые утилиты для snbld resvap
"""

import os
import subprocess
import re
from typing import Optional, Dict, Any

import requests

from backend.logger_manager import get_logger

logger = get_logger('network')


# ==================== СКАЧИВАНИЕ ФАЙЛОВ ====================

def download_file(
    url: str,
    dest_path: str,
    timeout: int = 30,
    chunk_size: int = 8192,
    show_progress: bool = False
) -> bool:
    """
    Скачивает файл по URL.
    
    Args:
        url: URL для скачивания
        dest_path: Путь сохранения
        timeout: Таймаут в секундах
        chunk_size: Размер чанка для скачивания
        show_progress: Показывать прогресс
        
    Returns:
        True если скачивание успешно
    """
    try:
        response = requests.get(url, stream=True, timeout=timeout)
        response.raise_for_status()
        
        total_size = int(response.headers.get('content-length', 0))
        downloaded = 0
        
        with open(dest_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=chunk_size):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    
                    if show_progress and total_size > 0:
                        progress = (downloaded / total_size) * 100
                        logger.debug(f"Прогресс: {progress:.1f}%")
        
        logger.info(f"Файл скачан: {dest_path}")
        return True
        
    except requests.exceptions.Timeout:
        logger.error(f"Таймаут при скачивании {url}")
        return False
    except requests.exceptions.RequestException as e:
        logger.error(f"Ошибка скачивания файла {url}: {e}")
        return False
    except Exception as e:
        logger.error(f"Неизвестная ошибка при скачивании: {e}")
        return False


def download_update(download_url: str, target_path: str) -> bool:
    """
    Скачивает обновление.
    
    Args:
        download_url: URL обновления
        target_path: Путь сохранения
        
    Returns:
        True если скачивание успешно
    """
    return download_file(download_url, target_path, timeout=60, show_progress=True)


# ==================== ПРОВЕРКА ЦЕЛОСТНОСТИ ====================

def verify_file_checksum(file_path: str, expected_sha256: str) -> bool:
    """
    Проверяет SHA256 хеш файла.
    
    Args:
        file_path: Путь к файлу
        expected_sha256: Ожидаемый хеш
        
    Returns:
        True если хеши совпадают
    """
    import hashlib
    
    sha256 = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256.update(chunk)
        
        computed_hash = sha256.hexdigest().lower()
        expected_hash = expected_sha256.lower()
        
        if computed_hash == expected_hash:
            logger.info(f"Хеш файла совпадает: {file_path}")
            return True
        else:
            logger.warning(f"Хеш не совпадает для {file_path}")
            logger.warning(f"  Ожидался: {expected_hash}")
            logger.warning(f"  Получен:  {computed_hash}")
            return False
            
    except Exception as e:
        logger.error(f"Ошибка проверки хеша: {e}")
        return False


def get_file_sha256(file_path: str) -> Optional[str]:
    """
    Вычисляет SHA256 хеш файла.
    
    Args:
        file_path: Путь к файлу
        
    Returns:
        Хеш или None при ошибке
    """
    import hashlib
    
    sha256 = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256.update(chunk)
        return sha256.hexdigest()
    except Exception as e:
        logger.error(f"Ошибка вычисления хеша: {e}")
        return None


# ==================== ПРОВЕРКА ОБНОВЛЕНИЙ ====================

def get_latest_version_info(update_url: str, timeout: int = 10) -> Optional[Dict[str, Any]]:
    """
    Получает информацию о последней версии.
    
    Args:
        update_url: URL для проверки обновлений
        timeout: Таймаут запроса
        
    Returns:
        Информация о версии или None
    """
    try:
        response = requests.get(update_url, timeout=timeout)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.Timeout:
        logger.error("Таймаут при проверке обновлений")
        return None
    except requests.exceptions.RequestException as e:
        logger.error(f"Ошибка проверки обновлений: {e}")
        return None
    except json.JSONDecodeError as e:
        logger.error(f"Ошибка парсинга ответа: {e}")
        return None


def is_update_available(
    current_version: str,
    latest_version: str
) -> bool:
    """
    Проверяет, доступно ли обновление.
    
    Args:
        current_version: Текущая версия
        latest_version: Последняя версия
        
    Returns:
        True если доступно обновление
    """
    try:
        from packaging import version as version_parser
        return version_parser.parse(latest_version) > version_parser.parse(current_version)
    except ImportError:
        logger.warning("packaging не установлен, сравнение версий недоступно")
        return current_version != latest_version
    except Exception as e:
        logger.error(f"Ошибка сравнения версий: {e}")
        return False


# ==================== SSL СЕРТИФИКАТЫ ====================

def setup_ssl_cert() -> bool:
    """
    Настраивает SSL сертификат для requests.
    
    Returns:
        True если успешно
    """
    try:
        import certifi
        
        if getattr(sys, 'frozen', False):
            # В собранной версии
            src_cert = os.path.join(sys._MEIPASS, 'certifi', 'cacert.pem')
            appdata = os.environ.get('APPDATA', '')
            dest_base = os.path.join(appdata, 'snbld_resvap', 'certifi')
            dest_cert = os.path.join(dest_base, 'cacert.pem')
            
            if not os.path.exists(dest_cert):
                os.makedirs(dest_base, exist_ok=True)
                if os.path.exists(src_cert):
                    shutil.copy2(src_cert, dest_cert)
                    logger.info(f"Сертификат скопирован в {dest_cert}")
                else:
                    logger.warning("Файл сертификата не найден")
                    return False
            
            if os.path.exists(dest_cert):
                os.environ['REQUESTS_CA_BUNDLE'] = dest_cert
                os.environ['SSL_CERT_FILE'] = dest_cert
                logger.info(f"Установлен путь к сертификату: {dest_cert}")
                return True
        
        # Используем системный сертификат
        cert_path = certifi.where()
        os.environ['REQUESTS_CA_BUNDLE'] = cert_path
        os.environ['SSL_CERT_FILE'] = cert_path
        logger.info(f"Используется системный сертификат: {cert_path}")
        return True
        
    except Exception as e:
        logger.error(f"Ошибка настройки SSL сертификата: {e}")
        return False
