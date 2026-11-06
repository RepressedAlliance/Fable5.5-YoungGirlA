"""Timing and camera for clip 2. Plain Python: used by both the Blender script and the painter."""
import json
import math
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SS = 1.5
T0, T1 = 69.30, 81.31


def _lyrics():
    return json.loads((ROOT / "work" / "analysis" / "lyrics_timed.json").read_text(encoding="utf-8"))


L = _lyrics()
HIT_T = [s["t"] for i in (19, 20, 21) for s in L[i]["syl"] if s["text"].strip() == "sa"][:14]
assert len(HIT_T) == 14


def desk_pos(col, row):
    W, D = 7.6, 9.2
    X0 = -W / 2
    return X0 + 1.05 + col * ((W - 2.1) / 5), D - 2.85 - row * 1.02


HER = (1, 3)


def her_desk():
    return desk_pos(*HER)


_dx, _dy = her_desk()
PAGE_W, PAGE_H = 0.50, 0.35         # folded once: smaller than the desk top
PAGE_ANGLE = math.radians(7.0)      # laid down by somebody, not lined up with the desk
PAGE_C = (_dx + 0.07, _dy - 0.035, 0.7165)   # a corner reaches over the desk's edge


def page_uv_axes():
    """World positions of the printed page's corners: origin (screen top-left in the opening view), u end, v end."""
    ca, sa = math.cos(PAGE_ANGLE), math.sin(PAGE_ANGLE)
    def w(dx, dy):
        return (PAGE_C[0] + dx * ca - dy * sa, PAGE_C[1] + dx * sa + dy * ca, PAGE_C[2])
    hw, hh = PAGE_W / 2, PAGE_H / 2
    return w(hw, -hh), w(-hw, -hh), w(hw, hh)


def desk_xy(c, r):
    """Where a desk stands in this shot: its place in the rows, except that the desks round hers have been pulled away from it."""
    x, y = desk_pos(c, r)
    ring = max(abs(c - HER[0]), abs(r - HER[1]))
    if 1 <= ring <= 2:
        push = (0.17, 0.05)[ring - 1]
        dx, dy = c - HER[0], r - HER[1]
        n = math.hypot(dx, dy)
        x += dx / n * push
        y -= dy / n * push    # row numbers count away from the board, y towards it
    return x, y


def _desk(c, r, z=0.716):
    x, y = desk_xy(c, r)
    return (x, y, z)


DESK_HALF = (0.31, 0.22)
DESK_TOP_Z = 0.715


def crack_spokes(seed, limit=None):
    """The crack under a word: spokes round its centre, in units of the crack's radius. limit(angle) is how far a spoke may go, so that a crack
    on a desk stops at the desk's edge. Plain Python: the renderer builds them as a mesh and the painter prints the first word's on the page."""
    r = random.Random(seed)
    out = []
    for a in range(9):
        ang = a / 9 * math.tau + r.uniform(-0.2, 0.2)
        L = r.uniform(0.45, 1.0)
        w = 0.05
        mid = L * r.uniform(0.35, 0.6)
        kink = r.uniform(-0.12, 0.12)
        if limit is not None:
            k = min(1.0, limit(ang) / L)
            L, mid = L * k, mid * k
        px = lambda d, s: (math.cos(ang + s) * d, math.sin(ang + s) * d)
        out.append([px(min(0.05, L * 0.3), -w), px(mid, -w * 0.5 + kink), px(L, kink * 1.4), px(mid, w * 0.5 + kink), px(min(0.05, L * 0.3), w)])
    return out


# Sung 5-5-4. First line: big blocks, spread out. Second: dense, packed on the windows. Third: biggest, closest.
HITS = [
    {"p": (PAGE_C[0], PAGE_C[1], 0.728), "n": (0, 0, 1), "size": 0.22, "w": 0.90, "roll": -7, "font": 0},
    {"p": (-0.6, 3.1, 0.0), "n": (0, 0, 1), "size": 1.0, "w": 0.34, "roll": 5, "font": 1, "stand": 0.9},
    {"p": (-2.2, 0.03, 2.15), "n": (0, 0, 1), "size": 1.05, "w": 0.34, "roll": -6, "font": 0, "stand": 0.9},
    {"p": (0.2, 0.40, 1.0), "n": (0, 0, 1), "size": 1.05, "w": 0.34, "roll": 4, "font": 2, "stand": 0.9},
    {"p": (-2.2, 2.2, 0.0), "n": (0, 0, 1), "size": 1.20, "w": 0.32, "roll": 8, "font": 1, "stand": 0.9},
    {"p": (-3.68, 1.9, 1.62), "n": (1, 0, 0), "size": 1.30, "w": 0.60, "roll": -5, "font": 0},
    {"p": (-3.68, 2.75, 1.25), "n": (1, 0, 0), "size": 1.15, "w": 0.60, "roll": 6, "font": 2},
    {"p": (-3.58, 3.25, 1.95), "n": (1, 0, 0), "size": 1.25, "w": 0.60, "roll": -3, "font": 1},
    {"p": (-3.68, 4.1, 1.45), "n": (1, 0, 0), "size": 1.20, "w": 0.60, "roll": 7, "font": 0, "vertical": True},
    {"p": (-3.68, 4.95, 1.85), "n": (1, 0, 0), "size": 1.25, "w": 0.60, "roll": -7, "font": 2},
    {"p": (*_desk(1, 1)[:2], 0.725), "n": (0, 0, 1), "size": 1.05, "w": 0.32, "roll": -5, "font": 1, "stand": 0.9},
    {"p": (-1.0, 4.4, 0.0), "n": (0, 0, 1), "size": 1.40, "w": 0.30, "roll": 6, "font": 0, "stand": 0.9},
    {"p": (-3.0, 9.17, 1.72), "n": (0, -1, 0), "size": 1.05, "w": 0.72, "roll": -4, "font": 2, "vertical": True},
    {"p": (-1.15, 9.13, 1.80), "n": (0, -1, 0), "size": 1.6, "w": 0.72, "roll": 3, "font": 1},
]
GROUP = [0] * 5 + [1] * 5 + [2] * 4


def clamp(x, a=0.0, b=1.0):
    return max(a, min(b, x))


def seg(t, a, b):
    return clamp((t - a) / (b - a))


def smooth(x):
    x = clamp(x)
    return x * x * x * (x * (6 * x - 15) + 10)


def ease_out(x, p=3.0):
    return 1 - (1 - clamp(x)) ** p


def lerp3(a, b, u):
    return tuple(x + (y - x) * u for x, y in zip(a, b))


ORBIT_C = (-0.45, 4.6)
ORBIT_R = 3.25
RISE_START = HIT_T[0]
RISE_END = RISE_START + 1.7
# Up close the first word is a block on the page. Seen at a slant a block that thin is only ink and side, a dark
# smudge on the paper, so from here on it is printed flat in the same place (paint_c2.flat_word), its crack with it.
# The change is hidden in the second blow, before the camera has tilted enough for the ink to pack together.
WORD_FLAT_T = HIT_T[1]
# the page goes clean of cast light later, when it is too far away for that to be seen happening
PAGE_CLEAN_T = RISE_START + 1.2


def _orbit(t):
    # one slow arc: from the front right looking back-left, round to the rear right looking at the board
    u = seg(t, RISE_START, T1)
    k = 1 - (1 - u) ** 1.35   # settles at the end, never stops dead
    a = math.radians(62 - 145 * k)
    x = ORBIT_C[0] + ORBIT_R * math.cos(a)
    y = ORBIT_C[1] + ORBIT_R * math.sin(a)
    z = 1.62 - 0.18 * k
    # looks a little past the centre of the room
    tx, ty = ORBIT_C[0] - 0.2 + 0.2 * math.sin(a), ORBIT_C[1] + 0.15
    return (x, y, z), (tx, ty, 1.12 + 0.28 * k)


def camera_at(t):
    """Returns eye, target, up. Starts straight above the page so it reads as flat, printed 2D."""
    h = 0.366 - 0.046 * seg(t, T0, RISE_START)   # slow push in on the page; the page always fills the frame
    # framed a little towards the masthead, which is at the page's -y edge
    top_eye = (PAGE_C[0], PAGE_C[1], PAGE_C[2] + h)
    top_target = (PAGE_C[0], PAGE_C[1], PAGE_C[2])
    # page top faces -y, so the camera looks with up = -y, turned to line up with the page
    top_up = (math.sin(PAGE_ANGLE), -math.cos(PAGE_ANGLE), 0.0)
    if t <= RISE_START:
        return top_eye, top_target, top_up
    oe, ot = _orbit(t)
    u = smooth(seg(t, RISE_START, RISE_END))
    # the eye leaves on a high arc; a small hit-reaction kick comes from the desk being struck
    eye = lerp3(top_eye, oe, u)
    eye = (eye[0], eye[1], eye[2] + 0.55 * math.sin(math.pi * u))
    target = lerp3(top_target, ot, smooth(seg(t, RISE_START + 0.06, RISE_END)))
    wup = (0.0, 0.0, 1.0)
    up = lerp3(top_up, wup, smooth(seg(t, RISE_START, RISE_START + 0.9)))
    n = math.sqrt(sum(c * c for c in up)) or 1.0
    return eye, target, tuple(c / n for c in up)


def _aim(t, sx, sy, axis, value, lens=26.0):
    """Point on the plane axis=value seen at screen position (sx, sy) at time t."""
    e, tg, up = camera_at(t)
    def sub(a, b): return [x - y for x, y in zip(a, b)]
    def dot(a, b): return sum(x * y for x, y in zip(a, b))
    def cross(a, b): return [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]]
    def norm(a):
        n = math.sqrt(dot(a, a)) or 1
        return [x / n for x in a]
    f = norm(sub(tg, e))
    r = norm(cross(f, up))
    u = cross(r, f)
    k = lens / 36.0
    x = (sx - 0.5) / k
    y = (0.5 - sy) * 9 / 16 / k
    d = [f[i] + r[i] * x + u[i] * y for i in range(3)]
    s = (value - e[axis]) / d[axis]
    return tuple(e[i] + d[i] * s for i in range(3))


# Composition is decided on screen: (hit index, screen x, screen y, axis, plane value)
_AIMS = {
    2: (0.78, 0.78, 2, 0.0),
    3: (0.22, 0.80, 2, 0.0),
    1: (0.74, 0.70, 2, 0.0),
    4: (0.24, 0.80, 2, 0.0),
    5: (0.22, 0.30, 0, -3.68),
    6: (0.33, 0.31, 0, -3.58),     # (these two reach over a gathered curtain, so they stand in front of it)
    7: (0.42, 0.34, 0, -3.58),
    8: (0.53, 0.40, 0, -3.58),
    9: (0.63, 0.36, 0, -3.58),
    10: (0.26, 0.74, 2, 0.725),
    11: (0.72, 0.86, 2, 0.0),
}
for _i, (_sx, _sy, _ax, _v) in _AIMS.items():
    HITS[_i]["p"] = _aim(HIT_T[_i], _sx, _sy, _ax, _v)
    HITS[_i].pop("desk", None)
# Words that struck the floor stood buried among the desks, only their tips showing, like cyan rubbish. These stand on a desk instead, a word
# about as wide as the desk, the crack in the desk top under it. Each desk was chosen from where the camera is at the blow and at the end of the shot:
# clear of the line to her newspaper for the whole orbit, not stacked on one another, and low enough to leave the chalk on the board readable.
# Each faces a fixed point on the camera's path, not the camera at its blow: the orbit goes so far round that a word turned to the camera of that
# moment was later seen from behind, its characters mirrored.
# (hit, column, row, size, the point it faces)
ON_DESK = {1: (0, 3, 0.90, (3.0, 3.3, 1.5)), 2: (1, 2, 0.80, (2.6, 3.0, 1.5)), 3: (1, 4, 1.00, (3.0, 3.0, 1.5)),
           4: (1, 0, 0.85, (2.6, 3.4, 1.5)), 10: (2, 1, 0.66, (2.2, 2.6, 1.5)), 11: (3, 2, 0.64, (1.0, 1.5, 1.5))}
# The foot of the block's strip stands on the desk top, in the crack it made. Any deeper and the desk cuts off the printed line.
for _i, (_c, _r, _s, _f) in ON_DESK.items():
    HITS[_i].update(p=(*desk_xy(_c, _r), 0.725), size=_s, crack=0.40, face=_f, stand=0.672, on_desk=True)


def cold_at(t):
    return smooth(seg(t, HIT_T[1], 79.0))


def freeze_table(objects):
    """Song time each object freezes. Small things go in rings around each blow; the room's big surfaces go on set blows."""
    big = {"wall_rear": 4, "wain_rear": 4, "win_sill": 7, "win_head": 7, "base_win": 7, "curtain_rail": 7, "floor": 9, "floor_top": 9,
           "wall_corr_low": 11, "wall_corr_top": 11, "wain_corr": 11, "ceil": 12, "wall_front": 13, "wain_front": 13, "step": 13}
    import numpy as np
    lut = np.full(max(o["id"] for o in objects) + 2, HIT_T[13], np.float64)
    for o in objects:
        name = o["name"].split(".")[0]
        # Her desk and chair are the last warm things in the room: they go on the last blow, when we are far from them,
        # and not in one frame just as the camera has lifted off the page.
        if name in (f"desk_{HER[0]}_{HER[1]}", f"desk_{HER[0]}_{HER[1]}_chair"):
            lut[o["id"]] = HIT_T[13]
            continue
        if name in big:
            lut[o["id"]] = HIT_T[big[name]]
            continue
        c = [(a + b) / 2 for a, b in zip(o["lo"], o["hi"])]
        for i in range(1, 14):
            d = math.dist(c, HITS[i]["p"])
            if d < 1.7 + 0.42 * i:
                lut[o["id"]] = HIT_T[i]
                break
    return lut


def freeze_at(t):
    """Each block freezes the room around where it struck. Later blocks spread further."""
    out = []
    for i, (tin, h) in enumerate(zip(HIT_T, HITS)):
        if i == 0 or t < tin:   # her desk and newspaper are never frozen
            continue
        reach = 1.6 + 0.62 * i
        out.append((h["p"], reach * ease_out((t - tin) / 1.1, 2.4)))
    # the very last of the warmth goes when the sung words begin
    if t > 78.4:
        out.append(((0.0, 4.5, 1.5), 12.0 * smooth(seg(t, 78.4, 79.3))))
    return out


def snow_at(t):
    return smooth(seg(t, HIT_T[7], T1 - 0.2))


def snow_fall_at(t):
    if t < HIT_T[5]:
        return None
    return -(t - HIT_T[5]) * 0.55


def sun_dir_at(t):
    """Sun climbs and swings: the big patches on the board shrink towards the windows and vanish."""
    # ends with exactly the light of the next clip, the reverse angle of this same room
    u = smooth(seg(t, HIT_T[0], 79.2))
    az = math.radians(-30 + 3.4 * u)
    el = math.radians(16 + 10.7 * u)
    return (math.cos(el) * math.cos(az), math.cos(el) * math.sin(az), -math.sin(el))


def frames_all():
    """Frame numbers count 60ths of a second; the film runs at 30 fps."""
    return list(range(0, int(round((T1 - T0) * 60)), 2))
