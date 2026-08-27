# Coding plan: desktop identity and settings

Status: APPROVED (user requested continuation on 2026-08-27)

## Scope

1. Generate `.icns` and `.ico` application assets from the supplied PNG.
2. Add a tested local settings/profile persistence layer.
3. Add a PySide6 settings window with the application icon.
4. Start the existing camera controller using the selected settings.
5. Preserve CLI operation and add a command that opens Settings.
6. Update dependencies, documentation, and deterministic tests.
7. Run security/review checks and push the reviewed change.

## Boundaries and data flow

- UI code lives in `src/vision_control/settings_ui.py`.
- Persistence code lives in `src/vision_control/settings.py`.
- User data is stored at `data/app_settings.json` and
  `data/user_profile.json`, both ignored by Git.
- The controller continues to consume the validated `Profile` model.
- No camera frames or settings are uploaded.

## Risks and mitigations

- PySide6 Essentials increases package size: omit unused Qt add-ons, isolate it
  to the launcher UI, and keep CLI operation available.
- Invalid local JSON: fall back with a clear error and never overwrite the
  default profile.
- Starting camera work on the UI thread: close Settings before launching the
  existing OpenCV event loop.

## Verification

- Unit tests for settings defaults, persistence, validation, and profile output.
- Existing test suite and compile checks.
- UI import smoke test without opening a camera.

## Rollback

The settings launcher and generated icon assets can be removed independently;
the existing `python -m vision_control.app` entry point remains unchanged.
