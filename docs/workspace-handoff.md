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

Current result: 41 tests pass.

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
- Loading uses the approved rounded gradient/glow treatment without a secondary
  percentage or stage line.
- Camera startup/frame failures leave Controller visible in `ERROR · PAUSED`,
  release all input, and allow a Settings → Save retry after permissions change.
- Fresh/reset settings select camera `1`; fixed display index `0` is normalized
  to the operating system primary display (the built-in Color LCD on this Mac).
- The fixed-display combo currently shows `Built-in Retina Display`,
  `DELL U2424HE`, and `ARZOPA`, including logical resolutions and a Primary tag.
- High-contrast combo/spin styling and bundled chevron assets replace the
  low-visibility native black increment/decrement controls.
- Gestures now edits Disabled/Press/Hold and key/chord mappings directly on each
  built-in gesture card; Fist remains a locked keyboard safety gesture.
- Gestures has role-aware `Mouse hand · Right` / `Keyboard hand · Left` views.
  Mouse controls can restrict pointer movement to a pose, swap/disable Index and
  Middle pinch clicks, and choose Peace/Three/Four/Open palm for scrolling.
  Fist always stops the pointer and releases mouse buttons.
- Keyboard configures fist hold/release/cooldown and hand-loss auto-disarm.
- Advanced contains only implemented recognition/pinch/drag/scroll thresholds,
  with pinch hysteresis validation and recommended-default guidance.
- Settings controls and navigation expose tooltips plus accessibility
  descriptions for purpose, direction, and safety consequences.
- Cursor response now defaults to `0.60` with a `0.5 px` deadzone. The current
  local user profile was updated to the same values.
- Settings pauses/releases input and stops the frame timer for its entire
  session, avoiding concurrent MediaPipe work during page navigation.
- `Processing · N FPS` is measured from completed tracking/render cycles and is
  smoothed for readability; it is not a configured camera mode.

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

The `.app` opens Controller directly and the embedded-camera UI previously ran
camera index `1` paused for 60 seconds while detecting one and two hands.
MediaPipe, the offline model, and TFLite CPU delegate initialized successfully.
The ZIP passed `unzip -t`, and the DMG passed
`hdiutil verify` plus a read-only mount/signature/model check. PyInstaller's
signature remains ad-hoc for local testing.

The app bundle was rebuilt after the responsive-control changes. A Launch Services
run reproduced missing Camera authorization and confirmed that the fixed app
remains open in a safe error state instead of terminating. The currently open
instance is waiting for packaged-app Camera access; after granting it, use
Settings → Save to retry initialization. Existing ZIP/DMG hashes above refer to
the prior release archive and should be regenerated before distribution.

`scripts/build_macos_release.sh` stages the app on the system volume before DMG
creation because `hdiutil -srcfolder` rejects the external repository volume.
It supports Developer ID signing and notarization via Keychain references. The
current Keychain has only an Apple Development identity and no `notarytool`
credentials, so public signing/notarization cannot yet be executed.

## Known limitations and next work

1. Grant Camera and Accessibility specifically to the rebuilt VisionControl app,
   retry via Settings, then complete `docs/macos-uat.md` with physical gestures.
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
