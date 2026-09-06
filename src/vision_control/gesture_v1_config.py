"""Versioned configuration for Gesture Hand v1. No OS side effects."""
from copy import deepcopy

DEFAULTS = {
    'version': 1, 'enabled': True, 'two_hands': True, 'fist_switch': False,
    'scroll': True, 'zoom': True, 'volume': True, 'modifier_seconds': 1.0,
    'pose_seconds': .3, 'scroll_speed': 40.0, 'reverse_scroll': False,
    'close_spread': .45, 'wide_spread': .7,
    'symbol_seconds': .5, 'corner_seconds': 2.5,
    'symbols': {}, 'corners': {}, 'bindings': {},
}
SYMBOLS = ('thumbs_up', 'thumbs_down', 'ok', 'victory')
CORNERS = ('top_left', 'top_right', 'bottom_left', 'bottom_right')
ACTIONS = ('volume_up', 'volume_down', 'mute', 'zoom_in', 'zoom_out')


def validate_action(action):
    if not isinstance(action, str):
        raise ValueError('Gesture action must be text')
    if not action or action in ACTIONS:
        return
    from .profile import ALLOWED_KEYS
    if any(k not in ALLOWED_KEYS for k in action.split('+')):
        raise ValueError(f'Unsupported action: {action}; use a key chord or built-in action')


def config(raw=None):
    result = deepcopy(DEFAULTS)
    if raw is None:
        result['enabled'] = False  # Older profiles stay compatible until migrated.
        return result
    if not isinstance(raw, dict):
        raise ValueError('gesture_v1 must be an object')
    result.update(deepcopy(raw))
    if result['version'] != 1:
        raise ValueError('Unsupported gesture_v1 version')
    for key in ('enabled', 'two_hands', 'fist_switch', 'scroll', 'zoom', 'volume', 'reverse_scroll'):
        if not isinstance(result[key], bool):
            raise ValueError(f'{key} must be boolean')
    for key, lo, hi in [('modifier_seconds', .3, 3), ('pose_seconds', .1, 1),
                        ('scroll_speed', 1, 150), ('symbol_seconds', .2, 2),
                        ('corner_seconds', 1, 5), ('close_spread', .15, .8),
                        ('wide_spread', .3, 1.5)]:
        if not lo <= float(result[key]) <= hi:
            raise ValueError(f'{key} must be between {lo} and {hi}')
        result[key] = float(result[key])
    if result['wide_spread'] <= result['close_spread']:
        raise ValueError('Wide spread must exceed close spread')
    for key, allowed in [('symbols', SYMBOLS), ('corners', CORNERS)]:
        if not isinstance(result[key], dict) or set(result[key]) - set(allowed):
            raise ValueError(f'Invalid {key}')
        for action in result[key].values():
            validate_action(action)
    if not isinstance(result['bindings'], dict) or set(result['bindings']) - set('12345'):
        raise ValueError('Finger bindings must use 1–5')
    for binding in result['bindings'].values():
        if binding.get('type') not in ('press', 'hold'):
            raise ValueError('Binding type must be press or hold')
        action = binding.get('keys', '')
        validate_action(action)
        if not action or action in ACTIONS:
            raise ValueError('Finger binding requires a key chord')
    return result
