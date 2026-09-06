# Pipeline performance experiment

Run isolated camera-only, sequential capture/inference and latest-frame worker
experiments at 640x480/30 and 1280x720/60. No input adapter, GUI or camera frames
saved. Each case runs in a separate process with a hard timeout. Reader thread
owns VideoCapture from open through release. Store only latest frame + sequence
and timestamp; never process same sequence twice. Measure delivered read FPS,
inference FPS, post-read age, hand count and negotiated codec. These are not
sensor latency or verified unique sensor exposures. Do not change app defaults,
calibration, exposure or user profile. Keep raw timing results in ignored build/.
