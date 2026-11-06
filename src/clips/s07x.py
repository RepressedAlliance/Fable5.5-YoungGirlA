"""Section 07, second half. The wall of rumours gets buried in cheerful reaction stickers, all except the empty cell.
We push into that cell, where an unseen hand draws a child's two crayon flowers in time with the words; a red stamp
says nobody answered; two shutters on "pa-ppa" and it is a photograph with the same word written small in the corner."""
import math
import sys
from pathlib import Path

import cv2
import numpy as np
import skia

sys.path.insert(0, str(Path(__file__).parent))
import common as K  # noqa: E402
import engine as E  # noqa: E402
import shared_c4 as S  # noqa: E402
from bar import _catmull, _polyline_lengths  # noqa: E402
import cutout as C  # noqa: E402
import handkit as HK  # noqa: E402

ROOT = K.ROOT
F0, F1 = 3395, 3989
PUSH0, PUSH1 = 118.42, 119.70
STAMP = K.LYRICS[37]["start"]
PULL0, PULL1 = K.LYRICS[37]["syl"][1]["t"], 131.35
PA = (131.60, 132.06)         # where the two "pa" attacks really are in the audio
CLOSE, FLASH, OPEN = 0.10, 0.067, 0.11
SUN = (-0.42, 0.72, -0.55)    # same sun as the 3D wall
SHADOW_TINT = (0.49, 0.47, 0.54)
# the camera, in pixels of the wide shot (the last frame of the 14 Rin clip)
FOCUS = (960.0, 555.0)
ZOOM = 5.56
WORLD_FLOWER = (978.0, 586.0)
FLOWER_W = 152.0
# what the grown-up is copying from: a print of her friend's drawing, taped down beside the place he draws. These flowers are not
# his, and they are not from her
PRINT_C = (841.0, 610.0)
PRINT_W, PRINT_H = 82.0, 60.0
PRINT_ROT = -4.0
TAKE2_ZOOM = 4.0
# the grown-up's hand, drawn the way every hand in this film is drawn; only the suit says he is a grown-up. One grip all along: the two drawings differ only by a slight press.
ADULT = (("press", "h45_a"), ("hard", "h45_b"))
ADULT_S = 0.120            # wide-shot pixels per picture pixel: a big hand beside the small flowers
ADULT_SLEEVE = (1.0, 0.72)
SLEEVE_LOOSE = 0.5
TICK = 15                  # the hand and the wax it lays down move together, on fifteens


def S07_tip(rgba):
    # The crayon is the leftmost thing in the drawing: its point is the first solid column.
    a = rgba[..., 3] > 0.6
    x = int(np.nonzero(a.any(0))[0][0])
    ys = np.nonzero(a[:, x:x + 6].any(1))[0]
    return float(x), float(ys.mean())


# ---- sticker shapes, each a path centred on the origin, about w by h ----
def heart(w, h):
    p = skia.Path()
    x, y = w / 2, h / 2
    p.moveTo(0, y)
    p.cubicTo(-x * 0.55, y * 0.45, -x, y * 0.05, -x, -y * 0.38)
    p.cubicTo(-x, -y * 0.86, -x * 0.34, -y * 1.08, 0, -y * 0.5)
    p.cubicTo(x * 0.34, -y * 1.08, x, -y * 0.86, x, -y * 0.38)
    p.cubicTo(x, y * 0.05, x * 0.55, y * 0.45, 0, y)
    p.close()
    return p


def burst(w, h, n=11, inner=0.74):
    p = skia.Path()
    for i in range(n * 2):
        a = -math.pi / 2 + i / (n * 2) * math.tau
        q = 1.0 if i % 2 == 0 else inner
        (p.moveTo if i == 0 else p.lineTo)(math.cos(a) * q * w / 2, math.sin(a) * q * h / 2)
    p.close()
    return p


def bubble(w, h, side=1):
    p = skia.Path()
    bh = h * 0.8
    p.addRRect(skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(-w / 2, -h / 2, w, bh), bh * 0.34, bh * 0.34))
    t = skia.Path()
    t.moveTo(side * w * 0.10, -h / 2 + bh - 2)
    t.lineTo(side * w * 0.34, -h / 2 + bh - 2)
    t.lineTo(side * w * 0.12, h / 2)
    t.close()
    return skia.Op(p, t, skia.PathOp.kUnion_PathOp) or p


def pill(w, h):
    p = skia.Path()
    p.addRRect(skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(-w / 2, -h / 2, w, h), h / 2, h / 2))
    return p


def disc(w, h):
    p = skia.Path()
    p.addOval(skia.Rect.MakeXYWH(-w / 2, -h / 2, w, h))
    return p


def ribbon(w, h):
    """A banner with notched ends."""
    p = skia.Path()
    n = h * 0.3
    p.moveTo(-w / 2, -h / 2)
    p.lineTo(w / 2, -h / 2)
    p.lineTo(w / 2 - n, 0)
    p.lineTo(w / 2, h / 2)
    p.lineTo(-w / 2, h / 2)
    p.lineTo(-w / 2 + n, 0)
    p.close()
    return p


def square(w, h):
    p = skia.Path()
    p.addRRect(skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(-w / 2, -h / 2, w, h), h * 0.2, h * 0.2))
    return p


# word, shape, aspect (w / h), font, share of the shape the word may fill and its vertical offset
SHAPES = {"heart": (heart, 1.1, 0.62, 0.46, -0.05), "burst": (burst, 1.0, 0.56, 0.5, 0.0), "bubble": (bubble, 1.55, 0.78, 0.58, -0.10),
          "pill": (pill, 2.6, 0.80, 0.60, 0.0), "disc": (disc, 1.0, 0.70, 0.60, 0.0), "ribbon": (ribbon, 2.7, 0.70, 0.62, 0.0),
          "square": (square, 1.25, 0.76, 0.66, 0.0)}
DELA, POTTA, MOCHI, ROCK, MARU, BLACK = ("DelaGothicOne-Regular", "PottaOne-Regular", "MochiyPopOne-Regular", "RocknRollOne-Regular",
                                         "MPLUSRounded1c-Black", "ZenKakuGothicNew-Black")
WORDS = [("いいね", "heart", MOCHI), ("草", "disc", DELA), ("応援", "ribbon", BLACK), ("それな", "bubble", POTTA),
         ("神", "burst", DELA), ("わかる", "bubble", MARU), ("尊い", "heart", MOCHI), ("推せる", "pill", ROCK),
         ("拡散希望", "ribbon", BLACK), ("泣いた", "bubble", POTTA), ("最高", "burst", DELA), ("いいね", "pill", MARU),
         ("草", "square", POTTA), ("大草原", "pill", DELA), ("がんばれ", "ribbon", MOCHI), ("天才", "burst", BLACK),
         ("保存した", "pill", MARU), ("優勝", "disc", DELA), ("エモい", "heart", ROCK), ("知ってた", "bubble", MARU),
         ("応援", "square", MOCHI), ("それな", "pill", BLACK), ("乙", "disc", POTTA), ("www", "pill", DELA)]
# (fill, text): the wall's own colours go, these take over; no red, the red is the stamp's
SCHEMES = [(E.RIN, E.INK), (E.PAPER, E.INK), (E.INK, E.PAPER), (E.CYAN, E.INK), (E.PAPER, E.INK), (E.INK, E.RIN), (E.RIN, E.INK), (E.CYAN, E.PAPER)]


class Sticker:
    def __init__(self, word, kind, font, w, scheme, rot):
        make, asp, share, hshare, off = SHAPES[kind]
        self.w, self.h = w, w / asp
        self.path = make(self.w, self.h)
        self.fill, self.tc = scheme
        self.rot = rot
        self.bw = max(3.0, w * 0.028) + 2.0
        self.ty = E.fit(word, font, self.w * share, self.h * hshare, max_size=240)
        self.off = off * self.h
        self.x = self.y = 0.0
        self.t = 0.0
        self.word = word

    def footprint(self):
        """Alpha of the die-cut outline, in wide-shot pixels at half size, with its offset from the top left."""
        b = self.path.computeTightBounds()
        r = math.hypot(b.width(), b.height()) / 2 + self.bw + 2
        n = int(r * 2 / 2) + 1
        surf = skia.Surface(n, n)
        c = surf.getCanvas()
        c.clear(skia.Color4f(0, 0, 0, 0))
        c.scale(0.5, 0.5)
        c.translate(r, r)
        c.rotate(self.rot)
        c.drawPath(self.path, skia.Paint(AntiAlias=True, Color4f=E.col(E.INK)))
        c.drawPath(self.path, skia.Paint(AntiAlias=True, Color4f=E.col(E.INK), Style=skia.Paint.kStroke_Style, StrokeWidth=self.bw * 2,
                                         StrokeJoin=skia.Paint.kRound_Join))
        return surf.makeImageSnapshot().toarray(colorType=skia.ColorType.kRGBA_8888_ColorType)[..., 3] > 127, r

    def draw(self, c, t):
        u = E.ease_out(E.seg(t, self.t - 0.067, self.t), 2)
        sc = 1 + 0.5 * (1 - u)
        c.save()
        c.translate(self.x, self.y)
        # a thin hard shadow, the same way as every other shadow on this wall
        sh = 0.05 * self.w * 0.45 + 2.5
        c.save()
        c.translate(-sh * 0.8, sh)
        c.rotate(self.rot)
        c.scale(sc, sc)
        p = skia.Paint(AntiAlias=True, Color4f=E.col("#3C4258", 0.55), Style=skia.Paint.kStrokeAndFill_Style, StrokeWidth=self.bw * 2,
                       StrokeJoin=skia.Paint.kRound_Join)
        p.setBlendMode(skia.BlendMode.kMultiply)
        c.drawPath(self.path, p)
        c.restore()
        c.rotate(self.rot)
        c.scale(sc, sc)
        c.drawPath(self.path, skia.Paint(AntiAlias=True, Color4f=E.col("#FFFFFF"), Style=skia.Paint.kStroke_Style, StrokeWidth=self.bw * 2,
                                         StrokeJoin=skia.Paint.kRound_Join))
        c.drawPath(self.path, skia.Paint(AntiAlias=True, Color4f=E.col(self.fill)))
        self.ty.draw(c, 0, self.off, self.tc)
        c.restore()


# ---- handwriting: the code word, in the same kind of hand-ruled strokes as the bar ----
_PA = [[(0.30, 0.22), (0.24, 0.52), (0.04, 0.94)], [(0.54, 0.20), (0.72, 0.52), (0.98, 0.90)]]
_TSU = [[(0.14, 0.30), (0.26, 0.64)], [(0.50, 0.24), (0.60, 0.58)], [(0.94, 0.20), (0.84, 0.62), (0.42, 1.02)]]


def pappa_strokes(seed=7):
    """Strokes in a box 1 high and about 3 wide; the little circle of each パ is a closed stroke."""
    rng = np.random.default_rng(seed)
    out = []
    def add(pts, ox, s=1.0, oy=0.0):
        q = [(ox + u * s + rng.normal(0, 0.012), oy + v * s + rng.normal(0, 0.014)) for u, v in pts]
        a = _catmull(q, 8)
        out.append((a, _polyline_lengths(a)))
    def circle(cx, cy, r):
        q = [(cx + r * math.cos(i / 8 * math.tau - 2.2), cy + r * math.sin(i / 8 * math.tau - 2.2)) for i in range(9)]
        a = _catmull(q, 4)
        out.append((a, _polyline_lengths(a)))
    for st in _PA:
        add(st, 0.0)
    circle(0.92, 0.10, 0.085)
    for st in _TSU:
        add(st, 1.06, 0.72, 0.28)
    for st in _PA:
        add(st, 1.92)
    circle(2.84, 0.10, 0.085)
    return out


def draw_strokes(c, strokes, x, y, h, width, u=1.0, color=E.INK):
    total = sum(s[-1] for _, s in strokes)
    remain = total * u
    p = skia.Paint(AntiAlias=True, Color4f=E.col(color), Style=skia.Paint.kStroke_Style, StrokeCap=skia.Paint.kRound_Cap,
                   StrokeJoin=skia.Paint.kRound_Join, StrokeWidth=width)
    for a, s in strokes:
        if remain <= 0:
            break
        n = max(2, int(np.searchsorted(s, min(remain, s[-1]))) + 1)
        remain -= s[-1]
        pa = skia.Path()
        pa.moveTo(x + a[0][0] * h, y + a[0][1] * h)
        for q in a[1:n]:
            pa.lineTo(x + q[0] * h, y + q[1] * h)
        c.drawPath(pa, p)


class Stickers(E.Clip):
    name = "s07x"
    t0, t1 = F0 / 30, F1 / 30
    shutter = 0.4
    cuts = (STAMP, PA[0] + FLASH, PA[1] + FLASH)

    def setup(self):
        self.t_ref = self.t0
        self.cuts = type(self).cuts
        self.k0 = S.project((1, 0, 0), self.t_ref)[0] - S.project((0, 0, 0), self.t_ref)[0]
        ww, wh = S.COLS * S.CELL_W * self.k0, S.ROWS * S.CELL_H * self.k0
        self.wall = skia.Rect.MakeXYWH(960 - ww / 2, 540 - wh / 2, ww, wh)
        cx, cz = S.cell_center(*S.EMPTY)
        cw, ch = S.CELL_W * self.k0, S.CELL_H * self.k0
        self.cell = skia.Rect.MakeXYWH(960 + cx * self.k0 - cw / 2, 540 - cz * self.k0 - ch / 2, cw, ch)
        self.build_wall()
        self.build_stickers()
        self.build_flowers()
        self.build_stamp()
        # a line stays until the next one starts, never both at once
        self.strips = [(K.LYRICS[i]["start"], K.LYRICS[i + 1]["start"], K.Strip(tx, K.chars_of(i, tx), size=46), i >= 36)
                       for i, tx in [(33, "朽ちるまでの愛憎を"), (34, "飲み込む君簡単に"), (35, "微笑む君どうして"),
                                     (36, "「子供だましの花ふたつ」"), (37, "きっときっと諦めたから？パッパ")]]
        self.strips[-1] = (self.strips[-1][0], self.t1 + 1, self.strips[-1][2], True)
        self.hand = pappa_strokes()
        self._photos = {}
        self._reveal = (None, None)

    # ---- the wall, exactly as the 3D clip leaves it ----
    def standee_world(self):
        meta = S.meta()
        out = []
        for r, cell in zip(S.RUMOURS, S.ORDER):
            name, off = r[0], r[5]
            m = meta[name]
            cx, cz = S.cell_center(*cell)
            px, pz = cx + S.CELL_W * 0.13, cz - S.CELL_H / 2 + 0.11 + m["h_m"] / 2
            out.append((name, m, px, -off, pz))
        return out

    def build_wall(self):
        wall = cv2.imread(str(ROOT / "assets" / "gen" / "c4_wall.png"), cv2.IMREAD_COLOR)[..., ::-1]
        r = self.wall
        wx, wy = int(S.EMPTY[0] * S.CELL_W * 900), int(S.EMPTY[1] * S.CELL_H * 900)
        wc, hc = int(S.CELL_W * 900), int(S.CELL_H * 900)
        cell = wall[wy:wy + hc, wx:wx + wc]
        small = cv2.resize(wall, (int(round(r.width() * 2)), int(round(r.height() * 2))), interpolation=cv2.INTER_AREA)
        del wall
        k0 = self.k0
        shadows, people = [], []
        for name, m, px, py, pz in self.standee_world():
            im = cv2.imread(str(ROOT / "assets" / "gen" / "standee" / f"{name}.png"), cv2.IMREAD_UNCHANGED)
            d = -S.project((px, py, pz), self.t_ref)[2] * 0 + S.project((px, py, pz), self.t_ref)[2]
            d0 = S.project((0, 0, 0), self.t_ref)[2]
            k = k0 * d0 / d    # nearer the camera than the wall, so a little bigger
            size = (max(2, int(round(m["w_m"] * k * 2))), max(2, int(round(m["h_m"] * k * 2))))
            a = im[..., 3:4].astype(np.float32) / 255
            pm = np.dstack([im[..., :3][..., ::-1] * a, im[..., 3:4].astype(np.float32)]).astype(np.float32)
            pm = cv2.resize(pm, size, interpolation=cv2.INTER_AREA)
            img = skia.Image.fromarray(np.ascontiguousarray((pm + 0.5).astype(np.uint8)), colorType=skia.ColorType.kRGBA_8888_ColorType,
                                       alphaType=skia.AlphaType.kPremul_AlphaType)
            sx, sy = S.project((px, py, pz), self.t_ref)[:2]
            people.append((img, sx, sy))
            # the hard shadow on the wall: thrown along the sun, drawn at wall scale
            s = -py / SUN[1]
            hx, hz = px + SUN[0] * s, pz + SUN[2] * s
            shx, shy = 960 + hx * k0, 540 - hz * k0
            ssize = (max(2, int(round(m["w_m"] * k0 * 4))), max(2, int(round(m["h_m"] * k0 * 4))))
            sa = cv2.resize(im[..., 3].astype(np.float32) / 255, ssize, interpolation=cv2.INTER_AREA)
            sa = (cv2.GaussianBlur(sa, (0, 0), 0.8) > 0.5).astype(np.float32)
            sa = cv2.GaussianBlur(sa, (0, 0), 0.6)
            rgba = np.zeros(ssize[::-1] + (4,), np.float32)
            rgba[..., 0], rgba[..., 1], rgba[..., 2], rgba[..., 3] = SHADOW_TINT[0], SHADOW_TINT[1], SHADOW_TINT[2], sa
            shadows.append((E.np_to_image(rgba), shx, shy, m["w_m"] * k0, m["h_m"] * k0))
        def throw(c):
            c.save()
            c.clipRect(r)
            p = skia.Paint(AntiAlias=True)
            p.setBlendMode(skia.BlendMode.kMultiply)
            for img, x, y, w, h in shadows:
                c.drawImageRect(img, skia.Rect.MakeXYWH(x - w / 2, y - h / 2, w, h), skia.SamplingOptions(skia.FilterMode.kLinear), p)
            c.restore()
        surf = skia.Surface(E.W * 2, E.H * 2)
        c = surf.getCanvas()
        c.clear(E.col(E.CYAN))
        c.scale(2, 2)
        c.drawImageRect(E.np_to_image(np.dstack([small, np.full(small.shape[:2], 255, np.uint8)])), r, skia.SamplingOptions(skia.FilterMode.kLinear))
        throw(c)
        for img, x, y in people:
            c.save()
            c.translate(x, y)
            c.scale(0.5, 0.5)
            c.drawImage(img, -img.width() / 2, -img.height() / 2, skia.SamplingOptions(skia.FilterMode.kLinear))
            c.restore()
        self.lines(c)
        self.base = surf.makeImageSnapshot()
        # the empty cell again at print resolution, for when we are inside it
        surf = skia.Surface(wc, hc)
        c = surf.getCanvas()
        c.drawImage(E.np_to_image(np.dstack([cell, np.full(cell.shape[:2], 255, np.uint8)])), 0, 0)
        c.scale(wc / self.cell.width(), hc / self.cell.height())
        c.translate(-self.cell.left(), -self.cell.top())
        self.lines(c)
        self.cell_img = surf.makeImageSnapshot()
        # the same at wide-shot size, for once the figure above it (whose foot shadow just reaches in) is buried
        mid = self.cell_img.toarray(colorType=skia.ColorType.kRGBA_8888_ColorType)
        mid = cv2.resize(mid, (int(self.cell.width() * 2), int(self.cell.height() * 2)), interpolation=cv2.INTER_AREA)
        self.cell_mid = E.np_to_image(mid)

    def lines(self, c):
        """The black line through all the bars, from the 14 Rin clip; it stops at the empty cell."""
        meta = S.meta()
        ends = {}
        for (name, m, px, py, pz), cell in zip(self.standee_world(), S.ORDER):
            fx, fy, fl, ft, ang = m["bar"]
            w, h = m["w_m"], m["h_m"]
            def world(u, v):
                return (px - w / 2 + u * w, py, pz + h / 2 - v * h)
            a = math.radians(ang)
            hw = fl * 0.47
            ends[cell] = (world(fx - hw * math.cos(a), fy - hw * math.sin(a) * (w / h)),
                          world(fx + hw * math.cos(a), fy + hw * math.sin(a) * (w / h)))
        p = skia.Paint(AntiAlias=True, Color4f=E.col("#0A0A0F"), StrokeWidth=6.0, StrokeCap=skia.Paint.kButt_Cap)
        def line(a, b):
            q0, q1 = S.project(a, self.t_ref), S.project(b, self.t_ref)
            c.drawLine(q0[0], q0[1], q1[0], q1[1], p)
        for r in range(S.ROWS):
            for col in range(S.COLS - 1):
                a, b = (col, r), (col + 1, r)
                if a == S.EMPTY or b == S.EMPTY or a not in ends or b not in ends:
                    continue
                ra, lb = ends[a][1], ends[b][0]
                mid = ((ra[0] + lb[0]) / 2, (ra[1] + lb[1]) / 2, (ra[2] + lb[2]) / 2)
                line(ra, mid)
                line(lb, mid)
        ex, ez = S.cell_center(*S.EMPTY)
        left, right = ends[(1, 1)][1], ends[(3, 1)][0]
        line(left, (ex - S.CELL_W / 2 + 0.03, left[1], left[2]))
        line(right, (ex + S.CELL_W / 2 - 0.03, right[1], right[2]))

    # ---- stickers: placed greedily so that at the end every rumour and every figure really is covered ----
    def build_stickers(self):
        rng = np.random.default_rng(714)
        r, cell = self.wall, self.cell
        # what must be covered: anything that is not the plain cell colour, from the wall as it looks
        arr = self.base.toarray(colorType=skia.ColorType.kRGBA_8888_ColorType)[..., :3].astype(np.int16)
        arr = cv2.resize(arr.astype(np.float32), (E.W, E.H), interpolation=cv2.INTER_AREA)[::1, ::1]
        H2, W2 = E.H // 2, E.W // 2
        small = cv2.resize(arr, (W2, H2), interpolation=cv2.INTER_AREA)
        wmask = np.zeros((H2, W2), bool)
        x0, y0, x1, y1 = [int(round(v / 2)) for v in (r.left() + 1, r.top() + 1, r.right() - 1, r.bottom() - 1)]
        wmask[y0:y1, x0:x1] = True
        forbid = ~wmask
        cx0, cy0, cx1, cy1 = [int(v / 2) for v in (cell.left() - 3, cell.top() - 3, cell.right() + 5, cell.bottom() + 5)]
        forbid[cy0:cy1, cx0:cx1] = True
        # important: differs from its cell's plain colour
        important = np.zeros((H2, W2), bool)
        for col in range(S.COLS):
            for row in range(S.ROWS):
                if (col, row) == S.EMPTY:
                    continue
                ax, ay = r.left() + col * S.CELL_W * self.k0, r.top() + row * S.CELL_H * self.k0
                bx, by = ax + S.CELL_W * self.k0, ay + S.CELL_H * self.k0
                sx0, sy0, sx1, sy1 = int(ax / 2) + 2, int(ay / 2) + 2, int(bx / 2) - 2, int(by / 2) - 2
                patch = small[sy0:sy1, sx0:sx1]
                # the cell's own colour is simply its commonest colour
                q = patch.reshape(-1, 3).astype(np.int32) // 8
                keys = q[:, 0] * 4096 + q[:, 1] * 64 + q[:, 2]
                top = np.bincount(keys).argmax()
                bg = np.array([top // 4096, (top // 64) % 64, top % 64], np.float32) * 8 + 4
                important[sy0:sy1, sx0:sx1] = np.abs(patch - bg).sum(-1) > 42
        weight = np.where(important, 6.0, 1.0)
        weight[forbid] = 0
        covered = np.zeros((H2, W2), bool)
        placed = []
        def word_for(i):
            return WORDS[i % len(WORDS)]
        n = 0
        def place(w, rand_rot=22, targeted=False, tries=70):
            nonlocal n
            word, kind, font = word_for(n)
            scheme = SCHEMES[n % len(SCHEMES)]
            st = Sticker(word, kind, font, w, scheme, float(rng.normal(0, rand_rot * 0.45)))
            fp, rad = st.footprint()
            fh, fw = fp.shape
            best, score = None, -1
            need = np.argwhere(important & ~covered & ~forbid)
            for _ in range(tries):
                if targeted and len(need):
                    yy, xx = need[rng.integers(len(need))]
                    ox, oy = int(xx - fw / 2 + rng.integers(-fw // 5, fw // 5 + 1)), int(yy - fh / 2 + rng.integers(-fh // 5, fh // 5 + 1))
                else:
                    ox, oy = int(rng.integers(x0, max(x0 + 1, x1 - fw))), int(rng.integers(y0, max(y0 + 1, y1 - fh)))
                if ox < 0 or oy < 0 or ox + fw > W2 or oy + fh > H2:
                    continue
                if forbid[oy:oy + fh, ox:ox + fw][fp].any():
                    continue
                g = (weight[oy:oy + fh, ox:ox + fw] * (~covered[oy:oy + fh, ox:ox + fw]))[fp].sum()
                g *= rng.uniform(0.92, 1.08)
                if g > score:
                    best, score = (ox, oy), g
            if best is None or score <= 0:
                return False
            ox, oy = best
            covered[oy:oy + fh, ox:ox + fw] |= fp
            st.x, st.y = (ox + fw / 2) * 2, (oy + fh / 2) * 2
            placed.append(st)
            n += 1
            return True
        for w in [300, 280, 320, 260, 300, 270, 250, 280, 240, 260, 250, 230]:
            place(w)
        for _ in range(40):
            place(float(rng.uniform(150, 215)))
        for _ in range(40):
            place(float(rng.uniform(105, 145)), targeted=True)
        for _ in range(80):
            if not (important & ~covered & ~forbid).any():
                break
            place(float(rng.uniform(62, 90)), targeted=True, tries=120)
        self.left_bare = int((important & ~covered & ~forbid).sum())
        # now the plain wall too, hardest of all right up against the empty cell, so it stands clear as a hole
        important[~forbid] = True
        for _ in range(70):
            bare = float((important & ~covered & ~forbid).sum()) / float((~forbid).sum())
            if bare < 0.004:
                break
            place(float(rng.uniform(58, 86)), targeted=True, tries=120)
        self.bare_frac = float((important & ~covered & ~forbid).sum()) / float((~forbid).sum())
        # one slap on each syllable to begin with, then a growing handful
        # (from the second syllable: the first frames still are the last frame of the clip before, untouched)
        syl = [s["t"] for ln in (33, 34, 35) for s in K.LYRICS[ln]["syl"]][1:]
        counts = np.array([1 + 5.5 * (i / (len(syl) - 1)) ** 2.2 for i in range(len(syl))])
        counts = np.maximum(1, np.round(counts * (len(placed) / counts.sum())))
        counts[:5] = 1
        while counts.sum() > len(placed):
            counts[np.argmax(counts)] -= 1
        while counts.sum() < len(placed):
            counts[-1 - int(rng.integers(0, 6))] += 1
        k = 0
        for t_, m in zip(syl, counts):
            for j in range(int(m)):
                placed[k].t = t_ + j * 0.024
                k += 1
        # the figure above the empty cell throws a foot shadow into it; that goes when a sticker lands on those feet
        above = [q for q, cell_ in zip(self.standee_world(), S.ORDER) if cell_ == (S.EMPTY[0], S.EMPTY[1] - 1)][0]
        fx, fy = S.project((above[2], above[3], above[4] - above[1]["h_m"] / 2 + 0.06), self.t_ref)[:2]
        self.t_clean = K.LYRICS[35]["end"]
        for st in sorted(placed, key=lambda q: q.t):
            a_ = math.radians(-st.rot)
            lx, ly = (fx - st.x) * math.cos(a_) - (fy - st.y) * math.sin(a_), (fx - st.x) * math.sin(a_) + (fy - st.y) * math.cos(a_)
            if st.path.contains(lx, ly):
                self.t_clean = st.t
                break
        # and the last ones keep coming, crowding the empty cell without ever going in
        self.stickers = placed
        late = K.LYRICS[37]["syl"][4:11]
        ring = [(-1, -0.2), (1, 0.3), (-0.3, -1), (0.4, 1), (-1, 0.7), (1, -0.8), (0.0, -1)]
        for s_, (ax, ay) in zip(late, ring):
            word, kind, font = word_for(n)
            st = Sticker(word, kind, font, float(rng.uniform(120, 165)), SCHEMES[n % len(SCHEMES)], float(rng.normal(0, 10)))
            fp, rad = st.footprint()
            fh, fw = fp.shape
            cxm, cym = (cell.left() + cell.right()) / 4, (cell.top() + cell.bottom()) / 4
            gap = np.array([(cell.width() / 4 + fw / 2) * ax, (cell.height() / 4 + fh / 2) * ay]) if ax and abs(ax) == 1 and abs(ay) < 1 else None
            for sh in range(0, 60):
                if abs(ax) == 1:
                    gx = cxm + ax * (cell.width() / 4 + fw / 2 + sh)
                    gy = cym + ay * cell.height() / 4
                else:
                    gx = cxm + ax * cell.width() / 4
                    gy = cym + ay * (cell.height() / 4 + fh / 2 + sh)
                ox, oy = int(gx - fw / 2), int(gy - fh / 2)
                if ox < 0 or oy < 0 or ox + fw > W2 or oy + fh > H2:
                    continue
                if not forbid[oy:oy + fh, ox:ox + fw][fp].any():
                    st.x, st.y = (ox + fw / 2) * 2, (oy + fh / 2) * 2
                    st.t = s_["t"]
                    self.stickers.append(st)
                    n += 1
                    break

    # ---- the crayon drawing: every pixel gets the song time at which the crayon passes over it ----
    def build_flowers(self):
        im = cv2.imread(str(ROOT / "assets" / "gen" / "raw" / "k01_flowers.png"), cv2.IMREAD_COLOR)[..., ::-1]
        im = cv2.resize(im, (im.shape[1] // 2, im.shape[0] // 2), interpolation=cv2.INTER_AREA)
        h, w = im.shape[:2]
        f = im.astype(np.float32) / 255
        # pure white where the paper is, so nothing but crayon reaches the wall's paper under the multiply
        f = np.clip(f / 0.97, 0, 1)
        self.fl_rgb = (f * 255 + 0.5).astype(np.uint8)
        mx, mn = f.max(-1), f.min(-1)
        sat = (mx - mn) / np.maximum(mx, 1e-3)
        ink = sat > 0.22
        R, G, B = f[..., 0], f[..., 1], f[..., 2]
        yy, xx = np.mgrid[0:h, 0:w]
        side = (xx > 365)   # the two flowers
        labels = np.zeros((h, w), np.int32)
        centres = [(197.5, 182.5), (530.0, 192.5)]
        # by colour and by place: the pale edge of an orange petal is yellow by colour alone, and must wait for its petal
        near = np.minimum(np.hypot(xx - centres[0][0], yy - centres[0][1]), np.hypot(xx - centres[1][0], yy - centres[1][1])) < 64
        yellow = ink & (G > 0.72) & (R > 0.7) & (B < 0.55) & near
        green = ink & (G > R + 0.12) & (G > B + 0.1)
        petal = ink & ~yellow & ~green
        bounds = [(-120, -46, 21, 92, 165), (-131, -56, 20, 95, 165)]
        # order of drawing inside a flower: centre, top petal then clockwise, stem
        def part_id(fl, name):
            return fl * 10 + name + 1
        for fl in (0, 1):
            m = side if fl else ~side
            labels[m & yellow] = part_id(fl, 0)
            labels[m & green] = part_id(fl, 6)
            cx, cy = centres[fl]
            ang = np.degrees(np.arctan2(yy - cy, xx - cx))
            b = bounds[fl]
            sect = np.where((ang >= b[0]) & (ang < b[1]), 1,
                            np.where((ang >= b[1]) & (ang < b[2]), 2,
                                     np.where((ang >= b[2]) & (ang < b[3]), 3,
                                              np.where((ang >= b[3]) & (ang < b[4]), 4, 5))))
            labels[m & petal] = (part_id(fl, 0) + sect)[m & petal]
        # the paler flecks inside a part belong to the nearest coloured pixel
        dist, idx = cv2.distanceTransformWithLabels((labels == 0).astype(np.uint8), cv2.DIST_L2, 5, labelType=cv2.DIST_LABEL_PIXEL)
        where = np.argwhere(labels != 0)
        lab_of = np.zeros(idx.max() + 1, np.int32)
        lab_of[idx[labels != 0]] = labels[labels != 0]
        full = lab_of[idx]
        syl = K.LYRICS[36]["syl"]
        times = [s["t"] for s in syl]
        durs = [s["dur"] for s in syl]
        # one stroke-group per sung syllable: the first flower slowly, the second in a child's hurry
        plan = [((0, 0), 0, 1), ((0, 1), 1, 1), ((0, 2), 2, 1), ((0, 3), 3, 1), ((0, 4), 4, 1), ((0, 5), 5, 1), ((0, 6), 6, 1),
                ((1, 0), 7, 1), ((1, 1), 8, 0.5), ((1, 2), 8.5, 0.5), ((1, 3), 9, 0.5), ((1, 4), 9.5, 0.5), ((1, 5), 10, 1), ((1, 6), 11, 1)]
        tm = np.full((h, w), np.inf, np.float32)
        rng = np.random.default_rng(36)
        self.tracks = []
        sing_end = [times[int(s0)] + (s0 - int(s0)) * durs[int(s0)] for _, s0, _ in plan] + [times[-1] + durs[-1] - 0.05]
        for j, ((fl, nm), s0, length) in enumerate(plan):
            pid = part_id(fl, nm)
            core = ((labels == pid)).astype(np.uint8)
            region = (full == pid)
            if not core.any():
                continue
            i0 = int(s0)
            t_a = times[i0] + (s0 - i0) * durs[i0]
            next_ = sing_end[j + 1]
            # the crayon is on the paper for all but the moment it takes to carry it to the next place
            hop = 0.0 if j == len(plan) - 1 else (0.134 if length >= 1 else 0.067)
            t_b = next_ - hop
            # nm 0 is the centre, 6 the stem; a petal goes out from the centre and comes back, twice when there is time
            legs = 2 if nm == 6 else (3 if nm == 0 else (4 if length >= 1 else 2))
            pts = self.scribble(core, legs, centres[fl], rng)
            seg_len = np.hypot(*(pts[1:] - pts[:-1]).T)
            cum = np.concatenate([[0], np.cumsum(seg_len)])
            total = max(cum[-1], 1e-3)
            self.tracks.append(dict(a=t_a, b=t_b, pts=pts, cum=cum, total=total, fl=fl, nm=nm,
                                    col=np.median(self.fl_rgb[region & ink], axis=0)))
            # each pixel of this part takes the time of the nearest point of the path: nothing can appear away from the tip
            seeds = np.full((h, w), 1, np.uint8)
            when = np.zeros((h, w), np.float32)
            n_ = max(2, int(total / 2.0))
            for d_ in np.linspace(total, 0, n_):        # backwards, so the first pass over a pixel is the one that stays
                k_ = min(int(np.searchsorted(cum, d_, side="right")) - 1, len(pts) - 2)
                q_ = pts[k_] + (pts[k_ + 1] - pts[k_]) * (d_ - cum[k_]) / max(cum[k_ + 1] - cum[k_], 1e-3)
                x_, y_ = int(np.clip(q_[0], 0, w - 1)), int(np.clip(q_[1], 0, h - 1))
                seeds[y_, x_] = 0
                when[y_, x_] = t_a + (t_b - t_a) * d_ / total
            _, nearest = cv2.distanceTransformWithLabels(seeds, cv2.DIST_L2, 5, labelType=cv2.DIST_LABEL_PIXEL)
            by_label = np.zeros(nearest.max() + 1, np.float32)
            by_label[nearest[seeds == 0]] = when[seeds == 0]
            tm[region] = by_label[nearest][region]
        tm[~np.isfinite(tm)] = times[0]   # only plain paper is left: no time to wait for
        self.fl_t = tm
        # the finished drawing, smaller, for when the camera is far off
        done = cv2.resize(self.fl_rgb, (w // 3, h // 3), interpolation=cv2.INTER_AREA)
        self.fl_small = E.np_to_image(np.dstack([done, np.full(done.shape[:2], 255, np.uint8)]))
        self.fl_full = E.np_to_image(np.dstack([self.fl_rgb, np.full((h, w), 255, np.uint8)]))
        self.fl_end = float(tm.max())
        self.build_adult_hand()
        self.build_print()
        # the hand's drawing changes on fifteens: a change inside the shutter would print both hands at once
        self.cuts = tuple(self.cuts) + tuple(n / TICK for n in range(int(PUSH0 * TICK), int(PUSH1 * TICK) + 2))

    def build_print(self):
        """A snapshot of the original drawing, on its white print border."""
        k = 5
        W_, H_ = int(PRINT_W * k), int(PRINT_H * k)
        surf = skia.Surface(W_, H_)
        c = surf.getCanvas()
        c.clear(E.col("#FFFEF8"))
        b = 18
        im = E.np_to_image(np.dstack([self.fl_rgb, np.full(self.fl_rgb.shape[:2], 255, np.uint8)]))
        c.drawImageRect(im, skia.Rect.MakeXYWH(b, b, W_ - 2 * b, H_ - 2 * b - 10), skia.SamplingOptions(skia.FilterMode.kLinear, skia.MipmapMode.kLinear))
        c.drawRect(skia.Rect.MakeXYWH(b, b, W_ - 2 * b, H_ - 2 * b - 10), skia.Paint(AntiAlias=True, Color4f=E.col("#8F8C84"), Style=skia.Paint.kStroke_Style, StrokeWidth=2))
        c.drawRect(skia.Rect.MakeXYWH(0, 0, W_, H_), skia.Paint(AntiAlias=True, Color4f=E.col("#8F8C84"), Style=skia.Paint.kStroke_Style, StrokeWidth=3))
        draw_strokes(c, pappa_strokes(), W_ - 96, H_ - 24, 20, 2.4, 1.0)
        self.print_img = surf.makeImageSnapshot()
        self.print_t = self.tracks[0]["a"] - 0.30

    def draw_print(self, c, t):
        if t < self.print_t:
            return
        u = E.seg(t, self.print_t, self.print_t + 2 / 30)
        sc = 1.25 - 0.25 * u
        x, y = PRINT_C
        r = skia.Rect.MakeXYWH(-PRINT_W / 2, -PRINT_H / 2, PRINT_W, PRINT_H)
        # the same way as every other shadow on this wall
        c.save()
        c.translate(x - 1.6, y + 2.0)
        c.rotate(PRINT_ROT)
        c.scale(sc, sc)
        c.drawRect(r, skia.Paint(AntiAlias=True, Color4f=E.col("#3C4258", 0.55)))
        c.restore()
        c.save()
        c.translate(x, y)
        c.rotate(PRINT_ROT)
        c.scale(sc, sc)
        c.drawImageRect(self.print_img, r, skia.SamplingOptions(skia.FilterMode.kLinear, skia.MipmapMode.kLinear))
        # two bits of tape
        for tx in (-PRINT_W * 0.34, PRINT_W * 0.34):
            c.save()
            c.translate(tx, -PRINT_H / 2)
            c.rotate(-14 if tx < 0 else 12)
            E.rect(c, -11, -3.2, 22, 6.4, "#F2E6A8")
            c.restore()
        c.restore()

    def scribble(self, core, legs, centre, rng):
        """How he colours in: a few long strokes up and down the part, always on the part's own wax, never out over the paper."""
        ys, xs = np.nonzero(core)
        q0 = np.stack([xs, ys], 1).astype(np.float32)
        cen = q0.mean(0)
        q = q0 - cen
        w_, v_ = np.linalg.eigh(np.cov(q.T))
        d = v_[:, 1].astype(np.float32)
        # along the part's long axis, starting at the end nearest the flower's centre
        if float((np.array(centre, np.float32) - cen) @ d) > 0:
            d = -d
        n = np.array([-d[1], d[0]], np.float32)
        along, across = q @ d, q @ n
        lo_, hi_ = np.percentile(across, [12, 88])
        rows = [lo_ + (hi_ - lo_) * ((i + 0.5) / legs) for i in range(legs)] if legs > 1 else [0.0]
        band = max((hi_ - lo_) / legs, 6.0)
        pts = []
        for i, r in enumerate(rows):
            near = np.abs(across - r) < band
            a0, a1 = np.percentile(along[near], [4, 96]) if near.any() else (along.min(), along.max())
            ends = (a0, a1) if i % 2 == 0 else (a1, a0)
            for e in ends:
                pts.append(cen + d * e + n * (r + rng.uniform(-2.0, 2.0)))
        return np.array(pts, np.float32)

    def flowers(self, c, t, s):
        p = skia.Paint(AntiAlias=True)
        p.setBlendMode(skia.BlendMode.kMultiply)
        h, w = self.fl_t.shape
        wh = FLOWER_W * h / w
        rect = skia.Rect.MakeXYWH(WORLD_FLOWER[0] - FLOWER_W / 2, WORLD_FLOWER[1] - wh / 2, FLOWER_W, wh)
        samp = skia.SamplingOptions(skia.FilterMode.kLinear)
        if t >= self.fl_end:
            c.drawImageRect(self.fl_full if s > 2.6 else self.fl_small, rect, samp, p)
            return
        if t < self.fl_t.min():
            return
        key = int(math.floor(t * TICK + 1e-6))
        if self._reveal[0] != key:
            vis = self.fl_t <= key / TICK
            rgb = np.where(vis[..., None], self.fl_rgb, 255).astype(np.uint8)
            self._reveal = (key, E.np_to_image(np.dstack([rgb, np.full(vis.shape, 255, np.uint8)])))
        c.drawImageRect(self._reveal[1], rect, samp, p)

    # ---- the hand that draws them: a grown-up's. These flowers are not from her. ----
    def build_adult_hand(self):
        self.adult = {}
        base = None
        for key, name in ADULT:
            raw = C.load(ROOT / "assets" / "gen" / "cut" / f"{name}.png")
            tip = S07_tip(raw)
            # where the shirt cuff is: the wrist stays put from one drawing to the next, only fingers and crayon change
            r, g, b = raw[..., 0], raw[..., 1], raw[..., 2]
            ys, xs = np.nonzero((r < 0.3) & (g < 0.3) & (b < 0.35) & (r > 0.12) & (raw[..., 3] > 0.9))
            v = (float(xs.mean()) - tip[0], float(ys.mean()) - tip[1])
            base = base or v
            turn = math.degrees(math.atan2(base[1], base[0]) - math.atan2(v[1], v[0]))
            size = math.hypot(*base) / math.hypot(*v)
            # the whole crayon in the drawing is orange: the same stub in each colour he draws with, as a small patch over the picture
            yy_, xx_ = np.mgrid[0:raw.shape[0], 0:raw.shape[1]]
            wax = (r > 0.55) & (r - b > 0.45) & (r - g > 0.2) & (raw[..., 3] > 0.5) & (np.hypot(xx_ - tip[0], yy_ - tip[1]) < 560)
            lit = np.clip(r / np.median(r[wax]), 0.05, 1.0)[..., None]
            # and the pixels where its colour runs into the outline
            wax |= (cv2.dilate(wax.astype(np.uint8), np.ones((5, 5), np.uint8)) > 0) & (r - b > 0.10) & (r - g > 0.04)
            ys, xs = np.nonzero(wax)
            x0, x1, y0, y1 = xs.min() - 2, xs.max() + 3, ys.min() - 2, ys.max() + 3
            pics = {}
            for tr in self.tracks:
                ck = tuple(int(u) // 24 for u in tr["col"])
                if ck not in pics:
                    im = raw[y0:y1, x0:x1].copy()
                    im[..., :3] = np.where(wax[y0:y1, x0:x1, None], np.clip(tr["col"].astype(np.float32) / 255 * lit[y0:y1, x0:x1], 0, 1), im[..., :3])
                    pics[ck] = E.np_to_image(im)
            ex = HK.extrude(raw, ADULT_SLEEVE, loose=SLEEVE_LOOSE)
            self.adult[key] = dict(img=E.np_to_image(ex), pics=pics, tip=tip, turn=turn, size=size, wax_at=(float(x0), float(y0)))

    def crayon_at(self, q):
        """Where the crayon is at time q in flower-picture pixels, the part it is on, and how far off the paper it is, 0 to 1."""
        trs = self.tracks
        if q < trs[0]["a"]:
            return trs[0]["pts"][0], trs[0], 1.0
        for i, tr in enumerate(trs):
            if q < tr["a"]:
                # carried from the end of the last part to the start of this one, in the air
                pr = trs[i - 1]
                u = E.ease_io(E.seg(q + 1 / TICK, pr["b"], tr["a"] + 1 / TICK), 1.5)
                return pr["pts"][-1] + (tr["pts"][0] - pr["pts"][-1]) * u, tr, math.sin(math.pi * u)
            if q < tr["b"]:
                d = (q - tr["a"]) / (tr["b"] - tr["a"]) * tr["total"]
                k = min(max(int(np.searchsorted(tr["cum"], d, side="right")) - 1, 0), len(tr["pts"]) - 2)
                seg = max(tr["cum"][k + 1] - tr["cum"][k], 1e-3)
                return tr["pts"][k] + (tr["pts"][k + 1] - tr["pts"][k]) * (d - tr["cum"][k]) / seg, tr, 0.0
        return trs[-1]["pts"][-1], trs[-1], 0.0

    def adult_hand(self, c, t):
        """Comes in as the first stroke starts, stays with the crayon on its own marks, and leaves before the stamp.
        The tip is exactly where the wax is being laid down in this very frame."""
        t0, t1 = self.tracks[0]["a"], self.tracks[-1]["b"]
        IN_, OUT_ = 0.30, STAMP - t1
        if t < t0 - IN_ or t >= t1 + OUT_:
            return
        q = math.floor(t * TICK + 1e-6) / TICK
        h, w = self.fl_t.shape
        k = FLOWER_W / w
        ox, oy = WORLD_FLOWER[0] - FLOWER_W / 2, WORLD_FLOWER[1] - FLOWER_W * h / w / 2
        tip, tr, air = self.crayon_at(q)
        x, y = ox + float(tip[0]) * k, oy + float(tip[1]) * k
        # in from, and out to, the lower right of the sheet
        off = E.ease_in(1 - E.seg(q, t0 - IN_, t0), 2.2) if q < t0 else (E.ease_in(E.seg(q, t1, t1 + OUT_), 1.6) if q >= t1 else 0.0)
        x += 240 * off
        y += 170 * off
        # one calm drawing per part, changed while the crayon is in the air, with the arm swinging from the elbow
        key = "hard" if tr["nm"] % 2 else "press"
        v = self.adult[key]
        y -= 1.2 * air
        S_ = ADULT_S * v["size"]
        rot = v["turn"] + 3.2 * (float(tip[0]) - 330) / 330
        z = 2.6 + 6.0 * max(air, off)
        ck = tuple(int(u) // 24 for u in tr["col"])
        samp = skia.SamplingOptions(skia.FilterMode.kLinear, skia.MipmapMode.kLinear)
        c.save()
        c.translate(x + z * 0.85, y + z)
        c.rotate(rot)
        c.scale(S_, S_)
        c.translate(-v["tip"][0], -v["tip"][1])
        c.drawImage(v["img"], 0, 0, samp, skia.Paint(AntiAlias=True, ColorFilter=skia.ColorFilters.Blend(E.col("#2A3A4C", 0.34), skia.BlendMode.kSrcIn)))
        c.restore()
        c.save()
        c.translate(x, y)
        c.rotate(rot)
        c.scale(S_, S_)
        c.translate(-v["tip"][0], -v["tip"][1])
        c.drawImage(v["img"], 0, 0, samp)
        c.drawImage(v["pics"][ck], v["wax_at"][0], v["wax_at"][1], samp)
        c.restore()

    # ---- the stamp: a real rubber stamp leaves uneven ink ----
    def build_stamp(self):
        W_, H_ = 1500, 520
        surf = skia.Surface(W_, H_)
        c = surf.getCanvas()
        c.clear(skia.Color4f(0, 0, 0, 0))
        p = skia.Paint(AntiAlias=True, Color4f=E.col(E.RED), Style=skia.Paint.kStroke_Style, StrokeWidth=26)
        c.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(30, 30, W_ - 60, H_ - 60), 26, 26), p)
        p2 = skia.Paint(AntiAlias=True, Color4f=E.col(E.RED), Style=skia.Paint.kStroke_Style, StrokeWidth=7)
        c.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(66, 66, W_ - 132, H_ - 132), 12, 12), p2)
        ty = E.fit("回答なし", "ZenKakuGothicNew-Black", W_ - 230, H_ - 210, max_size=400)
        ty.draw(c, W_ / 2, H_ / 2, E.RED)
        arr = surf.makeImageSnapshot().toarray(colorType=skia.ColorType.kRGBA_8888_ColorType, alphaType=skia.AlphaType.kUnpremul_AlphaType).astype(np.float32) / 255
        rng = np.random.default_rng(37)
        fine = cv2.resize(rng.random((H_ // 2, W_ // 2), dtype=np.float32), (W_, H_), interpolation=cv2.INTER_LINEAR)
        blot = cv2.resize(rng.random((H_ // 60, W_ // 60), dtype=np.float32), (W_, H_), interpolation=cv2.INTER_CUBIC)
        # ink runs thin in patches: gaps only where the blotch and the paper tooth agree
        keep = ((fine + (blot - 0.5) * 0.9) > 0.20).astype(np.float32)
        keep = cv2.GaussianBlur(keep, (0, 0), 0.8)
        arr[..., 3] *= keep
        arr[..., :3] = np.array([0xE5, 0x16, 0x2E], np.float32) / 255
        small = cv2.resize(arr, (W_ // 4, H_ // 4), interpolation=cv2.INTER_AREA)
        small[..., :3] = np.array([0xE5, 0x16, 0x2E], np.float32) / 255
        self.stamp_big, self.stamp_small = E.np_to_image(arr), E.np_to_image(small)

    def stamp(self, c, t, s):
        if t < STAMP - 0.067:
            return
        u = E.ease_in(E.seg(t, STAMP - 0.067, STAMP), 2)
        sc = 1.5 - 0.5 * u
        WW = 188.0   # width on the wall, in wide-shot pixels
        c.save()
        c.translate(968, 593)
        c.rotate(-8)
        c.scale(sc, sc)
        im = self.stamp_big if s > 2.2 else self.stamp_small
        hh = WW * im.height() / im.width()
        p = skia.Paint(AntiAlias=True)
        p.setBlendMode(skia.BlendMode.kMultiply)
        c.drawImageRect(im, skia.Rect.MakeXYWH(-WW / 2, -hh / 2, WW, hh), skia.SamplingOptions(skia.FilterMode.kLinear), p)
        c.restore()

    # ---- camera ----
    def camera(self, t):
        if t < PUSH0:
            return 1.0, 960.0, 540.0
        if t < STAMP:
            u = E.ease_io(E.seg(t, PUSH0, PUSH1), 2.4)
            # almost imperceptibly on, all through the drawing
            creep = 1 + 0.03 * E.seg(t, PUSH1, STAMP)
            s = math.exp(math.log(ZOOM) * u) * creep
        elif t < PULL0:
            s = ZOOM * 1.03
        else:
            u = E.ease_io(E.seg(t, PULL0, PULL1), 2.0)
            s = math.exp(math.log(ZOOM * 1.03) * (1 - u))
        # any zoom between wide and close keeps the same fixed point: a straight move, no sliding
        k = (1 - 1 / s) / (1 - 1 / ZOOM)
        return s, 960 + (FOCUS[0] - 960) * k, 540 + (FOCUS[1] - 540) * k

    def world(self, c, t, s, cursor=True):
        """Everything on the wall, drawn in wide-shot coordinates under the current camera."""
        c.drawImageRect(self.base, skia.Rect.MakeWH(E.W, E.H), skia.SamplingOptions(skia.FilterMode.kLinear))
        for st in self.stickers:
            if t >= st.t - 0.067:
                st.draw(c, t)
        if s > 2.0:
            c.drawImageRect(self.cell_img, self.cell, skia.SamplingOptions(skia.FilterMode.kLinear))
        elif t >= self.t_clean:
            c.drawImageRect(self.cell_mid, self.cell, skia.SamplingOptions(skia.FilterMode.kLinear))
        if cursor and t < STAMP and int((t - 111.6) / 0.24) % 2 == 0:
            ex, ez = S.cell_center(*S.EMPTY)
            q = S.project((ex - S.CELL_W * 0.30, 0.0, ez - S.CELL_H * 0.5 + S.CELL_H * 0.385), self.t_ref)
            E.rect(c, q[0], q[1] - 0.26 * self.k0, 0.06 * self.k0, 0.26 * self.k0, E.RED)
        self.draw_print(c, t)
        self.flowers(c, t, s)
        self.adult_hand(c, t)
        self.stamp(c, t, s)

    def apply(self, c, s, cx, cy, jolt=0.0):
        c.translate(960, 540 + jolt)
        c.scale(s, s)
        c.translate(-cx, -cy)

    # ---- the two photographs ----
    def photo(self, n):
        if n in self._photos:
            return self._photos[n]
        PW, PH = 1440, 810
        B, FOOT = 26, 78
        surf = skia.Surface(PW + 2 * B, PH + B + FOOT)
        c = surf.getCanvas()
        c.clear(E.col("#FFFEF8"))
        inner = skia.Surface(1920, 1080)
        ic = inner.getCanvas()
        ic.clear(E.col(E.CYAN))
        t = PA[0] + 0.001
        if n == 0:
            s, cx, cy = 1.0, 960.0, 540.0
        else:
            s, cx, cy = TAKE2_ZOOM, self.cell.centerX(), self.cell.centerY()
        ic.save()
        self.apply(ic, s, cx, cy)
        self.world(ic, t + 0.5, s, cursor=False)
        ic.restore()
        c.save()
        c.translate(B, B)
        c.scale(PW / 1920, PH / 1080)
        c.drawImage(inner.makeImageSnapshot(), 0, 0, skia.SamplingOptions(skia.FilterMode.kLinear, skia.MipmapMode.kNone))
        c.restore()
        # a hairline: white sticker edges must not melt into the white margin of the print
        c.drawRect(skia.Rect.MakeXYWH(B, B, PW, PH), skia.Paint(AntiAlias=True, Color4f=E.col("#8F8C84"), Style=skia.Paint.kStroke_Style, StrokeWidth=2))
        img = surf.makeImageSnapshot()
        self._photos[n] = img
        return img

    def draw_photos(self, c, t):
        c.clear(E.col(E.CYAN))
        for n, (x, y, rot) in enumerate([(944, 482, -3.2), (980, 492, 2.6)]):
            if t < PA[n] + FLASH:
                continue
            img = self.photo(n)
            u = E.ease_out(E.seg(t, PA[n] + FLASH, PA[n] + FLASH + 0.14), 3)
            sc = 1.03 - 0.03 * u
            c.save()
            c.translate(x, y)
            c.rotate(rot)
            c.scale(sc, sc)
            w, h = img.width(), img.height()
            sh = skia.Paint(AntiAlias=True, Color4f=E.col("#0A5F86"))
            c.drawRect(skia.Rect.MakeXYWH(-w / 2 - 14, -h / 2 + 18, w, h), sh)
            c.drawImage(img, -w / 2, -h / 2, E.SAMPLING)
            if n == 1:
                # the same two syllables, in somebody's hand, written on the print afterwards
                u_ = E.ease_io(E.seg(t, PA[1] + FLASH + 0.12, PA[1] + FLASH + 0.52), 1.4)
                if u_ > 0:
                    draw_strokes(c, self.hand, w / 2 - 212, h / 2 - 66, 54, 5.0, u_)
            c.restore()

    def shutter_blades(self, c, t):
        """An iris: hard ink blades closing to nothing, a flat white frame, then opening on the new picture."""
        for pa in PA:
            a, b, d = pa - CLOSE, pa + FLASH, pa + FLASH + OPEN
            if a <= t < pa:
                r = 1180 * (1 - E.ease_in(E.seg(t, a, pa), 1.6))
            elif pa <= t < b:
                c.clear(E.col("#FFFEF8"))
                return
            elif b <= t < d:
                r = 1180 * E.ease_out(E.seg(t, b, d), 2)
            else:
                continue
            n = 7
            turn = math.radians(38) * (1 - r / 1180) - 0.4
            pts = [(960 + r * math.cos(turn + i / n * math.tau), 540 + r * math.sin(turn + i / n * math.tau)) for i in range(n)]
            p = skia.Path()
            p.setFillType(skia.PathFillType.kEvenOdd)
            p.addRect(skia.Rect.MakeXYWH(-40, -40, E.W + 80, E.H + 80))
            p.moveTo(*pts[0])
            for q in pts[1:]:
                p.lineTo(*q)
            p.close()
            c.drawPath(p, skia.Paint(AntiAlias=True, Color4f=E.col(E.INK)))
            # blade edges run on past the opening
            ln = skia.Paint(AntiAlias=True, Color4f=E.col("#2B2E3A"), StrokeWidth=6)
            for i in range(n):
                q0, q1 = np.array(pts[i]), np.array(pts[(i + 1) % n])
                e = q1 + (q1 - q0) / max(np.hypot(*(q1 - q0)), 1) * 2400
                c.drawLine(q1[0], q1[1], float(e[0]), float(e[1]), ln)
            return

    def blur(self, t):
        if PUSH0 <= t <= PUSH1:
            return 24
        if PULL0 + 0.6 <= t <= PULL1 - 0.3:
            return 4
        return 1

    def draw(self, c, t):
        if t >= PA[0] + FLASH:
            self.draw_photos(c, t)
        else:
            c.clear(E.col(E.CYAN))
            s, cx, cy = self.camera(t)
            jolt = 16 * math.exp(-(t - STAMP) * 22) if t >= STAMP else 0.0
            c.save()
            self.apply(c, s, cx, cy, jolt)
            self.world(c, t, s)
            c.restore()
        self.shutter_blades(c, t)
        for a, b, st, dark in self.strips:
            if a <= t < b:
                if dark:
                    st.draw(c, 960, 1034, t, ax=0.5, color=E.PAPER, paper=E.INK)
                else:
                    st.draw(c, 960, 1034, t, ax=0.5)
