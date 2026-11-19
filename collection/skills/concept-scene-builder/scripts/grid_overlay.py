#!/usr/bin/env python3
"""Project a hex/square grid onto a concept image to read the layout cell by cell.

grid_overlay.py CONCEPT --grid hex --orient pointy --cols 12 --rows 9 \
    --corners "x,y x,y x,y x,y" -o overlay.png
Corners = image pixels of the grid's bounding box: top-left, top-right, bottom-right, bottom-left
(as the board appears in the image). Labels are axial q,r (hex) or col,row (square).
The board is treated as a plane: raised tiles (plateaus) will look shifted, that is expected.

Free-form concepts (no game grid): use --grid square as a MEASUREMENT grid on the ground plane.
Pick 4 ground points that form a rectangle in the world, set --cols/--rows to its size in cells
and --cell-m to the cell size in metres; labels then show the metre coordinates (x,y) of each
cell's centre instead of indices. Corners that are repeated, collinear or out of order are rejected.
Requires Pillow and numpy.
"""
import argparse
import math

import numpy as np
from PIL import Image, ImageDraw, ImageFont


def homography(src, dst):
    rows = []
    for (x, y), (u, v) in zip(src, dst):
        rows.append([-x, -y, -1, 0, 0, 0, u * x, u * y, u])
        rows.append([0, 0, 0, -x, -y, -1, v * x, v * y, v])
    _, _, vt = np.linalg.svd(np.asarray(rows, float))
    h = vt[-1].reshape(3, 3)
    return h / h[2, 2]


def project(h, pts):
    p = np.c_[pts, np.ones(len(pts))] @ h.T
    return p[:, :2] / p[:, 2:3]


def cells(grid, orient, cols, rows, cell_m=None):
    out = []
    for row in range(rows):
        for col in range(cols):
            if grid == "square":
                poly = [(col, row), (col + 1, row), (col + 1, row + 1), (col, row + 1)]
                label = f"{(col + 0.5) * cell_m:g},{(row + 0.5) * cell_m:g}" if cell_m else f"{col},{row}"
            elif orient == "pointy":
                cx, cy = math.sqrt(3) * (col + 0.5 * (row & 1)), 1.5 * row
                poly = [(cx + math.cos(math.radians(60 * i - 30)), cy + math.sin(math.radians(60 * i - 30))) for i in range(6)]
                label = f"{col - (row - (row & 1)) // 2},{row}"
            else:
                cx, cy = 1.5 * col, math.sqrt(3) * (row + 0.5 * (col & 1))
                poly = [(cx + math.cos(math.radians(60 * i)), cy + math.sin(math.radians(60 * i))) for i in range(6)]
                label = f"{col},{row - (col - (col & 1)) // 2}"
            out.append((np.asarray(poly, float), label))
    return out


def parse_corners(text):
    corners = [tuple(map(float, c.split(","))) for c in text.split()]
    if len(corners) != 4:
        raise ValueError('--corners needs four "x,y" points: TL TR BR BL')
    # A usable quad is strictly convex: all turns in one direction and no repeated or collinear points.
    turns = []
    for i in range(4):
        (ax, ay), (bx, by), (cx, cy) = corners[i], corners[(i + 1) % 4], corners[(i + 2) % 4]
        turns.append((bx - ax) * (cy - by) - (by - ay) * (cx - bx))
    if not (all(t > 0 for t in turns) or all(t < 0 for t in turns)):
        raise ValueError("--corners must form a convex quad in order TL TR BR BL (no repeated or collinear points)")
    return corners


def overlay(concept, out, grid="hex", orient="pointy", cols=1, rows=1, corners=None, cell_m=None):
    polys = cells(grid, orient, cols, rows, cell_m)
    allp = np.vstack([p for p, _ in polys])
    x0, y0 = allp.min(0)
    x1, y1 = allp.max(0)
    src = [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
    h = homography(src, corners)
    im = Image.open(concept).convert("RGB")
    draw = ImageDraw.Draw(im)
    try:
        font = ImageFont.load_default(size=max(12, im.width // 110))
    except TypeError:  # Pillow < 10.1
        font = ImageFont.load_default()
    for poly, label in polys:
        pp = [tuple(p) for p in project(h, poly)]
        draw.line(pp + [pp[0]], fill=(255, 0, 255), width=2)
        c = project(h, poly.mean(0, keepdims=True))[0]
        draw.text((c[0], c[1]), label, fill=(255, 255, 0), font=font, anchor="mm", stroke_width=2, stroke_fill=(0, 0, 0))
    im.save(out)
    return h


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("concept")
    ap.add_argument("--grid", choices=["hex", "square"], default="hex")
    ap.add_argument("--orient", choices=["pointy", "flat"], default="pointy")
    ap.add_argument("--cols", type=int, required=True)
    ap.add_argument("--rows", type=int, required=True)
    ap.add_argument("--corners", required=True, help='"x,y x,y x,y x,y" TL TR BR BL')
    ap.add_argument("--cell-m", type=float, default=None, help="square grid: cell size in metres (labels in metres)")
    ap.add_argument("-o", required=True)
    a = ap.parse_args(argv)
    if a.cols < 1 or a.rows < 1:
        ap.error("--cols and --rows must be positive")
    if a.cell_m is not None and (a.grid != "square" or a.cell_m <= 0):
        ap.error("--cell-m needs --grid square and a positive size")
    try:
        corners = parse_corners(a.corners)
    except ValueError as e:
        ap.error(str(e))
    overlay(a.concept, a.o, a.grid, a.orient, a.cols, a.rows, corners, a.cell_m)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
