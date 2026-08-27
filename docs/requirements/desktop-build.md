# Standalone desktop builds

Status: APPROVED (user requested continuation and standalone run files on 2026-08-27)

## MVP requirements

- Build a standalone macOS `.app` that opens Settings without Terminal.
- Bundle the logo icon, splash/loading images, default profile, MediaPipe model
  data, Qt, OpenCV, and runtime dependencies.
- Store writable settings and calibration outside the read-only application
  bundle.
- Allow Settings to start the camera controller from the packaged executable.
- Include a camera usage description in the macOS application metadata.
- Keep source/CLI development commands working.
- Provide a reproducible PyInstaller configuration suitable for a later Windows
  `.exe` build.

## Acceptance criteria

- `dist/VisionControl.app` launches Settings with the application icon.
- Saving settings and starting the controller works from the packaged app.
- User data is stored in the OS application-data directory.
- The app bundle passes an ad-hoc code-sign verification for local testing.
- Source tests still pass after frozen-path changes.

## Constraints

- Apple Developer ID signing and notarization require the user's Apple developer
  credentials and are not part of this local test build.
- Windows camera/input/DPI verification and final `.exe` must run on Windows 11
  or a Windows CI runner.

