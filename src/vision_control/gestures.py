import math

from .types import HandObservation, distance


FINGERTIPS = (8, 12, 16, 20)
FINGER_PIPS = (6, 10, 14, 18)

MOUSE_MOVE_GESTURES = {
    "any", "point", "peace", "three_fingers", "four_fingers", "open_palm",
}
MOUSE_CLICK_GESTURES = {"disabled", "pinch_index", "pinch_middle"}
MOUSE_SCROLL_GESTURES = {"peace", "three_fingers", "four_fingers", "open_palm"}


def _geometry(hand, frame_size=(640, 480)):
    """Use consistent image-axis units; depth follows MediaPipe's X scale."""
    if len(hand.landmarks) != 21 or frame_size[0] <= 0 or frame_size[1] <= 0:
        return None
    ratio = frame_size[0] / frame_size[1]
    points = [(x * ratio, y, z * ratio) for x, y, z in hand.landmarks]
    if not all(math.isfinite(value) for point in points for value in point):
        return None
    return points if distance(points[0], points[9]) > 1e-5 else None


def _joint_angle(a, joint, b):
    u = tuple(a[i] - joint[i] for i in range(3))
    v = tuple(b[i] - joint[i] for i in range(3))
    magnitude = math.sqrt(sum(x * x for x in u) * sum(x * x for x in v))
    if magnitude < 1e-10:
        return None
    cosine = max(-1.0, min(1.0, sum(x * y for x, y in zip(u, v)) / magnitude))
    return math.degrees(math.acos(cosine))


def finger_extended(hand, tip, frame_size=(640, 480)):
    points = _geometry(hand, frame_size)
    if points is None or tip not in FINGERTIPS:
        return False
    mcp, pip = tip - 3, tip - 2
    angle = _joint_angle(points[mcp], points[pip], points[tip])
    palm = distance(points[0], points[9])
    return (angle is not None and angle >= 145 and
            distance(points[tip], points[0]) > distance(points[pip], points[0]) + .1 * palm)


def is_closed_fist(hand, frame_size=(640, 480)):
    """A clear fist needs all four fingers bent and tucked toward the palm."""
    points = _geometry(hand, frame_size)
    if points is None:
        return False
    return all(_finger_folded(points, tip) for tip in FINGERTIPS)


def _finger_folded(points, tip):
    palm = distance(points[0], points[9])
    mcp, pip = tip - 3, tip - 2
    angle = _joint_angle(points[mcp], points[pip], points[tip])
    return (angle is not None and angle <= 110 and
            distance(points[tip], points[0]) <= distance(points[mcp], points[0]) + .1 * palm and
            distance(points[tip], points[mcp]) <= .75 * palm)


def thumb_state(hand, frame_size=(640, 480)):
    """Open/tucked/unknown relative to the palm, independent of hand labels."""
    points = _geometry(hand, frame_size)
    if points is None:
        return 'unknown'
    axis = tuple(points[5][i] - points[17][i] for i in range(3))
    width_squared = sum(value * value for value in axis)
    if width_squared < 1e-8:
        return 'unknown'
    outward = sum((points[4][i] - points[5][i]) * axis[i] for i in range(3)) / width_squared
    angle = _joint_angle(points[2], points[3], points[4])
    if angle is None:
        return 'unknown'
    if outward >= .35 and angle >= 140:
        return 'open'
    if outward <= .15:
        return 'tucked'
    return 'unknown'


def classify_mouse_pose(hand, frame_size=(640, 480)):
    if is_closed_fist(hand, frame_size):
        return 'fist'
    # Unused fingers may curl naturally; keyboard counting stays strict.
    if finger_states(hand, frame_size) == (True, False, False, False):
        return 'point'
    points = _geometry(hand, frame_size)
    if points is not None and not any(finger_states(hand, frame_size)[1:]):
        angle = _joint_angle(points[5], points[6], points[8])
        palm = distance(points[0], points[9])
        if (angle is not None and angle >= 130 and
                distance(points[8], points[0]) > distance(points[6], points[0]) + .05 * palm):
            return 'point'
    pose, _ = classify_static(hand, frame_size)
    return 'curled' if pose == 'fist' else pose


def finger_states(hand: HandObservation, frame_size=(640, 480)) -> tuple[bool, bool, bool, bool]:
    return tuple(finger_extended(hand, tip, frame_size) for tip in FINGERTIPS)


def classify_static(hand: HandObservation, frame_size=(640, 480)) -> tuple[str, float]:
    points = _geometry(hand, frame_size)
    if points is None:
        return 'none', 0.0
    states = finger_states(hand, frame_size)
    if any(not extended and not _finger_folded(points, tip)
           for tip, extended in zip(FINGERTIPS, states)):
        return 'none', 0.0
    count = sum(states)
    if states == (True, False, False, False): return "point", 0.9
    if states == (True, True, False, False): return "peace", 0.9
    if states == (True, True, True, False): return "three_fingers", 0.9
    if count == 4:
        thumb = thumb_state(hand, frame_size)
        if thumb == 'open': return 'open_palm', .85
        if thumb == 'tucked': return 'four_fingers', .9
        return 'none', 0.0
    if count == 0: return "fist", 0.9
    return "none", 0.5


def pinch(hand: HandObservation, a: int, b: int, close_ratio: float, open_ratio: float, active: bool) -> bool:
    p = hand.landmarks
    palm = max(distance(p[0], p[9]), 0.001)
    ratio = distance(p[a], p[b]) / palm
    return ratio < (open_ratio if active else close_ratio)
