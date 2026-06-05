import os
import sys
import logging
import winreg
from pathlib import Path

from backend.logger_manager import get_logger

logger = get_logger('file_utils')



def ensure_directory(directory: str) -> bool:
    try:
        Path(directory).mkdir(parents=True, exist_ok=True)
        return True
    except Exception as e:
        logger.error(f"╨Ю╤И╨╕╨▒╨║╨░ ╤Б╨╛╨╖╨┤╨░╨╜╨╕╤П ╨┤╨╕╤А╨╡╨║╤В╨╛╤А╨╕╨╕ {directory}: {e}", exc_info=True)
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



def resource_path(relative_path: str) -> str:
    import sys
    import os

    _logger = get_logger('debug')
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

    if hasattr(sys, "_MEIPASS"):
        path = os.path.join(sys._MEIPASS, relative_path)
        if os.path.exists(path):
            return path

    is_nuitka = (
        getattr(sys, 'frozen', False) or 
        hasattr(sys, 'compiled') or 
        sys.argv[0].endswith('.exe')
    )
    
    if is_nuitka:
        data_dir = get_data_dir()
        data_path = os.path.join(data_dir, relative_path)
        if os.path.exists(data_path):
            _logger.debug(f"  [Nuitka] FOUND in data dir: {data_path}")
            return data_path

        if hasattr(sys, 'compiled') and hasattr(sys.compiled, 'containing_dir'):
            internal_dir = sys.compiled.containing_dir
            internal_path = os.path.join(internal_dir, relative_path)
            _logger.debug(f"  [Nuitka] Check compiled dir: {internal_dir}")
            if os.path.exists(internal_path):
                _logger.debug(f"  [Nuitka] FOUND in compiled: {internal_path}")
                return internal_path
        
        exe_dir = os.path.dirname(sys.argv[0])
        snbld_data_path = os.path.join(exe_dir, ".snbld_data", relative_path)
        _logger.debug(f"  [Nuitka] Check .snbld_data: {snbld_data_path}")
        if os.path.exists(snbld_data_path):
            _logger.debug(f"  [Nuitka] FOUND in .snbld_data: {snbld_data_path}")
            return snbld_data_path
        
        dist_path = os.path.join(exe_dir, "qml_main.dist", relative_path)
        _logger.debug(f"  [Nuitka] Check qml_main.dist: {dist_path}")
        if os.path.exists(dist_path):
            _logger.debug(f"  [Nuitka] FOUND in qml_main.dist: {dist_path}")
            return dist_path
        
        local_path = os.path.join(exe_dir, relative_path)
        _logger.debug(f"  [Nuitka] Check argv[0] dir: {exe_dir}")
        if os.path.exists(local_path):
            _logger.debug(f"  [Nuitka] FOUND: {local_path}")
            return local_path
        
        exe_dir2 = os.path.dirname(sys.executable)
        local_path2 = os.path.join(exe_dir2, relative_path)
        _logger.debug(f"  [Nuitka] Check executable dir: {exe_dir2}")
        if os.path.exists(local_path2):
            _logger.debug(f"  [Nuitka] FOUND in executable dir: {local_path2}")
            return local_path2

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

    logger.warning(f"╨а╨╡╤Б╤Г╤А╤Б ╨╜╨╡ ╨╜╨░╨╣╨┤╨╡╨╜: {relative_path}")
    return ""


def resource_path_debug(relative_path: str) -> str:
    import sys

    print(f"[DEBUG resource_path] Request: {relative_path}")

    if hasattr(sys, "_MEIPASS"):
        path = os.path.join(sys._MEIPASS, relative_path)
        print(f"[DEBUG] _MEIPASS: {sys._MEIPASS}")
        if os.path.exists(path):
            print(f"[DEBUG] Found in _MEIPASS: {path}")
            return path
        else:
            print(f"[DEBUG] NOT in _MEIPASS: {path}")

    if getattr(sys, "frozen", False):
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





