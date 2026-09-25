# Windows v1.0.0 release

Build the release from the repository root using Python 3.11:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/build_windows_release.ps1
```

Run `dist/voice-release/VisionControl/VisionControl.exe`. Distribute the entire
VisionControl directory, including `_internal`, not the EXE alone. The script packages
that directory as `release/VisionControl-1.0.0-windows-x64.zip` and writes the matching
SHA-256 value to `.zip.sha256`. The bundle includes faster-whisper-small and voice
runtime dependencies. No private data, recordings, or API keys are included.

The script Authenticode-signs and verifies the executable when
`VISIONCONTROL_SIGN_CERT_THUMBPRINT` identifies a trusted code-signing certificate in
the current user's certificate store. Without one, the build remains unsigned and may
trigger SmartScreen. Do not treat a self-signed certificate as a publisher signature.

Packaged settings are stored under `%LOCALAPPDATA%/VisionControl`, separate from
source `data/`. Voice and diagnostic logging default off in a fresh profile.
Voice Debug is an explicit diagnostic tool, not background recording.

Included: Vietnamese local voice commands, opt-in Gemini transcription, configurable
hotkeys, stereo BRIO capture, countdown overlay, weekday, paste aliases, close-window
and lock-screen commands; startup/tray settings and pointer hot corners.

Copy, Paste, and Close Window preserve the current gesture-control state. Lock Screen
always pauses gesture control before locking Windows; resuming requires an explicit
Start after sign-in. Lock is not shutdown or sleep.

Known limits: timers do not survive exit, speech accuracy depends on the microphone and
environment, and unsigned binaries may show SmartScreen. Voice recordings, gesture
ergonomics, lock-screen behavior, and SmartScreen reputation require physical acceptance.

Verification before packaging: 431 automated tests, compileall, diff check, executable
version inspection, Authenticode status inspection, and SHA-256 archive verification.
