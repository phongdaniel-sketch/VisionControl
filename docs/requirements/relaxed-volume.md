# Relaxed hand volume, open hand pointer

Status: REVERTED at user request on 2026-09-19 after real-hand testing reported
failed Volume recognition and confusion with Scroll. This is a historical
experiment, not the active requirement. Use drag-volume-priority.md instead.

User-selected interaction: open hand moves the pointer; loosely curl all four
fingers and rotate the wrist to adjust volume. Do not require four extended
fingers for volume. Retain ordinary narrow-finger scroll and wide-hand zoom rules.

- Volume needs a distinct relaxed four-finger geometry, not a tight fist, pinch,
  index-only curl or paired index/middle click. Thumb stays clearly separated.
- Confirm the relaxed pose with the existing pose hold setting, then rotate for
  volume. An extended/open hand must never qualify for volume.
- Opening the hand must yield to pointer movement in that same update.
- Right contact, active left drag and configured symbols keep their priority.
- Do not overwrite personal profiles or hand calibration. Update user guidance
  and regression tests. Camera usability remains unverified until user retest.
