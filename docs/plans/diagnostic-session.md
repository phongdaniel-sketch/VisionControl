# Diagnostic implementation plan

1. Add a recording-only input adapter, bounded local video/JSONL recorder and
   summary generation. Video and synthetic target canvas use the same snapshot.
2. Instrument stage timings and pinch decision reasons without changing decisions.
3. Add a separate paused diagnostic UI with explicit start/countdown, guided
   30-second phases, stop and output location; route through launcher/PowerShell.
4. Test adapter isolation, recording duration, frame/log correspondence, partial
   failure, automatic stop and release. Verify UI offscreen and actual codec readback.
5. Open diagnostic UI for the user's physical recording; wait for completion or
   user input, then inspect summary and video frame samples. Awaiting a physical
   interaction is not a completed diagnostic finding.
