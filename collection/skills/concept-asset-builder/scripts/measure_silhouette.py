"""Measure a concept view to draft spec/object.json (geometry is measured, not eyeballed).

Usage: python3 tools/measure_silhouette.py <view> --height <m> [--rows 24] [--dark 80] [--bright 215]
  <view>: front|back|left|right|3q (reference/crops/<view>.png)
Prints: silhouette bbox, metres per pixel, the width profile (row by row, metres from the ground),
and the largest dark / bright components (openings, panels, glowing windows, buttons) in metres:
height range from the ground and the horizontal range in OBJECT coordinates (spec convention: front +Z, +X to the
object's right as seen from the front): front -> x as in the image; back -> x mirrored (the image's left is +x);
left view (camera at -X, front on the image's right) -> z = image offset; right view -> z mirrored; 3q -> image
offset only (not an object axis). Writing back/side positions in image coordinates was a real bug (a mirrored
back façade). Read them, then LOOK at the crop
and decide what each component is. Watch out: a contact shadow under the object belongs to the silhouette
(subtract it from heights), and the top surface seen from the camera adds a little to the height.
"""
import argparse, pathlib, sys
import numpy as np
from PIL import Image
from scipy import ndimage as ndi
sys.path.insert(0, str(pathlib.Path(__file__).parent))
import metrics as M

ap = argparse.ArgumentParser()
ap.add_argument("view"); ap.add_argument("--height", type=float, required=True)
ap.add_argument("--rows", type=int, default=24); ap.add_argument("--dark", type=float, default=80)
ap.add_argument("--bright", type=float, default=215)
a = ap.parse_args()
img = M.load(M.ROOT / f"reference/crops/{a.view}.png")
m = M.mask_of(img)
y0, y1, x0, x1 = M.bbox(m)
mpp = a.height / (y1 - y0); cx = (x0 + x1) / 2
AXIS, SIGN = {"front": ("x", 1), "back": ("x", -1), "left": ("z", 1), "right": ("z", -1)}.get(a.view, ("image x", 1))


def span(p0, p1):
    """image pixel range -> sorted object-axis range in metres"""
    u0, u1 = SIGN * (p0 - cx) * mpp, SIGN * (p1 - cx) * mpp
    return min(u0, u1), max(u0, u1)
print(f"bbox y {y0}-{y1} x {x0}-{x1}; {mpp * 1000:.2f} mm/px; width {(x1 - x0) * mpp:.3f} m; aspect {(x1 - x0) / (y1 - y0):.3f}")
print(f"view {a.view}: horizontal positions are {AXIS} in object coordinates" + ("" if AXIS != "image x" else " (3/4 view: image offset, not an object axis)"))
print("width profile (height from ground m: width m, range):")
for y in np.linspace(y0, y1 - 1, a.rows).astype(int):
    r = np.where(m[y])[0]
    if len(r):
        lo, hi = span(r.min(), r.max())
        print(f"  {(y1 - y) * mpp:6.3f}: {(r.max() - r.min()) * mpp:.3f}  {AXIS} [{lo:+.3f}, {hi:+.3f}]")
L = img.mean(2)
for name, mask in (("dark", (L < a.dark) & m), ("bright", (img[..., 1] > a.bright) & (img[..., 2] > a.bright) & m)):
    lab, n = ndi.label(ndi.binary_closing(mask, iterations=2))
    comps = sorted([sl for sl in ndi.find_objects(lab) if (sl[0].stop - sl[0].start) * (sl[1].stop - sl[1].start) > 40],
                   key=lambda s: -(s[0].stop - s[0].start) * (s[1].stop - s[1].start))[:8]
    print(f"{name} components (largest first):")
    for s in comps:
        lo, hi = span(s[1].start, s[1].stop)
        print(f"  y {(y1 - s[0].stop) * mpp:.3f}-{(y1 - s[0].start) * mpp:.3f} m   {AXIS} {lo:+.3f}..{hi:+.3f} m")
