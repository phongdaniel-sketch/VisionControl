import json
import os
from dataclasses import dataclass, asdict
from pathlib import Path
from .monitors import ScreenRegion


@dataclass
class MouseCalibration:
    left: float = 0.10
    right: float = 0.90
    top: float = 0.10
    bottom: float = 0.90

    def map(self, x: float, y: float, screen: tuple[int, int]) -> tuple[float, float]:
        return self.map_to_region(x, y, ScreenRegion(0, 0, screen[0], screen[1]))

    def map_to_region(self, x: float, y: float, region: ScreenRegion) -> tuple[float, float]:
        nx = max(0.0, min(1.0, (x - self.left) / max(self.right - self.left, 0.01)))
        ny = max(0.0, min(1.0, (y - self.top) / max(self.bottom - self.top, 0.01)))
        return region.x + nx * (region.width - 1), region.y + ny * (region.height - 1)


def pointer_point(hand, mode):
    if mode == 'palm':
        return tuple(sum(hand.landmarks[i][axis] for i in (0, 5, 9, 13, 17)) / 5
                     for axis in range(3))
    return hand.landmarks[8]


def calibration_filename(mode):
    return 'mouse_calibration_palm.json' if mode == 'palm' else 'mouse_calibration.json'


class CalibrationSession:
    stages = ("left", "right", "top", "bottom")

    def __init__(self):
        self.active = False
        self.index = 0
        self.values: dict[str, float] = {}

    @property
    def stage(self) -> str | None:
        return self.stages[self.index] if self.active else None

    def start(self) -> None:
        self.active = True
        self.index = 0
        self.values.clear()

    def cancel(self) -> None:
        self.active = False
        self.index = 0
        self.values.clear()

    def capture(self, x: float, y: float) -> bool:
        if not self.active:
            raise RuntimeError("Calibration has not started")
        stage = self.stages[self.index]
        self.values[stage] = x if stage in {"left", "right"} else y
        self.index += 1
        if self.index == len(self.stages):
            self.active = False
            return True
        return False

    def result(self) -> MouseCalibration:
        if self.active or set(self.values) != set(self.stages):
            raise RuntimeError("Calibration is incomplete")
        calibration = MouseCalibration(**self.values)
        if not (0 <= calibration.left < calibration.right <= 1 and
                0 <= calibration.top < calibration.bottom <= 1):
            raise ValueError("Captured calibration bounds are invalid")
        return calibration


def load_calibration(path: str | Path) -> MouseCalibration:
    file = Path(path)
    if not file.exists(): return MouseCalibration()
    values = json.loads(file.read_text(encoding="utf-8"))
    calibration = MouseCalibration(**values)
    if not (0 <= calibration.left < calibration.right <= 1 and 0 <= calibration.top < calibration.bottom <= 1):
        raise ValueError("Invalid mouse calibration bounds")
    return calibration


def save_calibration(path: str | Path, calibration: MouseCalibration) -> None:
    file = Path(path); file.parent.mkdir(parents=True, exist_ok=True)
    temporary = file.with_suffix(file.suffix + ".tmp")
    try:
        temporary.write_text(json.dumps(asdict(calibration), indent=2) + "\n", encoding="utf-8")
        os.replace(temporary, file)
    finally:
        temporary.unlink(missing_ok=True)
