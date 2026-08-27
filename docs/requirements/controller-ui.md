# Controller and Settings UI refresh

Status: APPROVED (user clarified the target interaction on 2026-08-27)

## Product behavior

- Launch into the VisionControl controller, not the Settings window.
- Embed the live camera preview and hand landmarks in the controller window.
- Open Settings only when the user presses the controller's Settings button.
- Pause and release all held input before Settings opens. Closing Settings must
  never resume control automatically.
- Keep Voice visible as a disabled “Coming soon” control.
- Show only the gestures already defined by VisionControl. Do not imply that
  users can train or add arbitrary gestures.
- Preserve Disabled, Press, Hold, and multi-key chord mapping.
- Keep Camera frames local and do not add telemetry.

## Controller requirements

- Make Pause/Resume the dominant safety action.
- Show tracking, mouse-hand, gesture, mouse action, monitor, and keyboard
  ARMED/DISARMED state without relying on color alone.
- Keep gesture guidance compact and derived from the actual configurable gesture
  list, with fist documented as reserved for arming.
- Preserve keyboard shortcuts: Escape, P, C, Space, and R.
- Release every held mouse button and key on pause, Settings, calibration, hand
  loss, window close, initialization failure, and frame-processing exceptions.

## Settings requirements

- Use a dark sidebar layout with General, Camera, Mouse, Gestures, Keyboard,
  Displays, Voice, and Advanced destinations.
- Disable Voice navigation and label it as planned functionality.
- Do not open a second camera stream while the controller owns the camera.
- Save validated settings locally. Applying saved settings restarts the runtime
  in a paused state.
- Retain native window frames for cross-platform resize, movement, and
  accessibility behavior.

## Acceptance criteria

- The packaged launcher opens Controller directly.
- Settings is absent until its button is pressed.
- Voice is visible and disabled in both Controller and Settings.
- Controller and Settings render at laptop-friendly sizes and tolerate smaller
  screens through scrolling or responsive layout.
- Existing deterministic behavior remains covered and all required verification
  commands pass.
