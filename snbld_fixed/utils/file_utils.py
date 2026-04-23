# -*- coding: utf-8 -*-
"""
utils/file_utils.py
Утилиты для работы с файлами и директориями
"""

import os
import sys
import json
import shutil
import logging
from pathlib import Path
from typing import Optional, Dict, Any, List

logger = logging.getLogger(__name__)


# ==================== СОЗДАНИЕ ДИРЕКТОРИЙ ====================

def ensure_directory(directory: str) -> bool:
    """Гарантирует существование директории."""
    try:
        Path(directory).mkdir(parents=True, exist_ok=True)
        return True
    except Exception as e:
        logger.error(f"Ошибка создания директории {directory}: {e}")
        return False


def get_cache_dir() -> Path:
    """Возвращает директорию кеша приложения"""
    if getattr(sys, "frozen", False):
        cache_dir = Path(os.environ.get("APPDATA", ".")) / "snbld_resvap"
    else:
        cache_dir = Path(__file__).parent.parent / "cache"
    ensure_directory(str(cache_dir))
    return cache_dir


def get_app_data_dir() -> Path:
    """Возвращает директорию данных приложения в APPDATA"""
    appdata = Path(os.environ.get("APPDATA", "."))
    data_dir = appdata / "snbld_resvap"
    ensure_directory(str(data_dir))
    return data_dir


def cleanup_directory(directory: str, keep_extensions: Optional[List[str]] = None) -> int:
    """Очищает директорию от файлов."""
    removed_count = 0
    try:
        dir_path = Path(directory)
        if not dir_path.exists():
            return 0

        for item in dir_path.iterdir():
            if item.is_file():
                if keep_extensions is None or item.suffix not in keep_extensions:
                    item.unlink()
                    removed_count += 1
                    logger.debug(f"Удалён файл: {item}")
            elif item.is_dir():
                shutil.rmtree(item)
                removed_count += 1
                logger.debug(f"Удалена папка: {item}")

    except Exception as e:
        logger.error(f"Ошибка очистки директории {directory}: {e}")

    return removed_count


# ==================== РАБОТА С JSON ====================

def load_json_file(file_path: str, default: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
    """Загружает JSON файл."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        logger.debug(f"Файл не найден: {file_path}")
        return default
    except json.JSONDecodeError as e:
        logger.error(f"Ошибка парсинга JSON {file_path}: {e}")
        return default
    except Exception as e:
        logger.error(f"Ошибка загрузки JSON {file_path}: {e}")
        return default


def save_json_file(
    file_path: str,
    data: Dict[str, Any],
    indent: int = 2,
    ensure_ascii: bool = False,
    create_backup: bool = True
) -> bool:
    """Сохраняет данные в JSON файл."""
    try:
        path = Path(file_path)

        if create_backup and path.exists():
            backup_path = path.with_suffix('.json.bak')
            shutil.copy2(path, backup_path)
            logger.debug(f"Создана резервная копия: {backup_path}")

        ensure_directory(str(path.parent))

        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=indent, ensure_ascii=ensure_ascii, default=str)

        logger.debug(f"Данные сохранены в {file_path}")
        return True

    except Exception as e:
        logger.error(f"Ошибка сохранения JSON {file_path}: {e}")
        return False


# ==================== ПУТИ И РЕСУРСЫ ====================

def resource_path(relative_path: str) -> str:
    """Возвращает абсолютный путь к ресурсу."""
    import sys
    import os

    # DEBUG: логирование для диагностики
    _logger = logging.getLogger('debug')
    _logger.debug(f"[resource_path] Request: {relative_path}")
    _logger.debug(f"  sys.frozen: {getattr(sys, 'frozen', False)}")
    _logger.debug(f"  sys.argv[0]: {sys.argv[0]}")
    _logger.debug(f"  sys.executable: {sys.executable}")
    _logger.debug(f"  hasattr(sys, '_MEIPASS'): {hasattr(sys, '_MEIPASS')}")
    _logger.debug(f"  hasattr(sys, 'compiled'): {hasattr(sys, 'compiled')}")
    if hasattr(sys, 'compiled'):
        _logger.debug(f"  sys.compiled: {sys.compiled}")
        if hasattr(sys.compiled, 'containing_dir'):
            _logger.debug(f"  sys.compiled.containing_dir: {sys.compiled.containing_dir}")

    # PyInstaller
    if hasattr(sys, "_MEIPASS"):
        path = os.path.join(sys._MEIPASS, relative_path)
        if os.path.exists(path):
            return path

    # Nuitka onefile detection
    is_nuitka = (
        getattr(sys, 'frozen', False) or 
        hasattr(sys, 'compiled') or 
        sys.argv[0].endswith('.exe')
    )
    
    if is_nuitka:
        # Приоритет 1: sys.compiled.containing_dir (распакованные файлы Nuitka)
        if hasattr(sys, 'compiled') and hasattr(sys.compiled, 'containing_dir'):
            internal_dir = sys.compiled.containing_dir
            internal_path = os.path.join(internal_dir, relative_path)
            _logger.debug(f"  [Nuitka] Check compiled dir: {internal_dir}")
            if os.path.exists(internal_path):
                _logger.debug(f"  [Nuitka] FOUND in compiled: {internal_path}")
                return internal_path
        
        # Приоритет 2: .snbld_data папка (кастомный tempdir)
        exe_dir = os.path.dirname(sys.argv[0])
        snbld_data_path = os.path.join(exe_dir, ".snbld_data", relative_path)
        _logger.debug(f"  [Nuitka] Check .snbld_data: {snbld_data_path}")
        if os.path.exists(snbld_data_path):
            _logger.debug(f"  [Nuitka] FOUND in .snbld_data: {snbld_data_path}")
            return snbld_data_path
        
        # Приоритет 3: qml_main.dist (стандартная папка распаковки onefile)
        dist_path = os.path.join(exe_dir, "qml_main.dist", relative_path)
        _logger.debug(f"  [Nuitka] Check qml_main.dist: {dist_path}")
        if os.path.exists(dist_path):
            _logger.debug(f"  [Nuitka] FOUND in qml_main.dist: {dist_path}")
            return dist_path
        
        # Приоритет 4: sys.argv[0] директория (файлы рядом с exe)
        local_path = os.path.join(exe_dir, relative_path)
        _logger.debug(f"  [Nuitka] Check argv[0] dir: {exe_dir}")
        if os.path.exists(local_path):
            _logger.debug(f"  [Nuitka] FOUND: {local_path}")
            return local_path
        
        # Приоритет 5: sys.executable директория
        exe_dir2 = os.path.dirname(sys.executable)
        local_path2 = os.path.join(exe_dir2, relative_path)
        _logger.debug(f"  [Nuitka] Check executable dir: {exe_dir2}")
        if os.path.exists(local_path2):
            _logger.debug(f"  [Nuitka] FOUND in executable dir: {local_path2}")
            return local_path2

    # Режим разработки - ищем в папке проекта
    cache_dir = get_cache_dir()
    cached_path = os.path.join(cache_dir, relative_path)
    if os.path.exists(cached_path):
        return cached_path

    script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    script_path = os.path.join(script_dir, relative_path)
    _logger.debug(f"  [Dev mode] script_dir: {script_dir}")
    if os.path.exists(script_path):
        _logger.debug(f"  [Dev mode] FOUND: {script_path}")
        return script_path

    logger.warning(f"Ресурс не найден: {relative_path}")
    return ""


def resource_path_debug(relative_path: str) -> str:
    """DEBUG: Возвращает абсолютный путь к ресурсу с отладкой."""
    import sys

    print(f"[DEBUG resource_path] Request: {relative_path}")

    # Nuitka onefile
    if hasattr(sys, "_MEIPASS"):
        path = os.path.join(sys._MEIPASS, relative_path)
        print(f"[DEBUG] _MEIPASS: {sys._MEIPASS}")
        if os.path.exists(path):
            print(f"[DEBUG] Found in _MEIPASS: {path}")
            return path
        else:
            print(f"[DEBUG] NOT in _MEIPASS: {path}")

    if getattr(sys, "frozen", False):
        # Nuitka onefile: используем sys.argv[0] для реального exe
        exe_dir = os.path.dirname(sys.argv[0])
        print(f"[DEBUG] frozen=True, exe_dir: {exe_dir}")

        local_path = os.path.join(exe_dir, relative_path)
        if os.path.exists(local_path):
            print(f"[DEBUG] Found local: {local_path}")
            return local_path
        else:
            print(f"[DEBUG] NOT local: {local_path}")

        internal_path = os.path.join(exe_dir, "_internal", relative_path)
        if os.path.exists(internal_path):
            print(f"[DEBUG] Found _internal: {internal_path}")
            return internal_path

    script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    script_path = os.path.join(script_dir, relative_path)
    if os.path.exists(script_path):
        print(f"[DEBUG] Found script: {script_path}")
        return script_path

    print(f"[DEBUG] NOT FOUND: {relative_path}")
    return ""


def app_path(relative_path: str) -> str:
    """Возвращает абсолютный путь относительно папки приложения."""
    if getattr(sys, "frozen", False):
        # Nuitka onefile: используем sys.argv[0] для реального exe
        base_path = os.path.dirname(sys.argv[0])
    else:
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)


def get_relative_path(full_path: str, base_path: Optional[str] = None) -> str:
    """Возвращает относительный путь от базовой."""
    if base_path is None:
        if getattr(sys, "frozen", False):
            base_path = os.path.dirname(sys.argv[0])
    else:
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)


def get_relative_path(full_path: str, base_path: Optional[str] = None) -> str:
    """Возвращает относительный путь от базового."""
    if base_path is None:
        if getattr(sys, "frozen", False):
            base_path = os.path.dirname(sys.executable)
        else:
            base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    try:
        return os.path.relpath(full_path, base_path)
    except ValueError:
        return full_path


# ==================== КОПИРОВАНИЕ И ПЕРЕМЕЩЕНИЕ ====================

def copy_file(src: str, dst: str, create_dirs: bool = True) -> bool:
    """Копирует файл."""
    try:
        if create_dirs:
            ensure_directory(os.path.dirname(dst))
        shutil.copy2(src, dst)
        logger.debug(f"Файл скопирован: {src} → {dst}")
        return True
    except Exception as e:
        logger.error(f"Ошибка копирования файла: {e}")
        return False


def move_file(src: str, dst: str, create_dirs: bool = True) -> bool:
    """Перемещает файл."""
    try:
        if create_dirs:
            ensure_directory(os.path.dirname(dst))
        shutil.move(src, dst)
        logger.debug(f"Файл перемещён: {src} → {dst}")
        return True
    except Exception as e:
        logger.error(f"Ошибка перемещения файла: {e}")
        return False


# ==================== ПРОВЕРКА ФАЙЛОВ ====================

def file_exists(file_path: str) -> bool:
    """Проверяет существование файла"""
    return os.path.isfile(file_path)


def directory_exists(dir_path: str) -> bool:
    """Проверяет существование директории"""
    return os.path.isdir(dir_path)


def get_file_size(file_path: str) -> int:
    """Возвращает размер файла в байтах"""
    try:
        return os.path.getsize(file_path)
    except Exception:
        return 0
