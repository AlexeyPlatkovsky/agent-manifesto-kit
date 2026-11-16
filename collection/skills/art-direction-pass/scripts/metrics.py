#!/usr/bin/env python3
"""Luminance and saturation statistics plus a 6-color palette per image.

metrics.py IMG [IMG...] -o metrics.json

Deterministic (fixed k-means seed). Requires Pillow and numpy.
"""
import argparse
import json

import numpy as np
from PIL import Image

LUMA = np.array([0.2126, 0.7152, 0.0722])


def stats(path, k=6, iters=12):
    im = Image.open(path).convert("RGB")
    im.thumbnail((256, 256))
    px = np.asarray(im, dtype=np.float32).reshape(-1, 3) / 255.0
    lum = px @ LUMA
    mx, mn = px.max(1), px.min(1)
    sat = np.where(mx > 0, (mx - mn) / np.maximum(mx, 1e-6), 0)
    k = min(k, len(px))
    rng = np.random.default_rng(0)
    centers = px[rng.choice(len(px), k, replace=False)]
    for _ in range(iters):
        labels = ((px[:, None] - centers[None]) ** 2).sum(-1).argmin(1)
        centers = np.array([px[labels == i].mean(0) if (labels == i).any() else centers[i] for i in range(k)])
    labels = ((px[:, None] - centers[None]) ** 2).sum(-1).argmin(1)
    share = np.bincount(labels, minlength=k) / len(px)
    order = share.argsort()[::-1]
    return {
        "lum_p5_p50_p95": [round(float(v), 3) for v in np.percentile(lum, [5, 50, 95])],
        "sat_mean": round(float(sat.mean()), 3),
        "palette": [
            {"hex": "#%02x%02x%02x" % tuple(np.clip(np.rint(centers[i] * 255), 0, 255).astype(int)),
             "share": round(float(share[i]), 3)}
            for i in order
        ],
    }


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("images", nargs="+")
    ap.add_argument("-o", required=True)
    a = ap.parse_args(argv)
    with open(a.o, "w") as f:
        json.dump({p: stats(p) for p in a.images}, f, indent=2)
        f.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
