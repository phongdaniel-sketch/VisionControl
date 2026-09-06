import math
import unittest
from dataclasses import replace
from types import SimpleNamespace
from unittest.mock import Mock
from vision_control.gesture_v1 import Features, PrimaryHand, SecondHand, features
from vision_control.gesture_v1_config import config, DEFAULTS
from vision_control.diagnostics import DiagnosticInputAdapter
from vision_control.monitors import ScreenRegion


def sample(**values):
    base = Features((.5,.5),(.5,.3),.2,.3,1.,0.,(True,True,True,True),
                    'tucked',False,False,'',False,True)
    return replace(base, **values)


class GestureV1Tests(unittest.TestCase):
    def setUp(self):
        self.cfg = config(DEFAULTS)
        self.adapter = DiagnosticInputAdapter()
        self.region = ScreenRegion(-1920,0,1920,1080,'test')
        self.mouse = SimpleNamespace(left_down=False,right_down=False,middle_down=False,
            profile=SimpleNamespace(pointer_mode='thumb_lock'),
            release_all=Mock(),thumb_control=SimpleNamespace(predict_enabled=True,
                clicks=Mock(),pending_at=None),layout=SimpleNamespace(target=lambda _:self.region))

    def test_modifier_waits_and_release_is_immediate(self):
        s = SecondHand(self.adapter,self.cfg); f = sample(fist=True,fingers=(False,)*4)
        for t in (0,.4,.99):s.update(f,t,True)
        self.assertFalse(self.adapter.held_keys)
        s.update(f,1.,True); self.assertEqual(self.adapter.held_keys,{'ctrl'})
        s.update(None,1.01,True);self.assertFalse(self.adapter.held_keys)
        s.update(f,2.,True);s.update(f,3.,True);s.update(f,3.1,False)
        self.assertFalse(self.adapter.held_keys)

    def test_shift_and_five_binding_are_exclusive(self):
        self.cfg['bindings']['5']={'type':'press','keys':'f'}
        s=SecondHand(self.adapter,self.cfg)
        s.update(sample(),0,True);s.update(sample(),1,True)
        self.assertEqual(self.adapter.held_keys,{'shift'})
        wide=sample(thumb='open',spread=.9)
        s.update(wide,1.1,True);self.assertFalse(self.adapter.held_keys)
        s.update(wide,1.5,True);s.update(wide,2,True)
        down=[e['key'] for e in self.adapter.events if e['action']=='key_down']
        self.assertEqual(down,['shift','f'])

    def test_symbol_single_shot_and_drag_owns_pose(self):
        self.cfg['symbols']['ok']='ctrl+c'
        p=PrimaryHand(self.adapter,self.cfg);f=sample(symbol='ok',pinch=True)
        p.update(f,0,self.mouse);p.update(f,.1,self.mouse)
        for i in range(2,12):p.update(f,i*.1,self.mouse)
        self.assertEqual(len([e for e in self.adapter.events if e['action']=='key_down']),2)
        self.mouse.left_down=True
        self.assertFalse(p.update(f,1.2,self.mouse))

    def test_scroll_locks_pointer_and_emits_horizontal(self):
        p=PrimaryHand(self.adapter,self.cfg);f=sample(thumb='open')
        for i in range(5):self.assertFalse(p.update(f,i*.1,self.mouse))
        p.update(replace(f,palm=(.55,.5)),.5,self.mouse)
        self.assertIn('scroll_xy',[e['action'] for e in self.adapter.events])
        event=next(e for e in self.adapter.events if e['action']=='scroll_xy')
        self.assertGreater(event['x'],0);self.assertEqual(event['y'],0)
        self.assertFalse(self.mouse.thumb_control.predict_enabled)

    def test_stationary_scroll_pose_does_not_steal_curl_click(self):
        p=PrimaryHand(self.adapter,self.cfg);f=sample(thumb='open')
        for i in range(5):self.assertFalse(p.update(f,i*.1,self.mouse))
        curled=replace(f,fingers=(False,True,True,True))
        self.assertFalse(p.update(curled,.5,self.mouse))
        self.mouse.release_all.assert_not_called()
        self.mouse.thumb_control.clicks.clear_cycle.assert_not_called()

    def test_fist_switch_once_until_release(self):
        self.cfg['fist_switch']=True;p=PrimaryHand(self.adapter,self.cfg)
        f=sample(fist=True,fingers=(False,)*4)
        for i in range(41):p.update(f,i*.1,self.mouse)
        self.assertFalse(p.two_hands)
        p.update(sample(fingers=(True,False,False,False)),4.1,self.mouse)
        for i in range(42,74):p.update(f,i*.1,self.mouse)
        self.assertTrue(p.two_hands)

    def test_corner_double_fist_and_negative_coordinates(self):
        self.cfg['corners']['top_left']='r';self.cfg['fist_switch']=True
        self.adapter.cursor=(-1918,2);p=PrimaryHand(self.adapter,self.cfg)
        fist=sample(fist=True,fingers=(False,)*4);opened=sample()
        for f,t in [(fist,0),(fist,.1),(fist,.2),(opened,.3),(opened,.4),
                    (opened,.5),(fist,.6),(fist,.7),(fist,.8),(opened,.9),
                    (opened,1.),(opened,1.1)]:p.update(f,t,self.mouse)
        self.assertEqual([e['key'] for e in self.adapter.events if e['action']=='key_down'],['r'])
        self.assertTrue(p.two_hands)

    def test_zoom_and_volume_directions(self):
        p=PrimaryHand(self.adapter,self.cfg);wide=sample(thumb='open',spread=.9,radius=1.4)
        for i in range(5):p.update(wide,i*.1,self.mouse)
        p.update(replace(wide,radius=1.,cluster=True),.5,self.mouse)
        keys=[e['key'] for e in self.adapter.events if e['action']=='key_down']
        self.assertIn('=',keys)
        p.reset();self.adapter.events.clear()
        f=sample(thumb='open',spread=.55,radius=.8,angle=math.radians(175))
        for i in range(5):p.update(f,1+i*.1,self.mouse)
        p.update(replace(f,angle=math.radians(-160)),1.5,self.mouse)
        self.assertIn('media_volume_up',[e['key'] for e in self.adapter.events if e['action']=='key_down'])

    def test_actions_preserve_modifier_owner(self):
        self.adapter.key_down('ctrl');self.adapter.perform('ctrl+c')
        self.assertEqual(self.adapter.held_keys,{'ctrl'})

    def test_landmark_jump_is_rejected_and_prediction_stops(self):
        p=PrimaryHand(self.adapter,self.cfg)
        f=sample(fingers=(True,False,False,False))
        self.assertFalse(p.update(f,0,self.mouse))
        self.assertTrue(p.update(replace(f,index=(.9,.3)),.03,self.mouse))
        self.mouse.release_all.assert_called_once()
        self.assertEqual(p.status,'Landmark jump')

    def test_invalid_config_rejected(self):
        for value in [{'version':2},{'symbols':{'ok':'bad key'}},{'modifier_seconds':0},
                      {'close_spread':.8,'wide_spread':.4},{'bindings':{'6':{}}}]:
            with self.assertRaises(ValueError):config(value)

    def test_four_fingers_with_folded_thumb_does_not_hold_shift(self):
        self.cfg['bindings']['4']={'type':'press','keys':'q'}
        s=SecondHand(self.adapter,self.cfg);f=sample(thumb_extended=False)
        for t in (0,.4,1.):s.update(f,t,True)
        self.assertFalse(self.adapter.held_keys)
        self.assertEqual([e['key'] for e in self.adapter.events if e['action']=='key_down'],['q'])

    def test_real_geometry_preserves_features_under_rotation(self):
        from tests.hand_geometry import pose, transformed
        hand=pose('open')
        a=features(hand,(640,480),self.cfg)
        b=features(transformed(hand,angle=40,scale=.7),(640,480),self.cfg)
        self.assertIsNotNone(a);self.assertIsNotNone(b)
        self.assertEqual(a.fingers,b.fingers)
        self.assertAlmostEqual(a.spread,b.spread)
        self.assertEqual(a.thumb,b.thumb)

    def test_migration_keeps_exact_backup_and_is_idempotent(self):
        import tempfile,json
        from pathlib import Path
        from scripts.migrate_gesture_v1 import migrate
        raw=Path('config/default_profile.json').read_bytes()
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'profile.json';path.write_bytes(raw)
            backup=migrate(path)
            self.assertEqual(backup.read_bytes(),raw)
            migrated=json.loads(path.read_text())
            self.assertEqual(migrated['gesture_v1']['bindings'],{})
            self.assertEqual(migrated['left_hand'],json.loads(raw)['left_hand'])
            self.assertIsNone(migrate(path))

    def test_settings_v1_round_trip(self):
        import os
        os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
        from PySide6.QtWidgets import QApplication
        from vision_control.gesture_v1_ui import GestureV1Panel
        app=QApplication.instance() or QApplication([])
        panel=GestureV1Panel(DEFAULTS)
        panel.bindings['3'][0].setCurrentText('Hold')
        panel.bindings['3'][1].setText('w')
        panel.actions['symbols','ok'].setText('ctrl+c')
        saved=panel.value();panel.load(saved)
        self.assertEqual(panel.value(),saved)
        self.assertFalse(saved['fist_switch'])
        panel.close()

    def test_runtime_modifier_pause_loss_and_stale_gap(self):
        import numpy as np
        from unittest.mock import patch
        from vision_control.runtime import VisionRuntime
        from vision_control.monitors import MonitorLayout
        from vision_control.types import HandsFrame
        from tests.hand_geometry import pose
        camera=Mock();camera.read.return_value=np.zeros((480,640,3),dtype=np.uint8)
        tracker=Mock();hands=[pose('fist')]
        tracker.track.side_effect=lambda frame,stamp:HandsFrame(stamp,tuple(hands),640,480)
        runtime=VisionRuntime(0,True,'config/gesture_v1_profile.json',
            camera_factory=lambda **kw:camera,tracker_factory=lambda:tracker,
            adapter_factory=lambda:self.adapter)
        with patch('vision_control.runtime.discover_monitors',return_value=MonitorLayout([self.region],'fixed')):
            runtime.start()
        try:
            runtime.set_paused(False)
            # Right-labelled observation is assigned to the keyboard by swap_hands.
            for i in range(12):
                with patch('time.monotonic',return_value=i*.1):runtime.process_frame()
            self.assertEqual(self.adapter.held_keys,{'ctrl'})
            runtime.set_paused(True);self.assertFalse(self.adapter.held_keys)
            runtime.set_paused(False)
            for i in range(20,32):
                with patch('time.monotonic',return_value=i*.1):runtime.process_frame()
            self.assertEqual(self.adapter.held_keys,{'ctrl'})
            hands.clear()
            with patch('time.monotonic',return_value=3.2):runtime.process_frame()
            self.assertFalse(self.adapter.held_keys)
            hands.append(pose('fist'))
            for t in (4.,5.2):
                with patch('time.monotonic',return_value=t):runtime.process_frame()
            self.assertFalse(self.adapter.held_keys)
        finally:runtime.close()

    def test_geometry_rejects_missing_or_nonfinite(self):
        from vision_control.types import HandObservation
        self.assertIsNone(features(None,(640,480),self.cfg))
        self.assertIsNone(features(HandObservation('Right',((float('nan'),0,0),)*21),(640,480),self.cfg))
