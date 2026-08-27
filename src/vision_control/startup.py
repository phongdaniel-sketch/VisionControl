class StartupCancelled(Exception):
    pass


class StartupScreen:
    def __init__(self, cv2_module, splash_path, loading_path,
                 window_name="VisionControl", size=(1000, 626)):
        self.cv2 = cv2_module
        self.window_name = window_name
        self.size = size
        self.splash = self._load(splash_path)
        self.loading = self._load(loading_path)

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
        width, height = self.size
        progress = max(0.0, min(1.0, progress))
        x = int(width * .552)
        y = int(height * .745)
        bar_width = int(width * .338)
        bar_height = max(8, int(height * .014))
        self.cv2.rectangle(frame, (x - 2, y - 2), (x + bar_width + 2, y + bar_height + 2),
                           (85, 80, 125), 1)
        self.cv2.rectangle(frame, (x, y), (x + bar_width, y + bar_height), (12, 18, 35), -1)
        filled = int(bar_width * progress)
        if filled:
            self.cv2.rectangle(frame, (x, y), (x + filled, y + bar_height), (245, 95, 70), -1)
        self.cv2.putText(frame, f"{int(progress * 100):3d}%  {status}",
                         (x, y + 38), self.cv2.FONT_HERSHEY_SIMPLEX, .48,
                         (220, 225, 240), 1, self.cv2.LINE_AA)
        return frame

    def _show(self, frame, wait_ms):
        self.cv2.namedWindow(self.window_name, self.cv2.WINDOW_NORMAL)
        self.cv2.resizeWindow(self.window_name, *self.size)
        self.cv2.imshow(self.window_name, frame)
        key = self.cv2.waitKey(max(1, wait_ms)) & 0xFF
        if key == 27:
            raise StartupCancelled()
