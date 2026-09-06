import json
from dataclasses import dataclass, field
from pathlib import Path
from .arming import ArmingSettings
from .gestures import (
    MOUSE_CLICK_GESTURES, MOUSE_MOVE_GESTURES, MOUSE_SCROLL_GESTURES,
)


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
    pointer_mode: str = "gesture"
    gesture_v1: dict = field(default_factory=dict)


def load_profile(path: str | Path) -> Profile:
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    if raw.get("version") != 1:
        raise ValueError("Unsupported profile version")
    pointer_mode = raw.get("pointer_mode", "gesture")
    if pointer_mode not in {"gesture", "index_fingertip", "thumb_lock", "palm"}:
        raise ValueError("Invalid pointer_mode")
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
        enabled=False,  # Legacy fist arming is retired, including saved profiles.
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
    if not 0 <= float(thresholds.get("pinch_confirm_seconds", .08)) <= .5:
        raise ValueError("pinch_confirm_seconds must be between 0 and 0.5")
    if not .04 <= float(thresholds.get('pinch_release_seconds', .1)) <= .5:
        raise ValueError('pinch_release_seconds must be between .04 and .5')
    if not isinstance(thresholds.get("cursor_adaptive_smoothing", False), bool):
        raise ValueError("cursor_adaptive_smoothing must be boolean")
    if not .05 <= float(thresholds.get("cursor_smoothing", .6)) <= 1:
        raise ValueError("cursor_smoothing must be between 0.05 and 1")
    for key in ("gesture_confidence", "pinch_close_ratio", "pinch_open_ratio"):
        if not 0 < float(thresholds.get(key, 0.5)) <= 1:
            raise ValueError(f"Invalid threshold: {key}")
    if float(thresholds.get("pinch_close_ratio", .35)) >= float(
            thresholds.get("pinch_open_ratio", .5)):
        raise ValueError("pinch_close_ratio must be lower than pinch_open_ratio")
    if int(thresholds.get("gesture_on_frames", 3)) < 1:
        raise ValueError("gesture_on_frames must be at least one")
    if float(thresholds.get("drag_hold_seconds", .4)) <= 0:
        raise ValueError("drag_hold_seconds must be greater than zero")
    if float(thresholds.get("scroll_deadzone", .015)) < 0:
        raise ValueError("scroll_deadzone must be zero or greater")
    move_gesture = str(thresholds.get("mouse_move_gesture", "any"))
    primary_click = str(thresholds.get(
        "mouse_primary_click_gesture", "pinch_index"))
    secondary_click = str(thresholds.get(
        "mouse_secondary_click_gesture", "pinch_middle"))
    scroll_gesture = str(thresholds.get("mouse_scroll_gesture", "peace"))
    if move_gesture not in MOUSE_MOVE_GESTURES:
        raise ValueError("Invalid mouse_move_gesture")
    if primary_click not in MOUSE_CLICK_GESTURES:
        raise ValueError("Invalid mouse_primary_click_gesture")
    if secondary_click not in MOUSE_CLICK_GESTURES:
        raise ValueError("Invalid mouse_secondary_click_gesture")
    if scroll_gesture not in MOUSE_SCROLL_GESTURES:
        raise ValueError("Invalid mouse_scroll_gesture")
    if primary_click != "disabled" and primary_click == secondary_click:
        raise ValueError("Primary and secondary click gestures must differ")
    if move_gesture != "any" and move_gesture == scroll_gesture:
        raise ValueError("Mouse move and scroll gestures must differ")
    edge_zone = float(thresholds.get("monitor_edge_zone", .08))
    edge_dwell = float(thresholds.get("monitor_edge_dwell_seconds", .8))
    if not 0 < edge_zone < .5 or edge_dwell <= 0:
        raise ValueError("Invalid monitor edge switching settings")
    if arming.enabled and arming.gesture in bindings:
        raise ValueError("The arming gesture must not also have a key binding")
    from .gesture_v1_config import config
    return Profile(raw["mouse_hand"], raw["keyboard_hand"], bool(raw.get("swap_hands", False)),
                   monitor_mode, fixed_monitor, arming, bindings, thresholds, pointer_mode,
                   config(raw.get('gesture_v1')))
