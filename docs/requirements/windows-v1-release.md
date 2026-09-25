# Windows v1.0 release requirements

- Voice Copy, Paste, and Close Window preserve the current gesture-control state.
- Lock Computer always pauses gesture control before Windows is locked.
- README and release documentation describe the implemented Voice feature and current tests.
- Package metadata and the Windows executable report version 1.0.0.
- The distributable is the complete one-directory PyInstaller bundle in a ZIP archive.
- A SHA-256 sidecar accompanies the ZIP.
- The release script signs and verifies the executable when a trusted certificate thumbprint
  is supplied through `VISIONCONTROL_SIGN_CERT_THUMBPRINT`.
- An unsigned build must be identified as unsigned; a self-signed certificate must not be
  represented as reducing SmartScreen warnings.
- The source commit is tagged `v1.0.0`, pushed to GitHub, and the ZIP plus checksum are
  attached to a GitHub Release.

Verification:

- Voice state-preservation unit tests.
- Full deterministic suite.
- Python compile check and `git diff --check`.
- EXE FileVersion and ProductVersion inspection.
- ZIP checksum verification.
- Source and remote tag equality.

Physical microphone, hand-gesture, Windows Location, SmartScreen reputation, and lock-screen
acceptance remain manual checks on the release machine.
