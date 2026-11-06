"""The world carrying on, one ordinary day in order: the train, the gate, the shoe lockers, the classroom, cut on two-bar lines.
She does something small in each: gets up as the train brakes, walks in through the gate (the same walk, cut on the step),
puts her loafers away and changes shoes, and in the classroom the wind lifts the paper on her desk and she puts her hand on it.
That paper is the form the next section opens on. Plain Python."""
import json
import math
from pathlib import Path

import shared_cam
import shared_gate as G
import shared_lockers as K
import shared_train as R

ROOT = Path(__file__).resolve().parents[2]
SS = 1.5
T0, T1 = 6180 / 30, 6660 / 30
_A = json.loads((ROOT / "work" / "analysis" / "audio.json").read_text())
BP = _A["beat_period"]


def bar_time(n):
    return _A["beat0"] + (_A["bar_phase"] + 4 * n) * BP


# hard cuts on every second bar line: 114, 116, 118 (210.805, 214.498, 218.190)
CUTS = (bar_time(114), bar_time(116), bar_time(118))
SCENES = ("train", "gate", "lockers", "classroom")
# every sun is low enough that her shadow is long, hard and in the same direction as everything else's in that place
SUNS = {"train": (0.60, 0.26, -0.75), "gate": (0.60, 0.58, -0.46), "lockers": (0.20, 0.74, -0.44), "classroom": (0.80, -0.22, -0.42)}


def scene_index(t):
    i = 0
    for c in CUTS:
        if t >= c - 1e-6:
            i += 1
    return i


def scene_at(t):
    return SCENES[scene_index(t)]


def scene_span(i):
    a = T0 if i == 0 else CUTS[i - 1]
    b = T1 if i == len(CUTS) else CUTS[i]
    return a, b


def smooth(x):
    x = max(0.0, min(1.0, x))
    return x * x * (3 - 2 * x)


# ---- the walk: four drawings of one cycle, a foot lands on every beat, she only moves when the drawing changes.
# The index runs on through the cut from train to gate, so the step carries across it.
HALF_BEAT = BP / 2
STEP = 0.275     # metres per drawing (two drawings are one pace)


def walk_index(t):
    return math.floor((t - _A["beat0"]) / HALF_BEAT + 1e-6)


def walk_drawing(t):
    return walk_index(t) % 4


# ---- the train: she sits, the train brakes, she gets up on the beat, and walks off down the car towards the door
BRAKE = CUTS[0] - 7 * BP
STOPPED = BRAKE + 3 * BP
RISE = CUTS[0] - 6 * BP
STAND = CUTS[0] - 5 * BP
WALK_T = CUTS[0] - 4 * BP
# Her loafers do not move while she gets up: every drawing is pinned by its feet to this one spot. The in-betweens are four frames each, so it reads as one movement.
HER_FEET = (0.849, 7.006, 0.0)
LEAN_T = RISE - 5 / 30
LEAN2_T = RISE - 2 / 30
UP_T = STAND - 4 / 30
TRAIN_WALK0 = (0.78, 7.05, 0.0)   # the first step out from the seat
TRAIN_WALK1 = (0.05, 8.90, 0.0)   # where the last drawing before the cut comes down


def train_state(t):
    """Which drawing (sit, lean, rise, up, stand, or 0-3 of the walk) and where its feet are."""
    if t < LEAN_T:
        return "sit", HER_FEET
    if t < LEAN2_T:
        return "lean", HER_FEET
    if t < RISE:
        return "lean2", HER_FEET
    if t < UP_T:
        return "rise", HER_FEET
    if t < STAND:
        return "up", HER_FEET
    if t < WALK_T:
        return "stand", HER_FEET
    a, b = walk_index(WALK_T), walk_index(CUTS[0] - 1e-4)
    u = (walk_index(t) - a) / max(1, b - a)
    p = tuple(x + (y - x) * u for x, y in zip(TRAIN_WALK0, TRAIN_WALK1))
    return walk_drawing(t), p


def train_contact(t):
    """Her dark patch on the car floor, in world metres (x, y, half length, half width, angle): the floor there is mostly out of the window's light, so the sun alone gives her no shadow.
    One under the feet, one thrown a short way along the sun's direction."""
    _, p = train_state(t)
    a = math.atan2(SUNS["train"][1], SUNS["train"][0])
    return [(p[0], p[1], 0.19, 0.115, 0.0), (p[0] + 0.20 * math.cos(a), p[1] + 0.20 * math.sin(a), 0.30, 0.095, a)]


def train_clock(t):
    """Outside the windows: this clock runs, slows through the braking, and stops."""
    k = 1.7
    if t <= BRAKE:
        return k * t
    d = STOPPED - BRAKE
    u = min(1.0, (t - BRAKE) / d)
    # the integral of a speed going from 1 to 0 as 1 - smoothstep(u)
    return k * (BRAKE + d * (u - u ** 3 + 0.5 * u ** 4))


def train_lean(t):
    """(forward lean of everything hanging, 0..1 and past it, how much of the running sway is left)."""
    if t < BRAKE:
        return 0.0, 1.0
    if t < STOPPED:
        return smooth((t - BRAKE) / 0.42), 1 - smooth((t - BRAKE) / (STOPPED - BRAKE))
    x = t - STOPPED
    # the train has stopped: it all swings back past upright and settles
    return math.exp(-x / 0.9) * math.cos(2 * math.pi * x / 1.5), 0.0


# ---- the gate: she walks in off the road and through it, with the camera coming along behind her, low
GATE_FROM = -3.45     # y of her feet as the shot opens: the road outside
GATE_X = -0.40


CURB_Y = (-1.89, -1.79)


def gate_at(t):
    a = walk_index(CUTS[0])
    y = GATE_FROM + STEP * (walk_index(t) - a)
    # the one step that would land inside the kerb comes down just in front of it, on the road, where the lens can see the sole and its shadow
    if CURB_Y[0] <= y <= CURB_Y[1]:
        y = CURB_Y[0] - 0.04
    return walk_drawing(t), (GATE_X, y, 0.0)


def scrap_tick(t):
    """The bit of barrier tape left tied to the post moves at 12 fps."""
    return math.floor(t * 12 + 1e-6)


# ---- the lockers: loafers into her cell, a foot into each indoor shoe, a finger at the heel, and away. All on the duckboard, within reach.
# Root cause of the old "slides like slides" (2026-11-06): the drawings came at different scales (a shoe was 230 px in one, 384 px in the next) and her stride was
# laid out shorter than the drawn stride, so a planted foot slipped back at each change. Now each drawing has its own scale, measured on the shoe's toe cap, and is
# pinned by the toe of the foot that is on the ground; a stride is exactly as long as the drawing says; and there are in-betweens.
LOCK_Z = 0.06
_CELL = K.HER_C[0]
TOE_X = _CELL - 0.097                             # the left toe of the indoor shoes she left on the board
# name, its picture, metres per pixel, row of the soles, column of the toe that is pinned
LOCK_PX = 0.00095
LOCK_DRAW = {
    "put": ("o46_put", 0.00073, 988, 189),
    "lift": ("o46_lift", 0.00073, 988, 189),
    "release": ("o46_release", 0.00073, 988, 189),
    "rise": ("o46_rise", 0.00092, 988, 374),
    "over": ("o45_step_over", 0.00092, 988, 374),
    "step": ("o42_shoes_step", 0.00095, 988, 374),
    "into": ("o47_into_shoe", 0.00071, 987, 223),
    "heel": ("o43_shoes_heel", 0.00068, 988, 219),
    "straight": ("o48_straighten", 0.00098, 973, 376),
}
# (start, in beats from the cut; drawing). Each pose is held on a beat; the moves between them are in-betweens of a few frames.
# The bag stays on one side throughout, and the loafers are set down by a drawing whose pair stands exactly where the pair in the cell does, so nothing jumps.
LOCK_SEQ = ((0.0, "put"), (0.62, "lift"), (1.0, "release"), (1.16, "rise"), (1.33, "over"), (1.5, "step"), (2.65, "into"), (3.0, "heel"), (4.15, "straight"))
LOCK_WALK = 4.5                                   # in beats from the cut
LOCK_HOME = 1.0                                   # her loafers are in the cell once her hand has let go
# the walk, a drawing each third of a beat (a stride of 64 cm in 0.6 s, an ordinary pace): (drawing, picture, row of the soles, column of the toe on the ground, is that the foot after this stride's change)
LOCK_WALK_DRAW = (("b", "o44_walk_b", 971, 549, 0), ("f", "o44_walk_f", 969, 549, 0), ("c", "o44_walk_c", 976, 929, 0),
                  ("g", "o44_walk_g", 976, 338, 1), ("d", "o44_walk_d", 977, 495, 1), ("h", "o44_walk_h", 976, 496, 1),
                  ("a", "o44_walk_a", 968, 950, 1), ("e", "o44_walk_e", 967, 325, 2))
STRIDE_CA = ((929 - 258) * LOCK_PX, (950 - 251) * LOCK_PX)   # the drawn strides of c and a, in metres


def _lock_walk(n):
    """The n-th drawing of the walk and the x of its planted toe. The planted foot never moves until the other has landed."""
    d = LOCK_WALK_DRAW[n % 8]
    cyc = n // 8
    x = TOE_X - cyc * sum(STRIDE_CA)
    if d[4] >= 1:
        x -= STRIDE_CA[0]
    if d[4] >= 2:
        x -= STRIDE_CA[1]
    return d[0], (x, -0.60, LOCK_Z)


def lockers_state(t):
    """Which drawing and where its planted toe is. Her loafers are in the cell from when the hand has let go."""
    k = (t - CUTS[1]) / BP
    if k < LOCK_WALK:
        key = LOCK_SEQ[0][1]
        for a, nm in LOCK_SEQ:
            if k >= a:
                key = nm
        return key, (TOE_X, -0.60, LOCK_Z)
    return _lock_walk(math.floor((k - LOCK_WALK) * 3 + 1e-6))


def loafers_home(t):
    return (t - CUTS[1]) / BP >= LOCK_HOME


# ---- the classroom: chin on her hand, looking out; the wind comes in; the paper lifts and she puts her hand on it
CHIN_END = CUTS[2] + 5.0 * BP
PRESS = CHIN_END + 0.5 * BP
GUST = CUTS[2] + 2.75 * BP
HER_ROOM = (-1.71, 2.72, 0.0)     # the card stands against her chair back, as seen from the lens


# She is in the wind too: her hair goes with the curtain and the paper. The body of these drawings is line for line the same picture, only hair, bow and scarf change, six drawings a second.
WIND_SEQ = ("wa", "wc", "wb0", "wb1", "wb2", "wb1", "wc", "wb0", "wb2")
TURN_T = CHIN_END
MID_T = CHIN_END + 3 / 30


def desk_drawing(t):
    if t < GUST + 0.08:
        return "chin"
    if t < TURN_T:
        return WIND_SEQ[min(int((t - (GUST + 0.08)) * 6 + 1e-6), len(WIND_SEQ) - 1)]
    if t < MID_T:
        return "tblown"
    if t < PRESS:
        return "mblown"
    x = t - PRESS
    # the hand is down; the wind lets go of her hair last of all, and it comes down as the curtain and the paper do (gust_at is gone by PRESS + 0.73)
    return "pblown" if x < 0.22 else "pwa" if x < 0.38 else "phalf" if x < 0.54 else "pwb" if x < 0.72 else "press"


def gust_at(t):
    """How far the wind has the curtain and the paper, 0..1, on twelve drawings a second."""
    tk = math.floor(t * 12 + 1e-6) / 12
    x = tk - GUST
    if x <= 0:
        return 0.0
    return smooth(x / 0.75) * (1 - smooth((x - 1.0) / 1.0))


def paper_lift(t):
    """The corner of the paper: it lifts with the wind until her hand comes down on it."""
    if t >= PRESS:
        return 0.0
    tk = math.floor(t * 12 + 1e-6) / 12
    return gust_at(t) * (1.0 + 0.16 * math.sin(tk * 19.0))


# ---- the other people: an ordinary day, and nobody looks at her. Each is a pair of drawings (or the four of a walk) pinned by the feet; which one shows changes on beats.
EXTRAS = json.loads((ROOT / "assets" / "gen" / "extras" / "extras.json").read_text())


def _b(n):
    """n beats before the cut out of the train."""
    return CUTS[0] - n * BP


def _c(n):
    """n beats after the cut into the classroom."""
    return CUTS[2] + n * BP


# name: (scene, feet x, y, z, height in metres from the feet to the top of the head, the moments it goes (to b, to a, to b, ...))
SITTERS = {
    # the office worker's head nods with the rails, lurches as the train brakes, and swings back when it has stopped
    "tp1": ("train", -0.80, 8.60, 0.0, 1.22, (_b(9), _b(8.6), BRAKE + 0.05, STOPPED + 0.20)),
    "tp2": ("train", -0.80, 12.40, 0.0, 1.15, (_b(8), _b(6), _b(3.5), _b(1.5))),
    # she turns a page
    "tp3": ("train", 0.80, 9.00, 0.0, 1.10, (_b(8.5), _b(7.9), _b(3), _b(2.4))),
    "tp4": ("train", -0.75, 15.30, 0.0, 1.72, (BRAKE + 0.10, STOPPED + 0.10)),
    "tp5": ("train", 0.80, 12.60, 0.0, 1.20, (STOPPED + 0.15, _b(1))),
    # the classmates: a girl at her own desk, and three at the front of the room, talking among themselves
    "cs1": ("classroom", -2.75, 5.77, 0.72, 1.13 - 0.72, (_c(1), _c(2), _c(5), _c(6))),
    "cs2": ("classroom", -2.85, 8.40, 0.0, 1.54, (_c(2), _c(3.5), _c(6.5))),
    "cs3": ("classroom", -2.35, 8.00, 0.0, 1.62, (_c(3), _c(5), _c(7.5))),
    "cs4": ("classroom", -3.25, 8.00, 0.0, 1.52, (_c(4), _c(6))),
}
# name: (height, x, y where the shot opens, by how many drawings their step is ahead of hers)
WALKERS = {"gs1": (1.52, -1.45, 3.0, 0), "gs2": (1.62, 0.90, 4.0, 1)}
GS_STEP = 0.255


def _table(key, ref, height):
    e, r = EXTRAS[key], EXTRAS[ref]
    return e, height / (r["sole"] - r["top"])


def people_table(scene):
    """Every drawing of the other people in this place: {key: (picture, metres per pixel, row of the soles, column pinned, canvas, column the shadow grows from)}."""
    out = {}
    for name, (sc, x, y, z, h, moves) in SITTERS.items():
        if sc == scene:
            for k in "ab":
                e, px = _table(f"{name}_{k}", f"{name}_a", h)
                out[f"{name}_{k}"] = (f"{name}_{k}", px, e["sole"], e["col"], e["wh"], e["col"])
    if scene == "gate":
        for name, w in WALKERS.items():
            for k in "abcd":
                e, px = _table(f"{name}_{k}", f"{name}_a", w[0])
                # a walker's head stays in one column; the shadow grows from the foot on the ground
                out[f"{name}_{k}"] = (f"{name}_{k}", px, e["sole"], e["wh"][0] / 2, e["wh"], e["col"])
    return out


def people_at(scene, t):
    """Who shows now in this place: [(key, (x, y, z))]."""
    out = []
    for name, (sc, x, y, z, h, moves) in SITTERS.items():
        if sc == scene:
            n = sum(1 for m in moves if t >= m)
            out.append((f"{name}_{'ab'[n % 2]}", (x, y, z)))
    if scene == "gate":
        a = walk_index(CUTS[0])
        for name, (h, x, y0, ph) in WALKERS.items():
            n = walk_index(t) - a
            out.append((f"{name}_{'abcd'[(walk_drawing(t) + ph) % 4]}", (x, y0 + GS_STEP * n, 0.004)))
    return out


def contacts(scene, t):
    """The dark patch each of the other people makes on the floor where they touch it, in world metres (x, y, half length, half width, angle). Fixed to the floor, one hard tone."""
    a = math.atan2(SUNS[scene][1], SUNS[scene][0])
    out = []
    for key, p in people_at(scene, t):
        if p[2] > 0.1:
            continue          # sitting at a desk, seen from the waist up
        out.append((p[0], p[1], 0.17, 0.12, 0.0))
        out.append((p[0] + 0.14 * math.cos(a), p[1] + 0.14 * math.sin(a), 0.24, 0.085, a))
    return out


# her foot on the ground in each drawing of the walk, relative to the column the drawing is pinned by, in metres
WALK_COL = 507
WALK_FOOT = (529, 465, 451, 525)
WALK_PX = 0.00112


def gate_contact(t):
    """Under the sole on the ground, and from it along the sun: she has the same light as the posts."""
    k, p = gate_at(t)
    x = p[0] + (WALK_FOOT[k] - WALK_COL) * WALK_PX
    a = math.atan2(SUNS["gate"][1], SUNS["gate"][0])
    return [(x + 0.03, p[1], 0.21, 0.085, 0.0)]


# the patches under her shoes on the board: each drawing's soles, measured from the drawing (work/qc/outro_group/patch_o2.py)
LOCK_SOLES = json.loads((ROOT / "assets" / "gen" / "extras" / "locker_soles.json").read_text())
LOCK_BOARD_Z = 0.075
LOCK_BOARD_Y = (-1.0, -0.2)
# her shadow on the kickboard: the board is only 6 cm of the picture, so her shadow card stands right against it, or what falls on it is the hem of her skirt, a hard rectangle.
# Moved along the sun's direction, it keeps the side the shadow falls on; what the board shows is her shoes and what is above it her legs.
LOCK_SHADOW_D = 0.58
LOCK_SHADOW_Z = 0.085


def lockers_contact(t):
    k, p = lockers_state(t)
    return [(p[0] + (a + b) / 2 - 0.004, p[1], (b - a) / 2 + 0.012, 0.06, 0.0) for a, b in LOCK_SOLES[k]]


# ---- cameras
def camera_at(t):
    i = scene_index(t)
    a, b = scene_span(i)
    u = (t - a) / (b - a)
    name = SCENES[i]
    if name == "train":
        # low in the aisle, a few metres behind her seat, hardly moving
        # once she is walking it starts to come along behind her, as it goes on doing at the gate
        x = max(0.0, t - WALK_T)
        follow = 0.5 * (x * x / 1.8 if x < 0.9 else x - 0.45)
        y = 3.35 + 0.14 * u + follow
        return (-0.16 + 0.05 * u, y, 1.00), (0.26 + 0.03 * u, y + 4.65, 0.97), (0, 0, 1)
    if name == "gate":
        # at her heels, low: her and the posts and the tower behind them, not a lot of road
        y = -9.05 + 2.20 * u
        return (-0.34, y, 0.82), (-0.12, y + 9.0, 1.20), (0, 0, 1)
    if name == "lockers":
        # the same line as the shot that stopped on her cell, right down at floor level
        x = K.HER_C[0] + 0.268 - 0.02 * u
        return (x, -4.05, 0.33), (x, -0.6, 0.30), (0, 0, 1)
    # from behind her and to her right, past the next desk: her, the elbow on her desk, the window beyond
    return (-0.56 - 0.03 * u, 1.13 + 0.06 * u, 1.24), (-2.41, 4.13, 0.81), (0, 0, 1)


LENSES = {"train": 35.0, "gate": 40.0, "lockers": 85.0, "classroom": 50.0}


def lens_at(t):
    return LENSES[scene_at(t)]


def project(p, t):
    return shared_cam.project(p, camera_at(t), lens_at(t))


def frames_all():
    return list(range(0, int(round((T1 - T0) * 60)), 2))
