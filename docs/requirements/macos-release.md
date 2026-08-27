# macOS acceptance, bundle optimization, and release

Status: APPROVED (user requested completion on 2026-08-27)

## Requirements

- Validate the packaged application without requiring a separate Python install.
- Start controller smoke tests paused and keep all camera frames local.
- Verify the application metadata declares Camera access and document the manual
  Camera and Accessibility checks that cannot be automated safely.
- Remove optional MediaPipe dependencies that VisionControl does not use while
  preserving the Tasks hand landmarker, OpenCV, Qt, and the offline model.
- Produce reproducible macOS ZIP and DMG artifacts from a clean app bundle.
- Support Developer ID Application signing and Apple notarization when release
  credentials are provided; never store credentials in the repository.
- Fail release operations clearly when the required identity or notarization
  profile is unavailable rather than silently shipping an ad-hoc build.

## Acceptance criteria

- Deterministic tests and Python bytecode compilation pass.
- The optimized application opens Settings and its packaged controller reaches
  paused startup with camera index `1` on the validated Mac.
- The application bundle contains neither JAX/JAXlib nor SciPy. Matplotlib is
  retained because MediaPipe 0.10.21 imports it eagerly through its package
  initializer even when VisionControl uses only the Tasks API.
- The optimized application is materially smaller than the 820 MB baseline.
- `codesign --verify --deep --strict` passes for the local artifact.
- A DMG and metadata-preserving ZIP are generated and their SHA-256 hashes are
  recorded.
- The release script supports Developer ID signing plus notarization/stapling,
  but refuses notarization if its credentials are missing.

## Manual user acceptance checks

- Grant Camera and Accessibility to `VisionControl.app` itself.
- Confirm mouse movement, all pinch buttons and drag, scrolling, keyboard
  Press/Hold chords, arming/disarming, calibration, and monitor switching.
- Confirm pause, hand loss, calibration, normal exit, and forced error paths
  release every held mouse button and keyboard key.

## Constraints

- macOS privacy prompts and physical hand/camera behavior require a person at
  the machine and cannot be asserted by deterministic automation.
- Public notarization requires a `Developer ID Application` certificate and
  Apple notary credentials. An Apple Development identity is not a substitute.
