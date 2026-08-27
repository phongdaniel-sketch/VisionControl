class Overlay:
    def __init__(self, cv2_module):
        self.cv2 = cv2_module

    def draw(self, frame, *, paused: bool, mouse_role: str, keyboard_role: str,
             gesture: str, hands=(), mouse_found=False, keyboard_found=False,
             error: str = ""):
        color = (0, 180, 255) if paused else (0, 220, 0)
        text = f"{'PAUSED' if paused else 'ACTIVE'} | mouse={mouse_role}:{'OK' if mouse_found else 'NO'} | keyboard={keyboard_role}:{'OK' if keyboard_found else 'NO'}"
        self.cv2.putText(frame, text, (12, 30), self.cv2.FONT_HERSHEY_SIMPLEX, .55, color, 2)
        self.cv2.putText(frame, f"gesture={gesture} | hands={len(hands)}", (12, 56),
                         self.cv2.FONT_HERSHEY_SIMPLEX, .55, color, 2)
        height, width = frame.shape[:2]
        for hand in hands:
            for x, y, _ in hand.landmarks:
                self.cv2.circle(frame, (int(x * width), int(y * height)), 3, (255, 120, 0), -1)
            wrist = hand.landmarks[0]
            self.cv2.putText(frame, f"{hand.label} {hand.confidence:.2f}",
                             (int(wrist[0] * width), int(wrist[1] * height)),
                             self.cv2.FONT_HERSHEY_SIMPLEX, .5, (255, 255, 0), 2)
        if error:
            self.cv2.putText(frame, error[:100], (12, 82), self.cv2.FONT_HERSHEY_SIMPLEX, .5, (0, 0, 255), 2)
        return frame
