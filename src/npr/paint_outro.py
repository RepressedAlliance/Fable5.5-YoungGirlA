"""The outro's paint: warm light on everything except the sky and her; violet-warm shadows."""
import json
import sys
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "src" / "npr"), str(ROOT / "src" / "three")]
import comp  # noqa: E402
import engine as E  # noqa: E402
import paint_train  # noqa: E402
import shared_outro as S  # noqa: E402

WARM = np.array((1.06, 0.98, 0.84), np.float32)    # in linear light, on the lit colour
WARM_ROOM = np.array((1.03, 0.99, 0.93), np.float32)   # the room's own paint is warm already
TINT = {"gate": (0.78, 0.72, 0.80), "lockers": (0.80, 0.72, 0.76), "train": (0.93, 0.89, 0.87), "classroom": (1.0, 0.93, 0.88)}   # the car: its window bars are a pattern on the floor, not the subject


def warm_passes(p, name, ids=()):
    ma = np.round(p["IndexMA"]).astype(np.int32)
    col = p["DiffCol"][..., :3].astype(np.float32)
    k = (ma != 2) & (ma != 5)
    col[k] *= WARM_ROOM if name == "classroom" else WARM
    p["DiffCol"] = np.clip(col, 0, 1)
    if name == "classroom" and "curtain" in ids:
        # a blowing curtain's folds sit right on the ink threshold and come out as black crumbs: inside it there is no crease ink, only its light and its outline
        cm = np.abs(p["IndexOB"] - ids["curtain"]) < 0.5
        if cm.any():
            n = p["Normal"].astype(np.float32).copy()
            n[cm, 0], n[cm, 1], n[cm, 2] = 1.0, 0.0, 0.0
            p["Normal"] = n
    return p


def floor_patches(p, patches, low_z=0.02, half_x=None, tone=(0.42, 0.38, 0.40), band_y=None):
    """Patches that join people to the floor. Fixed to the floor through the position pass, one hard tone, whatever light bar they fall across."""
    pos = np.nan_to_num(p["Position"][..., :3]).astype(np.float32)
    low = pos[..., 2] < low_z
    if half_x is not None:
        low &= np.abs(pos[..., 0]) < half_x
    if band_y is not None:
        low &= (pos[..., 1] > band_y[0]) & (pos[..., 1] < band_y[1])
    m = np.zeros(low.shape, bool)
    for x, y, a, b, ang in patches:
        c, s_ = np.cos(ang), np.sin(ang)
        u = (pos[..., 0] - x) * c + (pos[..., 1] - y) * s_
        v = -(pos[..., 0] - x) * s_ + (pos[..., 1] - y) * c
        m |= (u / a) ** 2 + (v / b) ** 2 < 1
    m &= low
    col = p["DiffCol"][..., :3].astype(np.float32)
    col[m] *= np.array(tone, np.float32)
    p["DiffCol"] = col
    return p


def look(name, ids):
    kw = dict(shadow_tint=TINT[name], no_ink_ids=[ids["her"]])
    if name == "gate":
        kw.update(line_px=2.5, line_near=1.3, line_min=0.62, force_lit=ids["gate"]["lit"])
    elif name == "lockers":
        kw.update(line_px=2.6, line_near=1.25, line_min=0.6, force_lit=[ids["lockers"]["her_plate"], ids["lockers"]["her_shoes"]])
    elif name == "train":
        kw.update(line_px=2.2, line_near=1.35, line_min=0.46)
    else:
        kw.update(line_px=2.6, line_near=1.25, line_min=0.6, force_lit=[ids.get("paper", -1)])
    return comp.Look(**kw)


def paint_time(exr, t, ids):
    name = S.scene_at(t)
    p = comp.read_exr(exr)
    if name == "train":
        # outside the windows slows and stops as the train brakes
        p, _, _ = paint_train.paint_windows(p, ids["train"], S.train_clock(t), paint_train.outside_warm)
        p = floor_patches(p, S.train_contact(t) + S.contacts(name, t), half_x=1.0)
    elif name == "gate":
        p = floor_patches(p, S.gate_contact(t) + S.contacts(name, t), tone=(0.56, 0.50, 0.55))
    elif name == "lockers":
        p = floor_patches(p, S.lockers_contact(t), low_z=S.LOCK_BOARD_Z, band_y=S.LOCK_BOARD_Y, tone=(0.55, 0.47, 0.45))
    elif name == "classroom":
        p = floor_patches(p, S.contacts(name, t), tone=(0.56, 0.50, 0.50))
    p = warm_passes(p, name, ids)
    rgba = comp.paint(p, look(name, ids), ss=S.SS)
    rgb, a = rgba[..., :3], rgba[..., 3:4]
    return np.clip(rgb * a + np.array((0.012, 0.76, 0.98), np.float32) * (1 - a), 0, 1)


if __name__ == "__main__":
    ids = json.loads((ROOT / "work" / "render" / "outro_ids.json").read_text())
    d = Path(sys.argv[1])
    out = ROOT / "work" / "qc" / "outro"
    out.mkdir(parents=True, exist_ok=True)
    for f in sorted(d.glob("t*.exr")):
        t = float(f.stem[1:])
        rgb = E.paper_grain(paint_time(f, t, ids), 0.010)
        cv2.imwrite(str(out / f"{f.stem}.png"), (rgb[..., ::-1] * 255 + 0.5).astype(np.uint8))
        print(f.stem, flush=True)
