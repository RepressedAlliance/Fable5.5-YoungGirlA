"""Timing and camera for clip 3 (tooi x14). Plain Python: used by Blender, the painter and the 2D overlay."""
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SS = 1.5
T0, T1 = 2439 / 30, 96.0
L = json.loads((ROOT / "work" / "analysis" / "lyrics_timed.json").read_text(encoding="utf-8"))
HIT_T = [s["t"] for i in (23, 24, 25) for s in L[i]["syl"] if s["text"].strip() == "to"][:14]
assert len(HIT_T) == 14
STOP = 93.52
FLAT_END = 95.59
LENS = 26.0
ICON_AT = 150          # her height on screen, in pixels, at which the small mark replaces the figure
D0, D1 = 1.62, 1750.0
D_FAR = 6.5            # the push towards her starts here, from the front of the room
EL_FAR = 13.5          # low enough that the far end of the push stays under the room's ceiling height
AZ_FAR = 15.0
HER_XY = (-1.65, 2.95)        # lap position on her chair
HER_HEAD = (-1.65, 2.72, 1.05)
SUN = (0.80, -0.40, -0.45)


def clamp(x, a=0.0, b=1.0):
    return max(a, min(b, x))


def seg(t, a, b):
    return clamp((t - a) / (b - a))


def smooth(x):
    x = clamp(x)
    return x * x * x * (x * (6 * x - 15) + 10)


def distance_at(t):
    """Log distance runs at a steady rate, with one small push per sung word on top. It never stalls."""
    if t < HIT_T[0]:
        # one slow push that comes to rest exactly where the pull begins, on the first word
        return math.exp(math.log(D0) + math.log(D_FAR / D0) * (1 - seg(t, T0, HIT_T[0])) ** 2)
    # the steady pull eases in and eases out over several frames: no start or stop on a single frame
    span = STOP - HIT_T[0]
    ramp = 0.45

    def area(x):
        x = max(0.0, min(span, x))
        if x < ramp:
            return x * x / (2 * ramp)
        if x > span - ramp:
            y = span - x
            return span - ramp - y * y / (2 * ramp)
        return x - ramp / 2

    u = area(t - HIT_T[0]) / (span - ramp)
    steps = 0.0
    for k in HIT_T:
        steps += 1 - (1 - clamp((t - k) / 0.26)) ** 3
    steps /= len(HIT_T)
    k = 0.88 * u + 0.12 * steps
    return math.exp(math.log(D0) + (math.log(D1) - math.log(D0)) * k)


def elevation_at(t):
    d = distance_at(t)
    if t < HIT_T[0]:
        return 24 - (24 - EL_FAR) * clamp(math.log(d / D0) / math.log(D_FAR / D0))
    x = clamp((math.log(d) - math.log(6)) / (math.log(400) - math.log(6)))
    el = 24 + 36 * smooth(x)
    el += (90 - el) * smooth(seg(t, STOP, FLAT_END - 0.3))
    return el


def azimuth_at(t):
    if t < HIT_T[0]:
        return AZ_FAR * (1 - smooth(seg(t, T0, HIT_T[0])))
    return 0.0 + 22 * smooth(seg(t, HIT_T[3], FLAT_END))


def camera_at(t):
    d = distance_at(t)
    el = math.radians(elevation_at(t))
    az = math.radians(azimuth_at(t))
    c = (HER_HEAD[0], HER_HEAD[1] + 0.05, HER_HEAD[2] - 0.15)
    eye = (c[0] + d * math.cos(el) * math.sin(az), c[1] + d * math.cos(el) * math.cos(az), c[2] + d * math.sin(el))
    # up: towards the back of the room, fades to a fixed heading when looking straight down
    up = (-math.sin(az), -math.cos(az), 0.0) if el > math.radians(89.9) else (0.0, 0.0, 1.0)
    if el > math.radians(70):
        k = smooth((el - math.radians(70)) / math.radians(20))
        up = (-math.sin(az) * k, -math.cos(az) * k, 1 - k)
        n = math.sqrt(sum(v * v for v in up)) or 1
        up = tuple(v / n for v in up)
    return eye, c, up


def project(p, t):
    """World point to pixel coordinates at 1920x1080."""
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


def flatten_at(t):
    """Height scale of the town. Grows a little so it reads from far away, then sinks to nothing."""
    grow = 1 + 0.7 * smooth(seg(t, HIT_T[6], STOP))
    sink = 1 - smooth(seg(t, STOP + 0.15, FLAT_END))
    return grow * sink


def mapmix_at(t):
    return smooth(seg(t, STOP + 0.5, FLAT_END + 0.15))


def roof_on(t):
    return t >= HIT_T[5]


def frames_all():
    return list(range(0, int(round((T1 - T0) * 60)), 2))   # the film runs at 30 fps
