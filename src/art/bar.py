"""The black bar: a real marker scrawl with white handwriting, drawn stroke by stroke.

Placed by hand for each image (see bars.json), never estimated. `progress` lets the opening draw it live.
"""
import math

import numpy as np
import skia

INK = skia.Color4f(0.035, 0.035, 0.05, 1)
WHITE = skia.Color4f(0.98, 0.98, 0.96, 1)

# 少女A in hand-ruled strokes, each char in a unit box. Order and direction follow real stroke order.
HAND = [
    [  # 少
        [(0.50, 0.00), (0.51, 0.28), (0.50, 0.56), (0.45, 0.60)],
        [(0.24, 0.20), (0.18, 0.34), (0.08, 0.46)],
        [(0.72, 0.18), (0.82, 0.30), (0.92, 0.44)],
        [(0.80, 0.54), (0.66, 0.74), (0.40, 0.90), (0.10, 1.00)],
    ],
    [  # 女
        [(0.42, 0.00), (0.34, 0.20), (0.24, 0.42), (0.46, 0.62), (0.70, 0.82), (0.90, 1.00)],
        [(0.68, 0.06), (0.64, 0.38), (0.48, 0.68), (0.26, 0.88), (0.06, 0.98)],
        [(0.00, 0.44), (0.40, 0.40), (1.00, 0.36)],
    ],
    [  # A
        [(0.50, 0.00), (0.34, 0.42), (0.10, 1.00)],
        [(0.48, 0.02), (0.68, 0.46), (0.92, 1.00)],
        [(0.20, 0.66), (0.50, 0.63), (0.80, 0.64)],
    ],
]


def _catmull(pts, n=10):
    p = [pts[0]] + list(pts) + [pts[-1]]
    out = []
    for i in range(1, len(p) - 2):
        p0, p1, p2, p3 = map(np.array, (p[i - 1], p[i], p[i + 1], p[i + 2]))
        for k in range(n):
            t = k / n
            out.append(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t * t +
                              (-p0 + 3 * p1 - 3 * p2 + p3) * t ** 3))
    out.append(np.array(pts[-1], float))
    return np.array(out, float)


def _polyline_lengths(a):
    d = np.hypot(*(a[1:] - a[:-1]).T)
    return np.concatenate([[0], np.cumsum(d)])


def scrawl_path(length, thick, rng, passes=11):
    """Back-and-forth marker path along x, centred on (0,0), covering the band.

    Long sloppy passes: the turnarounds land at different places, some passes sag, so the two ends
    look like a hand in a hurry and not like a rounded rectangle.
    """
    pts = []
    ys = np.linspace(-thick * 0.43, thick * 0.43, passes)
    rng.shuffle(ys[1:-1])  # the pen goes back over itself rather than ruling neat rows
    for i, y in enumerate(ys):
        lean = rng.normal(0, thick * 0.05)
        l_over = length * (0.40 + rng.random() * 0.115)
        r_over = length * (0.40 + rng.random() * 0.115)
        mid = rng.normal(0, thick * 0.055)
        if i % 2:
            pts += [(r_over, y - lean), (0.0, y + mid), (-l_over, y + lean)]
        else:
            pts += [(-l_over, y + lean), (0.0, y + mid), (r_over, y - lean)]
    return _catmull(pts, 12)


class Bar:
    """A bar in image coordinates. angle in degrees, clockwise on screen."""

    def __init__(self, cx, cy, length, thick, angle=0.0, seed=1, text=True, passes=11):
        self.cx, self.cy, self.length, self.thick, self.angle = cx, cy, length, thick, angle
        self.rng = np.random.default_rng(seed)
        self.path = scrawl_path(length, thick, self.rng, passes)
        self.s = _polyline_lengths(self.path)
        self.marker = thick / passes * 2.0
        self.text = text
        self._hand()

    def _hand(self):
        h = self.thick * 0.66
        adv = h * 1.22
        widths = [1.0, 1.0, 0.86]
        total = sum(w * adv for w in widths)
        x = -total / 2
        self.strokes = []
        for ch, w in zip(HAND, widths):
            for st in ch:
                pts = []
                wob = self.rng.normal(0, h * 0.018, (len(st), 2))
                for (u, v), j in zip(st, wob):
                    pts.append((x + u * h * w * 1.08 + j[0], -h / 2 + v * h + j[1]))
                a = _catmull(pts, 10)
                self.strokes.append((a, _polyline_lengths(a)))
            x += w * adv
        self.hand_w = h * 0.105
        self.hand_total = sum(s[-1] for _, s in self.strokes)

    def _xf(self, c):
        c.translate(self.cx, self.cy)
        c.rotate(self.angle)

    def draw(self, c, progress=1.0, write=1.0, ink=INK, white=WHITE):
        """progress: 0..1 of the marker scrawl. write: 0..1 of the handwriting."""
        c.save()
        self._xf(c)
        if progress > 0:
            n = max(2, int(np.searchsorted(self.s, self.s[-1] * progress)))
            p = skia.Path()
            p.moveTo(*self.path[0])
            for q in self.path[1:n]:
                p.lineTo(*q)
            c.drawPath(p, skia.Paint(AntiAlias=True, Color4f=ink, Style=skia.Paint.kStroke_Style,
                                     StrokeWidth=self.marker, StrokeCap=skia.Paint.kRound_Cap,
                                     StrokeJoin=skia.Paint.kRound_Join))
            if progress >= 1:
                # solid core so nothing can ever show through
                r = skia.Rect.MakeLTRB(-self.length * 0.40, -self.thick * 0.42, self.length * 0.40, self.thick * 0.42)
                rad = self.thick * 0.40
                c.drawRRect(skia.RRect.MakeRectXY(r, rad, rad), skia.Paint(AntiAlias=True, Color4f=ink))
        if self.text and write > 0:
            remain = self.hand_total * write
            for a, s in self.strokes:
                if remain <= 0:
                    break
                n = int(np.searchsorted(s, min(remain, s[-1])))
                remain -= s[-1]
                self._brush(c, a[:max(n, 2)], s[:max(n, 2)], white, s[-1])
        c.restore()

    def _brush(self, c, a, s, color, total):
        # marker pressure: fatter where the pen lands, thinner at the flick
        paint = skia.Paint(AntiAlias=True, Color4f=color, StrokeCap=skia.Paint.kRound_Cap,
                           Style=skia.Paint.kStroke_Style)
        for i in range(len(a) - 1):
            u = s[i] / max(total, 1e-3)
            w = self.hand_w * (1.25 - 0.55 * u)
            paint.setStrokeWidth(w)
            c.drawLine(a[i][0], a[i][1], a[i + 1][0], a[i + 1][1], paint)


def stamp(rgba, bar):
    """Draw a finished bar into a float RGBA image and return it."""
    h, w = rgba.shape[:2]
    arr = np.array((np.clip(rgba, 0, 1) * 255 + 0.5), dtype=np.uint8, order="C")
    # premultiply for skia
    arr[..., :3] = (arr[..., :3].astype(np.float32) * (arr[..., 3:4] / 255.0)).astype(np.uint8)
    surf = skia.Surface(arr, colorType=skia.ColorType.kRGBA_8888_ColorType, alphaType=skia.AlphaType.kPremul_AlphaType)
    c = surf.getCanvas()
    bar.draw(c)
    del c, surf
    out = arr.astype(np.float32) / 255
    a = np.maximum(out[..., 3:4], 1e-3)
    out[..., :3] = np.clip(out[..., :3] / a, 0, 1)
    return out
