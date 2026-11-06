"""Timing and motion for the dark bedroom (10 kowai, 11 first half). Plain Python: used by Blender, the painter and the 2D overlay.

World: door wall at y=0, room is y<0, corridor y>0. Her view looks towards +y, so screen right is +x. Floor z=0.
"""
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SS = 1.5
T0, T1 = 4930 / 30, 5376 / 30      # 10 kowai
T2 = 5597 / 30                     # end of 11, first half
L = json.loads((ROOT / "work" / "analysis" / "lyrics_timed.json").read_text(encoding="utf-8"))
KO = [s["t"] for i in (47, 48, 49) for s in L[i]["syl"] if s["text"].strip() == "ko"]
assert len(KO) == 14
LAST_KNOCK = KO[-1]

# brightness: hard steps on sung syllables, never a fade. Each step shows one more thing: the door, then what is on the floor, then the whole room.
STEPS = (165.25, 167.09, 168.93)

# room
X0, X1 = -1.35, 1.45
YBACK = -3.6
HT = 2.4
XD = 0.35                # door centre
DW = 0.76                # clear opening
DOOR_H = 2.0
GAP = 0.055              # door bottom above the floor: enough to see a whole toe cap through
DOOR_T = 0.04
LIGHT = (XD, 1.0, 0.117)  # the real light in the corridor, low: a lamp standing on the corridor floor. Its height against the gap sets how far the wedge reaches (0.82 m)
HINGE = (XD - DW / 2 + 0.015, 0.0)
LEVER = (XD + DW / 2 - 0.09, 1.0)
DOOR_EDGE = XD + DW / 2 - 0.015 - 0.003   # latch side of the door leaf

SHEET_W, SHEET_H = 0.297, 0.21
LENS = 22.0
CLOSE = (180.5333, 182.8333)   # the close view of a sheet, on sung syllables


def clamp(x, a=0.0, b=1.0):
    return max(a, min(b, x))


def seg(t, a, b):
    return clamp((t - a) / (b - a))


def smooth(x):
    x = clamp(x)
    return x * x * x * (x * (6 * x - 15) + 10)


def eout(x, p=3):
    return 1 - (1 - clamp(x)) ** p


def level(t):
    return sum(1 for s in STEPS if t >= s)


# ---- what each knock does (index into KO). The film cuts while it happens: each thing is seen by the shot that holds it. ----
# wide: 0 door jumps, dust, uniform swings; 1 pen rolls. upper: 2, 3 dust off the lintel. gap: 4 shoes step closer. books: 5 the top book slides.
# phone: 6 lights up, 7 skitters. lever: 8, 9 somebody tries the handle. wide: 10 shoes closer, bottle falls, a shelf book tips.
# gap: 11 shoes closer. panel: 12. wide: 13 shoes at the door, calendar drops on one pin.
def door_angle(t):
    """Degrees around the hinge. The latch side jumps into the room and rattles back; it never goes through the frame."""
    a = 0.0
    for i, k in enumerate(KO):
        if t >= k:
            amp = 1.8 + 1.5 * i / 13
            a = max(a, amp * math.exp(-(t - k) * 13) * abs(math.cos((t - k) * 46)))
    return -a


def book_slide(t):
    return 0.15 * eout((t - KO[5]) / 0.22)


def phone_on(t):
    return t >= KO[6]


def phone_turn(t):
    """Phone turns around the plug end, a jump and then stays."""
    dt = t - KO[7]
    if dt < 0:
        return 0.0
    return 11.0 * eout(dt / 0.14) + 1.2 * math.exp(-dt * 12) * math.sin(dt * 70)


def pen_roll(t):
    """Distance rolled, metres. Starts fast, friction brings it to rest in the dark beyond the wedge."""
    return 0.82 * eout((t - KO[1]) / 1.25, 2.6)


# The shoes in the corridor are real and can be seen through the gap from the floor. They walk in from screen right (on ha, zu, ga), turn to face the door,
# then come closer on knocks 4, 10, 11 and 13. Their shadow in the room is painted (paint_room) from foot_shadows, so that it reads as a pair of shoes.
WALK = (  # plant time, which foot, x, y of the heel, heading (0 faces the door, 90 faces along the corridor towards screen left)
    (170.31, 1, XD + 0.60, 0.70, 90.0),
    (170.77, 0, XD + 0.32, 0.64, 90.0),
    (171.23, 1, XD + 0.10, 0.72, 28.0),
    (171.50, 0, XD - 0.09, 0.72, 0.0),
)
STANCE = (  # from this knock: distance of the toes from the door, half stance; the shadow in the room: length, half width of one shoe
    (None, 0.42, 0.095, 0.50, 0.060),
    (4, 0.31, 0.095, 0.62, 0.072),
    (10, 0.20, 0.090, 0.74, 0.085),
    (11, 0.11, 0.090, 0.86, 0.100),
    (13, 0.05, 0.088, 0.98, 0.118),
)
SHOE_LEN = 0.262
SHADOW_SPLAY = 0.30      # radians away from the door's centre line: the lamp is behind the feet
STANCE_SPLAY = 12.0      # degrees each foot is turned out


def stance_now(t):
    """(toe distance, half stance, shadow length, shadow half width), each step taken in five frames."""
    cur = list(STANCE[0][1:])
    for row in STANCE[1:]:
        u = smooth((t - KO[row[0]]) / 0.16)
        cur = [a_ + (b_ - a_) * u for a_, b_ in zip(cur, row[1:])]
    return cur


def feet_at(t):
    """[(x, y of heel, z lift, heading degrees)] for the two feet. A foot in the air is above the gap, so it leaves the slit of light."""
    far = (XD + 2.2, 0.7, 0.0, 90.0)
    out = [far, far]
    for k, foot, x, y, h in WALK:
        if t >= k - 0.13:
            out[foot] = (x, y, 0.14 * (1 - smooth((t - k + 0.13) / 0.13)), h)
    k = WALK[-1][0]
    if t >= k:
        d, st = stance_now(t)[:2]
        u = smooth((t - k) / 0.16)
        y = DOOR_T + d + SHOE_LEN
        for foot, sx in ((0, -1), (1, 1)):
            x0, y0, z0, h0 = out[foot]
            # toes turned out a little, the way anybody stands: the shoe shows its side as well as its toe
            out[foot] = (x0 + (XD + sx * (st - 0.03) - x0) * u, y0 + (y - y0) * u, z0, h0 * (1 - u) - sx * STANCE_SPLAY * u)
    return out


# one loafer, heel at the origin, toe towards -y: used by Blender and by the 2D shot under the door, so that it is the same shoe.
# along the shoe, half width, height of the upper's top from the floor
_LOAFER = ((0.0, 0.018, 0.046), (0.03, 0.027, 0.056), (0.10, 0.031, 0.058), (0.22, 0.031, 0.052), (0.34, 0.028, 0.052), (0.44, 0.030, 0.062),
           (0.52, 0.034, 0.064), (0.62, 0.039, 0.054), (0.72, 0.042, 0.045), (0.82, 0.041, 0.040), (0.90, 0.034, 0.034), (0.955, 0.023, 0.026),
           (0.985, 0.012, 0.018), (1.0, 0.004, 0.011))


def _catmull_row(rows, k):
    out = []
    for i in range(len(rows) - 1):
        p0, p1, p2, p3 = rows[max(i - 1, 0)], rows[i], rows[i + 1], rows[min(i + 2, len(rows) - 1)]
        for q in range(k):
            x = q / k
            out.append(tuple(0.5 * (2 * b + (c - a) * x + (2 * a - 5 * b + 4 * c - d) * x * x + (3 * b - a - 3 * c + d) * x ** 3) for a, b, c, d in zip(p0, p1, p2, p3)))
    out.append(rows[-1])
    return out


def _sole_z(u):
    """(underside, top) of the sole: a heel block, a raised waist, the tread flat on the floor, the toe springing up a little."""
    if u < 0.25:
        low = 0.0
    elif u < 0.50:
        low = 0.012 * (1 - (u - 0.25) / 0.25)
    else:
        low = 0.0035 * clamp((u - 0.90) / 0.10)
    top = 0.019 + (0.007 - 0.019) * clamp((u - 0.22) / 0.22) + 0.0035 * clamp((u - 0.90) / 0.10)
    return low, top


def _toe_shift(u, side):
    """A real last is not symmetrical: the waist is cut in on the inside, the toe points inwards."""
    return side * (0.004 * math.sin(math.pi * min(u / 0.6, 1.0)) - 0.010 * u * u)


def _arch(u, w, h, side, a, grow=0.0):
    base = _sole_z(u)[1]
    ca, sa = math.cos(a), math.sin(a)
    return (_toe_shift(u, side) + math.copysign(abs(ca) ** 0.62, ca) * (w + grow), base + (h - base + grow) * max(sa, 0.0) ** 0.62)


def _ring(u, w, h, side, n, length, grow=0.0):
    out = []
    for j in range(n + 1):
        x, z = _arch(u, w, h, side, j / n * math.pi, grow)
        out.append((x, -u * length, z))
    return out


# A grown man's shoe stands about 9 cm at the instep. At the old height the whole shoe fitted under the door with room to spare, so the gap looked taller than a shoe.
SHOE_TALL = 1.42


def loafer(length, side):
    """Rings for the upper, the sole and the strap, and the line of the stitched apron. side: +1 when the outside of the foot is towards +x."""
    n = 18
    rows = [(u, w, h * SHOE_TALL) for u, w, h in _catmull_row(_LOAFER, 4)]
    upper, sole = [], []
    for u, w, h in rows:
        upper.append(_ring(u, w, h, side, n, length))
        lo, top = _sole_z(u)
        c = _toe_shift(u, side)
        w2 = w + 0.0018
        sole.append([(c + w2, -u * length, lo), (c + w2, -u * length, top), (c - w2, -u * length, top), (c - w2, -u * length, lo)])
    strap = []
    for u_ in (0.455, 0.47, 0.52, 0.535):
        u, w, h = min(rows, key=lambda r: abs(r[0] - u_))
        strap.append(_ring(u, w, h, side, n, length, 0.0028))
    # the apron: a raised seam round the top of the toe, down each side
    a0 = 0.33 * math.pi
    seam = []
    side_rows = [r for r in rows if 0.56 <= r[0] <= 0.93]
    for u, w, h in side_rows:
        x, z = _arch(u, w, h, side, a0, 0.0012)
        seam.append((x, -u * length, z))
    u, w, h = side_rows[-1]
    for j in range(1, 8):
        x, z = _arch(u + 0.02, w, h, side, a0 + (math.pi - 2 * a0) * j / 8, 0.0012)
        seam.append((x, -(u + 0.02 * math.sin(math.pi * j / 8)) * length, z))
    for u, w, h in reversed(side_rows):
        x, z = _arch(u, w, h, side, math.pi - a0, 0.0012)
        seam.append((x, -u * length, z))
    return dict(upper=upper, sole=sole, strap=strap, seam=seam, slot=(_toe_shift(0.495, side), -0.495 * length, _LOAFER[6][2] * SHOE_TALL + 0.0028))


# one shoe's shadow: position along it from the door to the toe, half width. Heel, narrow waist, ball of the foot, round toe.
SHOE_OUTLINE = ((-0.04, 0.60), (0.04, 0.70), (0.19, 0.72), (0.33, 0.58), (0.45, 0.58), (0.58, 0.84), (0.72, 1.0), (0.84, 0.94), (0.93, 0.72), (0.98, 0.42), (1.0, 0.0))


def foot_shadows(t):
    """World x-y polygons on the floor of the room: one sole-shaped hard shadow per shoe, running from the gap towards her.
    Lying on the floor looking along it, the shape of a sole would only be a jagged sliver, and a fan this wide leaves the frame at once: there each shadow is one clean band from its shoe towards the camera."""
    k1, k0 = WALK[2][0], WALK[3][0]
    if t < k1:
        return []
    d, st, ln, hw = stance_now(t)
    out = []
    for sx, k in ((1, k1), (-1, k0)):
        if t < k:
            continue
        L_ = ln * (0.72 + 0.28 * smooth((t - k) / 0.14))
        if shot_at(t)[1] == "gap":
            x0, w0 = XD + sx * (st + 0.008), SHOE_OUTLINE[0][1] * hw
            x1, w1 = x0 + sx * 0.05, hw * 1.05
            out.append([(x0 - w0, -0.001), (x0 + w0, -0.001), (x1 + w1, -1.3), (x1 - w1, -1.3)])
            continue
        ang = sx * SHADOW_SPLAY
        dx, dy = math.sin(ang), -math.cos(ang)
        nx, ny = -dy, dx
        left, right = [], []
        for u, w in SHOE_OUTLINE:
            W = w * hw * (1 + 0.28 * u)
            px, py = XD + sx * (st + 0.008) + dx * u * L_, dy * u * L_ - 0.001
            left.append((px + nx * W, py + ny * W))
            right.append((px - nx * W, py - ny * W))
        out.append(left + right[-2::-1])
    return out


def corridor_shadows(t):
    """On the corridor floor, between each planted shoe and the door; while they are still walking, on across the room's floor too."""
    out = []
    y_end = 0.0 if t >= WALK[2][0] else -0.5
    planted = {1: WALK[2][0], 0: WALK[3][0]}
    d, st, ln, hw_room = stance_now(t)
    for foot, (x, y, lift, head) in enumerate(feet_at(t)):
        if lift > 0.01 or x > XD + 2:
            continue
        s_, c_ = math.sin(math.radians(head)), math.cos(math.radians(head))
        # toe end of the shoe, and how wide it stands across the light
        ty = y - SHOE_LEN * c_
        tx = x - SHOE_LEN * s_ * 0.5
        hw = 0.043 + 0.05 * abs(s_)
        if t >= planted[foot]:
            # standing: this shadow runs from under the shoe to exactly where its shadow in the room begins, so the two are one shape
            sx = 1 if foot else -1
            xd = XD + sx * (st + 0.008)
            w0 = SHOE_OUTLINE[0][1] * hw_room
            out.append([(tx - hw, y), (tx + hw, y), (xd + w0, 0.0), (xd - w0, 0.0)])
        else:
            k = (LIGHT[1] - y_end) / (LIGHT[1] - ty)
            out.append([(tx - hw, y), (tx + hw, y), (XD + (tx + hw - XD) * k, y_end), (XD + (tx - hw - XD) * k, y_end)])
    return out


# Before they stop at her door, somebody walks up and down the corridor: each brightness step has this one small event in it, on sung syllables.
# (from, to, x of the foot in the corridor): one planted foot at a time, its shadow a hard notch in the light that swings across the floor.
PACE_Y = 0.42
# Somebody is out there the whole time: past on every sung syllable, and each pass stops a little nearer the middle of the door.
PACE = ((164.63, 164.86, XD + 0.20), (164.86, 165.09, XD + 0.04), (165.09, 165.25, XD - 0.13),     # black: right to left across the strip of light
        (165.71, 165.94, XD - 0.17), (165.94, 166.17, XD - 0.05), (166.17, 166.40, XD + 0.07), (166.40, 166.63, XD + 0.19),   # the door: back again
        (167.32, 167.55, XD + 0.21), (167.55, 167.78, XD + 0.09), (167.78, 168.01, XD - 0.03), (168.01, 168.24, XD - 0.15),   # low on the floor: across, close to the lens
        (168.47, 168.70, XD - 0.13), (168.70, 168.93, XD - 0.02),                                   # and back, as far as the door's middle
        (168.93, 169.16, XD + 0.03), (169.39, 169.62, XD + 0.13),                                   # the room: it stands a moment, moves on
        (169.85, 170.31, XD + 0.25))                                                                # on its way back, just coming into the light


def pace_shadows(t):
    for a, b, x in PACE:
        if a <= t < b:
            k = (LIGHT[1] + 1.3) / (LIGHT[1] - PACE_Y)
            hw = 0.07
            return [[(x - hw, PACE_Y), (x + hw, PACE_Y), (XD + (x + hw - XD) * k, -1.3), (XD + (x - hw - XD) * k, -1.3)]]
    return []


def uniform_swing(t):
    a = 0.0
    for i, k in enumerate(KO):
        dt = t - k
        if dt >= 0:
            # the first knock sets it swinging; each one after gives it another small shove
            a += (8.0 if i == 0 else 1.6) * math.exp(-dt * (1.0 if i == 0 else 2.4)) * math.sin(dt * 6.6)
    return a


def shelf_tip(t):
    dt = t - KO[10]
    if dt < 0:
        return 0.0
    return 15.0 * clamp(dt / 0.20) ** 2 - 1.6 * math.exp(-max(dt - 0.20, 0) * 16) * math.sin(max(dt - 0.20, 0) * 40)


def lever_dip(t):
    """Someone tries the handle, three times: it goes down hard, stays a moment, comes back up."""
    out = 0.0
    for k, dip in ((KO[8], 30.0), (KO[9], 40.0), (KO[12], 34.0)):
        dt = t - k
        if dt >= 0:
            out = max(out, dip * smooth(dt / 0.07) * (1 - smooth((dt - 0.17) / 0.09)))
    # any knock also rattles it loosely in its rose
    for k in KO:
        dt = t - k
        if dt >= 0:
            out = max(out, 5.0 * math.exp(-dt * 20) * abs(math.sin(dt * 60)))
    return out


def bottle_fall(t):
    dt = t - KO[10]
    if dt < 0:
        return 0.0
    if dt < 0.26:
        return 90.0 * (dt / 0.26) ** 2
    return 90.0 + 3.5 * math.exp(-(dt - 0.26) * 16) * math.sin((dt - 0.26) * 45) * -1


def calendar_drop(t):
    dt = t - KO[13]
    if dt < 0:
        return 0.0
    return 13.0 + 13.0 * (-math.exp(-dt * 4.5) * math.cos(dt * 11))


# dust: a burst per entry, drawn by the overlay as short falling lines. (knock index, how many, spread along the lintel)
DUST = ((0, 20, 0.36), (1, 8, 0.30), (2, 26, 0.38), (3, 14, 0.36), (12, 22, 0.38), (13, 26, 0.40))
DUST_TOP = DOOR_H + 0.07


def dust_points(t):
    """[(x, y, z top, z bottom)]: short streaks falling off the top of the door casing, slowing as air takes them, gone before the floor."""
    import random
    out = []
    for k, n, sp in DUST:
        dt = t - KO[k]
        if dt < 0 or dt > 1.6:
            continue
        r = random.Random(k * 13 + 7)
        for j in range(n):
            x0 = XD + r.uniform(-sp, sp)
            delay = r.uniform(0, 0.10)
            v = r.uniform(0.7, 1.7)
            life = r.uniform(0.22, 0.95)
            ln = r.uniform(0.015, 0.05)
            dj = dt - delay
            if dj < 0 or dj > life:
                continue
            z = DUST_TOP - v * (dj - 0.28 * dj * dj)
            if z < 0.02:
                continue
            x = x0 + 0.012 * math.sin(dj * r.uniform(2, 5) + j)
            y = -0.05 - 0.04 * dj - 0.02 * r.random()
            out.append((x, y, z + ln * (0.5 + 0.5 * v), z))
    return out


# ---- her view ----
def creep(t):
    """How far she has shuffled back: a slow drift and a flinch on each knock. Stops when the knocking stops."""
    u = 0.42 * smooth(seg(t, T0 + 1.0, LAST_KNOCK + 0.6)) ** 0.9
    for k in KO:
        u += 0.021 * eout((t - k) / 0.30)
    return u


# the cutting plan: (from this time, shot). Every cut is on a sung syllable or a knock.
PLAN = (
    (0.0, "wide"),            # black, one line of light; then the door
    (STEPS[1], "floor"),      # low on the floor: her clothes, a book, the phone's cable
    (STEPS[2], "wide"),       # the whole room
    (WALK[0][0], "gap"),      # flat on the floor, under the door: shoes walk up and stop
    (KO[0], "wide"),          # first knocks: the door jumps
    (KO[2], "upper"),         # the door square on, its leaf jumping in the frame, light at the cracks, dust off the lintel
    (KO[4], "gap"),           # they step closer
    (KO[5], "books"),         # a book slides
    (KO[6], "phone"),         # her phone lights up and jumps
    (KO[8], "lever"),         # somebody tries the handle, twice
    (KO[10], "wide"),         # further back now
    (KO[11], "gap"),          # closer
    (KO[12], "panel"),        # the door, full frame
    (KO[13], "wide"),         # further back still
    (178.21, "gap"),          # the knocking has stopped. They have not gone.
    (T1, "mid"),              # a sheet comes in under the door
    (CLOSE[0], "close"),
    (CLOSE[1], "foot"),
    (T2, "plate"),            # not in the film as such: stills of the door behind the 2D section, rendered once at t = 200 + index (see s11b)
)
# Square on to the door. Pixels per metre on its plane, x and height looked at, distance. s11b lays its paper over these.
# Across the room to see that it is a door, covered; right up against it where the arm is in the picture, because her body is out of frame only that close.
PLATE_VIEWS = (
    (400.0, XD, 0.75, 2.93),
    (1250.0, XD + 0.18, 0.88, 1.2),
    (1400.0, XD - 0.20, 1.30, 1.2),
    (1250.0, XD + 0.10, 0.42, 1.2),
    (470.0, XD, 0.72, 2.93),
    (1430.0, 0.446, 1.0, 1.2),     # the wall of paper, with the handle in a gap
)
GAP_LENS = ((WALK[0][0], 48.0), (KO[4], 60.0), (KO[11], 74.0))
GAP_DIST = 1.05
SHOT_LENS = dict(floor=26.0, upper=18.5, books=31.0, phone=36.0, lever=34.0, panel=28.0, mid=30.0, close=42.0)


def shot_at(t):
    cur = PLAN[0]
    for row in PLAN:
        if t >= row[0]:
            cur = row
    return cur


def _jolt(t, size=1.0):
    """A knock also shakes the floor she sits on: a hard jump of the frame that dies at once."""
    j = 0.0
    for k in KO:
        if t >= k:
            j = max(j, size * math.exp(-(t - k) * 16))
    return j


def camera_at(t):
    start, shot = shot_at(t)
    if shot == "plate":
        pm, cx, cz, d_ = PLATE_VIEWS[int(round(t - 200.0))]
        return (cx, -d_, cz), (cx, 0.0, cz), (0.0, 0.0, 1.0)
    b = creep(t)
    breath = 0.006 * math.sin(t * 1.9)
    if shot == "close":
        # above the first sheet, from her side, a slow lean in
        c = sheet_pose(0, CLOSE[0] + 5)
        d = 0.68 - 0.06 * smooth(seg(t, CLOSE[0], CLOSE[1]))
        return (c[0] + 0.025, c[1] - d * 0.62, d * 0.78), (c[0] + 0.0, c[1] + 0.045, 0.0), (0.0, 0.0, 1.0)
    if shot == "foot":
        return (-0.06 - 0.03 * b, -2.38 - b, 0.60 - 0.05 * b + breath), (0.27, -0.20, 0.16 + breath * 0.4), (0.012, 0.0, 1.0)
    if shot == "gap":
        # from far along the floor, on a long lens: the light is the same narrow wedge as in the wide shot, with the dark floor in front of it. The horizon stays 120 px below the middle of the frame.
        j = _jolt(t, 0.0035)
        ex = XD + 0.015
        f = lens_at(t) / 36 * 1920
        return (ex, -GAP_DIST, 0.028 + j), (ex, 0.0, 0.028 + j + 120 / f * GAP_DIST), (0.0, 0.0, 1.0)
    if shot == "floor":
        v = smooth(seg(t, STEPS[1], STEPS[2]))
        return (-0.25 + 0.02 * v, -1.72 + 0.05 * v, 0.155), (0.06, -0.40, 0.02), (0.0, 0.0, 1.0)
    if shot == "upper":
        # square on, level, so that it stands up: from the lever to above the lintel. The camera hardly moves: the leaf does.
        j = _jolt(t, 0.0015)
        return (XD - 0.02, -1.2, 1.50 + j), (XD - 0.02, 0.0, 1.50 + j), (0.0, 0.0, 1.0)
    if shot == "books":
        j = _jolt(t, 0.004)
        return (0.60, -1.17, 0.19 + j), (0.92, -0.70, 0.065 + j), (-0.015, 0.0, 1.0)
    if shot == "phone":
        j = _jolt(t, 0.005)
        return (-0.79, -1.57, 0.36 + j), (-0.66, -1.20, j), (0.0, 0.0, 1.0)
    if shot == "lever":
        j = _jolt(t, 0.004)
        return (0.34, -0.60, 0.80 + j), (0.60, 0.0, 0.965 + j), (0.0, 0.0, 1.0)
    if shot == "panel":
        j = _jolt(t, 0.010)
        return (XD - 0.03, -1.28, 0.72 + j), (XD - 0.01, 0.0, 0.66 + j * 1.5), (-0.01, 0.0, 1.0)
    if shot == "mid":
        v = smooth(seg(t, T1, CLOSE[0]))
        return (0.34, -1.42 + 0.10 * v, 0.56 - 0.03 * v), (0.37, -0.30, 0.03), (0.008, 0.0, 1.0)
    # wide
    jolt = _jolt(t, 0.012)
    return (-0.06 - 0.03 * b, -2.38 - b, 0.60 - 0.05 * b + breath - jolt), (-0.16, 0.0, 0.70 + breath * 0.5 - jolt * 2.4), (0.012, 0.0, 1.0)


def lens_at(t):
    start, shot = shot_at(t)
    if shot == "plate":
        pm, cx, cz, d_ = PLATE_VIEWS[int(round(t - 200.0))]
        return pm * d_ / 1920 * 36
    if shot == "gap":
        cur = GAP_LENS[0][1]
        for k, v in GAP_LENS:
            if t >= k:
                cur = v
        return cur
    if shot == "foot":
        return 44.0 + 9.0 * smooth(seg(t, CLOSE[1], T2))     # back from the close view: on the door's foot, still tightening
    return SHOT_LENS.get(shot, LENS)


def project(p, t):
    """World point to pixels at 1920x1080."""
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
    k = lens_at(t) / 36.0
    return 960 + dot(v, r) / z * k * 1920, 540 - dot(v, u) / z * k * 1920, z


# ---- sheets under the door (11) ----
# start, duration of the slide, final x, final y, final angle in degrees
SHEETS = [
    (179.50, 0.86, 0.360, -0.60, -4.0),    # the one she reads, between the two shadows
    (181.92, 0.62, 0.400, -0.415, 9.0),    # comes in during the close view, stops just short of the first
    (182.84, 0.70, 0.240, -0.32, -13.0),
    (183.30, 0.62, 0.500, -0.26, 16.0),
    (183.76, 0.70, 0.270, -0.80, 7.0),
    (184.22, 0.60, 0.470, -0.84, -14.0),
    (184.68, 0.58, 0.330, -0.18, 23.0),
    (185.14, 0.52, 0.140, -0.58, 26.0),
    (185.37, 0.46, 0.560, -0.55, -8.0),
    (185.60, 0.46, 0.400, -0.98, 12.0),
    (185.83, 0.42, 0.240, -0.47, -20.0),
    (186.06, 0.40, 0.460, -0.14, -6.0),
    (186.29, 0.26, 0.340, -0.30, 14.0),
]
SHEET_Y0 = 0.17          # centre of the sheet at the moment it is let go, on the corridor side


def sheet_pose(i, t):
    """(x, y, z, angle degrees) or None before it comes in. A flick: fast at first, the floor slows it."""
    s, dur, x1, y1, a1 = SHEETS[i]
    if t < s:
        return None
    u = eout((t - s) / dur, 2.8)
    x0 = XD + (x1 - XD) * 0.25
    x = x0 + (x1 - x0) * u
    y = SHEET_Y0 + (y1 - SHEET_Y0) * u
    a = a1 * (0.25 + 0.75 * u)
    return x, y, 0.0011 + 0.00025 * i, a


def sheet_axes(i, t):
    """Image corners in world: top left, top right, bottom left. The top of the picture is towards the door, so it faces her."""
    p = sheet_pose(i, t)
    if p is None:
        return None
    x, y, z, a = p
    r = math.radians(a)
    ux, uy = math.cos(r), math.sin(r)
    vx, vy = -uy, ux
    w, h = SHEET_W / 2, SHEET_H / 2
    tl = (x - ux * w + vx * h, y - uy * w + vy * h, z)
    tr = (x + ux * w + vx * h, y + uy * w + vy * h, z)
    bl = (x - ux * w - vx * h, y - uy * w - vy * h, z)
    return tl, tr, bl


def _hand_outline():
    """A hand flat on the floor, as a shadow from behind it: x across, y from the wrist (+) to the fingertips (-). Four fingers with round ends; the thumb is under the palm."""
    fingers = ((-0.047, 0.0092, -0.066), (-0.016, 0.0102, -0.092), (0.016, 0.0100, -0.088), (0.045, 0.0086, -0.062))
    pts = [(-0.060, 0.17), (-0.060, 0.03)]
    for cx, w, tip in fingers:
        # a finger tapers from its knuckle to its tip, and there is hardly a gap at the root
        pts.append((cx - w * 1.45, 0.006))
        for k in range(9):
            a = math.pi * k / 8
            pts.append((cx - w * math.cos(a), tip + w * 1.1 * (1 - math.sin(a))))
        pts.append((cx + w * 1.45, 0.006))
    pts += [(0.058, 0.03), (0.064, 0.17)]
    return tuple(pts)


HAND = _hand_outline()


def hand_shadow(t):
    """A hand lets each of the first sheets go at the gap. Only its shadow is seen: fingers on the floor, eight frames in, five frames out. World x-y polygons."""
    for s_, dur, x1, y1, a1 in SHEETS[:5]:
        lead, tail = 8 / 30, 5 / 30
        if s_ - lead <= t < s_ + tail:
            x0 = XD + (x1 - XD) * 0.25
            out = smooth((t - (s_ - lead)) / lead) * (1 - smooth((t - s_) / tail))
            tip = -0.34 * out
            return [[(x0 + px * 1.35, tip + py * 1.5 + 0.21 * (1 - out)) for px, py in HAND] + [(x0 + 0.12, 0.03), (x0 - 0.10, 0.03)]]
    return []


def frames_all():
    return list(range(0, int(round((T1 - T0) * 60)), 2))   # the film runs at 30 fps
