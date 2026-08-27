"""Generate desktop icon formats from the canonical VisionControl logo."""

from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "docs" / "Vision Control logo.png"
OUTPUT = ROOT / "assets"
SIZES = (16, 32, 48, 64, 128, 256, 512, 1024)


def main() -> None:
    OUTPUT.mkdir(exist_ok=True)
    with Image.open(SOURCE) as source:
        logo = source.convert("RGBA")
        logo.save(OUTPUT / "VisionControl.ico", sizes=[(size, size) for size in SIZES[:-1]])
        logo.resize((1024, 1024), Image.Resampling.LANCZOS).save(
            OUTPUT / "VisionControl.icns"
        )
    print(f"Generated desktop icons in {OUTPUT}")


if __name__ == "__main__":
    main()
