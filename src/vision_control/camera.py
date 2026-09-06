import sys
import os


class Camera:
    def __init__(self, index=0, width=None, height=None, fps=None):
        preset = os.environ.get('VISION_CONTROL_CAMERA_PRESET') == '720p30'
        width = width if width is not None else (1280 if preset else 640)
        height = height if height is not None else (720 if preset else 480)
        self.fps = fps if fps is not None else (30 if preset else None)
        self.index, self.width, self.height, self.cap = index, width, height, None
        self.reported_frame = False

    def open(self):
        import cv2
        # DirectShow avoids the default Windows backend stalling during startup.
        self.cap = (cv2.VideoCapture(self.index, cv2.CAP_DSHOW)
                    if sys.platform == "win32" else cv2.VideoCapture(self.index))
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
        if self.fps is not None:
            self.cap.set(cv2.CAP_PROP_FPS, self.fps)
            if sys.platform == 'win32':
                self.cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG'))
        if not self.cap.isOpened(): raise RuntimeError("Unable to open webcam")
        if self.fps is not None:
            print(f'[camera] requested={self.width}x{self.height}@{self.fps} '
                  f'driver_fps={self.cap.get(cv2.CAP_PROP_FPS):.2f}', flush=True)
        self.reported_frame = False

    def read(self):
        if self.cap is None: self.open()
        ok, frame = self.cap.read()
        if not ok: raise RuntimeError("Unable to read webcam frame")
        if self.fps is not None and not self.reported_frame:
            print(f'[camera] actual_frame={frame.shape[1]}x{frame.shape[0]}', flush=True)
            self.reported_frame = True
        return frame

    def close(self):
        cap, self.cap = self.cap, None
        if cap is not None:
            cap.release()
