# Controller clarity and guided calibration

Requested 2026-09-05 after user screenshots showed an unlabeled keyboard-only
gesture guide, raw Windows display identifiers and inaccessible calibration.

- Guide explicitly selects Mouse hand or Keyboard hand, shows current mappings
  and explains the poses, including safety actions and keyboard arming.
- Status distinguishes actual detected poses from paused input and keyboard arming.
- Display names remove Windows device prefixes for presentation only; preserve
  raw identifiers in tooltips and internal monitor mapping.
- A visible Calibrate button starts a four-step, paused workflow with live preview,
  direction instructions, hand visibility feedback, capture/countdown and cancel.
- Capture can use Space or a three-second countdown to avoid moving the hand to
  click a UI button while capturing. App shortcuts work within the Controller.
- Missing hands/invalid bounds/save errors are actionable and do not close the
  camera. Cancel and completion remain paused; old saved calibration survives
  incomplete or invalid sessions. Calibration data remains local.
