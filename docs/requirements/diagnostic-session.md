# Local diagnostic recording

User explicitly approved webcam plus a dedicated test area recording (2026-09-05).

- Provide a separate diagnostic window, initially paused/not recording, with
  Start recording, three-second preparation countdown, Stop and visible elapsed
  time. Automatically stop after 30 seconds and retain the window for review.
- Record only webcam plus a generated test canvas, no desktop capture or audio.
  Use the production tracking/controller logic with an in-memory input adapter;
  mouse/keyboard commands become logged test events, never OS input.
- Use the user's profile and calibration, mapping into a fixed test canvas.
  Explicitly distinguish simulated controller output from OS cursor behavior.
- Save per-frame JSONL with monotonic timing, landmarks, poses, pinch ratios,
  decision state, target hit events and stage durations; copy profile/calibration
  metadata for reproduction. Record a composite AVI with visible frame/time stamps.
- Each video frame maps to an exact JSONL frame number/timestamp. Nominal video
  playback FPS is not a camera FPS or end-to-end latency claim.
- Store unique sessions under ignored data/captures in source mode (OS application
  data in packaged mode). No upload/telemetry. Save failure stops recording and
  input simulation, preserves partial files and shows an error.
- After the user records, summarize and inspect timed frames. Do not infer human
  intention or hardware latency from log values alone.
