"""How far across each standing or sitting drawing reaches, row by row: assets/gen/opaque_bands.json.

For every 8 rows of a drawing, the first and last column with paint in them, keyed by the lowest painted row of the band.
The 3D shots read it to check, frame by frame, whether any painted part of a person's card is inside the set behind
them (a bench they sit on), and if so draw the card nearer the lens and smaller by the same ratio (setkit.pull_to_lens).
Run again after any of these drawings changes."""
import json
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "assets" / "gen" / "opaque_bands.json"
STEP = 8
SOURCES = [
    ("assets/gen/crowd", "ct*.png"),
    ("assets/gen/extras", "tp*.png"),
    ("assets/gen/cut", "o03_train_*.png"),
    ("assets/gen/cut", "o3[1-4]_train_*.png"),
    ("assets/gen/cut", "o11_walk_*.png"),
    ("assets/gen/cut", "o5[1-8]_*.png"),
]


def bands(path):
    a = np.asarray(Image.open(path).convert("RGBA"))[:, :, 3] > 32
    out = []
    for r0 in range(0, a.shape[0], STEP):
        band = a[r0:r0 + STEP]
        cols = np.flatnonzero(band.any(axis=0))
        if cols.size:
            # the lowest row that has paint in it, so a band never reaches below the soles
            out.append([r0 + int(np.flatnonzero(band.any(axis=1))[-1]), int(cols[0]), int(cols[-1])])
    return out


def main():
    table = {}
    for d, pat in SOURCES:
        for p in sorted((ROOT / d).glob(pat)):
            table[p.relative_to(ROOT).as_posix()] = bands(p)
    OUT.write_text(json.dumps(table, separators=(",", ":")))
    print(len(table), "drawings ->", OUT)


if __name__ == "__main__":
    main()
