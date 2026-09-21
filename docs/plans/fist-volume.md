# Fist horizontal volume; remove automatic zoom

Replace rotation volume with primary-hand closed fist, confirmed for pose_seconds.
Right in mirrored preview increases volume, left decreases it. Anchor after
confirmation; one media step per 0.04 camera width, capped at one per 120 ms.
No repeated output while stationary. Opening or losing hand cancels and requires
a fresh hold. Existing held drag retains priority. Fist volume owns folded-tip
contacts and suppresses click preparation. Volume wins over primary fist-switch
and corner gestures while enabled; second-hand keyboard gestures stay unchanged.
Remove automatic zoom recognition and its settings/guide; ignore legacy zoom=true.
Keep volume on/off setting and personal calibration. Add regression coverage and
run full suite, compileall and diff check. Camera acceptance requires user retest.

Verification: 209 tests passed, compileall and diff check passed. Regression
coverage includes direction, stationary/vertical motion, folded contacts, loss,
open-hand exit, disabled volume, drag ownership and legacy zoom configuration.
The saved volume toggle remains unchanged (previously disabled by the user).
Restart and enable Fist volume in Settings for physical acceptance testing.
