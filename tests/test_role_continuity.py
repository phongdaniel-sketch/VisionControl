import unittest
from dataclasses import replace
from tests.hand_geometry import pose
from vision_control.roles import RoleContinuity, assign_roles
from vision_control.types import HandsFrame


class RoleContinuityTests(unittest.TestCase):
    def setUp(self):
        self.selector = RoleContinuity()
        self.hand = pose('open')

    def shift(self, amount):
        return replace(self.hand, landmarks=tuple((x+amount,y,z) for x,y,z in self.hand.landmarks))

    def frame(self, time, *hands):
        return self.selector.update(HandsFrame(time, hands))

    def test_unique_current_match_survives_duplicate_and_order_changes(self):
        self.frame(1, self.hand)
        for t, hands in ((1.04,(self.shift(.2),self.shift(.01))),
                         (1.08,(self.shift(.02),self.shift(.2)))):
            result = self.frame(t,*hands)
            self.assertEqual(len(result.hands),1)
            self.assertIn(result.hands[0], hands)
            self.assertLess(result.hands[0].landmarks[0][0],.6)

    def test_cold_duplicate_is_ambiguous(self):
        result=self.frame(1,self.hand,self.shift(.2))
        self.assertIsNone(assign_roles(result,'Right','Left')[0])

    def test_two_close_matches_are_not_guessed(self):
        self.frame(1,self.hand)
        result=self.frame(1.04,self.shift(.01),self.shift(-.01))
        self.assertEqual(len(result.hands),2)
        self.assertFalse(self.selector.previous)

    def test_stale_and_nonmonotonic_frames_do_not_resolve(self):
        for stamp in (1, .9, 1.2):
            self.selector.reset()
            self.frame(1,self.hand)
            self.assertEqual(len(self.frame(stamp,self.hand,self.shift(.2)).hands),2)

    def test_loss_and_reset_forget_identity(self):
        for missing in (True,False):
            self.frame(1,self.hand)
            if missing:self.frame(1.02)
            else:self.selector.reset()
            self.assertEqual(len(self.frame(1.04,self.hand,self.shift(.2)).hands),2)

    def test_far_candidates_do_not_teleport(self):
        self.frame(1,self.hand)
        self.assertEqual(len(self.frame(1.04,self.shift(.3),self.shift(-.3)).hands),2)

    def test_distinct_roles_and_swap_are_preserved(self):
        left=replace(self.shift(.2),label='Left')
        result=self.frame(1,self.hand,left)
        self.assertEqual(assign_roles(result,'Right','Left',True),(left,self.hand))

    def test_low_confidence_does_not_seed_identity(self):
        self.frame(1,replace(self.hand,confidence=.2))
        self.assertEqual(len(self.frame(1.04,self.hand,self.shift(.2)).hands),2)

    def test_dimension_change_does_not_resolve(self):
        self.frame(1,self.hand)
        result=self.selector.update(HandsFrame(1.04,(self.hand,self.shift(.2)),1280,720))
        self.assertEqual(len(result.hands),2)
