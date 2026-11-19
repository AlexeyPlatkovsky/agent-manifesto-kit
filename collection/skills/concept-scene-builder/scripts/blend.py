#!/usr/bin/env python3
"""Overlay a render on the concept to check camera and layout alignment.

blend.py CONCEPT RENDER -o out.png [--alpha 0.5]   (the render is resized to the concept size)
Requires Pillow.
"""
import argparse

from PIL import Image


def blend(concept, render, out, alpha=0.5):
    c = Image.open(concept).convert("RGB")
    r = Image.open(render).convert("RGB").resize(c.size, Image.LANCZOS)
    Image.blend(c, r, alpha).save(out)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("concept")
    ap.add_argument("render")
    ap.add_argument("-o", required=True)
    ap.add_argument("--alpha", type=float, default=0.5)
    a = ap.parse_args(argv)
    if not 0.0 <= a.alpha <= 1.0:
        ap.error("--alpha must be between 0 and 1")
    blend(a.concept, a.render, a.o, a.alpha)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
