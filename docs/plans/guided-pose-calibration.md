# Guided pose calibration implementation

1. Add deterministic measurement, bounded fitting, sample quality gating and
   versioned atomic persistence in a dedicated module.
2. Use optional calibration consistently in mouse curl recognition and primary
   gesture arbitration; preserve default behavior when absent.
3. Add a modal wizard under Calibrate with a local camera preview, countdown,
   five pose captures, inert click testing, explicit Save, Cancel and reset.
4. Guard runtime resume and UI lifecycle during the wizard, remain paused after.
5. Test fitting/rejection, malformed persistence, atomic failures, preview click
   cycles, runtime guards, integration and offscreen UI. Run the full suite.

Manual acceptance: start paused; use Calibrate > Hand poses; collect each pose,
retry after removing the hand, test three clicks, cancel once and verify old
settings remain, then save and restart. Test 20 trials per click, neutral hand
for two minutes, pinch drag and scroll, and compare against the old profile.
Repeat for both pointer modes and the correct mouse-hand assignment. No real
desktop input should occur anywhere inside the wizard.

## Usability correction plan

1. Keep recognition thresholds and emergency-release behavior unchanged.
2. Add Vietnamese step content and a schematic pose widget beside live preview.
3. Add captured-step review, retry and explicit Next; make countdown preparation
   independent of hand detection, while keeping capture freshness checks.
4. Clarify startup overrides and mark unsupported edge switching inactive.
5. Test review/retry, loss during capture versus preparation, inert rehearsal,
   saved startup preferences and disabled edge options. Render small/normal UI.
