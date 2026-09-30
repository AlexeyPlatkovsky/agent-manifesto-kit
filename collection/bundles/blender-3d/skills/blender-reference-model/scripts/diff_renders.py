"""Compare two folders of renders view by view (for example before and after rigging).

  python3 diff_renders.py BEFORE_DIR AFTER_DIR [--tolerance 2] [--out diff.png]

For every <view>.png present in both folders: silhouette IoU of the alpha masks, the largest
per-channel difference, and how many pixels differ by more than --tolerance (0-255). Exits
non-zero when any view changed beyond the tolerance, so a "the model did not change" claim is
checked rather than asserted. --out writes a sheet highlighting changed pixels in red.
"""
import argparse
import glob
import os

import numpy as np
from PIL import Image


def main():
    p = argparse.ArgumentParser()
    p.add_argument("before")
    p.add_argument("after")
    p.add_argument("--tolerance", type=int, default=2)
    p.add_argument("--out")
    args = p.parse_args()
    views = sorted(os.path.basename(f) for f in glob.glob(os.path.join(args.before, "*.png"))
                   if os.path.exists(os.path.join(args.after, os.path.basename(f))))
    if not views:
        raise SystemExit("no matching <view>.png files in both folders")
    changed, tiles = False, []
    for name in views:
        a = np.asarray(Image.open(os.path.join(args.before, name)).convert("RGBA")).astype(int)
        b = np.asarray(Image.open(os.path.join(args.after, name)).convert("RGBA")).astype(int)
        if a.shape != b.shape:
            print(f"{name}: size differs {a.shape[1]}x{a.shape[0]} vs {b.shape[1]}x{b.shape[0]}")
            changed = True
            continue
        ma, mb = a[..., 3] > 128, b[..., 3] > 128
        iou = (ma & mb).sum() / max((ma | mb).sum(), 1)
        diff = np.abs(a - b).max(2)
        over = diff > args.tolerance
        changed |= bool(over.any())
        print(f"{name:14s} IoU {iou:.4f}  max channel diff {int(diff.max()):3d}  pixels over tolerance {int(over.sum())}")
        tile = np.asarray(Image.fromarray(b.astype(np.uint8)).convert("RGB")).copy()
        tile[over] = (230, 40, 40)
        tiles.append(Image.fromarray(tile))
    if args.out and tiles:
        sheet = Image.new("RGB", (sum(t.size[0] for t in tiles), max(t.size[1] for t in tiles)), (20, 20, 20))
        x = 0
        for t in tiles:
            sheet.paste(t, (x, 0))
            x += t.size[0]
        sheet.save(args.out)
    print("CHANGED" if changed else "IDENTICAL within tolerance")
    raise SystemExit(1 if changed else 0)


if __name__ == "__main__":
    main()
