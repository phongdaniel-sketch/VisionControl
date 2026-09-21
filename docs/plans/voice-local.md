# Local Vietnamese voice commands and countdown

Scope: open This PC, local date/time, copy/paste, relative countdown, cancel and
remaining time. No fixed-clock alarms, arbitrary shell, cloud audio or recordings.
Whisper small multilingual model is external under ignored models/; WinRT Vietnamese
voice provides offline replies. Audio stays in bounded memory, maximum 15 seconds.
Button/gesture toggle waits 5 seconds for speech, submits after 1.2 seconds of
silence, and cancels on a second activation or Escape. The hard limit rejects
truncated commands. See voice-toggle-corners.md for the current activation policy.
Windows global Ctrl+Alt+Space (or configurable Ctrl+Alt+V): hold to capture,
release to decode. RegisterHotKey reports conflicts. Never activate without opt-in.
Use a named input device; missing device never falls back to another microphone.
Only exact allowlisted phrases pass parsing; low-confidence output does nothing.
Clipboard requires the original foreground window, released physical modifiers,
and no settings/calibration/debug dialog; pause gestures before sending shortcuts.
One countdown, 1 second to 24 hours, survives Windows sleep while app stays alive;
not persisted across app exit. Reject replacement until cancellation. Notify with
window, periodic bell, speech, Stop and Snooze five minutes. Suspend capture during
speech. Cleanup cancels audio workers, hotkey, speech and timers. Source first;
existing exe must be rebuilt separately. Add parser/timer/worker/UI tests, synthetic
offline speech smoke test and full regression suite. Physical mic accuracy pending.
