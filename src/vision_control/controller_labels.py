"""Presentation helpers; never change stored gesture or monitor identifiers."""
import re


POSE_HELP = {
    'point': 'Raise only the index finger',
    'peace': 'Raise index + middle fingers',
    'three_fingers': 'Raise index + middle + ring fingers',
    'four_fingers': 'Raise four fingers; tuck the thumb',
    'open_palm': 'Open the hand, including the thumb',
    'pinch_index': 'Extend index first, then touch thumb + index fingertips',
    'pinch_middle': 'Raise middle finger, then touch thumb to it',
    'any': 'Any visible pose except a fist',
    'disabled': 'Disabled',
}


def display_name(raw):
    match = re.fullmatch(r'\\\\\.\\DISPLAY(\d+)', raw, flags=re.IGNORECASE)
    return f'Display {match.group(1)}' if match else 'All displays' if raw == 'all' else raw


def mouse_guide(profile):
    if profile.pointer_mode == 'thumb_lock':
        start_ms = profile.thresholds.get('pinch_confirm_seconds', .1) * 1000
        release_ms = profile.thresholds.get('pinch_release_seconds', .1) * 1000
        return [
            ('Move / lock', 'Thumb tucked = move\nThumb open = lock'),
            ('Left click', 'Index: curl → straighten'),
            ('Right click', 'Index + middle: together\ncurl → straighten'),
            ('Middle click', 'Middle: curl → straighten'),
            ('Drag', f'Thumb + index: apart → pinch {start_ms:g} ms\nMove palm; apart {release_ms:g} ms to drop.'),
        ]
    thresholds = profile.thresholds
    move = 'point' if profile.pointer_mode == 'index_fingertip' else thresholds.get('mouse_move_gesture', 'any')
    return [
        ('Move pointer', POSE_HELP[move]),
        ('Left click / drag', POSE_HELP[thresholds.get('mouse_primary_click_gesture', 'pinch_index')]),
        ('Right click / drag', POSE_HELP[thresholds.get('mouse_secondary_click_gesture', 'pinch_middle')]),
        ('Scroll', POSE_HELP[thresholds.get('mouse_scroll_gesture', 'peace')] + '; move up/down'),
        ('Stop / release', 'Make a fist; held mouse buttons release'),
    ]
