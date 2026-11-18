"""The woman in the beige coat in the outro's car (extras tp2_a, tp2_b): her coat ends where she sits.

Drawn on a high seat, her long coat hangs straight down from under her, behind her legs, to her ankles. On a bench that part
of it would have to go down through the cushion: wherever her card stood, either her seat floated in front of the bench or the
coat came down through the cushion (src/three/sitfit.py). Cut off below the seat, with an outline along the cut, the coat reads
as tucked under her on the bench. The originals are kept in work/gen/fix1118/tp2_orig.

usage: trim_coat.py"""
import shutil
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
DIR = ROOT / "assets" / "gen" / "extras"
KEEP = ROOT / "work" / "gen" / "fix1118" / "tp2_orig"
SEAT_ROW = 621      # the underside of her thighs, where they come out of the coat (sit_contacts: 619)
LINE = 5            # outline thickness, as drawn elsewhere on her
INK = (32, 30, 34)
COAT_END = 790      # below the coat's lowest point (row 765), above her ankles


def trim(name):
    src = KEEP / f"{name}.png"
    if not src.exists():
        KEEP.mkdir(parents=True, exist_ok=True)
        shutil.copy2(DIR / f"{name}.png", src)
    im = np.asarray(Image.open(src).convert("RGBA")).astype(np.int32)
    r, g, b, a = im[..., 0], im[..., 1], im[..., 2], im[..., 3]
    navy = (a > 128) & (b > r + 15) & (b > 40)
    out = im.copy()
    h, w = a.shape
    painted = np.flatnonzero((a[SEAT_ROW] > 128))
    left = int(painted[0])
    # the coat ends above her ankles; the trousers and shoes below that are left alone
    rows = range(SEAT_ROW, COAT_END)
    # the leg's own outline: the left edge of the trousers, less the width of the line round them
    lefts = {}
    for row in rows:
        c = np.flatnonzero(navy[row, 200:470])
        if c.size:
            lefts[row] = 200 + int(c[0]) - LINE - 1
    right = lefts[SEAT_ROW + LINE + 2]
    for row in rows:
        if row not in lefts:
            break
        stop = lefts[row]
        for c in range(0, stop):
            # a slight sag in the cut, as cloth sitting on a cushion
            u = (c - left) / max(1, right - left)
            edge = SEAT_ROW + 3.0 * np.sin(np.pi * min(max(u, 0.0), 1.0))
            d = row - edge
            if d > LINE / 2 + 0.5:
                out[row, c, 3] = 0
            elif d > -LINE / 2 - 0.5 and c >= left - 1:
                # the outline along the cut, soft at its lower edge
                k = 1.0 if d < LINE / 2 - 0.5 else (LINE / 2 + 0.5 - d)
                out[row, c, :3] = INK
                out[row, c, 3] = int(round(255 * k)) if d > 0 else max(int(a[row, c]), int(round(255 * k)))
    Image.fromarray(out.astype(np.uint8), "RGBA").save(DIR / f"{name}.png")
    print(name, "cut below row", SEAT_ROW, "from column", left, "to", right)


if __name__ == "__main__":
    for n in ("tp2_a", "tp2_b"):
        trim(n)
