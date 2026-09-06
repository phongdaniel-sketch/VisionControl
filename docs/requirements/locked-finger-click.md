# Thumb lock, curl clicks and pinch drag

Confirmed user mapping: index curl/re-extend -> left, simultaneous index+middle
curl/re-extend -> right, middle curl/re-extend -> middle. Only while thumb-open
lock is confirmed. Use release-completed cycles for all clicks to arbitrate the
two-finger chord without an early single click. Curl >=60ms; chord join <=120ms;
complete <=800ms. Cold curls/unknown/pinch cannot generate click. Rearm by extension.
Index-thumb pinch is separate drag, possible unlocked, requires prior separated
extended index then stable pinch >=100ms; release opens at hysteresis threshold.
Drag uses relative palm displacement from activation anchor, never an absolute
fingertip catch-up. Missing hand, fist, pause, calibration, errors and exit release
all three buttons. Add opt-in thumb_lock mode, select it in local user profile
with backup, update Settings and guide. Preserve old modes and calibration.
