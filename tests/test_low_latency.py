import threading
import time
import unittest
from types import SimpleNamespace
from unittest.mock import Mock,patch
import numpy as np
from vision_control.cursor_filter import CursorFilter, output_step
from vision_control.perception_worker import LatestPerception
from vision_control.runtime import VisionRuntime

class LatencyTests(unittest.TestCase):
    def test_output_easing_is_time_based_and_does_not_overshoot(self):
        def remaining(intervals):
            distance = 20.
            for dt in intervals:
                distance -= output_step(distance, 1000, dt)
            return distance
        self.assertAlmostEqual(remaining([.016, .016]), remaining([.032]))
        self.assertEqual(output_step(20, 1000, 0), 0)
        self.assertGreater(remaining([.016]), 0)
        self.assertLess(remaining([.016] * 5), 1)
        self.assertLessEqual(output_step(1000, 1000, .016), 57.6)

    def test_prediction_is_bounded_not_fed_back_and_expires(self):
        f=CursorFilter();f.update((0.,0.),0,1000);f.update((100.,0.),.03,1000)
        measured=f.value
        for t in (.04,.06,.1):
            predicted=f.predict(t,1000)
            self.assertLessEqual(abs(predicted[0]-measured[0]),20.001)
            self.assertEqual(f.value,measured)
        self.assertIsNone(f.predict(.2,1000))
        f.reset();self.assertIsNone(f.predict(.3,1000))
    def test_filter_reduces_stationary_noise_and_ignores_duplicate_time(self):
        f=CursorFilter();f.update((100.,100.),0,1000)
        values=[]
        for i in range(1,60):values.append(f.update((100+(-1)**i,100),i/30,1000)[0])
        self.assertLess(max(values)-min(values),1)
        before=f.value;f.update((999.,999.),59/30,1000);self.assertEqual(f.value,before)
    def test_latest_workers_own_resources_and_skip_backlog(self):
        seen=[];closed=[];captured=threading.Event()
        inference_started=threading.Event();backlog_ready=threading.Event()
        class Camera:
            def __init__(self,index):self.i=0
            def open(self):self.thread=threading.get_ident()
            def read(self):
                self.i+=1
                if self.i == 2: inference_started.wait(2)
                if self.i >= 10: backlog_ready.set()
                # Blocking camera I/O simulated by event wait.
                captured.wait(.002)
                return np.full((4,4,3),self.i%255,dtype=np.uint8)
            def close(self):closed.append(('camera',self.thread==threading.get_ident()))
        class Tracker:
            def __init__(self):self.thread=threading.get_ident()
            def track(self,frame,stamp):
                seen.append(stamp)
                inference_started.set()
                if len(seen) == 1: backlog_ready.wait(2)
                captured.wait(.01);return SimpleNamespace(hands=())
            def close(self):closed.append(('tracker',self.thread==threading.get_ident()))
        w=LatestPerception(Camera,Tracker,0);w.start()
        try:
            deadline=time.monotonic()+2
            while len(seen)<4 and time.monotonic()<deadline:captured.wait(.01)
            self.assertGreaterEqual(len(seen),4)
            self.assertEqual(len(seen),len(set(seen)))
            packet=w.take();self.assertIsNotNone(packet)
            self.assertGreater(w.sequence,len(seen))
        finally:w.close()
        self.assertCountEqual(closed,[('camera',True),('tracker',True)])
    def test_no_new_results_releases_after_freshness_deadline(self):
        r=VisionRuntime();r.started=True;r.perception=Mock();r.perception.take.return_value=None
        r.last_snapshot=SimpleNamespace(sample_time=1.)
        r._release_controls=Mock()
        with patch('vision_control.runtime.time.monotonic',return_value=1.2):
            self.assertIsNone(r.process_frame())
        r._release_controls.assert_called_once()
    def test_pre_resume_packet_is_rejected(self):
        r=VisionRuntime();r.started=True;r.perception=Mock();r.accept_after=1.1
        r.perception.take.return_value=(1,None,None,1.05,1.,1.)
        r._release_controls=Mock()
        with patch('vision_control.runtime.time.monotonic',return_value=1.12):
            self.assertIsNone(r.process_frame())
        r._release_controls.assert_called_once()
