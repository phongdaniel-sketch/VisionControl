# VisionControl workspace handoff

Updated: 2026-08-27 (Asia/Ho_Chi_Minh)

## Repository

- GitHub: `https://github.com/phongdaniel-sketch/VisionControl`
- Branch: `main`
- Packaged-build baseline: `2ca20e6 Add standalone desktop build workflow`
- Open this repository folder directly as the VS Code workspace; do not open the
  parent `/Volumes/Data Extern/VS Code` folder.

## Current validated environment

- macOS 26.6.2 on Apple Silicon (M4)
- Python 3.11
- Virtual environment: `.venv311`
- MediaPipe 0.10.21
- Physical MacBook camera index: `1`
- Camera index `0` is occupied by the Immersed virtual camera
- `swap_hands` is `true` for the mirrored camera feed
- Camera and Accessibility permissions were previously enabled for VS Code;
  packaged `VisionControl.app` may require its own permissions

## Setup after opening the new workspace

```bash
python3.11 -m venv .venv311
source .venv311/bin/activate
python -m pip install -r requirements.txt
python -m pip install -e .
```

In VS Code, run **Python: Select Interpreter** and choose `.venv311`. Repository
settings already exclude virtual environments, `build/`, and `dist/` from
Pylance analysis.

## Run and test

Open Settings:

```bash
PYTHONPATH=src .venv311/bin/python -m vision_control.settings_ui
```

Run the controller safely:

```bash
PYTHONPATH=src .venv311/bin/python -m vision_control.app \
  --camera-index 1 --start-paused
```

Run deterministic verification:

```bash
PYTHONPATH=src .venv311/bin/python -m unittest discover -s tests -v
```

Current result: 31 tests pass.

## Implemented behavior

- Right-hand mouse movement, pinch buttons/drag, scrolling, smoothing, deadzone,
  and calibration.
- Left-hand configurable Disabled/Press/Hold keyboard mappings and multi-key
  chords.
- Hold left fist for one second to toggle keyboard ARMED/DISARMED; hand loss,
  pause, calibration, and exit release all held keys.
- Active/fixed/all monitor modes, including negative display coordinates.
- Point-pose edge dwell switches to the spatial previous/next display with
  progress and a release latch.
- Settings UI, application icons, splash/loading screens, offline hand model,
  and source CLI.

## Runtime controls

- `Esc`: exit camera controller
- `P`: pause/resume
- `C`: start mouse calibration
- `Space`: capture current calibration boundary
- `R`: cancel calibration

## Local data

Source runs store ignored JSON under `data/`. Frozen builds store writable data
under:

- macOS: `~/Library/Application Support/VisionControl`
- Windows: `%LOCALAPPDATA%\VisionControl`

Never commit personal profiles, calibration data, credentials, or permission
artifacts.

## Standalone macOS build

```bash
source .venv311/bin/activate
python -m pip install -r requirements-build.txt
pyinstaller --noconfirm --clean VisionControl.spec
open dist/VisionControl.app
```

The current local Apple Silicon artifacts are ignored by Git:

- `dist/VisionControl.app` (about 820 MB)
- `dist/VisionControl-0.1.0-macOS-arm64.zip` (about 220 MB)
- ZIP SHA-256: `f03badef5d023cce554451c05fa1392e397946d48cf1f74a451cfeaba8fdc620`

The `.app` opens Settings and the bundled controller has successfully started
camera index `1`. Its PyInstaller signature is ad-hoc for local testing. DMG
creation was not completed because `hdiutil` returned `Operation not permitted`
in the current environment.

## Known limitations and next work

1. User acceptance-test `VisionControl.app` with Camera and Accessibility granted
   specifically to VisionControl.
2. Reduce the 820 MB prototype bundle; MediaPipe collection currently includes
   optional modules such as Matplotlib and SciPy.
3. Add Apple Developer ID signing, notarization, and a distributable DMG when
   credentials are available.
4. Build on Windows 11, verify camera/input/DPI/multiple monitors, then create and
   Authenticode-sign the `.exe` installer.

## Key files

- Runtime entry: `src/vision_control/app.py`
- Desktop launcher: `src/vision_control/launcher.py`
- Settings UI: `src/vision_control/settings_ui.py`
- Frozen/source paths: `src/vision_control/paths.py`
- Profile defaults: `config/default_profile.json`
- Packaging: `VisionControl.spec`
- Current status: `docs/development-status.md`

