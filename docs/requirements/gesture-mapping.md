# Configurable left-hand gesture mappings

Status: APPROVED (user requested the next step on 2026-08-27)

## MVP requirements

- Show every supported left-hand keyboard gesture in Settings.
- Allow each gesture to be disabled or configured as `press` or `hold`.
- Accept one or more supported keys and validate them before saving.
- Preserve the left fist exclusively for keyboard arming while arming is enabled.
- Save mappings in the local validated user profile.
- Keep held-key safety release behavior unchanged.

## Acceptance criteria

- Settings edits `point`, `peace`, `three_fingers`, `four_fingers`, and
  `open_palm` mappings without manual JSON editing.
- Empty or unsupported key values are rejected with a useful message.
- Disabled gestures are removed from `left_hand` in the saved profile.
- Invalid changes do not replace the last valid user profile.
- Deterministic tests cover parsing, disabled mappings, invalid keys, and profile
  validation.

## Out of scope

- Training custom hand shapes.
- Reassigning the fist while hold-to-arm is enabled.
- OS-specific global shortcut recording.

