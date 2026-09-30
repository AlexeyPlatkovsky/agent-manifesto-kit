"""Row-by-row silhouette edge differences for one view, in millimetres.

  python3 edges.py ref_spec.json RENDERDIR front [--step 6] [--tol-mm 8]

For each sampled row: height above ground, how far the render's left and right edges sit
outside (+) or inside (-) the reference's, and the width difference. Rows beyond --tol-mm are
flagged with '!'. Use it to turn the red/blue overlay into concrete geometry corrections.
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from refspec import load_reference, load_spec, reference_mask, render_image, render_mask, row_extents  # noqa: E402


def main():
    p = argparse.ArgumentParser()
    p.add_argument("spec")
    p.add_argument("render_dir")
    p.add_argument("view")
    p.add_argument("--step", type=int, default=6)
    p.add_argument("--tol-mm", type=float, default=8.0)
    args = p.parse_args()
    spec = load_spec(args.spec)
    _, arr = load_reference(spec)
    view = spec["views"][args.view]
    x0, y0, x1, y1 = view["crop"]
    mm_per_px = spec["meters_per_px"] * 1000
    ref = row_extents(reference_mask(spec, arr, args.view))
    ren = row_extents(render_mask(render_image(args.render_dir, args.view, (x1 - x0, y1 - y0))))

    print(f"{args.view}: + means the render extends beyond the reference")
    print("  row      z   left_mm  right_mm  width_mm")
    flagged = 0
    for r in range(0, len(ref), args.step):
        a, b = ref[r], ren[r]
        z = (spec["ground_px"] - (r + y0 + 0.5)) * spec["meters_per_px"]
        if a is None and b is None:
            continue
        if a is None or b is None:
            print(f"! {r + y0:4d} {z:6.3f}  {'render only' if a is None else 'reference only'}")
            flagged += 1
            continue
        left = (a[0] - b[0]) * mm_per_px
        right = (b[1] - a[1]) * mm_per_px
        mark = "!" if max(abs(left), abs(right)) > args.tol_mm else " "
        flagged += mark == "!"
        print(f"{mark} {r + y0:4d} {z:6.3f} {left:+8.1f} {right:+9.1f} {left + right:+9.1f}")
    print(f"{flagged} row(s) beyond {args.tol_mm} mm")


if __name__ == "__main__":
    main()
