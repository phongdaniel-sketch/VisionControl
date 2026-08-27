# Edge-dwell multi-monitor switching

Status: APPROVED (user requested continuation on 2026-08-27)

## MVP requirements

- In `active` monitor mode, allow the right hand to switch to the previous or
  next display by dwelling near the calibrated left or right edge.
- Require the point gesture and no active pinch to avoid accidental switching.
- Require leaving the edge zone before another switch can occur.
- Support displays with negative desktop coordinates.
- Allow edge switching, dwell time, and edge-zone size to be configured in
  Settings.
- Keep `fixed` and `all` monitor modes unchanged.

## Acceptance criteria

- Holding point at the right edge switches exactly once to the next spatial
  display after the configured dwell time.
- A continued hold cannot repeatedly cycle displays; returning to the center
  rearms switching.
- Holding at an outermost edge does not wrap around.
- Cursor is placed safely at the center of the new display on switch.
- Overlay status exposes edge progress and completed switches.
- Deterministic tests cover timing, latching, display order, and negative origins.

## Safety and privacy

- Switching emits only local cursor movement.
- Pause, missing hand, fist, and non-point poses cancel pending dwell state.

