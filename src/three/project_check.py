"""Where does each word block land on screen at the moment it lands? Plain Python."""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import shared_c2 as S  # noqa: E402


def project(p, eye, target, up, lens=26.0):
    def sub(a, b): return [x - y for x, y in zip(a, b)]
    def dot(a, b): return sum(x * y for x, y in zip(a, b))
    def cross(a, b): return [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]]
    def norm(a):
        n = math.sqrt(dot(a, a)) or 1
        return [x / n for x in a]
    f = norm(sub(target, eye))
    r = norm(cross(f, up))
    u = cross(r, f)
    d = sub(p, eye)
    z = dot(d, f)
    if z <= 0:
        return None
    k = lens / 36.0
    x = dot(d, r) / z * k
    y = dot(d, u) / z * k
    return (0.5 + x, 0.5 - y * 16 / 9), z


for i, (t, h) in enumerate(zip(S.HIT_T, S.HITS)):
    e, tg, up = S.camera_at(t)
    pr = project(h["p"], e, tg, up)
    if pr:
        (sx, sy), z = pr
        size_frac = h["size"] / z * (26 / 36)
        flag = "" if 0.05 < sx < 0.95 and 0.05 < sy < 0.95 else "  <-- OFF"
        print(f"{i + 1:2d} t={t:.2f} eye=({e[0]:.1f},{e[1]:.1f},{e[2]:.1f}) screen=({sx:.2f},{sy:.2f}) dist={z:.1f} width_frac={size_frac:.2f}{flag}")
    else:
        print(i + 1, t, "BEHIND")
