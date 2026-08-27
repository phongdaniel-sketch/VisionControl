# Coding plan: configurable gesture mappings

Status: APPROVED (user requested the next step on 2026-08-27)

## Implementation

1. Add pure parsing and profile-update helpers to the settings layer.
2. Add a keyboard gesture group to the existing PySide6 Settings window.
3. Support Disabled, Press, and Hold modes with comma-separated keys.
4. Validate through both the helper and the existing `load_profile` boundary.
5. Add deterministic tests, update docs, visually smoke-test Settings, review,
   and push.

## Safety

- Do not expose the fist mapping while arming reserves it.
- Keep atomic profile replacement so failed validation preserves prior settings.
- Do not emit keyboard events from Settings itself.

## Rollback

Removing the gesture editor leaves existing JSON profiles and controller behavior
compatible with the prior release.

