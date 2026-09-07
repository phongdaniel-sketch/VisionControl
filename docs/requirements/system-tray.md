# System tray and Start label

- Provide macOS menu-bar / Windows tray controls: Open Controller, Start/Pause,
  Settings and Quit, with visible Active/Paused/Error state.
- Escape hides Controller in the tray while preserving its current Start/Pause
  state. If a tray is unavailable, Escape minimizes the window so it is not lost.
- Closing Controller, Alt+F4, Cmd+Q and explicit Quit exit the application.
- Settings, diagnostics, calibration and errors block Start. Settings pauses
  input; saving returns paused. Hidden runtime errors restore the window.
- Exit closes child windows, releases all input, stops camera/workers, and removes
  the tray icon. Application quit must also clean up the runtime.
- Replace user-facing Resume with Start throughout Controller and Settings.
- No changes to personal profiles, camera privacy or gesture behavior.
