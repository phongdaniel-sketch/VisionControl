# Pinch/fist implementation and research

Implemented: 82 deterministic tests pass, compileall and diff checks pass. Guide
wording updated. Saved calibration/profile unchanged. Synthetic fixtures test
PIP-below-tip ambiguity, in-plane rotation/scale, first-frame pinches, held-pinch
continuity, real-fist priority and loss/pause reset. Physical UAT remains pending.

1. Review project geometry and state transitions plus public primary sources.
2. Add deterministic geometric fist/extension helpers and mouse-pose presentation.
3. Gate new pinches on an open, extended finger observed within .8 seconds; keep
   pending/held pinches alive through bending but never override a clear fist.
4. Update guide wording and test realistic synthetic joint geometry, rotation,
   cold starts, safety transitions and both configurable button mappings.
5. Run deterministic tests and compilation. Reopen paused for physical user
   acceptance without overwriting the saved profile or successful calibration.

## Public sources reviewed (2026-09-05)

- https://github.com/HarishG20/air-mouse-gesture-control documents pinch-before-fist
  priority and multi-frame confirmation. These are project choices, not measured
  evidence that its implementation is more accurate than ours.
- https://gist.github.com/feynlee/7236fbbe977d8b21d5ebadf07b84249e explicitly discusses
  reducing fist confusion by keeping other fingers extended during a pinch.
- https://github.com/miftahfaridhh/edge-ai-gesture documents gesture
  misclassification and suggests clearer poses/more training data/custom models.
- https://developers.google.com/edge/mediapipe/solutions/vision/gesture_recognizer/python
  documents canned Closed_Fist/Open_Palm/etc. Pinch is not in that canned list.
  Our app uses HandLandmarker plus our own rules, not this canned classifier.

Decision: implement our own geometry plus transition gate, preserve fist release
priority and avoid adding a new ML model in this increment. No third-party code
is copied. These examples establish known design concerns, not a failure-rate
estimate or a guarantee under occlusion.
