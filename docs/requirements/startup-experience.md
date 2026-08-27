# Startup experience reliability and loading bar

Status: APPROVED (user request on 2026-08-27)

## Loading presentation

- Keep the existing branded loading artwork and `INITIALIZING...` heading.
- Replace the rectangular progress overlay with a thin rounded progress track.
- Render the completed portion as an orange/red through purple to blue gradient.
- Add a restrained glow at the leading edge and a blue outline around the track.
- Do not render a percentage or stage message below the progress bar.
- Continue to update progress from the real local initialization stages.

## Application lifetime

- Closing the temporary OpenCV splash/loading window must not terminate the Qt
  application before the Controller is visible.
- The normal application lifetime is owned by the Controller window.
- A recoverable frame/camera error must pause and release every held input,
  leave the Controller visible, and present an actionable error instead of
  immediately closing the application.
- Explicit Controller close, startup failure, and exceptions must preserve the
  existing emergency release behavior.

## Acceptance criteria

- Source and packaged launches transition from loading to Controller without
  closing during the window handoff.
- The loading bar visually matches the approved rounded gradient direction and
  contains no percentage/status line.
- A frame-processing exception stops processing and releases input while the
  Controller remains open.
- Required deterministic tests, compilation, and diff checks pass.
