"""Worker-owned capture/inference with bounded latest-only handoff; no input."""
import threading
import time

class LatestPerception:
    def __init__(self, camera_factory, tracker_factory, index):
        self.camera_factory,self.tracker_factory,self.index=camera_factory,tracker_factory,index
        self.condition=threading.Condition();self.stop=threading.Event()
        self.frame=self.result=self.error=None
        self.sequence=0
        self.threads=[]
    def start(self):
        self.threads=[threading.Thread(target=self.capture,daemon=True),threading.Thread(target=self.infer,daemon=True)]
        for t in self.threads:t.start()
    def fail(self,exc):
        with self.condition:self.error=exc;self.stop.set();self.condition.notify_all()
    def capture(self):
        camera=None
        try:
            camera=self.camera_factory(index=self.index);camera.open()
            while not self.stop.is_set():
                before=time.perf_counter();frame=camera.read();stamp=time.monotonic()
                read_ms=(time.perf_counter()-before)*1000
                with self.condition:
                    self.sequence+=1;self.frame=(self.sequence,frame,stamp,read_ms);self.condition.notify_all()
        except Exception as exc:self.fail(exc)
        finally:
            if camera is not None:camera.close()
    def infer(self):
        tracker=None;last=0
        try:
            import cv2
            tracker=self.tracker_factory()
            while not self.stop.is_set():
                with self.condition:
                    self.condition.wait_for(lambda:self.stop.is_set() or (self.frame is not None and self.frame[0]>last),timeout=.1)
                    if self.stop.is_set():break
                    if self.frame is None or self.frame[0]<=last:continue
                    last,frame,stamp,read_ms=self.frame
                if time.monotonic()-stamp>.15:continue
                before=time.perf_counter();frame=cv2.flip(frame,1)
                hands=tracker.track(frame,stamp)
                packet=(last,frame,hands,stamp,read_ms,(time.perf_counter()-before)*1000)
                with self.condition:self.result=packet
        except Exception as exc:self.fail(exc)
        finally:
            if tracker is not None:tracker.close()
    def take(self):
        with self.condition:
            if self.error:raise RuntimeError(f'Perception worker: {self.error}') from self.error
            packet,self.result=self.result,None
            return packet
    def close(self):
        self.stop.set()
        with self.condition:self.condition.notify_all()
        for t in self.threads:t.join(3)
        if any(t.is_alive() for t in self.threads):
            raise RuntimeError('Camera worker is still stopping; retry after device responds')
