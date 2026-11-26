"""Crop concept views by reference/boxes.json -> reference/crops/<name>.png"""
import json, sys, pathlib
from PIL import Image
root = pathlib.Path(__file__).resolve().parent.parent
img = Image.open(root / "reference/concept.png").convert("RGB")
(root / "reference/crops").mkdir(parents=True, exist_ok=True)
for name, box in json.loads((root / "reference/boxes.json").read_text()).items():
    img.crop(tuple(box)).save(root / f"reference/crops/{name}.png")
    print(name, box)
