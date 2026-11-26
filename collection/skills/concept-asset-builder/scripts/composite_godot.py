"""Composite Godot RGBA captures (out/godot/raw) onto the spec background -> out/godot/<view>.png"""
import json, pathlib
import numpy as np
from PIL import Image
ROOT = pathlib.Path(__file__).resolve().parent.parent
bg = json.loads((ROOT / "spec/object.json").read_text())["palette"]["background"].lstrip("#")
bgc = np.array([int(bg[i:i + 2], 16) for i in (0, 2, 4)], np.float32)
for p in sorted((ROOT / "out/godot/raw").glob("*.png")):
    a = np.asarray(Image.open(p).convert("RGBA")).astype(np.float32)
    al = a[..., 3:4] / 255
    rgb = a[..., :3] * al + bgc * (1 - al)
    Image.fromarray(rgb.round().astype(np.uint8)).save(ROOT / "out/godot" / p.name)
    print("composited", p.name, "alpha range", float(al.min()), float(al.max()))
