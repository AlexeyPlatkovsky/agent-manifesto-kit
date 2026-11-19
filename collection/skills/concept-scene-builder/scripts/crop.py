#!/usr/bin/env python3
"""Cut kit-sheet items into per-asset reference images.

crop.py SHEET boxes.json -o docs/art/reference/kit/
boxes.json: {"tile_grass": [x0, y0, x1, y1], ...} in sheet pixels. Requires Pillow.
"""
import argparse
import json
import pathlib
import re

from PIL import Image


NAME = re.compile(r"^[A-Za-z0-9_][A-Za-z0-9_.-]*$")


def crop(sheet, boxes, out_dir):
    if not isinstance(boxes, dict):
        raise ValueError('boxes must be an object: {"name": [x0, y0, x1, y1], ...}')
    im = Image.open(sheet).convert("RGB")
    for name, box in boxes.items():  # check everything before writing anything
        if not NAME.match(name):
            raise ValueError(f"box name {name!r} must be a plain file name")
        if not (isinstance(box, list) and len(box) == 4 and all(isinstance(v, int) for v in box)):
            raise ValueError(f"box {name} must be four integers [x0, y0, x1, y1], got {box!r}")
        x0, y0, x1, y1 = box
        if not (0 <= x0 < x1 <= im.width and 0 <= y0 < y1 <= im.height):
            raise ValueError(f"box {name} {box} is outside the {im.width}x{im.height} sheet or empty")
    out = pathlib.Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    written = []
    for name, box in boxes.items():
        path = out / f"{name}.png"
        im.crop(tuple(box)).save(path)
        written.append(path)
    return written


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("sheet")
    ap.add_argument("boxes")
    ap.add_argument("-o", required=True)
    a = ap.parse_args(argv)
    with open(a.boxes) as f:
        boxes = json.load(f)
    try:
        crop(a.sheet, boxes, a.o)
    except ValueError as e:
        ap.error(str(e))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
