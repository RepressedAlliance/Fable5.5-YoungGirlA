"""Her hand wiping the bar off her eyes, drawn in the same language as her face in p05_face_close: one flat skin tone, a bold
black line with a little weight to it, no knuckles, tendons, creases or nails. Small, soft, fourteen. Drawn from numbers, so
all the drawings are one hand and the pose changes only as much as it should.
Usage: make_wipe_hand.py [outdir] [--scale 1.0] [--shade]    Prints the WIPE table for c6.py.
"""
import argparse
import json
import math
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
SS = 4
SKIN = (0xFD / 255, 0xE8 / 255, 0xDA / 255)
SKIN_SHADE = (0.86, 0.73, 0.70)
CLOTH = (1.0, 1.0, 1.0)
INK = (0.0, 0.0, 0.0)

# along the hand from the wrist (u), across it towards the little finger (v). Pixels of the 1920 frame.
PALM = 150
# base v, base u, length, width at the base, fan in degrees
FINGERS = (("index", -60, 2, 150, 45, -3.0), ("middle", -18, 8, 172, 45, -0.8), ("ring", 24, 6, 156, 43, 1.5), ("little", 62, -6, 118, 38, 5.0))


def smooth(points, closed=True, n=20):
    """Catmull-Rom through the points."""
    p = np.asarray(points, np.float64)
    N = len(p)
    out = []
    for i in range(N if closed else N - 1):
        p0, p1, p2, p3 = p[(i - 1) % N if closed else max(i - 1, 0)], p[i], p[(i + 1) % N if closed else i + 1], p[(i + 2) % N if closed else min(i + 2, N - 1)]
        for s in np.linspace(0, 1, n, endpoint=False):
            out.append(0.5 * (2 * p1 + (p2 - p0) * s + (2 * p0 - 5 * p1 + 4 * p2 - p3) * s * s + (3 * p1 - p0 - 3 * p2 + p3) * s ** 3))
    return np.array(out)


def finger_outline(v0, u0, length, w, fan, curl):
    """One finger in (u, v): soft, tapering, with a rounded tip, bending a little towards the little finger as it goes."""
    a = math.radians(fan)
    ss = np.linspace(0, 1, 40)
    cu = u0 + length * ss * math.cos(a)
    cv = v0 + length * ss * math.sin(a) + curl * length * ss ** 2
    du, dv = np.gradient(cu), np.gradient(cv)
    nn = np.hypot(du, dv)
    nu, nv = -dv / nn, du / nn
    half = w / 2 * (1 - 0.34 * ss ** 1.4)
    left = np.stack([cu + nu * half, cv + nv * half], 1)
    right = np.stack([cu - nu * half, cv - nv * half], 1)
    th = np.linspace(math.pi / 2, -math.pi / 2, 16)[1:-1]
    r = half[-1]
    d = math.atan2(dv[-1], du[-1])
    cap = np.stack([cu[-1] + r * np.cos(th + d) * 1.15, cv[-1] + r * np.sin(th + d)], 1)
    return np.concatenate([left, cap, right[::-1]])


def palm_outline():
    return smooth([(-30, -46), (40, -62), (100, -80), (PALM + 12, -82), (PALM + 18, 0), (PALM + 8, 80), (90, 80), (30, 62), (-30, 46)])


class Canvas:
    def __init__(self, x0, y0, w, h):
        self.x0, self.y0, self.w, self.h = x0, y0, w, h

    def mask(self, polys):
        m = np.zeros((self.h * SS, self.w * SS), np.uint8)
        for p in polys:
            q = ((np.asarray(p) - (self.x0, self.y0)) * SS).astype(np.int32)
            cv2.fillPoly(m, [q], 1, lineType=cv2.LINE_8)
        return m


def disc(r):
    r = int(round(r))
    return cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * r + 1, 2 * r + 1))


def soften(m, r):
    """Round every corner of a mask, inside and out."""
    b = cv2.GaussianBlur(m.astype(np.float32), (0, 0), r)
    return (b > 0.5).astype(np.uint8)


def shift(m, dx, dy):
    return cv2.warpAffine(m, np.float32([[1, 0, dx], [0, 1, dy]]), (m.shape[1], m.shape[0]))


def lens(a, b, wa, wb, n=24):
    """A tapering stroke from a to b, the way the lines on her face end."""
    a, b = np.asarray(a, float), np.asarray(b, float)
    d = b - a
    nn = np.array([-d[1], d[0]]) / max(np.hypot(*d), 1e-6)
    ss = np.linspace(0, 1, n)
    wd = wa + (wb - wa) * ss
    c = a + np.outer(ss, d)
    return np.concatenate([c + np.outer(wd / 2, nn), (c - np.outer(wd / 2, nn))[::-1]])


def draw(theta, phi, curl=0.04, scale=1.0, relax=0.0, shade=False, line=4.2, wrist_show=34):
    """theta: the fingers point left and this many degrees up. phi: the forearm leaves the wrist this many degrees below
    the horizontal, going right. relax: fingers shorter and more bent, for the hand coming away."""
    th, ph = math.radians(theta), math.radians(phi)
    U, V = np.array([-math.cos(th), -math.sin(th)]), np.array([-math.sin(th), math.cos(th)])
    F = np.array([math.cos(ph), math.sin(ph)])
    G = np.array([-F[1], F[0]])

    def uv(pts):
        pts = np.asarray(pts, float)
        return scale * (pts[:, :1] * U + pts[:, 1:] * V)

    fingers = []
    ups = []
    for name, v0, u0, ln, w, fan in FINGERS:
        ln2 = ln * (1 - 0.14 * relax)
        o = finger_outline(v0, PALM + u0, ln2, w, fan + 3 * relax, curl + 0.10 * relax)
        fingers.append(uv(o))
        ss = 1.0
        a = math.radians(fan + 3 * relax)
        ups.append((PALM + u0 + ln2 * math.cos(a), v0 + ln2 * math.sin(a) + (curl + 0.10 * relax) * ln2))
    palm = uv(palm_outline())
    # the thumb lies out of sight behind the hand: only a soft rise on the top edge says it is there
    thumb = uv(smooth([(40, -58), (72, -84), (112, -94), (150, -84), (140, -60), (80, -50)]))
    # wrist and forearm, slim
    wh = 44 * scale
    wrist_pts = [np.array([0.0, 0.0])]
    arm_len = 3000
    cuff_at = wrist_show * scale
    arm = np.array([G * wh, -G * wh, F * arm_len - G * wh * 1.2, F * arm_len + G * wh * 1.2])
    wr_c = cv2.ellipse2Poly((0, 0), (int(wh), int(wh)), 0, 0, 360, 6).astype(float)
    # the sleeve: a plain cuff, its mouth a shallow curve, then plain cloth running off the picture
    sw0, sw1 = 74 * scale, 84 * scale
    mouth = np.array([F * cuff_at + G * sw0 * s + F * (-16 * scale) * (1 - s * s) for s in np.linspace(1, -1, 24)])
    sleeve = np.concatenate([mouth, [F * 260 * scale - G * sw1, F * arm_len - G * sw1, F * arm_len + G * sw1, F * 260 * scale + G * sw1]])

    allp = np.concatenate(fingers + [palm, thumb, np.array([F * 420 * scale + G * sw1, F * 420 * scale - G * sw1])])
    # the picture ends across the sleeve: extrude() carries it on from there
    x0, y0 = allp.min(0) - 24
    x1, y1 = allp.max(0) + 2
    cv_ = Canvas(int(math.floor(x0)), int(math.floor(y0)), int(math.ceil(x1 - x0)), int(math.ceil(y1 - y0)))

    hand_m = cv_.mask(fingers + [palm, thumb, arm, wr_c])
    # the web between the fingers and the join of wrist and hand are soft, never pinched
    hand_m = cv2.morphologyEx(hand_m, cv2.MORPH_CLOSE, disc(5 * SS))
    hand_m = soften(hand_m, 2.6 * SS)
    sleeve_m = soften(cv_.mask([sleeve]), 1.5 * SS)

    def outline(m):
        lw = line * scale * SS
        off = (V + F) * 0.5
        o1 = cv2.dilate(m, disc(lw * 0.82))
        o2 = shift(cv2.dilate(m, disc(lw * 0.82)), off[0] * lw * 0.42, off[1] * lw * 0.42)
        return soften(o1 | o2, 0.8 * SS)

    H, W = hand_m.shape
    rgb = np.zeros((H, W, 3), np.float32)
    a = np.zeros((H, W), np.float32)

    def paint(m, col):
        nonlocal rgb, a
        rgb[m > 0] = col
        a[m > 0] = 1

    paint(outline(hand_m), INK)
    paint(hand_m, SKIN)
    if shade:
        s = hand_m & ~soften(shift(hand_m, -V[0] * 11 * scale * SS, -V[1] * 11 * scale * SS), 1.2 * SS)
        paint(s, SKIN_SHADE)
    # the lines between the fingers: start in the notch, thin away to nothing before the palm
    lines = []
    for i in range(3):
        n1, v1, u1, l1, w1, f1 = FINGERS[i]
        n2, v2, u2, l2, w2, f2 = FINGERS[i + 1]
        end = min(ups[i][0], ups[i + 1][0]) - 8
        mid_tip = (end, (ups[i][1] + ups[i + 1][1]) / 2)
        base = (PALM + 22, (v1 + v2) / 2 + 1)
        lines.append(uv(lens(mid_tip, base, 6.5, 0.5)))
    ln_m = soften(cv_.mask(lines), 0.6 * SS) if lines else None
    if ln_m is not None:
        paint(ln_m & hand_m, INK)
    # sleeve in front of the wrist
    paint(outline(sleeve_m), INK)
    paint(sleeve_m, CLOTH)
    # one line for the cuff, no stripes
    cl = lens(F * (cuff_at + 40 * scale) + G * (sw1 - 2), F * (cuff_at + 40 * scale) - G * (sw1 - 2), 4.5, 4.5)
    paint(soften(cv_.mask([cl]), 0.5 * SS) & sleeve_m, INK)

    rgba = np.dstack([rgb, a])
    premul = rgba.copy()
    premul[..., :3] *= premul[..., 3:]
    small = cv2.resize(premul, (cv_.w, cv_.h), interpolation=cv2.INTER_AREA)
    al = np.maximum(small[..., 3:], 1e-4)
    small[..., :3] = np.clip(small[..., :3] / al, 0, 1)
    # where the row of fingertips is in the picture: just behind the tip of the middle finger
    tip_uv = np.array([[max(u for u, _ in ups) - 26, (ups[1][1] + ups[2][1]) / 2]])
    tip = uv(tip_uv)[0] - (cv_.x0, cv_.y0)
    return small, (round(float(tip[0]), 1), round(float(tip[1]), 1)), (round(float(F[0]), 3), round(float(F[1]), 3))


POSES = {"a": dict(theta=34, phi=62), "b": dict(theta=25, phi=58), "c": dict(theta=18, phi=55), "e": dict(theta=13, phi=52),
         "d": dict(theta=44, phi=66, relax=1.0)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("out", nargs="?", default=str(ROOT / "assets" / "gen" / "cut"))
    ap.add_argument("--scale", type=float, default=1.0)
    ap.add_argument("--shade", action="store_true")
    ap.add_argument("--prefix", default="h40_wipe")
    a = ap.parse_args()
    Path(a.out).mkdir(parents=True, exist_ok=True)
    table = []
    for key, pose in POSES.items():
        im, tip, d = draw(scale=a.scale, shade=a.shade, **pose)
        name = f"{a.prefix}_{key}"
        bgra = np.dstack([im[..., 2], im[..., 1], im[..., 0], im[..., 3]])
        cv2.imwrite(str(Path(a.out) / f"{name}.png"), (np.clip(bgra, 0, 1) * 255 + 0.5).astype(np.uint8))
        table.append((key, name, d, tip))
    print(json.dumps(table))


if __name__ == "__main__":
    main()
