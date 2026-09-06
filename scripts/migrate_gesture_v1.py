"""Opt-in migration: backup exact bytes, preserve calibration and legacy bindings."""
import argparse
import json
from pathlib import Path
from vision_control.gesture_v1_config import DEFAULTS, config
from vision_control.settings import save_user_profile


def migrate(path):
    path = Path(path)
    original = path.read_bytes()
    raw = json.loads(original.decode('utf-8-sig'))
    if 'gesture_v1' in raw:
        config(raw['gesture_v1'])
        return None
    backup = path.with_name(path.name + '.pre-gesture-v1.bak')
    if backup.exists() and backup.read_bytes() != original:
        raise ValueError(f'Backup already exists with different content: {backup}')
    if not backup.exists():
        backup.write_bytes(original)
    raw['gesture_v1'] = config(DEFAULTS)
    raw['pointer_mode'] = 'thumb_lock'
    raw.setdefault('arming', {})['enabled'] = False
    save_user_profile(path, raw)
    return backup


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('profile', type=Path)
    args = parser.parse_args()
    print(migrate(args.profile) or 'Already migrated; preserved current settings')
