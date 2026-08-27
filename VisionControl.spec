from PyInstaller.utils.hooks import collect_all


mediapipe_datas, mediapipe_binaries, mediapipe_hiddenimports = collect_all("mediapipe")

analysis = Analysis(
    ["src/vision_control/launcher.py"],
    pathex=["src"],
    binaries=mediapipe_binaries,
    datas=[
        ("docs/Vision Control logo.png", "docs"),
        ("docs/Splash Screen.png", "docs"),
        ("docs/Loading Screen.png", "docs"),
        ("config/default_profile.json", "config"),
        ("assets/models/hand_landmarker.task", "assets/models"),
    ] + mediapipe_datas,
    hiddenimports=mediapipe_hiddenimports,
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
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
    codesign_identity=None,
    entitlements_file=None,
    icon="assets/VisionControl.icns",
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
        "CFBundleShortVersionString": "0.1.0",
        "CFBundleVersion": "1",
        "NSCameraUsageDescription": "VisionControl uses the camera to detect hand gestures for local mouse and keyboard control.",
        "NSHighResolutionCapable": True,
    },
)
