"""Contact sheet: concept | three.js | blender | glb_in_three for given views -> path"""
import sys, pathlib
from PIL import Image
ROOT = pathlib.Path(__file__).resolve().parent.parent
out, views = sys.argv[1], sys.argv[2].split(",")
pipes = sys.argv[3].split(",") if len(sys.argv) > 3 else ["threejs", "blender", "glb_in_three"]
H = 1100
rows = []
for v in views:
    c = Image.open(ROOT / f"reference/crops/{v}.png"); c = c.resize((round(c.width * H / c.height), H))
    ims = [c] + [Image.open(ROOT / f"out/{p}/{v}.png") for p in pipes]
    W = sum(i.width for i in ims) + 10 * (len(ims) - 1)
    r = Image.new("RGB", (W, H), "black"); x = 0
    for i in ims: r.paste(i, (x, 0)); x += i.width + 10
    rows.append(r)
W = max(r.width for r in rows); s = Image.new("RGB", (W, H * len(rows) + 10 * (len(rows) - 1)), "black")
for k, r in enumerate(rows): s.paste(r, (0, k * (H + 10)))
scale = float(sys.argv[4]) if len(sys.argv) > 4 else 0.5
s.resize((int(s.width * scale), int(s.height * scale))).save(out)
