"""Silhouette overlap and comparison sheet: reference vs render_views.py output.

  python3 compare.py ref_spec.json RENDERDIR [--out RENDERDIR/compare.png] [--json RENDERDIR/compare.json]

Sheet rows: reference crop, render on the reference background, overlay
(grey = both, red = reference only / missing in model, blue = model only / extra).
IoU (intersection over union) is 1.0 for identical silhouettes. It says nothing about details
inside the outline; inspect zoom crops for those.
"""
import argparse
import json
import os
import sys

import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from refspec import background_colour, composite, load_reference, load_spec, reference_mask, render_image, render_mask  # noqa: E402


def main():
    p = argparse.ArgumentParser()
    p.add_argument("spec")
    p.add_argument("render_dir")
    p.add_argument("--out")
    p.add_argument("--json")
    args = p.parse_args()
    spec = load_spec(args.spec)
    ref, arr = load_reference(spec)
    bg = background_colour(arr)
    mpp = spec["meters_per_px"]

    columns, report = [], {}
    for name, view in spec["views"].items():
        x0, y0, x1, y1 = view["crop"]
        crop = ref.crop((x0, y0, x1, y1))
        rm = reference_mask(spec, arr, name)
        img = render_image(args.render_dir, name, crop.size)
        mm = render_mask(img)
        inter, union = int((rm & mm).sum()), int((rm | mm).sum())
        ref_rows, ren_rows = np.flatnonzero(rm.any(1)), np.flatnonzero(mm.any(1))
        height_diff_mm = None
        if ref_rows.size and ren_rows.size:
            height_diff_mm = round(((ren_rows[-1] - ren_rows[0]) - (ref_rows[-1] - ref_rows[0])) * mpp * 1000, 1)
        report[name] = {
            "iou": round(inter / max(union, 1), 4),
            "ref_only_px": int((rm & ~mm).sum()),
            "render_only_px": int((mm & ~rm).sum()),
            "height_diff_mm": height_diff_mm,
        }
        overlay = np.full(rm.shape + (3,), 40, np.uint8)
        overlay[rm & mm] = (200, 200, 200)
        overlay[rm & ~mm] = (230, 60, 60)
        overlay[mm & ~rm] = (60, 170, 240)
        columns.append((crop, composite(img, bg), Image.fromarray(overlay)))

    h = max(c[0].size[1] for c in columns)
    sheet = Image.new("RGB", (sum(c[0].size[0] for c in columns), h * 3 + 24), (30, 30, 30))
    x = 0
    for col in columns:
        for i, im in enumerate(col):
            sheet.paste(im, (x, i * h))
        x += col[0].size[0]
    summary = " | ".join(f"{n} IoU={r['iou']:.3f} ref_only={r['ref_only_px']} extra={r['render_only_px']}" for n, r in report.items())
    ImageDraw.Draw(sheet).text((5, h * 3 + 6), summary, fill=(255, 255, 255))
    out = args.out or os.path.join(args.render_dir, "compare.png")
    sheet.save(out)
    with open(args.json or os.path.join(args.render_dir, "compare.json"), "w") as f:
        json.dump(report, f, indent=2)
    for n, r in report.items():
        print(f"{n:8s} IoU {r['iou']:.3f}  ref_only {r['ref_only_px']:6d}  extra {r['render_only_px']:6d}  height diff {r['height_diff_mm']} mm")
    print(f"sheet: {out}")


if __name__ == "__main__":
    main()
