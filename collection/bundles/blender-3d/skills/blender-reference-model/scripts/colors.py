"""Compare sampled colours between the reference and the renders.

  python3 colors.py ref_spec.json RENDERDIR points.json

points.json maps a label to [view, x, y] in reference image pixels, for example
  {"skin_cheek": ["front", 278, 85], "trousers": ["front", 260, 330]}
Each sample averages a 5x5 patch. ratio = reference / render per channel: values above 1 mean the
render is too dark. Reference samples are display (sRGB) values while Blender's Base Color is
linear, so convert before use, then adjust until the ratios are close to 1.
"""
import argparse
import json
import os
import sys

import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from refspec import background_colour, composite, load_reference, load_spec  # noqa: E402


def main():
    p = argparse.ArgumentParser()
    p.add_argument("spec")
    p.add_argument("render_dir")
    p.add_argument("points")
    args = p.parse_args()
    spec = load_spec(args.spec)
    _, arr = load_reference(spec)
    bg = background_colour(arr)
    with open(args.points) as f:
        points = json.load(f)
    renders = {}
    print(f"{'label':16s} {'reference':>15s} {'render':>15s}  ratio")
    for label, (view, x, y) in points.items():
        cx0, cy0, cx1, cy1 = spec["views"][view]["crop"]
        if view not in renders:
            img = composite(Image.open(os.path.join(args.render_dir, f"{view}.png")).convert("RGBA"), bg)
            renders[view] = (np.asarray(img).astype(float), img.size[0] / (cx1 - cx0), img.size[1] / (cy1 - cy0))
        ren, sx, sy = renders[view]
        rx, ry = round((x - cx0) * sx), round((y - cy0) * sy)
        a = arr[y - 2:y + 3, x - 2:x + 3].reshape(-1, 3).mean(0)
        b = ren[max(ry - 2, 0):ry + 3, max(rx - 2, 0):rx + 3].reshape(-1, 3).mean(0)
        ratio = np.round(a / np.maximum(b, 1), 2)
        print(f"{label:16s} {str(a.astype(int).tolist()):>15s} {str(b.astype(int).tolist()):>15s}  {ratio.tolist()}")


if __name__ == "__main__":
    main()
