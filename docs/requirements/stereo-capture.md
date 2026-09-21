# Stereo capture diagnostic

Capture up to two input channels at the device default sample rate. Preserve
interleaved PCM in debug WAV files only when recording is explicitly enabled.
Use channel 1 consistently for VAD and recognition during this diagnostic trial,
avoiding possible phase cancellation from averaging. Do not switch channels within
an utterance. Log per-channel RMS, peak and clipping to support subsequent selection.
Mono-only devices retain their existing behavior. No threshold or cloud changes.

Plan: update capture and recording metadata, test stereo/mono conversion and WAV
round trips, run full regression suite, then request a real BRIO debug recording.
Stereo is an experiment, not a confirmed fix for the recognition failures.
