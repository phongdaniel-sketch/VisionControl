"""Deterministic curl/re-extension cycles while thumb lock is confirmed."""
class LockedFingerClicks:
    def __init__(self): self.reset()

    def reset(self):
        self.locked = False
        self.open_since = None
        self.clear_cycle()

    def clear_cycle(self):
        self.ready = {}
        self.members = set()
        self.curled_at = {}
        self.confirmed = set()
        self.started = None

    def update(self, thumb, fingers, pinching, now):
        if thumb == 'tucked':
            self.reset(); return ()
        if thumb != 'open':
            self.open_since = None
            self.clear_cycle(); return ()
        if not self.locked:
            if self.open_since is None: self.open_since = now
            if now-self.open_since < .12: return ()
            self.locked = True
        if pinching:
            self.clear_cycle(); return ()
        if self.started is not None and now-self.started > .8:
            self.clear_cycle(); return ()
        for finger in ('index', 'middle'):
            state = fingers[finger]
            if state == 'unknown':
                # A bending finger crosses an intermediate angle; keep the
                # bounded cycle, but never confirm or emit from that sample.
                continue
            if state == 'extended' and finger not in self.members:
                self.ready[finger] = now
            if state == 'curled' and finger not in self.members:
                ready = self.ready.get(finger)
                if ready is not None and now-ready <= .5:
                    if self.started is None: self.started = now
                    if now-self.started > .12:
                        self.clear_cycle(); return ()
                    self.members.add(finger)
                    self.curled_at[finger] = now
            if state == 'curled' and finger in self.members:
                if now-self.curled_at[finger]+1e-9 >= .06:
                    self.confirmed.add(finger)
        if self.members and all(fingers[f] == 'extended' for f in self.members):
            complete = self.confirmed == self.members
            button = ('right' if len(self.members)==2 else
                      'left' if 'index' in self.members else 'middle')
            self.clear_cycle()
            return (button,) if complete else ()
        return ()
