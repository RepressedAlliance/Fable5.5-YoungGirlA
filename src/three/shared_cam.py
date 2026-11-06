"""World point to 1920x1080 pixels, for any (eye, target, up, lens). Plain Python."""
import math


def project(p, cam, lens):
    eye, tg, up = cam

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
