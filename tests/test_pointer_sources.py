import unittest
from dataclasses import replace
from unittest.mock import Mock, patch
from vision_control.calibration import pointer_point, calibration_filename
from vision_control.controllers import MouseController
from vision_control.profile import load_profile
from vision_control.diagnostics import DiagnosticInputAdapter
from vision_control.gesture_v1 import PrimaryHand
from vision_control.gesture_v1_config import config, DEFAULTS
from tests.hand_geometry import pose
from tests.test_gesture_v1 import sample


class PointerSourceTests(unittest.TestCase):
    def setUp(self):
        self.profile=load_profile('config/gesture_v1_profile.json')
        self.adapter=DiagnosticInputAdapter()
        self.mouse=MouseController(self.adapter,self.profile,screen=(1920,1080))

    def step(self,hand,t):
        with patch('time.monotonic',return_value=t):self.mouse.update(hand,(640,480))

    def test_palm_uses_center_not_index_and_does_not_lock(self):
        h=pose('open');self.mouse.thumb_control.move=Mock()
        self.step(h,0)
        target=self.mouse.thumb_control.move.call_args.args[0]
        center=pointer_point(h,'palm')
        self.assertEqual(target,self.mouse.calibration.map_to_region(*center[:2],self.mouse.target_region))
        points=list(h.landmarks);points[8]=(.4,.10,0)
        self.step(replace(h,landmarks=tuple(points)),.1)
        self.assertEqual(self.mouse.thumb_control.move.call_args.args[0],target)
        self.assertEqual(self.mouse.status,'move')

    def test_palm_clicks_allow_movement(self):
        h=pose('open');self.step(h,0);self.step(h,.13)
        start=self.adapter.position()
        folded=pose('fist');points=list(h.landmarks)
        for i in (6,7,8):points[i]=folded.landmarks[i]
        curled=replace(h,landmarks=tuple(points))
        self.step(curled,.2);self.step(curled,.27)
        moved=replace(h,landmarks=tuple((x+.05,y,z) for x,y,z in h.landmarks))
        self.step(moved,.3)
        self.assertNotEqual(self.adapter.position(),start)
        self.assertEqual([e['button'] for e in self.adapter.events if e['action']=='button_down'],['left'])
        self.assertFalse(self.adapter.held_buttons)

    def test_scroll_pose_reserves_palm_but_spread_hand_does_not(self):
        p=PrimaryHand(self.adapter,config(DEFAULTS))
        f=sample(thumb='open')
        self.assertTrue(p.update(f,0,self.mouse))
        self.assertEqual(self.adapter.position(),(320.,240.))
        p.reset()
        wide=sample(thumb='open',spread=.9,radius=1.4)
        for i in range(8):
            self.assertFalse(p.update(wide,i*.1,self.mouse))
        self.assertFalse(self.adapter.events)

    def test_palm_and_index_keep_drag_latch(self):
        for mode in ('palm','thumb_lock'):
            self.mouse=MouseController(self.adapter,replace(self.profile,pointer_mode=mode),screen=(1920,1080))
            self.step(pose('four'),0);start=self.adapter.position()
            self.step(pose('pinch'),.1);self.step(pose('pinch'),.21)
            self.assertEqual(self.adapter.held_buttons,{'left'})
            self.assertEqual(self.adapter.position(),start)
            self.step(pose('point'),.3);self.assertTrue(self.adapter.held_buttons)
            self.step(pose('point'),.41);self.assertFalse(self.adapter.held_buttons)

    def test_ok_assignment_and_active_drag_in_both_sources(self):
        for mode in ('palm','thumb_lock'):
            self.mouse=MouseController(self.adapter,replace(self.profile,pointer_mode=mode),screen=(1920,1080))
            cfg=config(DEFAULTS);f=sample(pinch=True,symbol='ok',fingers=(False,True,True,True))
            p=PrimaryHand(self.adapter,cfg)
            self.assertFalse(p.update(f,0,self.mouse))
            cfg['symbols']['ok']='ctrl+c';p=PrimaryHand(self.adapter,cfg)
            self.assertTrue(p.update(f,0,self.mouse))
            self.mouse.left_down=True
            self.assertFalse(p.update(f,.05,self.mouse))
            self.mouse.release_all()

    def test_calibration_is_separate_and_uses_palm_landmarks(self):
        h=pose('open')
        self.assertNotEqual(pointer_point(h,'palm'),pointer_point(h,'thumb_lock'))
        self.assertEqual(calibration_filename('thumb_lock'),'mouse_calibration.json')
        self.assertEqual(calibration_filename('palm'),'mouse_calibration_palm.json')
