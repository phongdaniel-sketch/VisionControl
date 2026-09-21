"""Validated single-chord Windows hotkey settings."""
def parse_hotkey(value):
    if value in ('Space', 'V'):
        value = 'Ctrl+Alt+'+value
    parts = [part.strip().lower() for part in value.split('+')]
    if len(parts) < 2 or len(set(parts)) != len(parts):
        raise ValueError('Hotkey cần Ctrl/Alt/Shift và một phím, ví dụ Ctrl+Shift+Space.')
    modifiers = {'ctrl': 2, 'alt': 1, 'shift': 4}
    if any(part not in modifiers for part in parts[:-1]):
        raise ValueError('Phím bổ trợ hỗ trợ: Ctrl, Alt, Shift.')
    key = parts[-1]
    if key == 'space':
        code, label = 0x20, 'Space'
    elif len(key) == 1 and key in 'abcdefghijklmnopqrstuvwxyz0123456789':
        code, label = ord(key.upper()), key.upper()
    elif key in {f'f{i}' for i in range(1, 13)}:
        code, label = 0x6F+int(key[1:]), key.upper()
    else:
        raise ValueError('Phím chính hỗ trợ: Space, A-Z, 0-9, F1-F12.')
    mask = sum(modifiers[part] for part in parts[:-1])
    normalized = '+'.join([m.title() for m in modifiers if m in parts[:-1]]+[label])
    return normalized, mask, code
