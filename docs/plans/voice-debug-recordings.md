# Temporary local voice debug recordings

User explicitly authorized saving audio samples and logs until voice recognition
is fixed. Add an opt-in debug_audio setting (default false); enable only in this
user's current source config. No microphone opens until user activates voice/test.
Each activated capture has a UUID, timestamp, PCM WAV and JSONL sidecar containing
capture mode/device/provider, decoder output, audio metrics and final result.
Keep rejected/timeout/cancelled samples for diagnosis, but never execute cancelled
commands. Audio persistence adds no network access; existing cloud consent remains.

Store under ignored data/voice_debug. Limit to 500 samples / 256 MiB; stop new debug
captures with a clear error when full, never silently delete existing evidence.
Expose recording checkbox and folder button in Settings. User can disable saving.
Do not delete existing logs now. Cleanup after acceptance, only this debug directory.

Plan: bounded recording helper, capture-finally WAV persistence, per-session event
linkage, UI opt-in, enable current config using structured JSON, deterministic tests
with synthetic PCM, full regression. Do not autonomously record the room.
