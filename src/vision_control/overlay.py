class Overlay:
    def __init__(self, cv2_module):
        self.cv2 = cv2_module

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
        self.draw_landmarks(frame, hands)
        if error:
            self.cv2.putText(frame, error[:100], (12, 134), self.cv2.FONT_HERSHEY_SIMPLEX, .5, (0, 0, 255), 2)
        return frame

    def draw_landmarks(self, frame, hands=()):
        height, width = frame.shape[:2]
        connections = (
            (0, 1), (1, 2), (2, 3), (3, 4),
            (0, 5), (5, 6), (6, 7), (7, 8),
            (5, 9), (9, 10), (10, 11), (11, 12),
            (9, 13), (13, 14), (14, 15), (15, 16),
            (13, 17), (17, 18), (18, 19), (19, 20), (0, 17),
        )
        for hand in hands:
            points = [(int(x * width), int(y * height))
                      for x, y, _ in hand.landmarks]
            for start, end in connections:
                self.cv2.line(frame, points[start], points[end],
                              (255, 125, 45), 2, self.cv2.LINE_AA)
            for point in points:
                self.cv2.circle(frame, point, 4, (255, 255, 255), -1,
                                self.cv2.LINE_AA)
                self.cv2.circle(frame, point, 6, (255, 125, 45), 1,
                                self.cv2.LINE_AA)
        return frame

    def draw_fingertip(self, frame, hand):
        if len(hand.landmarks) < 21:
            return frame
        height, width = frame.shape[:2]
        x, y, _ = hand.landmarks[8]
        point = (int(x * width), int(y * height))
        self.cv2.circle(frame, point, 12, (0, 230, 255), 3, self.cv2.LINE_AA)
        self.cv2.circle(frame, point, 3, (0, 230, 255), -1, self.cv2.LINE_AA)
        tx, ty, _ = hand.landmarks[4]
        thumb = (int(tx * width), int(ty * height))
        self.cv2.circle(frame, thumb, 10, (255, 220, 0), 2, self.cv2.LINE_AA)
        self.cv2.putText(frame, 'I8', (point[0]+10, point[1]-10),
                         self.cv2.FONT_HERSHEY_SIMPLEX, .45, (0,230,255), 1)
        self.cv2.putText(frame, 'T4', (thumb[0]+10, thumb[1]+18),
                         self.cv2.FONT_HERSHEY_SIMPLEX, .45, (255,220,0), 1)
        return frame

    def draw_calibration(self, frame, calibration):
        height, width = frame.shape[:2]
        left, right = [round(v * (width - 1)) for v in (calibration.left, calibration.right)]
        top, bottom = [round(v * (height - 1)) for v in (calibration.top, calibration.bottom)]
        color = (80, 230, 80)
        self.cv2.rectangle(frame, (left, top), (right, bottom), color, 2)
        self.cv2.line(frame, ((left+right)//2, top), ((left+right)//2, bottom), color, 1)
        self.cv2.line(frame, (left, (top+bottom)//2), (right, (top+bottom)//2), color, 1)
        return frame
