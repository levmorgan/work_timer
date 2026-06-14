"""Generate icon.icns for the work_timer app.

Draws a minimalist tomato silhouette in #e0e0e0 on #1a1a1a background.
Requires Pillow and macOS (for iconutil).
"""

import math
import subprocess
import shutil
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw

BG = (0x1A, 0x1A, 0x1A)  # #1a1a1a
FG = (0xE0, 0xE0, 0xE0)  # #e0e0e0

SIZES = [16, 32, 64, 128, 256, 512, 1024]


def draw_tomato(draw: ImageDraw.Draw, size: int) -> None:
    """Draw a tomato silhouette centered on a square canvas of given size."""
    margin = size * 0.12
    cx = size / 2
    available = size - 2 * margin

    # Body: slightly flattened circle (tomato shape)
    body_rx = available * 0.35
    body_ry = available * 0.33
    body_y = size * 0.55  # centre of body, shifted down to make room for leaf
    draw.ellipse(
        [
            (cx - body_rx, body_y - body_ry),
            (cx + body_rx, body_y + body_ry),
        ],
        fill=FG,
    )

    # Stem
    stem_bottom = body_y - body_ry * 1.02
    stem_top = stem_bottom - available * 0.10
    stem_width = available * 0.025
    draw.rectangle(
        [
            (cx - stem_width, stem_top),
            (cx + stem_width, stem_bottom),
        ],
        fill=FG,
    )

    # Leaf on the right side of the stem
    leaf_cx = cx + stem_width + available * 0.07
    leaf_cy = stem_top + (stem_bottom - stem_top) * 0.4
    leaf_rx = available * 0.10
    leaf_ry = available * 0.035
    draw.ellipse(
        [
            (leaf_cx - leaf_rx, leaf_cy - leaf_ry),
            (leaf_cx + leaf_rx, leaf_cy + leaf_ry),
        ],
        fill=FG,
    )


def generate_iconset(output_dir: Path) -> Path:
    """Generate PNGs at all required sizes in an .iconset directory."""
    iconset = output_dir / "icon.iconset"
    iconset.mkdir(parents=True, exist_ok=True)

    for size in SIZES:
        img = Image.new("RGB", (size, size), BG)
        draw = ImageDraw.Draw(img)
        draw_tomato(draw, size)

        # Standard resolution
        img.save(iconset / f"icon_{size}x{size}.png")

        # Retina (@2x) — save as the 2x version of the half-size
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

    # Clean up iconset directory
    shutil.rmtree(iconset)

    print(f"Generated {icns_path}")


if __name__ == "__main__":
    main()
