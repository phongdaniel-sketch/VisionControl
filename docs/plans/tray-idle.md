# Tray resource optimization

Add runtime suspend/wake perception methods independent of profile setup, and a
preview-work switch. Track explicit tray hiding in Controller; suspend only when
hidden and paused, skip rendering while hidden active. Wake through Start/Open,
reject old frames, preserve safety and exclusive child-window gates. Test worker
cleanup/restart, hidden processing, no drawing/logging, stale clearing and wake
errors; run full deterministic suite, compileall and diff checks.

Validation: 158 tests pass; compileall/diff pass. Native Cocoa mocked-resource
lifecycle checks pass. Real camera wake latency and resource savings unmeasured.
