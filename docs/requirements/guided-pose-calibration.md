# Guided pose calibration

Calibrate offers Movement area (existing) and Hand poses (new, palm/thumb-lock
modes). Pose calibration learns bounded thumb openness and index/middle curl
angles for the selected mouse hand, not a new ML model or keyboard poses.

- Pause and release every input before opening; block Start until closed.
- Collect five explicit poses using fresh, confident, in-frame landmarks after
  a countdown. Require multiple stable frames and separated pose distributions.
- Never mutate live thresholds during collection or preview.
- Preview left/middle/right curl clicks with a side-effect-free state machine;
  require all three and a tucked thumb before enabling explicit Save.
- Save atomically in local data, keyed by mouse role and swap setting. Invalid
  files fall back to defaults. Cancel/close/error retains the old calibration.
- Keep movement calibration, pinch/drag thresholds, keyboard gestures and timing
  unchanged. Persisted settings need real-camera user acceptance; no guarantee
  of higher accuracy without measurement.
- Offer retry, restart and confirmed reset to defaults. Do not store images.

## Usability correction

- Provide Vietnamese instructions, a schematic hand example and a live camera
  view with distinct labels. Explain which fingers move and which stay extended.
- Separate static sample capture from curl/re-extension click rehearsal.
- Countdown allows the user to leave the physical mouse before showing the pose.
- Review each captured pose; Next is explicit and Retry replaces only that pose.
- Rehearsal presents one pending task at a time with a demonstration and clear
  completion state. Never enable Save before all existing validation passes.
- Explain that --start-paused overrides the saved startup setting, and that
  closing Settings/calibration never resumes control automatically.
- Disable the legacy edge-switch setting for Palm/Thumb lock, which bypass that
  recognizer. Do not claim the setting works in the current pointer modes.
