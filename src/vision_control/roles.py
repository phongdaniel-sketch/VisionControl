import math
from dataclasses import replace
from .types import HandObservation, HandsFrame


class RoleContinuity:
    """Resolve duplicate labels only with a unique, fresh palm match."""
    def __init__(self):
        self.reset()

    def reset(self):
        self.previous = {}

    @staticmethod
    def palm(hand, frame):
        if len(hand.landmarks) != 21 or hand.confidence < .7:
            return None
        points = tuple((hand.landmarks[i][0] * frame.width,
                        hand.landmarks[i][1] * frame.height)
                       for i in (0, 5, 9, 13, 17))
        if not all(math.isfinite(v) for p in points for v in p):
            return None
        return points if math.dist(points[0], points[2]) > 5 else None

    def update(self, frame):
        kept = []
        history = {}
        for label in dict.fromkeys(h.label for h in frame.hands):
            group = [h for h in frame.hands if h.label == label]
            selected = group[0] if len(group) == 1 else None
            old = self.previous.get(label)
            if len(group) > 1 and old is not None:
                stamp, dimensions, palm = old
                if dimensions == (frame.width, frame.height) and 0 < frame.timestamp-stamp <= .15:
                    scale = math.dist(palm[0], palm[2])
                    ranked = []
                    for index, hand in enumerate(group):
                        current = self.palm(hand, frame)
                        score = (sum(math.dist(a, b)**2 for a, b in zip(palm, current))/5)**.5/scale if current else math.inf
                        ranked.append((score, index))
                    ranked.sort()
                    if ranked[0][0] <= .3 and ranked[1][0]-ranked[0][0] >= .2:
                        selected = group[ranked[0][1]]
            kept.extend([selected] if selected is not None else group)
            if selected is not None:
                palm = self.palm(selected, frame)
                if palm is not None:
                    history[label] = (frame.timestamp, (frame.width, frame.height), palm)
        self.previous = history
        return replace(frame, hands=tuple(kept))


def assign_roles(frame: HandsFrame, mouse_label: str, keyboard_label: str, swap_hands: bool = False):
    """Return (mouse hand, keyboard hand); ambiguity never produces input."""
    if swap_hands:
        mouse_label = "Left" if mouse_label == "Right" else "Right"
        keyboard_label = "Left" if keyboard_label == "Right" else "Right"
    mouse = [h for h in frame.hands if h.label == mouse_label]
    keyboard = [h for h in frame.hands if h.label == keyboard_label]
    return (mouse[0] if len(mouse) == 1 else None,
            keyboard[0] if len(keyboard) == 1 else None)
