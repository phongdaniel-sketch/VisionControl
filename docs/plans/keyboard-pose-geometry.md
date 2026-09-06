# Keyboard gesture correction

Implemented: 87 deterministic tests pass, compilation and diff checks pass.
Synthetic tests cover left/right labels, mirroring, rotation/scale and actual
D/S/Space dispatch. None is returned for an ambiguous thumb; held-key release
is tested. Physical camera pose verification remains pending.

Root cause: static classifier uses thumb_tip.x < thumb_ip.x and fingertip.y <
pip.y. These rules change with handedness, mirroring and hand orientation.

1. Add palm-relative thumb state and geometry-based finger states using shared
   helpers from pinch/fist work. Use unknown for uncertain geometry.
2. Pass actual frame dimensions through runtime/static and mouse classification.
3. Replace degenerate legacy hand fixtures with articulated test geometry and
   add regressions for three/four/open, both labels, mirroring and rotation.
4. Verify mapped D/S/Space dispatch, held-key release on uncertainty, prior mouse
   safety tests and compilation/diff checks. Open paused for user acceptance.
