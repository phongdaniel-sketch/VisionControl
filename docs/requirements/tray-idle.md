# Tray resource use

- Hidden Active keeps tracking, gesture arbitration, cursor ticks and emergency
  releases; skips preview overlays, preview painting, widget status and debug logs.
- Hidden Paused stops camera/inference workers and the frame timer, clears stale
  snapshots and releases input. Existing profile and calibration stay in memory.
- Start from tray reopens perception before enabling input. Open Controller
  reopens paused preview. Failed wake stays safely paused with a visible error.
- Settings/diagnostics own their existing camera handoff; never wake a competing
  camera. Quit also works from suspended state. No recordings or personal edits.
