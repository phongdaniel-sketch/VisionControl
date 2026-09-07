# Shared main and macOS verification

`main` contains the shared application source. `windows` was a temporary
development branch, not a separate product. Build Windows and macOS artifacts
on their respective operating systems; this integration does not publish binaries.

## Integration review (2026-09-07)

- Remote main already included PR #1. Merged the remaining Settings/drag-volume
  commit 66e93d9 without conflicts.
- Camera enumeration selects DirectShow on Windows and AVFoundation on macOS.
  cv2-enumerate-cameras declares its AVFoundation dependency for Darwin.
- Windows capture settings are platform guarded. Shared paths, input adapter,
  Qt UI and the macOS bundle configuration remain present.
- Windows: 146 deterministic tests, compileall and pip check pass.
- No macOS execution or new packaged build was performed on this Windows host.

## Run on a Mac

From a clean checkout of main, using Python 3.11:

```bash
python3.11 -m venv .venv311
.venv311/bin/python -m pip install -r requirements.txt
.venv311/bin/python -m pip install -e .
.venv311/bin/python -m pip check
QT_QPA_PLATFORM=offscreen PYTHONPATH=src .venv311/bin/python -m unittest discover -s tests -v
PYTHONPATH=src .venv311/bin/python -m compileall -q src tests scripts
PYTHONPATH=src .venv311/bin/python -m vision_control.launcher --camera-index 0 --start-paused
```

Choose the correct camera by name in Settings if camera 0 is not the intended
device. Verify camera/input permissions, both pointer sources and their separate
calibrations, click/drag/release, volume/scroll/zoom, modifier release on pause or
hand loss, multiple displays, and the Settings-to-recorder camera handoff.
Run the existing macOS packaging workflow on the Mac after runtime acceptance.
