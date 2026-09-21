# Windows voice release (2026-09-21)

Build from the repository root using Python 3.11:

```powershell
.\.venv311\Scripts\python.exe -m PyInstaller --noconfirm --distpath dist/voice-release --workpath build/voice-release VisionControl.spec
```

Run `dist/voice-release/VisionControl/VisionControl.exe`. Distribute the entire
VisionControl directory, including `_internal`, not the EXE alone. The bundle
includes faster-whisper-small and voice runtime dependencies. No private data,
recordings or API keys are included. The unsigned build may trigger SmartScreen.

Packaged settings are stored under `%LOCALAPPDATA%/VisionControl`, separate from
source `data/`. Voice and diagnostic logging default off in a fresh profile.
Voice Debug is an explicit diagnostic tool, not background recording.

Included: Vietnamese local voice commands, opt-in Gemini transcription, configurable
hotkeys, stereo BRIO capture, countdown overlay, weekday, paste aliases, close-window
and lock-screen commands; startup/tray settings and pointer hot corners.

Known limits: timers do not survive exit; Copy/Paste and window/lock actions pause
gestures; speech accuracy still depends on the input. Lock is not shutdown/sleep.
Voice recordings and Windows actions require physical acceptance testing.

Verification before packaging: 399 unit tests passed, compileall and diff checks
passed. Packaging uses a custom hook for the webrtcvad-wheels distribution.
