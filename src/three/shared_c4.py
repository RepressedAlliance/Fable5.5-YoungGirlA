"""Clip 4: fourteen rumours on a wall. Plain Python: used by Blender, the painter and the overlay."""
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SS = 1.5
T0, T1 = 103.87, 113.16
BEAT = 0.46155
LENS = 35.0
CELL_W, CELL_H = 3.0, 2.1
COLS, ROWS = 5, 3

# (id, big rumour, who says so, wall colour, text colour, distance off the wall)
RUMOURS = [
    ("w01_honor", "学年一位の優等生", "元担任", "#F4EFE0", "#0A0A0F", 0.30),
    ("w02_delinquent", "札付きの不良", "同級生", "#2B2D38", "#F4EFE0", 0.42),
    ("w03_rich", "社長令嬢", "近所の人", "#E8D9B8", "#0A0A0F", 0.24),
    ("w04_gothic", "ゴスロリで登校", "後輩", "#B9A9C8", "#0A0A0F", 0.36),
    ("w05_shut_in", "ずっと引きこもり", "SNS", "#AEB4B8", "#0A0A0F", 0.20),
    ("w06_athlete", "陸上部のエース", "部活の先輩", "#F7C9A0", "#0A0A0F", 0.46),
    ("w07_idol", "アイドル志望", "友人", "#F5C6D6", "#0A0A0F", 0.30),
    ("w08_artist", "天才絵描き", "美術教師", "#CDE3D2", "#0A0A0F", 0.26),
    ("w09_delivery", "新聞配達のバイト", "商店街", "#C8D6E8", "#0A0A0F", 0.40),
    ("w10_shrine", "実家は神社", "親戚", "#F2E6D0", "#B5222E", 0.22),
    ("w11_farmer", "田舎で大根農家", "週刊誌", "#D7E2B4", "#0A0A0F", 0.34),
    ("w12_hero", "正義の味方", "小学生", "#FEE45F", "#0A0A0F", 0.44),
    ("w13_detective", "実は名探偵", "掲示板", "#D9C7A6", "#0A0A0F", 0.28),
    ("w14_alien", "実は宇宙人", "専門家", "#101426", "#F4EFE0", 0.38),
]
# serpentine, leaving the middle cell of the middle row empty
ORDER = [(0, 0), (1, 0), (2, 0), (3, 0), (4, 0), (4, 1), (3, 1), (1, 1), (0, 1), (0, 2), (1, 2), (2, 2), (3, 2), (4, 2)]
EMPTY = (2, 1)
BEATS = [2, 2, 1.5, 1.5, 1.5, 1.5, 1.5, 1.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5]
KEY = []
_t = T0
for _b in BEATS:
    KEY.append(_t)
    _t += _b * BEAT
ALIEN_END = _t + 0.05
PULL_START = 111.31
PULL_END = 112.20


def clamp(x, a=0.0, b=1.0):
    return max(a, min(b, x))


def seg(t, a, b):
    return clamp((t - a) / (b - a))


def smooth(x):
    x = clamp(x)
    return x * x * x * (x * (6 * x - 15) + 10)


def cell_center(c, r):
    """World x and z of a cell. Wall is the plane y=0, the camera stands at negative y."""
    return (c - (COLS - 1) / 2) * CELL_W, ((ROWS - 1) / 2 - r) * CELL_H


def _base_distance():
    # frames a whole figure, with the edge of the next cell showing
    return 3.78 / (36.0 / LENS)


_grid = None


def _card_pos(t):
    """Card index as a function of time: each card's interval is held, then the whole thing is smoothed twice."""
    global _grid
    import numpy as np
    if t >= KEY[8]:
        i = int(np.searchsorted(np.array(KEY), t, side="right") - 1)
        return i + 0.018 * seg(t, KEY[i], KEY[i] + 0.23)
    if _grid is None:
        ts = np.arange(T0 - 1.0, KEY[8] + 1.0, 1 / 240)
        raw = np.clip(np.searchsorted(np.array(KEY[:8]), ts, side="right") - 1.0, 0, 7)
        win = int(0.20 * 240)
        kern = np.ones(win) / win
        pad = np.pad(raw, win, mode="edge")
        sm = np.convolve(np.convolve(pad, kern, "same"), kern, "same")[win:-win]
        _grid = (ts, sm)
    return float(np.interp(t, _grid[0], _grid[1]))


# The first eight cards: not eight times the same slide. Only three of the changes are moves (along the top row, down the end
# of it, and the long one across the empty cell); the others are hard cuts on the beat to another size of shot. Each card:
# (x off its cell's centre, z off it at the start, z at the end, distance at the start, distance at the end), distance in units of
# the plain full-figure shot. None is the plain shot, with its slow push.
CARD_SHOTS = {
    2: (-0.35, 0.18, 0.18, 0.62, 0.68),     # hard cut: head and shoulders with the words, drawing back
    3: (0.00, -0.62, 0.28, 0.72, 0.72),     # hard cut: from her shoes up to the bar
    4: (-0.90, -0.17, -0.17, 1.42, 1.34),   # hard cut: back, the end of the wall and her neighbour in the frame, closing in
    6: (0.00, 0.30, 0.42, 0.60, 0.58),      # hard cut: close, going up along the raised arm
}
PANS = {1: 0.20, 5: 0.20, 7: 0.26}          # the cards that are moved to, and half the length of the move
HARD_CUTS = tuple(KEY[i] for i in range(1, 9) if i not in PANS)


def _card_state(i, t):
    """Where the lens looks and how far back it is, on card i at time t."""
    d0 = _base_distance()
    cx, cz = cell_center(*ORDER[i])
    tk, dur = KEY[i], KEY[i + 1] - KEY[i]
    sh = CARD_SHOTS.get(i)
    if sh is None:
        return cx, cz - 0.17, d0 * (1.04 - 0.04 * seg(t, tk, tk + dur))
    u = smooth(seg(t, tk, tk + dur))
    v = seg(t, tk, tk + dur)
    return cx + sh[0], cz + sh[1] + (sh[2] - sh[1]) * u, d0 * (sh[3] + (sh[4] - sh[3]) * v)


def _early_camera(t):
    i = 0
    for k in range(8):
        if t >= KEY[k]:
            i = k
    # (a move that belongs to the next card has already begun)
    for j, w in PANS.items():
        if KEY[j] - w <= t < KEY[j] + w:
            a, b = _card_state(j - 1, t), _card_state(j, t)
            u = smooth(seg(t, KEY[j] - w, KEY[j] + w))
            x, z, d = [q0 + (q1 - q0) * u for q0, q1 in zip(a, b)]
            break
    else:
        x, z, d = _card_state(i, t)
    return (x - 0.12, -d, z - 0.10), (x, 0.0, z), (0.0, 0.0, 1.0)


def camera_at(t):
    if t < KEY[8]:
        return _early_camera(t)
    d0 = _base_distance()
    # which card are we on: a smoothed position along the serpentine, so speed changes but the camera never stops
    p = _card_pos(t)
    i = min(int(p), len(KEY) - 2)
    f = p - i
    x0_, z0_ = cell_center(*ORDER[i])
    x1_, z1_ = cell_center(*ORDER[i + 1])
    x = x0_ + (x1_ - x0_) * f
    z = z0_ + (z1_ - z0_) * f
    i = min(int(round(p)), len(KEY) - 1)
    # a slow push on every card, so nothing is ever still
    tk = KEY[i]
    dur = (KEY[i + 1] - tk) if i + 1 < len(KEY) else 0.6
    d = d0 * (1.04 - 0.04 * seg(t, tk, tk + dur))
    # a little parallax lean, opposite to where it is heading
    z -= 0.17
    eye_x, eye_z = x - 0.12, z - 0.10
    # pull out to the whole wall
    p = smooth(seg(t, PULL_START, PULL_END))
    wall_d = (COLS * CELL_W * 1.08) / (36.0 / LENS)
    d = d + (wall_d - d) * p ** 1.3
    x *= (1 - p)
    z *= (1 - p)
    eye_x = eye_x * (1 - p)
    eye_z = eye_z * (1 - p)
    return (eye_x, -d, eye_z), (x, 0.0, z), (0.0, 0.0, 1.0)


def project(p, t):
    eye, tg, up = camera_at(t)
    def sub(a, b): return [x - y for x, y in zip(a, b)]
    def dot(a, b): return sum(x * y for x, y in zip(a, b))
    def cross(a, b): return [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]]
    def norm(a):
        n = math.sqrt(dot(a, a)) or 1
        return [x / n for x in a]
    f = norm(sub(tg, eye))
    r = norm(cross(f, up))
    u = cross(r, f)
    v = sub(p, eye)
    z = dot(v, f)
    if z <= 0.01:
        return None
    k = LENS / 36.0
    return 960 + dot(v, r) / z * k * 1920, 540 - dot(v, u) / z * k * 1920, z


def meta():
    return json.loads((ROOT / "assets" / "gen" / "standee" / "meta.json").read_text(encoding="utf-8"))


def frames_all():
    return list(range(0, int(round((T1 - T0) * 60)), 2))   # the film runs at 30 fps
