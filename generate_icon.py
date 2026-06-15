"""Generate app icons for the work_timer app.

Draws the text 'work' in #e0e0e0 on a #1a1a1a background.
On macOS: produces icon.icns via iconutil.
On Windows: produces icon.ico via Pillow.
On Linux: produces icon.png.
"""

import shutil
import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

BG = (0x1A, 0x1A, 0x1A)  # #1a1a1a
FG = (0xE0, 0xE0, 0xE0)  # #e0e0e0

SIZES = [16, 32, 64, 128, 256, 512, 1024]
BASE_SIZE = 1024

FONT_PATHS = [
    # macOS
    "/System/Library/Fonts/Menlo.ttc",
    "/System/Library/Fonts/Helvetica.ttc",
    # Linux
    "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationMono-Regular.ttf",
    # Windows
    "C:/Windows/Fonts/consola.ttf",
    "C:/Windows/Fonts/cour.ttf",
    # fallback
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


def _draw_text(draw: ImageDraw.Draw, size: int) -> None:
    font_size = max(int(size * 0.28), 12)
    font = _load_font(font_size)
    draw.text(
        (size / 2, size / 2), "work",
        fill=FG, font=font, anchor="mm",
    )


def _base_image() -> Image.Image:
    img = Image.new("RGB", (BASE_SIZE, BASE_SIZE), BG)
    _draw_text(ImageDraw.Draw(img), BASE_SIZE)
    return img


def _gen_icns(output_dir: Path) -> Path:
    iconset = output_dir / "icon.iconset"
    iconset.mkdir(parents=True, exist_ok=True)
    for size in SIZES:
        img = _base_image().resize((size, size), Image.LANCZOS)
        img.save(iconset / f"icon_{size}x{size}.png")
        half = size // 2
        if half >= 16:
            img.save(iconset / f"icon_{half}x{half}@2x.png")

    icns = output_dir / "icon.icns"
    subprocess.run(
        ["iconutil", "-c", "icns", "-o", str(icns), str(iconset)],
        check=True,
    )
    shutil.rmtree(iconset)
    return icns


def _gen_ico(output_dir: Path) -> Path:
    ico = output_dir / "icon.ico"
    # Standard Windows icon sizes, largest first (required by Windows)
    sizes = [256, 128, 64, 48, 32, 24, 16]
    base = _base_image()
    imgs = [base.resize((s, s), Image.LANCZOS) for s in sizes]
    # Pillow ICO saver — each sub-image must match its declared size
    imgs[0].save(
        ico, format="ICO",
        sizes=[(s, s) for s in sizes],
        append_images=imgs[1:],
    )
    return ico


def _gen_png(output_dir: Path) -> Path:
    png = output_dir / "icon.png"
    _base_image().save(png, "PNG")
    return png


def main() -> None:
    output_dir = Path(__file__).resolve().parent

    if sys.platform == "darwin":
        path = _gen_icns(output_dir)
    elif sys.platform == "win32":
        path = _gen_ico(output_dir)
    else:
        path = _gen_png(output_dir)

    print(f"Generated {path}")


if __name__ == "__main__":
    main()
