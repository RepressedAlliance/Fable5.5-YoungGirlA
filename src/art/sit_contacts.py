"""Where each sitting drawing's seat rests: assets/gen/sit_contacts.json, and a sheet to check them by eye (work/qc/sit_contacts.png).

Seen from the side, the bottom edge of a sitting body runs, from its back towards its knees: down round the seat, along the
seat (the part that rests on the bench), then down again where the skirt or coat hangs over the bench's front edge, and on
down the shins to the soles. The resting part is the first gentle stretch after the curve of the back. What hangs lower than it
on the knees' side has to be in front of the bench's edge (src/three/sitfit.py places each card so).

{drawing: {"col": c, "row": r, "wall": +1 or -1}}  (wall: which way the drawing's back faces, in columns)
Points set by hand in OVERRIDE win over the found ones. Run again after any of these drawings changes."""
import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "assets" / "gen" / "sit_contacts.json"
SHEET = ROOT / "work" / "qc" / "sit_contacts.png"

CROWD = json.loads((ROOT / "assets" / "gen" / "crowd" / "crowd.json").read_text())
EXTRAS = json.loads((ROOT / "assets" / "gen" / "extras" / "extras.json").read_text())


def drawings():
    """(key, path, sole row, pinned column) of everyone who sits in a train."""
    out = []
    for pid in ("ct1", "ct2", "ct3", "ct4", "ct5", "ct6", "ct7", "ct8", "ct15", "ct16"):
        for d in "ab":
            r = CROWD[f"{pid}_{d}"]
            out.append((f"{pid}_{d}", ROOT / "assets" / "gen" / "crowd" / f"{pid}_{d}.png", r["sole"], r["col"]))
    for pid in ("tp1", "tp2", "tp3", "tp5"):
        for d in "ab":
            r = EXTRAS[f"{pid}_{d}"]
            out.append((f"{pid}_{d}", ROOT / "assets" / "gen" / "extras" / f"{pid}_{d}.png", r["sole"], r["col"]))
    for name, sole, col in (("o03_train_sit", 1489, 283), ("o33_train_lean", 1489, 283), ("o33_train_lean2", 1484, 516), ("o31_train_rise", 1484, 516)):
        out.append((name, ROOT / "assets" / "gen" / "cut" / f"{name}.png", sole, col))
    return out


# hand-set points, where the search below picks the wrong stretch: {key: (col, row)} or (col, row, wall)
OVERRIDE = {
    # the outro's passengers and Rin, measured on the bottom edge of the seat (2026-11-18)
    "tp1_a": (250, 613), "tp1_b": (250, 613),
    # the lower edge of her coat, cut off where she sits (src/art/trim_coat.py)
    "tp2_a": (250, 626), "tp2_b": (250, 626),
    "tp3_a": (450, 858), "tp3_b": (450, 858),
    "tp5_a": (400, 588), "tp5_b": (400, 588),
    "o03_train_sit": (640, 1038), "o33_train_lean": (640, 1038), # getting up she leans forward over her feet, which the search takes for her back: her back is to the right in all four
    "o33_train_lean2": (680, 1072, 1), "o31_train_rise": (700, 1074, 1),
}


def find(alpha, sole, col):
    h, w = alpha.shape

    # which way the back faces: the body above the seat leans to the side the back is on
    upper = alpha[: int(sole * 0.55)]
    ys, xs = np.nonzero(upper)
    wall = 1 if xs.mean() > col else -1
    bottom = np.full(w, -1)
    for c in range(w):
        r = np.flatnonzero(alpha[: int(sole) - 20, c])
        if r.size:
            bottom[c] = r.max()
    cols = [c for c in (range(w - 1, -1, -1) if wall > 0 else range(w)) if bottom[c] >= 0]
    # from the back towards the knees: skip the curve round the seat, then the first stretch that runs flat for 4 cm or more
    step = 6
    seq = cols[::step]
    slopes = [abs(bottom[b] - bottom[a]) / step for a, b in zip(seq, seq[1:])]
    run, best = [], None
    for i, s in enumerate(slopes):
        if s < 0.45 and bottom[seq[i]] > sole * 0.45:
            run.append(i)
        else:
            if len(run) * step >= 36:
                best = run
                break
            run = []
    if best is None and len(run) * step >= 36:
        best = run
    if best is None:
        return None, wall
    pts = [seq[i] for i in best] + [seq[best[-1] + 1]]
    c = max(pts, key=lambda c: bottom[c])
    return (int(c), int(bottom[c])), wall


def main():
    table = {}
    tiles = []
    for key, path, sole, col in drawings():
        im = Image.open(path).convert("RGBA")
        a = np.asarray(im)[:, :, 3] > 32
        pt, wall = find(a, sole, col)
        if key in OVERRIDE:
            pt = OVERRIDE[key][:2]
            wall = OVERRIDE[key][2] if len(OVERRIDE[key]) > 2 else wall
        if pt is None:
            print("NO CONTACT FOUND", key)
            continue
        table[key] = {"col": pt[0], "row": pt[1], "wall": wall}
        bg = Image.new("RGBA", im.size, (255, 255, 255, 255))
        bg.alpha_composite(im)
        d = ImageDraw.Draw(bg)
        r = max(6, im.size[0] // 90)
        d.line([(0, pt[1]), (im.size[0], pt[1])], fill=(255, 0, 0, 255), width=max(2, r // 3))
        d.ellipse([pt[0] - r, pt[1] - r, pt[0] + r, pt[1] + r], outline=(255, 0, 0, 255), width=max(2, r // 3))
        d.line([(col, sole - 3 * r), (col, sole)], fill=(0, 160, 255, 255), width=max(2, r // 3))
        d.text((10, 10), f"{key} wall {'+' if wall > 0 else '-'}", fill=(255, 0, 0, 255))
        s = 420 / im.size[1]
        tiles.append(bg.convert("RGB").resize((int(im.size[0] * s), 420)))
    OUT.write_text(json.dumps(table, indent=1), encoding="utf-8")
    per = 8
    rows_ = [tiles[i:i + per] for i in range(0, len(tiles), per)]
    W = max(sum(t.size[0] for t in r) for r in rows_)
    sheet = Image.new("RGB", (W, 420 * len(rows_)), (255, 255, 255))
    for j, r in enumerate(rows_):
        x = 0
        for t in r:
            sheet.paste(t, (x, j * 420))
            x += t.size[0]
    SHEET.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(SHEET)
    print(len(table), "drawings ->", OUT)


if __name__ == "__main__":
    main()
