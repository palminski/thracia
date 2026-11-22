#!/usr/bin/env python3
"""Draw the Thracia pixel borders into public/thracia/img/border/.

The stripe colours are sampled from the battle-forecast windows in the game
(plum-brown bevels, black gaps; the gold is softened to #d0b561); the corner
rivet is our own.
Images are drawn at 1px per game pixel then scaled up by SCALE, so the CSS
shows them with image-rendering: pixelated.

    python3 tools/make_borders.py   # needs Pillow
"""
from pathlib import Path

from PIL import Image

OUT = Path(__file__).resolve().parent.parent / "public" / "thracia" / "img" / "border"
SCALE = 2

K, P, G, M = (0, 0, 0), (0x48, 0x30, 0x38), (0xd0, 0xb5, 0x61), (0x70, 0x50, 0x50)
# outside -> inside, as in the game's window frame
STRIPE = [K, P, G, M, P, K, P]
W = len(STRIPE)


def save(im, name):
    im.resize((im.width * SCALE, im.height * SCALE), Image.NEAREST).save(OUT / name)


# Top-left corner ornament, after William's hand-drawn sketch: a rounded gold
# knot with a lattice of dark holes, centred on the point where the gold lines
# meet. It is OUT_PX bigger than the stripe on the outside, so it pokes out
# past the frame (CSS border-image-outset). Symmetric across the diagonal;
# the last row and column must equal "..KPGMPKP" (the stripe) so the corner
# joins the edges.
OUT_PX = 2
C = W + OUT_PX                      # corner size in game pixels
CLEAR = (0, 0, 0, 0)
CORNER = [
    "..KKKKK..",
    ".KGGGGGK.",
    "KGPGKGPGK",
    "KGGPGPGGP",
    "KGKGGGKGG",
    "KGGPGPGGM",
    "KGPGKGPGP",
    ".KGGGGGKK",
    "..KPGMPKP",
]
CODES = {".": CLEAR, "K": K + (255,), "P": P + (255,), "G": G + (255,), "M": M + (255,)}


def corner():
    assert all(CORNER[y][x] == CORNER[x][y] for y in range(C) for x in range(C)), "corner not symmetric"
    im = Image.new("RGBA", (C, C), CLEAR)
    for y, row in enumerate(CORNER):
        for x, ch in enumerate(row):
            im.putpixel((x, y), CODES[ch])
    return im


# Splotchy "watercolour" fill, in the spirit of the game's window backgrounds
# but in the site's own column brown (--column #1f1612). Seamless tile.
TEX = 96                                   # tile size in game pixels
TEX_SHADES = [(0x1a, 0x12, 0x0f), (0x1f, 0x16, 0x12), (0x25, 0x1a, 0x15), (0x2a, 0x1e, 0x18)]


def texture(shades=TEX_SHADES):
    """The splotch tile; other games reuse it with their own four shades."""
    import random
    rnd = random.Random(776)

    def octave(cells):
        """Smooth value noise on a cells x cells grid that wraps around."""
        grid = [[rnd.random() for _ in range(cells)] for _ in range(cells)]
        step = TEX / cells

        def at(x, y):
            gx, gy = x / step, y / step
            x0, y0 = int(gx), int(gy)
            fx, fy = gx - x0, gy - y0
            fx, fy = fx * fx * (3 - 2 * fx), fy * fy * (3 - 2 * fy)
            a = grid[y0 % cells][x0 % cells]
            b = grid[y0 % cells][(x0 + 1) % cells]
            c = grid[(y0 + 1) % cells][x0 % cells]
            d = grid[(y0 + 1) % cells][(x0 + 1) % cells]
            return (a * (1 - fx) + b * fx) * (1 - fy) + (c * (1 - fx) + d * fx) * fy
        return at

    layers = [(octave(4), 0.55), (octave(8), 0.3), (octave(24), 0.15)]
    vals = [[sum(f(x, y) * w for f, w in layers) for x in range(TEX)] for y in range(TEX)]
    flat = sorted(v for row in vals for v in row)
    # cut points chosen by share of area: mostly base brown, a few dark and light blots
    cuts = [flat[int(len(flat) * q)] for q in (0.18, 0.62, 0.9)]
    im = Image.new("RGB", (TEX, TEX))
    for y in range(TEX):
        for x in range(TEX):
            im.putpixel((x, y), shades[sum(vals[y][x] > c for c in cuts)])
    return im


def main():
    OUT.mkdir(parents=True, exist_ok=True)

    # header bottom edge: header above (inside), page below (outside)
    h = Image.new("RGB", (1, W))
    for y, c in enumerate(reversed(STRIPE)):
        h.putpixel((0, y), c)
    save(h, "edge-bottom.png")
    save(h.transpose(Image.FLIP_TOP_BOTTOM), "edge-top.png")   # footer top edge

    # column sides: outside is away from the centre column
    left = Image.new("RGB", (W, 1))
    for x, c in enumerate(STRIPE):
        left.putpixel((x, 0), c)
    save(left, "edge-left.png")
    save(left.transpose(Image.FLIP_LEFT_RIGHT), "edge-right.png")

    # full frame for CSS border-image: C x C corners, a 1px edge between them
    n = 2 * C + 1
    frame = Image.new("RGBA", (n, n), CLEAR)
    c = corner()
    frame.paste(c, (0, 0))
    frame.paste(c.transpose(Image.FLIP_LEFT_RIGHT), (C + 1, 0))
    frame.paste(c.transpose(Image.FLIP_TOP_BOTTOM), (0, C + 1))
    frame.paste(c.transpose(Image.ROTATE_180), (C + 1, C + 1))
    for i, col in enumerate(STRIPE, start=OUT_PX):
        for xy in ((C, i), (C, n - 1 - i), (i, C), (n - 1 - i, C)):
            frame.putpixel(xy, col + (255,))
    # frame.png is now hand-edited: only draw it if it is missing
    if not (OUT / "frame.png").exists():
        save(frame, "frame.png")
    save(texture(), "texture.png")
    print("wrote", ", ".join(sorted(p.name for p in OUT.glob("*.png"))), "to", OUT)


if __name__ == "__main__":
    main()
