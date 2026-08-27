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
- The camera view stays unobstructed; branding is limited to startup screens.
- A branded splash screen and stage-driven loading screen are shown during startup.
- Native macOS and Windows icons are generated from the supplied application logo.
- A cross-platform Settings window saves validated local camera, hand, monitor,
  cursor, and scrolling preferences before launching VisionControl.
- Settings configures left-hand gestures as Disabled, Press, or Hold actions,
  including validated multi-key chords; fist remains reserved for arming.
- Active monitor mode supports configurable point-pose edge dwell, spatial
  previous/next display switching, progress feedback, and a release latch.
- A PyInstaller macOS Apple Silicon app bundle opens Settings and starts the
  bundled camera controller without a separate Python installation.
- Frozen builds use bundled read-only resources and OS-specific writable
  application-data directories; the hand model is bundled for offline startup.
- Deterministic unit tests cover profile validation, role swapping, debounce,
  held-key release, calibration mapping, and special key resolution.

## Current test setup

- macOS on Apple Silicon
- Python 3.11
- MediaPipe 0.10.21
- Physical MacBook camera at index `1` because Immersed virtual camera uses index `0`

## Next priorities

1. User acceptance-test the macOS `.app`, including Camera and Accessibility.
2. Reduce prototype bundle size and add Developer ID signing/notarization.
3. Build and verify permissions, camera, input, and DPI behavior on Windows 11.

## Run

```bash
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m pip install -e .
python -m vision_control.app --camera-index 1
```
