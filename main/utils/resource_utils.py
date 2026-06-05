import os
import shutil
from typing import List, Optional, Any

from backend.logger_manager import get_logger
from .file_utils import ensure_directory, get_cache_dir, resource_path

logger = get_logger('resource_utils')



def ensure_resource(filename: str, subdir: str = "", source_dir: Optional[str] = None) -> bool:
    try:
        res = resource_path(os.path.join(subdir, filename))
        if res and os.path.exists(res):
            logger.debug(f"╨а╨╡╤Б╤Г╤А╤Б {filename} ╨┐╤А╨╕╤Б╤Г╤В╤Б╤В╨▓╤Г╨╡╤В")
            return True
    except Exception:
        pass
    
    cache_dir = get_cache_dir()
    if subdir:
        target_dir = os.path.join(cache_dir, subdir)
        ensure_directory(target_dir)
    else:
        target_dir = cache_dir
    
    dest_path = os.path.join(target_dir, filename)
    
    if source_dir and os.path.exists(os.path.join(source_dir, filename)):
        src_path = os.path.join(source_dir, filename)
    else:
        src_path = resource_path(os.path.join(subdir, filename))
    
    if src_path and os.path.exists(src_path) and src_path != dest_path:
        try:
            shutil.copy2(src_path, dest_path)
            logger.debug(f" ╨а╨╡╤Б╤Г╤А╤Б {filename} ╤Б╨║╨╛╨┐╨╕╤А╨╛╨▓╨░╨╜ ╨▓ ╨║╤Н╤И")
            return os.path.exists(dest_path)
        except Exception as e:
            logger.warning(f" ╨Э╨╡ ╤Г╨┤╨░╨╗╨╛╤Б╤М ╤Б╨║╨╛╨┐╨╕╤А╨╛╨▓╨░╤В╤М ╤А╨╡╤Б╤Г╤А╤Б {filename}: {e}", exc_info=True)
    
    return os.path.exists(dest_path)


def ensure_icon(icon_file: str = "123.ico") -> bool:
    return ensure_resource(icon_file)


def ensure_logo(logo_file: str = "logo.png") -> bool:
    return ensure_resource(logo_file)


def ensure_all_resources() -> bool:
    results = [
        ensure_icon(),
        ensure_logo(),
    ]
    return all(results)



def ensure_skill_icons(skill_list: List[Any], icons_dir: Optional[str] = None) -> None:
    if icons_dir is None:
        icons_dir = os.path.join(get_cache_dir(), "icons", "skills")
    
    ensure_directory(icons_dir)
    
    for skill in skill_list:
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
                    logger.debug(f" ╨Ш╨║╨╛╨╜╨║╨░ {skill_id}.png ╤Б╨║╨╛╨┐╨╕╤А╨╛╨▓╨░╨╜╨░ ╨▓ ╨║╤Н╤И")
                except Exception as e:
                    logger.warning(f" ╨Э╨╡ ╤Г╨┤╨░╨╗╨╛╤Б╤М ╤Б╨║╨╛╨┐╨╕╤А╨╛╨▓╨░╤В╤М ╨╕╨║╨╛╨╜╨║╤Г {skill_id}.png: {e}", exc_info=True)




