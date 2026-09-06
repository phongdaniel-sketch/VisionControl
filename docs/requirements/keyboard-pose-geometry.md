# Keyboard pose geometry correction

User reported Three fingers/Four fingers/Open palm confusion and supplied an
open left palm labeled Four fingers (2026-09-05).

- Replace absolute image-X thumb direction with thumb extension relative to the
  palm's index-to-pinky axis. Recognition must not depend on Left/Right labels.
- Use joint geometry for finger extension/folding, including image aspect ratio.
- Three fingers = index/middle/ring extended, pinky folded. Four fingers = four
  extended with thumb tucked. Open palm = four extended with thumb spread.
- Reject uncertain thumb/finger states instead of turning uncertainty into a
  different keyboard shortcut. Maintain existing activation debounce/release.
- Preserve mappings and saved calibration. Test mirrored hands, in-plane rotation,
  scale, boundary ambiguity, actual key dispatch and immediate held-key release.
