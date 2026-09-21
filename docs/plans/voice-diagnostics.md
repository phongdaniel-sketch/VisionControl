# Voice recognition diagnostics and Save behavior

Save closes Voice Control only after successful validation and persistence.
Errors leave the dialog open. Existing configuration remains backward compatible.

Local diagnostic logging is opt-in and off by default. JSONL includes timestamp,
selected device, capture mode, audio duration/RMS/peak/clipping, VAD speech duration,
recognized text, score, rejection reason and errors. Never store raw audio or upload.
Bound logs to 256 KiB plus one rotated backup. Show latest audio metrics in RAM even
with disk logging off. Clear distinction between weak speech and unsupported text.

Plan: logging helper, capture metrics for hold/toggle, Settings opt-in, Save accept,
tests for rotation/privacy, successful/failed save and capture quality. No confidence
threshold reduction or automatic execution of fuzzy/hallucinated commands.
