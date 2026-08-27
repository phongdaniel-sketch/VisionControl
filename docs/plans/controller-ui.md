# Plan: Controller and Settings UI refresh

Status: IMPLEMENTED

## Implementation

1. Extract one-frame runtime processing so CLI and Qt controller share the same
   safety and gesture logic.
2. Build a PySide6 Controller window with embedded camera, status cards, actual
   gesture guide, Pause/Resume, disabled Voice, and Settings.
3. Refactor Settings into an importable window with sidebar pages and the
   existing validated profile controls.
4. Change the desktop launcher to Controller-first while preserving explicit
   `--settings` and legacy CLI entry points.
5. Add deterministic state tests and offscreen render checks, then perform a
   paused camera smoke test.

## Safety

- Opening Settings pauses the runtime before constructing the window.
- Runtime reconfiguration and shutdown release input before replacing adapters,
  controllers, camera, or tracker instances.
- Exceptions stop the frame timer and close runtime resources before reporting
  the error.

## Rollback

- The existing `vision_control.app` CLI remains available independently of the
  desktop controller UI.
