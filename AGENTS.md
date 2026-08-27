# VisionControl agent guide

## Project objective

Build a local-first, cross-platform desktop application that uses webcam hand
tracking to control the mouse with one hand and configurable keyboard gestures
with the other.

## Development rules

- Use Python 3.11. MediaPipe 0.10.21 is the validated version.
- Keep camera frames local; do not add uploads or telemetry without explicit
  approval.
- Preserve emergency release behavior for every mouse button and keyboard key on
  pause, hand loss, calibration, exit, and exceptions.
- Keep platform side effects behind the input adapter and keep core logic
  deterministic and testable.
- Write/update requirements in `docs/requirements/` and plans in `docs/plans/`
  before implementing a new milestone.
- Run deterministic tests before commits. Real camera tests are explicit smoke
  tests and must start paused when possible.
- Do not commit `.venv*`, `build/`, `dist/`, personal files under `data/`, logs,
  credentials, or signing certificates.
- Do not remove or overwrite unrelated user changes.

## Required verification

```bash
PYTHONPATH=src .venv311/bin/python -m unittest discover -s tests -v
PYTHONPATH=src .venv311/bin/python -m compileall -q src tests scripts
git diff --check
```

For a camera smoke test on the current Mac:

```bash
PYTHONPATH=src .venv311/bin/python -m vision_control.app \
  --camera-index 1 --start-paused
```

## Current handoff

Read `docs/workspace-handoff.md` and `docs/development-status.md` before starting
new work. They contain the current runtime, packaging status, known limitations,
and next priorities.

