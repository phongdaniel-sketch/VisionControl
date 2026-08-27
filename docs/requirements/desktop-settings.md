# Desktop identity and settings

Status: APPROVED (user requested continuation on 2026-08-27)

## User and problem

VisionControl users need a recognizable desktop application and a settings
screen so camera and control behavior can be changed without editing JSON or
command-line arguments.

## MVP requirements

### Must

- Use `docs/Vision Control logo.png` as the application icon.
- Provide native icon assets for macOS and Windows 11.
- Provide a cross-platform settings window for camera index, hand roles,
  mirrored-hand swapping, monitor mode, and mouse sensitivity controls.
- Validate settings before saving and retain the existing safe defaults.
- Keep the existing command-line launch path available.

### Should

- Load saved settings on the next launch.
- Allow starting VisionControl from the settings window.
- Show actionable validation and startup errors.

### Could

- Add editable keyboard gesture mappings in the following milestone.

## Acceptance criteria

- macOS `.icns` and Windows `.ico` files are generated from the supplied logo.
- The settings window uses the supplied logo as its icon.
- Saved settings produce a valid profile accepted by `load_profile`.
- Existing mouse, keyboard, splash, loading, and CLI behavior remains working.
- Deterministic tests pass without opening a real camera.

## Assumptions

- PySide6 Essentials is the shared desktop UI toolkit because the current
  Python installation does not include Tk; unused Qt add-on modules are omitted.
- User settings remain local under `data/` and are not committed.
