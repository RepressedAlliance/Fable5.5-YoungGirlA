"""Remove the flat green background the character images are generated on.

The figure's outline is black, so edge pixels are mixes of black and green: alpha can be solved
directly, and the leftover green is removed from the colour (no halo).
Usage: cutout.py raw.png out.png   or   cutout.py --all
"""
import sys
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "assets" / "gen" / "raw"
CUT = ROOT / "assets" / "gen" / "cut"


def cutout(bgr):
    im = bgr[..., ::-1].astype(np.float32) / 255
    r, g, b = im[..., 0], im[..., 1], im[..., 2]
    green = np.clip(g - np.maximum(r, b), 0, 1)
    a = 1 - green
    a = np.where(a > 0.965, 1, a)
    # the generated background is not a perfectly flat green: anything this faint is background noise
    a = np.where(a < 0.20, 0, a)
    # background pixels are connected to the border: keep any isolated green-ish specks inside the figure opaque
    solid = (a > 0.5).astype(np.uint8)
    n, lab = cv2.connectedComponents(1 - solid, connectivity=4)
    border = np.unique(np.concatenate([lab[0], lab[-1], lab[:, 0], lab[:, -1]]))
    # holes between arm and body are also background only if they are really green
    for i in range(1, n):
        if i in border:
            continue
        m = lab == i
        if green[m].mean() < 0.6:
            a[m] = 1
    # unmix
    safe = np.maximum(a, 1e-3)
    fg = np.dstack([r / safe, np.clip((g - (1 - a)) / safe, 0, 1), b / safe])
    fg = np.clip(fg, 0, 1)
    edge = (a < 0.999)
    fg[..., 1] = np.where(edge, np.minimum(fg[..., 1], np.maximum(fg[..., 0], fg[..., 2])), fg[..., 1])
    out = np.dstack([fg, a])
    # slivers of green left inside the figure, between fingers or under a collar: closed with ink. A flat green paint would be far bigger than this.
    core = ((out[..., 1] > out[..., 0] + 0.05) & (out[..., 1] > out[..., 2] + 0.05) & (a > 0.15)).astype(np.uint8)
    n, lab, st, _ = cv2.connectedComponentsWithStats(core, connectivity=8)
    for i in range(1, n):
        if 3 <= st[i, 4] <= 400:
            m = cv2.dilate((lab == i).astype(np.uint8), np.ones((3, 3), np.uint8)) > 0
            out[m] = (0.03, 0.03, 0.03, 1.0)
    return out


def key_magenta(rgba):
    """Phone screens are generated pure magenta: makes the screen transparent and returns its mask."""
    r, g, b = rgba[..., 0], rgba[..., 1], rgba[..., 2]
    m = np.minimum(r, b) - g
    mask = np.clip(m / 0.6, 0, 1)
    out = rgba.copy()
    out[..., 3] = out[..., 3] * (1 - mask)
    return out, mask


def save(rgba, path):
    path.parent.mkdir(parents=True, exist_ok=True)
    bgra = (np.clip(rgba[..., [2, 1, 0, 3]], 0, 1) * 255 + 0.5).astype(np.uint8)
    cv2.imwrite(str(path), bgra)


def load(path):
    bgra = cv2.imread(str(path), cv2.IMREAD_UNCHANGED).astype(np.float32) / 255
    return bgra[..., [2, 1, 0, 3]]


if __name__ == "__main__":
    if sys.argv[1] == "--all":
        # sorted so the newest take of an image is the one that ends up in cut/
        for f in sorted(RAW.glob("[pwtgoh]*.png"), key=lambda p: p.name.replace(".png", "")):
            save(cutout(cv2.imread(str(f))), CUT / (f.name.split(".")[0] + ".png"))
            print(f.name)
    else:
        save(cutout(cv2.imread(sys.argv[1])), Path(sys.argv[2]))
