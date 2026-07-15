#!/usr/bin/env python3
"""Optimize hero/section photos for the web.

Drops any large PNG/JPG into assets/images/stock/ and run this to
re-encode every image to a progressive JPG (quality 82, max 1600px
wide). Full-page photos as PNG are typically 2-4 MB; as JPG ~150-300 KB
with no visible loss — the difference between a snappy load and a slow
one, especially on mobile data.

Usage:
    python tools/optimize-images.py            # optimize whole stock dir
    python tools/optimize-images.py hero.png   # one file (writes hero.jpg)

Requires Pillow:  pip install Pillow
"""
import os
import sys
from PIL import Image

STOCK = os.path.join(os.path.dirname(__file__), "..", "assets", "images", "stock")
MAX_W = 1600
QUALITY = 82


def optimize(path):
    root, _ = os.path.splitext(path)
    dst = root + ".jpg"
    before = os.path.getsize(path)
    im = Image.open(path).convert("RGB")
    if im.width > MAX_W:
        im = im.resize((MAX_W, round(MAX_W * im.height / im.width)), Image.LANCZOS)
    im.save(dst, "JPEG", quality=QUALITY, optimize=True, progressive=True)
    after = os.path.getsize(dst)
    # drop the heavy source if it was a PNG we just replaced
    if path.lower().endswith(".png") and os.path.exists(dst):
        os.remove(path)
    saved = 100 - after * 100 // before if before else 0
    print(f"{os.path.basename(path):28} {before//1024:>6}KB -> {after//1024:>4}KB  ({saved}% smaller)")


def main():
    args = sys.argv[1:]
    if args:
        for a in args:
            p = a if os.path.isabs(a) else os.path.join(STOCK, a)
            optimize(p)
    else:
        for f in sorted(os.listdir(STOCK)):
            if f.lower().endswith((".png", ".jpeg")):
                optimize(os.path.join(STOCK, f))


if __name__ == "__main__":
    main()
