import numpy as np


class StartupCancelled(Exception):
    pass


class StartupScreen:
    def __init__(self, cv2_module, splash_path, loading_path,
                 window_name="VisionControl", size=(1000, 626)):
        self.cv2 = cv2_module
        self.window_name = window_name
        self.size = size
        self.splash = self._load(splash_path)
        self.loading = self._clean_loading_bar(self._load(loading_path))

    def _load(self, path):
        image = self.cv2.imread(str(path), self.cv2.IMREAD_COLOR)
        if image is None:
            raise RuntimeError(f"Unable to load startup image: {path}")
        return self.cv2.resize(image, self.size, interpolation=self.cv2.INTER_AREA)

    def show_splash(self, duration_ms=1000):
        self._show(self.splash, duration_ms)

    def show_loading(self, progress: float, status: str, wait_ms=1):
        self._show(self.render_loading(progress, status), wait_ms)

    def render_loading(self, progress: float, status: str):
        frame = self.loading.copy()
        progress = max(0.0, min(1.0, progress))
        x, center_y, bar_width, bar_height = self._bar_geometry()
        self._draw_rounded_line(frame, x, center_y, bar_width, bar_height + 4,
                                (220, 92, 24))
        self._draw_rounded_line(frame, x, center_y, bar_width, bar_height,
                                (24, 15, 12))

        filled = int(round(bar_width * progress))
        if filled > 0:
            self._draw_gradient_fill(frame, x, center_y, bar_width,
                                     bar_height, filled)
            self._draw_leading_glow(frame, x + filled, center_y)
        return frame

    def _bar_geometry(self):
        width, height = self.size
        return (int(width * .552), int(height * .751),
                int(width * .338), max(8, int(height * .014)))

    def _clean_loading_bar(self, frame):
        """Remove the baked sample progress so runtime progress can replace it."""
        x, center_y, bar_width, bar_height = self._bar_geometry()
        mask = np.zeros(frame.shape[:2], dtype=np.uint8)
        padding_x = 14
        padding_y = 18
        self.cv2.rectangle(
            mask,
            (x - padding_x, center_y - bar_height // 2 - padding_y),
            (x + bar_width + padding_x,
             center_y + bar_height // 2 + padding_y),
            255, -1,
        )
        return self.cv2.inpaint(frame, mask, 7, self.cv2.INPAINT_TELEA)

    def _draw_rounded_line(self, frame, x, center_y, width, thickness, color):
        radius = thickness // 2
        self.cv2.line(frame, (x + radius, center_y),
                      (x + width - radius, center_y), color, thickness,
                      self.cv2.LINE_AA)
        self.cv2.circle(frame, (x + radius, center_y), radius, color, -1,
                        self.cv2.LINE_AA)
        self.cv2.circle(frame, (x + width - radius, center_y), radius, color, -1,
                        self.cv2.LINE_AA)

    def _draw_gradient_fill(self, frame, x, center_y, full_width, height,
                            filled):
        radius = height // 2
        left = x
        right = min(x + full_width, x + max(1, filled))
        top = center_y - radius
        bottom = center_y + radius + 1
        gradient = np.empty((bottom - top, right - left, 3), dtype=np.uint8)
        stops = (
            (0.00, np.array((55, 100, 255))),
            (0.34, np.array((105, 55, 240))),
            (0.66, np.array((245, 75, 120))),
            (1.00, np.array((255, 125, 30))),
        )
        positions = np.linspace(0.0, filled / full_width, right - left)
        for channel in range(3):
            gradient[:, :, channel] = np.interp(
                positions,
                [stop[0] for stop in stops],
                [stop[1][channel] for stop in stops],
            ).astype(np.uint8)

        mask = np.zeros((bottom - top, right - left), dtype=np.uint8)
        self.cv2.rectangle(mask, (radius, 0),
                           (max(radius, right - left - radius), height), 255, -1)
        self.cv2.circle(mask, (min(radius, right - left - 1), radius),
                        radius, 255, -1, self.cv2.LINE_AA)
        self.cv2.circle(mask, (max(0, right - left - radius - 1), radius),
                        radius, 255, -1, self.cv2.LINE_AA)
        roi = frame[top:bottom, left:right]
        alpha = mask.astype(np.float32)[:, :, None] / 255.0
        roi[:] = (gradient * alpha + roi * (1.0 - alpha)).astype(np.uint8)

    def _draw_leading_glow(self, frame, tip_x, center_y):
        glow = np.zeros_like(frame)
        self.cv2.circle(glow, (tip_x, center_y), 18, (255, 170, 75), -1,
                        self.cv2.LINE_AA)
        glow = self.cv2.GaussianBlur(glow, (0, 0), 10)
        self.cv2.addWeighted(frame, 1.0, glow, .95, 0.0, frame)
        self.cv2.circle(frame, (tip_x, center_y), 4, (255, 245, 220), -1,
                        self.cv2.LINE_AA)

    def _show(self, frame, wait_ms):
        self.cv2.namedWindow(self.window_name, self.cv2.WINDOW_NORMAL)
        self.cv2.resizeWindow(self.window_name, *self.size)
        self.cv2.imshow(self.window_name, frame)
        key = self.cv2.waitKey(max(1, wait_ms)) & 0xFF
        if key == 27:
            raise StartupCancelled()
