import json
from dataclasses import dataclass
from pathlib import Path


ALLOWED_ACTIONS = {"press", "hold"}
ALLOWED_KEYS = set("abcdefghijklmnopqrstuvwxyz0123456789") | {
    "space", "enter", "esc", "tab", "shift", "ctrl", "alt", "win",
    "left", "right", "up", "down", "backspace", "delete"
}


@dataclass(frozen=True)
class GestureBinding:
    action_type: str
    keys: tuple[str, ...]


@dataclass(frozen=True)
class Profile:
    mouse_hand: str
    keyboard_hand: str
    swap_hands: bool
    monitor_mode: str
    fixed_monitor: int
    bindings: dict[str, GestureBinding]
    thresholds: dict[str, float]


def load_profile(path: str | Path) -> Profile:
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    if raw.get("version") != 1:
        raise ValueError("Unsupported profile version")
    if raw.get("mouse_hand") not in {"Left", "Right"} or raw.get("keyboard_hand") not in {"Left", "Right"}:
        raise ValueError("Hand roles must be Left or Right")
    if raw["mouse_hand"] == raw["keyboard_hand"]:
        raise ValueError("Mouse and keyboard hands must differ")
    monitor_mode = raw.get("monitor_mode", "active")
    if monitor_mode not in {"active", "fixed", "all"}:
        raise ValueError("monitor_mode must be active, fixed, or all")
    fixed_monitor = int(raw.get("fixed_monitor", 0))
    if fixed_monitor < 0:
        raise ValueError("fixed_monitor must be zero or greater")
    bindings = {}
    for gesture, binding in raw.get("left_hand", {}).items():
        action_type = binding.get("type")
        keys = tuple(binding.get("keys", []))
        if action_type not in ALLOWED_ACTIONS or not keys or any(k not in ALLOWED_KEYS for k in keys):
            raise ValueError(f"Invalid binding for gesture: {gesture}")
        bindings[gesture] = GestureBinding(action_type, keys)
    thresholds = raw.get("thresholds", {})
    for key in ("gesture_confidence", "pinch_close_ratio", "pinch_open_ratio"):
        if not 0 < float(thresholds.get(key, 0.5)) <= 1:
            raise ValueError(f"Invalid threshold: {key}")
    return Profile(raw["mouse_hand"], raw["keyboard_hand"], bool(raw.get("swap_hands", False)),
                   monitor_mode, fixed_monitor, bindings, thresholds)
