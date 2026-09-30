"""Measure a turnaround reference and draft or inspect its ref_spec.json.

Draft a spec (views are found as column groups separated by background):
  python3 measure_ref.py character.png --height-m 1.80 --out ref_spec.json

Print a view's silhouette profile in metres, for building geometry from measurements:
  python3 measure_ref.py --spec ref_spec.json --profile front [--step 6]

Drafted view names and cameras are guesses (widest group = front; the others are named right,
left, back in left-to-right order):
check them against the sheet's labels, and adjust center_px for side views if the model's
origin is not the silhouette centre.
"""
import argparse
import json
import os
import sys

import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from refspec import background_colour, load_reference, load_spec, reference_mask, row_extents  # noqa: E402


def runs(flags, min_gap):
    """[start, end) runs of True, bridging gaps shorter than min_gap."""
    idx = np.flatnonzero(flags)
    if idx.size == 0:
        return []
    out, start, prev = [], idx[0], idx[0]
    for i in idx[1:]:
        if i - prev > min_gap:
            out.append((int(start), int(prev) + 1))
            start = i
        prev = i
    out.append((int(start), int(prev) + 1))
    return out


def draft(args):
    arr = np.asarray(Image.open(args.reference).convert("RGB")).astype(int)
    bg = background_colour(arr)
    mask = np.abs(arr - bg).sum(2) > args.bg_threshold
    groups = [g for g in runs(mask.any(0), args.min_gap) if g[1] - g[0] >= args.min_width]
    if not groups:
        raise SystemExit("no foreground found; lower --bg-threshold")
    found = []
    for x0, x1 in groups:
        rows = runs(mask[:, x0:x1].any(1), 3)
        y0, y1 = max(rows, key=lambda r: r[1] - r[0])  # tallest run = the figure, not its label
        found.append({"x0": x0, "x1": x1, "y0": y0, "y1": y1})
    ground = int(np.median([f["y1"] for f in found]))  # soft shadows can extend single views
    widest = max(found, key=lambda f: f["x1"] - f["x0"])
    top = widest["y0"]
    label_rows = [r for x0, x1 in groups for r in runs(mask[:, x0:x1].any(1), 3) if r[0] >= ground]
    ignore_below = min((r[0] for r in label_rows), default=None)

    order = sorted(range(len(found)), key=lambda i: found[i]["x1"] - found[i]["x0"], reverse=True)
    guesses = ["front", "right", "left", "back"]
    views = {}
    for rank, i in enumerate(sorted(order[:1]) + sorted(order[1:])):
        f = found[i]
        name = guesses[rank] if rank < len(guesses) else f"view{rank + 1}"
        views[name] = {
            "crop": [f["x0"] - args.pad if f["x0"] >= args.pad else 0, 0,
                     min(f["x1"] + args.pad, arr.shape[1]), arr.shape[0] if ignore_below is None else int(ignore_below)],
            "camera": name if name in guesses else "",
            "center_px": round((f["x0"] + f["x1"]) / 2, 1),
            "silhouette_px": [f["x0"], f["y0"], f["x1"], f["y1"]],
        }
    height_px = ground - top
    spec = {
        "reference": os.path.relpath(args.reference, os.path.dirname(os.path.abspath(args.out or "."))),
        "meters_per_px": round(args.height_m / height_px, 6) if args.height_m else None,
        "ground_px": float(ground),
        "bg_threshold": args.bg_threshold,
        "views": views,
    }
    if ignore_below is not None:
        spec["ignore_below_px"] = int(ignore_below)
    print(f"background RGB {bg.astype(int).tolist()}, front figure height {height_px} px, ground row {ground}")
    for name, v in views.items():
        print(f"  {name:6s} silhouette {v['silhouette_px']}  center_px {v['center_px']}")
    if not args.height_m:
        print("meters_per_px left empty: pass --height-m with the intended character height")
    text = json.dumps(spec, indent=2) + "\n"
    if args.out:
        with open(args.out, "w") as f:
            f.write(text)
        print(f"wrote {args.out}; verify view names and cameras before use")
    else:
        print(text)


def profile(args):
    spec = load_spec(args.spec)
    _, arr = load_reference(spec)
    view = spec["views"][args.profile]
    x0, y0 = view["crop"][:2]
    mpp, ground, c = spec["meters_per_px"], spec["ground_px"], view["center_px"]
    ext = row_extents(reference_mask(spec, arr, args.profile))
    print(f"{args.profile}: z = height above ground; left/right = world offset of silhouette edges (m)")
    print("  row      z     left    right   width")
    for r in range(0, len(ext), args.step):
        if ext[r] is None:
            continue
        a, b = ext[r][0] + x0, ext[r][1] + x0
        z = (ground - (r + y0 + 0.5)) * mpp
        print(f"  {r + y0:4d} {z:6.3f} {(a - c) * mpp:+7.3f} {(b - c) * mpp:+7.3f} {(b - a) * mpp:6.3f}")


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("reference", nargs="?")
    p.add_argument("--height-m", type=float, help="intended character height in metres")
    p.add_argument("--out", help="write the drafted spec here")
    p.add_argument("--bg-threshold", type=int, default=30)
    p.add_argument("--min-gap", type=int, default=20, help="background columns that separate views")
    p.add_argument("--min-width", type=int, default=20, help="ignore narrower column groups")
    p.add_argument("--pad", type=int, default=10, help="crop padding around each silhouette")
    p.add_argument("--spec", help="existing spec, for --profile")
    p.add_argument("--profile", help="view name to print row extents for")
    p.add_argument("--step", type=int, default=6)
    args = p.parse_args()
    if args.profile:
        if not args.spec:
            p.error("--profile needs --spec")
        profile(args)
    elif args.reference:
        draft(args)
    else:
        p.error("pass a reference image, or --spec with --profile")


if __name__ == "__main__":
    main()
