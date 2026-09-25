# Voice close-command recognition

- Local Vietnamese transcription must bias decoding toward the supported close-window phrases.
- `Đóng cửa sổ` and `Tắt app` remain the canonical commands.
- Explicit, low-risk recognition variants such as `Tắt áp`, `Đóng cửa sổ này`,
  `Đóng cửa sổ đi`, and `Đóng cửa sổ lại` map to the same allowlisted action.
- The parser must continue rejecting negation, chained actions, and arbitrary fuzzy matches.
- The existing confidence threshold and foreground-window safety check remain unchanged.
- No microphone recording or diagnostic logging is enabled by this change.

Acceptance requires deterministic parser tests, the full test suite, a rebuilt Windows
bundle, and a physical BRIO retest of both canonical phrases.
