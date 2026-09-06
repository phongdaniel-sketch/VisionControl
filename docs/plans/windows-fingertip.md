# Windows readiness and fingertip mode implementation plan

Date: 2026-09-05
Requirements: [windows-fingertip.md](../requirements/windows-fingertip.md)

## Progress (2026-09-05)

- Steps 1-3 implemented, with 56 passing deterministic tests and successful
  compilation/diff checks. Physical fingertip/drag usability remains unverified.
- Step 4 partially complete: platform-specific fresh camera defaults, Windows
  DirectShow selection, Settings visual inspection, and 15-second paused camera
  0 smoke test (physical hands detected, clean exit) outside the sandbox.
- Remaining: actual input/gesture acceptance, mixed-DPI verification, macOS
  regression, CI and standalone Windows packaging/signing.

## 1. Establish the Windows baseline

Completed 2026-09-05: Python 3.11.9 AMD64 installed, `.venv311` and editable
installation ready, 41 tests plus compileall/pip check/diff checks pass. Bundled
model inference on a synthetic blank frame passes. PowerShell helper implemented
as `scripts/windows.ps1`. Physical camera/input testing remains pending.

- Create local branch `windows` from `main`; no remote push or release implied.
- Install/locate Python 3.11 and create `.venv311`. Install requirements and the
  editable package. Record OS, architecture and dependency versions.
- Run existing tests before code changes. The original machine had no `.venv311`;
  registered Python 3.13 could not be launched (Access is denied). This is now
  resolved by the dedicated Python 3.11 environment.
- Add repeatable PowerShell setup/test/run scripts with explicit interpreter
  paths, exit-code checks and paused camera startup.

## 2. Fix safety issues in shared code

- `input_adapter.py`: track single-key presses and release all inputs independently
  on failures, preserving failed entries for retry.
- `controller_ui.py`: route Settings reload failures to the safe error UI instead
  of closing the application.
- `runtime.py`: reuse role assignment during calibration and reject missing mouse
  hands even when the other hand remains visible.
- Add deterministic failure-injection and role-swap regression tests, including
  partial chord release failures and both mouse buttons held.

## 3. Add the pointer option without breaking profiles

- `profile.py`, `settings.py`, default profile: add a validated pointer-mode field
  with a backward-compatible default. Keep it separate from existing pose mappings.
- `controllers.py`: compute effective move eligibility from the selected mode;
  reuse index-tip coordinates and keep existing click/scroll processing.
- `settings_ui.py`: add the two choices, hand-visibility explanation, and clarify
  effective movement restrictions without overwriting stored custom mappings.
- `overlay.py` / Controller preview: highlight the tracked index tip in this mode.
- Test missing/invalid values, settings round trip, mode switching, movement only
  for pointing, fist/hand-loss release, pinch/drag/scroll and keyboard independence.
- Physically evaluate pinch-to-drag ergonomics; adjust the documented behavior if
  tracking cannot reliably preserve a held pinch while returning to pointing.

## 4. Verify Windows runtime and packaging

Camera investigation 2026-09-05: default OpenCV backend took approximately 25
seconds during startup outside the sandbox, then processed frames successfully.
Explicit DirectShow opened camera 0 and read a frame in approximately 3 seconds.
Select DirectShow on Windows; retain the existing default backend on macOS.
Sandbox camera access itself was unavailable in this session.

- Verify camera index on this machine; do not carry over the Mac-specific index 1
  assumption. Make fresh Windows defaults appropriate without overriding profiles.
- Measure monitor and pynput coordinate consistency at 100%, 125%, 150% scaling
  and mixed scaling. Add Windows DPI initialization before UI/input creation only
  if required by the verified coordinate behavior.
- Make `VisionControl.spec` select `.ico` for Windows and retain `.icns`, BUNDLE,
  entitlements and signing on macOS. Test the Windows standalone folder first.
- Add Windows/macOS CI for deterministic tests on Python 3.11, with headless UI
  setup and no physical input or camera activation.
- Complete the Windows checklist below; rerun macOS UAT for shared changes.
- Produce an unsigned internal Windows test build, then plan installer and
  Authenticode signing as a later distribution step.

## Windows source test procedure (PowerShell)

Prerequisite: Python 3.11 installed and visible to `py -3.11`. Setup and automated
checks now pass through `scripts/windows.ps1`; camera launch remains untested.
Run from the repository root;
stop and resolve errors at each step before continuing.

```powershell
py -3.11 --version
py -3.11 -m venv .venv311
.\.venv311\Scripts\python.exe -m pip install -r requirements.txt
.\.venv311\Scripts\python.exe -m pip install -e .
$env:PYTHONPATH = 'src'
$env:QT_QPA_PLATFORM = 'offscreen'
.\.venv311\Scripts\python.exe -m unittest discover -s tests -v
.\.venv311\Scripts\python.exe -m compileall -q src tests scripts
git diff --check
Remove-Item Env:QT_QPA_PLATFORM
.\.venv311\Scripts\python.exe -m vision_control.launcher --camera-index 0 --start-paused
```

If index 0 fails, select the correct physical camera in Settings and save, or
relaunch with its index. No virtual-environment activation script is required.

## Physical Windows checklist

- [ ] Preview opens paused and keyboard DISARMED; model initializes locally.
- [ ] Mouse/keyboard roles are correct with one and two hands and role swapping.
- [ ] Existing movement, click, drag, scroll and calibration work.
- [ ] Fingertip mode, after implementation, moves only for its intended pose and
      survives switching back without losing previous mappings.
- [ ] Pause, hand loss, fist, calibration, Settings and exit release held inputs.
- [ ] Camera disconnect/retry leaves an actionable paused error state.
- [ ] Press/Hold/chords work in a normal desktop test application.
- [ ] Single/multiple monitors and scaling combinations map cursor correctly.
- [ ] Packaged build starts without a separately installed Python and persists
      settings under the Windows application-data directory.

Do not mark these physical checks complete based only on automated tests.
