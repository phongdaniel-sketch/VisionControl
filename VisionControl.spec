import os
import sys

from PyInstaller.utils.hooks import collect_all


mediapipe_datas, mediapipe_binaries, mediapipe_hiddenimports = collect_all("mediapipe")
voice_datas, voice_binaries, voice_imports = [], [], []
for package in ('faster_whisper', 'ctranslate2', 'av', 'sounddevice', 'winrt'):
    data, binaries, imports = collect_all(package)
    voice_datas += data
    voice_binaries += binaries
    voice_imports += imports

# MediaPipe ships optional research and accelerator integrations that are not
# used by VisionControl's CPU hand landmarker. Excluding them avoids bundling
# hundreds of megabytes of JAX and SciPy code. Matplotlib remains because
# MediaPipe 0.10.21 imports it eagerly from the package initializer.
unused_optional_packages = [
    "Cython",
    "IPython",
    "jax",
    "jaxlib",
    "pandas",
    "scipy",
]

codesign_identity = os.environ.get("VISIONCONTROL_SIGN_IDENTITY") or None

analysis = Analysis(
    ["src/vision_control/launcher.py"],
    pathex=["src"],
    binaries=mediapipe_binaries + voice_binaries,
    datas=[
        ("docs/Vision Control logo.png", "docs"),
        ("docs/Splash Screen.png", "docs"),
        ("docs/Loading Screen.png", "docs"),
        ("assets/ui", "assets/ui"),
        ("config/default_profile.json", "config"),
        ("config/gesture_v1_profile.json", "config"),
        ("assets/models/hand_landmarker.task", "assets/models"),
    ] + mediapipe_datas + voice_datas + [
        ("models/faster-whisper-small/" + filename, "models/faster-whisper-small")
        for filename in ('config.json', 'model.bin', 'tokenizer.json', 'vocabulary.txt')
    ],
    hiddenimports=mediapipe_hiddenimports + voice_imports,
    hookspath=['packaging/hooks'],
    runtime_hooks=[],
    excludes=unused_optional_packages,
    noarchive=False,
)

pyz = PYZ(analysis.pure)

executable = EXE(
    pyz,
    analysis.scripts,
    [],
    exclude_binaries=True,
    name="VisionControl",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=codesign_identity,
    version="packaging/windows-version.txt" if sys.platform == 'win32' else None,
    entitlements_file="packaging/macos-entitlements.plist",
    icon="assets/VisionControl.ico" if sys.platform == 'win32' else "assets/VisionControl.icns",
)

collection = COLLECT(
    executable,
    analysis.binaries,
    analysis.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="VisionControl",
)

app = BUNDLE(
    collection,
    name="VisionControl.app",
    icon="assets/VisionControl.icns",
    bundle_identifier="com.visioncontrol.desktop",
    info_plist={
        "CFBundleDisplayName": "VisionControl",
        "CFBundleShortVersionString": "1.0.0",
        "CFBundleVersion": "1",
        "NSCameraUsageDescription": "VisionControl uses the camera to detect hand gestures for local mouse and keyboard control.",
        "NSHighResolutionCapable": True,
    },
)
