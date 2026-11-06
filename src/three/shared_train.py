"""The carriage. Plain Python: timing, the sway everything shares, the camera."""
import json
import math
from pathlib import Path

import shared_cam

ROOT = Path(__file__).resolve().parents[2]
SS = 1.5
T0, T1 = 1123 / 30, 1344 / 30
L = json.loads((ROOT / "work" / "analysis" / "lyrics_timed.json").read_text(encoding="utf-8"))
LINE_T = [L[i]["syl"][0]["t"] for i in (8, 9, 10, 11)]
_A = json.loads((ROOT / "work" / "analysis" / "audio.json").read_text())
BEAT0, BP = _A["beat0"], _A["beat_period"]
LENS = 21.0
SUN = (0.05, 0.16, -0.98)      # the carriage's own lights: straight down, shadows short and all one way

# the car: x across, y along, z up
HW, LEN, CEIL = 1.42, 20.0, 2.32
DOORS = ((3.6, 4.9), (9.6, 10.9), (15.6, 16.9))
BENCHES = ((0.2, 3.5), (5.0, 9.5), (11.0, 15.5), (17.0, 19.8))
AD_ROWS = tuple(2.7 + 2.2 * k for k in range(8))
AD_W, AD_H = 0.74, 0.508
AD_TOP = 2.09
AD_PIVOT = 2.16
STRAP_X = 0.83                 # outside the ads' reach: at 0.74 the rail ran through the corner of each ad and hid its last characters
STRAP_Z = 1.98


def clamp(x, a=0.0, b=1.0):
    return max(a, min(b, x))


def sway(t):
    """One value for the whole carriage: everything hanging swings together, reaching its ends on the beats."""
    return math.sin(2 * math.pi * (t - BEAT0) / (4 * BP))


# Hard cuts on the sung lines. Two lines of the whole empty car, then in on the ads themselves: a passenger's view from
# the seat, the paper swinging in the frame. (shot start, pivot row, lens x, lens back from the row, lens height)
CUTS = (LINE_T[2], LINE_T[3])
CLOSE = ((LINE_T[2], 2.7, 0.04, 0.86, 1.47), (LINE_T[3], 7.1, 0.34, 0.84, 1.38))
CLOSE_LENS = 30.0


def close_at(t):
    out = None
    for c in CLOSE:
        if t >= c[0] - 1e-6:
            out = c
    return out


def lens_at(t, t0=None):
    return CLOSE_LENS if t0 is None and close_at(t) else LENS


def camera_at(t, t0=None):
    if t0 is None and (c := close_at(t)):
        # looking up at one ad from below it and a little to the side; only the car's own sway moves the lens
        _, ry, ex, back, ez = c
        s = sway(t - 0.08)
        drift = 0.012 * (t - c[0])
        r = math.radians(0.7 * s)
        eye = (ex + 0.010 * s, ry - back + drift, ez)
        return eye, (0.40, ry, 1.80), (math.sin(r), 0.0, math.cos(r))
    t0 = T0 if t0 is None else t0
    s = sway(t - 0.08)
    y = 0.55 + 0.20 * (t - t0)
    roll = 0.55 * s
    eye = (0.05 + 0.012 * s, y, 1.40 + 0.004 * abs(s))
    target = (0.0, y + 8.0, 1.60)
    r = math.radians(roll)
    return eye, target, (math.sin(r), 0.0, math.cos(r))


def project(p, t):
    return shared_cam.project(p, camera_at(t), lens_at(t))


def frames_all():
    return list(range(0, int(round((T1 - T0) * 60)), 2))
