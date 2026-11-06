"""Curves and brush lines for the last shot, in close-up picture pixels. Only numpy: used by the build of the head and in the clip."""
import numpy as np


def spline(pts, n=24):
    """Catmull-Rom through the points (centripetal), n samples per span. Sharp corners: call it once per side."""
    p = np.asarray(pts, np.float64)
    if len(p) == 2:
        t = np.linspace(0, 1, n)[:, None]
        return p[0] * (1 - t) + p[1] * t
    q = np.vstack([2 * p[0] - p[1], p, 2 * p[-1] - p[-2]])
    out = []
    for i in range(1, len(q) - 2):
        p0, p1, p2, p3 = q[i - 1], q[i], q[i + 1], q[i + 2]
        t0 = 0.0
        t1 = t0 + np.linalg.norm(p1 - p0) ** 0.5 + 1e-6
        t2 = t1 + np.linalg.norm(p2 - p1) ** 0.5 + 1e-6
        t3 = t2 + np.linalg.norm(p3 - p2) ** 0.5 + 1e-6
        t = np.linspace(t1, t2, n, endpoint=i == len(q) - 3)[:, None]
        a1 = (t1 - t) / (t1 - t0) * p0 + (t - t0) / (t1 - t0) * p1
        a2 = (t2 - t) / (t2 - t1) * p1 + (t - t1) / (t2 - t1) * p2
        a3 = (t3 - t) / (t3 - t2) * p2 + (t - t2) / (t3 - t2) * p3
        b1 = (t2 - t) / (t2 - t0) * a1 + (t - t0) / (t2 - t0) * a2
        b2 = (t3 - t) / (t3 - t1) * a2 + (t - t1) / (t3 - t1) * a3
        out.append((t2 - t) / (t2 - t1) * b1 + (t - t1) / (t2 - t1) * b2)
    return np.vstack(out)


def normals(c):
    d = np.gradient(c, axis=0)
    d /= np.linalg.norm(d, axis=1, keepdims=True) + 1e-9
    return np.c_[-d[:, 1], d[:, 0]]


def arclen(c):
    s = np.r_[0, np.cumsum(np.linalg.norm(np.diff(c, axis=0), axis=1))]
    return s / max(s[-1], 1e-6)


def brush(c, w):
    """A brush line along curve c as a closed polygon. w: width as a list of (u, width) over the line's length, or a number."""
    u = arclen(c)
    if np.isscalar(w):
        ww = np.full(len(c), float(w))
    else:
        us, vs = zip(*w)
        ww = np.interp(u, us, vs)
    n = normals(c) * ww[:, None] / 2
    return np.vstack([c + n, (c - n)[::-1]])
