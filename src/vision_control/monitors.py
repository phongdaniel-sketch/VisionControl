from dataclasses import dataclass


@dataclass(frozen=True)
class ScreenRegion:
    x: int
    y: int
    width: int
    height: int
    name: str = "display"
    is_primary: bool = False

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


class EdgeDwellSwitcher:
    def __init__(self, regions: list[ScreenRegion], edge_zone: float = .08,
                 dwell_seconds: float = .8):
        if not 0 < edge_zone < .5:
            raise ValueError("edge_zone must be between zero and 0.5")
        if dwell_seconds <= 0:
            raise ValueError("dwell_seconds must be greater than zero")
        self.regions = sorted(regions, key=lambda item: (
            item.x + item.width / 2, item.y + item.height / 2))
        self.edge_zone = edge_zone
        self.dwell_seconds = dwell_seconds
        self.pending_edge: str | None = None
        self.started_at: float | None = None
        self.latched = False
        self.progress = 0.0

    def update(self, normalized_x: float | None, current: ScreenRegion, now: float,
               active: bool = True) -> ScreenRegion | None:
        edge = None
        if normalized_x is not None:
            if normalized_x <= self.edge_zone:
                edge = "left"
            elif normalized_x >= 1.0 - self.edge_zone:
                edge = "right"
        if edge is None:
            self.reset()
            return None
        if not active:
            self.pending_edge = None
            self.started_at = None
            self.progress = 0.0
            return None
        if self.latched:
            return None
        if edge != self.pending_edge:
            self.pending_edge = edge
            self.started_at = now
            self.progress = 0.0
            return None
        elapsed = max(0.0, now - (self.started_at if self.started_at is not None else now))
        self.progress = min(1.0, elapsed / self.dwell_seconds)
        if elapsed < self.dwell_seconds:
            return None
        self.latched = True
        return self._adjacent(current, -1 if edge == "left" else 1)

    def _adjacent(self, current: ScreenRegion, offset: int) -> ScreenRegion | None:
        try:
            index = self.regions.index(current)
        except ValueError:
            return None
        target = index + offset
        return self.regions[target] if 0 <= target < len(self.regions) else None

    def reset(self) -> None:
        self.pending_edge = None
        self.started_at = None
        self.latched = False
        self.progress = 0.0


def discover_monitors(mode: str = "active", fixed_index: int = 0) -> MonitorLayout:
    try:
        from screeninfo import get_monitors
        monitors = sorted(get_monitors(),
                          key=lambda item: not bool(getattr(item, "is_primary", False)))
        regions = [ScreenRegion(
            int(item.x), int(item.y), int(item.width), int(item.height),
            getattr(item, "name", None) or f"display-{index}",
            bool(getattr(item, "is_primary", False)),
        ) for index, item in enumerate(monitors)]
    except Exception:
        regions = [ScreenRegion(0, 0, 1920, 1080, "fallback")]
    return MonitorLayout(regions, mode, fixed_index)
