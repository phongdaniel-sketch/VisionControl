"""Replay recorded landmarks through v1 using simulated input; no camera/OS input."""
import argparse
import json
from pathlib import Path
from unittest.mock import patch
from vision_control.controllers import MouseController
from vision_control.diagnostics import DiagnosticInputAdapter
from vision_control.gesture_v1 import PrimaryHand, SecondHand, features
from vision_control.profile import load_profile
from vision_control.types import HandObservation, HandsFrame
from vision_control.roles import assign_roles


def replay(records, profile):
    adapter = DiagnosticInputAdapter()
    mouse = MouseController(adapter, profile, screen=(1920,1080))
    primary = PrimaryHand(adapter, profile.gesture_v1)
    secondary = SecondHand(adapter, profile.gesture_v1)
    previous = None
    try:
        for record in records:
            stamp = record['sample_time']
            size = tuple(record.get('frame_size', (1280,720)))
            hands = tuple(HandObservation(h['label'], tuple(tuple(p) for p in h['landmarks']), h.get('confidence',1.)) for h in record['hands'])
            a,b = assign_roles(HandsFrame(stamp,hands,*size),profile.mouse_hand,profile.keyboard_hand,profile.swap_hands)
            with patch('time.monotonic',return_value=stamp):
                if previous is not None and stamp-previous > .15:
                    mouse.release_all(); primary.reset(); secondary.reset()
                mouse.sample_time=stamp
                consumed=primary.update(features(a,size,profile.gesture_v1),stamp,mouse)
                if not consumed:mouse.update(a,size)
                secondary.update(features(b,size,profile.gesture_v1),stamp,primary.two_hands)
                yield {'sample_time':stamp,'mouse':primary.status if consumed else mouse.status,
                       'keyboard':secondary.status,'events':adapter.drain()}
            previous=stamp
    finally:
        secondary.reset();mouse.release_all();adapter.release_all()


if __name__ == '__main__':
    p=argparse.ArgumentParser();p.add_argument('recording',type=Path);p.add_argument('profile',type=Path)
    args=p.parse_args()
    profile=load_profile(args.profile)
    with args.recording.open(encoding='utf-8') as stream:
        for row in replay((json.loads(line) for line in stream if line.strip()),profile):
            print(json.dumps(row))
