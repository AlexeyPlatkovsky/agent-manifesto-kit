"""Measure a concept view to draft spec/object.json (geometry is measured, not eyeballed).

Usage: python3 tools/measure_silhouette.py <view> --height <m> [--rows 24] [--dark 80] [--bright 215]
  <view>: front|back|left|right|3q (reference/crops/<view>.png)
Prints: silhouette bbox, metres per pixel, the width profile (row by row, metres from the ground),
and the largest dark / bright components (openings, panels, glowing windows, buttons) in metres:
height range from the ground and x range from the silhouette centre. Read them, then LOOK at the crop
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
print(f"bbox y {y0}-{y1} x {x0}-{x1}; {mpp * 1000:.2f} mm/px; width {(x1 - x0) * mpp:.3f} m; aspect {(x1 - x0) / (y1 - y0):.3f}")
print("width profile (height from ground m: width m, x-range from centre):")
for y in np.linspace(y0, y1 - 1, a.rows).astype(int):
    r = np.where(m[y])[0]
    if len(r):
        print(f"  {(y1 - y) * mpp:6.3f}: {(r.max() - r.min()) * mpp:.3f}  [{(r.min() - cx) * mpp:+.3f}, {(r.max() - cx) * mpp:+.3f}]")
L = img.mean(2)
for name, mask in (("dark", (L < a.dark) & m), ("bright", (img[..., 1] > a.bright) & (img[..., 2] > a.bright) & m)):
    lab, n = ndi.label(ndi.binary_closing(mask, iterations=2))
    comps = sorted([sl for sl in ndi.find_objects(lab) if (sl[0].stop - sl[0].start) * (sl[1].stop - sl[1].start) > 40],
                   key=lambda s: -(s[0].stop - s[0].start) * (s[1].stop - s[1].start))[:8]
    print(f"{name} components (largest first):")
    for s in comps:
        print(f"  y {(y1 - s[0].stop) * mpp:.3f}-{(y1 - s[0].start) * mpp:.3f} m   x {(s[1].start - cx) * mpp:+.3f}..{(s[1].stop - cx) * mpp:+.3f} m")
