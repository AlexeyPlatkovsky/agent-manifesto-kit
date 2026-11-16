#!/usr/bin/env python3
"""Side-by-side comparison sheets and blind A/B pairs for art direction passes.

sheet: compare.py sheet REF BEFORE [AFTER] -o out.png
blind: compare.py blind BEFORE AFTER -o dir/ [--mapping mapping.json]

`blind` writes dir/A.png and dir/B.png in random order. The mapping is written to --mapping, or
next to the folder (dir.mapping.json), never inside it. Put dir in a temporary directory outside
the project and keep the mapping in the project, away from the reviewer's files.
Requires Pillow.
"""
import argparse
import json
import pathlib
import random

from PIL import Image, ImageDraw

HEIGHT = 720
GAP = 10
LABEL_BAR = 30


def fit(path, height=HEIGHT):
    im = Image.open(path).convert("RGB")
    return im.resize((max(1, round(im.width * height / im.height)), height), Image.LANCZOS)


def sheet(paths, labels, out):
    ims = [fit(p) for p in paths]
    width = sum(i.width for i in ims) + GAP * (len(ims) - 1)
    canvas = Image.new("RGB", (width, HEIGHT + LABEL_BAR), (20, 20, 20))
    draw, x = ImageDraw.Draw(canvas), 0
    for im, label in zip(ims, labels):
        canvas.paste(im, (x, LABEL_BAR))
        draw.text((x + 8, 8), label, fill=(230, 230, 230))
        x += im.width + GAP
    canvas.save(out)
    return out


def mapping_path(out_dir):
    out_dir = pathlib.Path(out_dir).resolve()
    return out_dir.parent / f"{out_dir.name}.mapping.json"


def blind(before, after, out_dir, rng=random, mapping=None):
    out = pathlib.Path(out_dir).resolve()
    target = pathlib.Path(mapping).resolve() if mapping else mapping_path(out)
    if out == target.parent or out in target.parents:
        raise ValueError("the mapping must not be written inside the reviewer folder")
    images = [Image.open(p).convert("RGB") for p in (before, after)]  # fail before writing anything
    out.mkdir(parents=True, exist_ok=True)
    pair = [("before", images[0]), ("after", images[1])]
    rng.shuffle(pair)
    for slot, (_, image) in zip("AB", pair):
        image.save(out / f"{slot}.png")
    result = {slot: label for slot, (label, _) in zip("AB", pair)}
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(result) + "\n")
    return result


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("mode", choices=["sheet", "blind"])
    ap.add_argument("images", nargs="+")
    ap.add_argument("-o", required=True, help="output PNG (sheet) or output folder (blind)")
    ap.add_argument("--mapping", help="blind: where to write the A/B mapping (default: beside the folder)")
    a = ap.parse_args(argv)
    if a.mode == "sheet":
        if not 2 <= len(a.images) <= 3:
            ap.error("sheet takes REF BEFORE [AFTER]")
        sheet(a.images, ["reference", "before", "after"][: len(a.images)], a.o)
    else:
        if len(a.images) != 2:
            ap.error("blind takes exactly BEFORE AFTER")
        try:
            blind(a.images[0], a.images[1], a.o, mapping=a.mapping)
        except ValueError as e:
            ap.error(str(e))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
