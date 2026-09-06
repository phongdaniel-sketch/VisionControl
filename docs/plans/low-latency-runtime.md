# Low-latency runtime plan

1. Worker-owned camera and tracker, latest frame/result slots and bounded shutdown.
2. Integrate freshness gating and independent cursor ticks on UI thread.
3. One Euro + bounded prediction, reset on all gesture/safety transitions.
4. Debug default OFF, configurable100ms start/release confirmation, accurate UI FPS.
5. Deterministic safety/filter/worker tests, existing tests and compilation; camera
   smoke starts paused. No promise of60 inference FPS without measurement.
