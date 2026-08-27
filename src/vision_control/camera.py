class Camera:
    def __init__(self, index=0, width=640, height=480):
        self.index, self.width, self.height, self.cap = index, width, height, None

    def open(self):
        import cv2
        self.cap = cv2.VideoCapture(self.index)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
        if not self.cap.isOpened(): raise RuntimeError("Unable to open webcam")

    def read(self):
        if self.cap is None: self.open()
        ok, frame = self.cap.read()
        if not ok: raise RuntimeError("Unable to read webcam frame")
        return frame

    def close(self):
        if self.cap is not None: self.cap.release()
