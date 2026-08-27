# VisionControl

Local-first webcam control: right hand for mouse input, left hand for configurable keyboard gestures.

## MVP status

The deterministic controller core is implemented. Webcam runtime requires Python dependencies from `requirements.txt` and a Windows input permission setup.

## Setup

Use Python 3.11 on macOS and Windows 11.

```bash
python3.11 -m venv .venv
source .venv/bin/activate  # Windows: .venv\\Scripts\\activate
python -m pip install -r requirements.txt
python -m pip install -e .
python -m vision_control.app --camera-index 0
```

If a virtual camera occupies index `0`, select the physical webcam, for example
`--camera-index 1`. On macOS, grant Camera and Accessibility permissions to the
terminal or editor that launches the process.

The app defaults to `config/default_profile.json`. Set `swap_hands` there when a
mirrored camera reverses physical left/right roles. Press `Esc` in the preview to
stop. Press `p` to pause/resume.

## Safety

Keep the emergency stop available. The application releases all held mouse buttons and keys on pause, camera failure, normal exit, and exceptions. Camera frames are processed locally and are not uploaded.

## Development

```bash
PYTHONPATH=src python -m unittest discover -s tests -v
```

The test suite uses fake observations and a recording input adapter; it does not open a camera or emit OS input.
