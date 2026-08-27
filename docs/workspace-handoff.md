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

Run the desktop Controller safely:

```bash
PYTHONPATH=src .venv311/bin/python -m vision_control.launcher \
  --camera-index 1 --start-paused
```

Open Settings directly for diagnostics:

```bash
PYTHONPATH=src .venv311/bin/python -m vision_control.settings_ui
```

Run deterministic verification:

```bash
PYTHONPATH=src .venv311/bin/python -m unittest discover -s tests -v
```

Current result: 33 tests pass.

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
- Controller-first dark desktop UI with embedded camera/landmarks, actual
  gesture guide, prominent Pause/Resume, explicit ARMED/DISARMED status, and
  Voice shown disabled for future development.
- Settings opens only from the Controller's Settings button in normal use;
  opening it pauses and releases input, and saved changes restart paused.

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

The current optimized local Apple Silicon artifacts are ignored by Git:

- `dist/VisionControl.app` (about 510 MB)
- `dist/VisionControl-0.1.0-macOS-arm64.zip` (about 144 MB)
- `dist/VisionControl-0.1.0-macOS-arm64.dmg` (about 160 MB)
- ZIP SHA-256: `e3f70be8da8dc59b64b9612789ef9188cc6fc1513b88190e1279efb7fcfd30a4`
- DMG SHA-256: `27b3e41c85823dd11541947ab41f8bfc903e2f83f1ba9c2fd1cee794a58afb09`

The `.app` opens Controller directly and the embedded-camera UI successfully ran
camera index `1` paused for 20 seconds while detecting one and two hands.
MediaPipe, the offline model, and TFLite CPU delegate initialized successfully.
The ZIP passed `unzip -t`, and the DMG passed
`hdiutil verify` plus a read-only mount/signature/model check. PyInstaller's
signature remains ad-hoc for local testing.

`scripts/build_macos_release.sh` stages the app on the system volume before DMG
creation because `hdiutil -srcfolder` rejects the external repository volume.
It supports Developer ID signing and notarization via Keychain references. The
current Keychain has only an Apple Development identity and no `notarytool`
credentials, so public signing/notarization cannot yet be executed.

## Known limitations and next work

1. Complete `docs/macos-uat.md` with physical gestures and Accessibility granted
   specifically to VisionControl; automated packaged smoke checks already pass.
2. Add the Developer ID Application identity and notary Keychain profile, then
   run `scripts/build_macos_release.sh --notarize`.
3. Consider narrower MediaPipe collection in a later optimization; Matplotlib is
   currently required by MediaPipe 0.10.21 package initialization.
4. Build on Windows 11, verify camera/input/DPI/multiple monitors, then create and
   Authenticode-sign the `.exe` installer.

## Key files

- Runtime entry: `src/vision_control/app.py`
- Shared frame runtime: `src/vision_control/runtime.py`
- Desktop Controller: `src/vision_control/controller_ui.py`
- Desktop launcher: `src/vision_control/launcher.py`
- Settings UI: `src/vision_control/settings_ui.py`
- Frozen/source paths: `src/vision_control/paths.py`
- Profile defaults: `config/default_profile.json`
- Packaging: `VisionControl.spec`
- Current status: `docs/development-status.md`
