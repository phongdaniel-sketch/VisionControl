# Voice activation and pointer hot corners

Requirements: retain opt-in voice and selectable available microphones, BRIO default.
Controller button and voice_listen_toggle action start one utterance, cancel on
second activation or Escape. No speech for 5 s cancels, 1.2 s silence after speech
submits, hard 15 s limit cancels without executing truncated text. Existing hold
hotkey remains. Never listen during speech playback. No cloud/Gemini in this scope.

Use WebRTC VAD locally and deterministic endpoint timing. Display remaining time.
Reject stale recognition after cancellation. Keep input target validation.

Hot corners depend on pointer position, not hand pose. Dwell .7 s by default,
once per entry, progress feedback. Suppress while paused, settings/calibration,
dragging, scrolling or adjusting volume. Leave corner to rearm after suppression.
Retain corner bindings; new corner_dwell_seconds replaces old double-fist timing.
Add named media, desktop, task view, screenshot, This PC, undo/redo, Escape,
pause gestures and voice toggle actions. Route app actions through adapter callback.

Plan: deterministic endpoint/corner logic, audio worker integration, Qt controls
and action dispatch, regression tests, native UI smoke, manual mic/camera UAT.
Source-only delivery; old EXE must be rebuilt separately. No model or audio commits.
