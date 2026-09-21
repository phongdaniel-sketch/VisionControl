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

    def test_volume_hands_off_to_drag_without_losing_preparation(self):
        for mode in ('palm','thumb_lock'):
            self.mouse=MouseController(self.adapter,replace(self.profile,pointer_mode=mode),screen=(1920,1080))
            p=PrimaryHand(self.adapter,config(DEFAULTS))
            volume=sample(thumb='tucked',fist=True,fingers=(False,)*4,pinch_ratio=1.)
            for i in range(5):p.update(volume,i*.1,self.mouse)
            self.assertEqual(p.mode,'volume')
            opened=sample(thumb='open',spread=.55,radius=.8,pinch_ratio=1.)
            p.update(opened,.45,self.mouse)
            contact=replace(opened,pinch=True,pinch_ratio=.1,fingers=(False,False,False,False))
            for t in (.5,.6):
                self.assertFalse(p.update(contact,t,self.mouse))
                self.step(pose('pinch'),t)
            self.assertTrue(self.mouse.left_down)
            self.assertFalse(p.update(volume,.7,self.mouse))
            self.mouse.release_all()

    def test_near_pinch_or_curled_fingers_cannot_enter_volume(self):
        p=PrimaryHand(self.adapter,config(DEFAULTS))
        volume=sample(thumb='open',spread=.55,radius=.8)
        self.assertNotEqual(p.candidate(replace(volume,pinch_ratio=.6)),'volume')
        self.assertNotEqual(p.candidate(replace(volume,fingers=(True,False,False,False))),'volume')

    def test_assigned_ok_keeps_priority_when_leaving_volume(self):
        cfg=config(DEFAULTS);cfg['symbols']['ok']='ctrl+c'
        p=PrimaryHand(self.adapter,cfg)
        volume=sample(thumb='tucked',fist=True,fingers=(False,)*4,pinch_ratio=1.)
        for i in range(5):p.update(volume,i*.1,self.mouse)
        self.assertEqual(p.mode,'volume')
        p.update(sample(thumb='open',spread=.55,radius=.8),.45,self.mouse)
        ok=sample(thumb='open',pinch=True,pinch_ratio=.1,symbol='ok',fingers=(False,True,True,True))
        self.assertTrue(p.update(ok,.5,self.mouse))
        self.assertEqual(p.gate.name,'symbol:ok')
        self.assertFalse(self.mouse.left_down)

    def test_palm_scroll_pose_preserves_all_curl_clicks(self):
        self.mouse=MouseController(self.adapter,replace(self.profile,pointer_mode='palm'),screen=(1920,1080))
        for curled_names, button in [(('index',), 'left'), (('index', 'middle'), 'middle')]:
            self.mouse.release_all(); self.adapter.drain()
            primary=PrimaryHand(self.adapter,config(DEFAULTS))
            open_features=sample(thumb='open',spread=.3)
            for t in (0, .10, .20, .30):
                self.assertTrue(primary.update(open_features,t,self.mouse))
            states={name:('curled' if name in curled_names else 'extended')
                    for name in ('index','middle')}
            curled_features=replace(open_features, fingers=(
                'index' not in curled_names, 'middle' not in curled_names, True, True))
            for t in (.35,.42):
                self.assertFalse(primary.update(curled_features,t,self.mouse))
                self.assertEqual(self.mouse.thumb_control.clicks.update('open',states,False,t),())
            self.assertTrue(self.mouse.thumb_control.clicks.cycle_active)
            self.assertFalse(primary.update(open_features,.50,self.mouse))
            result=self.mouse.thumb_control.clicks.update(
                'open',{'index':'extended','middle':'extended'},False,.50)
            self.assertEqual(result,(button,))
