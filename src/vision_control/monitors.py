from dataclasses import dataclass


@dataclass(frozen=True)
class ScreenRegion:
    x: int
    y: int
    width: int
    height: int
    name: str = "display"

    def contains(self, point: tuple[float, float]) -> bool:
        px, py = point
        return self.x <= px < self.x + self.width and self.y <= py < self.y + self.height

    @classmethod
    def union(cls, regions: list["ScreenRegion"]) -> "ScreenRegion":
        if not regions:
            return cls(0, 0, 1920, 1080, "fallback")
        left = min(region.x for region in regions)
        top = min(region.y for region in regions)
        right = max(region.x + region.width for region in regions)
        bottom = max(region.y + region.height for region in regions)
        return cls(left, top, right - left, bottom - top, "all")


class MonitorLayout:
    def __init__(self, regions: list[ScreenRegion], mode: str = "active", fixed_index: int = 0):
        if mode not in {"active", "fixed", "all"}:
            raise ValueError(f"Unsupported monitor mode: {mode}")
        self.regions = regions or [ScreenRegion(0, 0, 1920, 1080, "fallback")]
        self.mode = mode
        self.fixed_index = max(0, min(fixed_index, len(self.regions) - 1))

    def target(self, cursor: tuple[float, float]) -> ScreenRegion:
        if self.mode == "all":
            return ScreenRegion.union(self.regions)
        if self.mode == "fixed":
            return self.regions[self.fixed_index]
        return next((region for region in self.regions if region.contains(cursor)), self.regions[0])


def discover_monitors(mode: str = "active", fixed_index: int = 0) -> MonitorLayout:
    try:
        from screeninfo import get_monitors
        regions = [ScreenRegion(int(item.x), int(item.y), int(item.width), int(item.height),
                                getattr(item, "name", None) or f"display-{index}")
                   for index, item in enumerate(get_monitors())]
    except Exception:
        regions = [ScreenRegion(0, 0, 1920, 1080, "fallback")]
    return MonitorLayout(regions, mode, fixed_index)
