"""One Euro position filter; prediction never becomes a measured sample."""
import math


def output_step(distance, diagonal, elapsed):
    """Short, time-based easing; duplicate ticks cannot accelerate the cursor."""
    dt = max(0., min(elapsed, .05))
    return min(distance * -math.expm1(-dt / .018), diagonal * 3.6 * dt)


class CursorFilter:
    def __init__(self):self.reset()
    def reset(self):
        self.stamp=None;self.raw=self.value=None;self.velocity=(0.,0.)
    @staticmethod
    def alpha(cutoff,dt):return 1/(1+1/(2*math.pi*cutoff*dt))
    def update(self,point,stamp,scale):
        if self.stamp is None or stamp-self.stamp>.15:
            self.stamp=stamp;self.raw=self.value=point;self.velocity=(0.,0.);return point
        dt=stamp-self.stamp
        if dt<=0:return self.value
        measured=tuple((b-a)/dt for a,b in zip(self.raw,point))
        a=self.alpha(1.,dt)
        self.velocity=tuple(max(-scale*3,min(scale*3,v+a*(m-v))) for v,m in zip(self.velocity,measured))
        cutoff=1.5+4*math.hypot(*self.velocity)/max(scale,1)
        a=self.alpha(cutoff,dt)
        self.value=tuple(v+a*(p-v) for v,p in zip(self.value,point))
        self.raw=point;self.stamp=stamp
        return self.value
    def predict(self,now,scale):
        if self.stamp is None:return None
        age=now-self.stamp
        if age<0 or age>.15:return None
        horizon=min(age,.03)
        # At rest avoid turning small derivative noise into visible drift.
        if math.hypot(*self.velocity)<scale*.02:return self.value
        delta=tuple(v*horizon for v in self.velocity);length=math.hypot(*delta)
        factor=min(1.,scale*.02/max(length,1e-9))
        return tuple(p+d*factor for p,d in zip(self.value,delta))
