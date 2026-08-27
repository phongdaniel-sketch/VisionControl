class MediaPipeTracker:
    def __init__(self, max_hands=2, model_path=None):
        from pathlib import Path
        from urllib.request import urlopen
        from mediapipe.tasks.python.core.base_options import BaseOptions
        from mediapipe.tasks.python.vision import HandLandmarker, HandLandmarkerOptions, RunningMode
        from .paths import resource_root, runtime_data_dir
        self.mp = __import__("mediapipe")
        bundled_model = resource_root() / "assets" / "models" / "hand_landmarker.task"
        model = Path(model_path) if model_path else bundled_model
        if not model.exists():
            model = runtime_data_dir() / "models" / "hand_landmarker.task"
        if not model.exists():
            model.parent.mkdir(parents=True, exist_ok=True)
            url = "https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task"
            with urlopen(url, timeout=30) as response: model.write_bytes(response.read())
        options = HandLandmarkerOptions(base_options=BaseOptions(model_asset_path=str(model),
                                                                 delegate=BaseOptions.Delegate.CPU),
                                        running_mode=RunningMode.IMAGE, num_hands=max_hands,
                                        min_hand_detection_confidence=.6,
                                        min_hand_presence_confidence=.6,
                                        min_tracking_confidence=.6)
        self.landmarker = HandLandmarker.create_from_options(options)

    def track(self, frame, timestamp=0):
        import cv2
        from .types import HandObservation, HandsFrame
        image = self.mp.Image(image_format=self.mp.ImageFormat.SRGB,
                              data=cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        result = self.landmarker.detect(image)
        hands = []
        for landmarks, handedness in zip(result.hand_landmarks or [], result.handedness or []):
            points = tuple((p.x, p.y, p.z) for p in landmarks)
            hands.append(HandObservation(handedness[0].category_name, points, handedness[0].score))
        return HandsFrame(timestamp, tuple(hands), frame.shape[1], frame.shape[0])

    def close(self):
        self.landmarker.close()
