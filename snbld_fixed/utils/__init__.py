# -*- coding: utf-8 -*-
"""
utils/
Пакет утилит для snbld resvap
Разделение на модули по назначению
"""

# Импортируем из новых модулей
from .file_utils import (
    ensure_directory,
    get_cache_dir,
    get_app_data_dir,
    cleanup_directory,
    load_json_file,
    save_json_file,
    resource_path,
    resource_path_debug,
    app_path,
    get_relative_path,
    copy_file,
    move_file,
    file_exists,
    directory_exists,
    get_file_size,
)

from .network_utils import (
    download_file,
    download_update,
    verify_file_checksum,
    get_file_sha256,
    get_latest_version_info,
    is_update_available,
    setup_ssl_cert,
)

from .resource_utils import (
    ensure_resource,
    ensure_icon,
    ensure_logo,
    ensure_all_resources,
    ensure_skill_icons,
    get_skill_icon_path,
    get_skill_icon_url,
    ensure_tesseract,
    get_tesseract_path,
)


# ==================== ADMIN UTILS ====================

def is_admin() -> bool:
    """Проверяет, запущена ли программа от имени администратора"""
    import ctypes
    try:
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except Exception:
        return False


def run_as_admin() -> bool:
    """Перезапускает программу от имени администратора"""
    import ctypes
    import sys
    try:
        # Nuitka onefile: используем sys.argv[0]
        # sys.frozen может быть False в Nuitka, но sys.argv[0] работает
        # sys.executable в onefile указывает в TEMP папку!
        
        # Debug
        print(f"[DEBUG] sys.frozen={getattr(sys, 'frozen', False)}")
        print(f"[DEBUG] sys.argv[0]={sys.argv[0]}")
        print(f"[DEBUG] sys.executable={sys.executable}")
        if hasattr(sys, '_MEIPASS'):
            print(f"[DEBUG] sys._MEIPASS={sys._MEIPASS}")
        if hasattr(sys, 'compiled'):
            print(f"[DEBUG] sys.compiled={sys.compiled}")
        
        exe = sys.argv[0]

        # Добавляем флаг --admin-requested чтобы избежать бесконечного цикла
        args = list(sys.argv)
        if '--admin-requested' not in args:
            args.append('--admin-requested')
        params = ' '.join(args[1:]) if len(args) > 1 else ''
        # 42 = SW_SHOWNORMAL
        result = ctypes.windll.shell32.ShellExecuteW(
            None, "runas", exe, params, None, 42
        )
        return result > 32  # >32 = успех
    except Exception:
        return False


__all__ = [
    # File utils
    "ensure_directory",
    "get_cache_dir",
    "get_app_data_dir",
    "cleanup_directory",
    "load_json_file",
    "save_json_file",
    "resource_path",
    "resource_path_debug",
    "app_path",
    "get_relative_path",
    "copy_file",
    "move_file",
    "file_exists",
    "directory_exists",
    "get_file_size",

    # Network utils
    "download_file",
    "download_update",
    "verify_file_checksum",
    "get_file_sha256",
    "get_latest_version_info",
    "is_update_available",
    "setup_ssl_cert",

    # Resource utils
    "ensure_resource",
    "ensure_icon",
    "ensure_logo",
    "ensure_all_resources",
    "ensure_skill_icons",
    "get_skill_icon_path",
    "get_skill_icon_url",
    "ensure_tesseract",
    "get_tesseract_path",

    # Admin utils
    "is_admin",
    "run_as_admin",
]
