import unittest
from dataclasses import replace
from unittest.mock import patch

from tests.test_pose_calibration import sample_hand, samples, fit
from vision_control.controllers import MouseController
from vision_control.diagnostics import DiagnosticInputAdapter
from vision_control.gesture_v1 import PrimaryHand, features
from vision_control.locked_clicks import ContactClick
from vision_control.pose_calibration import PosePreview
from vision_control.profile import load_profile


class ContactRightClickTests(unittest.TestCase):
    def setUp(self):
        self.profile = load_profile('config/gesture_v1_profile.json')
        self.adapter = DiagnosticInputAdapter()
        self.mouse = MouseController(self.adapter,self.profile,screen=(1920,1080))

    def step(self,hand,now):
        with patch('time.monotonic',return_value=now):
            self.mouse.update(hand,(640,480))

    def downs(self):
        return [e['button'] for e in self.adapter.events if e['action']=='button_down']

    def test_contact_latch_fires_on_touch_not_release_and_rearms(self):
        latch = ContactClick()
        self.assertFalse(latch.update(True,False))
        self.assertFalse(latch.update(False,True))
        self.assertTrue(latch.update(True,False))
        for _ in range(50):self.assertFalse(latch.update(True,False))
        self.assertFalse(latch.update(False,False))
        self.assertFalse(latch.update(True,False))
        self.assertFalse(latch.update(False,True))
        self.assertTrue(latch.update(True,False))

    def test_mouse_immediate_contact_freezes_and_holds_without_repeats(self):
        for mode in ('palm','thumb_lock'):
            self.mouse = MouseController(self.adapter,replace(self.profile,pointer_mode=mode),screen=(1920,1080))
            self.adapter.drain()
            self.step(sample_hand('open'),0)
            position = self.adapter.position()
            self.step(sample_hand('right_contact'),.1)
            self.assertEqual(self.downs(),['right'])
            self.assertEqual(self.mouse.status,'right_click')
            self.assertFalse(self.adapter.held_buttons)
            for i in range(1,50):
                self.step(sample_hand('right_contact'),.1+i*.02)
            self.assertEqual(self.downs(),['right'])
            self.assertEqual(self.adapter.position(),position)
            self.step(sample_hand('open'),1.2)
            self.assertEqual(self.downs(),['right'])
            self.step(sample_hand('right_contact'),1.3)
            self.assertEqual(self.downs(),['right','right'])

    def test_hand_loss_and_cold_contact_need_separation(self):
        self.step(sample_hand('right_contact'),0)
        self.assertFalse(self.downs())
        self.step(sample_hand('open'),.1)
        self.step(sample_hand('right_contact'),.2)
        self.step(None,.3)
        self.step(sample_hand('right_contact'),.4)
        self.assertEqual(self.downs(),['right'])
        self.step(sample_hand('open'),.5)
        self.step(sample_hand('right_contact'),.6)
        self.assertEqual(self.downs(),['right','right'])

    def test_ambiguous_three_tip_contact_never_clicks_or_drags(self):
        hand = sample_hand('right_contact'); points = list(hand.landmarks)
        points[8] = points[4]
        ambiguous = replace(hand,landmarks=tuple(points))
        self.step(sample_hand('open'),0)
        for t in (.1,.2,.3):self.step(ambiguous,t)
        self.assertFalse(self.downs())
        self.step(sample_hand('right_contact'),.4)
        self.assertFalse(self.downs())
        self.step(sample_hand('open'),.5)
        self.step(sample_hand('right_contact'),.6)
        self.assertEqual(self.downs(),['right'])

    def test_active_left_drag_wins_and_never_emits_right(self):
        from tests.hand_geometry import pose
        self.step(pose('four'),0)
        self.step(pose('pinch'),.1);self.step(pose('pinch'),.21)
        self.assertTrue(self.mouse.left_down)
        hand = pose('pinch');points=list(hand.landmarks);points[12]=points[4]
        self.step(replace(hand,landmarks=tuple(points)),.25)
        self.assertEqual(self.downs(),['left'])
        self.assertTrue(self.mouse.left_down)
        self.step(sample_hand('right_contact'),.3)
        self.step(sample_hand('right_contact'),.41)
        self.step(sample_hand('right_contact'),.45)
        self.assertEqual(self.downs(),['left'])
        self.assertFalse(self.adapter.held_buttons)

    def test_contact_wins_over_primary_motion_and_symbol_arbitration(self):
        for mode in ('scroll','volume','zoom'):
            self.mouse.release_all();self.adapter.drain()
            primary = PrimaryHand(self.adapter,self.profile.gesture_v1)
            opened = features(sample_hand('open'),(640,480),self.profile.gesture_v1)
            primary.update(opened,0,self.mouse)
            primary.mode = mode
            contact = features(sample_hand('right_contact'),(640,480),self.profile.gesture_v1)
            self.assertFalse(primary.update(contact,.1,self.mouse))
            self.assertEqual(primary.mode,'')
            self.step(sample_hand('right_contact'),.1)
            self.assertEqual(self.downs(),['right'])

    def test_preview_uses_contact_not_curl_for_right(self):
        preview = PosePreview(fit(samples()),self.profile.thresholds)
        self.assertEqual(preview.update(sample_hand('open'),(640,480),0,0),())
        self.assertEqual(preview.update(sample_hand('right_contact'),(640,480),.1,.1),('right',))
        self.assertEqual(preview.update(sample_hand('right_contact'),(640,480),.2,.2),())
        self.assertEqual(preview.update(sample_hand('open'),(640,480),.3,.3),())

    def test_failed_right_release_retains_flag_for_safety_retry(self):
        self.step(sample_hand('open'),0)
        with patch.object(self.adapter,'button_up',side_effect=RuntimeError('retry')):
            with self.assertRaises(RuntimeError):self.step(sample_hand('right_contact'),.1)
        self.assertTrue(self.mouse.right_down)
        self.mouse.release_all()
        self.assertFalse(self.mouse.right_down)
        self.assertFalse(self.adapter.held_buttons)


if __name__ == '__main__':
    unittest.main()
