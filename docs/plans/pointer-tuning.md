# Pointer tuning implementation

Implemented 2026-09-05; 64 tests pass. Local profile backed up and tuned with both
click mappings preserved because no revised mapping was selected. Offscreen
Settings render verified. 45-frame camera measurements: 25.8 -> 25.9 ms median
tracking, 25.3 -> 25.3 capture/tracking FPS. Video tracking did not produce a
measured speedup in these short runs; ergonomic improvement requires user retest.

1. Inspect the actual local profile and installed MediaPipe API; collect a camera
   timing baseline without sending input or retaining frames.
2. Switch tracker from IMAGE/detect to VIDEO/detect_for_video; enforce strictly
   increasing timestamps, including repeated/default timestamps.
3. Add time-normalized adaptive smoothing and stable, exclusive pinch activation.
   Keep immediate release and reset pending activation on safety transitions.
4. Add Settings controls, profile validation/defaults and regression tests.
5. Back up and tune local profile according to the user's chosen click mapping.
6. Run tests/compileall/diff checks, compare camera timing, and reopen paused for
   the user to check pointer feel and click accuracy. Do not claim ergonomic
   acceptance from automated tests alone.
