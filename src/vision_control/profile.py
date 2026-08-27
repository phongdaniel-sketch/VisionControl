import json
from dataclasses import dataclass
from pathlib import Path
from .arming import ArmingSettings


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
    arming: ArmingSettings
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
    arming_raw = raw.get("arming", {})
    arming = ArmingSettings(
        enabled=bool(arming_raw.get("enabled", True)),
        gesture=str(arming_raw.get("gesture", "fist")),
        hold_seconds=float(arming_raw.get("hold_seconds", 1.0)),
        release_frames=int(arming_raw.get("release_frames", 4)),
        cooldown_seconds=float(arming_raw.get("cooldown_seconds", .5)),
        auto_disarm_seconds=float(arming_raw.get("auto_disarm_on_hand_loss_seconds", 2.0)),
    )
    if arming.hold_seconds <= 0 or arming.release_frames < 1 or arming.cooldown_seconds < 0 or arming.auto_disarm_seconds < 0:
        raise ValueError("Invalid arming settings")
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
    if arming.enabled and arming.gesture in bindings:
        raise ValueError("The arming gesture must not also have a key binding")
    return Profile(raw["mouse_hand"], raw["keyboard_hand"], bool(raw.get("swap_hands", False)),
                   monitor_mode, fixed_monitor, arming, bindings, thresholds)
