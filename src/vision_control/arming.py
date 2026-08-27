from dataclasses import dataclass


@dataclass(frozen=True)
class ArmingSettings:
    enabled: bool = True
    gesture: str = "fist"
    hold_seconds: float = 1.0
    release_frames: int = 4
    cooldown_seconds: float = 0.5
    auto_disarm_seconds: float = 2.0


class ArmingController:
    def __init__(self, settings: ArmingSettings):
        self.settings = settings
        self.armed = not settings.enabled
        self.hold_started: float | None = None
        self.cooldown_until = 0.0
        self.missing_since: float | None = None
        self.latched = False
        self.release_count = 0
        self.last_event: str | None = None
        self._last_progress = 0.0

    @property
    def progress(self) -> float:
        return self._last_progress

    @property
    def label(self) -> str:
        if self.hold_started is not None:
            return "DISARMING" if self.armed else "ARMING"
        return "ARMED" if self.armed else "DISARMED"

    def update(self, gesture: str, hand_present: bool, now: float) -> str | None:
        self.last_event = None
        if not self.settings.enabled:
            self.armed = True
            return None
        if not hand_present:
            self.hold_started = None
            self._last_progress = 0.0
            self.release_count = 0
            self.latched = False
            if self.missing_since is None:
                self.missing_since = now
            elif self.armed and now - self.missing_since >= self.settings.auto_disarm_seconds:
                self.armed = False
                self.last_event = "auto_disarmed"
            return self.last_event

        self.missing_since = None
        if gesture != self.settings.gesture:
            self.hold_started = None
            self._last_progress = 0.0
            if self.latched:
                self.release_count += 1
                if self.release_count >= self.settings.release_frames:
                    self.latched = False
                    self.release_count = 0
            return None

        self.release_count = 0
        if self.latched or now < self.cooldown_until:
            self._last_progress = 0.0
            return None
        if self.hold_started is None:
            self.hold_started = now
            self._last_progress = 0.0
            return None
        self._last_progress = min(1.0, max(0.0, (now - self.hold_started) / self.settings.hold_seconds))
        if now - self.hold_started >= self.settings.hold_seconds:
            self.armed = not self.armed
            self.latched = True
            self.hold_started = None
            self._last_progress = 0.0
            self.cooldown_until = now + self.settings.cooldown_seconds
            self.last_event = "armed" if self.armed else "disarmed"
        return self.last_event

    def disarm(self) -> bool:
        changed = self.armed
        self.armed = False if self.settings.enabled else True
        self.hold_started = None
        self.latched = False
        self.release_count = 0
        self.missing_since = None
        self._last_progress = 0.0
        return changed
