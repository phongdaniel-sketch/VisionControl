# Pipeline experiment plan

1. Create bounded standalone benchmark with camera-only / sequential / latest.
2. Run two passes at 480p/30 and 720p/60, verifying negotiated FOURCC and size.
3. Compare throughput, age and hand-count workload; report limits and choose
   whether integration is justified. Full application behavior is not benchmarked.
