# macOS packaged-app acceptance

Updated: 2026-08-27 (Asia/Ho_Chi_Minh)

## Automated checks completed

- PASS: `VisionControl.app` Settings remained running for an 8-second launch
  smoke test.
- PASS: packaged controller opened physical camera index `1` with
  `--start-paused` and remained running for 25 seconds.
- PASS: rebuilt Controller-first PySide6 `.app` embedded camera index `1`,
  detected one and two hands, stayed paused/DISARMED, and closed cleanly after a
  20-second smoke test.
- PASS: offscreen render and deterministic UI test confirm Settings does not
  exist until its button is pressed and Voice is disabled in both windows.
- PASS: runtime output confirmed `paused`, keyboard `DISARMED`, display mapping,
  MediaPipe GL initialization, offline hand model loading, and TFLite XNNPACK.
- PASS: app metadata includes `NSCameraUsageDescription`.
- PASS: `codesign --verify --deep --strict` on the ad-hoc local app.
- PASS: ZIP integrity, DMG checksum, read-only DMG mount, bundled app signature,
  and bundled offline model presence.

## Manual checks requiring a person

Grant Camera and Accessibility to `VisionControl.app`, start paused, and record
PASS/FAIL for each item:

- [ ] Camera preview and two-hand role recognition.
- [ ] Mouse movement, left/right/middle pinch, drag, scrolling, and calibration.
- [ ] Keyboard arming/disarming, Press actions, Hold actions, and multi-key chords.
- [ ] Active/fixed/all monitor behavior and point-pose edge dwell switching.
- [ ] Pause releases held mouse buttons and keyboard keys.
- [ ] Mouse-hand loss releases held mouse buttons.
- [ ] Keyboard-hand loss disarms and releases held keys.
- [ ] Calibration, normal exit, and an induced camera failure release all input.

Physical gesture behavior and macOS Accessibility-generated input cannot be
validated safely by a headless deterministic test. Do not mark these items PASS
without observing them on the target Mac.
