"""Side-by-side magnified crop of the reference and the render for one region.

  python3 zoom.py ref_spec.json RENDERDIR front 240,20,360,130 --out head_front.png [--zoom 4]

The region is x0,y0,x1,y1 in reference image pixels and must lie inside the view's crop.
Render at --scale 2 or more in render_views.py for sharper detail; the crop is resampled
from whatever resolution the render has.
"""
import argparse
import os
import sys

from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from refspec import background_colour, composite, load_reference, load_spec  # noqa: E402


def main():
    p = argparse.ArgumentParser()
    p.add_argument("spec")
    p.add_argument("render_dir")
    p.add_argument("view")
    p.add_argument("region")
    p.add_argument("--out", required=True)
    p.add_argument("--zoom", type=int, default=4)
    args = p.parse_args()
    spec = load_spec(args.spec)
    ref, arr = load_reference(spec)
    cx0, cy0, cx1, cy1 = spec["views"][args.view]["crop"]
    x0, y0, x1, y1 = (int(v) for v in args.region.split(","))
    if not (cx0 <= x0 < x1 <= cx1 and cy0 <= y0 < y1 <= cy1):
        raise SystemExit(f"region {args.region} is outside the {args.view} crop {[cx0, cy0, cx1, cy1]}")
    ren = composite(Image.open(os.path.join(args.render_dir, f"{args.view}.png")).convert("RGBA"), background_colour(arr))
    sx, sy = ren.size[0] / (cx1 - cx0), ren.size[1] / (cy1 - cy0)
    a = ref.crop((x0, y0, x1, y1))
    b = ren.crop((round((x0 - cx0) * sx), round((y0 - cy0) * sy), round((x1 - cx0) * sx), round((y1 - cy0) * sy)))
    w, h = (x1 - x0) * args.zoom, (y1 - y0) * args.zoom
    out = Image.new("RGB", (w * 2 + 10, h), (20, 20, 20))
    out.paste(a.resize((w, h), Image.LANCZOS), (0, 0))
    out.paste(b.resize((w, h), Image.LANCZOS), (w + 10, 0))
    out.save(args.out)
    print(f"reference | render -> {args.out}")


if __name__ == "__main__":
    main()
