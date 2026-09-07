# macOS tray resource measurement

Measured on the current Apple M4 Mac, 2026-09-07, using camera 1 and current
source/profile. Real Controller, camera and inference; DiagnosticInputAdapter
simulates input and drains events each frame. No camera recording or OS input.

Eight sequential phases, four seconds settling and 12–13 seconds sampling each.
CPU = process CPU seconds / elapsed seconds (100% = one core), including all
process threads. RSS sampled via ps once per second. Measurement overhead is
included. This is a short live-camera comparison, not a controlled replay.

| Phase | CPU % | RSS MiB | FPS | Frames with hands / frames |
| --- | ---: | ---: | ---: | ---: |
| Window Start 1 | 53.16 | 484.5 | 28.67 | 22 / 344 |
| Tray Start 1 | 79.99 | 489.4 | 30.00 | 360 / 360 |
| Window Paused 1 | 94.01 | 489.6 | 30.00 | 390 / 390 |
| Tray Paused 1 | 2.60 | 406.8 | 0 | 0 / 0 |
| Tray Paused 2 | 1.83 | 416.2 | 0 | 0 / 0 |
| Window Paused 2 | 83.21 | 492.6 | 30.00 | 390 / 390 |
| Tray Start 2 | 92.73 | 491.6 | 30.00 | 390 / 390 |
| Window Start 2 | 82.75 | 481.1 | 30.00 | 390 / 390 |

Paused averages: window 88.61% CPU / 491.1 MiB; tray 2.215% / 411.5 MiB.
Relative reduction: 97.5% CPU, 79.6 MiB (16.2%) RSS. Camera/inference were
suspended during both tray-paused phases. RAM remains allocated for Python/Qt
and other process resources.

Exclude Window Start 1 from comparable active results: only 6.4% of frames had
hands. With hands present, Window Start measured 82.75% CPU, versus tray runs
79.99% and 92.73%. All delivered 30 FPS. These samples do not establish an
active-tray CPU saving or FPS improvement; hand motion, detection work, thermal
state and sequential run variation were not controlled. No latency, system-wide
WindowServer load, GPU, watts or battery-life savings were measured.

Raw results and temporary harness for this session:
/tmp/visioncontrol-perf.EneTsb/results.json and measure.py (not persistent artifacts).
