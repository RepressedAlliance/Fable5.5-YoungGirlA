"""The school gate: timing, camera and where the gear stands. Plain Python."""
import json
import math
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SS = 1.5
T0, T1 = 681 / 30, 902 / 30
L = json.loads((ROOT / "work" / "analysis" / "lyrics_timed.json").read_text(encoding="utf-8"))
LINE_T = [L[i]["syl"][0]["t"] for i in (0, 1, 2, 3)]
_A = json.loads((ROOT / "work" / "analysis" / "audio.json").read_text())
BEAT0, BP = _A["beat0"], _A["beat_period"]
LENS = 50.0
SUN = (0.50, -0.80, -0.36)     # low, behind the school: long hard shadows come towards us and to the right
AIM = (0.0, 0.0, 1.35)         # every lens points at the middle of the door
DOOR_W, DOOR_H = 4.4, 2.2


def clamp(x, a=0.0, b=1.0):
    return max(a, min(b, x))


def smooth(x):
    x = clamp(x)
    return x * x * (3 - 2 * x)


def camera_at(t):
    """A slow crane: a road-level view of the shut door rises until the gear is laid out like a plan."""
    u = smooth((t - T0 + 1.0) / (T1 - T0 + 2.0))
    eye = (0.7 - 1.4 * u, -23.5 + 1.0 * u, 1.45 + 6.0 * u)
    target = (0.0, -0.5 - 2.5 * u, 1.75 - 0.75 * u)
    return eye, target, (0, 0, 1)


def project(p, t, lens=LENS, cam=None):
    eye, tg, up = cam or camera_at(t)

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
    k = lens / 36.0 * 1920
    return 960 + dot(v, r) / z * k, 540 - dot(v, u) / z * k, z


def gear():
    """Two arcs of tripods facing the gate. Fixed by seed so the shot, the painter and the outro's marks agree."""
    r = random.Random(19)
    out = []
    # a clear lane is left down the middle: everyone wants the same line to the door
    # front row: flash cameras and video cameras in turn, on low tripods
    for i, deg in enumerate((-50, -37, -24, -13, 13, 24, 37, 50)):
        a = math.radians(deg) + r.uniform(-0.02, 0.02)
        rad = 6.6 + r.uniform(-0.25, 0.25)
        out.append(dict(kind="still" if i % 2 == 0 else "video", x=rad * math.sin(a), y=-rad * math.cos(a), h=1.30 + r.uniform(-0.05, 0.05), turn=r.uniform(0, 2)))
    # back row: mostly video cameras on tall tripods, a few metres behind and between
    for i, deg in enumerate((-44, -32, -21, -11, 11, 21, 32, 44)):
        a = math.radians(deg) + r.uniform(-0.015, 0.015)
        rad = 10.0 + r.uniform(-0.3, 0.3)
        out.append(dict(kind="video" if i % 3 else "still", x=rad * math.sin(a), y=-rad * math.cos(a), h=1.62 + r.uniform(-0.04, 0.06), turn=r.uniform(0, 2)))
    return out


GEAR = gear()


def aim_angles(g):
    dx, dy, dz = AIM[0] - g["x"], AIM[1] - g["y"], AIM[2] - g["h"]
    yaw = math.atan2(dx, dy)
    pitch = math.atan2(dz, math.hypot(dx, dy))
    return yaw, pitch


def local_to_world(g, lx, ly, lz):
    yaw, pitch = aim_angles(g)
    cp, sp = math.cos(pitch), math.sin(pitch)
    y1, z1 = ly * cp - lz * sp, ly * sp + lz * cp
    cy, sy = math.cos(-yaw), math.sin(-yaw)
    return g["x"] + lx * cy - y1 * sy, g["y"] + lx * sy + y1 * cy, g["h"] + z1


# Every lens in the street turns at once, with nobody at any of them: each move is taken in five frames, on a sung syllable, and held.
# (time, degrees from the door, positive anticlockwise seen from above)
PANS = ((LINE_T[0] + 1.01, -17.0), (LINE_T[1] + 1.01, 15.0), (LINE_T[2] + 0.78, -24.0), (LINE_T[3] + 0.55, 21.0), (LINE_T[3] + 1.12, 0.0))


def pan_at(t):
    a = 0.0
    for k, deg in PANS:
        x = clamp((t - k) / (5 / 30))
        a += (deg - a) * (1 - (1 - x) ** 3)
    return a


def _spun(g, p, t):
    """A point fixed to a rig, carried round the head of its tripod."""
    r = math.radians(pan_at(t))
    c, si = math.cos(r), math.sin(r)
    dx, dy = p[0] - g["x"], p[1] - g["y"]
    return g["x"] + dx * c - dy * si, g["y"] + dx * si + dy * c, p[2]


def flash_head(g, t=T0):
    """Where a still camera's flash sits, in the world, at this moment."""
    return _spun(g, local_to_world(g, 0.0, 0.05, 0.215), t)


def aim_point(g, t):
    """Where this camera's lens points at this moment: the door, turned with the pan."""
    return _spun(g, AIM, t)


STILLS = [i for i, g in enumerate(GEAR) if g["kind"] == "still"]
# which cameras fire, and when: three as each line starts, a shutter apart, and one on every beat in between, going to two and then three by the last line
FLASHES = []
_r = random.Random(4)
for k, lt in enumerate(LINE_T):
    pick = _r.sample(STILLS, 3)
    for j, idx in enumerate(pick):
        FLASHES.append((lt + j * 0.1, idx))
_n = math.ceil((LINE_T[0] - BEAT0) / BP)
while BEAT0 + _n * BP < T1 - 0.1:
    _b = BEAT0 + _n * BP
    _n += 1
    if min(abs(_b - lt) for lt in LINE_T) < 0.25:
        continue
    _how = sum(1 for lt in LINE_T[2:] if _b >= lt) + 1
    for j, idx in enumerate(_r.sample(STILLS, _how)):
        FLASHES.append((_b + j * 0.067, idx))
FLASHES.sort()


def flash_level(t):
    """1 on the frame a flash fires, half on the next, then nothing. Hard steps, 30 fps."""
    lv = 0.0
    for ft, _ in FLASHES:
        d = t - ft
        if -1e-3 <= d < 1 / 30 - 1e-3:
            lv = max(lv, 1.0)
        elif 1 / 30 - 1e-3 <= d < 2 / 30 - 1e-3:
            lv = max(lv, 0.45)
    return lv


def frames_all():
    return list(range(0, int(round((T1 - T0) * 60)), 2))
