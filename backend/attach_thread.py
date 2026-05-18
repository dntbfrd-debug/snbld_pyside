from contextlib import contextmanager
from backend.win32_api import GetWindowThreadProcessId, GetCurrentThreadId, AttachThreadInput
from backend.logger_manager import get_logger


@contextmanager
def attached_thread_input(hwnd: int):
    """Пытается прикрепить ввод к потоку окна.
    
    Если AttachThreadInput не удался (UIPI на Windows 8+), не yield'ит — 
    вызывающий код должен использовать SendInput вместо PostMessage.
    Возвращает True в yield, если attach успешен, иначе False.
    """
    current = None
    target = None
    attached = False
    try:
        target = GetWindowThreadProcessId(hwnd)[0]
        current = GetCurrentThreadId()
        if current == target:
            yield True
            return
        attached = AttachThreadInput(current, target, True)
        if not attached:
            logger = get_logger('attach_thread')
            logger.warning(f"AttachThreadInput вернул 0 (UIPI? hwnd={hwnd}), PostMessage может не сработать")
            yield False
            return
        yield True
    except Exception as e:
        logger = get_logger('attach_thread')
        logger.warning(f"AttachThreadInput не удался (UIPI?): {e}")
        yield False
    finally:
        if current is not None and target is not None and current != target and attached:
            try:
                AttachThreadInput(current, target, False)
            except Exception:
                pass
