"""Generate icon.icns for the work_timer app.

Draws the text 'work' in #e0e0e0 on a #1a1a1a background.
Requires Pillow and macOS (for iconutil).
"""

import shutil
import subprocess
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

BG = (0x1A, 0x1A, 0x1A)  # #1a1a1a
FG = (0xE0, 0xE0, 0xE0)  # #e0e0e0

SIZES = [16, 32, 64, 128, 256, 512, 1024]

FONT_PATHS = [
    "/System/Library/Fonts/Menlo.ttc",
    "/System/Library/Fonts/Helvetica.ttc",
    "/Library/Fonts/Arial.ttf",
]


def _load_font(size: int) -> ImageFont.FreeTypeFont:
    for path in FONT_PATHS:
        if Path(path).exists():
            try:
                return ImageFont.truetype(path, size=size)
            except OSError:
                continue
    return ImageFont.load_default()


def draw_text(draw: ImageDraw.Draw, size: int) -> None:
    """Draw 'work' centred on the canvas."""
    font_size = max(int(size * 0.42), 12)
    font = _load_font(font_size)
    bbox = draw.textbbox((0, 0), "work", font=font)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    x = (size - tw) / 2
    y = (size - th) / 2 - font_size * 0.05
    draw.text((x, y), "work", fill=FG, font=font)


def generate_iconset(output_dir: Path) -> Path:
    """Generate PNGs at all required sizes in an .iconset directory."""
    iconset = output_dir / "icon.iconset"
    iconset.mkdir(parents=True, exist_ok=True)

    for size in SIZES:
        img = Image.new("RGB", (size, size), BG)
        draw = ImageDraw.Draw(img)
        draw_text(draw, size)

        img.save(iconset / f"icon_{size}x{size}.png")

        half = size // 2
        if half >= 16:
            img.save(iconset / f"icon_{half}x{half}@2x.png")

    return iconset


def main() -> None:
    output_dir = Path(__file__).resolve().parent
    iconset = generate_iconset(output_dir)

    icns_path = output_dir / "icon.icns"
    subprocess.run(
        ["iconutil", "-c", "icns", "-o", str(icns_path), str(iconset)],
        check=True,
    )

    shutil.rmtree(iconset)
    print(f"Generated {icns_path}")


if __name__ == "__main__":
    main()
