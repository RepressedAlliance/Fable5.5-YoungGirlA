"""Different ways for the empty eyes to fill with light. Each style paints one iris at full strength for a given
amount n (0..11 sung syllables) inside the drawn iris; the caller keeps it inside the iris shape.

All shapes hard-edged. Coordinates are the picture's own pixels, (x, y) is the iris centre, side=-1/+1 is which eye,
so the pair is not a perfect mirror. RX, RY is the iris size.
"""
import math

import numpy as np
import skia

import engine as E

RX, RY = 80.5, 105.5
T1, T2, T3, T4 = "#048396", "#218EA3", "#5BB8CA", "#B0E8EA"
DEEP = "#0B4A58"
PUPIL = "#06262F"


def P(col, a=1.0):
    return skia.Paint(AntiAlias=True, Color4f=E.col(col, a))


def oval(c, x, y, rx, ry, col):
    c.drawOval(skia.Rect.MakeLTRB(x - rx, y - ry, x + rx, y + ry), P(col))


def blob(c, pts, col):
    """Closed hand-cut shape through points: smooth curves with a few corners, never a perfect ellipse."""
    p = skia.Path()
    n = len(pts)
    p.moveTo((pts[0][0] + pts[-1][0]) / 2, (pts[0][1] + pts[-1][1]) / 2)
    for i in range(n):
        q = pts[i]
        r = pts[(i + 1) % n]
        p.quadTo(q[0], q[1], (q[0] + r[0]) / 2, (q[1] + r[1]) / 2)
    p.close()
    c.drawPath(p, P(col))


def flat_base(c, x, y, n, dull="#1E6573", live=T2):
    c.drawRect(skia.Rect.MakeLTRB(x - 110, y - 130, x + 110, y + 130), P(dull if n < 1 else live))


# ---- A. window: her eyes reflect the one thing the song has been keeping outside ----
def window(c, x, y, n, side, t=0.0):
    flat_base(c, x, y, n)
    if n >= 1:
        c.drawRect(skia.Rect.MakeLTRB(x - 110, y - 130, x + 110, y - 28), P(DEEP))
    if n >= 3:
        oval(c, x, y + 150, 120, 130, T1)
    if n >= 5:
        oval(c, x, y + 8, 38, 58, PUPIL)
    if n >= 7:
        oval(c, x + 8 * side, y + 170, 105, 112, T3)
    if n >= 9:
        # the window: a leaning four-pane rectangle, cut with hard corners
        c.save()
        c.translate(x - 26, y - 44)
        c.skew(-0.14, 0)
        c.rotate(-4)
        w, h = 66, 78
        c.drawRect(skia.Rect.MakeLTRB(-w / 2, -h / 2, w / 2, h / 2), P("#FFFFFF"))
        c.drawRect(skia.Rect.MakeLTRB(-w / 2, -3.5, w / 2, 3.5), P(DEEP))
        c.drawRect(skia.Rect.MakeLTRB(-3.5, -h / 2, 3.5, h / 2), P(DEEP))
        c.restore()
    if n >= 11:
        # and the same window again, faint and small, thrown onto the far side of the eye
        c.save()
        c.translate(x + 40, y + 62)
        c.rotate(-8)
        c.drawRect(skia.Rect.MakeLTRB(-13, -9, 13, 9), P(T4))
        c.restore()


# ---- B. tide: one hard edge of light rises up the iris, syllable by syllable ----
def tide(c, x, y, n, side, t=0.0):
    flat_base(c, x, y, 0, dull="#1A5563")
    if n >= 1:
        # wet line wobbles very slightly, like a real water level
        steps = [(n >= 2, T1, 0.70), (n >= 5, T2, 0.40), (n >= 8, T3, 0.12), (n >= 10, T4, -0.14)]
        level0 = [(True, T1, 0.92)]
        for on, col, lev in level0 + steps:
            if not on:
                continue
            yy = y - RY + (lev + 0.0) * 2 * RY * 0.5 + RY * 0.5
            p = skia.Path()
            p.moveTo(x - 120, y + 140)
            p.lineTo(x - 120, yy + 10 * side)
            p.quadTo(x, yy - 24, x + 120, yy - 10 * side)
            p.lineTo(x + 120, y + 140)
            p.close()
            c.drawPath(p, P(col))
    if n >= 6:
        oval(c, x, y + 4, 34, 52, PUPIL)
    if n >= 9:
        blob(c, [(x - 58, y - 66), (x - 18, y - 84), (x - 6, y - 56), (x - 34, y - 34), (x - 62, y - 40)], "#FFFFFF")
    if n >= 11:
        blob(c, [(x + 26, y - 74), (x + 44, y - 76), (x + 46, y - 62), (x + 30, y - 60)], "#FFFFFF")
        blob(c, [(x - 30, y + 78), (x + 34, y + 72), (x + 44, y + 86), (x - 26, y + 92)], "#FFFFFF")


# ---- C. facets: the iris is cut like glass into fourteen shards, lit a few at a time ----
_F = None


def facets(c, x, y, n, side, t=0.0):
    flat_base(c, x, y, 0, dull="#1A5563")
    rng = np.random.default_rng(14 if side < 0 else 41)
    count = 14
    order = rng.permutation(count)
    tones = [DEEP, T1, T1, T2, T2, T3, T3, T4]
    start = -math.pi / 2 + rng.uniform(-0.2, 0.2)
    angs = [start + (i + rng.uniform(-0.28, 0.28)) / count * math.tau for i in range(count)]
    lit = int(round(n / 11 * count))
    for rank in range(lit):
        i = int(order[rank])
        a0, a1 = angs[i], angs[(i + 1) % count] + (math.tau if i == count - 1 else 0)
        # lower shards are brightest, the way light falls in an eye
        mid = (a0 + a1) / 2
        k = (math.sin(mid) + 1) / 2
        col = tones[min(len(tones) - 1, int(k * (len(tones) - 1) + rng.uniform(-0.8, 0.8)))]
        p = skia.Path()
        r0 = 40
        p.moveTo(x + math.cos(a0) * r0, y + math.sin(a0) * r0 * 1.3)
        p.lineTo(x + math.cos(a0) * 130, y + math.sin(a0) * 170)
        p.lineTo(x + math.cos(a1) * 130, y + math.sin(a1) * 170)
        p.lineTo(x + math.cos(a1) * r0, y + math.sin(a1) * r0 * 1.3)
        p.close()
        c.drawPath(p, P(col))
    if n >= 4:
        oval(c, x, y, 34, 50, PUPIL)
    if n >= 11:
        blob(c, [(x - 52, y - 58), (x - 20, y - 74), (x - 10, y - 50), (x - 40, y - 34)], "#FFFFFF")


# ---- D. brush: painted by hand, with lopsided strokes, every shape a little different in each eye ----
def brush(c, x, y, n, side, t=0.0):
    flat_base(c, x, y, 0, dull="#1E6573")
    s = side
    if n >= 1:
        # the shadow under the lash, with a torn lower edge
        blob(c, [(x - 110, y - 130), (x + 110, y - 130), (x + 112, y - 40), (x + 58, y - 22 - 8 * s), (x + 18, y - 44),
                 (x - 28, y - 18 + 8 * s), (x - 70, y - 42), (x - 112, y - 26)], DEEP)
    if n >= 2:
        blob(c, [(x - 90, y + 8), (x - 40, y + 22), (x + 8 * s, y + 8), (x + 62, y + 20), (x + 96, y + 2), (x + 100, y + 130), (x - 100, y + 130)], T1)
    if n >= 4:
        blob(c, [(x - 34 - 4 * s, y - 36), (x + 22, y - 44), (x + 40, y + 2), (x + 26, y + 46), (x - 18, y + 54), (x - 40, y + 14)], PUPIL)
    if n >= 6:
        blob(c, [(x - 88, y + 50), (x - 50, y + 66 - 6 * s), (x - 8, y + 54), (x + 34, y + 70 + 6 * s), (x + 86, y + 44), (x + 90, y + 130), (x - 90, y + 130)], T2)
    if n >= 8:
        blob(c, [(x - 70, y + 88), (x - 26, y + 76), (x + 22 * s, y + 90), (x + 66, y + 76), (x + 62, y + 120), (x - 64, y + 120)], T3)
    if n >= 9:
        # scattered flecks: hand dabs, never two alike
        for fx, fy, r in ((-46, 42, 7), (54, 34, 5), (30, 64, 6), (-16, 70, 4)):
            blob(c, [(x + fx - r, y + fy), (x + fx, y + fy - r * 1.3), (x + fx + r, y + fy), (x + fx + r * 0.2, y + fy + r)], T4)
    if n >= 10:
        # main highlight: a slash with a flick at one end, the shape of a brush lifting off
        blob(c, [(x - 62, y - 42), (x - 42, y - 76), (x - 6, y - 84), (x + 6 * s, y - 70), (x - 18, y - 58), (x - 28, y - 30), (x - 52, y - 22)], "#FFFFFF")
    if n >= 11:
        blob(c, [(x + 30, y - 70), (x + 48, y - 72), (x + 52, y - 54), (x + 36, y - 48)], "#FFFFFF")
        blob(c, [(x - 40, y + 84), (x + 10, y + 76), (x + 46, y + 84), (x + 8, y + 94)], T4)


# ---- E. key: the way a key animator paints an eye: every tone follows the curve of the eyeball ----
def key(c, x, y, n, side, t=0.0):
    flat_base(c, x, y, 0, dull="#1E6573")
    s = side
    if n >= 1:
        c.drawRect(skia.Rect.MakeLTRB(x - 110, y - 130, x + 110, y + 130), P("#1A7284"))
    if n >= 2:
        # the shadow the lid throws, a crescent that hugs the top of the eyeball with pointed ends
        blob(c, [(x - 112, y - 12), (x - 96, y - 130), (x + 96, y - 130), (x + 112, y - 12), (x + 66, y - 42 + 4 * s), (x + 8 * s, y - 56), (x - 62, y - 40 - 4 * s)], DEEP)
    if n >= 3:
        # the pupil is not an oval: it hangs from the lid's shadow like a drop
        blob(c, [(x - 30, y - 70), (x + 30, y - 70), (x + 34, y - 8), (x + 22, y + 34), (x - 2 * s, y + 44), (x - 24, y + 30), (x - 34, y - 10)], PUPIL)
    if n >= 4:
        # first real colour: a wide band following the lower curve
        blob(c, [(x - 92, y + 6), (x - 54, y + 42), (x + 6 * s, y + 58), (x + 58, y + 42), (x + 92, y + 4), (x + 92, y + 130), (x - 92, y + 130)], T1)
    if n >= 6:
        blob(c, [(x - 84, y + 40), (x - 44, y + 68), (x + 4 * s, y + 78), (x + 48, y + 68), (x + 84, y + 38), (x + 84, y + 130), (x - 84, y + 130)], T2)
    if n >= 8:
        blob(c, [(x - 70, y + 72), (x - 34, y + 86), (x + 8 * s, y + 92), (x + 38, y + 84), (x + 70, y + 68), (x + 64, y + 130), (x - 64, y + 130)], T3)
    if n >= 9:
        # hard rim of light right at the bottom of the eye
        blob(c, [(x - 42, y + 96), (x + 4 * s, y + 90), (x + 42, y + 94), (x + 30, y + 110), (x - 30, y + 110)], T4)
    if n >= 10:
        # the highlight: a brush slash, heavy at one end and lifting off at the other. It sits over pupil and shadow.
        blob(c, [(x - 68, y - 48), (x - 50, y - 84), (x - 12, y - 90), (x + 12, y - 74), (x - 6, y - 66), (x - 24, y - 52), (x - 34, y - 28), (x - 58, y - 22)], "#FFFFFF")
    if n >= 11:
        blob(c, [(x + 32, y - 74), (x + 50, y - 76), (x + 56, y - 56), (x + 38, y - 50)], "#FFFFFF")
        # three flecks, on the side opposite the highlight, and they twinkle: two drawings alternating
        alt = int(t * 7) % 2
        fl = [(40, 34, 7), (54, 52, 4), (18, 62, 5)] if alt == 0 else [(44, 30, 5), (50, 56, 6), (16, 66, 4)]
        for fx, fy, r in fl:
            blob(c, [(x + fx - r, y + fy), (x + fx, y + fy - r * 1.4), (x + fx + r, y + fy), (x + fx, y + fy + r * 1.1)], T4)


# ---- F. pane: a single tall window, reflected. Not four squares in a logo: a slanted pane and a thin frame ----
def pane(c, x, y, n, side, t=0.0):
    key(c, x, y, min(n, 9), side, t)
    if n >= 10:
        c.save()
        c.translate(x - 30, y - 52)
        c.skew(-0.22, 0)
        p = skia.Path()
        p.moveTo(-26, -36)
        p.lineTo(24, -40)
        p.lineTo(30, 36)
        p.lineTo(-24, 42)
        p.close()
        c.drawPath(p, P("#FFFFFF"))
        c.drawLine(2, -40, 5, 40, skia.Paint(AntiAlias=True, Color4f=E.col(DEEP), StrokeWidth=4))
        c.restore()
    if n >= 11:
        blob(c, [(x + 30, y + 40), (x + 48, y + 38), (x + 52, y + 54), (x + 34, y + 56)], T4)


STYLES = {"window": window, "facets": facets, "brush": brush, "key": key, "pane": pane}
