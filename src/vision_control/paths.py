import os
import sys
from pathlib import Path


def resource_root() -> Path:
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS)
    return Path(__file__).resolve().parents[2]


def user_data_dir(platform_name: str | None = None,
                  environ: dict[str, str] | None = None,
                  home: Path | None = None) -> Path:
    platform_name = platform_name or sys.platform
    environ = environ if environ is not None else os.environ
    home = home or Path.home()
    if platform_name == "darwin":
        return home / "Library" / "Application Support" / "VisionControl"
    if platform_name.startswith("win"):
        base = environ.get("LOCALAPPDATA") or environ.get("APPDATA")
        return Path(base) / "VisionControl" if base else home / "AppData" / "Local" / "VisionControl"
    base = environ.get("XDG_CONFIG_HOME")
    return (Path(base) if base else home / ".config") / "visioncontrol"


def runtime_data_dir() -> Path:
    return user_data_dir() if getattr(sys, "frozen", False) else resource_root() / "data"

