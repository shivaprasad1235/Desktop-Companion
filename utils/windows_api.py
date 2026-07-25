import ctypes
import os
import sys
import winreg

class LASTINPUTINFO(ctypes.Structure):
    _fields_ = [
        ("cbSize", ctypes.c_uint),
        ("dwTime", ctypes.c_uint)
    ]

def get_system_idle_time() -> float:
    """Returns the time in seconds since the last user input (keyboard/mouse)."""
    lii = LASTINPUTINFO()
    lii.cbSize = ctypes.sizeof(LASTINPUTINFO)
    if ctypes.windll.user32.GetLastInputInfo(ctypes.byref(lii)):
        millis = ctypes.windll.kernel32.GetTickCount() - lii.dwTime
        return max(0.0, millis / 1000.0)
    return 0.0

def set_auto_start(enabled: bool):
    """Adds or removes the application from the Windows CurrentVersion\\Run registry key."""
    key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
    app_name = "DesktopBuddyAI"
    # Get current executable path
    if getattr(sys, 'frozen', False):
        # Running as PyInstaller executable
        exe_path = sys.executable
    else:
        # Running as python script
        exe_path = f'"{sys.executable}" "{os.path.abspath(sys.argv[0])}"'

    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE)
        if enabled:
            winreg.SetValueEx(key, app_name, 0, winreg.REG_SZ, exe_path)
        else:
            try:
                winreg.DeleteValue(key, app_name)
            except FileNotFoundError:
                pass
        winreg.CloseKey(key)
    except Exception as e:
        print(f"Error setting registry auto start: {e}")
