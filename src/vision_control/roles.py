from .types import HandObservation, HandsFrame


def assign_roles(frame: HandsFrame, mouse_label: str, keyboard_label: str, swap_hands: bool = False):
    """Return (mouse hand, keyboard hand); ambiguity never produces input."""
    if swap_hands:
        mouse_label = "Left" if mouse_label == "Right" else "Right"
        keyboard_label = "Left" if keyboard_label == "Right" else "Right"
    mouse = [h for h in frame.hands if h.label == mouse_label]
    keyboard = [h for h in frame.hands if h.label == keyboard_label]
    return (mouse[0] if len(mouse) == 1 else None,
            keyboard[0] if len(keyboard) == 1 else None)
