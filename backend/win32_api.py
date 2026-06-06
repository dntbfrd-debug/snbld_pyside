# backend/win32_api.py — Pure ctypes wrapper for Win32 API
import ctypes
from ctypes import wintypes, Structure, POINTER, byref
from typing import Optional, List, Tuple


_user32 = ctypes.windll.user32
_kernel32 = ctypes.windll.kernel32
_gdi32 = ctypes.windll.gdi32

_user32.SetWindowsHookExW.restype = ctypes.c_void_p
_user32.SetWindowsHookExW.argtypes = [
    wintypes.INT, ctypes.c_void_p, ctypes.c_void_p, wintypes.DWORD
]
_kernel32.GetModuleHandleW.restype = ctypes.c_void_p
_kernel32.GetModuleHandleW.argtypes = [wintypes.LPCWSTR]


class POINT(Structure):
    _fields_ = [("x", wintypes.LONG), ("y", wintypes.LONG)]

class RECT(Structure):
    _fields_ = [("left", wintypes.LONG), ("top", wintypes.LONG),
                ("right", wintypes.LONG), ("bottom", wintypes.LONG)]

class MONITORINFO(Structure):
    _fields_ = [
        ("cbSize", wintypes.DWORD),
        ("rcMonitor", RECT),
        ("rcWork", RECT),
        ("dwFlags", wintypes.DWORD),
    ]

class PROCESSENTRY32W(Structure):
    _fields_ = [
        ("dwSize", wintypes.DWORD),
        ("cntUsage", wintypes.DWORD),
        ("th32ProcessID", wintypes.DWORD),
        ("th32DefaultHeapID", ctypes.c_void_p),
        ("th32ModuleID", wintypes.DWORD),
        ("cntThreads", wintypes.DWORD),
        ("th32ParentProcessID", wintypes.DWORD),
        ("pcPriClassBase", wintypes.LONG),
        ("dwFlags", wintypes.DWORD),
        ("szExeFile", ctypes.c_wchar * 260),
    ]

class MIB_TCPROW2(Structure):
    _fields_ = [
        ("dwState", wintypes.DWORD),
        ("dwLocalAddr", wintypes.DWORD),
        ("dwLocalPort", wintypes.DWORD),
        ("dwRemoteAddr", wintypes.DWORD),
        ("dwRemotePort", wintypes.DWORD),
        ("dwOwningPid", wintypes.DWORD),
        ("dwOffloadState", wintypes.DWORD),
    ]

HWND_TOP = 0
HWND_BOTTOM = 1
HWND_TOPMOST = -1
HWND_NOTOPMOST = -2
HWND_MESSAGE = -3

SW_HIDE = 0
SW_SHOWNORMAL = 1
SW_SHOWMINIMIZED = 2
SW_SHOWMAXIMIZED = 3
SW_SHOWNOACTIVATE = 4
SW_SHOW = 5
SW_RESTORE = 9
SW_SHOWDEFAULT = 10

SWP_NOMOVE = 0x0002
SWP_NOSIZE = 0x0001
SWP_SHOWWINDOW = 0x0040
SWP_NOACTIVATE = 0x0010

WM_KEYDOWN = 0x0100
WM_KEYUP = 0x0101
WM_SYSKEYDOWN = 0x0104
WM_SYSKEYUP = 0x0105
WM_LBUTTONDOWN = 0x0201
WM_LBUTTONUP = 0x0202
WM_RBUTTONDOWN = 0x0204
WM_RBUTTONUP = 0x0205
WM_MOUSEMOVE = 0x0200


MK_LBUTTON = 0x0001
MK_RBUTTON = 0x0002
MK_CONTROL = 0x0008

MONITOR_DEFAULTTONULL = 0
MONITOR_DEFAULTTOPRIMARY = 1
MONITOR_DEFAULTTONEAREST = 2
MONITORINFOF_PRIMARY = 1

CLR_INVALID = 0xFFFFFFFF

TH32CS_SNAPPROCESS = 0x00000002
TH32CS_SNAPTHREAD = 0x00000004

PROCESS_QUERY_INFORMATION = 0x0400
PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
PROCESS_VM_READ = 0x0010
STILL_ACTIVE = 259

MIB_TCP_STATE_ESTAB = 5

ERROR_ALREADY_EXISTS = 183

WNDENUMPROC = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
MONITORENUMPROC = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HMONITOR, wintypes.HDC, POINTER(RECT), wintypes.LPARAM)

def GetForegroundWindow():
    return _user32.GetForegroundWindow()

def GetWindowText(hwnd):
    length = _user32.GetWindowTextLengthW(hwnd) + 1
    buf = ctypes.create_unicode_buffer(length)
    _user32.GetWindowTextW(hwnd, buf, length)
    return buf.value

SMTO_ABORTIFHUNG = 0x0002
WM_GETTEXT = 0x000D

def GetWindowTextTimeout(hwnd, timeout_ms=500):
    length = _user32.GetWindowTextLengthW(hwnd) + 1
    if length <= 1:
        return ""
    buf = ctypes.create_unicode_buffer(length)
    result = _user32.SendMessageTimeoutW(hwnd, WM_GETTEXT, length, buf, SMTO_ABORTIFHUNG, timeout_ms, None)
    if result:
        return buf.value
    return ""

def IsWindowVisible(hwnd):
    return bool(_user32.IsWindowVisible(hwnd))

def ShowWindow(hwnd, cmd_show):
    return _user32.ShowWindow(hwnd, cmd_show)

def SetForegroundWindow(hwnd):
    return _user32.SetForegroundWindow(hwnd)

def SetWindowPos(hwnd, hwnd_after, x, y, w, h, flags):
    return _user32.SetWindowPos(hwnd, hwnd_after, x, y, w, h, flags)

def EnumWindows(callback, lParam=0):
    def _wrapper(hwnd, lparam):
        ret = callback(hwnd, lparam)
        return True if ret is None else ret
    cb = WNDENUMPROC(_wrapper)
    _user32.EnumWindows(cb, lParam)

def GetCursorPos() -> Tuple[int, int]:
    pt = POINT()
    _user32.GetCursorPos(byref(pt))
    return (pt.x, pt.y)

def ScreenToClient(hwnd, pos: Tuple[int, int]) -> Tuple[int, int]:
    pt = POINT(pos[0], pos[1])
    _user32.ScreenToClient(hwnd, byref(pt))
    return (pt.x, pt.y)

def PostMessage(hwnd, msg, wparam, lparam):
    return _user32.PostMessageW(hwnd, msg, wparam, lparam)

def MapVirtualKey(vk, format):
    return _user32.MapVirtualKeyW(vk, format)

def GetDC(hwnd):
    return _user32.GetDC(hwnd)

def GetWindowDC(hwnd):
    return _user32.GetWindowDC(hwnd)

def ReleaseDC(hwnd, hdc):
    return _user32.ReleaseDC(hwnd, hdc)

def GetPixel(hdc, x, y):
    return _gdi32.GetPixel(hdc, x, y)

def GetDeviceCaps(hdc, index):
    return _gdi32.GetDeviceCaps(hdc, index)

def GetWindowThreadProcessId(hwnd) -> Tuple[int, int]:
    pid = wintypes.DWORD()
    tid = _user32.GetWindowThreadProcessId(hwnd, byref(pid))
    return (tid, pid.value)

def AttachThreadInput(id_attach, id_attach_to, attach):
    return _user32.AttachThreadInput(id_attach, id_attach_to, attach)

def GetCurrentThreadId():
    return _kernel32.GetCurrentThreadId()

def GetLastError():
    return _kernel32.GetLastError()

def CreateMutex(name):
    return _kernel32.CreateMutexW(None, True, name)

def ReleaseMutex(handle):
    return _kernel32.ReleaseMutex(handle)

def MessageBox(owner, text, title, style):
    return _user32.MessageBoxW(owner, text, title, style)

def MonitorFromWindow(hwnd, flags):
    return _user32.MonitorFromWindow(hwnd, flags)

def GetMonitorInfo(hmonitor) -> dict:
    mi = MONITORINFO()
    mi.cbSize = ctypes.sizeof(MONITORINFO)
    if _user32.GetMonitorInfoW(hmonitor, byref(mi)):
        return {
            'Monitor': (mi.rcMonitor.left, mi.rcMonitor.top,
                       mi.rcMonitor.right, mi.rcMonitor.bottom),
            'Work': (mi.rcWork.left, mi.rcWork.top,
                    mi.rcWork.right, mi.rcWork.bottom),
            'Flags': mi.dwFlags,
        }
    return {}

def EnumDisplayMonitors() -> int:
    count = [0]
    def callback(hmonitor, hdc, rect, lparam):
        count[0] += 1
        return True
    cb = MONITORENUMPROC(callback)
    _user32.EnumDisplayMonitors(None, None, cb, 0)
    return count[0]

def process_exists(pid) -> bool:
    handle = _kernel32.OpenProcess(PROCESS_QUERY_INFORMATION, False, pid)
    if not handle:
        return False
    try:
        exit_code = wintypes.DWORD()
        if _kernel32.GetExitCodeProcess(handle, byref(exit_code)):
            return exit_code.value == STILL_ACTIVE
        return False
    finally:
        _kernel32.CloseHandle(handle)

def find_processes_by_name(name: str) -> List[Tuple[int, str]]:
    results = []
    snapshot = _kernel32.CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS, 0)
    if snapshot == -1:
        return results
    try:
        pe = PROCESSENTRY32W()
        pe.dwSize = ctypes.sizeof(PROCESSENTRY32W)
        if _kernel32.Process32FirstW(snapshot, byref(pe)):
            while True:
                if name.lower() in pe.szExeFile.lower():
                    results.append((pe.th32ProcessID, pe.szExeFile))
                if not _kernel32.Process32NextW(snapshot, byref(pe)):
                    break
        return results
    finally:
        _kernel32.CloseHandle(snapshot)

def get_process_name(pid) -> Optional[str]:
    handle = _kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid)
    if not handle:
        return None
    try:
        buf = ctypes.create_unicode_buffer(260)
        size = wintypes.DWORD(260)
        if _kernel32.QueryFullProcessImageNameW(handle, 0, buf, ctypes.byref(size)):
            import os
            return os.path.basename(buf.value)
        return None
    finally:
        _kernel32.CloseHandle(handle)

def get_process_tcp_connections(pid) -> List[dict]:
    results = []
    try:
        iphlpapi = ctypes.windll.iphlpapi
        GetExtendedTcpTable = iphlpapi.GetExtendedTcpTable
        GetExtendedTcpTable.restype = wintypes.DWORD
        buf_size = wintypes.DWORD(0)
        GetExtendedTcpTable(None, byref(buf_size), False, 2, 2, 0)
        buf = ctypes.create_string_buffer(buf_size.value)
        if GetExtendedTcpTable(buf, byref(buf_size), False, 2, 2, 0) != 0:
            return results
        row_count = ctypes.cast(buf, POINTER(wintypes.DWORD))[0]
        rows_ptr = ctypes.cast(
            ctypes.byref(buf, ctypes.sizeof(wintypes.DWORD)),
            POINTER(MIB_TCPROW2)
        )
        for i in range(row_count):
            row = rows_ptr[i]
            if row.dwOwningPid == pid:
                import socket
                def ip_to_str(ip):
                    return f"{(ip >> 0) & 0xFF}.{(ip >> 8) & 0xFF}.{(ip >> 16) & 0xFF}.{(ip >> 24) & 0xFF}"
                state = 'ESTABLISHED' if row.dwState == MIB_TCP_STATE_ESTAB else str(row.dwState)
                results.append({
                    'status': state,
                    'laddr': (ip_to_str(row.dwLocalAddr), socket.ntohs(row.dwLocalPort)),
                    'raddr': (ip_to_str(row.dwRemoteAddr), socket.ntohs(row.dwRemotePort)),
                })
        return results
    except Exception:
        return []


