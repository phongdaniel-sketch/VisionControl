# Development status

## Working

- MediaPipe tracks up to two hands locally.
- Right and left hand roles can be swapped for mirrored cameras.
- Right hand moves the cursor and supports pinch mouse buttons.
- Left-hand static gestures map to configurable press/hold keyboard actions.
- macOS Camera and Accessibility permissions have been verified.
- Camera index can be selected from the command line.
- Fresh/reset desktop settings use camera index `1` on the current target setup.
- Active, fixed, and all-display monitor mapping is supported.
- Fixed mode defaults to the platform primary display, normalized to display
  index `0` during monitor discovery.
- Settings lists fixed displays by operating-system name and logical resolution,
  with the primary display marked explicitly instead of requiring a numeric
  monitor index.
- Mouse calibration is integrated and persisted locally.
- Two-finger vertical motion emits scroll events.
- Cursor movement has configurable smoothing and a pixel deadzone.
- Left-hand fist hold toggles keyboard ARMED/DISARMED state with progress,
  release latch, cooldown, and automatic hand-loss disarm.
- The camera view stays unobstructed; branding is limited to startup screens.
- A branded splash and stage-driven loading screen use a thin rounded
  orange/red-to-purple-to-blue progress bar with a leading glow and no secondary
  percentage/status line.
- Native macOS and Windows icons are generated from the supplied application logo.
- A cross-platform Settings window saves validated local camera, hand, monitor,
  cursor, and scrolling preferences before launching VisionControl.
- A dark PySide6 Controller embeds the local camera preview, landmark skeleton,
  actual gesture guide, safety/status cards, Pause/Resume, disabled future Voice,
  and the only normal entry point to Settings.
- Opening Settings pauses and releases input; saving rebuilds the runtime with
  the new profile and camera settings while remaining paused.
- The Controller suspends camera inference/rendering throughout a Settings
  session, improving navigation responsiveness, then resumes still paused.
- Settings inputs use higher-contrast surfaces and borders, with bundled white
  arrow icons and distinct button wells for combo/spin controls.
- Cursor defaults favor response (`0.60`) with a small `0.5 px` movement
  deadzone; Settings explains how to tune response versus jitter.
- The header reports smoothed, measured processing/render FPS rather than a
  configured camera FPS value.
- macOS Camera denial and recoverable frame errors keep Controller visible in an
  explicit safe paused state; partially initialized runtime cleanup is
  idempotent and does not mask the original error.
- Settings configures left-hand gestures as Disabled, Press, or Hold actions,
  including validated multi-key chords; fist remains reserved for arming.
- Built-in gesture action/key editors now live directly on the Gestures page;
  the page explicitly distinguishes action mapping from training new poses.
- Gestures separates the configured Mouse and Keyboard hand roles. Mouse-hand
  mapping supports move pose, primary/secondary pinch swap or disable, and a
  configurable scroll pose; Fist remains the fixed pointer-stop release gesture.
- Keyboard exposes fist arm/disarm timing and hand-loss safety controls.
- Advanced exposes implemented recognition confidence, activation frames,
  pinch hysteresis, drag timing, and scroll deadzone settings with validation.
- Settings controls, navigation, and save/reset actions include concise tooltips
  and accessibility descriptions explaining effects and safety tradeoffs.
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
  held-key release, calibration mapping, Settings gating/disabled Voice,
  loading visuals, safe frame failure, idempotent cleanup, and special keys.

## Current test setup

- macOS on Apple Silicon
- Python 3.11
- MediaPipe 0.10.21
- Physical MacBook camera at index `1` because Immersed virtual camera uses index `0`

## Next priorities

1. Grant Camera access to the packaged `VisionControl.app`, retry through
   Settings, and complete the physical-hand checklist in `docs/macos-uat.md`,
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
