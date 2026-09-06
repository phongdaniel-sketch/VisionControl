"""Synthetic joint fixtures with distinct MCP/PIP/DIP/tip positions."""
from dataclasses import replace
import math
from vision_control.types import HandObservation


def pose(kind='point'):
    points = [(.5, .6, 0)] * 21
    points[0] = (.5, .85, 0)
    points[1], points[2], points[3], points[4] = (
        (.38, .7, 0), (.29, .6, 0), (.23, .48, 0), (.18, .38, 0))
    for tip, x in zip((8, 12, 16, 20), (.40, .49, .58, .67)):
        points[tip-3] = (x, .5, 0)
        extended = (kind in ('open', 'four') or (kind == 'three' and tip != 20) or
                    (kind == 'point' and tip == 8) or (kind == 'middle' and tip == 12))
        if extended:
            points[tip-2], points[tip-1], points[tip] = (x, .34, 0), (x, .24, 0), (x, .14, 0)
        else:
            points[tip-2], points[tip-1], points[tip] = (x, .36, 0), (x+.02, .48, 0), (x, .60, 0)
    if kind in ('pinch', 'middle_pinch'):
        tip = 8 if kind == 'pinch' else 12
        x = points[tip][0]
        # Tip below PIP but outside the palm: old Y-only fist test mislabels this.
        points[tip-1], points[tip] = (x-.025, .32, 0), (x-.06, .40, 0)
        points[4] = points[tip]
    if kind in ('fist', 'four', 'three'):
        points[4] = (.41, .59, 0)
    return HandObservation('Right', tuple(points))


def transformed(hand, angle=0, scale=1):
    # Rotate in aspect-corrected coordinates, then convert back to camera units.
    radians = math.radians(angle)
    cosine, sine = math.cos(radians), math.sin(radians)
    result = []
    for x, y, z in hand.landmarks:
        x, y = (x-.5)*4/3*scale, (y-.5)*scale
        result.append(((x*cosine-y*sine)*3/4+.5, x*sine+y*cosine+.5, z*scale))
    return replace(hand, landmarks=tuple(result))
