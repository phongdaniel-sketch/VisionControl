# Plan: Startup experience reliability and loading bar

Status: IMPLEMENTED

1. Make the Qt application lifetime explicit across the OpenCV-to-Controller
   window transition.
2. Render a procedural rounded gradient progress bar over a cleaned region of
   the existing loading artwork and remove secondary progress text.
3. Convert frame-processing failure from application shutdown to a safe paused
   error state with all input released.
4. Add deterministic tests for loading visuals and Controller failure behavior.
5. Rebuild the macOS bundle and run a paused packaged-camera smoke test.

## Verification result

- The packaged failure was reproduced through macOS Launch Services and traced
  to Camera authorization returning before OpenCV could initialize the device.
- Runtime cleanup is now idempotent, so a partially initialized MediaPipe task
  cannot replace the original camera error with a shutdown exception.
- The Controller remains open in `ERROR · PAUSED` with input released and can
  retry through Settings after Camera access is granted.
- The rebuilt app remained alive during the Launch Services smoke check while
  Camera access was unavailable.

## Safety

- Runtime errors pause and close the active runtime before any error is shown.
- No error recovery path automatically resumes mouse or keyboard control.
- Camera frames and diagnostics remain local.

## Rollback

- The legacy OpenCV controller remains available through
  `vision_control.launcher --legacy-controller`.
