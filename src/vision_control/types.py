from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class HandObservation:
    label: str
    landmarks: tuple[tuple[float, float, float], ...]
    confidence: float = 1.0


@dataclass(frozen=True)
class HandsFrame:
    timestamp: float
    hands: tuple[HandObservation, ...]
    width: int = 640
    height: int = 480


@dataclass(frozen=True)
class ActionIntent:
    action: str
    payload: Any = None
    source: str = "system"


def distance(a: tuple[float, float, float], b: tuple[float, float, float]) -> float:
    return sum((a[i] - b[i]) ** 2 for i in range(3)) ** 0.5
