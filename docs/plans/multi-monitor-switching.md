# Coding plan: edge-dwell multi-monitor switching

Status: APPROVED (user requested continuation on 2026-08-27)

## Implementation

1. Add a pure edge-dwell state machine to the monitor module.
2. Integrate it into mouse control only for active mode and point pose.
3. Add validated defaults and Settings controls.
4. Surface dwell progress and switch completion through the existing overlay.
5. Add deterministic tests, run visual/behavior smoke checks, review, and push.

## Risks and mitigations

- Accidental switches: require point pose, dwell time, no pinch, and release latch.
- Repeated switching while held: latch until the hand leaves the edge zone.
- Irregular monitor topology: order displays spatially by center x then center y.

## Rollback

The feature can be disabled in Settings; fixed and all-display modes bypass the
state machine entirely.

