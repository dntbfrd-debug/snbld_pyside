import os
import sys
import winreg
from pathlib import Path


def ensure_directory(directory: str) -> bool:
    try:
        Path(directory).mkdir(parents=True, exist_ok=True)
        return True
    except Exception:
        return False


def get_cache_dir() -> Path:
    if getattr(sys, "frozen", False):
        cache_dir = Path(os.environ.get("APPDATA", ".")) / "snbld_resvap"
    else:
        cache_dir = Path(__file__).parent.parent / "cache"
    ensure_directory(str(cache_dir))
    return cache_dir


def get_app_data_dir() -> Path:
    appdata = Path(os.environ.get("APPDATA", "."))
    data_dir = appdata / "snbld_resvap"
    ensure_directory(str(data_dir))
    return data_dir


def get_install_dir() -> Path:
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\snbld_resvap")
        value, _ = winreg.QueryValueEx(key, "InstallPath")
        winreg.CloseKey(key)
        install_dir = Path(value)
        ensure_directory(str(install_dir))
        return install_dir
    except Exception:
        return get_app_data_dir()


def get_data_dir() -> str:
    if getattr(sys, "frozen", False):
        local_app_data = os.environ.get("LOCALAPPDATA", os.environ.get("APPDATA", "."))
        data_dir = os.path.join(local_app_data, "snbld_resvap", "data")
        if os.path.isdir(data_dir):
            return data_dir
        exe_dir = os.path.dirname(sys.executable)
        if os.path.isdir(os.path.join(exe_dir, "qml")):
            return exe_dir
        return os.path.dirname(sys.argv[0])
    else:
        return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
