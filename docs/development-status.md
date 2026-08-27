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
- A dark PySide6 Controller embeds the local camera preview, landmark skeleton,
  actual gesture guide, safety/status cards, Pause/Resume, disabled future Voice,
  and the only normal entry point to Settings.
- Opening Settings pauses and releases input; saving rebuilds the runtime with
  the new profile and camera settings while remaining paused.
- Settings configures left-hand gestures as Disabled, Press, or Hold actions,
  including validated multi-key chords; fist remains reserved for arming.
- Active monitor mode supports configurable point-pose edge dwell, spatial
  previous/next display switching, progress feedback, and a release latch.
- A PyInstaller macOS Apple Silicon app bundle opens the desktop Controller
  directly without a separate Python installation.
- The optimized macOS bundle excludes unused JAX/JAXlib and SciPy stacks,
  reducing the app from about 820 MB to 510 MB while retaining MediaPipe's
  required Matplotlib import.
- Reproducible release tooling creates and validates metadata-preserving ZIP and
  DMG artifacts, with optional Developer ID signing and notarization.
- Frozen builds use bundled read-only resources and OS-specific writable
  application-data directories; the hand model is bundled for offline startup.
- Deterministic unit tests cover profile validation, role swapping, debounce,
  held-key release, calibration mapping, Settings gating/disabled Voice, and
  special key resolution.

## Current test setup

- macOS on Apple Silicon
- Python 3.11
- MediaPipe 0.10.21
- Physical MacBook camera at index `1` because Immersed virtual camera uses index `0`

## Next priorities

1. Complete the physical-hand acceptance checklist in `docs/macos-uat.md`,
   especially Accessibility-controlled input and emergency release paths.
2. Install a Developer ID Application certificate and configure a `notarytool`
   Keychain profile, then run the implemented signing/notarization workflow.
3. Build and verify permissions, camera, input, and DPI behavior on Windows 11.

## Run

```bash
python3.11 -m venv .venv311
source .venv311/bin/activate
python -m pip install -r requirements.txt
python -m pip install -e .
python -m vision_control.launcher --camera-index 1 --start-paused
```
