# System tray implementation

1. Add a Qt tray component with state icons and menu actions using existing
   Controller callbacks. Use QSystemTrayIcon availability for Escape fallback.
2. Route Escape to tray hiding. Route window close, Alt+F4, Cmd+Q and explicit
   Quit through shutdown. Keep frame processing running while hidden and skip
   preview painting.
3. Synchronize tray state and Start gating with Controller lifecycle transitions.
4. Add deterministic lifecycle tests for Escape hide/reopen, window-close exit,
   Start gating,
   release on pause/quit, and hidden errors. Run full tests, compileall, diff check.
5. Verify native macOS tray lifecycle with a simulated runtime, then document
   results and remaining Windows/packaged acceptance.

Reference: https://doc.qt.io/qtforpython-6/PySide6/QtWidgets/QSystemTrayIcon.html

Completed: implementation and 160-test suite pass, compileall/diff pass. Native
macOS tray smoke passed for Escape hide, reopen and window-close shutdown;
Controller Start label visually checked.
Windows, packaged builds and real active input while hidden remain acceptance work.
