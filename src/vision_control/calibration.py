import json
from dataclasses import dataclass, asdict
from pathlib import Path


@dataclass
class MouseCalibration:
    left: float = 0.10
    right: float = 0.90
    top: float = 0.10
    bottom: float = 0.90

    def map(self, x: float, y: float, screen: tuple[int, int]) -> tuple[float, float]:
        width, height = screen
        nx = max(0.0, min(1.0, (x - self.left) / max(self.right - self.left, 0.01)))
        ny = max(0.0, min(1.0, (y - self.top) / max(self.bottom - self.top, 0.01)))
        return nx * (width - 1), ny * (height - 1)


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
    file.write_text(json.dumps(asdict(calibration), indent=2) + "\n", encoding="utf-8")
