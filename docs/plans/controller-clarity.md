# Controller clarity implementation

Implemented 2026-09-05: 73 tests pass, including guide/profile correspondence,
paused pose status, countdown, Space with button focus, invalid capture recovery,
four-boundary persistence and atomic-save preservation. Controller and calibration
screens visually inspected offscreen. Physical user workflow acceptance pending.

1. Add requirements before editing and inspect existing UI/runtime capture paths.
2. Render role-aware guides and human-readable status/display labels using current
   profile and frame data, without changing gesture mappings.
3. Add visible inline calibration controls with per-step instructions/countdown;
   handle missing hands and invalid captures without advancing the step.
4. Save calibration atomically, keep runtime paused after completion/cancel, and
   preserve the previous mapping until a valid complete calibration is saved.
5. Test guide mappings, status, keyboard focus, cancellation, invalid bounds and
   persistence. Render Controller offscreen for visual inspection and rerun the
   deterministic suite, compilation and diff checks.
