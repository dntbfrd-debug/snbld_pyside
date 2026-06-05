from .file_utils import (
    ensure_directory,
    get_cache_dir,
    get_app_data_dir,
    resource_path,
    resource_path_debug,
)

from .resource_utils import (
    ensure_all_resources,
    ensure_skill_icons,
)



def is_admin() -> bool:
    import ctypes
    try:
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except Exception:
        return False


def run_as_admin() -> bool:
    import ctypes
    import sys
    try:
        
        print(f"[DEBUG] sys.frozen={getattr(sys, 'frozen', False)}")
        print(f"[DEBUG] sys.argv[0]={sys.argv[0]}")
        print(f"[DEBUG] sys.executable={sys.executable}")
        if hasattr(sys, '_MEIPASS'):
            print(f"[DEBUG] sys._MEIPASS={sys._MEIPASS}")
        if hasattr(sys, 'compiled'):
            print(f"[DEBUG] sys.compiled={sys.compiled}")
        
        exe = sys.argv[0]

        args = list(sys.argv)
        if '--admin-requested' not in args:
            args.append('--admin-requested')
        params = ' '.join(args[1:]) if len(args) > 1 else ''
        result = ctypes.windll.shell32.ShellExecuteW(
            None, "runas", exe, params, None, 0
        )
        return result > 32
    except Exception:
        return False


__all__ = [
    "ensure_directory",
    "get_cache_dir",
    "get_app_data_dir",
    "resource_path",
    "resource_path_debug",
    "ensure_all_resources",
    "ensure_skill_icons",
    "is_admin",
    "run_as_admin",
]
