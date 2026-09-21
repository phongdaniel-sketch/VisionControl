# Duplicate hand role continuity

Requirement: recover a same-label duplicate only when exactly one current
observation clearly matches a recent unambiguous palm. Never replay old landmarks,
guess from confidence alone, or bridge hand loss. Ambiguous matches remain blocked.
Keep click mappings, gesture priorities and personal calibration unchanged.

Plan: filter role observations before runtime arbitration and snapshot creation;
use aspect-correct palm geometry, bounded age and a runner-up distance margin.
Reset on missing/ambiguous frames and lifecycle control release. Add deterministic
tests, replay the local diagnostic landmarks without OS input, then run the suite.
Physical acceptance requires a restarted app and another camera test.
