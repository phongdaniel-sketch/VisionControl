# Voice close-command recognition plan

1. Add every supported close-window phrase to Whisper's Vietnamese initial prompt.
2. Extend only the explicit close-command allowlist for common transcription variants.
3. Add regression tests for accepted variants and unsafe multi-action phrases.
4. Run unit tests, compile checks, and whitespace validation.
5. Rebuild the Windows voice bundle and relaunch it for physical testing.

Do not lower the recognition-confidence threshold or introduce broad fuzzy matching:
closing a foreground window is a sensitive side effect and must retain the existing
foreground-target and released-modifier checks.
