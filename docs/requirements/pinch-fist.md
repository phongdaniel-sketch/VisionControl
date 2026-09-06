# Distinguish pinch from a closed fist

Requested 2026-09-05 after successful calibration and physical click testing.

- Replace the mouse fist test based solely on image Y coordinates with joint
  bending and fingertip proximity to the wrist/palm, normalized to hand scale.
- A new pinch needs a recently extended corresponding finger with the pinch open;
  starting with a clenched hand or already pinched hand must not create a click.
- Once a valid pinch is pending/held, allow the finger to bend without applying
  the extension prerequisite again. Preserve confirmation, exclusivity and release
  hysteresis. A clear geometric fist releases immediately, as do Pause/hand loss.
- Mouse pose status uses the same fist decision as mouse control. Do not silently
  change keyboard mappings or introduce a new downloaded classifier.
- Test rotation/scale, pointed-to-pinched sequences, cold-start pinches, true fists,
  loss/pause reset, swapped buttons and degenerate landmark geometry.
- This increment addresses recognition. Cursor anchoring during clicks is a
  separate pending improvement; do not claim to fix the downward cursor jump.
