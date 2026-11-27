"""Overlay the wear masks of tools/wear_stats.py on images: chips magenta, rust orange, grime green, excluded areas dimmed.
Usage: python3 tools/overlay_masks.py <out.png> [image_dir] [views]   (default reference/crops, 3q,front,back,left)"""
import sys, pathlib
import numpy as np
from PIL import Image
HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import metrics as M
src_code = (HERE / "wear_stats.py").read_text().split("\nres = {}")[0]
src_code = src_code.replace('src = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "reference/crops"', 'src = None')
ns = {"__file__": str(HERE / "wear_stats.py")}
exec(compile(src_code, "wear_stats", "exec"), ns)
out = sys.argv[1]
d = pathlib.Path(sys.argv[2]) if len(sys.argv) > 2 else M.ROOT / "reference/crops"
views = sys.argv[3].split(",") if len(sys.argv) > 3 else ["3q", "front", "back", "left"]
tiles = []
for v in views:
    img = ns["normalise"](M.load(d / f"{v}.png")); sil = M.mask_of(img); y0, y1, x0, x1 = M.bbox(sil)
    ns["VIEW"] = v; chip, rust, grime, keep = ns["masks"](img, ns["H"] / (y1 - y0), sil)
    vis = img.copy(); vis[chip] = [255, 0, 200]; vis[rust] = [255, 140, 0]; vis[grime] = [0, 200, 0]
    vis[~keep & sil] = vis[~keep & sil] * 0.4
    tiles.append(Image.fromarray(np.concatenate([img, vis], 1).clip(0, 255).astype(np.uint8)))
W = sum(t.width for t in tiles) + 10 * (len(tiles) - 1); s = Image.new("RGB", (W, max(t.height for t in tiles)), "black"); x = 0
for t in tiles: s.paste(t, (x, 0)); x += t.width + 10
s.save(out); print(out, s.size)
