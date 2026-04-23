import os
import sys

def is_windows():
    return os.name == 'nt'

def is_macos():
    return sys.platform == 'darwin'

def is_posix():
    return os.name == 'posix'

def is_windows_dark_mode():
    """Detects if Windows is configured to use dark mode."""
    if not is_windows():
        return False
    try:
        import winreg
        registry = winreg.ConnectRegistry(None, winreg.HKEY_CURRENT_USER)
        key = winreg.OpenKey(registry, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Themes\Personalize")
        value, _ = winreg.QueryValueEx(key, "AppsUseLightTheme")
        return value == 0
    except Exception:
        return False

def reverse_filenames_if_windows(filenames):
    """GTK file chooser on Windows can return files in reverse order."""
    if is_windows():
        return list(reversed(filenames))
    return list(filenames)
