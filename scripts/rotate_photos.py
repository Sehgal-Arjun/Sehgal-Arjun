#!/usr/bin/env python3
"""Pick 4 photos from assets/photos/pool and lay them out for the README.

Writes:
  assets/photos/row.webp   4 across, for desktop
  assets/photos/grid.webp  2 x 2, for phones

GitHub strips styling from README images, so the rounded corners are baked
into the images (transparent corners work on both light and dark themes).
The pick is seeded by today's date, so re-running on the same day gives the
same photos. A GitHub Action runs this once a day.

Run:  python3 scripts/rotate_photos.py            (today's pick)
      python3 scripts/rotate_photos.py --seed x   (any other pick)
"""
import argparse
import datetime as dt
import random
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent.parent
POOL = ROOT / "assets/photos/pool"
OUT = ROOT / "assets/photos"

SCALE = 2  # render at 2x so they stay sharp on retina screens


def rounded(img, radius):
    mask = Image.new("L", img.size, 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, img.size[0] - 1, img.size[1] - 1), radius, fill=255)
    out = Image.new("RGBA", img.size, (0, 0, 0, 0))
    out.paste(img, (0, 0), mask)
    return out


def square(path, size):
    im = Image.open(path).convert("RGB")
    w, h = im.size
    s = min(w, h)
    im = im.crop(((w - s) // 2, (h - s) // 2, (w - s) // 2 + s, (h - s) // 2 + s))
    return im.resize((size, size), Image.LANCZOS)


def layout(paths, width, cols, gap, radius):
    width, gap, radius = width * SCALE, gap * SCALE, radius * SCALE
    tile = (width - gap * (cols - 1)) // cols
    rows = (len(paths) + cols - 1) // cols
    canvas = Image.new("RGBA", (width, rows * tile + (rows - 1) * gap), (0, 0, 0, 0))
    for i, p in enumerate(paths):
        x = (i % cols) * (tile + gap)
        y = (i // cols) * (tile + gap)
        t = rounded(square(p, tile), radius)
        canvas.alpha_composite(t, (x, y))
    return canvas


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", default=dt.date.today().isoformat())
    args = ap.parse_args()

    pool = sorted(p for p in POOL.iterdir() if p.suffix.lower() in {".jpg", ".jpeg", ".png", ".webp"})
    picks = random.Random(args.seed).sample(pool, 4)
    layout(picks, 840, 4, 12, 12).save(OUT / "row.webp", quality=82, method=6)
    layout(picks, 358, 2, 10, 12).save(OUT / "grid.webp", quality=82, method=6)
    print("picked:", ", ".join(p.name for p in picks))


if __name__ == "__main__":
    main()
