# Pointer recovery correction

Separate mouse point recognition from strict keyboard pose counting: an extended
index with other fingers not extended may move despite partially curled fingers.
Keep clear-fist release, keyboard classification and pinch safeguards unchanged.
After a nonmoving pose, bound catch-up travel to 12% of the display diagonal per
nominal 30 FPS frame (time-scaled with a 50 ms ceiling) until the target is reached.
Validate against deterministic synthetic hands and the authorized local recording.
Do not claim real Windows latency or gesture accuracy from replay.
