"""Compare renders with concept crops: silhouette IoU and zone colour (CIELAB). Wear is measured by wear_stats.py.

Usage: python3 tools/metrics.py [pipeline ...]   (default: threejs blender glb_in_three)
For each view: silhouette mask (distance from background colour), bbox-normalised IoU,
width profile error, and colour stats per zone (cap / body / base) in CIELAB.
Writes out/metrics.json and prints a table.
"""
import json, sys, pathlib
import numpy as np
from PIL import Image

ROOT = pathlib.Path(__file__).resolve().parent.parent
VIEWS = ["3q", "front", "back", "left", "right"]
N = 256  # normalised mask size


def load(p):
    return np.asarray(Image.open(p).convert("RGB")).astype(np.float32)


def mask_of(img):
    bg = np.median(np.concatenate([img[:6].reshape(-1, 3), img[:, :6].reshape(-1, 3), img[:, -6:].reshape(-1, 3)]), axis=0)
    d = np.abs(img - bg).sum(2)
    m = d > 45
    # ground shadow = background scaled by a near-constant factor (neutral darkening): not part of the object
    ratio = img / np.maximum(bg, 1)
    spread = ratio.max(2) - ratio.min(2)
    shadow = (spread < 0.03) & (ratio.mean(2) > 0.6) & (ratio.mean(2) < 0.97)
    m &= ~shadow
    # remove isolated leftovers: keep columns/rows with enough support
    # drop the soft ground shadow: low-saturation, darker-than-bg pixels in the bottom rows outside the core
    return m


def bbox(m):
    ys, xs = np.where(m)
    # robust bbox: ignore tiny stray pixels
    rows = np.where(m.sum(1) > 3)[0]
    cols = np.where(m.sum(0) > 3)[0]
    return rows.min(), rows.max() + 1, cols.min(), cols.max() + 1


def norm_mask(m, box):
    y0, y1, x0, x1 = box
    h = y1 - y0
    # keep aspect: normalise by height, centre horizontally in an N x N canvas
    crop = Image.fromarray((m[y0:y1, x0:x1] * 255).astype(np.uint8))
    w = max(1, round((x1 - x0) * N / h))
    crop = crop.resize((w, N), Image.BILINEAR)
    canvas = np.zeros((N, N), np.float32)
    off = (N - w) // 2
    a, b = max(0, off), min(N, off + w)
    canvas[:, a:b] = np.asarray(crop, np.float32)[:, a - off:b - off] / 255
    return canvas > 0.5


def srgb_to_lab(rgb):
    c = rgb / 255.0
    c = np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)
    M = np.array([[0.4124, 0.3576, 0.1805], [0.2126, 0.7152, 0.0722], [0.0193, 0.1192, 0.9505]])
    xyz = c @ M.T / np.array([0.95047, 1.0, 1.08883])
    f = np.where(xyz > 0.008856, np.cbrt(xyz), 7.787 * xyz + 16 / 116)
    return np.stack([116 * f[..., 1] - 16, 500 * (f[..., 0] - f[..., 1]), 200 * (f[..., 1] - f[..., 2])], -1)


# zones as fractions of the silhouette height (from top), measured on the concept front view
ZONES = {"cap": (0.02, 0.15), "body": (0.22, 0.78), "base": (0.88, 0.98)}


def zone_stats(img, m, box):
    y0, y1, x0, x1 = box
    h = y1 - y0
    out = {}
    for z, (a, b) in ZONES.items():
        ya, yb = y0 + int(a * h), y0 + int(b * h)
        # central 60% of the width at those rows to avoid edges/background
        xs = np.where(m[ya:yb].any(0))[0]
        cx0, cx1 = xs.min(), xs.max()
        pad = int((cx1 - cx0) * 0.2)
        reg = img[ya:yb, cx0 + pad:cx1 - pad]
        mm = m[ya:yb, cx0 + pad:cx1 - pad]
        px = reg[mm]
        lab = srgb_to_lab(px)
        out[z] = {
            "rgb_median": np.median(px, 0).round().astype(int).tolist(),
            "lab_median": np.median(lab, 0).round(1).tolist(),
            "L_p10_p90": np.percentile(lab[:, 0], [10, 90]).round(1).tolist(),
            "chroma_median": float(np.median(np.hypot(lab[:, 1], lab[:, 2])).round(1)),
            # exposed cream undercoat (chips) and dark rust streaks, as share of zone pixels
            "chip_share": float(((lab[:, 0] > 62) & (np.hypot(lab[:, 1], lab[:, 2]) < 32)).mean().round(3)),
            "rust_share": float(((lab[:, 0] < 40) & (lab[:, 2] > 18)).mean().round(3)),
        }
    return out


def width_profile(nm):
    w = nm.sum(1).astype(np.float32) / N
    return w


def compare(view, pipe):
    c_img = load(ROOT / f"reference/crops/{view}.png")
    r_path = ROOT / f"out/{pipe}/{view}.png"
    if not r_path.exists():
        return None
    r_img = load(r_path)
    cm, rm = mask_of(c_img), mask_of(r_img)
    cb, rb = bbox(cm), bbox(rm)
    cn, rn = norm_mask(cm, cb), norm_mask(rm, rb)
    iou = float((cn & rn).sum() / max(1, (cn | rn).sum()))
    prof_err = float(np.abs(width_profile(cn) - width_profile(rn)).mean())
    aspect_c = (cb[3] - cb[2]) / (cb[1] - cb[0])
    aspect_r = (rb[3] - rb[2]) / (rb[1] - rb[0])
    cz, rz = zone_stats(c_img, cm, cb), zone_stats(r_img, rm, rb)
    de = {z: float(np.linalg.norm(np.array(cz[z]["lab_median"]) - np.array(rz[z]["lab_median"])).round(1)) for z in ZONES}
    return {"iou": round(iou, 3), "profile_err": round(prof_err, 3), "aspect": [round(aspect_c, 3), round(aspect_r, 3)],
            "deltaE_median": de, "concept": cz, "render": rz}


def main():
    pipes = sys.argv[1:] or ["threejs", "blender", "glb_in_three", "godot"]
    res = {}
    for p in pipes:
        res[p] = {}
        for v in VIEWS:
            r = compare(v, p)
            if r:
                res[p][v] = r
    path = ROOT / "out/metrics.json"
    old = json.loads(path.read_text()) if path.exists() else {}
    old.update(res)
    path.write_text(json.dumps(old, indent=1))
    for p, vs in res.items():
        print(f"\n[{p}]  view   IoU   prof  aspect(c/r)    dE top/middle/bottom   L p10-p90 middle (c | r)   chroma middle (c|r)")
        for v, r in vs.items():
            d = r["deltaE_median"]
            print(f"  {v:6s} {r['iou']:.3f} {r['profile_err']:.3f}  {r['aspect'][0]:.2f}/{r['aspect'][1]:.2f}   "
                  f"{d['cap']:5.1f}/{d['body']:5.1f}/{d['base']:5.1f}    {r['concept']['body']['L_p10_p90']} | {r['render']['body']['L_p10_p90']}"
                  f"   {r['concept']['body']['chroma_median']}|{r['render']['body']['chroma_median']}")
    print("\n(zones: top 2-15%, middle 22-78%, bottom 88-98% of the silhouette height; for wear use tools/wear_stats.py)")


if __name__ == "__main__":
    main()
