"""The carriage's paint. What is outside is painted straight onto the glass plane through the position pass, at 12 fps:
rain in three layers, a dark town going by, hard bars of light. Inside, bars of light run along the floor and seats."""
import json
import math
import sys
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "src" / "npr"), str(ROOT / "src" / "three")]
import comp  # noqa: E402
import crowd_paint as CP  # noqa: E402
import engine as E  # noqa: E402
import rain as R  # noqa: E402
import shared_crowd as C  # noqa: E402
import shared_train as S  # noqa: E402

PEOPLE = C.train_people(S)
# umbrellas: those who hold theirs on the floor leave a wet patch; those it hangs from drip. (the tip in the first drawing's picture, fractions of its size)
FLOOR_UMB = {"ct2": (0.47, 0.985), "ct16": (0.78, 0.99)}
HANG_UMB = {"ct12": (0.122, 0.758), "ct13": (0.92, 0.693)}
WET = (0.72, 0.80, 0.93)
DROP = (0.86, 0.95, 1.0)


def tip_world(p, eye, tip):
    """A point of a person's picture, in the world: the card stands on their feet and faces the lens."""
    r = C.TABLE[f"{p['pid']}_a"]
    px = C.person_px(p)
    w, h = r["wh"]
    col = w - r["col"] if p["flip"] else r["col"]
    u = (1 - tip[0] if p["flip"] else tip[0]) * w
    dx, dy = eye[0] - p["x"], eye[1] - p["y"]
    n = math.hypot(dx, dy) or 1.0
    rx, ry = -dy / n, dx / n     # the card's right, as Figure.matrix has it
    off = (u - col) * px
    return p["x"] + rx * off, p["y"] + ry * off, (r["sole"] - tip[1] * h) * px


def wet_patches(eye):
    out = []
    for p in PEOPLE:
        tip = FLOOR_UMB.get(p["pid"]) or HANG_UMB.get(p["pid"])
        if tip:
            x, y, _ = tip_world(p, eye, tip)
            out.append((x, y, 0.14, 0.10, 0.4))
    return out


def drips(rgb, t, pos):
    """A drop lets go of each hanging umbrella and falls to the floor, on the same twelve drawings a second as the rain. Anybody standing nearer the lens hides it."""
    if S.close_at(t):
        return rgb
    eye = S.camera_at(t)[0]
    h, w = rgb.shape[:2]
    hit = np.linalg.norm(cv2.resize(pos, (w, h), interpolation=cv2.INTER_NEAREST) - np.array(eye, np.float32), axis=-1)
    out = (np.clip(rgb, 0, 1) * 255 + 0.5).astype(np.uint8).copy()
    for i, p in enumerate(PEOPLE):
        tip = HANG_UMB.get(p["pid"])
        if not tip:
            continue
        x, y, z = tip_world(p, eye, tip)
        f = ((R.tick(t) + i * 2) % 6) / 6
        z0 = z * (1 - f * f)
        a, b = S.project((x, y, z0 + 0.03), t), S.project((x, y, max(0.0, z0 - 0.03)), t)
        if a and b and a[2] > 0.5:
            lw = 3 if a[2] < 5 else 2
            one = np.zeros((h, w), np.uint8)
            cv2.line(one, (int(a[0]), int(a[1])), (int(b[0]), int(b[1])), 255, lw, cv2.LINE_AA)
            d = math.dist(eye, (x, y, z0))
            k = (one.astype(np.float32) / 255 * (hit > d - 0.05))[..., None]
            out = (out * (1 - k) + k * np.array(DROP, np.float32) * 255).astype(np.uint8)
    return out.astype(np.float32) / 255


def lin(h):
    c = np.array([int(h[i:i + 2], 16) / 255 for i in (1, 3, 5)], np.float32)
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4).astype(np.float32)


def hash1(a, seed=0.0):
    return np.mod(np.sin(a * 12.9898 + seed * 78.233) * 43758.5453, 1.0).astype(np.float32)


# ------------------------------------------------- rainy dusk
DUSK = lin("#4F6C8C")
TOWN = lin("#25354E")
TOWN2 = lin("#334763")
PALE = lin("#C7D6E4")
BAR_COLS = [lin("#F6F3EA"), lin("#FEE45F"), lin("#9FE3FA")]


def outside_rain(u, v, t, side):
    """u along the car, v up: returns linear rgb for the window pixels."""
    tk = R.tick(t) / 12.0
    rgb = np.empty(u.shape + (3,), np.float32)
    rgb[...] = DUSK
    # a far town, slow
    a = (u + side * 7.0 * tk) / 0.55
    h = 1.30 + 0.42 * hash1(np.floor(a), 1.0)
    rgb[v < h] = TOWN2
    # a nearer one, faster, with lit windows here and there
    a = (u + side * 19.0 * tk) / 0.9
    i = np.floor(a)
    h = 1.04 + 0.34 * hash1(i, 2.0)
    near = v < h
    rgb[near] = TOWN
    # small lit windows, a few
    wx = np.mod(a * 13.0, 1.0)
    wz = np.mod(v * 30.0, 1.0)
    lit = near & (wx < 0.55) & (wz < 0.5) & (hash1(np.floor(a * 13.0) * 5.0 + np.floor(v * 30.0) * 17.0, 3.0) > 0.86)
    rgb[lit] = BAR_COLS[1]
    # bars of light: long, hard, gone in a moment
    for row, (zc, dz, speed, ln) in enumerate(((1.08, 0.022, 44.0, 6.5), (1.27, 0.014, 58.0, 8.5), (1.44, 0.03, 37.0, 5.0), (1.62, 0.016, 66.0, 9.5))):
        a = (u + side * speed * tk + row * 3.1) / ln
        i = np.floor(a)
        on = (hash1(i, 5.0 + row) > 0.42) & (np.mod(a, 1.0) < 0.26 + 0.5 * hash1(i, 9.0 + row)) & (np.abs(v - zc) < dz)
        col = BAR_COLS[row % 3]
        rgb[on] = col
    # rain on the glass and beyond: slanted hard lines, three weights
    for k, (sp, wd, slope, fall, seg, tone) in enumerate(((0.052, 0.0035, 0.62, 3.1, 0.34, 0.45), (0.11, 0.006, 0.55, 4.3, 0.55, 0.75), (0.24, 0.011, 0.48, 6.1, 0.85, 1.0))):
        a = (u * 1.0 + side * v * slope + side * k * 0.37 + tk * side * 2.1 * (k + 1)) / sp
        i = np.floor(a)
        b = (v + tk * fall) / seg + hash1(i, 11.0 + k) * 7.0
        line = (np.abs(np.mod(a, 1.0) - 0.5) < wd / sp) & (np.mod(b, 1.0) < 0.55)
        rgb[line] = PALE * tone + rgb[line] * (1 - tone)
    return rgb


# ------------------------------------------------- warm afternoon: used by the outro
SKY = lin("#03C3FB")
FARTOWN = lin("#F0DFC0")
FARTOWN2 = lin("#E0C69C")
ROOFS = lin("#8A7C6E")
TREES = lin("#7FA765")
POLE = lin("#5F5A52")


def outside_warm(u, v, t, side):
    tt = t
    rgb = np.empty(u.shape + (3,), np.float32)
    rgb[...] = SKY
    # far houses and blocks, then a line of trees, then the embankment's wall: all sliding gently by
    a = (u + side * 1.6 * tt) / 0.8
    i = np.floor(a)
    h = 1.26 + 0.34 * hash1(i, 1.0)
    rgb[v < h] = FARTOWN
    rgb[(v < h) & (v > h - 0.035)] = ROOFS
    wn = (v < h - 0.08) & (np.mod(a * 5.0, 1.0) < 0.5) & (np.mod(v * 16.0, 1.0) < 0.45)
    rgb[wn] = FARTOWN2
    a = (u + side * 4.4 * tt) / 1.3
    i = np.floor(a)
    f = np.mod(a, 1.0) - 0.5
    h = 1.03 + 0.20 * hash1(i, 2.0) - 0.6 * f * f
    rgb[v < h] = TREES
    rgb[v < 0.99] = FARTOWN2
    a = (u + side * 7.5 * tt) / 5.0
    rgb[(np.mod(a, 1.0) < 0.012)] = POLE
    return rgb


def paint_windows(p, ids, t, fn):
    ob = p["IndexOB"]
    pos = np.nan_to_num(p["Position"][..., :3]).astype(np.float32)
    col = p["DiffCol"][..., :3].astype(np.float32)
    for k, oid in enumerate(ids["win"]):
        m = np.abs(ob - oid) < 0.5
        if m.any():
            # both sides of the car see the world run the same way past the camera's direction of travel
            col[m] = fn(pos[m][..., 1], pos[m][..., 2], t, 1.0)
    p["DiffCol"] = col
    return p, pos, ob


def light_bars(p, pos, ob, t, ids):
    """Bars of outside light passing along the floor and seats: each one lifts what it touches, hard-edged."""
    tk = R.tick(t) / 12.0
    u = pos[..., 1]
    a = (u + 17.0 * tk) / 6.0
    i = np.floor(a)
    on = (hash1(i, 21.0) > 0.45) & (np.mod(a, 1.0) < 0.20) & (pos[..., 2] < 0.95)
    for oid in ids["win"]:
        on &= np.abs(ob - oid) >= 0.5
    # the people are cards: a bar across a card would light a slice of a person. It runs along the floor and seats behind them.
    on &= np.abs(ob - ids.get("crowd", -1)) >= 0.5
    col = p["DiffCol"][..., :3]
    col[on] = col[on] * np.array((1.34, 1.30, 1.18), np.float32) + 0.02
    p["DiffCol"] = col
    return p


def look(t, ids):
    return comp.Look(shadow_tint=(0.76, 0.80, 0.88), line_px=2.2, line_near=1.35, line_min=0.46, no_ink_ids=[ids.get("crowd", -1)])


def paint_time(exr, t, ids):
    p = comp.read_exr(exr)
    p, pos, ob = paint_windows(p, ids, t, outside_rain)
    p = light_bars(p, pos, ob, t, ids)
    if "crowd" in ids:
        p = CP.floor_patches(p, C.contacts(PEOPLE, t, lambda q, _: (q["x"], q["y"]), half=(0.20, 0.12)), half_x=1.3, tone=(0.46, 0.47, 0.56))
        p = CP.floor_patches(p, wet_patches(S.camera_at(t)[0]), half_x=1.3, tone=WET)
    rgba = comp.paint(p, look(t, ids), ss=S.SS)
    rgb, a = rgba[..., :3], rgba[..., 3:4]
    return drips(np.clip(rgb * a + np.array((0.3, 0.4, 0.5), np.float32) * (1 - a), 0, 1), t, pos)


if __name__ == "__main__":
    ids = json.loads((ROOT / "work" / "render" / "train_ids.json").read_text())
    d = Path(sys.argv[1])
    out = Path(sys.argv[2]) if len(sys.argv) > 2 else ROOT / "work" / "qc" / "train"
    out.mkdir(parents=True, exist_ok=True)
    for f in sorted(d.glob("t*.exr")):
        t = float(f.stem[1:])
        rgb = E.paper_grain(paint_time(f, t, ids), 0.010)
        cv2.imwrite(str(out / f"{f.stem}.png"), (rgb[..., ::-1] * 255 + 0.5).astype(np.uint8))
        print(f.stem, flush=True)
