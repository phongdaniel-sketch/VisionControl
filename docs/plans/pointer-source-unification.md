# Pointer source unification plan

1. Add palm pointer behavior to the current mouse engine, preserve fingertip lock.
2. Reserve palm scrolling pose and retain OK/drag ownership.
3. Use source-specific calibration and preview marker/instructions.
4. Replace old Gestures page with new editor, remove extra menu/toggle and show
   only two pointer sources. Migrate current/template profiles without losing data.
5. Test movement/click/scroll/drag/OK in both modes, Settings round trips and
   calibration separation; full tests, compileall, diff and paused smoke.
