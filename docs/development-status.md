# Development status

## Voice close-command recognition (2026-09-25)

- Added close-window phrases to the local Whisper decoding prompt and explicit
  allowlisted variants for common Vietnamese recognition output such as `tắt áp`.
- Canonical `Đóng cửa sổ` and `Tắt app` behavior is unchanged. Confidence,
  foreground-target, modifier-release and single-action safety checks remain active.
- No fuzzy command matching, background recording or diagnostic logging was enabled.
- Physical BRIO acceptance remains required after rebuilding the Windows bundle.

## Gemini transcription and custom hotkeys (2026-09-21)

- Added opt-in Gemini 2.5 Flash transcription, explicit audio-upload consent,
  masked API-key field and Windows user-scoped DPAPI storage. Local remains default.
- Gemini errors are sanitized; no key in config/log/URL, no redirect forwarding,
  no retries or automatic cloud fallback, bounded WAV upload after voice activation.
- Configurable Ctrl/Alt/Shift hotkeys, legacy migration, native checks for
  Ctrl+Shift+Space and Ctrl+Space. Save closes on success, errors stay visible.
- 329 tests passed, native DPAPI roundtrip and UI checks passed, compileall and
  diff checks passed. API tests mocked; no real key, network request or mic capture.
- EXE rebuild and physical voice/API acceptance remain pending.

## Voice toggle and pointer corners (2026-09-21)

- Implemented Controller Voice activation, bounded single-utterance VAD, repeat
  toggle/Escape cancellation, countdown, micro refresh, and local action routing.
- Replaced pose-driven corner sequence with .7 s pointer dwell and entry latch;
  suppresses drag, volume, scroll, pause and modal operations. Existing gesture
  corner bindings preserved; added corner_dwell_seconds setting.
- Added media, desktop, task view, screenshot, This PC, undo/redo, Escape, pause
  gestures and Voice Listen Toggle actions. No Gemini/cloud integration.
- Native Windows button/settings screenshots and Vietnamese synthetic speech VAD
  smoke passed. Real microphone/camera acceptance and EXE rebuild remain pending.
- Regression suite: 272 tests passed, including audio endpoint and pointer-to-voice
  action integration. No live microphone capture was performed during verification.

## Keyboard three/four/open correction (2026-09-05)

- User screenshot showed an open left palm labeled Four fingers. Removed the
  fixed image-X thumb test and Y-only finger counts from static classification.
- Thumb spread is measured against the palm's index-to-pinky axis, with joint
  extension and a rejection band. Finger states use aspect-corrected joint and
  reach geometry. Uncertain states return None and release held keys.
- Runtime and keyboard/mouse controllers use actual frame dimensions. Existing
  profile bindings and calibration unchanged.
- PASS: 87 tests, compileall and diff checks. Tests include both hand labels,
  mirroring, in-plane rotation/scale, aspect ratios, D/S/Space dispatch and key
  release on uncertain thumb geometry. Physical user verification pending.

## Pinch versus fist (2026-09-05)

- User confirmed the guided calibration works, then reported mouse pinch/fist
  confusion. Mouse fist recognition now uses joint bend plus palm/wrist proximity
  in aspect-corrected landmark coordinates instead of only vertical ordering.
- New clicks require the corresponding finger recently extended with its thumb
  pinch open (within .8 s). Pending/held clicks tolerate bending; a clear fist,
  pause or hand loss releases immediately and clears preparation.
- Mouse status uses the same fist rule; keyboard gesture rules remain unchanged.
- PASS: 82 tests, compileall, diff checks. New synthetic-joint tests cover
  in-plane rotation/scale, cold-start pinches, release, timeout and swapped clicks.
- Physical click accuracy needs user retesting. Downward cursor movement during
  pinching still requires the separate click-position anchoring improvement.
- Public-source findings and links are in `docs/plans/pinch-fist.md`.

## Controller clarity and calibration (2026-09-05)

- Guide now selects Mouse hand / Keyboard hand and describes the configured
  movement, clicks, scroll, shortcuts and fist safety behavior.
- Status displays actual mouse/keyboard poses even while input is paused.
  Windows device prefixes are removed from display labels, retained in tooltips.
- Visible Calibrate button starts a paused four-step preview workflow. Capture
  with Space or a three-second countdown; missing-hand and invalid-boundary
  feedback keeps the current step. Cancel/completion remain paused.
- Calibration saves atomically; an unsuccessful write leaves the old file and
  allows the last step to be retried. Successful capture shows a saved message.
- PASS: 73 tests, compileall, diff checks and offscreen Controller/calibration
  visual review. Includes focused-button Space capture and local persistence.
- User physical calibration acceptance remains pending.

## Pointer tuning after Windows user test (2026-09-05)

- User reported lag, uneven pointer motion and unintended right clicks.
- VIDEO tracking with monotonic millisecond timestamps replaces per-image detection.
- Optional time-normalized adaptive smoothing is exposed in Mouse Settings.
- Pinch confirmation is configurable in Advanced; ambiguous pinches are rejected,
  button switching requires opening both pinches, and release remains immediate.
- Starting a middle pinch requires a raised middle finger; held pinches still use
  distance hysteresis. Gesture mappings remain editable and were preserved locally.
- Local profile backed up and tuned: response .70, adaptive on, deadzone .8 px,
  pinch close/open .28/.45 and confirmation .10 s.
- PASS: 64 tests, compileall and diff checks, plus offscreen Settings visual check.
- Camera timing (45 frames, no input): before 25.8 ms median tracking / 25.3 FPS;
  after 25.9 ms / 25.3 FPS. No measured FPS improvement is claimed. These are
  separate short runs, not controlled end-to-end latency measurements.
- User must recheck pointer feel, deliberate right-click ergonomics and false
  clicks. Capture buffering and separating inference from the UI remain possible
  next investigations if latency persists.

## Windows baseline (2026-09-05)

Implementation update:

- Shared input cleanup attempts all releases on error and retains failed adapter
  state for retry; calibration rejects a missing/ambiguous swapped mouse hand.
- Settings camera retry errors remain visible in ERROR / PAUSED.
- Mouse Settings offers Current gesture controls / Index fingertip, persists the
  choice without overwriting gesture mappings, and highlights the index tip.
- Fresh Windows settings use camera 0; macOS retains camera 1. Windows uses
  DirectShow after a substantially faster startup was observed on this machine.
- PASS: 56 deterministic tests, compileall, diff check; Mouse Settings visually
  inspected through an offscreen render with Segoe UI registered for the renderer.
- PASS: camera 0 Controller smoke test outside sandbox, 15 seconds processing
  physical hand detections, always PAUSED / DISARMED, exit code 0.
- Pending: actual cursor/click/drag/chord ergonomics, DPI combinations, Windows
  packaging and macOS regression. No active OS input acceptance is claimed.

- Python 3.11.9 AMD64 and `.venv311` are ready on local branch `windows`.
- Requirements and editable installation succeed; `pip check` passes.
- All 41 existing tests pass with Qt offscreen; compileall and diff checks pass.
- Bundled MediaPipe 0.10.21 model loads and processes a synthetic blank frame.
- `scripts/windows.ps1` provides setup, test and paused run commands.
- The original baseline below predates the implementation update above. See
  `docs/plans/windows-fingertip.md` for the Windows sequence.

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

## Local diagnostic sessions (Windows)

Run `./scripts/windows.ps1 diagnose -CameraIndex 0`. The separate window opens
paused. Start begins a three-second countdown and records at most 30 seconds of
webcam plus a synthetic pointer canvas, without desktop capture, audio, or OS
input. Uses the current profile and calibration with a fixed 640x480 test area.
Artifacts under ignored `data/captures/<session>/`: `session.avi`, `frames.jsonl`,
`metadata.json`, `summary.json`. Frame numbers and elapsed timestamps align video
with landmarks, poses, pinch decisions, simulated clicks and stage timings.
AVI playback uses nominal 30 FPS; measured processed FPS is in the summary.
This does not measure sensor-to-screen latency or real Windows input delivery.
Validation: 91 deterministic tests passed, compileall and diff check passed.
Actual user recording and analysis remain pending; camera preview opened paused.

## Pointer recovery correction — 2026-09-05

Mouse point recognition now tolerates naturally curled unused fingers while
keyboard counting remains strict. Interrupted pose recovery caps movement at
12% of target diagonal per nominal 30 FPS frame, scaled by elapsed time up to
50 ms. Fist, pinch preparation/confirmation and emergency releases preserved.
93 tests pass; compileall and diff checks pass. Offline replay of the authorized
846-frame recording: move 183 -> 652 frames, waiting_point 657 -> 188, maximum
canvas step 643.80 -> 300.84 px, no clicks before or after. Remaining large steps
and physical feel require camera acceptance; no claim of complete jitter removal.
Existing calibration/profile unchanged. Restart the application to load fixes.

## Aim/click update

Space toggles Pause/Resume within the focused Controller; calibration retains
Space capture. P remains available, auto-repeat is ignored, and Settings/error/
calibration block resuming. Tooltip documents scope (not a global OS shortcut).
Mouse-only point tolerates moderate index bend (130 degrees plus wrist reach)
with other fingers not extended. This also prepares index pinch while separated.
Adaptive smoothing adds a display-scaled resting radius; prepared approaching
pinches anchor the pointer through confirmation and initial drag-hold interval.
Click thresholds, emergency releases and saved calibration/profile preserved.
97 deterministic tests passed before the aligned preparation change; final suite
must pass as well. Physical occluded-hand and click acceptance remain pending.

## Calibration preview and debug access

Controller now has Show calibration area (preview-only saved rectangle/axes),
Debug recording (exclusive camera handoff to local simulated diagnostic window),
and per-frame Camera read / Tracking / Runtime timings. Closing diagnostics
restores the Controller paused. 99 deterministic tests, compilation and diff
checks passed. Physical camera handoff/visual acceptance still required.
Camera currently requests 640x480 but no explicit FPS. Processing FPS counts
completed UI tracking/render cycles, not advertised camera FPS. Prior recording
had median inference 22.21 ms; 60 processed FPS requires <16.67 ms total per frame.
Calibration maps camera coordinates to selected display bounds, clamps outside
coordinates, then movement eligibility, smoothing and click anchoring apply.

## Thumb lock and three-button curl clicks

Implemented opt-in thumb_lock mode and selected user's local profile with backup.
Click on completed curl/re-extension cycle: index=left, middle=middle,
index+middle chord=right, only after thumb-open lock. Simultaneous window120ms,
curl confirmation60ms, full cycle<=800ms. Pinch separated/prepared first then
held100ms starts relative-palm left drag without prior lock. UI mappings,
Vietnamese guide and diagnostic prompts updated; old modes preserved.
109 deterministic tests pass including all3 clicks, chord arbitration, no
startup pinch, unlocked drag anchor/motion/loss and middle release retry.
Physical camera accuracy not yet verified. No calibration/exposure changes.

## Pinch latch correction

Removed strict extended-index and0.8s preparation from thumb_lock. Observed
separation is required after start/loss, stable100ms pinch activates, stable100ms
opening releases. Brief opening noise holds button and freezes motion; emergency
release unchanged. I8/T4 markers identify index/thumb.111 tests passed. User must
restart app; fresh camera acceptance remains pending. Settings preserved.

## Low-latency Controller update (2026-09-06)

- Controller now uses separate camera/inference workers with latest-only slots.
  Input and independent cursor ticks remain on Qt; stale results (>150 ms) and
  pre-resume results are rejected, with emergency release on stale tracking.
- Thumb-lock free movement uses One Euro filtering plus bounded 30 ms velocity
  prediction. Prediction is disabled during lock/pinch/drag and reset on release.
- Debug toggle defaults OFF each launch: no landmark overlay or periodic vision
  logging; turn ON to enable Debug recording. Recording still requires explicit
  start. Startup/errors remain logged. Calibration overlay is independent.
- Settings > Advanced recognition exposes pinch start/release confirmation;
  both default to 0.10 s. Existing personal start value remains 0.10 s.
- Debug timing shows frame age since camera read and stage total separately;
  neither includes sensor exposure/display scanout. FPS counts delivered results.
- Diagnostic recording still uses its synchronous runtime; its FPS is not a
  direct benchmark of the asynchronous Controller pipeline.
- Validation: 116 tests passed; compileall and diff check passed. Paused 12-second
  desktop smoke opened 1280x720 with driver FPS 30 and exited successfully.
  Actual hand-to-screen latency and gesture feel still require user comparison.

## Preview controls (2026-09-06)

Skeleton is now independent of Debug and defaults ON; Debug still defaults OFF.
Guide has a show/hide toggle and concise thumb-lock instructions that display
current start/release settings. Calibration rectangle no longer draws a caption.
Cursor output uses 18 ms exponential easing with elapsed-time speed limiting;
free movement emits an age-adjusted target rather than briefly stepping back to
an unpredicted sample. Gesture timing and emergency release remain unchanged.
117 tests passed, compileall/diff passed, offscreen toggle smoke passed. Offscreen
font rendering is unavailable in this environment; real desktop visual/hand
acceptance remains pending. No camera session or calibration was changed.

## Gesture Hand v1 implementation — 2026-09-06

Implemented the v1 configuration/editor, geometric features, temporal arbitration,
second-hand modifier holds/count mappings, optional 3 s primary fist switch,
directional scroll, assignable symbols/corners, zoom and volume rotation.
Actions stay behind input adapters; diagnostic recording uses simulated input.
Scroll reserves input only after directional movement, preserving stationary
thumb-lock curl clicks. Zoom requires a full gathered/spread endpoint, not just
one curled index. Landmark jumps and stale gaps cancel input state.

Personal profile migrated with exact pre-v1 backup; legacy bindings preserved but
not used while v1 is enabled. New finger mappings, symbols and corners are empty.
Two-hand input enabled; fist switch Off. New template config/gesture_v1_profile.json.
Use Settings > Gesture v1; old keyboard binding controls are disabled in v1.

Verification: full suite 134 tests, compileall and diff checks passed before the
final zoom endpoint refinement (rerun below). Settings/guide offscreen smoke passed;
12 s paused desktop camera smoke opened 1280x720@30 and exited cleanly.
16 s camera benchmark with simulated input/no GUI: 241 measured frames with hands,
26.17 FPS, tracking p50/p95 38.89/46.88 ms, controller .44/.74 ms, frame age 62/79 ms.
These are not hand-to-display latency measurements. Historical 727-frame replay
completed locally; it is not labelled reference data for the new gestures.

Physical acceptance of new poses remains pending, especially thumb extension for
Shift vs four fingers, OK/drag, gathered zoom and forward-facing volume. Heuristic
spacing thresholds are editable; this is not personalized model training. macOS
hardware and application-specific zoom support are not verified. Do not claim
all milestones accepted or all gesture intentions accurately classified.
See docs/gesture-hand-v1-testing-vi.md for mappings, limitations and replay.

Final verification after zoom endpoint refinement: 134 tests passed; compileall
and git diff --check passed. New poses still require user recording/acceptance.

## Pointer source update

The user-facing Mouse selector now contains only Palm (default) and Index
fingertip. Both use the current gesture engine under Gestures; the extra Gesture
v1 menu and enable toggle are removed. Legacy identifiers remain readable for
backward compatibility, but are no longer presented as selectable user modes.

Palm follows the average of wrist + four MCP landmarks and does not lock on
thumb opening. Open thumb still arms curl clicks; fingertip retains locking.
Palm scroll pose reserves motion immediately; stationary spread palm does not
reserve zoom. Assigned OK preempts new pinch drag; existing drag retains ownership.
Calibration capture uses the selected source. Palm saves mouse_calibration_palm.json;
existing mouse_calibration.json remains the fingertip mapping. Missing palm
calibration shows an explicit hint. Personal profile now selects palm; backup
user_profile.json.pre-pointer-sources.bak preserves the prior configuration.

Verification: 140 tests passed, compileall and diff check passed; offscreen unified
Settings smoke passed (two options, one Gestures menu, no engine enable toggle).
Real palm calibration/click/scroll acceptance is still pending user testing.

## Settings clarity update

Removed I8/T4 text while retaining fingertip color rings and palm marker.
Settings checkboxes now show explicit On/Off text plus switch position/checkmark;
state is no longer conveyed by color alone. Gestures uses Controls, Keyboard,
Actions and Fine tuning tabs. Actions offer named choices and editable shortcuts,
without changing saved identifiers. Numeric fields are compact; camera/general
instructions shortened; unused Voice placeholder hidden.
Verified rendered Settings screenshots with Windows font, switch state and
configuration/action round trips. Final verification: 140 tests, compileall and
diff check passed. No gesture timing, camera,
calibration or personal mappings changed by this UI update.


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

## Palm curl-click arbitration (2026-09-19)

- Fixed Gesture v1 motion-pose arbitration consuming the preparation and release
  frames needed by Palm curl clicks.
- Palm right click remains: thumb open, curl index + middle together, then extend
  both. Left uses index; middle click uses middle.
- Active scrolling retains ownership; drag/pinch and emergency release behavior
  are unchanged. Palm Gesture Guide now matches the implemented controls.
- Focused regression tests cover all three click mappings with scroll enabled.

## Guided hand pose calibration (2026-09-19)

Calibrate now offers Movement area and Hand poses. The new modal wizard collects
five steady poses, fits bounded thumb and index/middle thresholds, and requires
inert left/middle/right click rehearsal plus a tucked thumb before explicit Save.
Samples never modify live settings. Cancel retains the previous calibration;
reset is confirmed. Input remains paused throughout and after the wizard.

Personal calibration is local and keyed by mouse hand / Swap hands; it applies
to Palm and Thumb lock, including primary gesture arbitration. Keyboard poses,
pinch/drag thresholds and movement calibration are unchanged. Invalid files use
default thresholds. No camera images are stored by this feature.

Validation: 179 tests, compileall and diff check passed; the wizard was rendered
offscreen at 720x680 and 580x640 with simulated hand landmarks. Deterministic
capture, persistence, UI workflow and input-safety tests are included.
Real-camera accuracy, native interaction and packaged builds still need user
acceptance. Restart the source app to see Calibrate > Hand poses.

## Calibration guidance and Settings clarity (2026-09-19)

Hand poses now has Vietnamese step instructions, separate schematic/live-camera
views, explicit review/Next, retry of only the last captured pose, and sequential
click rehearsal prompts. The preparation countdown no longer rejects a missing
hand before capture starts. Tracking confidence/freshness checks remain active
during collection. Save still requires all inert rehearsal checks.

Settings now explains that explicit --start-paused overrides the saved Off
preference; returning from Settings/calibration remains paused. Windows helper
run now follows the saved preference unless -StartPaused is explicitly supplied.
No startup preference was changed. Legacy edge switching controls are
disabled for Palm/current Index fingertip, whose runtime bypasses that recognizer.

Validation: 184 tests, compileall and diff check passed. Vietnamese wizard was
rendered offscreen at 820x730 and 640x580; small windows scroll the content while
keeping commands visible. Webcam usability and packaged builds remain unverified.

## Contact right click and paired-curl middle click (2026-09-19)

For Palm and current Index fingertip: index curl/re-extension remains left click;
index + middle curl/re-extension now emits middle click; middle-only curl emits
nothing. Thumb/middle contact emits right click on the first recognized contact,
not on release. Held contact never repeats; clear thumb separation from index and
middle rearms it. Cold contact after startup/pause/loss cannot click until opened.

Right-contact approach/hold reserves the cursor and overrides motion/symbol
arbitration. Ambiguous three-tip contact emits no button. Existing left drag
retains ownership. Guide, Vietnamese rehearsal/example and acceptance cases now
use the same mapping; existing personal geometric calibration is preserved.

193 tests, compileall and diff check passed. Contact rehearsal rendered offscreen.
Real-hand acceptance and new packaged builds remain pending; restart source app.

## Relaxed-hand volume (2026-09-19)

User-selected correction: volume requires all four fingers loosely curled, not
extended/open, with the thumb clearly separated from index and middle. Measured
joint angles distinguish the relaxed pose from pointer/open hand, individual
click curls and a tight fist. Existing pose hold and rotation thresholds remain.
Opening the hand yields pointer ownership in the same update. Pending wide-hand
zoom yields to a deliberate relaxed volume pose; active zoom remains unchanged.

Right-contact/left-drag/symbol priorities and personal calibration are preserved.
Controller guide, Settings and Vietnamese acceptance instructions are updated.
203 tests, compileall and diff check passed; physical camera accuracy still needs
user retest after source restart. Narrow-finger scroll remains a separate pose.

## Volume rollback (2026-09-19)

The user rejected the relaxed-hand experiment after failed Volume recognition
and confusion with Scroll. Restored the previous extended-finger Volume rule,
release conditions and pending zoom priorities; updated the guide accordingly.
Right-contact click, paired-curl middle click, calibration and startup behavior
remain unchanged. All 196 tests, compileall and diff check passed; physical
acceptance requires another real-hand test after restarting the app.

## Duplicate role continuity (2026-09-21)

Added conservative fresh-palm matching for duplicate labels, before arbitration
and snapshot creation. Ambiguity, missing hands and lifecycle release clear
identity history. Click mappings and personal configuration are unchanged.
205 tests, compileall and diff check passed. Offline role replay: 114557 missing
64 -> 18, 114232 0 -> 0, 113409 134 -> 105. Remaining ambiguous candidates are
intentionally blocked. These are role-selection results, not end-to-end latency
or physical acceptance measurements. Restart and real-hand retest remain needed.

## Windows v1.0.0 release (2026-09-25)

Voice Copy, Paste and Close Window now preserve the existing gesture-control
state. Lock Screen remains deliberately different: it pauses input before
locking Windows and requires an explicit Start after sign-in. Close-command
recognition also accepts the documented safe Vietnamese variants.

Package, Python and Windows resource metadata are 1.0.0. The complete Windows
one-directory bundle is packaged as `VisionControl-1.0.0-windows-x64.zip` with
a SHA-256 sidecar. File Version is 1.0.0.0 and Product Version is 1.0.0.

Validation: 431 automated tests, compileall, diff check, PowerShell parse check,
packaged EXE smoke test, version-resource inspection and archive checksum check
passed. No trusted code-signing certificate is installed on the build machine,
so this bundle is unsigned and can trigger SmartScreen. Physical microphone,
gesture, lock-screen and SmartScreen acceptance remain manual checks.
