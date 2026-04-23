# -*- coding: utf-8 -*-
"""
utils/resource_utils.py
Утилиты для работы с ресурсами (иконки, логотипы, фоны)
"""

import os
import sys
import shutil
import logging
from typing import List, Optional, Any
from pathlib import Path

from .file_utils import ensure_directory, get_cache_dir, resource_path, copy_file

logger = logging.getLogger(__name__)


# ==================== ЗАГРУЗКА РЕСУРСОВ ====================

def ensure_resource(filename: str, subdir: str = "", source_dir: Optional[str] = None) -> bool:
    """
    Проверяет наличие ресурса и копирует его при необходимости.
    
    Args:
        filename: Имя файла ресурса
        subdir: Подпапка (например, 'fonts', 'icons')
        source_dir: Исходная директория (по умолчанию - директория приложения)
        
    Returns:
        True если ресурс доступен
    """
    try:
        # Проверяем наличие в директории приложения
        res = resource_path(os.path.join(subdir, filename))
        if res and os.path.exists(res):
            logger.debug(f"Ресурс {filename} присутствует")
            return True
    except Exception:
        pass
    
    # Копируем в кэш
    cache_dir = get_cache_dir()
    if subdir:
        target_dir = os.path.join(cache_dir, subdir)
        ensure_directory(target_dir)
    else:
        target_dir = cache_dir
    
    dest_path = os.path.join(target_dir, filename)
    
    # Ищем источник
    if source_dir and os.path.exists(os.path.join(source_dir, filename)):
        src_path = os.path.join(source_dir, filename)
    else:
        src_path = resource_path(os.path.join(subdir, filename))
    
    if src_path and os.path.exists(src_path) and src_path != dest_path:
        try:
            shutil.copy2(src_path, dest_path)
            logger.debug(f"✅ Ресурс {filename} скопирован в кэш")
            return os.path.exists(dest_path)
        except Exception as e:
            logger.warning(f"⚠️ Не удалось скопировать ресурс {filename}: {e}")
    
    return os.path.exists(dest_path)


def ensure_icon(icon_file: str = "123.ico") -> bool:
    """Гарантирует наличие иконки приложения"""
    return ensure_resource(icon_file)


def ensure_logo(logo_file: str = "logo.png") -> bool:
    """Гарантирует наличие логотипа"""
    return ensure_resource(logo_file)


def ensure_all_resources() -> bool:
    """Гарантирует наличие всех основных ресурсов"""
    results = [
        ensure_icon(),
        ensure_logo(),
    ]
    return all(results)


# ==================== ИКОНКИ СКИЛЛОВ ====================

def ensure_skill_icons(skill_list: List[Any], icons_dir: Optional[str] = None) -> None:
    """
    Копирует иконки скиллов из ресурсов в кеш.
    
    Args:
        skill_list: Список скиллов с атрибутами id
        icons_dir: Директория с иконками (по умолчанию - icons/skills)
    """
    if icons_dir is None:
        icons_dir = os.path.join(get_cache_dir(), "icons", "skills")
    
    ensure_directory(icons_dir)
    
    for skill in skill_list:
        # Получаем ID скилла
        if hasattr(skill, 'id'):
            skill_id = skill.id
        elif isinstance(skill, dict):
            skill_id = skill.get("id")
        else:
            continue
        
        if not skill_id:
            continue
        
        local_path = os.path.join(icons_dir, f"{skill_id}.png")
        
        if not os.path.exists(local_path):
            src_path = resource_path(os.path.join("icons", "skills", f"{skill_id}.png"))
            
            if src_path and os.path.exists(src_path) and src_path != local_path:
                try:
                    shutil.copy2(src_path, local_path)
                    logger.debug(f"✅ Иконка {skill_id}.png скопирована в кэш")
                except Exception as e:
                    logger.warning(f"⚠️ Не удалось скопировать иконку {skill_id}.png: {e}")


def get_skill_icon_path(skill_id: int) -> str:
    """
    Возвращает путь к иконке скилла.
    
    Args:
        skill_id: ID скилла
        
    Returns:
        Путь к иконке или пустая строка
    """
    # Проверяем в кэше
    cache_path = os.path.join(get_cache_dir(), "icons", "skills", f"{skill_id}.png")
    if os.path.exists(cache_path):
        return cache_path
    
    # Проверяем в ресурсах
    res_path = resource_path(os.path.join("icons", "skills", f"{skill_id}.png"))
    if os.path.exists(res_path):
        return res_path
    
    return ""


def get_skill_icon_url(skill_id: int) -> str:
    """
    Возвращает file:// URL к иконке скилла.
    
    Args:
        skill_id: ID скилла
        
    Returns:
        file:// URL или пустая строка
    """
    path = get_skill_icon_path(skill_id)
    if path:
        # Преобразуем обратные слеши в прямые (для Windows)
        path = path.replace('\\', '/')
        return f"file:///{path}"
    return ""


# ==================== ТЕССЕРАКТ ====================

def ensure_tesseract() -> str:
    """
    Копирует Tesseract из временной папки PyInstaller.
    Также устанавливает TESSDATA_PREFIX для корректного поиска tessdata.
    
    Returns:
        Путь к tesseract.exe или пустая строка
    """
    import sys
    import shutil
    
    if getattr(sys, 'frozen', False):
        base_dir = os.path.dirname(sys.executable)
        dest = os.path.join(base_dir, 'tesseract')
        src = os.path.join(sys._MEIPASS, 'tesseract')
    else:
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        dest = os.path.join(base_dir, 'tesseract')
        src = dest
    
    if not os.path.exists(dest) and os.path.exists(src):
        try:
            shutil.copytree(src, dest)
            logger.info(f"Tesseract скопирован в {dest}")
        except Exception as e:
            logger.error(f"Ошибка копирования Tesseract: {e}")
            dest = src
    
    # Устанавливаем TESSDATA_PREFIX для корректного поиска tessdata
    tessdata_dir = os.path.join(dest, 'tessdata')
    if os.path.exists(tessdata_dir):
        os.environ['TESSDATA_PREFIX'] = tessdata_dir
        logger.info(f"TESSDATA_PREFIX установлен: {tessdata_dir}")
    else:
        logger.warning(f"tessdata не найден в {tessdata_dir}")
    
    tesseract_exe = os.path.join(dest, 'tesseract.exe')
    
    if os.path.exists(tesseract_exe):
        logger.info(f"Tesseract найден: {tesseract_exe}")
        return tesseract_exe
    
    # Проверяем системные пути
    possible_paths = [
        r'C:\Program Files\Tesseract-OCR\tesseract.exe',
        r'C:\Program Files (x86)\Tesseract-OCR\tesseract.exe'
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            logger.info(f"Tesseract найден (системный): {path}")
            # Также устанавливаем TESSDATA_PREFIX для системного tesseract
            tessdata_sys = os.path.join(os.path.dirname(path), 'tessdata')
            if os.path.exists(tessdata_sys):
                os.environ['TESSDATA_PREFIX'] = tessdata_sys
                logger.info(f"TESSDATA_PREFIX (системный) установлен: {tessdata_sys}")
            return path
    
    logger.error("Tesseract не найден!")
    return ""


def get_tesseract_path() -> str:
    """Возвращает путь к tesseract.exe"""
    return ensure_tesseract()
