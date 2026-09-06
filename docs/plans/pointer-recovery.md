# Pointer recovery plan

1. Add mouse-only relaxed point recognition, preserving strict keyboard logic.
2. Track interrupted movement and limit catch-up steps without slowing ordinary tracking.
3. Test relaxed pointing, fist/click safeguards, bounded recovery and replay all
   846 stored landmark frames using recorded monotonic times and calibration.
4. Run full deterministic tests, compileall and diff check; report before/after.
