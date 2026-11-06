"""The lockers' paint. The sky goes grey in steps; lights go out in hard steps until only her cell has any; rain is drawn on top."""
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
import shared_lockers as S  # noqa: E402

PEOPLE = S.people()
SCREEN = (0.60, 0.90, 1.0)    # phones stay lit when the lights have gone
SCREEN_SHOE = np.array((0.34, 0.075, 0.018), np.float32)   # the photo on them is of her brown loafers: keyed #FF0080 in the picture, so the dark cannot touch it


def lin(h):
    c = np.array([int(h[i:i + 2], 16) / 255 for i in (1, 3, 5)], np.float32)
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4).astype(np.float32)


def look(t, ids):
    # ink is lighter while the shot is wide and the cells are small
    w = S.clamp((S.lens_at(t) - 26.0) / 40.0)
    return comp.Look(shadow_tint=(0.84, 0.82, 0.84), line_px=1.7 + 1.0 * w, line_near=1.25, line_min=0.5 + 0.1 * w, force_lit=[ids.get("her_shoes", -1)], no_ink_ids=[ids.get("crowd", -1)])


# the dark is never black: everything goes to a deep blue, keeping its values
NIGHT_LO = np.array((0.010, 0.016, 0.040), np.float32)
NIGHT_HI = np.array((0.105, 0.150, 0.270), np.float32)
# people keep their contrast: drawn lines and dark uniforms stay dark against the room, or they go flat and grey like ghosts
NIGHT_INK = NIGHT_LO * 0.45
PERSON_REACH = 1.9            # how far from a lamp a person stands in its light: the pool's reach at chest height


def person_mask(p, q, eye, card, pos):
    """The pixels of this one person's card, by the plane it stands in (crowdkit.Crowd.place)."""
    fx, fy = eye[0] - q["x"], eye[1] - q["y"]
    n_ = math.hypot(fx, fy) or 1.0
    fx, fy = fx / n_, fy / n_
    r0, r1 = pos[..., 0] - q["x"], pos[..., 1] - q["y"]
    wide = C.person_px(q) * C.TABLE[f"{q['pid']}_{q['seq'][0]}"]["wh"][0] * 1.4
    return card & (np.abs(r0 * fx + r1 * fy) < 0.05) & (np.abs(-r0 * fy + r1 * fx) < wide)


def grade_passes(p, t, ids):
    keep = shoe = None
    if "crowd" in ids:
        m_ = CP.screens(p, ids["crowd"])
        c_ = p["DiffCol"][..., :3]
        shoe = m_ & (c_[..., 2] < 0.6 * c_[..., 0])
        keep = CP.light_screens(p, ids["crowd"], SCREEN)
        p = CP.floor_patches(p, C.contacts(PEOPLE, t, lambda q, _: (q["x"], q["y"]), half=(0.17, 0.10)), low_z=0.075, tone=(0.50, 0.50, 0.58))
    col = p["DiffCol"]
    rgb = col[..., :3].astype(np.float32)
    ob = p["IndexOB"]
    pos = np.nan_to_num(p["Position"][..., :3]).astype(np.float32)
    # the sky by steps
    sky = np.abs(ob - ids["sky"]) < 0.5
    rgb[sky] = lin(S.stepped(S.SKY_TIERS, t))
    # what lies outside, or is the building's outside: the ground and pillars sink with the sky
    g = S.stepped(S.GROUND_TIERS, t)
    outside = (pos[..., 1] < S.EAVE_Y - 0.24) & ~sky
    tone = np.array((g ** 2.2, g ** 2.0, g ** 1.7), np.float32)
    rgb[outside] *= tone
    # the lights: what is still lit is the pool under each lamp still on, wider towards the floor, with one hard step of half light
    # round it. So the dark comes down the hall lamp by lamp and its edge is a slant of light, not a straight cut through the building
    inside = ~outside & ~sky
    x_, z_ = pos[..., 0], pos[..., 2]
    if t < S.LAST_LAMP_OFF:
        hw = 1.3 + 0.9 * np.clip((S.HALL_H - z_) / S.HALL_H, 0, 1)
        lit = np.zeros(x_.shape, bool)
        half = np.zeros(x_.shape, bool)
        for xl in S.lamps_on(t):
            d_ = np.abs(x_ - xl)
            lit |= d_ < hw
            half |= d_ < hw + 0.55
        # a person takes the light whole: no pool's edge runs through anybody
        if "crowd" in ids and len(S.lamps_on(t)) < len(S.LAMP_X):
            card = CP.card_mask(p, ids["crowd"])
            lit &= ~card
            half &= ~card
            eye = S.camera_at(t)[0]
            for q in PEOPLE:
                d_ = min((abs(q["x"] - xl) for xl in S.lamps_on(t)), default=99.0)
                if d_ < PERSON_REACH + 0.55:
                    m = person_mask(p, q, eye, card, pos)
                    half |= m
                    if d_ < PERSON_REACH:
                        lit |= m
    else:
        # the last lamp is gone: only her column of the bank itself, narrowing to her cell
        x0, x1, z0, z1 = S.lit_box(t)
        lit = (x_ >= x0) & (x_ <= x1) & (z_ >= z0) & (z_ <= z1) & (pos[..., 1] > -0.02) & (z_ < S.TOP)
        half = lit
    dark = inside & ~lit
    lum = rgb.mean(-1, keepdims=True)
    night = NIGHT_LO + (NIGHT_HI - NIGHT_LO) * np.clip(lum / 0.7, 0, 1) ** 0.6
    k_half = (inside & half & ~lit)[..., None]
    half_tone = night * 0.45 + rgb * 0.45
    if "crowd" in ids:
        card = CP.card_mask(p, ids["crowd"])[..., None]
        night = np.where(card, NIGHT_INK + (NIGHT_HI - NIGHT_INK) * np.clip(lum / 0.7, 0, 1) ** 0.8, night)
        half_tone = np.where(card, night * 0.25 + rgb * 0.5, half_tone)
    rgb = np.where(dark[..., None], np.where(k_half, half_tone, night), rgb)
    # the tubes themselves: a fitting that is out is dark; it does not go on glowing over a black hall
    on_ = S.lamps_on(t)
    tube = inside & (z_ > S.HALL_H - 0.11) & (z_ < S.HALL_H - 0.004) & (((pos[..., 1] > -0.99) & (pos[..., 1] < -0.81)) | ((pos[..., 1] > -2.19) & (pos[..., 1] < -2.01)))
    for xl in S.LAMP_X:
        if xl not in on_:
            tube_k = tube & (np.abs(x_ - xl) < 0.68)
            rgb[tube_k] = night[tube_k] * 0.55
    last = S.STEPS[-1][0]
    if t >= last - 1e-6:
        # only her cell now, and a warm patch at that
        k = inside & lit
        rgb[k] *= np.array((1.10, 0.98, 0.74), np.float32)
        # its back wall takes the light as well, or the one lit cell is a grey box
        d = p["DiffDir"][..., :3].astype(np.float32)
        d[k & (pos[..., 1] > S.DEPTH * 0.7)] = 1.0
        p["DiffDir"] = d
    if keep is not None:
        rgb[keep] = np.array(SCREEN, np.float32)
        rgb[shoe] = SCREEN_SHOE
    p["DiffCol"] = rgb
    # a dark interior keeps its shadow shapes but stops being lit by the "sun"
    return p


def outdoors_mask(p, ids):
    """Where the rain can be: the sky (through the high windows and past the pillars) and what lies beyond the eave.
    Inside the hall there is none. Measured on the render, returned at the size of the finished frame."""
    ob = p["IndexOB"]
    pos = np.nan_to_num(p["Position"][..., :3]).astype(np.float32)
    sky = np.abs(ob - ids["sky"]) < 0.5
    out = (pos[..., 1] < S.EAVE_Y - 0.25) & (pos[..., 2] < 2.7)
    m = (sky | out).astype(np.float32)
    return cv2.resize(m, (1920, 1080), interpolation=cv2.INTER_AREA)[..., None]


def rain_and_rings(rgb, t, mask):
    far, mid, near = S.rain_density(t)
    if far <= 0:
        return rgb
    eye = S.camera_at(t)[0]
    # rings only on the wet ground outside, from the eave outward, and only ahead of the lens
    rs = R.rings(t, (eye[0] - 1.5, eye[0] + 13.5), (S.EAVE_Y - 6.5, S.EAVE_Y - 0.35), -0.05, density=max(far, mid))
    base = rgb
    rgb = R.draw_rings(rgb, rs, lambda q: S.project(q, t), mask=mask)
    return R.apply_rain(rgb, t, (far, mid, near), mask=mask, base=base)


def paint_time(exr, t, ids):
    raw = comp.read_exr(exr)
    mask = outdoors_mask(raw, ids)
    p = grade_passes(raw, t, ids)
    rgba = comp.paint(p, look(t, ids), ss=S.SS)
    rgb = rgba[..., :3]
    a = rgba[..., 3:4]
    rgb = rgb * a + S_NONE * (1 - a)
    return np.clip(rain_and_rings(rgb.astype(np.float32), t, mask), 0, 1)


S_NONE = np.array((0.2, 0.3, 0.4), np.float32)


if __name__ == "__main__":
    ids = json.loads((ROOT / "work" / "render" / "lockers_ids.json").read_text())
    d = Path(sys.argv[1])
    out = Path(sys.argv[2]) if len(sys.argv) > 2 else ROOT / "work" / "qc" / "lockers"
    out.mkdir(parents=True, exist_ok=True)
    for f in sorted(d.glob("t*.exr")):
        t = float(f.stem[1:])
        rgb = E.paper_grain(paint_time(f, t, ids), 0.010)
        cv2.imwrite(str(out / f"{f.stem}.png"), (rgb[..., ::-1] * 255 + 0.5).astype(np.uint8))
        print(f.stem, flush=True)
