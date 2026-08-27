# VisionControl

Local-first webcam control: right hand for mouse input, left hand for configurable keyboard gestures.

## MVP status

The deterministic controller core is implemented. Webcam runtime requires Python dependencies from `requirements.txt` and a Windows input permission setup.

## Setup

Use Python 3.11 on macOS and Windows 11.

```bash
python3.11 -m venv .venv
source .venv/bin/activate  # Windows: .venv\\Scripts\\activate
python -m pip install -r requirements.txt
python -m pip install -e .
python -m vision_control.app --camera-index 0
```

If a virtual camera occupies index `0`, select the physical webcam, for example
`--camera-index 1`. On macOS, grant Camera and Accessibility permissions to the
terminal or editor that launches the process.

The app defaults to `config/default_profile.json`. Set `swap_hands` there when a
mirrored camera reverses physical left/right roles. Press `Esc` in the preview to
stop. Press `p` to pause/resume.

## Mouse calibration

Press `C` to start calibration. Move the right index fingertip to each requested
comfortable boundary (`left`, `right`, `top`, `bottom`) and press `Space` once per
stage. Press `R` to cancel. The result is stored locally in
`data/mouse_calibration.json` and is intentionally not committed.

## Multiple monitors

Set `monitor_mode` in `config/default_profile.json`:

- `active`: map the hand to the monitor currently containing the cursor.
- `fixed`: map to `fixed_monitor` by zero-based index.
- `all`: map across the union of every display, including negative coordinates.

The overlay shows the current `monitor` and `mouse_action`. Two extended fingers
activate scroll mode; a fist pauses mouse control and releases held buttons.

## Left-hand keyboard arming

Keyboard gestures start in `DISARMED` mode. Hold a left-hand fist steadily for
one second to toggle `ARMED`; release the fist before toggling again. While armed,
the configured left-hand gestures emit keys. Losing the left hand for two seconds,
pausing, calibrating, or exiting automatically disarms and releases held keys.

The overlay shows `ARMING`/`DISARMING` progress and the final keyboard mode. The
fist is reserved for arming and cannot also be assigned to a key while arming is
enabled. Timing and auto-disarm behavior are configurable under `arming` in the
default profile.

The application logo is stored at `docs/Vision Control logo.png`. The live camera
view does not render a logo overlay so the hand-tracking area stays unobstructed.
Desktop icon assets are generated from that source at `assets/VisionControl.icns`
for macOS and `assets/VisionControl.ico` for Windows.

## Settings

Open the cross-platform settings window with:

```bash
python -m vision_control.settings_ui
```

Settings lets you choose the camera index, mouse hand, mirrored-hand swapping,
monitor mode, cursor smoothing/deadzone, and scroll sensitivity. Use **Save and
Start VisionControl** to persist a validated local profile and launch the camera
controller. Personal settings are stored under `data/` and are ignored by Git.

The left-hand gesture editor supports Disabled, Press, and Hold actions. Enter
one key (`space`) or a comma-separated shortcut (`ctrl, c`). A press shortcut is
emitted as a chord; held keys are always released when the gesture ends, the app
pauses, or keyboard mode is disarmed. The fist remains reserved for arming.

In `active` monitor mode, point with the mouse hand and hold at the calibrated
left or right camera edge to switch displays. The overlay shows dwell progress;
move away from the edge before switching again. Settings controls whether this
is enabled, the dwell duration, and the edge-zone width. `fixed` and `all` modes
keep their existing behavior.

The original CLI remains available and accepts a custom profile:

```bash
python -m vision_control.app --camera-index 1 --profile data/user_profile.json
```

## Splash and loading screens

Startup uses two 1586×992 source assets, displayed at 1000×626 to preserve their
aspect ratio:

- `docs/Splash Screen.png`: shown first for one second without a loading bar.
- `docs/Loading Screen.png`: shown while profile, input, monitors, MediaPipe, and
  camera initialize; its progress bar and status reflect real startup stages.

Press `Esc` during startup to cancel safely.

## Standalone desktop build

Install build dependencies and create the macOS application bundle:

```bash
python -m pip install -r requirements-build.txt
pyinstaller --noconfirm --clean VisionControl.spec
open dist/VisionControl.app
```

The current local build targets Apple Silicon (`arm64`). It includes the hand
model and runs without a separate Python installation. Writable settings and
calibration are stored in `~/Library/Application Support/VisionControl` on
macOS and `%LOCALAPPDATA%\VisionControl` on Windows.

For local macOS testing, PyInstaller applies an ad-hoc signature. Public
distribution still requires Apple Developer ID signing and notarization. The
same launcher and `.ico` asset are ready for a Windows 11 PyInstaller build,
which must be produced and verified on Windows.

The local test artifact can be compressed for transfer while preserving macOS
bundle metadata:

```bash
ditto -c -k --sequesterRsrc --keepParent dist/VisionControl.app \
  dist/VisionControl-0.1.0-macOS-arm64.zip
```

## Safety

Keep the emergency stop available. The application releases all held mouse buttons and keys on pause, camera failure, normal exit, and exceptions. Camera frames are processed locally and are not uploaded.

## Development

```bash
PYTHONPATH=src python -m unittest discover -s tests -v
```

The test suite uses fake observations and a recording input adapter; it does not open a camera or emit OS input.
