"""Zone brightness/chroma of one pipeline vs another (default: godot vs blender).
Usage: python3 tools/compare_to.py [pipe] [ref] [views]"""
import sys, pathlib
import numpy as np
sys.path.insert(0, str(pathlib.Path(__file__).parent))
import metrics as M
pipe = sys.argv[1] if len(sys.argv) > 1 else "godot"
ref = sys.argv[2] if len(sys.argv) > 2 else "blender"
views = sys.argv[3].split(",") if len(sys.argv) > 3 else M.VIEWS
acc = {}
for v in views:
    out = {}
    for p in (pipe, ref):
        img = M.load(M.ROOT / f"out/{p}/{v}.png"); m = M.mask_of(img); b = M.bbox(m)
        zs = M.zone_stats(img, m, b)
        out[p] = zs
    for z in M.ZONES:
        a, r = out[pipe][z], out[ref][z]
        d = [a["L_p10_p90"][0] - r["L_p10_p90"][0], a["lab_median"][0] - r["lab_median"][0],
             a["L_p10_p90"][1] - r["L_p10_p90"][1], a["chroma_median"] - r["chroma_median"]]
        acc.setdefault(z, []).append(d)
print(f"mean {pipe}-{ref} (Lp10 Lp50 Lp90 chroma):")
for z, ds in acc.items():
    print(f"  {z:5s}", " ".join(f"{x:+6.1f}" for x in np.mean(ds, 0)))
