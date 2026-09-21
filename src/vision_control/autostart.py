"""Opt-in Windows login startup, scoped to the current user."""
import subprocess
import sys
from pathlib import Path

RUN_KEY = r'Software\Microsoft\Windows\CurrentVersion\Run'
VALUE_NAME = 'VisionControl'


def launch_command():
    executable = Path(sys.executable).resolve()
    if getattr(sys, 'frozen', False):
        return subprocess.list2cmdline([str(executable)])
    pythonw = executable.with_name('pythonw.exe')
    if not pythonw.is_file():
        raise RuntimeError('pythonw.exe is required for background startup')
    source = str(Path(__file__).resolve().parents[1])
    code = f'import sys; sys.path.insert(0, {source!r}); from vision_control.launcher import main; raise SystemExit(main())'
    return subprocess.list2cmdline([str(pythonw), '-c', code])


def is_enabled():
    if sys.platform != 'win32':
        return False
    import winreg
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY, 0, winreg.KEY_READ) as key:
            value, _ = winreg.QueryValueEx(key, VALUE_NAME)
            return bool(value)
    except FileNotFoundError:
        return False


def set_enabled(enabled):
    if sys.platform != 'win32':
        raise RuntimeError('Start with the Desktop is available on Windows only')
    import winreg
    if enabled:
        command = launch_command()
        with winreg.CreateKeyEx(winreg.HKEY_CURRENT_USER, RUN_KEY, 0, winreg.KEY_SET_VALUE) as key:
            winreg.SetValueEx(key, VALUE_NAME, 0, winreg.REG_SZ, command)
    else:
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY, 0, winreg.KEY_SET_VALUE) as key:
                winreg.DeleteValue(key, VALUE_NAME)
        except FileNotFoundError:
            pass
