"""Section 03: everybody lays her past out on the table, the red pens come in, and two shutter clicks make it a photograph."""
import math
import sys
from pathlib import Path

import cv2
import numpy as np
import skia

sys.path.insert(0, str(Path(__file__).parent))
import common as K  # noqa: E402
import engine as E  # noqa: E402
import bar as B  # noqa: E402

ROOT = K.ROOT
RAW = ROOT / "assets" / "gen" / "raw"
F0, F1 = 1566, 1996
NOTES = [s["t"] for s in K.LYRICS[16]["syl"]]     # 12 long notes: one thing on each
RED_NOTES = [s["t"] for s in K.LYRICS[17]["syl"]]  # chot to chot to ma chi ga e ta ka ra pa pa
PEN_IN = RED_NOTES[0]
WIDE = RED_NOTES[4]        # ma: back to the whole table, more pens
# Measured in the audio: the sung パッ / パ start at 65.12 and 65.58 and stop dead at 65.42 and 65.88; a last hit at 66.04.
# So the click runs on the sung attack and the finished photograph stands in the silence (65.4, 65.9).
SHOT1, SHOT2, LAST_HIT = 65.12, 65.58, 66.04
CLOSE, BLACK_TO, WHITE_TO, OPEN_TO = 0.10, 0.14, 0.20, 0.30

SHADOW = 0.30
HAND = "KleeOne-SemiBold"
LIGHT = np.array([0.78, 1.0])  # every hard shadow falls this way (right and down)


def fill(color, alpha=1.0):
    return skia.Paint(AntiAlias=True, Color4f=E.col(color, alpha))


def line_paint(color, w, alpha=1.0):
    return skia.Paint(AntiAlias=True, Color4f=E.col(color, alpha), Style=skia.Paint.kStroke_Style, StrokeWidth=w,
                      StrokeCap=skia.Paint.kRound_Cap, StrokeJoin=skia.Paint.kRound_Join)


def poly(pts, close=True):
    p = skia.Path()
    p.moveTo(*pts[0])
    for q in pts[1:]:
        p.lineTo(*q)
    if close:
        p.close()
    return p


# ---- handwriting, by stroke order ----
PAPPA = [
    [  # パ
        [(0.33, 0.20), (0.27, 0.48), (0.05, 0.86)],
        [(0.60, 0.20), (0.76, 0.52), (0.95, 0.84)],
        [(0.86, 0.02), (0.97, 0.08), (0.97, 0.20), (0.85, 0.22), (0.78, 0.13), (0.86, 0.02)],
    ],
    [  # ッ (small)
        [(0.08, 0.46), (0.18, 0.62)],
        [(0.34, 0.40), (0.44, 0.56)],
        [(0.72, 0.38), (0.62, 0.66), (0.28, 0.94)],
    ],
    [  # パ
        [(0.31, 0.16), (0.24, 0.46), (0.03, 0.82)],
        [(0.58, 0.18), (0.75, 0.48), (0.96, 0.86)],
        [(0.84, 0.00), (0.96, 0.05), (0.96, 0.18), (0.84, 0.20), (0.77, 0.11), (0.84, 0.00)],
    ],
]


def draw_pappa(c, x, y, h, color=E.INK, seed=4):
    """The small handwritten word, ~2.75 h wide, with (x, y) its top left. Each stroke presses, then lifts."""
    rng = np.random.default_rng(seed)
    adv = [1.04, 0.74, 1.0]
    px = x
    for ch, a in zip(PAPPA, adv):
        for st in ch:
            pts = [(px + u * h + rng.normal(0, h * 0.008), y + v * h + rng.normal(0, h * 0.008)) for u, v in st]
            arr = B._catmull(pts, 8)
            for i in range(len(arr) - 1):
                w = h * 0.085 * (1.15 - 0.55 * i / max(len(arr) - 2, 1))
                c.drawLine(arr[i][0], arr[i][1], arr[i + 1][0], arr[i + 1][1], line_paint(color, w))
        px += a * h


# ---- paper ----
def sheet_shape(w, h, ear=None, seed=1, wob=1.6):
    """A sheet outline: not a perfect rectangle. ear = (corner index 0..3 clockwise from top left, size) folds that corner over."""
    rng = np.random.default_rng(seed)
    cs = [(0.0, 0.0), (w, 0.0), (w, h), (0.0, h)]
    cs = [(x + rng.normal(0, wob), y + rng.normal(0, wob)) for x, y in cs]
    pts = []
    for i, q in enumerate(cs):
        a = cs[(i - 1) % 4]
        b = cs[(i + 1) % 4]
        if ear and ear[0] == i:
            d = ear[1]
            la, lb = math.dist(q, a), math.dist(q, b)
            pts.append((q[0] + (a[0] - q[0]) / la * d, q[1] + (a[1] - q[1]) / la * d))
            pts.append((q[0] + (b[0] - q[0]) / lb * d, q[1] + (b[1] - q[1]) / lb * d))
        else:
            pts.append(q)
    return pts, cs


def draw_sheet(c, w, h, color=E.PAPER, ear=None, folds=(), seed=1, outline=2.2):
    """The paper itself: a body colour, a darker half across each fold, a crease, a turned-over corner, and an ink line."""
    pts, cs = sheet_shape(w, h, ear, seed)
    path = poly(pts)
    c.drawPath(path, fill(color))
    c.save()
    c.clipPath(path, True)
    for f in folds:
        if f[0] == "v":     # vertical crease at x; the side towards the light stays bright
            E.rect(c, f[1], -5, w - f[1] + 5, h + 10, E.INK, 0.055)
            c.drawLine(f[1], 0, f[1], h, line_paint(E.INK, 1.6, 0.26))
            c.drawLine(f[1] - 2, 0, f[1] - 2, h, line_paint("#FFFFFF", 1.4, 0.55))
        else:
            E.rect(c, -5, f[1], w + 10, h - f[1] + 5, E.INK, 0.055)
            c.drawLine(0, f[1], w, f[1], line_paint(E.INK, 1.6, 0.26))
            c.drawLine(0, f[1] - 2, w, f[1] - 2, line_paint("#FFFFFF", 1.4, 0.55))
    c.restore()
    return path, pts, cs


def draw_ear(c, pts, ear, cs, color="#D9D5C8"):
    """The turned-over corner, on top of whatever is printed there."""
    q = cs[ear[0]]
    a, b = pts[ear[0]], pts[ear[0] + 1]
    # the corner, mirrored over the fold line
    mx, my = (a[0] + b[0]) / 2, (a[1] + b[1]) / 2
    r = (2 * mx - q[0], 2 * my - q[1])
    c.drawPath(poly([(a[0] + 5, a[1] + 8), (r[0] + 6, r[1] + 9), (b[0] + 5, b[1] + 8)]), fill(E.INK, 0.16))
    c.drawPath(poly([a, r, b]), fill(color))
    c.drawPath(poly([a, r, b]), line_paint(E.INK, 2.0))


def outline(c, path, w=2.2):
    c.drawPath(path, line_paint(E.INK, w))


def text_v(c, s, x, y, font, size, color=E.INK, step=None):
    """Vertical text, one glyph at a time from (x centre, y top). Returns the y it ended at."""
    step = size * 1.08 if step is None else step
    for ch in s:
        if ch != "　":
            ty = E.Type(ch, font, size, vertical=True)
            ty.draw(c, x, y + step / 2, color)
        y += step
    return y


def blot(c, cx, cy, length, thick, angle=0.0, seed=1):
    """A name or an answer gone under marker. No handwriting on it: just gone."""
    bar = B.Bar(cx, cy, length, thick, angle, seed, text=False, passes=7)
    bar.draw(c)


def bgr_image(bgr):
    return E.np_to_image(np.dstack([bgr[..., ::-1], np.full(bgr.shape[:2], 255, np.uint8)]))


def screen_print(path, cell=6.0):
    """A black-and-white picture of her, drawn in her own hand in flat greys, printed the way a cheap magazine prints it: ink and paper only, the greys become dots."""
    g = cv2.cvtColor(cv2.imread(str(path)), cv2.COLOR_BGR2GRAY).astype(np.float32) / 255
    h, w = g.shape
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    a = math.radians(45)
    u = (xx * math.cos(a) + yy * math.sin(a)) / cell * math.tau
    v = (-xx * math.sin(a) + yy * math.cos(a)) / cell * math.tau
    dots = (np.cos(u) * np.cos(v) + 1) / 2
    # white stays paper and ink stays ink, so her line is never broken up
    m = np.clip((np.clip((g - 0.10) / 0.82, 0, 1) - dots * 0.98) * 4 + 0.5, 0, 1)
    ink, paper = np.array([29, 23, 23], np.float32), np.array([232, 240, 243], np.float32)   # BGR
    return bgr_image((ink + (paper - ink) * m[..., None] + 0.5).astype(np.uint8))


class Item:
    def __init__(self, name, x, y, w, h, rot, frm, pic, lift=(8, 8, 12, 8), shape=None):
        self.name, self.x, self.y, self.w, self.h, self.rot = name, x, y, w, h, rot
        self.frm = frm      # the side it is pushed in from (unit vector)
        self.pic = pic
        self.lift = lift    # how far each corner stands off the table: more shadow there
        self.shape = shape or [(0, 0), (w, 0), (w, h), (0, h)]
        self.t_in = 0.0
        self.push = []      # later items knock it a little: (time, dx, dy, drot)

    def rest(self, t=1e9):
        x, y, r = self.x, self.y, self.rot
        for tt, dx, dy, dr in self.push:
            u = E.ease_out(E.seg(t, tt, tt + 0.14), 3)
            x += dx * u
            y += dy * u
            r += dr * u
        return x, y, r

    def pose(self, t):
        x, y, r = self.rest(t)
        u = E.ease_out(E.seg(t, self.t_in, self.t_in + 0.40), 4.2)
        d = (1 - u) * 2600
        return x + self.frm[0] * d, y + self.frm[1] * d, r + (1 - u) * 16 * (1 if self.frm[0] > 0 else -1)

    def loc(self, u, v):
        """World position of a point given in the item's own units, once it has come to rest."""
        x, y, r = self.rest()
        a = math.radians(r)
        dx, dy = u - self.w / 2, v - self.h / 2
        return (x + dx * math.cos(a) - dy * math.sin(a), y + dx * math.sin(a) + dy * math.cos(a))


def record(w, h, fn, pad=40):
    rec = skia.PictureRecorder()
    c = rec.beginRecording(skia.Rect.MakeLTRB(-pad, -pad, w + pad, h + pad))
    fn(c)
    return rec.finishRecordingAsPicture()


# ---- the things, one by one ----
def make_flowers():
    img = E.load_image(RAW / "k01_flowers.png")
    w, h = 660, 440
    ear = (1, 44)

    def f(c):
        path, pts, cs = draw_sheet(c, w, h, E.PAPER, ear, folds=(("v", 330),), seed=2)
        c.save()
        c.clipPath(path, True)
        c.scale(w / img.width(), h / img.height())
        pa = skia.Paint(AntiAlias=True)
        pa.setBlendMode(skia.BlendMode.kMultiply)
        c.drawImage(img, 0, 0, E.SAMPLING, pa)
        c.restore()
        draw_ear(c, pts, ear, cs)
        outline(c, path)
    return w, h, f, sheet_shape(w, h, ear, 2)[0]


def make_crayon():
    img = E.load_image(RAW / "r03_crayon.png")
    w, h = 345, 460
    bar = B.Bar(492, 472, 450, 165, -1.0, 41)
    ear = (2, 34)

    def f(c):
        path, pts, cs = draw_sheet(c, w, h, E.PAPER, ear, seed=3)
        c.save()
        c.clipPath(path, True)
        c.scale(w / img.width(), h / img.height())
        pa = skia.Paint(AntiAlias=True)
        pa.setBlendMode(skia.BlendMode.kMultiply)
        c.drawImage(img, 0, 0, E.SAMPLING, pa)
        bar.draw(c)
        c.restore()
        draw_ear(c, pts, ear, cs)
        outline(c, path)
    return w, h, f, sheet_shape(w, h, ear, 3)[0]


def make_badge():
    w, h = 250, 150

    def f(c):
        # a plastic school name badge with its safety pin behind
        c.drawLine(24, 16, w - 24, 16, line_paint("#6E7686", 5))
        E.rect(c, 0, 0, w, h, "#FBFAF5", radius=16)
        c.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(0, 0, w, h), 16, 16), line_paint(E.INK, 2.6))
        E.rect(c, 10, 10, w - 20, 36, "#2B3A6B", radius=7)
        E.fit("六年二組", "ZenKakuGothicNew-Bold", w - 60, 24, max_size=24).draw(c, w / 2, 28, E.PAPER)
        blot(c, w / 2, 98, 176, 50, -1.0, 12)
        # the shine of the plastic cover
        c.drawPath(poly([(30, 0), (84, 0), (40, h), (-14, h)]), fill("#FFFFFF", 0.10))
    return w, h, f, None


def make_cert():
    w, h = 450, 640

    def f(c):
        path, _, _ = draw_sheet(c, w, h, "#FAF7EC", folds=(), seed=4)
        gold = "#C2A24C"
        for m, t in ((16, 6.5), (30, 1.8)):
            c.drawRect(skia.Rect.MakeLTRB(m, m, w - m, h - m), line_paint(gold, t))
        for i, (x, y) in enumerate(((30, 30), (w - 30, 30), (w - 30, h - 30), (30, h - 30))):
            c.drawCircle(x, y, 13, fill(gold))
        B_ = "YujiSyuku-Regular"
        E.fit("賞状", B_, 150, 190, vertical=True, max_size=84).draw(c, w - 84, 150, E.INK)
        # right to left: the name, the citation, the date, who gave it
        blot(c, w - 172, 150, 180, 42, 90.5, 13)
        E.Type("殿", B_, 34).draw(c, w - 172, 280, E.INK)
        cols = ["あなたは読書感想文", "コンクールにおいて優秀な", "成績をおさめましたので", "ここに賞します"]
        for i, s_ in enumerate(cols):
            text_v(c, s_, w - 226 - i * 36, 78, B_, 27, E.INK, 32)
        text_v(c, "三月十日", 92, 400, B_, 22, E.INK, 26)
        text_v(c, "第四小学校長", 56, 372, B_, 22, E.INK, 26)
        # the seal: faded, it is years old. The only red here belongs to the pen.
        E.rect(c, 37, 536, 38, 38, "#B5725A", radius=3)
        E.Type("印", B_, 25).draw(c, 56, 555, "#FAF7EC")
        outline(c, path)
    return w, h, f, None


def make_report():
    w, h = 540, 372

    def f(c):
        path, _, _ = draw_sheet(c, w, h, "#EEF0E2", folds=(("v", w / 2),), seed=5)
        G = "ZenKakuGothicNew-Bold"
        E.Type("通知表", G, 36).draw(c, 32, 40, E.INK, ax=0)
        E.Type("六年二組", "ZenKakuGothicNew-Medium", 20).draw(c, w / 2 - 16, 44, E.INK, ax=1)
        subj = ["国語", "算数", "理科", "社会", "音楽", "図工", "体育"]
        marks = ["○", "△", "○", "○", "◎", "◎", "△"]
        x0, y0 = 28, 72
        rw, rh = w / 2 - 50, 38
        for i, (s, m) in enumerate(zip(subj, marks)):
            y = y0 + i * rh
            c.drawRect(skia.Rect.MakeXYWH(x0, y, rw, rh), line_paint(E.INK, 1.5))
            c.drawLine(x0 + rw * 0.62, y, x0 + rw * 0.62, y + rh, line_paint(E.INK, 1.5))
            E.Type(s, "ZenKakuGothicNew-Medium", 21).draw(c, x0 + rw * 0.31, y + rh / 2, E.INK)
            E.Type(m, "ZenKakuGothicNew-Medium", 23).draw(c, x0 + rw * 0.81, y + rh / 2, E.INK)
        # the teacher's words, by hand
        rx = w / 2 + 28
        E.Type("先生から", G, 22).draw(c, rx, 44, E.INK, ax=0)
        c.drawRect(skia.Rect.MakeXYWH(rx, 72, w - rx - 26, 7 * rh), line_paint(E.INK, 1.5))
        for i, s in enumerate(["おとなしいですが", "友だちにやさしく", "絵がとても上手です。", "もう少し手を", "あげましょう。"]):
            E.Type(s, HAND, 23).draw(c, rx + 14, 98 + i * 48, E.INK, ax=0, ay=0)
            c.drawLine(rx + 10, 130 + i * 48, w - 36, 130 + i * 48, line_paint(E.INK, 1.0, 0.3))
        outline(c, path)
    return w, h, f, None


COMPOSITION = [
    # a column of 20 squares each, right to left. # is under the marker.
    "　　　将来の夢",
    "　　　　　　　六年二組　######",
    "　わたしの将来の夢は、#########",
    "#####になることです。",
    "　なぜかというと、小さいころ",
    "友だちがほめてくれたからです。",
    "　いつか、その友だちに見せたいです。",
]


def make_composition():
    cell = 32
    gap = 34
    m = 26
    w = 20 * cell + gap + 2 * m
    h = 20 * cell + 2 * m
    ear = (3, 52)
    grid = "#6FA08C"

    def f(c):
        path, pts, cs = draw_sheet(c, w, h, "#F7F4E6", ear, folds=(("v", w / 2), ("h", h / 2)), seed=6)
        x_right = w - m
        # 400 squares, 20 x 20, with the gutter in the middle
        def col_x(i):
            return x_right - (i + 1) * cell - (gap if i >= 10 else 0)
        for i in range(20):
            x = col_x(i)
            for r in range(20):
                c.drawRect(skia.Rect.MakeXYWH(x, m + r * cell, cell, cell), line_paint(grid, 1.3))
        c.drawRect(skia.Rect.MakeXYWH(m, m, w - 2 * m, h - 2 * m), line_paint(grid, 2.6))
        blots = []
        for i, s in enumerate(COMPOSITION):
            cx = col_x(i) + cell / 2
            for r, ch in enumerate(s):
                cy = m + r * cell + cell / 2
                if ch == "#":
                    blots.append((i, r))
                    continue
                if ch == "　":
                    continue
                if ch in "、。":
                    # punctuation sits in the top right of its square
                    ty = E.Type(ch, HAND, 25)
                    ty.draw(c, cx + 7, cy - 7, E.INK)
                else:
                    size = 28 if i else 29
                    E.Type(ch, HAND, size).draw(c, cx, cy, E.INK)
        # marker over the answer and the name, column by column
        by = {}
        for i, r in blots:
            by.setdefault(i, []).append(r)
        for i, rs in by.items():
            cx = col_x(i) + cell / 2
            top, bot = m + min(rs) * cell, m + (max(rs) + 1) * cell
            blot(c, cx, (top + bot) / 2, (bot - top) * 1.16, cell * 1.05, 90.0, 20 + i)
        draw_ear(c, pts, ear, cs, "#E2DFD0")
        outline(c, path)
    w_, h_ = w, h
    return w_, h_, f, sheet_shape(w, h, ear, 6)[0]


def photo_print(c, w, h, border, image, crop=None, bar=None, caption=None, seed=7, gloss=True):
    """A glossy print: white border, the picture, one hard band of shine."""
    path, _, _ = draw_sheet(c, w, h, "#FBFBF8", seed=seed)
    bb = caption[1] if caption else border
    x, y, iw, ih = border, border, w - 2 * border, h - border - bb
    c.save()
    c.clipRect(skia.Rect.MakeXYWH(x, y, iw, ih))
    c.translate(x, y)
    image(c, iw, ih)
    if gloss:
        c.drawPath(poly([(iw * 0.55, 0), (iw * 0.82, 0), (iw * 0.42, ih), (iw * 0.15, ih)]), fill("#FFFFFF", 0.07))
    c.restore()
    if caption:
        E.fit(caption[0], "ShipporiMincho-Medium", iw * 0.9, bb * 0.46, max_size=24).draw(c, w / 2, h - bb / 2, E.INK)
    outline(c, path, 2.0)


def make_chalk():
    img = E.load_image(RAW / "r12_chalk.png")
    w, h = 400, 430
    bar = B.Bar(600, 575, 560, 205, 0.0, 42)

    def f(c):
        def im(cc, iw, ih):
            s = max(iw / img.width(), ih / img.height())
            cc.translate(iw / 2, ih / 2)
            cc.scale(s, s)
            cc.translate(-img.width() / 2, -img.height() / 2)
            cc.drawImage(img, 0, 0, E.SAMPLING)
            bar.draw(cc)
        photo_print(c, w, h, 16, im, seed=8)
    return w, h, f, None


# A class of 41 in four rows. Everyone is small and plain; only one has yellow hair, and only she has no eyes to look at.
def make_group():
    """The class photo: an old black-and-white print, thirty-odd different children, drawn in the same hand as she is. It comes up close."""
    img = screen_print(RAW / "r23_class.png")
    w, h = 690, 500
    border, cap = 18, 64
    iw, ih = w - 2 * border, h - border - cap
    s_ = max(iw / img.width(), ih / img.height())
    # her head in the picture (second row from the top, a little right of centre) and the bar over her eyes
    hx, hy = 938.0, 338.0
    bar = B.Bar(hx, hy, 104, 40, 0.0, 45)

    def picture(c, cw, ch):
        c.translate(cw / 2, ch / 2)
        c.scale(s_, s_)
        c.translate(-img.width() / 2, -img.height() / 2)
        c.drawImage(img, 0, 0, E.SAMPLING_DOWN)
        bar.draw(c)

    def f(c):
        photo_print(c, w, h, border, picture, caption=("第四十二回 卒業記念", cap), seed=9)
    # the ring goes round her head and her bow together
    return w, h, f, None, (border + iw / 2 + (hx - img.width() / 2) * s_, border + ih / 2 + (hy - 34 - img.height() / 2) * s_)


def make_id():
    img = bgr_image(cv2.imread(str(RAW / "r21_id.png")))
    bar = B.Bar(540, 722, 480, 176, 0.0, 43)
    cw, ch = 176, 233
    g = 12
    w, h = 2 * cw + 3 * g, 2 * ch + 3 * g
    # an uncut sheet of four; one has been cut off and used
    pts = [(0, 0), (w, 0), (w, ch + 1.5 * g), (cw + 1.5 * g, ch + 1.5 * g), (cw + 1.5 * g, h), (0, h)]

    def f(c):
        path = poly(pts)
        c.drawPath(path, fill("#FBFBF8"))
        for (i, j) in ((0, 0), (1, 0), (0, 1)):
            x, y = g + i * (cw + g), g + j * (ch + g)
            c.save()
            c.clipRect(skia.Rect.MakeXYWH(x, y, cw, ch))
            c.translate(x, y)
            c.scale(cw / img.width(), ch / img.height())
            c.drawImage(img, 0, 0, E.SAMPLING_DOWN)
            bar.draw(c)
            c.restore()
        c.drawPath(poly([(w * 0.5, 0), (w * 0.72, 0), (w * 0.36, h * 0.5), (w * 0.14, h * 0.5)]), fill("#FFFFFF", 0.06))
        outline(c, path, 2.0)
    return w, h, f, pts


def make_shikishi():
    w, h = 460, 460
    msgs = [("元気でね", 96, 92, -30, "HachiMaruPop-Regular", 27), ("ずっと友だち", 330, 84, 22, "Yomogi-Regular", 34),
            ("また遊ぼう", 392, 232, 86, "KleeOne-SemiBold", 30), ("絵じょうず！", 340, 372, -36, "HachiMaruPop-Regular", 25),
            ("中学でもがんばれ", 150, 386, 22, "ZenKurenaido-Regular", 29), ("ありがとう", 64, 240, -86, "YuseiMagic-Regular", 28)]

    def f(c):
        # a square of card board with its gold edge
        E.rect(c, 0, 0, w, h, "#C2A24C", radius=3)
        E.rect(c, 7, 7, w - 14, h - 14, "#F9F7EF")
        c.drawRect(skia.Rect.MakeXYWH(0, 0, w, h), line_paint(E.INK, 2.4))
        blot(c, w / 2 - 34, h / 2, 150, 62, -2.0, 15)
        E.Type("へ", "HachiMaruPop-Regular", 56).draw(c, w / 2 + 84, h / 2 + 4, E.INK)
        for s, x, y, r, font, size in msgs:
            E.Type(s, font, size).draw(c, x, y, E.INK, rot=r)
    return w, h, f, None


def make_library():
    w, h = 320, 450
    rows = [("銀河鉄道の夜", "5/12"), ("銀河鉄道の夜", "5/26"), ("星の王子さま", "6/9"), ("銀河鉄道の夜", "6/23"), ("花の図鑑", "7/7"), ("花の図鑑", "9/1"), ("銀河鉄道の夜", "9/15")]

    def f(c):
        path, _, _ = draw_sheet(c, w, h, "#EAD9AE", seed=10)
        E.Type("図書カード", "ZenKakuGothicNew-Bold", 30).draw(c, w / 2, 40, E.INK)
        blot(c, w / 2, 86, 200, 34, -0.5, 16)
        x0, y0, rw, rh = 18, 116, w - 36, 44
        for i in range(7):
            c.drawRect(skia.Rect.MakeXYWH(x0, y0 + i * rh, rw, rh), line_paint(E.INK, 1.5))
            c.drawLine(x0 + rw * 0.72, y0 + i * rh, x0 + rw * 0.72, y0 + (i + 1) * rh, line_paint(E.INK, 1.5))
            s, d = rows[i]
            E.fit(s, HAND, rw * 0.66, 30, max_size=23).draw(c, x0 + 10, y0 + i * rh + rh / 2, E.INK, ax=0)
            E.Type(d, HAND, 21).draw(c, x0 + rw * 0.86, y0 + i * rh + rh / 2, E.INK)
        outline(c, path)
    return w, h, f, None


def make_candid():
    img = screen_print(RAW / "r22_candid.png")
    w, h = 600, 412
    bar = B.Bar(762, 318, 280, 104, -12.0, 44)

    def f(c):
        def im(cc, iw, ih):
            s = max(iw / img.width(), ih / img.height())
            cc.translate(iw / 2, ih / 2)
            cc.scale(s, s)
            cc.translate(-img.width() / 2, -img.height() / 2)
            cc.drawImage(img, 0, 0, E.SAMPLING_DOWN)
            bar.draw(cc)
        photo_print(c, w, h, 16, im, seed=11)
    return w, h, f, None


# ---- the red pen ----
def press(pts, width, seed):
    """Variable-width marker: lands fat, thins as it goes, with a little pressure wander."""
    rng = np.random.default_rng(seed)
    a = np.array(pts, float)
    s = B._polyline_lengths(a)
    n = len(a)
    w = width * (1.08 - 0.42 * (s / max(s[-1], 1)) + 0.10 * np.sin(s / max(width * 6, 1) + rng.random() * 6))
    w[:2] *= 0.8
    return a, s, w


def ribbon(a, w, n=None):
    """A filled outline around a polyline, with round ends."""
    n = len(a) if n is None else n
    if n < 2:
        return None
    d = np.gradient(a[:n], axis=0)
    d /= np.maximum(np.hypot(d[:, 0], d[:, 1])[:, None], 1e-3)
    nrm = np.stack([-d[:, 1], d[:, 0]], 1) * (w[:n, None] / 2)
    left = a[:n] + nrm
    right = (a[:n] - nrm)[::-1]
    p = skia.Path()
    p.moveTo(*left[0])
    for q in left[1:]:
        p.lineTo(*q)
    for q in right:
        p.lineTo(*q)
    p.close()
    return p


def draw_ribbon(c, p, a, w, paint):
    c.drawPath(p, paint)
    c.drawCircle(a[0][0], a[0][1], w[0] / 2, paint)
    c.drawCircle(a[-1][0], a[-1][1], w[-1] / 2, paint)


class Stroke:
    def __init__(self, pts, t0, t1, width, seed, pen=0):
        self.a, self.s, self.w = press(pts, width, seed)
        self.t0, self.t1 = t0, t1
        self.pen = pen
        self.full = ribbon(self.a, self.w)

    def at(self, t):
        """Number of points drawn and the position of the pen tip."""
        u = E.seg(t, self.t0, self.t1)
        # a hand slows in the turns a little: slight ease at both ends
        u = 0.7 * u + 0.3 * E.ease_io(u, 2)
        target = self.s[-1] * u
        i = int(np.searchsorted(self.s, target))
        i = min(max(i, 1), len(self.a) - 1)
        s0, s1 = self.s[i - 1], self.s[i]
        v = (target - s0) / max(s1 - s0, 1e-6)
        tip = self.a[i - 1] * (1 - v) + self.a[i] * v
        return i, tip


def circle_pts(cx, cy, rx, ry, seed, turns=1.55, start=None, rot=0.0):
    rng = np.random.default_rng(seed)
    a0 = rng.uniform(0, math.tau) if start is None else start
    n = int(46 * turns)
    pts = []
    drift = rng.normal(0, 0.05, 2)
    wob = rng.uniform(0, 6.28, 3)
    cr, sr = math.cos(rot), math.sin(rot)
    for i in range(n + 1):
        u = i / n
        a = a0 + u * turns * math.tau
        # a hand-drawn loop never meets itself: it spirals, and bulges
        k = 1 + (u - 0.5) * 0.12 + 0.035 * math.sin(a * 2 + wob[0]) + 0.02 * math.sin(a * 3 + wob[1])
        x, y = rx * k * math.cos(a) + drift[0] * rx * u, ry * k * math.sin(a) + drift[1] * ry * u
        pts.append((cx + x * cr - y * sr, cy + x * sr + y * cr))
    return pts


def curve_pts(p0, p1, bow, seed, n=26):
    rng = np.random.default_rng(seed)
    p0, p1 = np.array(p0, float), np.array(p1, float)
    d = p1 - p0
    nrm = np.array([-d[1], d[0]])
    wob = rng.uniform(0, 6.28)
    pts = []
    for i in range(n + 1):
        u = i / n
        q = p0 + d * u + nrm * (bow * math.sin(u * math.pi) + 0.012 * math.sin(u * 9 + wob))
        pts.append(tuple(q))
    return pts


def arrow_head(tip, frm, size, seed):
    rng = np.random.default_rng(seed)
    tip, frm = np.array(tip, float), np.array(frm, float)
    d = frm - tip
    d = d / max(np.hypot(*d), 1e-3)
    out = []
    for sgn in (1, -1):
        a = sgn * (0.5 + rng.normal(0, 0.05))
        r = np.array([d[0] * math.cos(a) - d[1] * math.sin(a), d[0] * math.sin(a) + d[1] * math.cos(a)])
        out.append([tuple(tip + r * size), tuple(tip + r * size * 0.5), tuple(tip)])
    return out


def glyph_strokes(kind, cx, cy, size, seed):
    """!? and ? and x, as strokes."""
    rng = np.random.default_rng(seed)

    def j(u, v):
        return (cx + (u + rng.normal(0, 0.012)) * size, cy + (v + rng.normal(0, 0.012)) * size)
    if kind == "x":
        return [[j(-0.5, -0.5), j(-0.1, -0.08), j(0.5, 0.52)], [j(0.5, -0.5), j(0.08, -0.05), j(-0.5, 0.5)]]
    q = [[j(-0.32, -0.32), j(-0.22, -0.52), j(0.05, -0.6), j(0.3, -0.42), j(0.22, -0.16), j(0.0, 0.0), j(0.0, 0.2)], [j(-0.02, 0.5), j(0.02, 0.56), j(-0.02, 0.6)]]
    if kind == "?":
        return q
    # !?
    bang = [[j(-0.62, -0.58), j(-0.6, -0.2), j(-0.58, 0.22)], [j(-0.6, 0.5), j(-0.56, 0.56), j(-0.6, 0.6)]]
    return bang + q


def smooth(pts, n=7):
    return B._catmull(pts, n).tolist() if len(pts) > 2 else curve_pts(pts[0], pts[1], 0.01, 1, 10)


PEN_L = 400.0
PEN_R = 21.0


def draw_pen(c, tip, ang, lift=0.0):
    """A red marker seen from above, tip at `tip`, its body rising towards the viewer away from the tip. Its shadow meets it at the tip."""
    x, y = tip
    ca, sa = math.cos(ang), math.sin(ang)
    ex, ey = x + ca * PEN_L, y + sa * PEN_L
    nx, ny = -sa, ca
    sx0, sy0 = LIGHT * (lift * 40 + 1)
    sx1, sy1 = LIGHT * (lift * 40 + 62)
    sh = [(x + sx0 - nx * 5, y + sy0 - ny * 5), (ex + sx1 - nx * PEN_R, ey + sy1 - ny * PEN_R),
          (ex + sx1 + nx * PEN_R, ey + sy1 + ny * PEN_R), (x + sx0 + nx * 5, y + sy0 + ny * 5)]
    c.drawPath(poly(sh), fill(E.INK, SHADOW))
    c.save()
    c.translate(x, y)
    c.rotate(math.degrees(ang))
    R = PEN_R
    # felt tip, nose, barrel, label, cap end; lines all round
    c.drawPath(poly([(0, -3.5), (24, -7), (24, 7), (0, 3.5)]), fill(E.RED))
    nose = skia.Path()
    nose.moveTo(24, -7)
    nose.lineTo(74, -R * 0.82)
    nose.lineTo(74, R * 0.82)
    nose.lineTo(24, 7)
    nose.close()
    c.drawPath(nose, fill("#E8E6DF"))
    c.drawPath(nose, line_paint(E.INK, 2.6))
    body = skia.Path()
    body.addRRect(skia.RRect.MakeRectXY(skia.Rect.MakeLTRB(74, -R, PEN_L, R), 6, 6))
    c.drawPath(body, fill(E.RED))
    E.rect(c, 74, R * 0.32, PEN_L - 74, R * 0.68, "#B20E22")
    E.rect(c, 150, -R + 2, 150, 2 * R - 4, E.PAPER)
    E.rect(c, 150, R * 0.32, 150, R * 0.68 - 2, "#D8D5CA")
    E.rect(c, 150, -R + 2, 150, 8, E.RED)
    c.drawPath(body, line_paint(E.INK, 3.0))
    c.drawLine(PEN_L - 34, -R, PEN_L - 34, R, line_paint(E.INK, 2.6))
    c.restore()


# The chat before this has pushed into the drawing until its paper fills the frame (s02d). The camera comes back off it on the first sung note, and
# what is round the paper is the table. So the first item does not slide in: it is here already.
FILL_S = 3.45
FILL_OUT = NOTES[0] - 0.05 + 0.62      # the camera comes to rest on the table; the second note's crayon is already arriving
FLOWERS_AT = (-40.0, -40.0, -3.0)


def table_view(t):
    """The table's camera while things are arriving."""
    u = E.seg(t, NOTES[0] - 0.05, NOTES[-1] + 0.6)
    s = math.exp(E.lerp(math.log(1.28), math.log(0.60), u ** 0.92))
    return -40 * (1 - u), E.lerp(-30, 40, u), s


def fill_pose(t0):
    """Where the drawing is, on the screen, on this section's first frame: centre, rotation, and how big one unit of the sheet is."""
    cx, cy, s = table_view(t0)
    return 960 + (FLOWERS_AT[0] - cx) * FILL_S, 540 + (FLOWERS_AT[1] - cy) * FILL_S, FLOWERS_AT[2], FILL_S


class Digging(E.Clip):
    name = "s03"
    t0, t1 = F0 / 30, F1 / 30
    grain = 0.010
    shutter = 0.18

    def setup(self):
        # the close-ups of the first pen cut on the long notes
        self.cuts = tuple(RED_NOTES[:5]) + (SHOT1 + CLOSE, SHOT2 + CLOSE, LAST_HIT)
        self.build_items()
        self.build_pens()
        self.lyr16 = K.Strip("捨ててきた夢をあつめて", K.chars_of(16, "捨ててきた夢をあつめて"), size=46)
        self.lyr17 = K.Strip("ちょっとちょっと間違えたからパッパ", K.chars_of(17, "ちょっとちょっと間違えたからパッパ"), size=46)
        self._photo1 = None
        self._photo2 = None
        self._print2 = None

    # ---- the table ----
    def build_items(self):
        spec = [
            # maker, x, y, rot, from (unit vector, away from the table's centre), corner lift
            ("flowers", make_flowers, -40, -40, -3.0, (-0.2, -1.0), (5, 16, 6, 5)),
            ("crayon", make_crayon, 520, -250, 7.0, (1.0, -0.2), (5, 6, 18, 5)),
            ("badge", make_badge, -500, -300, -11.0, (-1.0, -0.3), (9, 9, 9, 9)),
            ("cert", make_cert, -640, 200, 3.5, (-1.0, 0.25), (5, 6, 7, 5)),
            ("report", make_report, 660, 250, -5.0, (1.0, 0.35), (5, 6, 10, 6)),
            ("comp", make_composition, 60, 548, 2.0, (0.1, 1.0), (6, 6, 8, 18)),
            ("chalk", make_chalk, -1150, -340, -6.0, (-1.0, -0.2), (4, 4, 6, 4)),
            ("group", make_group, 1120, -440, 4.0, (1.0, -0.4), (5, 12, 5, 4)),
            ("id", make_id, 1190, 330, -6.0, (1.0, 0.3), (4, 4, 4, 4)),
            ("shikishi", make_shikishi, -430, -630, 8.0, (-0.3, -1.0), (12, 12, 12, 12)),
            ("library", make_library, -1240, 420, 6.0, (-1.0, 0.5), (4, 5, 6, 4)),
            ("candid", make_candid, -640, 672, -4.5, (-0.4, 1.0), (4, 4, 7, 12)),
        ]
        self.items = []
        self.by = {}
        for i, (name, mk, x, y, rot, frm, lift) in enumerate(spec):
            res = mk()
            w, h, fn, shape = res[:4]
            it = Item(name, x, y, w, h, rot, np.array(frm) / np.hypot(*frm), record(w, h, fn), lift, shape)
            it.t_in = NOTES[i] - 0.05
            if name == "flowers":
                it.t_in = self.t0 - 1.0
            if name == "group":
                it.her = res[4]
            self.items.append(it)
            self.by[name] = it
        # what a sliding thing touches gets knocked a little, away from where it came
        for i, a in enumerate(self.items):
            for b in self.items[:i]:
                reach = (math.hypot(a.w, a.h) + math.hypot(b.w, b.h)) / 2 * 0.72
                if math.hypot(a.x - b.x, a.y - b.y) < reach:
                    k = -a.frm * 13
                    b.push.append((a.t_in + 0.13, k[0], k[1], -a.frm[0] * 0.7))

    def draw_item(self, c, it, t):
        x, y, r = it.pose(t)
        c.save()
        c.translate(x, y)
        c.rotate(r)
        c.translate(-it.w / 2, -it.h / 2)
        # the hard shadow: each corner is its own height off the table, in the frame of the table, not of the sheet
        a = math.radians(-r)
        lx = LIGHT[0] * math.cos(a) - LIGHT[1] * math.sin(a)
        ly = LIGHT[0] * math.sin(a) + LIGHT[1] * math.cos(a)
        n = len(it.shape)
        sh = []
        for i, q in enumerate(it.shape):
            ql = it.lift[min(int(i * 4 / n), 3)]
            sh.append((q[0] + lx * ql, q[1] + ly * ql))
        c.drawPath(poly(sh), fill(E.INK, SHADOW))
        c.drawPicture(it.pic)
        c.restore()

    # ---- the pens ----
    def add(self, pts, t0, t1, pen, width=11.0, seed=None):
        self._seed += 1
        self.strokes.append(Stroke(pts, t0, t1, width, self._seed if seed is None else seed, pen))

    def mark(self, kind, pen, t0, t1, *args, width=11.0):
        """Lays a mark's strokes one after another in [t0, t1]."""
        self._seed += 1
        sd = self._seed * 7
        if kind == "circle":
            cx, cy, rx, ry = args
            self.add(circle_pts(cx, cy, rx, ry, sd), t0, t1, pen, width)
        elif kind == "arrow":
            p0, p1, bow = args
            body = curve_pts(p0, p1, bow, sd)
            heads = arrow_head(body[-1], body[-4], 46 * width / 11, sd)
            tb = t0 + (t1 - t0) * 0.66
            self.add(body, t0, tb, pen, width)
            tm = (tb + t1) / 2
            self.add(smooth(heads[0]), tb + 0.005, tm, pen, width)
            self.add(smooth(heads[1]), tm + 0.005, t1, pen, width)
        elif kind == "line":
            p0, p1, bow = args
            self.add(curve_pts(p0, p1, bow, sd), t0, t1, pen, width)
        elif kind in ("x", "?", "!?"):
            cx, cy, size = args
            sts = glyph_strokes(kind, cx, cy, size, sd)
            n = len(sts)
            for i, s in enumerate(sts):
                self.add(smooth(s), t0 + (t1 - t0) * i / n, t0 + (t1 - t0) * (i + 0.85) / n, pen, width)
        elif kind == "zig":
            p0, p1, amp, k = args
            p0, p1 = np.array(p0, float), np.array(p1, float)
            d = p1 - p0
            nrm = np.array([-d[1], d[0]]) / max(np.hypot(*d), 1) * amp
            pts = [tuple(p0 + d * (i / k) + nrm * (1 if i % 2 else -1)) for i in range(k + 1)]
            self.add(smooth(pts, 5), t0, t1, pen, width)

    def build_pens(self):
        self.strokes = []
        self._seed = 100
        I = self.by
        n = RED_NOTES
        fx, fy = I["flowers"].x, I["flowers"].y
        # 1. chot: both flowers, ringed
        c0 = I["flowers"].loc(330, 215)
        self.targets = [(n[0], n[1], c0, 1.34)]
        self.mark("circle", 0, n[0] + 0.14, n[0] + 0.80, c0[0], c0[1], 372, 248, width=15)
        # 2. to: the class photo, one face
        g = I["group"]
        her = g.loc(*g.her)
        self.targets.append((n[1], n[2], (her[0] - 90, her[1] + 70), 1.42))
        self.mark("circle", 0, n[1] + 0.10, n[1] + 0.50, her[0], her[1] + 2, 62, 70, width=9)
        self.mark("arrow", 0, n[1] + 0.52, n[1] + 0.88, (her[0] - 290, her[1] + 180), (her[0] - 62, her[1] + 44), 0.10, width=9)
        # 3. chot: the answer in the composition
        cp = I["comp"]
        ans = cp.loc(cp.w - 26 - 3 * 32 + 12, 26 + 15.5 * 32)
        self.targets.append((n[2], n[3], (cp.loc(cp.w * 0.66, cp.h * 0.56)), 1.24))
        self.mark("circle", 0, n[2] + 0.08, n[2] + 0.46, ans[0], ans[1], 86, 170, width=12)
        self.mark("!?", 0, n[2] + 0.50, n[2] + 0.88, ans[0] - 200, ans[1] - 70, 118, width=12)
        # 4. to: what a friend wrote on the card
        sk = I["shikishi"]
        fr = sk.loc(330, 84)
        self.targets.append((n[3], n[4], sk.loc(190, 215), 1.55))
        # the ring lies along the words, which run at an angle
        self.add(circle_pts(fr[0], fr[1], 158, 58, 7, rot=math.radians(sk.rot + 22)), n[3] + 0.08, n[3] + 0.50, 0, 10)
        q = sk.loc(-92, 190)
        self.mark("?", 0, n[3] + 0.54, n[3] + 0.88, q[0], q[1], 150, width=12)

        # 5. the whole table: lines start joining things. More pens every couple of notes: this is everybody.
        idp = I["id"].loc(100, 120)
        cert = I["cert"].loc(I["cert"].w - 174, 170)
        badge = I["badge"].loc(125, 96)
        rep = I["report"].loc(405, 200)
        lib = I["library"].loc(160, 200)
        chk = I["chalk"].loc(200, 200)
        cry = I["crayon"].loc(172, 150)
        cnd = I["candid"].loc(310, 150)
        c0r = (c0[0] + 372, c0[1])
        d = 0.46
        # ma
        self.mark("line", 0, n[4] + 0.02, n[4] + 0.42, (c0[0] + 250, c0[1] - 170), (her[0] - 60, her[1] + 60), -0.10)
        # chi
        self.mark("circle", 0, n[5] + 0.02, n[5] + 0.22, idp[0], idp[1], 118, 138)
        self.mark("line", 1, n[5] + 0.06, n[5] + 0.40, (her[0] + 40, her[1] + 66), (idp[0] + 20, idp[1] - 136), 0.10)
        self.mark("x", 0, n[5] + 0.26, n[5] + 0.44, rep[0], rep[1], 120)
        # ga
        self.mark("circle", 1, n[6] + 0.02, n[6] + 0.20, cert[0], cert[1], 70, 150, width=10)
        self.mark("arrow", 0, n[6] + 0.02, n[6] + 0.34, (idp[0] - 120, idp[1] + 40), (ans[0] + 90, ans[1] - 60), 0.08)
        self.mark("!?", 2, n[6] + 0.10, n[6] + 0.44, cert[0] + 120, cert[1] - 200, 110)
        self.mark("line", 1, n[6] + 0.24, n[6] + 0.44, (cert[0] + 60, cert[1] + 40), (c0[0] - 372, c0[1] + 20), 0.08)
        # e
        self.mark("circle", 0, n[7] + 0.02, n[7] + 0.18, chk[0], chk[1], 150, 150)
        self.mark("arrow", 1, n[7] + 0.02, n[7] + 0.26, (chk[0] + 150, chk[1] + 40), (cert[0] - 60, cert[1] - 150), -0.12)
        self.mark("circle", 2, n[7] + 0.02, n[7] + 0.20, badge[0], badge[1], 130, 66)
        self.mark("line", 0, n[7] + 0.22, n[7] + 0.44, (chk[0] + 110, chk[1] - 110), (badge[0] - 120, badge[1] + 10), -0.08)
        self.mark("line", 2, n[7] + 0.24, n[7] + 0.44, (badge[0] + 120, badge[1] - 20), (fr[0] - 120, fr[1] + 40), 0.12)
        self.mark("?", 3, n[7] + 0.08, n[7] + 0.42, cry[0] + 10, cry[1] + 280, 120)
        # ta
        self.mark("circle", 3, n[8] + 0.02, n[8] + 0.20, cry[0], cry[1], 150, 112)
        self.mark("arrow", 0, n[8] + 0.02, n[8] + 0.22, (c0r[0] - 80, c0r[1] - 130), (cry[0] - 130, cry[1] + 70), 0.10)
        self.mark("circle", 1, n[8] + 0.03, n[8] + 0.20, lib[0], lib[1], 150, 230, width=10)
        self.mark("arrow", 2, n[8] + 0.03, n[8] + 0.26, (fr[0] + 60, fr[1] + 80), (cry[0] - 60, cry[1] - 120), -0.14)
        self.mark("x", 3, n[8] + 0.24, n[8] + 0.44, I["crayon"].loc(70, 410)[0], I["crayon"].loc(70, 410)[1], 90)
        self.mark("line", 1, n[8] + 0.24, n[8] + 0.44, (lib[0] + 120, lib[1] - 150), (chk[0] - 60, chk[1] + 150), 0.08)
        self.mark("!?", 0, n[8] + 0.24, n[8] + 0.44, her[0] - 190, her[1] - 150, 96)
        # ka
        self.mark("circle", 4, n[9] + 0.02, n[9] + 0.20, cnd[0], cnd[1], 196, 120)
        self.mark("arrow", 1, n[9] + 0.02, n[9] + 0.20, (lib[0] + 130, lib[1] + 140), (cnd[0] - 170, cnd[1] - 20), -0.10)
        self.mark("line", 3, n[9] + 0.02, n[9] + 0.20, (cry[0] + 60, cry[1] + 100), (rep[0] - 30, rep[1] - 170), 0.10)
        self.mark("zig", 2, n[9] + 0.02, n[9] + 0.18, (fr[0] - 280, fr[1] + 130), (fr[0] + 40, fr[1] + 260), 16, 7)
        self.mark("arrow", 0, n[9] + 0.03, n[9] + 0.24, (ans[0] - 90, ans[1] - 120), (c0[0] + 120, c0[1] + 215), 0.14)
        self.mark("x", 4, n[9] + 0.24, n[9] + 0.44, cnd[0] + 200, cnd[1] + 170, 96)
        self.mark("?", 1, n[9] + 0.24, n[9] + 0.44, cert[0] - 240, cert[1] + 180, 110)
        self.mark("line", 3, n[9] + 0.24, n[9] + 0.44, (rep[0] + 60, rep[1] - 140), (idp[0] - 90, idp[1] + 110), -0.12)
        self.mark("!?", 2, n[9] + 0.22, n[9] + 0.44, c0[0] + 10, c0[1] - 300, 96)
        self.mark("zig", 0, n[9] + 0.26, n[9] + 0.44, (idp[0] - 110, idp[1] + 190), (idp[0] + 150, idp[1] + 210), 18, 7)
        # ra: nobody is checking anything now. Long lines across the whole table.
        rng = np.random.default_rng(77)
        hubs = [her, idp, ans, c0, cert, fr, cry, cnd, lib, chk, rep, badge]
        t = n[10]
        for k in range(11):
            a, b = rng.choice(len(hubs), 2, replace=False)
            pen = k % 5
            t0 = t + (k % 5) * 0.012 + (k // 5) * 0.150
            self.mark("arrow" if k % 3 == 0 else "line", pen, t0, t0 + 0.145, hubs[a], hubs[b], float(rng.uniform(-0.16, 0.16)), width=10)
        # the sung パッ cuts them off where they are
        for k in range(5):
            a, b = rng.choice(len(hubs), 2, replace=False)
            self.mark("line", k, n[11] - 0.015 + k * 0.01, n[11] + 0.16, hubs[a], hubs[b], float(rng.uniform(-0.14, 0.14)), width=10)
        self.strokes.sort(key=lambda s: s.t0)
        self.pens = {}
        for s in self.strokes:
            self.pens.setdefault(s.pen, []).append(s)
        # each pen is someone on a different side of the table
        self.pen_ang = [math.radians(a) for a in (38, 148, -38, -142, 76)]
        self.pen_from = [(1500, 1400), (-1900, 800), (1900, -1100), (-1500, -1300), (300, 1700)]

    def pen_tip(self, k, t):
        ss = self.pens[k]
        first = ss[0]
        if t < first.t0:
            u = E.ease_out(E.seg(t, first.t0 - 0.16, first.t0), 3)
            start = np.array(self.pen_from[k], float)
            return start + (first.a[0] - start) * u, 1.0 - u
        prev = None
        for s in ss:
            if s.t0 <= t <= s.t1:
                return s.at(t)[1], 0.0
            if t < s.t0:
                # in the air between strokes
                u = E.ease_io(E.seg(t, prev.t1, s.t0), 2)
                h = math.sin(u * math.pi)
                return prev.a[-1] + (s.a[0] - prev.a[-1]) * u, 0.7 * h
            prev = s
        return prev.a[-1], 0.0

    def draw_ink(self, c, t):
        paint = fill(E.RED)
        for s in self.strokes:
            if t < s.t0:
                break
            if t >= s.t1:
                draw_ribbon(c, s.full, s.a, s.w, paint)
            else:
                i, tip = s.at(t)
                a = np.vstack([s.a[:i], tip])
                w = np.append(s.w[:i], s.w[min(i, len(s.w) - 1)])
                p = ribbon(a, w)
                if p is not None:
                    draw_ribbon(c, p, a, w, paint)

    def draw_pens(self, c, t):
        for k in sorted(self.pens):
            if t < self.pens[k][0].t0 - 0.16:
                continue
            tip, lift = self.pen_tip(k, t)
            # the wrist moves as it writes: the angle is never quite still
            ang = self.pen_ang[k] + 0.09 * math.sin(t * 7.1 + k * 2.0) + 0.05 * math.sin(t * 13 + k)
            draw_pen(c, tip, ang, lift)

    # ---- the camera ----
    def camera(self, t):
        if t < PEN_IN:
            # a steady log pull so the table keeps making room for what arrives
            cx, cy, s = table_view(t)
            if t < FILL_OUT:
                # back off the drawing: the paper's own edges come in from outside the frame. The drawing's centre goes straight home.
                # The push before this slowed to a stop on this very frame, so the pull starts from rest as well, gathers, and settles
                x_ = E.seg(t, self.t0, FILL_OUT) ** 0.72
                w = 1 - x_ * x_ * x_ * (x_ * (6 * x_ - 15) + 10)
                k = math.exp(math.log(FILL_S / s) * w)
                ox, oy = FLOWERS_AT[0], FLOWERS_AT[1]
                full = 960 + (ox - cx) * FILL_S, 540 + (oy - cy) * FILL_S
                rest = 960 + (ox - cx) * s, 540 + (oy - cy) * s
                a = (k - 1) / (FILL_S / s - 1)
                sx, sy = rest[0] + (full[0] - rest[0]) * a, rest[1] + (full[1] - rest[1]) * a
                return ox - (sx - 960) / (s * k), oy - (sy - 540) / (s * k), s * k
            return cx, cy, s
        for t0, t1, q, s in self.targets:
            if t0 <= t < t1:
                # a push, slow, the whole time the pen is working
                return q[0], q[1], s * (1 + 0.035 * E.seg(t, t0, t1))
        u = E.seg(t, WIDE, SHOT1)
        return 0.0, 40.0, 0.60 * (1 + 0.04 * E.ease_in(u, 1.6))

    def world(self, c, t):
        c.clear(E.col(E.CYAN))
        cx, cy, s = self.camera(t)
        c.save()
        c.translate(960, 540)
        c.scale(s, s)
        c.translate(-cx, -cy)
        for it in self.items:
            if t >= it.t_in:
                self.draw_item(c, it, t)
        if t >= PEN_IN:
            self.draw_ink(c, t)
            self.draw_pens(c, t)
        c.restore()

    def blur(self, t):
        for it in self.items:
            if it.t_in - 0.02 <= t <= it.t_in + 0.26:
                return 16
        if PEN_IN - 0.01 <= t < SHOT1 + CLOSE:
            return 28
        return 1

    def frame_rgb(self, t):
        return K.soft_frame(self, t)

    # ---- the shutter ----
    def iris(self, c, u, spin):
        """u = 0 wide open .. 1 shut. Seven blades, pinwheeled, their edges catching a little light."""
        r = 1250 * (1 - u) ** 1.4
        n = 7
        a0 = spin + u * 0.95
        vs = [np.array([960 + r * math.cos(a0 + i * math.tau / n), 540 + r * math.sin(a0 + i * math.tau / n)]) for i in range(n)]
        L = 4200.0
        dirs = []
        for i in range(n):
            d = vs[i] - vs[i - 1]
            ln = max(np.hypot(*d), 1e-6)
            dirs.append(d / ln if r > 1 else np.array([math.cos(a0 + i * math.tau / n + 1.2), math.sin(a0 + i * math.tau / n + 1.2)]))
        for i in range(n):
            j = (i + 1) % n
            q = [tuple(vs[i]), tuple(vs[i] + dirs[i] * L), tuple(vs[j] + dirs[j] * L), tuple(vs[j])]
            c.drawPath(poly(q), fill("#14161E" if i % 2 else "#1B1E28"))
        for i in range(n):
            c.drawLine(vs[i][0], vs[i][1], *(vs[i] + dirs[i] * L), line_paint("#3A3F4E", 3.0))

    def snapshot(self, fn):
        surf = skia.Surface(E.W, E.H)
        fn(surf.getCanvas())
        return surf.makeImageSnapshot()

    def photo1(self):
        if self._photo1 is None:
            self._photo1 = self.snapshot(lambda cc: self.world(cc, SHOT1 + CLOSE))
        return self._photo1

    def photo2(self):
        """The first photograph, photographed: what the news will print."""
        if self._photo2 is None:
            self._photo2 = self.snapshot(lambda cc: self.print_on_table(cc, self.photo1(), -2.4, (952, 508), seed=4))
        return self._photo2

    def print2(self):
        """At the last hit it goes to newsprint: coarse dots of ink."""
        if self._print2 is None:
            a = self.photo2().toarray(colorType=skia.ColorType.kRGBA_8888_ColorType, alphaType=skia.AlphaType.kOpaque_AlphaType)[..., :3]
            g = (a.astype(np.float32) / 255 * np.array([0.30, 0.59, 0.11], np.float32)).sum(-1)
            g = np.clip((g - 0.04) / 0.92, 0, 1) ** 0.85
            yy, xx = np.mgrid[0:E.H, 0:E.W].astype(np.float32)
            cell = 9.0
            ang = math.radians(45)
            u = (xx * math.cos(ang) + yy * math.sin(ang)) / cell * math.tau
            v = (-xx * math.sin(ang) + yy * math.cos(ang)) / cell * math.tau
            screen = (np.cos(u) * np.cos(v) + 1) / 2
            m = np.clip((g * 1.04 - screen * 0.96) * 5 + 0.5, 0, 1)
            ink_c = np.array([20, 20, 28], np.float32) / 255
            paper_c = np.array([233, 229, 214], np.float32) / 255
            rgb = ink_c + (paper_c - ink_c) * m[..., None]
            rgb = (rgb * 255 + 0.5).astype(np.uint8)
            self._print2 = E.np_to_image(np.dstack([rgb, np.full(rgb.shape[:2], 255, np.uint8)]))
        return self._print2

    def print_on_table(self, c, img, rot, center, seed=4):
        """A whole frame as a print lying on the table, with the word in its wide bottom margin."""
        c.clear(E.col(E.CYAN))
        s = 0.755
        iw, ih = E.W * s, E.H * s
        m, mb = 24, 82
        w, h = iw + 2 * m, ih + m + mb
        lift = (8, 16, 24, 10)
        c.save()
        c.translate(*center)
        c.rotate(rot)
        c.translate(-w / 2, -h / 2)
        a = math.radians(-rot)
        lx = LIGHT[0] * math.cos(a) - LIGHT[1] * math.sin(a)
        ly = LIGHT[0] * math.sin(a) + LIGHT[1] * math.cos(a)
        cs = [(0, 0), (w, 0), (w, h), (0, h)]
        c.drawPath(poly([(q[0] + lx * l_, q[1] + ly * l_) for q, l_ in zip(cs, lift)]), fill(E.INK, SHADOW))
        c.drawPath(poly(cs), fill("#FBFBF8"))
        c.save()
        c.translate(m, m)
        c.scale(s, s)
        c.drawImage(img, 0, 0, E.SAMPLING_DOWN)
        c.restore()
        c.drawPath(poly([(iw * 0.60, m), (iw * 0.78, m), (iw * 0.47, m + ih), (iw * 0.29, m + ih)]), fill("#FFFFFF", 0.05))
        c.drawPath(poly(cs), line_paint(E.INK, 2.2))
        draw_pappa(c, w - 196, h - mb + 13, 56, E.INK, seed)
        c.restore()

    def draw_stage(self, c, t):
        """Whatever the shutter is in front of at time t."""
        if t < SHOT1 + BLACK_TO:
            self.world(c, min(t, SHOT1 + CLOSE))
        elif t < SHOT2 + BLACK_TO:
            self.print_on_table(c, self.photo1(), -2.4, (952, 508), seed=4)
        elif t < LAST_HIT:
            self.print_on_table(c, self.photo2(), 1.8, (968, 502), seed=9)
        else:
            self.print_on_table(c, self.print2(), 1.8, (968, 502), seed=9)
            self.falling_shadow(c, t)

    def falling_shadow(self, c, t):
        """Something large is coming down from above: its shadow is on the table before it is in the shot."""
        u = E.seg(t, 66.20, self.t1 + 0.033)
        if u <= 0:
            return
        k = E.ease_in(u, 2.0)
        cx = E.lerp(1500, 1040, k)
        cy = E.lerp(-420, 430, k)
        hw, hh = E.lerp(330, 860, k), E.lerp(240, 600, k)
        a = math.radians(E.lerp(-24, -7, k))
        ca, sa = math.cos(a), math.sin(a)
        pts = [(cx + x * ca - y * sa, cy + x * sa + y * ca) for x, y in ((-hw, -hh), (hw, -hh * 0.94), (hw * 0.98, hh), (-hw, hh * 0.96))]
        c.drawPath(poly(pts), fill(E.INK, SHADOW + 0.06))

    def draw(self, c, t):
        self.draw_stage(c, t)
        for shot, spin in ((SHOT1, 0.2), (SHOT2, 1.1)):
            dt = t - shot
            if 0 <= dt < CLOSE:
                self.iris(c, dt / CLOSE, spin)
            elif CLOSE <= dt < BLACK_TO:
                c.clear(E.col("#101219"))
            elif BLACK_TO <= dt < WHITE_TO:
                c.clear(E.col("#FFFFFF"))
            elif WHITE_TO <= dt < OPEN_TO:
                self.iris(c, 1 - (dt - WHITE_TO) / (OPEN_TO - WHITE_TO), spin + 0.95)
        # the sung words, on their tape
        if t < RED_NOTES[0] - 0.02:
            self.lyr16.draw(c, 960, 1034, t, ax=0.5)
        elif t < LAST_HIT:
            self.lyr17.draw(c, 960, 1034, t, ax=0.5)
