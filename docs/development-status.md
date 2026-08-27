# Development status

## Working

- MediaPipe tracks up to two hands locally.
- Right and left hand roles can be swapped for mirrored cameras.
- Right hand moves the cursor and supports pinch mouse buttons.
- Left-hand static gestures map to configurable press/hold keyboard actions.
- macOS Camera and Accessibility permissions have been verified.
- Camera index can be selected from the command line.
- Active, fixed, and all-display monitor mapping is supported.
- Mouse calibration is integrated and persisted locally.
- Two-finger vertical motion emits scroll events.
- Cursor movement has configurable smoothing and a pixel deadzone.
- Left-hand fist hold toggles keyboard ARMED/DISARMED state with progress,
  release latch, cooldown, and automatic hand-loss disarm.
- The supplied VisionControl logo is rendered as an RGBA overlay.
- A branded splash screen and stage-driven loading screen are shown during startup.
- Deterministic unit tests cover profile validation, role swapping, debounce,
  held-key release, calibration mapping, and special key resolution.

## Current test setup

- macOS on Apple Silicon
- Python 3.11
- MediaPipe 0.10.21
- Physical MacBook camera at index `1` because Immersed virtual camera uses index `0`

## Next priorities

1. Add camera/profile selection UI and Windows 11 verification.
2. Add edge-dwell or gesture-based monitor switching for `active` mode.
3. Package signed desktop builds for macOS and Windows 11.

## Run

```bash
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m pip install -e .
python -m vision_control.app --camera-index 1
```
