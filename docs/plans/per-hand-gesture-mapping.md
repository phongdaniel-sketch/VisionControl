# Plan: Per-hand gesture mapping

Status: IMPLEMENTED

1. Add validated mouse-gesture mapping defaults and profile constants.
2. Split Gestures UI into role-aware Mouse hand and Keyboard hand views.
3. Wire configurable move, primary/secondary pinch, and scroll mappings into
   `MouseController` while preserving Fist emergency release.
4. Extend reset/save/tooltips and deterministic tests.
5. Render-check Settings, run required verification, rebuild, and launch paused.

## Safety

- Fist behavior is not configurable for either hand.
- Duplicate button pinch mappings and move/scroll conflicts are rejected.
- Reconfiguration remains paused and releases held mouse buttons and keys.

## Verification result

- Gestures renders separate `Mouse hand · Right` and `Keyboard hand · Left`
  views and updates the labels when the Mouse hand changes.
- Mouse-hand configuration preserves existing defaults while supporting move
  pose restriction, click-pinch swap/disable, and scroll-pose remapping.
- Profile and Settings reject duplicate button pinches and move/scroll pose
  conflicts.
- Deterministic tests cover move restriction, scroll remapping, profile
  validation, UI role labels, tooltips, and settings round-trip.
- Both hand views were render-checked, and the rebuilt packaged app remains open
  in its safe paused/error state while Camera permission is unavailable.
