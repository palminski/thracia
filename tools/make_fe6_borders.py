#!/usr/bin/env python3
"""Draw the FE6 (Binding Blade) border strips and window texture into
public/fe6/img/border/, to go with the hand-drawn public/fe6/img/frame.png.

- edge-*.png: the frame's edge stripe, read straight from frame.png (the
  middle row, outside -> inside, up to the first transparent pixel), so the
  header, footer and column sides always match the hand-drawn panel frame.
- texture.png: a diagonal diamond check, after the game's battle-window
  fill, in the site's own FE6 column colour.

Drawn at 1px per game pixel, scaled up by SCALE; the CSS shows them with
image-rendering: pixelated. frame.png itself is never touched.

    python3 tools/make_fe6_borders.py   # needs Pillow
"""
from pathlib import Path

from PIL import Image

IMG = Path(__file__).resolve().parent.parent / "public" / "fe6" / "img"
OUT = IMG / "border"
SCALE = 2

# diamond fill: two close shades of --column (#170c0c) plus a faint edge line
TILE = 16                                   # one diamond per tile, in game pixels
DARK, LIGHT, EDGE = (0x17, 0x0c, 0x0c), (0x20, 0x10, 0x10), (0x29, 0x15, 0x15)


def save(im, name):
    im.resize((im.width * SCALE, im.height * SCALE), Image.NEAREST).save(OUT / name)


def frame_stripe():
    frame = Image.open(IMG / "frame.png").convert("RGBA")
    y = frame.height // 2
    stripe = []
    for x in range(frame.width // 2):
        px = frame.getpixel((x, y))
        if px[3] == 0:
            break
        stripe.append(px)
    return stripe                           # outside -> inside


def texture():
    im = Image.new("RGB", (TILE, TILE))
    h = TILE // 2
    for y in range(TILE):
        for x in range(TILE):
            d = abs(x - h + 0.5) + abs(y - h + 0.5)   # distance from the tile centre
            if abs(d - h) < 0.6:
                col = EDGE                  # diamond outline
            elif d < h:
                col = LIGHT                 # diamond
            else:
                col = DARK                  # the diamonds between (at the tile corners)
            im.putpixel((x, y), col)
    return im


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    stripe = frame_stripe()
    w = len(stripe)

    top = Image.new("RGBA", (1, w))                     # header bottom: inside on top
    for y, c in enumerate(reversed(stripe)):
        top.putpixel((0, y), c)
    save(top, "edge-bottom.png")
    save(top.transpose(Image.FLIP_TOP_BOTTOM), "edge-top.png")

    left = Image.new("RGBA", (w, 1))                    # column sides: outside away from centre
    for x, c in enumerate(stripe):
        left.putpixel((x, 0), c)
    save(left, "edge-left.png")
    save(left.transpose(Image.FLIP_LEFT_RIGHT), "edge-right.png")

    save(texture(), "texture.png")
    print(f"stripe {w} game px wide; wrote", ", ".join(sorted(p.name for p in OUT.glob("*.png"))), "to", OUT)


if __name__ == "__main__":
    main()
