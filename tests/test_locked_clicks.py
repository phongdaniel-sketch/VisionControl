import unittest
from vision_control.locked_clicks import LockedFingerClicks

class LockedClickTests(unittest.TestCase):
    def step(self,c,t,index='extended',middle='extended',thumb='open',pinch=False):
        return c.update(thumb,{'index':index,'middle':middle},pinch,t)
    def locked(self):
        c=LockedFingerClicks();self.step(c,0);self.step(c,.13);return c
    def test_release_completed_cycles(self):
        for index,middle,button in [('curled','extended','left'),('curled','curled','middle')]:
            c=self.locked()
            self.assertEqual(self.step(c,.2,index,middle),())
            self.assertEqual(self.step(c,.27,index,middle),())
            self.assertEqual(self.step(c,.3), (button,))
            self.assertEqual(self.step(c,.4),())
    def test_chord_does_not_fire_early_single(self):
        c=self.locked()
        self.step(c,.2,'curled');self.step(c,.27,'curled','curled')
        self.step(c,.34,'curled','curled')
        self.assertEqual(self.step(c,.4,'extended','curled'),())
        self.assertEqual(self.step(c,.45),('middle',))
    def test_middle_only_curl_no_longer_clicks(self):
        c=self.locked()
        self.step(c,.2,'extended','curled');self.step(c,.27,'extended','curled')
        self.assertEqual(self.step(c,.3),())
    def test_cold_curl_and_pinch_do_not_click(self):
        c=LockedFingerClicks()
        for t in (0,.13,.25):self.assertEqual(self.step(c,t,'curled','curled'),())
        self.assertEqual(self.step(c,.3),())
        self.step(c,.4,'curled','curled',pinch=True)
        self.assertEqual(self.step(c,.5),())
    def test_unknown_thumb_unlock_and_timeout_cancel(self):
        for thumb in ('unknown','tucked'):
            c=self.locked();self.step(c,.2,'curled');self.step(c,.27,'curled')
            self.step(c,.3,thumb=thumb)
            self.assertEqual(self.step(c,.4),())
        c=self.locked();self.step(c,.2,'curled')
        self.assertEqual(self.step(c,1.2),())
    def test_intermediate_angle_does_not_lose_preparation(self):
        c=self.locked();self.step(c,.18,'unknown');self.step(c,.2,'curled');self.step(c,.27,'curled')
        self.assertEqual(self.step(c,.3),('left',))
