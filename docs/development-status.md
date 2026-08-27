# Development status

## Working

- MediaPipe tracks up to two hands locally.
- Right and left hand roles can be swapped for mirrored cameras.
- Right hand moves the cursor and supports pinch mouse buttons.
- Left-hand static gestures map to configurable press/hold keyboard actions.
- macOS Camera and Accessibility permissions have been verified.
- Camera index can be selected from the command line.
- Deterministic unit tests cover profile validation, role swapping, debounce,
  held-key release, calibration mapping, and special key resolution.

## Current test setup

- macOS on Apple Silicon
- Python 3.11
- MediaPipe 0.10.21
- Physical MacBook camera at index `1` because Immersed virtual camera uses index `0`

## Next priorities

1. Detect monitor topology and support active/fixed/all-monitor cursor modes.
2. Integrate mouse calibration into the live controller.
3. Add explicit click-versus-drag timing and real scroll gestures.
4. Add a safe arming gesture for left-hand keyboard actions.
5. Add camera/profile selection UI and Windows 11 verification.

## Run

```bash
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m pip install -e .
python -m vision_control.app --camera-index 1
```
