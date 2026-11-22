#!/usr/bin/env python3
"""Draw the FE4 (Genealogy of the Holy War) border strips and window texture
into public/fe4/img/border/, to go with the hand-drawn public/fe4/img/frame.png.

- edge-*.png: cut straight from frame.png's own edge strips (the repeating
  middle of each side), so the header, footer and column sides always match
  the hand-drawn panel frame. frame.png is drawn with FRAME_SCALE image px
  per game pixel; the strips are re-scaled to SCALE so every game's borders
  share one pixel size.
- texture.png: Thracia's splotch tile (tools/make_borders.py) in light blues.

frame.png itself is never touched.

    python3 tools/make_fe4_borders.py   # needs Pillow
"""
import sys
from pathlib import Path

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
import make_borders  # noqa: E402  (shared splotch texture)

IMG = Path(__file__).resolve().parent.parent / "public" / "fe4" / "img"
OUT = IMG / "border"
FRAME_SCALE = 3          # frame.png is drawn at 3 image px per game pixel
SCALE = 2                # output: 2 screen px per game pixel, like the other games

# four light-ish blues for the splotches, darkest first (dark enough that the
# site's pale text stays readable on top)
SHADES = [(0x22, 0x40, 0x5a), (0x28, 0x4a, 0x67), (0x2f, 0x55, 0x75), (0x37, 0x61, 0x84)]


def save(im, name):
    """im is at 1 px per game pixel."""
    im.resize((im.width * SCALE, im.height * SCALE), Image.NEAREST).save(OUT / name)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    frame = Image.open(IMG / "frame.png").convert("RGBA")
    # back to 1 px per game pixel (sample the middle of each block)
    n = frame.width // FRAME_SCALE
    frame = frame.resize((n, n), Image.NEAREST, box=(0, 0, n * FRAME_SCALE, n * FRAME_SCALE))
    c = (n - 2) // 2                          # corner size; the middle 2 px repeat along each edge
    print(f"frame: {n}x{n} game px, {c} px corners")

    save(frame.crop((c, 0, c + 2, c)), "edge-top.png")         # footer top: outside up
    save(frame.crop((c, n - c, c + 2, n)), "edge-bottom.png")  # header bottom: outside down
    save(frame.crop((0, c, c, c + 2)), "edge-left.png")
    save(frame.crop((n - c, c, n, c + 2)), "edge-right.png")
    save(make_borders.texture(SHADES), "texture.png")
    print("wrote", ", ".join(sorted(p.name for p in OUT.glob("*.png"))), "to", OUT)


if __name__ == "__main__":
    main()
