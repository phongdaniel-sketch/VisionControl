from .types import HandObservation, distance


FINGERTIPS = (8, 12, 16, 20)
FINGER_PIPS = (6, 10, 14, 18)


def finger_states(hand: HandObservation) -> tuple[bool, bool, bool, bool]:
    p = hand.landmarks
    return tuple(p[tip][1] < p[pip][1] for tip, pip in zip(FINGERTIPS, FINGER_PIPS))


def classify_static(hand: HandObservation) -> tuple[str, float]:
    states = finger_states(hand)
    count = sum(states)
    thumb_open = hand.landmarks[4][0] < hand.landmarks[3][0]
    if states == (True, False, False, False): return "point", 0.9
    if states == (True, True, False, False): return "peace", 0.9
    if states == (True, True, True, False): return "three_fingers", 0.9
    if count == 4 and thumb_open: return "open_palm", 0.85
    if states == (True, True, True, True): return "four_fingers", 0.9
    if count == 0: return "fist", 0.9
    return "none", 0.5


def pinch(hand: HandObservation, a: int, b: int, close_ratio: float, open_ratio: float, active: bool) -> bool:
    p = hand.landmarks
    palm = max(distance(p[0], p[9]), 0.001)
    ratio = distance(p[a], p[b]) / palm
    return ratio < (open_ratio if active else close_ratio)
