# Optional Gemini transcription and configurable hotkeys

Default remains local Whisper. Gemini selection plus explicit audio-upload consent
is required before sending one bounded utterance to Google's generateContent API.
No background uploads, automatic retries or cloud fallback. API errors are sanitized.
The API returns transcription only; deterministic allowlisted commands still execute
locally. Gemini has no comparable confidence score: show unavailable, never invent one.

API key is entered in a masked field, stored via Windows user-scoped DPAPI outside
source/config/logs, never passed in URLs. Do not embed or test the key shared in chat;
recommend rotation. Empty field retains saved key; explicit delete clears it.

Hotkey accepts Ctrl/Alt/Shift plus Space, A-Z, 0-9 or F1-F12. At least one modifier
is required. Legacy Space/V settings migrate to Ctrl+Alt+Space/V. Preserve conflict
reporting and press-hold-release operation. Save errors leave dialog open.

Plan: pure hotkey parser; DPAPI secret store; bounded REST STT with WAV in RAM;
provider selector, consent, masked key and editable hotkey presets; regression,
mocked network/security tests, native hotkey/DPAPI roundtrip and UI smoke. No live
API request or microphone capture during automated checks. Existing EXE unchanged.

References:
https://ai.google.dev/gemini-api/docs/models/gemini-2.5-flash
https://ai.google.dev/gemini-api/docs/generate-content/audio
https://ai.google.dev/gemini-api/docs/api-key
https://learn.microsoft.com/en-us/windows/win32/api/dpapi/nf-dpapi-cryptprotectdata
