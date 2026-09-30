"""Tile rendered images into one labelled contact sheet (one row per prefix).

  python3 contact_sheet.py FRAMEDIR front,side,q34 --out sheet.png [--every 2] [--max-width 1600]

Expects files named <prefix>_<label>.png (for example front_012.png). Rows that are wider than
--max-width are scaled down so the sheet stays readable in one image.
"""
import argparse
import glob
import os

from PIL import Image, ImageDraw


def main():
    p = argparse.ArgumentParser()
    p.add_argument("frame_dir")
    p.add_argument("prefixes")
    p.add_argument("--out", required=True)
    p.add_argument("--every", type=int, default=1, help="keep every Nth frame")
    p.add_argument("--max-width", type=int, default=1600)
    args = p.parse_args()
    rows = []
    for prefix in args.prefixes.split(","):
        files = sorted(glob.glob(os.path.join(args.frame_dir, f"{prefix}_*.png")))[:: args.every]
        if not files:
            raise SystemExit(f"no {prefix}_*.png in {args.frame_dir}")
        tiles = []
        for f in files:
            im = Image.open(f).convert("RGB")
            ImageDraw.Draw(im).text((4, 4), os.path.basename(f)[len(prefix) + 1:-4], fill=(255, 255, 0))
            tiles.append(im)
        row = Image.new("RGB", (sum(t.size[0] for t in tiles), max(t.size[1] for t in tiles)), (20, 20, 20))
        x = 0
        for t in tiles:
            row.paste(t, (x, 0))
            x += t.size[0]
        if row.size[0] > args.max_width:
            row = row.resize((args.max_width, round(row.size[1] * args.max_width / row.size[0])), Image.LANCZOS)
        rows.append(row)
    sheet = Image.new("RGB", (max(r.size[0] for r in rows), sum(r.size[1] for r in rows)), (20, 20, 20))
    y = 0
    for r in rows:
        sheet.paste(r, (0, y))
        y += r.size[1]
    sheet.save(args.out)
    print(f"{len(rows)} row(s) -> {args.out}")


if __name__ == "__main__":
    main()
