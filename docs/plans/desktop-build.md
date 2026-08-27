# Coding plan: standalone desktop builds

Status: APPROVED (user requested continuation and standalone run files on 2026-08-27)

## Implementation

1. Centralize bundled resource and writable user-data paths.
2. Add a unified launcher that routes Settings and camera-controller modes in
   both source and frozen execution.
3. Add a PyInstaller spec with application icon, resources, camera permission,
   and MediaPipe collection.
4. Build and ad-hoc sign the local macOS `.app`.
5. Launch-test Settings and controller startup from the bundle.
6. Document reproducible macOS and Windows build commands.

## Security and release

- No credentials or user profiles are bundled.
- Local ad-hoc signing is for test execution only.
- Public macOS release still requires Developer ID signing and notarization.
- Public Windows release still requires Authenticode signing.

## Rollback

Packaging files and launcher routing are additive; source entry points remain
available independently.

