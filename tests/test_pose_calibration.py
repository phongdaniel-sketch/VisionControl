import json
import os
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

from tests.hand_geometry import pose
from vision_control.pose_calibration import (PoseCalibration, PoseCapture, PosePreview,
    STAGES, calibration_path, fit, load_pose_calibration, measure, save_pose_calibration)
from vision_control.profile import load_profile
from vision_control.runtime import VisionRuntime, RuntimeSnapshot
from vision_control.gesture_v1 import features
from vision_control.thumb_control import ThumbControl
from vision_control.controllers import MouseController
from vision_control.diagnostics import DiagnosticInputAdapter
from vision_control.gesture_v1 import PrimaryHand


def sample_hand(stage):
    hand = pose('four' if stage == 'tucked' else 'open')
    folded = pose('fist')
    points = list(hand.landmarks)
    for tip, name in ((8, 'index'), (12, 'middle')):
        if stage in (name, 'both'):
            for i in (tip-2, tip-1, tip):
                points[i] = folded.landmarks[i]
    if stage == 'right_contact':
        points[11], points[12] = (.465,.32,0), (.43,.40,0)
        points[4] = points[12]
    return replace(hand, landmarks=tuple(points))


def samples():
    return {s: [measure(sample_hand(s), (640,480))]*30 for s in STAGES}


def click_sequence(stage):
    opened, curled = sample_hand('open'), sample_hand(stage)
    transition = [replace(opened, landmarks=tuple(
        tuple(a+(b-a)*fraction for a,b in zip(p,q))
        for p,q in zip(opened.landmarks,curled.landmarks)))
        for fraction in (.25,.5,.75)]
    return [opened]*6 + transition + [curled]*3 + list(reversed(transition)) + [opened]*2


class PoseCalibrationTests(unittest.TestCase):
    def test_fit_recognizes_all_captured_poses(self):
        candidate = fit(samples())
        for stage in STAGES:
            hand = sample_hand(stage)
            self.assertEqual(candidate.thumb(hand, (640,480)), 'tucked' if stage == 'tucked' else 'open')
            for tip, name in ((8,'index'), (12,'middle')):
                self.assertEqual(candidate.finger(hand,tip,(640,480)),
                                 'curled' if stage in (name,'both') else 'extended')

    def test_incomplete_and_overlapping_samples_rejected(self):
        with self.assertRaises(ValueError): fit({})
        values = samples()
        values['index'] = values['open']
        with self.assertRaises(ValueError): fit(values)
        values = samples()
        values['tucked'] = values['open']
        with self.assertRaises(ValueError): fit(values)

    def test_invalid_measurements_and_thresholds_rejected(self):
        self.assertIsNone(measure(None,(640,480)))
        self.assertIsNone(measure(replace(pose(),confidence=.4),(640,480)))
        self.assertIsNone(measure(replace(pose(),confidence=float('nan')),(640,480)))
        h = pose(); points = list(h.landmarks); points[8] = (float('nan'),.5,0)
        self.assertIsNone(measure(replace(h,landmarks=tuple(points)),(640,480)))
        with self.assertRaises(ValueError): replace(fit(samples()),index_extended=float('inf')).validate()
        with self.assertRaises(ValueError): replace(fit(samples()),index_curled=160).validate()

    def test_capture_requires_continuous_unique_frames_and_duration(self):
        capture = PoseCapture(); capture.begin(0)
        for i in range(130):
            stamp = i/30
            capture.observe(sample_hand('open'),(640,480),stamp,stamp)
        self.assertIn('open',capture.samples)
        self.assertGreaterEqual(len(capture.samples['open']),20)
        self.assertEqual(capture.stage,'tucked')
        capture.begin(5)
        for _ in range(50): capture.observe(sample_hand('tucked'),(640,480),8,8)
        self.assertEqual(len(capture.pending),1)
        self.assertNotIn('tucked',capture.samples)

    def test_capture_loss_stale_and_jitter_retry_same_stage(self):
        for hand, stamp, now in ((None,3,3),(pose(),1,3),(pose(),4,3)):
            capture = PoseCapture(); capture.begin(0)
            self.assertFalse(capture.observe(hand,(640,480),stamp,now))
            self.assertIsNone(capture.deadline)
            self.assertEqual(capture.stage,'open')
        capture = PoseCapture(); capture.begin(0)
        for i in range(130):
            capture.observe(sample_hand('open' if i%2 else 'both'),(640,480),i/30,i/30)
        self.assertFalse(capture.samples)
        self.assertIn('steady',capture.message)

    def test_countdown_allows_hand_to_leave_mouse_before_capture(self):
        capture = PoseCapture(); capture.begin(10)
        for now in (10,11,12,12.9):
            self.assertFalse(capture.observe(None,(640,480),0,now))
            self.assertEqual(capture.deadline,13)
        self.assertFalse(capture.observe(None,(640,480),13,13))
        self.assertIsNone(capture.deadline)
        self.assertFalse(capture.samples)

    def test_persistence_validation_and_atomic_failure(self):
        candidate = fit(samples())
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/'pose.json'
            self.assertIsNone(load_pose_calibration(path))
            save_pose_calibration(path,candidate)
            self.assertEqual(load_pose_calibration(path),candidate)
            original = path.read_bytes()
            with patch('vision_control.pose_calibration.os.replace',side_effect=OSError('disk')):
                with self.assertRaises(OSError): save_pose_calibration(path,candidate)
            self.assertEqual(path.read_bytes(),original)
            self.assertFalse(path.with_suffix('.json.tmp').exists())
            for value in ('bad json','[]','null','{"version":2}',json.dumps({'version':1,'thresholds':{}})):
                path.write_text(value)
                self.assertIsNone(load_pose_calibration(path))

    def test_assignment_has_separate_file(self):
        p = load_profile('config/gesture_v1_profile.json')
        self.assertNotEqual(calibration_path('.',p),calibration_path('.',replace(p,swap_hands=not p.swap_hands)))
        self.assertNotEqual(calibration_path('.',p),calibration_path('.',replace(p,mouse_hand='Left' if p.mouse_hand=='Right' else 'Right')))

    def test_preview_clicks_require_full_cycles_and_tucked_thumb(self):
        preview = PosePreview(fit(samples()),{})
        t = 0.
        for stage, button in (('index','left'),('both','middle'),('right_contact','right')):
            result = []
            for state in ['open']*6+[stage]*3+['open']*2:
                t += .04
                result.extend(preview.update(sample_hand(state),(640,480),t,t))
            self.assertEqual(result,[button])
        self.assertFalse(preview.complete)
        t += .04
        preview.update(sample_hand('tucked'),(640,480),t,t)
        self.assertTrue(preview.complete)

    def test_preview_loss_resets_cycle_without_click(self):
        preview = PosePreview(fit(samples()),{})
        for i,state in enumerate(['open']*6+['index']*3):
            preview.update(sample_hand(state),(640,480),i*.04,i*.04)
        preview.update(None,(640,480),.4,.4)
        self.assertEqual(preview.update(sample_hand('open'),(640,480),.44,.44),())
        self.assertFalse(preview.seen)

    def test_primary_and_mouse_share_calibrated_states(self):
        p = load_profile('config/gesture_v1_profile.json')
        candidate = fit(samples())
        for stage in STAGES:
            h = sample_hand(stage)
            f = features(h,(640,480),p.gesture_v1,candidate)
            self.assertEqual(f.thumb,candidate.thumb(h,(640,480)))
            for i,tip in enumerate((8,12)):
                self.assertEqual(f.fingers[i],ThumbControl.finger(h,tip,(640,480),candidate)=='extended')

    def test_calibrated_clicks_through_primary_arbitration_in_both_modes(self):
        p = load_profile('config/gesture_v1_profile.json')
        for mode in ('palm','thumb_lock'):
            for stage, button in (('index','left'),('both','middle'),('right_contact','right')):
                adapter = DiagnosticInputAdapter()
                mouse = MouseController(adapter,replace(p,pointer_mode=mode),screen=(1920,1080))
                mouse.pose_calibration = fit(samples())
                primary = PrimaryHand(adapter,p.gesture_v1)
                for i,h in enumerate(click_sequence(stage)):
                    now = i*.04
                    with patch('time.monotonic',return_value=now):
                        f = features(h,(640,480),p.gesture_v1,mouse.pose_calibration)
                        if not primary.update(f,now,mouse):
                            mouse.update(h,(640,480))
                buttons = [e['button'] for e in adapter.events if e['action']=='button_down']
                self.assertEqual(buttons,[button],(mode,stage))
                self.assertFalse(adapter.held_buttons)


class PoseRuntimeTests(unittest.TestCase):
    def setUp(self):
        self.runtime = VisionRuntime()
        self.runtime.profile = replace(load_profile('config/gesture_v1_profile.json'),pointer_mode='palm',swap_hands=False)
        self.runtime.mouse = SimpleNamespace(release_all=Mock(),pose_calibration=None)
        self.runtime.started = True

    def test_start_blocks_resume_and_cancel_preserves_previous(self):
        old = fit(samples()); self.runtime.mouse.pose_calibration = old
        self.runtime.start_pose_calibration()
        self.assertTrue(self.runtime.paused)
        self.runtime.mouse.release_all.assert_called()
        self.runtime.set_paused(False)
        self.runtime.toggle_paused()
        self.runtime.start_calibration()
        self.assertTrue(self.runtime.paused)
        self.assertFalse(self.runtime.calibration_session.active)
        self.runtime.finish_pose_calibration()
        self.assertIs(self.runtime.mouse.pose_calibration,old)
        self.assertTrue(self.runtime.paused)

    def test_save_failure_preserves_live_thresholds(self):
        self.runtime.start_pose_calibration()
        with patch('vision_control.runtime.save_pose_calibration',side_effect=OSError('disk')):
            with self.assertRaises(OSError): self.runtime.save_pose_calibration(fit(samples()))
        self.assertIsNone(self.runtime.mouse.pose_calibration)
        self.assertTrue(self.runtime.pose_calibrating)
        self.assertTrue(self.runtime.paused)

    def test_save_reload_reset_preserve_movement(self):
        self.runtime.mouse.calibration = object()
        old = self.runtime.mouse.calibration
        with tempfile.TemporaryDirectory() as directory, patch('vision_control.runtime.runtime_data_dir',return_value=Path(directory)):
            candidate = fit(samples()); self.runtime.start_pose_calibration()
            self.runtime.save_pose_calibration(candidate)
            path = calibration_path(directory,self.runtime.profile)
            self.assertEqual(load_pose_calibration(path),candidate)
            self.assertFalse(self.runtime.pose_calibrating)
            self.assertTrue(self.runtime.paused)
            self.runtime.start_pose_calibration(); self.runtime.reset_pose_calibration()
            self.assertFalse(path.exists())
            self.assertIsNone(self.runtime.mouse.pose_calibration)
            self.assertIs(self.runtime.mouse.calibration,old)

    def test_dialog_cancel_and_incomplete_save(self):
        os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
        from PySide6.QtWidgets import QApplication
        from vision_control.pose_calibration_ui import PoseCalibrationDialog
        app = QApplication.instance() or QApplication([])
        self.runtime.start_pose_calibration()
        dialog = PoseCalibrationDialog(self.runtime)
        dialog.timer.stop()
        self.runtime.save_pose_calibration = Mock()
        dialog.save()
        self.runtime.save_pose_calibration.assert_not_called()
        self.assertFalse(dialog.save_button.isEnabled())
        dialog.reject()
        self.assertFalse(self.runtime.pose_calibrating)
        self.assertTrue(self.runtime.paused)
        dialog.deleteLater()

    def test_dialog_full_capture_rehearsal_and_explicit_save(self):
        os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
        import numpy as np
        from PySide6.QtWidgets import QApplication
        from vision_control.pose_calibration_ui import PoseCalibrationDialog
        app = QApplication.instance() or QApplication([])
        self.runtime.start_pose_calibration()
        dialog = PoseCalibrationDialog(self.runtime)
        dialog.timer.stop()
        self.addCleanup(dialog.reject)
        now = 0.

        def tick(stage, stamp):
            hand = replace(sample_hand(stage),label=self.runtime.profile.mouse_hand)
            self.runtime.last_snapshot = RuntimeSnapshot(
                np.zeros((480,640,3),dtype=np.uint8),True,'Right','Left','paused',
                (hand,),True,False,'paused','Display','Idle',0.,sample_time=stamp)
            with patch('vision_control.pose_calibration_ui.time.monotonic',return_value=stamp):
                dialog.tick()

        for stage in STAGES:
            self.assertEqual(dialog.capture.stage,stage)
            with patch('vision_control.pose_calibration_ui.time.monotonic',return_value=now):
                dialog.begin_capture()
            for i in range(132): tick(stage,now+i/30)
            self.assertEqual(dialog.review_stage,stage)
            self.assertTrue(dialog.next_button.isEnabled())
            self.assertFalse(dialog.capture_button.isEnabled())
            dialog.next_step()
            now += 4.4
        self.assertIsNotNone(dialog.rehearsal)
        self.assertFalse(dialog.save_button.isEnabled())
        self.assertIsNone(self.runtime.mouse.pose_calibration)
        tick('tucked',now)
        for stage in ('index','both','right_contact'):
            for state in ['open']*6+[stage]*3+['open']*2:
                now += .04; tick(state,now)
        self.assertTrue(dialog.save_button.isEnabled())
        self.assertIsNone(self.runtime.mouse.pose_calibration)
        with tempfile.TemporaryDirectory() as directory, patch('vision_control.runtime.runtime_data_dir',return_value=Path(directory)):
            dialog.save()
            self.assertIsNotNone(self.runtime.mouse.pose_calibration)
            self.assertTrue(calibration_path(directory,self.runtime.profile).exists())
        self.assertFalse(self.runtime.pose_calibrating)
        self.assertTrue(self.runtime.paused)

    def test_dialog_retry_keeps_prior_steps_and_requires_confirmation(self):
        os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
        from PySide6.QtWidgets import QApplication
        from vision_control.pose_calibration_ui import PoseCalibrationDialog
        app = QApplication.instance() or QApplication([])
        self.runtime.start_pose_calibration()
        dialog = PoseCalibrationDialog(self.runtime)
        dialog.timer.stop()
        try:
            dialog.capture.samples = {s:values for s,values in samples().items() if s in ('open','tucked')}
            dialog.review_stage = 'tucked'
            dialog.refresh_stage()
            self.assertTrue(dialog.retry_button.isEnabled())
            self.assertFalse(dialog.capture_button.isEnabled())
            dialog.retry_step()
            self.assertEqual(set(dialog.capture.samples),{'open'})
            self.assertEqual(dialog.capture.stage,'tucked')
            self.assertTrue(dialog.capture_button.isEnabled())
            self.assertFalse(dialog.next_button.isEnabled())
            self.assertIn('2/5',dialog.title.text())
            self.assertFalse(dialog.save_button.isEnabled())
        finally:
            dialog.reject()

    def test_schematic_has_distinct_poses(self):
        os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
        from PySide6.QtWidgets import QApplication
        from vision_control.pose_guide import PoseExample, GUIDE
        app = QApplication.instance() or QApplication([])
        widget = PoseExample()
        try:
            rendered = []
            for stage in STAGES:
                widget.set_stage(stage)
                image = widget.grab().toImage()
                self.assertFalse(image.isNull())
                rendered.append(image)
                self.assertEqual(len(GUIDE[stage][1]),3)
            for i in range(len(rendered)):
                for j in range(i):
                    self.assertNotEqual(rendered[i],rendered[j])
        finally:
            widget.close()

    def test_runtime_frames_never_emit_input_while_calibrating(self):
        import numpy as np
        from vision_control.monitors import MonitorLayout, ScreenRegion
        from vision_control.types import HandsFrame
        adapter = DiagnosticInputAdapter()
        camera = Mock(); camera.read.return_value = np.zeros((480,640,3),dtype=np.uint8)
        tracker = Mock()
        tracker.track.side_effect = lambda frame,stamp: HandsFrame(stamp,(pose('fist'),),640,480)
        runtime = VisionRuntime(0,True,'config/gesture_v1_profile.json',camera_factory=lambda **kw:camera,
            tracker_factory=lambda:tracker,adapter_factory=lambda:adapter)
        with tempfile.TemporaryDirectory() as directory, patch('vision_control.runtime.runtime_data_dir',return_value=Path(directory)), patch(
                'vision_control.runtime.discover_monitors',return_value=MonitorLayout([ScreenRegion(0,0,1920,1080)],'fixed')):
            profile = load_profile('config/gesture_v1_profile.json')
            candidate = fit(samples())
            save_pose_calibration(calibration_path(directory,profile),candidate)
            runtime.start()
            self.assertEqual(runtime.mouse.pose_calibration,candidate)
        try:
            runtime.start_pose_calibration()
            adapter.drain()
            for i in range(30):
                with patch('time.monotonic',return_value=i*.05):
                    runtime.set_paused(False)
                    runtime.process_frame()
                    runtime.cursor_tick()
            self.assertTrue(runtime.paused)
            self.assertFalse(adapter.held_keys)
            self.assertFalse(adapter.held_buttons)
            self.assertFalse([e for e in adapter.events if e['action'] in ('button_down','key_down','move','scroll')])
        finally:
            runtime.close()


if __name__ == '__main__':
    unittest.main()
