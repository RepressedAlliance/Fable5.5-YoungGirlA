"""The gate's paint: plain sun, one shadow tone, ink. A flash is one frame of one camera's own light, thrown through the position pass on to the road
ahead of it and the people standing there. No veil over the picture, and no shape of light on the wall, the posts, the door or the tape.
On the road it is printed as hard dots that thin out with the distance, the film's own screen: a flat oval with an outline, however hard-edged, reads as a puddle."""
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
import shared_crowd as C  # noqa: E402
import shared_gate as S  # noqa: E402

SHADOW = np.array((0.76, 0.80, 0.88), np.float32)
POOL_AHEAD = 2.4                 # the pool of a flash on the road: its middle this far ahead of the camera
POOL_OUT, POOL_IN = (3.3, 1.9), (1.7, 0.95)
ROAD_END = -1.90                 # it stops at the kerb
DOT_PITCH = 8.0                  # the screen on the road, in pixels of the finished frame, at 45 degrees
ROAD_LIT = 0.92
PERSON_OUT, PERSON_IN = 1.7, 2.5       # on a person it multiplies: colours get brighter and drawn lines stay dark. Mixed towards white, a figure in it was a pale ghost
CARD_TILT = 0.75                 # shot_gate's Crowd(tilt=)
BLUE = np.array((0.93, 0.97, 1.0), np.float32)


SCREEN = (0.55, 0.88, 1.0)
# the sun is behind the school, so we see everybody's back in shade; what is right at the lens goes darker still, a black mass of heads and shoulders
BACK_TONE = np.array((0.60, 0.65, 0.76), np.float32)
NEAR_TONE = np.array((0.26, 0.29, 0.40), np.float32)
PEOPLE = C.gate_people(S)


def people_pos(p, t):
    if p["gear"] is not None:
        return C.gear_pos(p, S, t)
    if p["walk"]:
        return C.walk_pos(p, t)
    return p["x"], p["y"]


def feet(t):
    return C.contacts([p for p in PEOPLE if not p["near"] and p["z"] < 0.1], t, people_pos, half=(0.20, 0.13))


def look(t, ids):
    return comp.Look(shadow_tint=tuple(float(v) for v in SHADOW), line_px=2.5, line_near=1.3, line_min=0.62, edge_m=0.0, force_lit=ids.get("lit", []), no_ink_ids=[ids.get("crowd", -1), ids.get("thin", -1)])


def firing(t):
    """The cameras that go off on this frame. One frame each, then it is over."""
    return [idx for ft, idx in S.FLASHES if -1e-3 <= t - ft < 1 / 30 - 1e-3]


def pool_of(idx, t):
    """A firing camera's pool of light on the road ahead of it: (centre x, y, the way it points, half length, half width), as far as it matters."""
    head = S.flash_head(S.GEAR[idx], t)
    aim = S.aim_point(S.GEAR[idx], t)
    dx, dy = aim[0] - head[0], aim[1] - head[1]
    n = math.hypot(dx, dy) or 1.0
    dx, dy = dx / n, dy / n
    return head[0] + dx * POOL_AHEAD, head[1] + dy * POOL_AHEAD, dx, dy


def in_pool(x, y, pool, a, b):
    cx, cy, dx, dy = pool
    u = (x - cx) * dx + (y - cy) * dy
    v = -(x - cx) * dy + (y - cy) * dx
    return (u / a) ** 2 + (v / b) ** 2 < 1


def pool_level(x, y, pool, a, b):
    """How much of this pool's light falls here, 1 in its middle to 0 at its rim: how big the screen's dots are."""
    cx, cy, dx, dy = pool
    u = (x - cx) * dx + (y - cy) * dy
    v = -(x - cx) * dy + (y - cy) * dx
    return np.clip(1.25 * (1 - np.sqrt((u / a) ** 2 + (v / b) ** 2)), 0, 1)


def person_mask(p, q, t, eye, uid_mask, pos):
    """The pixels of this one person's card, by the plane it stands in (crowdkit.Crowd.place): a person takes a light whole, never cut through by its edge."""
    x, y = people_pos(q, t)
    fx, fy = eye[0] - x, eye[1] - y
    n_ = math.hypot(fx, fy) or 1.0
    fx, fy = fx / n_, fy / n_
    rx, ry = -fy, fx
    a = math.atan2(max(eye[2] - q["z"] - 0.9, 0.0), n_) * CARD_TILT
    # the card leans back about its feet
    nx, ny, nz = fx * math.cos(a), fy * math.cos(a), math.sin(a)
    r0 = pos[..., 0] - x
    r1 = pos[..., 1] - y
    r2 = pos[..., 2] - q["z"]
    wide = C.person_px(q) * C.TABLE[f"{q['pid']}_a"]["wh"][0] * 1.4
    return uid_mask & (np.abs(r0 * nx + r1 * ny + r2 * nz) < 0.03) & (np.abs(r0 * rx + r1 * ry) < wide)


def throw_light(p, t, uid=None):
    """A flash lights the people and the road in front of its camera, for one frame. The road takes a pool of hard dots that stops at the kerb; whoever stands in that pool is lit whole,
    keeping their drawn lines. Nothing else takes it: not the wall, the posts, the door or the tape, which only show a flat white shape if they are lifted, and not the gear."""
    idxs = firing(t)
    if not idxs:
        return p
    pos = np.nan_to_num(p["Position"][..., :3]).astype(np.float32)
    col = p["DiffCol"][..., :3].astype(np.float32)
    d = p["DiffDir"][..., :3].astype(np.float32)
    x_, y_ = pos[..., 0], pos[..., 1]
    is_card = CP.card_mask(p, uid) if uid is not None else np.zeros(col.shape[:2], bool)
    road = (pos[..., 2] < 0.0095) & (y_ < ROAD_END) & ~is_card
    white = BLUE ** 2.2
    eye = S.camera_at(t)[0]
    h, w = col.shape[:2]
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    k = 2 * np.pi * np.sqrt(0.5) / (DOT_PITCH * w / 1920.0)
    lattice = 0.5 + 0.25 * (np.cos((xx + yy) * k) + np.cos((xx - yy) * k))
    for idx in idxs:
        pool = pool_of(idx, t)
        lit = road & (pool_level(x_, y_, pool, *POOL_OUT) > lattice)
        col[lit] = (col + (white - col) * ROAD_LIT)[lit]
        d[lit] = 1.0
        if uid is None:
            continue
        for q in PEOPLE:
            if q["near"] or q["z"] >= 0.1:
                continue
            x, y = people_pos(q, t)
            if in_pool(x, y, pool, *POOL_OUT):
                m = person_mask(p, q, t, eye, is_card, pos)
                col[m] = np.minimum(col * (PERSON_IN if in_pool(x, y, pool, *POOL_IN) else PERSON_OUT), 1.0)[m]
    p["DiffCol"] = col
    p["DiffDir"] = d
    return p


def paint_time(exr, t, ids):
    p = comp.read_exr(exr)
    uid = ids.get("crowd", -1)
    if not p["IndexOB"].size or not (abs(p["IndexOB"] - uid) < 0.5).any():
        uid = None
    if uid is not None:
        keep = CP.light_screens(p, uid, SCREEN)
        pos_y = np.nan_to_num(p["Position"][..., 1]).astype(np.float32)
        k = np.clip((-pos_y - 14.5) / 4.5, 0, 1)[..., None]
        m = CP.card_mask(p, uid) & ~keep
        col = p["DiffCol"][..., :3].astype(np.float32)
        col[m] = (col * (BACK_TONE * (1 - k) + NEAR_TONE * k))[m]
        p["DiffCol"] = col
        p = CP.floor_patches(p, feet(t), tone=(0.46, 0.46, 0.56))
    p = throw_light(p, t, uid)
    rgba = comp.paint(p, look(t, ids), ss=S.SS)
    rgb = rgba[..., :3]
    a = rgba[..., 3:4]
    return rgb * a + np.array([0.012, 0.76, 0.98], np.float32) * (1 - a)


if __name__ == "__main__":
    ids = json.loads((ROOT / "work" / "render" / "gate_ids.json").read_text())
    d = Path(sys.argv[1])
    out = Path(sys.argv[2]) if len(sys.argv) > 2 else ROOT / "work" / "qc" / "gate"
    out.mkdir(parents=True, exist_ok=True)
    for f in sorted(d.glob("t*.exr")):
        t = float(f.stem[1:])
        rgb = E.paper_grain(paint_time(f, t, ids), 0.010)
        cv2.imwrite(str(out / f"{f.stem}.png"), (rgb[..., ::-1] * 255 + 0.5).astype(np.uint8))
        print(f.stem, flush=True)
