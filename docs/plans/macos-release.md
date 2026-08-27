# Plan: macOS acceptance, bundle optimization, and release

Status: IMPLEMENTED (public signing/notarization awaits credentials)

## Implementation

1. Record the current bundle size, signature, metadata, and dominant contents.
2. Retain MediaPipe's required runtime collection while explicitly excluding
   unused accelerator, scientific, and development stacks.
3. Build cleanly and run Settings plus a paused controller smoke test.
4. Add a release script that verifies the app, creates a DMG and ZIP, computes
   hashes, and optionally performs Developer ID signing and notarization.
5. Run deterministic verification and update development/handoff documentation
   with measured results and remaining manual acceptance work.

## Safety

- Controller tests start with `--start-paused`.
- No camera frames, profiles, credentials, or permission databases are copied
  into release artifacts.
- Signing credentials are referenced by Keychain identity/profile name only.
- Artifact replacement is limited to explicit files under `dist/`.

## Rollback

- Restore the previous PyInstaller collection rules and rebuild; source runtime
  behavior remains unchanged.
