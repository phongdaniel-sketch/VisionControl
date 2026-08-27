# Per-hand gesture mapping

Status: APPROVED (user request on 2026-08-27)

## Hand separation

- The Gestures page must explicitly separate the current Mouse hand and Keyboard
  hand, using the roles selected in Settings rather than assuming fixed sides.
- Changing the Mouse hand must update the role labels; the opposite hand remains
  the Keyboard hand.

## Mouse-hand configuration

- Allow pointer movement to use any visible non-safety pose or one selected
  built-in pose.
- Allow primary and secondary click/drag to use Index pinch, Middle pinch, or be
  disabled. The same pinch cannot drive both buttons.
- Allow scrolling to use Peace, Three fingers, Four fingers, or Open palm.
- Keep Fist reserved as the non-configurable pointer stop/release gesture.
- Preserve the current behavior as defaults: any pose moves, Index pinch is
  primary click/drag, Middle pinch is secondary click/drag, and Peace scrolls.

## Keyboard-hand configuration

- Retain Disabled, Press, Hold, and validated key/chord mapping for the existing
  built-in static poses.
- Keep Fist reserved for keyboard arming/disarming.

## Acceptance criteria

- Settings visibly identifies both role hands and saves mouse mappings locally.
- Runtime honors configured move, click, and scroll mappings deterministically.
- Invalid duplicate click mappings or move/scroll pose conflicts are rejected.
- Pause, Fist, hand loss, Settings, calibration, errors, and exit continue to
  release every held input.
