"""Shared helpers for the reference-matching scripts (system Python 3 with Pillow and numpy).

A reference spec (ref_spec.json) maps each view of a turnaround sheet to a crop and a camera:

{
  "reference": "character.png",        # path relative to the spec file
  "meters_per_px": 0.004,              # world size of one reference pixel
  "ground_px": 471.0,                  # image row (continuous coords) of the ground line
  "bg_threshold": 30,                  # summed RGB distance from the background colour
  "ignore_below_px": 475,              # optional: rows at or below this are labels, not model
  "views": {
    "front": {"crop": [0, 0, 600, 519], "camera": "front", "center_px": 299.5},
    "right": {"crop": [600, 0, 850, 519], "camera": "right", "center_px": 727.0}
  }
}

camera is one of front | back | right | left (the character faces -Y, its left side is +X).
center_px is the image column that maps to world 0 on that view's horizontal axis.
"""
import json
import os

import numpy as np
from PIL import Image

CAMERAS = ("front", "back", "right", "left")


def load_spec(path):
    with open(path) as f:
        spec = json.load(f)
    base = os.path.dirname(os.path.abspath(path))
    spec["reference"] = os.path.join(base, spec["reference"])
    for key in ("meters_per_px", "ground_px", "views"):
        if spec.get(key) in (None, {}):
            raise SystemExit(f"{path}: '{key}' is not set")
    for name, view in spec["views"].items():
        if view.get("camera") not in CAMERAS:
            raise SystemExit(f"{path}: view '{name}' needs camera in {CAMERAS}")
        if "center_px" not in view or len(view.get("crop", [])) != 4:
            raise SystemExit(f"{path}: view '{name}' needs crop [x0,y0,x1,y1] and center_px")
    spec.setdefault("bg_threshold", 30)
    return spec


def load_reference(spec):
    img = Image.open(spec["reference"]).convert("RGB")
    return img, np.asarray(img).astype(int)


def background_colour(arr):
    """Median colour of the image border."""
    border = np.concatenate([arr[0], arr[-1], arr[:, 0], arr[:, -1]])
    return np.median(border, axis=0)


def reference_mask(spec, arr, view_name):
    """Foreground mask of one view's crop, labels removed."""
    x0, y0, x1, y1 = spec["views"][view_name]["crop"]
    mask = np.abs(arr - background_colour(arr)).sum(2) > spec["bg_threshold"]
    cut = spec.get("ignore_below_px")
    if cut is not None:
        mask[int(cut):, :] = False
    return mask[y0:y1, x0:x1]


def render_image(render_dir, view_name, size):
    """Load a transparent render, resized to the crop size when rendered at another scale."""
    img = Image.open(os.path.join(render_dir, f"{view_name}.png")).convert("RGBA")
    if img.size != size:
        img = img.resize(size, Image.LANCZOS)
    return img


def render_mask(img):
    return np.asarray(img)[..., 3] > 128


def composite(img, colour):
    bg = Image.new("RGBA", img.size, tuple(int(c) for c in colour) + (255,))
    bg.alpha_composite(img)
    return bg.convert("RGB")


def row_extents(mask):
    """Outermost filled column per row, or None for empty rows."""
    out = []
    for row in mask:
        xs = np.flatnonzero(row)
        out.append((int(xs[0]), int(xs[-1]) + 1) if xs.size else None)
    return out
