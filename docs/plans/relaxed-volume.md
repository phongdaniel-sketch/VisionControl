# Implementation and acceptance

Status: REVERTED on 2026-09-19. User testing rejected the relaxed-hand pose:
Volume was not recognized reliably and conflicted with Scroll. The previous
extended-finger volume behavior is restored. Do not reapply this plan by default.

1. Add measured relaxed four-finger feature using MCP/PIP/tip joint angles and
   retain existing geometry validation. Bound the pose away from fully extended
   fingers and exclude fist/pinch/cluster.
2. Replace the extended-finger volume predicate and release guard with one shared
   relaxed-pose predicate. Preserve pinch/drag/contact arbitration.
3. Update guide/settings and synthetic rotation/drag tests. Add regressions for
   open-hand movement, relaxed rotation, immediate open-hand exit, one/two curled
   fingers, tight fist, pinch, stale tracking and direction wraparound.
4. Test real use with source restart: open hand movement must not change volume;
   relaxed hold+rotation must change volume; open hand must recover movement;
   retest left/right/middle clicks and left drag. Start paused and low volume.
