import json
import os
import re
import sys
from copy import deepcopy
from dataclasses import asdict, dataclass, field
from pathlib import Path

from .profile import ALLOWED_KEYS, load_profile


EDITABLE_GESTURES = (
    "point",
    "peace",
    "three_fingers",
    "four_fingers",
    "open_palm",
)


@dataclass(frozen=True)
class DesktopSettings:
    camera_index: int = field(default_factory=lambda: 0 if sys.platform == "win32" else 1)
    start_paused: bool = False
    show_skeleton: bool = True
    show_guide: bool = True
    start_minimized: bool = False


def load_desktop_settings(path: str | Path) -> DesktopSettings:
    path = Path(path)
    if not path.exists():
        return DesktopSettings()
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
        camera_index = int(raw.get("camera_index", DesktopSettings().camera_index))
        if camera_index < 0:
            raise ValueError("Camera index must be zero or greater")
        return DesktopSettings(camera_index, bool(raw.get("start_paused", False)),
                               bool(raw.get('show_skeleton', True)), bool(raw.get('show_guide', True)),
                               bool(raw.get('start_minimized', False)))
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


def parse_key_list(value: str) -> tuple[str, ...]:
    keys = tuple(part for part in re.split(r"[\s,+]+", value.strip().lower()) if part)
    if not keys:
        raise ValueError("Enter at least one key")
    invalid = [key for key in keys if key not in ALLOWED_KEYS]
    if invalid:
        raise ValueError(f"Unsupported key(s): {', '.join(invalid)}")
    return keys


def apply_gesture_bindings(raw: dict, selections: dict[str, tuple[str, str]]) -> dict:
    updated = deepcopy(raw)
    bindings = dict(updated.get("left_hand", {}))
    for gesture, (action, key_text) in selections.items():
        if gesture not in EDITABLE_GESTURES:
            raise ValueError(f"Gesture cannot be configured here: {gesture}")
        normalized_action = action.strip().lower()
        if normalized_action == "disabled":
            bindings.pop(gesture, None)
            continue
        if normalized_action not in {"press", "hold"}:
            raise ValueError(f"Unsupported action for {gesture}: {action}")
        bindings[gesture] = {
            "type": normalized_action,
            "keys": list(parse_key_list(key_text)),
        }
    updated["left_hand"] = bindings
    return updated


def _write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")
    os.replace(temporary, path)
