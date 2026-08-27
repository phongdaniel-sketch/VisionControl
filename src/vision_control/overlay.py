class Overlay:
    def __init__(self, cv2_module, logo_path=None):
        self.cv2 = cv2_module
        self.logo = None
        if logo_path:
            logo = self.cv2.imread(str(logo_path), self.cv2.IMREAD_UNCHANGED)
            if logo is not None and len(logo.shape) == 3 and logo.shape[2] == 4:
                self.logo = self.cv2.resize(logo, (64, 64), interpolation=self.cv2.INTER_AREA)

    def draw(self, frame, *, paused: bool, mouse_role: str, keyboard_role: str,
             gesture: str, hands=(), mouse_found=False, keyboard_found=False,
             mouse_status="paused", monitor_name="display",
             keyboard_state="DISARMED", arming_progress=0.0,
             error: str = ""):
        color = (0, 180, 255) if paused else (0, 220, 0)
        text = f"{'PAUSED' if paused else 'ACTIVE'} | mouse={mouse_role}:{'OK' if mouse_found else 'NO'} | keyboard={keyboard_role}:{'OK' if keyboard_found else 'NO'}"
        self.cv2.putText(frame, text, (12, 30), self.cv2.FONT_HERSHEY_SIMPLEX, .55, color, 2)
        self.cv2.putText(frame, f"mouse_action={mouse_status} | monitor={monitor_name}", (12, 56),
                         self.cv2.FONT_HERSHEY_SIMPLEX, .55, color, 2)
        self.cv2.putText(frame, f"gesture={gesture} | hands={len(hands)}", (12, 82),
                         self.cv2.FONT_HERSHEY_SIMPLEX, .55, color, 2)
        keyboard_color = (0, 220, 0) if keyboard_state == "ARMED" else (0, 165, 255)
        progress_text = f" {int(arming_progress * 100)}%" if arming_progress > 0 else ""
        self.cv2.putText(frame, f"keyboard_mode={keyboard_state}{progress_text}", (12, 108),
                         self.cv2.FONT_HERSHEY_SIMPLEX, .55, keyboard_color, 2)
        height, width = frame.shape[:2]
        self._draw_logo(frame, width)
        for hand in hands:
            for x, y, _ in hand.landmarks:
                self.cv2.circle(frame, (int(x * width), int(y * height)), 3, (255, 120, 0), -1)
            wrist = hand.landmarks[0]
            self.cv2.putText(frame, f"{hand.label} {hand.confidence:.2f}",
                             (int(wrist[0] * width), int(wrist[1] * height)),
                             self.cv2.FONT_HERSHEY_SIMPLEX, .5, (255, 255, 0), 2)
        if error:
            self.cv2.putText(frame, error[:100], (12, 134), self.cv2.FONT_HERSHEY_SIMPLEX, .5, (0, 0, 255), 2)
        return frame

    def _draw_logo(self, frame, width):
        if self.logo is None or width < 88 or frame.shape[0] < 88:
            return
        x, y = width - 76, 12
        rgb = self.logo[:, :, :3].astype("float32")
        alpha = (self.logo[:, :, 3:4].astype("float32") / 255.0)
        target = frame[y:y + 64, x:x + 64].astype("float32")
        frame[y:y + 64, x:x + 64] = (rgb * alpha + target * (1 - alpha)).astype("uint8")
