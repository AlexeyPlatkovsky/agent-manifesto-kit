"""Generic wear measurement (v2) for an object concept vs renders.

Usage: python3 tools/wear_stats.py [image_dir]   (default reference/crops) -> table + out/wear_stats_<dir>.json
Config: reference/zones.json
  height_m: real height of the silhouette
  bands: {name: [y0_m, y1_m]}            horizontal bands over the whole silhouette (every view)
  front_rects: {name: [x0, x1, y0, y1]}  metres, x from the silhouette centre; front view only
  chip: {dL, min_L, max_C, window_m}     chip = lighter than the local paint by dL, L > min_L, chroma < max_C
        or {mode: "hue", paint_hue: [h0, h1], neutral_C, min_L, max_C}   for light paint: chip = not the paint hue
  rust: {mode: "dark"|"hue", hue: [h0, h1], min_C, dL}  hue mode: orange-brown hue range (for non-red paint)
  grime: {hue: [h0, h1], min_C, max_L}   olive grime
  exclude_emissive: true                 drop the glowing window (and what is inside it) from all measurements
All images are resampled so the silhouette is 527 px tall; windows are in metres; vertical components longer
than 0.2 m are dropped from rust (edges/grooves, not drips).
"""
import json, sys, pathlib
import numpy as np
from PIL import Image
from scipy import ndimage as ndi
sys.path.insert(0, str(pathlib.Path(__file__).parent))
import metrics as M

ROOT = M.ROOT
Z = json.loads((ROOT / "reference/zones.json").read_text())
H = Z["height_m"]
src = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "reference/crops"
TARGET = 527


def normalise(img):
    m = M.mask_of(img); y0, y1, x0, x1 = M.bbox(m); k = TARGET / (y1 - y0)
    if abs(k - 1) < 0.02:
        return img
    im = Image.fromarray(img.clip(0, 255).astype(np.uint8)).resize((round(img.shape[1] * k), round(img.shape[0] * k)), Image.LANCZOS)
    return np.asarray(im).astype(np.float32)


def masks(img, mpp, sil):
    lab = M.srgb_to_lab(img); L, a, b = lab[..., 0], lab[..., 1], lab[..., 2]
    C = np.hypot(a, b); hue = np.degrees(np.arctan2(b, a)) % 360
    win = max(5, int(round(0.033 / mpp)) | 1)
    Lloc = ndi.median_filter(L, size=win)
    ch = Z.get("chip", {}); dL, minL, maxC = ch.get("dL", 10), ch.get("min_L", 55), ch.get("max_C", 38)
    # chips can be larger than the rust window: compare with a wider (8 cm) paint neighbourhood
    Lchip = ndi.median_filter(L, size=max(7, int(round(ch.get("window_m", 0.08) / mpp)) | 1))
    chip = (L > np.minimum(Lloc, Lchip) + dL) & (L > minL) & (C < maxC)
    if ch.get("mode") == "hue":
        # light paint: chips are not much lighter, they differ by hue (warm/neutral primer vs the paint hue)
        ph0, ph1 = ch["paint_hue"]
        not_paint = ~((hue >= ph0) & (hue <= ph1)) | (C < ch.get("neutral_C", 4))
        chip = not_paint & (C < maxC) & (L > minL) & (L > np.minimum(Lloc, Lchip) - 3)
    r = Z.get("rust", {"mode": "dark"})
    if r.get("mode") == "hue":
        h0, h1 = r.get("hue", [30, 85])
        rust = (hue >= h0) & (hue <= h1) & (C > r.get("min_C", 15)) & (L < Lloc - r.get("dL", 2)) & (L < 72)
    else:
        rust = (L < Lloc - 6) & (L < 50) & (C > 20)
    g = Z.get("grime")
    grime = ((hue >= g["hue"][0]) & (hue <= g["hue"][1]) & (C > g.get("min_C", 10)) & (L < g.get("max_L", 65))) if g else np.zeros_like(rust)
    keep = sil.copy()
    if Z.get("exclude_emissive"):
        glow = (L > 93) & (C < 25) & sil  # the display glows at L 95-99; lit light paint stays below ~90
        glow = ndi.binary_closing(glow, iterations=3)
        lab_, n = ndi.label(glow)
        if n:
            sizes = ndi.sum(glow, lab_, range(1, n + 1))
            big = np.isin(lab_, 1 + np.where(sizes > 0.01 * sil.sum())[0])
            win_m = ndi.binary_fill_holes(ndi.binary_dilation(big, iterations=4))
            # fill also the box spanned by the glow (bottles split it into bands)
            if win_m.any():
                ys, xs = np.where(win_m); win_m[ys.min():ys.max() + 1, xs.min():xs.max() + 1] = True
            keep &= ~win_m
    lab_, n = ndi.label(rust)
    for i, sl in enumerate(ndi.find_objects(lab_), 1):
        if sl is not None and (sl[0].stop - sl[0].start) * mpp > 0.20:
            rust[sl][lab_[sl] == i] = False
    return chip & keep, rust & keep, grime & keep, keep


def summarise(mask, area, mpp):
    lab_, n = ndi.label(mask); out = []
    for sl in ndi.find_objects(lab_):
        h = (sl[0].stop - sl[0].start) * mpp * 100; w = (sl[1].stop - sl[1].start) * mpp * 100
        if max(h, w) >= 0.6:
            out.append((h, w))
    if not out:
        return {"count": 0}
    s = np.array([max(h, w) for h, w in out])
    return {"count": int(len(s)), "size_cm_p10_p50_p90_max": [round(float(np.percentile(s, q)), 1) for q in (10, 50, 90)] + [round(float(s.max()), 1)],
            "small_lt2cm": int((s < 2).sum()), "medium_2_5cm": int(((s >= 2) & (s < 5)).sum()), "large_ge5cm": int((s >= 5).sum())}


def measure(region, chip, rust, grime, mpp):
    area = region.sum()
    if area < 50:
        return None
    return {"chip_pct": round(100 * (chip & region).sum() / area, 1), "rust_pct": round(100 * (rust & region).sum() / area, 1),
            "grime_pct": round(100 * (grime & region).sum() / area, 1),
            "chips": summarise(chip & region, area, mpp), "drips": summarise(rust & region, area, mpp)}


res = {}
for v in M.VIEWS:
    p = src / f"{v}.png"
    if not p.exists():
        continue
    img = normalise(M.load(p)); sil = M.mask_of(img); y0, y1, x0, x1 = M.bbox(sil); mpp = H / (y1 - y0)
    sil = ndi.binary_erosion(sil, iterations=3)
    chip, rust, grime, keep = masks(img, mpp, sil)
    rv = {}
    for z, (a, b) in Z["bands"].items():
        reg = np.zeros_like(sil); reg[max(int(y1 - b / mpp), 0):int(y1 - a / mpp)] = True
        r = measure(reg & keep, chip, rust, grime, mpp)
        if r: rv[z] = r
    if v == "front":
        cx = (x0 + x1) / 2
        for z, (xa, xb, a, b) in Z.get("front_rects", {}).items():
            reg = np.zeros_like(sil); reg[int(y1 - b / mpp):int(y1 - a / mpp), int(cx + xa / mpp):int(cx + xb / mpp)] = True
            r = measure(reg & keep, chip, rust, grime, mpp)
            if r: rv[z] = r
    res[v] = rv
name = "concept" if src == ROOT / "reference/crops" else src.name
(ROOT / "out").mkdir(exist_ok=True)
(ROOT / f"out/wear_stats_{name}.json").write_text(json.dumps(res, indent=1))
for v, rv in res.items():
    print(f"\n[{v}] zone           chip%  rust%  grime%  chips n (S/M/L) size p10/p50/p90/max cm      rust comps n")
    for z, r in rv.items():
        c, d = r["chips"], r["drips"]
        cs = f"{c['count']:3d} ({c['small_lt2cm']}/{c['medium_2_5cm']}/{c['large_ge5cm']}) {c['size_cm_p10_p50_p90_max']}" if c["count"] else "  0"
        print(f"  {z:14s} {r['chip_pct']:5.1f}  {r['rust_pct']:5.1f}  {r['grime_pct']:5.1f}   {cs:42s} {d['count']}")
