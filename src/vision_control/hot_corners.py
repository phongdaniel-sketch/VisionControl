"""Pointer-only corner dwell, independent of gesture arbitration."""
class HotCorners:
    def __init__(self):
        self.key = None
        self.started = None
        self.latched = False
        self.progress = 0.

    def update(self, point, region, bindings, now, dwell=.7, blocked=False):
        x, y = point
        margin = 12
        side = 'left' if x < region.x+margin else 'right' if x >= region.x+region.width-margin else ''
        edge = 'top' if y < region.y+margin else 'bottom' if y >= region.y+region.height-margin else ''
        name = edge+'_'+side if region.contains(point) and side and edge else ''
        action = bindings.get(name, '')
        key = (region.x, region.y, region.width, region.height, name, action) if action else None
        self.progress = 0.
        if key != self.key:
            self.key, self.started, self.latched = key, now, False
        if key is None:
            return None
        if blocked:
            self.latched = True  # Require exit after a drag, pause or modal dialog.
        if self.latched:
            return None
        self.progress = min(1., max(0., now-self.started)/dwell)
        if self.progress >= 1.:
            self.latched = True
            return action
        return None
