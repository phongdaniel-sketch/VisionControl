import json
import os
from dataclasses import asdict, dataclass
from pathlib import Path

from .profile import load_profile


@dataclass(frozen=True)
class DesktopSettings:
    camera_index: int = 0
    start_paused: bool = False


def load_desktop_settings(path: str | Path) -> DesktopSettings:
    path = Path(path)
    if not path.exists():
        return DesktopSettings()
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
        camera_index = int(raw.get("camera_index", 0))
        if camera_index < 0:
            raise ValueError("Camera index must be zero or greater")
        return DesktopSettings(camera_index, bool(raw.get("start_paused", False)))
    except (json.JSONDecodeError, TypeError, ValueError) as exc:
        raise ValueError(f"Invalid desktop settings: {exc}") from exc


def save_desktop_settings(path: str | Path, settings: DesktopSettings) -> None:
    if settings.camera_index < 0:
        raise ValueError("Camera index must be zero or greater")
    _write_json(Path(path), asdict(settings))


def save_user_profile(path: str | Path, raw: dict) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(raw, indent=2) + "\n", encoding="utf-8")
    try:
        load_profile(temporary)
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def _write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")
    os.replace(temporary, path)
