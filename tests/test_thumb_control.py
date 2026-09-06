from dataclasses import replace
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from tests.hand_geometry import pose
from vision_control.controllers import MouseController
from vision_control.diagnostics import DiagnosticInputAdapter
from vision_control.profile import load_profile

class ThumbControlTests(unittest.TestCase):
    def setUp(self):
        p=load_profile(Path(__file__).parents[1]/'config/default_profile.json')
        self.profile=replace(p,pointer_mode='thumb_lock')
        self.a=DiagnosticInputAdapter();self.c=MouseController(self.a,self.profile,screen=(640,480))
    def step(self,hand,t):
        with patch('vision_control.thumb_control.time.monotonic',return_value=t):self.c.update(hand)
    def curls(self,tips):
        h=pose('open');pts=list(h.landmarks);folded=pose('fist')
        for tip in tips:
            for i in range(tip-2,tip+1):pts[i]=folded.landmarks[i]
        return replace(h,landmarks=tuple(pts))
    def test_all_clicks_locked_at_same_coordinate(self):
        for tips,button in [([8],'left'),([12],'middle'),([8,12,16,20],'right')]:
            self.c.release_all();self.a.drain()
            self.step(pose('open'),0);self.step(pose('open'),.13)
            anchor=self.a.position()
            self.step(self.curls(tips),.2);self.step(self.curls(tips),.27)
            self.step(pose('open'),.3)
            self.assertEqual([(e['action'],e['button']) for e in self.a.drain() if 'button' in e],
                             [('button_down',button),('button_up',button)])
            self.assertEqual(anchor,self.a.position())
    def test_pinch_drag_without_lock_no_initial_jump_then_relative_motion(self):
        self.step(pose('four'),0)
        anchor=self.a.position()
        self.assertFalse(self.c.thumb_control.clicks.locked)
        self.step(pose('pinch'),.1);self.step(pose('pinch'),.21)
        self.assertEqual(self.a.held_buttons,{'left'})
        self.assertEqual(self.a.position(),anchor)
        h=pose('pinch');h=replace(h,landmarks=tuple((x+.08,y,z) for x,y,z in h.landmarks))
        self.step(h,.3)
        self.assertGreater(self.a.position()[0],anchor[0])
        self.step(pose('point'),.4)
        self.assertTrue(self.a.held_buttons)
        self.step(pose('point'),.51)
        self.assertFalse(self.a.held_buttons)

    def test_bent_index_separation_can_prepare_without_timeout(self):
        h=pose('pinch');pts=list(h.landmarks);pts[4]=(.1,.15,0)
        self.step(replace(h,landmarks=tuple(pts)),0)
        self.step(pose('pinch'),5);self.step(pose('pinch'),5.11)
        self.assertEqual(self.a.held_buttons,{'left'})

    def test_transient_gap_keeps_drag_and_loss_still_releases_immediately(self):
        self.step(pose('point'),0);self.step(pose('pinch'),.1);self.step(pose('pinch'),.21)
        anchor=self.a.position()
        self.step(pose('point'),.3)
        self.assertEqual(self.c.status,'drag_release_pending')
        self.assertEqual(self.a.position(),anchor)
        self.step(pose('pinch'),.35)
        self.assertTrue(self.a.held_buttons)
        self.step(pose('point'),.4);self.step(None,.41)
        self.assertFalse(self.a.held_buttons)
        self.step(pose('pinch'),.5);self.step(pose('pinch'),.7)
        self.assertFalse(self.a.held_buttons)
    def test_cold_pinch_rejected_and_hand_loss_releases_drag(self):
        self.step(pose('pinch'),0);self.step(pose('pinch'),.2)
        self.assertFalse(self.a.held_buttons)
        self.step(pose('point'),.3);self.step(pose('pinch'),.4);self.step(pose('pinch'),.51)
        self.assertTrue(self.a.held_buttons)
        self.step(None,.6)
        self.assertFalse(self.a.held_buttons)
    def test_middle_release_failure_retains_state_for_retry(self):
        self.c.middle_down=True;self.a.button_down('middle')
        with patch.object(self.a,'button_up',side_effect=RuntimeError('retry')):
            with self.assertRaises(ExceptionGroup):self.c.release_all()
        self.assertTrue(self.c.middle_down)
        self.c.release_all();self.assertFalse(self.c.middle_down)
    def test_profile_accepts_new_mode(self):
        raw=json.loads((Path(__file__).parents[1]/'config/default_profile.json').read_text())
        raw['pointer_mode']='thumb_lock'
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'profile.json';p.write_text(json.dumps(raw))
            self.assertEqual(load_profile(p).pointer_mode,'thumb_lock')
