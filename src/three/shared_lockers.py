"""Shoe lockers in the rain. Plain Python: timing, camera, the bank's layout and when each light goes out."""
import json
import math
import sys
from pathlib import Path

import shared_cam

ROOT = Path(__file__).resolve().parents[2]
SS = 1.5
T0, T1 = 902 / 30, 1123 / 30
L = json.loads((ROOT / "work" / "analysis" / "lyrics_timed.json").read_text(encoding="utf-8"))
LINE_T = [L[i]["syl"][0]["t"] for i in (4, 5, 6, 7)]
SUN = (0.10, 0.52, -0.85)     # the light comes down and in: hard shadow in every cell and under every shelf

# The bank: open cubbyholes facing -y. Cell (col, tier): col 0 at X0, tier 0 at the bottom.
X0, COLS = -9.0, 52
CW, CH, DEPTH, PLINTH = 0.30, 0.27, 0.34, 0.12
TIERS = 6
LIP = 0.05                    # the rail under each cell floor carries that cell's name plate
HER = (38, 1)                 # her cell
EAVE_Y = -3.0                 # the hall's open side; only outside this does the rain fall and the ground get wet
HALL_H = 2.75
TOP = PLINTH + TIERS * CH


def cell_box(col, tier):
    x = X0 + col * CW
    z = PLINTH + tier * CH
    return x, x + CW, z, z + CH


HER_X0, HER_X1, HER_Z0, HER_Z1 = cell_box(*HER)
HER_C = ((HER_X0 + HER_X1) / 2, -0.05, HER_Z0 + 0.12)


def clamp(x, a=0.0, b=1.0):
    return max(a, min(b, x))


def smooth(x):
    x = clamp(x)
    return x * x * x * (x * (6 * x - 15) + 10)


STOP = LINE_T[3] + 0.7       # the camera has arrived at her cell and rests


TURN_T = LINE_T[2] + 0.9      # looks along the hall until the rain is full, then turns to face her cell


def lens_at(t):
    return 26.0 + (40.0 - 26.0) * smooth((t - TURN_T) / (STOP - TURN_T))


def camera_at(t):
    """Under the eave, inside the hall, looking along the bank: the lockers recede on the left and the rain is out on
    the right, past the pillars. It slides along the bank and turns until it faces her cell, then rests."""
    u = clamp((t - T0) / (STOP - T0))
    # a steady slide that eases into its stop: no stop on a single frame
    s = 0.55 * u + 0.45 * u * u * (3 - 2 * u)
    x = -6.2 + (HER_C[0] - 0.05 + 6.2) * s
    k = smooth((t - TURN_T) / (STOP - TURN_T))
    y = -2.2 - 0.4 * k
    z = 1.12 - 0.17 * k
    # the view turns from along the hall (8 degrees off it) to square on
    yaw = math.radians(8.0 + 82.0 * k)
    # at the end it is the point of the turn that lands on her cell, so the aim blends to it
    far = 6.0
    tx = (x + far * math.cos(yaw)) * (1 - k) + HER_C[0] * k
    ty = (y + far * math.sin(yaw)) * (1 - k) + HER_C[1] * k
    tz = 1.0 * (1 - k) + (HER_C[2] + 0.02) * k
    # the rest is never dead still: a very slow drift
    if t > STOP:
        x += 0.012 * (t - STOP)
    return (x, y, z), (tx, ty, tz), (0, 0, 1)


def project(p, t):
    return shared_cam.project(p, camera_at(t), lens_at(t))


# Lights: each step is a hard change on a beat. The lit box shrinks: first whole sections, then columns, then tiers.
def _steps():
    a, b = LINE_T[1], LINE_T[3] + 0.46
    x_lo, x_hi = X0 - 2, X0 + COLS * CW + 2
    z_lo, z_hi = -1.0, 99.0
    states = []
    # sections go out from the far ends in towards her cell: four from the left, two from the right
    for xl in (-7.0, -4.5, -2.0, 0.0):
        states.append(("x0", xl))
    states.append(("x1", 4.6))
    states.append(("x0", 1.0))
    states.append(("x1", 3.6))
    # now it is her neighbours
    states.append(("x0", HER_X0 - CW * 2))
    states.append(("x1", HER_X1 + CW))
    states.append(("x0", HER_X0))
    states.append(("x1", HER_X1))
    # and everything above and below her in that column
    states.append(("z1", HER_Z1 + 0.012))
    states.append(("z0", HER_Z0 - 0.012))
    n = len(states)
    out = []
    for i, (kind, v) in enumerate(states):
        out.append((a + (b - a) * i / (n - 1), kind, v))
    return out


STEPS = _steps()
CARDS_FROM = STEPS[-1][0]     # the last light has narrowed to her own cell: every other shoe is in the dark, and the cells face the lens enough for drawn ones


ARM_OUT_BEAT = 70             # from this beat the first pointing girl is past the lens with only her arm left in the frame
OVER_BOY_BEAT = 76            # from this beat the second stands over the crouching boy
# The close-up on her cell. From this beat the people round it hold one drawing to the end of the shot: their pictures are almost a metre tall in the frame by now, and a swap under a camera
# that has come to rest throws a phone hundreds of pixels in one frame. Drawings by person: the boy on the left holds the one the push goes into (s02b's HOLD_N), the boy on the right
# the one where his phone is held out over the cell, and the girl above him stands upright, clear of his head.
CLOSE_BEAT = 76
CLOSE_HOLD = {"h15": "a", "h16": "b", "h17": "a", "h12": "a", "h11": "d"}
# Her arm is level at the lens's own height, so it can only ever end on somebody's chest down the hall. These three stood right at her fingertip, and she read as pointing at the boy's shoulder.
# They stand further in, so that past her finger there is a clear gap, and then the crowd and the lockers.
CLEAR_OF_FINGER = {"h25": (4.35, -2.34), "h27": (5.0, -2.42), "h30": (6.7, -2.34)}


def _hold(p, beat, drawing, n_len=64):
    """This person shows this drawing from this beat on; before it they go on as they were."""
    seq = [p["seq"][k % len(p["seq"])] for k in range(n_len)]
    for b in range(beat, beat + 40):
        seq[((b + p["phase"]) // p["every"]) % n_len] = drawing
    p["seq"] = "".join(seq)


def lit_box(t):
    """(x0, x1, z0, z1) of what still has light at time t."""
    box = dict(x0=-99.0, x1=99.0, z0=-99.0, z1=99.0)
    for st, kind, v in STEPS:
        if t >= st:
            box[kind] = v
    return box["x0"], box["x1"], box["z0"], box["z1"]


# Before the shrinking box there are the real lamps: tube fittings every 2.5 m along the ceiling. Each goes out whole, on a beat, the
# far ones and the ones behind the lens first; what it lit goes with it. The fitting over her column is the last, and when that goes
# only her column of the bank is left. (time, the lamp's x)
LAMP_X = [X0 - 2.0 + 2.5 * k for k in range(9)]     # -11 ... 9
_st = [s_[0] for s_ in STEPS]
# The last two, one over the people nearest the lens and one over the far end of the hall, go on the same beat: the room and everyone in it go dark on one frame.
LAMP_OFF = [(_st[0], -11.0), (_st[0], -8.5), (_st[1], -6.0), (_st[2], -3.5), (_st[4], 9.0), (_st[5], 6.5), (_st[5], -1.0), (_st[6], 4.0), (_st[6], 1.5)]
LAST_LAMP_OFF = _st[6]


def lamps_on(t):
    off = {x for st, x in LAMP_OFF if t >= st}
    return [x for x in LAMP_X if x not in off]


SKY_TIERS = [(LINE_T[0] - 1, "#03C3FB"), (LINE_T[0] + 0.62, "#33AEDC"), (LINE_T[1], "#5A9CC0"), (LINE_T[1] + 0.92, "#6C8FAB"),
             (LINE_T[2], "#587C97"), (LINE_T[3], "#4A667F")]
GROUND_TIERS = [(LINE_T[0] - 1, 1.0), (LINE_T[0] + 0.62, 0.94), (LINE_T[1], 0.86), (LINE_T[1] + 0.92, 0.78), (LINE_T[2], 0.68), (LINE_T[3], 0.58)]


def stepped(tiers, t):
    v = tiers[0][1]
    for a, b in tiers:
        if t >= a:
            v = b
    return v


def rain_density(t):
    """It starts with the far layer on 'utsu', and is three layers by 'tokidoki ame'."""
    far = clamp((t - (LINE_T[1] + 0.46)) / 1.2)
    mid = clamp((t - (LINE_T[1] + 1.38)) / 0.6)
    near = clamp((t - LINE_T[2]) / 0.3)
    return far, mid, near


def people():
    """shared_crowd's people of the hall. The girl who points has her arm up now (cl1_d): she points across the hall at the lockers, and over the crouching boy, not down at the floor and on to his head.
    When only her arm would still be in the frame, or her other arm would hang over the boy, she holds the drawing that keeps it out."""
    import shared_crowd as C
    extra = ROOT / "assets" / "gen" / "crowd" / "hall_extra.json"
    C.TABLE.update(json.loads(extra.read_text()))
    out = C.hall_people(sys.modules[__name__])
    first = True
    for p in out:
        if p["name"] in CLEAR_OF_FINGER:
            p["x"], p["y"] = CLEAR_OF_FINGER[p["name"]]
        if p["pid"] == "cl1":
            hold = ("b", ARM_OUT_BEAT) if first else ("d", OVER_BOY_BEAT)
            first = False
            n_len = 64
            # the arm goes out and comes back every two beats, for both of them: on every beat it flapped
            seq = [p["seq"].replace("a", "d")[(k // (2 // p["every"])) % 2] for k in range(n_len)]
            for b in range(hold[1], hold[1] + 40):
                seq[((b + p["phase"]) // p["every"]) % n_len] = hold[0]
            p["seq"] = "".join(seq)
        if p["name"] in CLOSE_HOLD:
            _hold(p, CLOSE_BEAT, CLOSE_HOLD[p["name"]])
    return out


def frames_all():
    return list(range(0, int(round((T1 - T0) * 60)), 2))
