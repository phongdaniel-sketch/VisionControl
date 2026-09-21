"""Current fist-volume regressions superseding the rotation experiment."""
import unittest
from dataclasses import replace
from tests.test_gesture_v1 import sample
from vision_control.controllers import MouseController
from vision_control.diagnostics import DiagnosticInputAdapter
from vision_control.gesture_v1 import PrimaryHand
from vision_control.gesture_v1_config import config
from vision_control.profile import load_profile


class FistVolumeTests(unittest.TestCase):
    def setUp(self):
        profile=load_profile('config/gesture_v1_profile.json')
        self.adapter=DiagnosticInputAdapter()
        self.mouse=MouseController(self.adapter,profile,screen=(1920,1080))
        self.primary=PrimaryHand(self.adapter,profile.gesture_v1)
        self.fist=sample(thumb='tucked',fist=True,fingers=(False,)*4,
                         pinch=True,pinch_ratio=.1,middle_pinch_ratio=.1)

    def hold(self):
        for i in range(5):self.primary.update(self.fist,i*.1,self.mouse)
        self.assertEqual(self.primary.mode,'volume')

    def test_folded_contacts_do_not_click_and_stationary_hold_is_silent(self):
        self.hold()
        for i in range(5,20):self.primary.update(self.fist,i*.1,self.mouse)
        self.assertFalse(self.adapter.events)

    def test_horizontal_direction_and_no_repeat_when_stationary(self):
        self.hold()
        right=replace(self.fist,palm=(self.fist.palm[0]+.08,self.fist.palm[1]))
        self.primary.update(right,.5,self.mouse)
        self.primary.update(right,.6,self.mouse)
        self.primary.update(self.fist,.7,self.mouse)
        keys=[e['key'] for e in self.adapter.events if e['action']=='key_down']
        self.assertEqual(keys,['media_volume_up','media_volume_down'])

    def test_vertical_motion_and_jitter_are_silent(self):
        self.hold()
        self.primary.update(replace(self.fist,palm=(self.fist.palm[0]+.01,.8)),.5,self.mouse)
        self.assertFalse(self.adapter.events)

    def test_open_hand_releases_and_never_enters_old_volume_or_zoom(self):
        self.hold()
        opened=sample(thumb='open',spread=.55,radius=.8)
        self.assertFalse(self.primary.update(opened,.5,self.mouse))
        self.assertEqual(self.primary.mode,'')
        for f in (opened,replace(opened,spread=.9),replace(opened,cluster=True)):
            self.assertNotIn(self.primary.candidate(f),('volume','zoom'))
        self.assertFalse(config({'zoom':True})['zoom'])

    def test_loss_requires_fresh_confirmation(self):
        self.hold()
        self.primary.update(None,.5,self.mouse)
        self.primary.update(self.fist,.6,self.mouse)
        self.assertEqual(self.primary.mode,'')
        self.assertFalse(self.adapter.events)

    def test_disabled_volume_and_held_drag_keep_ownership(self):
        self.primary.cfg['volume']=False
        self.assertNotEqual(self.primary.candidate(self.fist),'volume')
        self.primary.cfg['volume']=True
        self.mouse.left_down=True
        self.assertFalse(self.primary.update(self.fist,0,self.mouse))
        self.assertEqual(self.primary.mode,'')
