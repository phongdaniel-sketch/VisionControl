# Start in tray

Persist start_minimized, default false for old settings. Add exact user-requested
label Alway start at mini mode. Apply on next controller launch, including login
launch; do not change pause preference. Skip splash/loading windows in mini mode.
Use existing tray lifecycle without showing the main window first. Fall back to
visible controller if tray is unavailable. Startup errors remain visible.
Verify settings round-trip, hidden startup/reopen and unavailable-tray fallback.
