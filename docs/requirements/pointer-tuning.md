# Pointer response and pinch safety

Date: 2026-09-05. Requested after Windows physical testing reported lag, uneven
movement and unintended right clicks.

- Reduce redundant detection work by using MediaPipe video tracking with strictly
  increasing frame timestamps. Keep processing local and synchronous for now.
- Add optional speed-adaptive cursor smoothing: stronger filtering for fine motion
  and quicker response for large motion. Normalize response to elapsed frame time.
- Require configurable stable pinch confirmation before mouse-down, but release
  immediately on opening, fist, hand loss, pause, calibration or exceptions.
- Reject ambiguous simultaneous pinches. Once a button is held, do not start the
  other until both mapped pinches have opened. Preserve existing drag behavior.
- A middle-finger pinch can start only with that finger raised, preventing a
  folded middle finger beside the thumb from triggering a click. Once held,
  distance hysteresis controls release without the pose prerequisite.
- Expose adaptive smoothing and pinch confirmation time in Settings with help.
- Preserve saved mappings unless the user selects a revised mapping. Back up the
  local profile before tuning it; keep backups ignored by Git.
- Validate behavior with deterministic tests, settings persistence and a paused
  real-camera smoke test. Physical feel and mistaken-click rate require user UAT.
