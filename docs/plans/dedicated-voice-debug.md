# Dedicated Voice Debug

Supersedes the global debug_audio capture behavior. Normal Voice, hotkeys and
Settings quick mic test never save WAV, even with an old debug_audio=true setting.
Only explicit capture in the separate Voice Debug dialog can save local WAV and
sidecar logs. Debug is preview-only and never executes recognized commands.
Optional expected-text field supplies ground truth for analysis. Opening the
dialog alone never records. Close/Escape cancels; normal hotkeys are blocked while
debug is open. Retain prior samples, limits and opt-in textual logging settings.

Plan: isolate debug dialog and explicit capture flag, remove global WAV toggle,
regression tests for legacy flag isolation and command suppression, UI smoke.
