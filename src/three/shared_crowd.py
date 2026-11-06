"""The people at the gate, in the shoe hall and on the train in 0:24-0:43. Plain Python: who stands where, and which drawing shows when.
All of them are Codex pictures on cards with their feet on the floor (assets/gen/crowd), the way the outro's people are. Which drawing shows changes on beats and sung syllables."""
import json
import math
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TABLE_PATH = ROOT / "assets" / "gen" / "crowd" / "crowd.json"
TABLE = json.loads(TABLE_PATH.read_text()) if TABLE_PATH.exists() else {}
_A = json.loads((ROOT / "work" / "analysis" / "audio.json").read_text())
BEAT0, BP = _A["beat0"], _A["beat_period"]
HEIGHTS = {"cg1": 1.72, "cg2": 1.74, "cg3": 1.62, "cg4": 1.70, "cg5": 1.70, "cg6": 1.76, "cg7": 2.02, "cg8": 1.60, "cg9": 1.98, "cg10": 1.60, "cg11": 1.52, "cg12": 1.60, "cg13": 1.58,
           "cl1": 1.50, "cl2": 1.52, "cl3": 1.62, "cl4": 1.50, "cl5": 1.86, "cl6": 1.48, "cl7": 0.88, "cl8": 1.54, "cl9": 1.50, "cl10": 1.60, "cl11": 1.48, "cl12": 1.52, "cl13": 1.64, "cl14": 1.56, "cl15": 1.66, "cl16": 0.96,
           "ct1": 1.26, "ct2": 1.20, "ct3": 1.24, "ct4": 1.16, "ct5": 1.18, "ct6": 1.15, "ct7": 1.28, "ct8": 1.14, "ct13": 1.60, "ct14": 1.76, "ct15": 1.22, "ct16": 1.26, "ct17": 1.74}
STRAP_TOP = 1.97     # the top of the drawn strap band meets the rail


def px_of(pid, height=None):
    """Metres per pixel of this person: taken from the first drawing, so every drawing of them is one size. Saved per person, not per drawing."""
    r = TABLE[f"{pid}_a"]
    return (height if height is not None else HEIGHTS[pid]) / (r["sole"] - r["top"])


def beat_no(t):
    return math.floor((t - BEAT0) / BP + 1e-6)


def person(name, pid, x, y, z=0.0, flip=False, seq="ab", every=2, phase=0, height=None, flip_t=None, walk=None, tilt=1.0, near=False, gear=None):
    return dict(name=name, pid=pid, x=x, y=y, z=z, flip=flip, seq=seq, every=every, phase=phase, height=height, flip_t=flip_t, walk=walk, tilt=tilt, near=near, gear=gear)


def drawing_at(p, t):
    if p["walk"]:
        w = p["walk"]
        n = max(0, math.floor((t - BEAT0) / (BP / 2) + 1e-6) - w["start"])
        return p["seq"][(n + p["phase"]) % len(p["seq"])]
    n = math.floor((beat_no(t) + p["phase"]) / p["every"])
    return p["seq"][n % len(p["seq"])]


def flip_at(p, t):
    f = p["flip"]
    if p["flip_t"] is not None and t >= p["flip_t"]:
        f = not f
    return f


def walk_pos(p, t):
    w = p["walk"]
    n = max(0, math.floor((t - BEAT0) / (BP / 2) + 1e-6) - w["start"])
    return p["x"] + w["dx"] * n, p["y"]


def keys_of(p):
    """Every card this person needs: (drawing, flipped)."""
    flips = {p["flip"]}
    if p["flip_t"] is not None:
        flips.add(not p["flip"])
    return [(d, f) for d in sorted(set(p["seq"])) for f in sorted(flips)]


# --------------------------------------------------------------------------------- the gate
def gate_people(G):
    """G is shared_gate. Everyone looks at the same shut door, so we mostly get backs; a clear lane stays down the middle for the camera's line to the door."""
    r = random.Random(77)
    out = []
    taken = []
    block = [(-2.6, -8.2), (-1.7, -8.3), (2.4, -8.2), (-3.6, -13.0), (-2.8, -13.3), (2.6, -13.5), (3.45, -13.1), (-3.9, -10.9), (3.3, -11.2), (-4.4, -7.3), (4.5, -7.2), (3.9, -7.7), (-3.0, -13.6)]
    # a press person at about two cameras in three, standing behind and to the side of it, and carried round with it when the lenses turn
    for i, g in enumerate(G.GEAR):
        if i % 3 == 2:
            continue
        yaw, _ = G.aim_angles(g)
        side = 0.33 if g["x"] > 0 else -0.33
        ox = g["x"] - 0.50 * math.sin(yaw) + side * math.cos(yaw)
        oy = g["y"] - 0.50 * math.cos(yaw) - side * math.sin(yaw)
        if g["kind"] == "still":
            pid, seq = "cg1", "abac"
        else:
            pid, seq = ("cg2", "ab") if i % 2 else ("cg3", "ab")
        out.append(person(f"op{i}", pid, ox, oy, flip=i % 4 == 1, seq=seq, every=2, phase=i, gear=i))
        taken.append((ox, oy))
    # two up on the stepladders, shooting over everyone
    for k, (x, y, z) in enumerate(((-3.9, -11.28, 0.75), (3.3, -11.58, 0.75))):
        out.append(person(f"lad{k}", "cg1", x, y, z=z, flip=k == 1, seq="acab", every=1, phase=k * 3))
    # everybody else, thickening away from the gear: the press first, whoever came to look behind them. No two neighbours are the same person.
    press = {"cg4": "abac", "cg5": "ab", "cg1": "abac", "cg10": "ab"}
    crowd = {"cg6": "ab", "cg7": "ab", "cg8": "ab", "cg9": "ab", "cg10": "ab", "cg13": "ab", "cg5": "ab", "cg4": "abcb"}
    # few who hold a phone straight up where they would stand big in front of the lens
    # (nor an arm with a microphone stretched across the line to the door)
    dark_row = {"cg8": "ab", "cg10": "ab", "cg13": "ab", "cg6": "ab", "cg7": "ab"}
    weight = {"cg9": 2.5, "cg6": 1.6}
    placed = []

    def pick(table, x, y):
        best, score = None, 1e9
        for pid in table:
            sc = sum(1 / (0.5 + (x - a) ** 2 + (y - b) ** 2) for a, b, q in placed if q == pid) * weight.get(pid, 1.0) + r.uniform(0, 0.02)
            if sc < score:
                best, score = pid, sc
        placed.append((x, y, best))
        return best, table[best]

    n = 0

    def add(xx, yy, table, flip=None, every=None):
        nonlocal n
        pid, seq = pick(table, xx, yy)
        n += 1
        f = (n * 7) % 3 == 0 if flip is None else flip
        out.append(person(f"g{n}", pid, xx, yy, flip=f, seq=seq, every=every or r.choice((1, 2, 2)), phase=r.randrange(4)))
        taken.append((xx, yy))

    y = -11.2
    while y > -19.0:
        d = y + 23.5
        lane = 2.2 * d / 23.5 + 0.30
        reach = 0.36 * d + 2.0
        for sx in (-1, 1):
            x = lane + r.uniform(0.0, 0.25)
            while x < reach:
                xx = sx * x
                yy = y + r.uniform(-0.28, 0.28)
                if all(math.hypot(xx - a, yy - b) > 0.62 for a, b in block + taken):
                    add(xx, yy, dark_row if y < -16.5 else press if y > -13.6 and r.random() < 0.7 else crowd)
                x += r.uniform(0.62, 0.95)
        y -= r.uniform(0.85, 1.05)
    # between the two arcs of tripods, and thick along both ends of the wall, leaning in towards the gate: what the crane sees when it has risen over the back rows
    for y0, xs in ((-8.7, (1.95, 2.95, 3.65, 4.4, 5.25, 6.0, 6.9, 7.8, 8.7)), (-7.4, (5.6, 6.5, 7.3, 8.25, 9.2)), (-5.6, (5.3, 6.15, 7.0, 7.9, 8.8, 9.7)), (-4.3, (4.4, 5.2, 6.0, 6.9, 7.8, 8.6)), (-3.0, (3.75, 4.6, 5.5, 6.35, 7.2, 8.1, 9.0))):
        for sx in (-1, 1):
            for x in xs:
                xx, yy = sx * (x + r.uniform(-0.15, 0.15)), y0 + r.uniform(-0.25, 0.25)
                if all(math.hypot(xx - a, yy - b) > 0.6 for a, b in block + taken):
                    # those at the ends turn in towards the door
                    add(xx, yy, crowd if abs(y0) < 8 else press, flip=sx < 0, every=2)
    # two schoolchildren who do not stop: they film it as they walk past, on the half beats, the same in-and-out step as hers
    t0 = math.floor((G.T0 - BEAT0) / (BP / 2))
    out.append(person("girl", "cg11", -7.0, -15.3, seq="abcd", walk=dict(start=t0, dx=0.31)))
    out.append(person("boy", "cg12", 7.9, -12.15, flip=True, seq="abcd", walk=dict(start=t0, dx=-0.33), phase=1))
    # what is right in front of the lens: dark heads and shoulders, either side of the line to the door; the crane rises over them
    for k, (pid, x, y_, top, h, seq, ph) in enumerate((("cf1", -0.08, -21.0, 1.64, 0.99, "ab", 0), ("cf3", 1.18, -20.72, 1.72, 0.98, "ab", 1), ("cf2", -0.34, -19.3, 1.62, 0.95, "ab", 2), ("cf1", 1.30, -19.45, 1.68, 0.97, "ba", 1))):
        out.append(person(f"fg{k}", pid, x, y_, z=top - h, flip=k == 3, seq=seq, every=4, phase=ph, height=h, near=True))
    return out


def gear_pos(p, G, t):
    """An operator goes round with the rig when every lens in the street turns."""
    g = G.GEAR[p["gear"]]
    x, y, _ = G._spun(g, (p["x"], p["y"], 0.0), t)
    return x, y


# --------------------------------------------------------------------------------- the shoe hall
def hall_people(K):
    """K is shared_lockers. Not a line: twos and threes who face each other down the hall, a knot round her cell, and everyone past her cell looking back at it, so towards us.
    The drawings of cl9-cl15 are turned to the picture's left, which from the lens is the bank. Those this side of the cell turn when the camera comes round square to the bank."""
    cell = K.HER_C[0]
    turn = K.TURN_T + 0.55 * (K.STOP - K.TURN_T)
    beat = lambda t: BEAT0 + round((t - BEAT0) / BP) * BP
    flip_t = beat(turn)
    table = (
        # the first two the lens passes: one whispers across to the other, a third looks on
        ("cl3", -4.35, -1.20, False, "ab", 2, 0, None), ("cl4", -3.85, -0.62, False, "ab", 2, 1, None), ("cl11", -3.45, -1.05, False, "ab", 2, 0, None),
        # floor, then three at the bank: a note on the lockers is being pointed out, and somebody across the hall by the pillars points at it too
        ("cl12", -2.20, -0.62, False, "ab", 2, 2, None), ("cl9", -1.75, -1.05, False, "abac", 1, 0, None), ("cl8", -1.55, -1.72, False, "ab", 2, 1, None), ("cl1", -1.35, -2.86, False, "ab", 2, 2, None),
        # floor again, then two with one phone, two boys, whoever is filming the bank
        ("cl6", -0.30, -0.60, False, "ab", 2, 1, None), ("cl14", 0.00, -1.12, False, "ab", 2, 0, None), ("cl2", 0.30, -1.68, False, "ab", 2, 2, None), ("cl15", 0.42, -0.62, False, "ab", 2, 3, None),
        # the knot round her cell, this side of it
        ("cl1", cell - 0.72, -1.05, False, "ab", 1, 0, flip_t), ("cl4", cell - 1.10, -0.62, True, "ab", 2, 1, None), ("cl2", cell - 1.35, -1.28, False, "ab", 2, 0, flip_t), ("cl6", cell - 0.98, -1.55, False, "ab", 2, 1, flip_t),
        ("cl7", cell - 0.62, -0.60, False, "ab", 2, 2, flip_t),
        # and the far side: close in they are seen from behind when the lens comes round, further off they look back at it and we see their faces
        ("cl16", cell + 0.72, -0.62, False, "ab", 4, 1, None), ("cl2", cell + 0.74, -1.02, False, "ba", 2, 0, None), ("cl6", cell + 0.72, -1.95, True, "ba", 2, 3, None),
        ("cl9", cell + 1.10, -1.30, False, "abac", 1, 2, None), ("cl12", cell + 1.35, -0.72, False, "ab", 2, 0, None), ("cl10", cell + 1.60, -1.62, False, "ab", 2, 1, None), ("cl13", cell + 1.95, -1.05, False, "ab", 1, 0, None),
        ("cl11", cell + 2.25, -1.85, False, "ab", 2, 1, None), ("cl14", cell + 2.35, -0.75, False, "ab", 2, 1, None),
        # across to the pillars and on down the hall: the whole far end is turned this way
        ("cl15", 4.35, -2.62, False, "ab", 2, 1, None), ("cl12", 5.60, -2.25, False, "ba", 2, 0, None), ("cl13", 5.35, -2.78, False, "ab", 2, 2, None), ("cl14", 6.15, -2.05, False, "ba", 2, 3, None),
        ("cl9", 6.20, -1.50, False, "ab", 2, 1, None), ("cl10", 6.70, -2.60, False, "ab", 2, 0, None), ("cl12", 6.90, -0.90, False, "ab", 2, 1, None), ("cl11", 7.40, -1.90, False, "ab", 2, 2, None), ("cl15", 7.85, -1.15, False, "ba", 2, 0, None),
    )
    out = []
    for n, (pid, x, y, flip, seq, every, ph, ft) in enumerate(table):
        z = 0.062 if -0.92 < y < -0.32 else 0.0
        out.append(person(f"h{n}", pid, x, y, z=z, flip=flip, seq=seq, every=every, phase=ph, flip_t=ft))
    return out


# --------------------------------------------------------------------------------- the train
def train_people(R):
    """R is shared_train. The benches are full; the aisle stands. Every head is down over a phone or a weekly, and the weekly has her on the cover."""
    out = []
    # (id on the left bench looking right; mirrored on the right bench)
    sit_l = ("ct15", "ct2", "ct1", "ct7", "ct6", "ct5", "ct16", "ct4", "ct3", "ct8", "ct1", "ct2", "ct7", "ct5", "ct3", "ct4", "ct6", "ct8", "ct1", "ct2")
    sit_r = ("ct3", "ct16", "ct8", "ct6", "ct4", "ct15", "ct7", "ct1", "ct5", "ct2", "ct16", "ct4", "ct8", "ct6", "ct2", "ct7", "ct1", "ct5", "ct3", "ct8")
    r = random.Random(5)
    for s, ids in ((-1, sit_l), (1, sit_r)):
        i = 0
        for a, b in R.BENCHES:
            n = int((b - a) / 0.56)
            for k in range(n):
                y = a + (k + 0.5) * (b - a) / n + r.uniform(-0.03, 0.03)
                if y < 1.05:
                    continue    # beside and behind the lens
                pid = ids[i % len(ids)]
                i += 1
                out.append(person(f"s{s}_{i}", pid, s * 0.79, y, flip=s > 0, seq="ab", every=2 if i % 3 else 4, phase=r.randrange(4)))
    # standing, holding a strap: the strap is in the drawing, and its ring goes where the car's strap for that place would hang
    hold = ((-1, 3.55, "ct10"), (1, 3.75, "ct11"), (-1, 4.75, "ct9"), (1, 4.70, "ct12"), (-1, 7.65, "ct11"), (1, 7.60, "ct10"), (-1, 8.70, "ct12"), (1, 8.80, "ct9"),
            (-1, 10.2, "ct9"), (1, 10.3, "ct11"), (-1, 11.6, "ct10"), (1, 11.7, "ct12"), (-1, 13.1, "ct11"), (1, 13.3, "ct10"), (-1, 14.9, "ct12"), (1, 15.0, "ct9"), (-1, 16.8, "ct10"), (1, 16.9, "ct11"))
    for k, (s, y, pid) in enumerate(hold):
        # the drawn ring goes on the wall side of the feet, under the car's rail
        r0 = TABLE[f"{pid}_a"]
        px = STRAP_TOP / (r0["sole"] - r0["top"])
        ring = (r0["topcol"] - r0["col"]) * px
        flip = (ring > 0) == (s < 0)
        off = -ring if flip else ring
        x = s * R.STRAP_X - off
        out.append(person(f"h{k}", pid, x, y, flip=flip, seq="ab", every=2, phase=k, height="strap"))
    # the middle of the aisle further down, where the lens sees over them
    for k, (x, y, pid, flip) in enumerate(((0.44, 5.7, "ct17", True), (0.20, 9.15, "ct13", False), (-0.18, 12.4, "ct17", False), (0.34, 14.1, "ct13", True), (-0.05, 16.2, "ct13", False), (0.25, 18.0, "ct17", True))):
        out.append(person(f"m{k}", pid, x, y, flip=flip, seq="ab", every=2, phase=k))
    return out


# which straps of the car are taken over by a drawn one: their own 3D strap is not shown
def hidden_strap_ys(people, s):
    return [p["y"] for p in people if p["height"] == "strap" and (p["x"] > 0) == (s > 0)]


def person_px(p):
    h = p["height"]
    if h == "strap":
        h = STRAP_TOP
    return px_of(p["pid"], h)


WIDE = {"cl7": 1.25, "cl14": 1.9, "cl15": 1.9, "cl16": 1.6}


def contacts(people, t, pos_fn, half=(0.17, 0.11)):
    """Under the feet of everyone standing on the floor: dark hard patches in world metres (x, y, half length, half width, angle)."""
    out = []
    for p in people:
        x, y = pos_fn(p, t)
        out.append((x, y, half[0] * WIDE.get(p["pid"], 1.0), half[1], 0.0))
    return out
