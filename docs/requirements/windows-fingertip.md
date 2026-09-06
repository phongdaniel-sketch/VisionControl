# Windows 11 and fingertip control

Date: 2026-09-05
Status: Planned; implementation and physical acceptance pending.

## Platform support

- Support macOS Apple Silicon and Windows 11 using Python 3.11 and MediaPipe
  0.10.21. Keep one shared tracking/controller/settings implementation.
- Develop Windows readiness on branch `windows`; integrate portable fixes back
  into `main`. Do not duplicate the application into separate OS source trees.
- Keep OS input effects in the input adapter; isolate DPI/bootstrap and packaging
  differences behind platform checks. Preserve the existing macOS release flow.
- Keep camera frames local. Ship the offline hand model in both desktop builds.

## Pointer mode

The existing controller already maps index fingertip landmark 8 to the cursor.
The new option changes when pointer movement is enabled, not the tracking model.

- Settings exposes `Current gesture controls` and `Index fingertip` modes.
- Preserve existing profiles and their custom move/click/scroll mappings when the
  new mode field is absent or when switching back to the existing mode.
- In fingertip mode, move only during the index-only pointing pose, using landmark
  8 with existing calibration, smoothing and deadzone settings.
- Keep configured pinch clicks and scrolling available. During a pinch, freeze
  the pointer at the last position; returning to a pointing pose while a button
  remains pinched may resume movement for dragging. Verify this interaction with
  physical gestures before considering the feature accepted.
- A fist stops pointer movement and releases mouse buttons in either mode.
- Explain in Settings that the hand must remain visible for reliable tracking;
  detecting a lone fingertip with the hand outside the image is a separate future
  detector investigation, not an acceptance claim for this milestone.
- Show a visible index-tip marker in the preview when fingertip mode is selected.
- Save mode changes through the existing paused Settings reload flow.

## Safety and acceptance

- Attempt every held key/button release even if another release raises; retain
  failed release state for retry. A single-key press must participate in cleanup.
- Pause, hand loss, calibration, Settings, exit and exceptions release applicable
  held inputs. Keyboard arming remains independent of pointer mode.
- Camera retry failures keep the Controller visible and safely paused.
- Calibration uses the same role assignment as frame processing; if the mouse
  hand is absent, reject capture rather than using the keyboard hand.
- Run deterministic unit tests and compilation on Python 3.11, plus diff checks.
- Physically verify both modes on Windows 11 and regress macOS before release.
- Verify Windows display scaling, mixed-DPI displays, negative monitor origins,
  camera failure/retry and actual OS mouse/keyboard events.
