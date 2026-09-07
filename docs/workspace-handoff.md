# VisionControl workspace handoff

Latest keyboard correction: 87 tests pass. Three/four/open static poses now use
joint geometry; thumb spread is relative to the palm, independent of Left/Right
labels or mirroring. Ambiguous states return None. This fixes the hardcoded thumb
direction responsible for the user's open-left-palm screenshot. Saved mappings
and calibration preserved; physical user retest pending. See
`docs/plans/keyboard-pose-geometry.md`.

Latest: user successfully calibrated. Mouse pinch/fist refinement implemented;
82 tests pass. Extend the intended clicking finger with thumb apart, then pinch
within .8 s. A confirmed pinch may bend; clear geometric fist/Pause/hand loss
releases input. Stored mappings/calibration were preserved. See
`docs/plans/pinch-fist.md` for research and pending physical click acceptance.
Click-position anchoring remains unimplemented.

Latest UI update: 73 tests pass. Controller has a role selector in Gesture Guide,
clean Windows Display N labels and separate live pose/input status. Calibrate
button opens a four-boundary inline workflow; Space captures immediately or use
Capture in 3 seconds. The runtime stays paused throughout and after completion.
Errors preserve the current step; cancel keeps the old calibration. Files save
atomically. See `docs/plans/controller-clarity.md`; physical user UAT pending.

Latest pointer tuning (2026-09-05): 64 tests pass. VIDEO tracking, optional adaptive
smoothing and confirmed/exclusive pinches are implemented. Local tuning is backed
up under ignored `data/user_profile.before_tuning.*.json`. Response .70, deadzone
.8 px, close/open .28/.45, confirmation .10 s; mappings remain unchanged. Starting
a middle pinch requires raising the middle finger. No FPS improvement measured
in short 45-frame before/after runs (both approximately 25.3 capture/tracking FPS).
Physical feel and click accuracy await user retest. See `docs/plans/pointer-tuning.md`.

## Windows setup update (2026-09-05)

Follow-up implementation: shared safety fixes and Index fingertip mode are now
implemented; 56 tests pass. Choose Settings -> Mouse -> Pointer mode -> Index
fingertip -> Save; the Controller restarts paused. Keep the hand visible and point
with only the index finger to move. Existing pinch and scroll bindings remain.
Windows camera 0 now uses DirectShow; a 15-second paused Controller smoke test
outside sandbox detected physical hands and exited successfully. Active input,
mixed DPI, Windows packaging and macOS regression still require acceptance.

- Local development branch: `windows`; both platforms share application logic.
- Python 3.11.9 AMD64 installed for the current user; `.venv311` created and
  requirements plus the editable project installed successfully.
- Windows environment reports build 26200, display version 25H2.
- MediaPipe 0.10.21, NumPy 1.26.4, OpenCV 4.11.0, PySide6 6.11.2 and pynput 1.8.2.
- PASS: 41 deterministic tests, compileall, pip check and git diff --check.
- PASS: bundled MediaPipe model initialization and inference on a synthetic blank
  640x480 frame (zero hands), followed by tracker cleanup. No webcam/input smoke
  test has been performed on Windows.
- PowerShell entry point: `scripts/windows.ps1 setup|test|run`; run starts paused
  and accepts `-CameraIndex 0` (select the actual camera before physical testing).
- Next: active input/DPI and packaged Windows acceptance, plus macOS regression.
  See `docs/plans/windows-fingertip.md`. The 41-test entry below records the initial
  setup baseline; the follow-up result above supersedes it.

The macOS handoff below is historical and remains relevant for macOS regression.

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

## Diagnostic recording handoff

User approved local webcam + dedicated test canvas recording to investigate
tracking errors. `scripts/windows.ps1 diagnose` launches a paused standalone UI;
recording requires Start, counts down three seconds and stops after 30 seconds.
Inspect newest `data/captures/*/summary.json`, then correlate `frames.jsonl` with
AVI frame numbers. No desktop/audio capture or OS input; do not interpret test
canvas results as Windows cursor latency. Current validation: 91 tests passed.
User's physical recording/gesture comparison is still pending.

Latest pointer correction: mouse-only relaxed pointing plus bounded catch-up
implemented; 93 tests pass. Recorded 846-frame replay increases move frames from
183 to 652; waiting_point drops 657 to 188. Maximum canvas step falls 643.80 to
300.84 px, so large steps are reduced, not eliminated. No replay clicks.
See docs/requirements/pointer-recovery.md and docs/plans/pointer-recovery.md.
User must restart the app and perform physical acceptance; settings preserved.

Aim/click usability: focused-window Space pause/resume (calibration capture
retained), mouse-only moderate bend tolerance, adaptive resting radius and
prepared-pinch cursor anchoring implemented. See docs/plans/aim-click.md.
Restart app for user acceptance; do not claim hidden fingertips are recoverable
or that synthetic jitter tests establish physical-camera accuracy.

Latest UI: Show calibration area + Debug recording + stage timings added.
Debug closes Controller camera before starting simulated recorder; closing debug
restores paused Controller. 99 tests pass. Physical handoff acceptance pending.
See docs/plans/calibration-debug-access.md. Camera FPS setting was not changed.

Pipeline experiment completed: standalone scripts/benchmark_pipeline.py measured
camera-only / sequential / latest-frame twice at 480p and 720p. 720p camera-only
~19.9 FPS, sequential ~19.8-20, latest ~20 despite driver reporting MJPG/60 FPS.
No clear threading gain at this capture rate. One startup timeout retried with
20s initial wait successfully. No application defaults/input/calibration changed.
See docs/plans/pipeline-experiment-results-vi.md; investigate capture conditions
before claiming 60 FPS or integrating pipeline changes.

Latest: thumb_lock mode integrated and selected in local user profile with backup.
Thumb tucked follows index; thumb open freezes and confirms lock; curl/re-extend
index left, middle middle, both right. Pinch independently starts left drag after
prepared separation +100ms; relative palm displacement avoids absolute snap.
No Peace scroll in this mode. All3 buttons released on pause/loss/error/exit;
full fist safety requires thumb not open so locked chord is not mistaken for fist.
109 tests pass, compileall/diff pass. Guide/settings/debug instructions updated.
New mode requires application restart; physical hand acceptance pending.

Pinch latch update: separation of thumb/index arms drag without index extension
or0.8s deadline. Contact100ms starts; separation100ms releases with pending
release cursor freeze. Recontact cancels release, hand loss/Pause/fist still
release immediately and clear arming. Preview labels I8/T4 distinguish tips.
111 tests pass, compileall/diff pass. Physical user acceptance pending; prior
recording still contains hand loss that this change intentionally does not hide.

## 2026-09-06 low-latency runtime

Controller uses async latest-only camera/inference; cursor tick stays on Qt.
Debug defaults OFF; enable the Debug toggle before opening Debug recording.
Pinch start/release default 100 ms, adjustable in Advanced recognition.
See docs/requirements/low-latency-runtime.md and docs/plans/low-latency-runtime.md.
116 tests and paused 720p30 desktop smoke passed. Diagnostic recorder remains
synchronous, so compare Controller responsiveness directly rather than treating
recorder FPS as the same pipeline. Real hand-to-display latency is not measured.

Preview update: Skeleton defaults ON independently of Debug OFF; Guide can hide.
Calibration caption removed. Time-based output easing added (18 ms time constant).
117 tests pass; offscreen toggle smoke passes. Real hand smoothness needs testing.

## Legacy fist arming removed

Loaded profiles now ignore legacy arming.enabled; keyboard fist no longer toggles
input. Settings/Controller guide remove the old gate. Existing bindings operate
while ACTIVE; Pause/hand loss/calibration/exit still release held keys. New
Ctrl/Shift/Alt poses and the new two-hand toggle are not implemented yet.

## Gesture Hand v1 test build

V1 code integrated into runtime + Settings > Gesture v1. Personal profile enabled
with backup data/user_profile.json.pre-gesture-v1.bak. New count bindings/symbols/
corners empty; two-hand input On, optional 3 s fist switch Off. Ctrl/Shift/Alt
confirm 1 s; existing drag 100 ms. Scroll starts only after hand translation.
New config/gesture_v1_profile.json and migrate/replay scripts available.
Use docs/gesture-hand-v1-testing-vi.md. Full unit/smoke verification exists, but
physical acceptance of new poses, cross-platform input and complete app zoom
coverage remain pending. No exe build or commit made for this test iteration.

## Unified pointer sources / Gestures

Current personal and new desktop template default to palm. Mouse Settings exposes
Palm and Index fingertip; Gestures replaces both old gesture pages. Palm does not
thumb-lock, fingertip does. Palm calibration is separate and initially required;
keep existing fingertip file. 140 tests and unified Settings smoke passed. See
requirements/pointer-source-unification.md. Restart the app to load this change.

Settings clarity: no I8/T4 captions; color markers retained. On/Off switches have
text + thumb position. Gestures grouped into four tabs; named action picker still
accepts custom shortcuts. Voice placeholder hidden. UI appearance inspected via
offscreen renders with Windows font. Restart to load UI changes.


## Camera/preview Settings and drag-volume arbitration

Camera selection now lists device names with capture-backend indices; Logitech
BRIO and virtual cameras enumerated successfully on Windows. Refresh preserves
an unplugged selection. Skeleton/Guide preferences persist locally; Debug stays
session-only and starts Off. Preview & Debug replaces the redundant Keyboard
page and the four main-window controls. Save & open Debug recording pauses and
hands the camera to the diagnostic window; Start is still required to record.
The packaged data list now includes the Gesture v1 default profile.

Volume now requires four extended fingers and clear thumb/index separation.
Approaching pinch or curling fingers exits volume without losing drag readiness;
assigned OK retains priority, and an active drag cannot be taken over by volume.
Drag confirmation stays 100 ms. Both pointer sources have regression coverage.
146 deterministic tests passed; compileall/diff checks and offscreen Settings
render passed. Physical drag/volume acceptance and a new exe build are pending.
Changes are local and have not been pushed to GitHub.


## Unified gesture fine tuning

Removed Advanced navigation and its page. Gestures > Fine tuning now groups the
four active pinch controls under Click & Drag, motion spacing/sensitivity under
Scroll / Zoom / Volume, and confirmation/corner timing under Keys & Symbols.
Pose confirmation is explicitly shared with motion gestures. Legacy activation
frames, drag hold time, scroll deadzone and confidence controls are no longer
shown; their stored fields remain compatible. Runtime behavior and personal
settings are unchanged. Verified 146 tests, compileall, diff check and an
offscreen render of the grouped page. Restart the app to load the new layout.


## Shared main integration (2026-09-07)

Integrated windows commit 66e93d9 into main after fetching remote PR #1.
Main is the shared Windows/macOS source branch; build platform artifacts separately.
Review found platform-guarded Windows capture settings and a Darwin AVFoundation
camera-enumeration dependency. Windows verification: 146 tests, compileall and
pip check passed. macOS runtime, permissions, camera and packaging remain untested
on this host; see docs/plans/macos-main-verification.md for the acceptance steps.
This entry supersedes earlier notes that the UI changes were not yet pushed.


## System tray and Start label (2026-09-07)

Desktop launcher now installs a macOS menu-bar / Windows tray icon with
Open Controller, Start/Pause, Settings and Quit. Icons and menu status distinguish
Active, Paused and Error. Escape hides Controller in the tray; if no tray exists,
it minimizes the window. Window close, Alt+F4, Cmd+Q, Quit and --quit-after shut
down the application. Application quit also runs
idempotent cleanup, attempts all child/runtime cleanup and removes the tray icon.
Hidden processing continues; preview painting is skipped. Errors reopen Controller.
Start is blocked during Settings, diagnostics, calibration, shutdown and errors.
All user-facing Resume labels in Controller/Settings are now Start.

Validation: 153 deterministic tests passed on macOS; compileall and diff check
passed. Native Cocoa smoke with simulated input verified tray availability,
hide/reopen, running timer while hidden, Start/Pause and shutdown/icon removal.
Controller screenshot verified Start label. No new real-camera/active-input
acceptance or packaged/Windows tray test was performed for this change.
Restart the source app to load it; older packaged apps require rebuilding.
See docs/requirements/system-tray.md and docs/plans/system-tray.md.


## Tray resource optimization (2026-09-07)

Supersedes the earlier note that hidden paused processing continues. Hidden
Active retains inference/input and freshness safety, but skips runtime overlays,
periodic debug logs, preview painting and status widget updates. Hidden Paused
releases input, closes camera/inference resources, clears the last snapshot and
stops the frame timer. Start reopens perception then enables input with a fresh
acceptance timestamp. Opening Controller reopens preview while remaining paused.
Profile/calibration stay in memory. Visible paused preview is intentionally kept.
Wake errors restore a visible safe error state; Settings/diagnostics keep their
exclusive handoff. No personal settings or recordings changed.

Validation: 158 deterministic tests, compileall and diff check passed. Three
lifecycle tests also passed with native Cocoa and mocked camera/input resources.
Actual camera wake latency, CPU/power savings and Windows acceptance are unmeasured.
Restart source app to load this change. See docs/plans/tray-idle.md.

## Tray close behavior correction (2026-09-07)

Escape now hides Controller in the menu bar/system tray. Window close, Alt+F4,
Cmd+Q and tray Quit shut down the application, release input, stop camera/workers
and remove the tray icon. If a system tray is unavailable, Escape minimizes the
window. This supersedes the earlier close/hide wording above. Validation: 160
tests, compileall and diff check passed; native macOS smoke verified Escape hide,
reopen and window-close shutdown.

## macOS source update ready for GitHub

Controller no longer shows the hotkey hint block. Display resolves the controlled
screen to its Qt name, including Built-in Retina Display, DELL U2424HE and ARZOPA
on this Mac. The Start label, tray lifecycle and idle resource changes are shared
source; Windows and rebuilt packages still need acceptance.

See docs/plans/tray-performance-results.md for the measured M4 comparison:
hidden Paused substantially reduced process CPU and RSS; active tray did not show
a demonstrated CPU/FPS advantage in the short live-camera samples. No changes to
the recognition model or pointer filtering were made as part of this update.
