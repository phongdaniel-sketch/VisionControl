# Responsive controls and device defaults

Status: APPROVED (user request on 2026-08-27)

## Defaults

- Use local camera index `1` when no saved desktop setting exists.
- Default pointer mapping to `fixed` mode on the operating system's primary
  display.
- Keep the primary display at fixed index `0` even if the display enumeration
  order returned by the platform changes.
- Prefer a responsive cursor default with less filtering and a smaller movement
  deadzone while retaining both controls in Settings.

## Settings responsiveness

- Opening Settings must pause and release input, then stop the Controller frame
  timer so MediaPipe inference and camera rendering do not compete with Settings
  navigation on the GUI thread.
- Closing Settings without saving must restart frame processing while remaining
  paused.
- Saving Settings may rebuild the runtime as before and must remain paused.

## Display selection and field contrast

- Replace the numeric fixed-display selector with a named display list.
- Each display option must show the operating-system name, logical resolution,
  and an explicit `Primary` marker where applicable.
- Preserve the validated numeric fixed-display index in the saved profile.
- Text fields, combo boxes, and numeric fields must have a clearly visible
  border and surface against Settings cards.
- Combo drop-down and spin-box increment/decrement areas must use visible,
  high-contrast controls in normal, hover, focus, and disabled states.

## Feedback

- Label the displayed FPS as measured processing FPS. It represents completed
  tracking/render cycles, smoothed for readability, rather than a configured
  camera frame-rate claim.
- Explain that higher cursor response follows the hand faster and a smaller
  deadzone detects smaller movements.

## Acceptance criteria

- Fresh/reset settings select camera `1`, fixed display mode, primary display,
  cursor response `0.60`, and deadzone `0.5 px`.
- Settings navigation does not run concurrent camera/tracking frames.
- Existing safety release behavior and deterministic tests remain intact.
