"""The drawings of the last shot, redrawn for every picture of the wind: her back hair, the scarf's tail, the bow. Plus the things that do
not move: the sky, which is her iris enlarged, and her scarf and collar. All in close-up picture pixels. Hard-edged flat tones, brush lines.

`wind` goes from 1 (the gust) down to about 0.2 (a breath); `phase` is how far the wave has travelled along the hair. A picture is a
function of those two only, so the wind can only die if `wind` only falls."""
import math
import sys
from pathlib import Path

import numpy as np
import skia

sys.path.insert(0, str(Path(__file__).parents[1] / "art"))
import finale_shapes as FS  # noqa: E402

INK = "#030304"
HAIR, HAIR_S, HAIR_D = "#FEE25E", "#F7BD3E", "#DE9628"
WHITE, WHITE_S = "#FBF8F1", "#C6D2E4"
SCARF, SCARF_S, SCARF_B = "#50525E", "#33353F", "#3D3F4A"
NAVY, NAVY_S = "#1B2547", "#111832"
SKIN_S = "#F5CDB9"
# the iris, from the top down: its deep shapes, then its bright ones
SKY = ["#035F75", "#0B7C93", "#218EA3", "#35A7BC", "#5BB8CA", "#8CD7DF", "#B0E8EA", "#D4F4F2"]


def _rgb(h):
    return [int(h[i:i + 2], 16) / 255 for i in (1, 3, 5)]


def tone(hexc, band=None):
    """Colour in one of the steps of the light arriving. band None: her own colour. Otherwise a ramp of the iris, by how light the colour is."""
    r, g, b = _rgb(hexc)
    if band is None:
        return skia.Color4f(r, g, b, 1)
    dk, lt = band
    y = (r + g + b) / 3
    dk, lt = _rgb(dk), _rgb(lt)
    v = min(y / 0.15, 1.0)   # ink stays ink
    return skia.Color4f(*[(dk[i] + (lt[i] - dk[i]) * y) * v for i in range(3)], 1)


def path_of(pts):
    p = skia.Path()
    p.addPoly([skia.Point(float(x), float(y)) for x, y in pts], True)
    return p


def fill(c, pts, col, band=None):
    c.drawPath(path_of(pts), skia.Paint(AntiAlias=True, Color4f=tone(col, band)))


def ink(c, curve, w, band=None):
    fill(c, FS.brush(curve, w), INK, band)


# ---- a long ribbon of hair or cloth: a spine integrated from an angle along its length
def spine(root, length, angle, curl, wave, freq, phase, n=70):
    """angle at the root in degrees (0 = to the right, positive = downward). curl: how much it turns by its end. wave: the swing of a travelling wave"""
    u = np.linspace(0, 1, n)
    a = np.radians(angle + curl * u ** 2 + wave * (0.25 + u) * np.sin(2 * np.pi * (freq * u - phase)))
    step = length / (n - 1)
    x = root[0] + np.r_[0, np.cumsum(np.cos(a[:-1]) * step)]
    y = root[1] + np.r_[0, np.cumsum(np.sin(a[:-1]) * step)]
    return np.c_[x, y], u


class Lock:
    """One lock of her back hair: a big simple shape that swells from the root, sweeps in one or two curves and ends in one sharp point, like the
    hair tips on her character sheet."""

    def __init__(self, root, length, gust, breath, curl, width, wave=14.0, freq=0.9, off=0.0, top_line=13, low_line=15):
        self.__dict__.update(root=root, length=length, gust=gust, breath=breath, curl=curl, width=width, wave=wave, freq=freq, off=off, top_line=top_line, low_line=low_line)

    def draw(self, c, wind, phase, band=None):
        L = self.length * (0.74 + 0.26 * wind)
        ang = self.breath + (self.gust - self.breath) * wind ** 0.8
        curl = self.curl * (0.7 + 0.3 * wind)
        s, u = spine(self.root, L, ang, curl, self.wave * (0.3 + 0.7 * wind), self.freq, phase + self.off)
        # width: stays full for its first third, then a long taper; the last part comes in hollow to a sharp point
        w = self.width * np.clip(1.0 - np.maximum(u - 0.30, 0) / 0.70, 0, 1) ** 1.25
        n = FS.normals(s)
        up, dn = s - n * w[:, None] * 0.5, s + n * w[:, None] * 0.5   # for a lock going right, the normal points down
        fill(c, np.vstack([up, dn[::-1]]), HAIR, band)
        # lower side in shadow, one big shape with a long point; deep where it goes behind the head
        k = np.interp(u, (0, 0.5, 0.86, 1), (0.10, 0.05, 0.30, 0.5))[:, None]
        fill(c, np.vstack([s + n * w[:, None] * k, dn[::-1]]), HAIR_S, band)
        m = u < 0.5
        v = np.clip((0.5 - u[m]) / 0.5, 0, 1)[:, None]
        fill(c, np.vstack([up[m] + (dn[m] - up[m]) * (1 - 0.75 * v ** 0.7), dn[m][::-1]]), HAIR_D, band)
        # line: heavier on the lower, shadowed side, coming to nothing at the point
        ink(c, up, [(0, self.top_line), (0.6, self.top_line - 1), (0.9, 6), (1, 1.5)], band)
        ink(c, dn, [(0, self.low_line), (0.6, self.low_line), (0.9, 8), (1, 1.5)], band)


# her right side, drawn from the lowest up, so the upper ones lie over the lower ones. Long and short alternate.
LOCKS_R = [
    Lock((1140, 950), 720, 30, 68, -74, 230, wave=11, off=0.62),
    Lock((1160, 790), 1010, 18, 58, -78, 290, wave=13, off=0.40),
    Lock((1180, 600), 830, 10, 50, -72, 260, wave=12, off=0.18),
    Lock((1170, 420), 1060, 2, 42, -72, 310, wave=13, off=0.80),
    Lock((1160, 230), 770, -8, 34, -62, 260, wave=11, off=0.55),
]
LOCKS_L = [
    Lock((230, 700), 340, 176, 146, 66, 150, wave=6, freq=0.7, off=0.3, top_line=13, low_line=11),
]


def _smooth(x):
    x = np.clip(x, 0, 1)
    return x * x * (3 - 2 * x)


def scarf_tail(c, wind, phase, band=None):
    """The end of the scarf, out from behind her hair on her right: a soft strip of cloth. It keeps its one turn where it is along the cloth, narrowing there as it
    shows its other side, and spreads a little to a hem cut aslant. A picture of it is a function of wind and phase only, like the hair."""
    L = 1130 * (0.82 + 0.18 * wind)
    root = (1090, 1050)
    s, u = spine(root, L, 6 - 10 * wind ** 0.8, -26, 20 + 14 * wind, 1.0, phase * 0.75, n=90)
    turn = 0.56
    w = (138 + 26 * u ** 3) * (0.26 + 0.74 * _smooth(np.abs(u - turn) / 0.16))
    n = FS.normals(s)
    up, dn = s - n * w[:, None] * 0.5, s + n * w[:, None] * 0.5
    # the hem: slanted, one corner leading, the cut a little hollow
    d = (s[-1] - s[-2]) / np.linalg.norm(s[-1] - s[-2])
    dn = dn[:-2]     # the lower edge stops short, so the cut runs back from the leading corner
    c0, c1 = up[-1] + d * 46, dn[-1]
    hem = FS.spline([c0, (c0 + c1) / 2 - d * 9, c1], 10)[:-1]
    outline = np.vstack([up, hem, dn[::-1]])
    fill(c, outline, SCARF, band)
    # before the turn its lower edge is in shadow, running out to nothing at the turn. Past the turn we see the cloth's other side, a shade darker, with
    # the shadow of the fold where it comes round
    a_, b_ = u <= turn, u >= turn
    dn_a, dn_b = dn[a_[:-2]], dn[b_[:-2]]
    k = 0.42 * (1 - _smooth((u - turn + 0.22) / 0.20))
    fill(c, np.vstack([dn_a + (up[a_] - dn_a) * k[a_][:, None], dn_a[::-1]]), SCARF_S, band)
    fill(c, np.vstack([up[b_], hem, dn_b[::-1]]), SCARF_B, band)
    k2 = 0.70 * (1 - _smooth((u - turn) / 0.15))
    n_b = len(dn_b)
    fill(c, np.vstack([up[b_][:n_b], (up[b_][:n_b] + (dn_b - up[b_][:n_b]) * k2[b_][:n_b, None])[::-1]]), SCARF_S, band)
    # one closed outline, so nothing sticks out at the corners of the hem
    c.drawPath(path_of(outline), skia.Paint(AntiAlias=True, Color4f=tone(INK, band), Style=skia.Paint.kStroke_Style, StrokeWidth=8.5, StrokeJoin=skia.Paint.kRound_Join))
    # the edge that comes across at the turn, and one soft crease running towards the hem
    m = (u > turn - 0.035) & (u < turn + 0.02)
    ink(c, np.vstack([up[m][:1], dn[m[:-2]][-1:]]), [(0, 7), (1, 3)], band)
    m = (u > 0.74) & (u < 0.95)
    ink(c, s[m] + n[m] * w[m, None] * 0.16, [(0, 0.6), (0.5, 5), (1, 0.6)], band)


def bow(c, wind, phase, band=None):
    """Two big pointed lobes and a small square knot, as on her sheet: each lobe rises out and up to a sharp point, with a full belly below.
    The wind only leans them over and sets the tips swaying; it does not press them flat."""
    w = wind
    sway = math.sin(2 * math.pi * phase)
    sway2 = math.sin(2 * math.pi * (phase - 0.22))
    k = np.array((798.0, -440.0))
    R = 430.0
    # unit drawing of her right lobe, knot at the origin
    top_ = np.array([(0, 0), (0.09, -0.17), (0.30, -0.47), (0.62, -0.65), (1.0, -0.80)])
    bot_ = np.array([(1.0, -0.80), (0.985, -0.46), (0.87, -0.14), (0.60, 0.05), (0.28, 0.115), (0.0, 0.10)])
    for sgn, sw in ((-1.0, sway), (1.0, sway2)):
        a = math.radians((w - 0.2) * 16 + (3.0 if sgn > 0 else 0.0))
        ca, sa = math.cos(a), math.sin(a)

        def place(q, tipw):
            x, y = q[:, 0] * sgn, q[:, 1].copy()
            # the outer part of the lobe lags behind its body
            y = y + tipw * 0.035 * w * sw * q[:, 0] ** 2
            return k + R * np.c_[x * ca - y * sa, x * sa + y * ca]
        top, bot = FS.spline(place(top_, 1.0)), FS.spline(place(bot_, 1.0))
        _lobe(c, top, bot, (k[0], k[1] + 18), band)
    # knot
    kn = [(762, -480), (834, -480), (840, -404), (756, -404)]
    fill(c, kn, WHITE, band)
    fill(c, [(758, -422), (838, -422), (840, -404), (756, -404)], WHITE_S, band)
    ink(c, np.array(kn + [kn[0]], float), 10, band)


def _lobe(c, top, bot, knot, band):
    outline = np.vstack([top, bot])
    fill(c, outline, WHITE, band)
    # one hard shadow along the lower edge, coming to a point towards the tip; and where the cloth gathers at the knot
    n = FS.normals(bot)
    u = FS.arclen(bot)
    wd = np.interp(u, (0, 0.3, 0.8, 1), (0, 22, 36, 64))[:, None]
    side = np.sign(np.dot(np.mean(top, 0) - np.mean(bot, 0), np.mean(n, 0))) or 1
    fill(c, np.vstack([bot, (bot + n * wd * side)[::-1]]), WHITE_S, band)
    ink(c, top, [(0, 10), (0.2, 12), (0.8, 11), (1, 4)], band)
    ink(c, bot, [(0, 4), (0.15, 13), (0.8, 14), (1, 10)], band)
    # one fold line, from the knot towards the tip, tapering to nothing
    mid = top[len(top) * 3 // 5]
    a = np.array(knot, float)
    b = a + (mid - a) * 0.72
    ctrl = (a + b) / 2 + np.array([0, 16.0])
    ink(c, FS.spline([a, ctrl, b]), [(0, 8), (0.4, 5), (1, 0.5)], band)


# ---- what does not move
def body(c, band=None):
    """Blouse and collar below the scarf, narrow shoulders, then the scarf wound once round her neck, with two big folds."""
    fill(c, [(140, 1700), (250, 1270), (470, 1130), (1070, 1130), (1300, 1270), (1420, 1700)], WHITE, band)
    # collar: navy, one white line, as on her sheet
    col_o = FS.spline([(250, 1290), (420, 1160), (560, 1110)])
    col_r = FS.spline([(1300, 1290), (1120, 1160), (980, 1110)])
    fill(c, np.vstack([col_o, col_r[::-1], [(1040, 1420), (770, 1560), (500, 1420)]]), NAVY, band)
    ink(c, col_o, 11, band)
    ink(c, col_r, 11, band)
    for a, b in (((286, 1322), (560, 1200)), ((1254, 1322), (980, 1200))):
        fill(c, FS.brush(np.array([a, b], float), 9), WHITE, band)


def scarf(c, band=None, behind=False):
    """Wound round her neck as on her sheet: the throat in dark above its upper edge, which comes down to a shallow V in front of the neck where one band crosses the
    other, and a few clear folds with hard shadows. The lower part of it, and the collar under it, are below the frame in the last shot.
    behind: also the dark inside of the scarf behind her neck (the first pass, before the head)."""
    if behind:
        fill(c, FS.spline([(420, 985), (520, 948), (770, 925), (1020, 948), (1120, 985), (770, 1060)], 12), "#17181F", band)
    top = FS.spline([(372, 992), (470, 968), (610, 985), (772, 1010), (930, 980), (1072, 958), (1176, 990)])
    low = FS.spline([(1176, 990), (1222, 1085), (1215, 1180), (1190, 1270), (980, 1340), (770, 1370), (560, 1340), (350, 1270), (322, 1180), (326, 1085), (372, 992)])
    fill(c, np.vstack([top, low]), SCARF, band)
    # hard shadows: under the crossing, and under each fold
    cross = FS.spline([(776, 1012), (700, 1036), (620, 1046)], 10)
    fold_r = FS.spline([(1176, 1012), (990, 1040), (850, 1078), (720, 1122)], 12)
    fold_l = FS.spline([(372, 1046), (470, 1072), (610, 1092)], 10)
    fill(c, np.vstack([cross, FS.spline([(620, 1046), (705, 1058), (790, 1034), (776, 1012)], 10)]), SCARF_S, band)
    fill(c, np.vstack([fold_r, FS.spline([(720, 1122), (860, 1122), (1010, 1082), (1195, 1054)], 12)]), SCARF_S, band)
    fill(c, np.vstack([fold_l, FS.spline([(610, 1092), (490, 1112), (345, 1086)], 10)]), SCARF_S, band)
    ink(c, top, [(0, 12), (0.5, 11), (1, 12)], band)
    ink(c, low, [(0, 12), (0.5, 13), (1, 12)], band)
    # the band coming across from her right, over the other, at the V; the folds, heavy where they start and running out to nothing
    ink(c, cross, [(0, 9), (0.5, 6.5), (1, 0.8)], band)
    ink(c, fold_r, [(0, 11), (0.45, 8.5), (1, 0.8)], band)
    ink(c, fold_l, [(0, 11), (0.5, 8.5), (1, 0.8)], band)


def streaks(c, wind, phase, band=None):
    """Long tapered strokes of the wind across the sky, each one of the iris's own paler colours. They slide along faster while the wind is strong."""
    for (x, y, ln, th, col, off) in ((1620, -250, 980, 22, SKY[5], 0.0), (1760, -120, 700, 14, SKY[6], 0.3), (1540, 90, 840, 18, SKY[5], 0.6), (-720, -80, 560, 13, SKY[4], 0.15), (-640, 330, 680, 16, SKY[4], 0.5), (1960, 330, 500, 11, SKY[6], 0.8),
                                     (-260, -190, 760, 16, SKY[5], 0.25), (120, 480, 620, 13, SKY[5], 0.7), (-1250, 120, 900, 19, SKY[5], 0.4), (-1500, -300, 640, 13, SKY[6], 0.9), (-1100, 560, 720, 15, SKY[6], 0.1)):
        # they run on across the sky and come round again, far outside the frame, so the wind never runs out of them
        x_ = -2400 + (x + 160 * phase + 40 * off + 2400) % 5200
        c_ = FS.spline([(x_, y), (x_ + ln * 0.5, y - ln * 0.05), (x_ + ln, y - ln * 0.13)], 20)
        fill(c, FS.brush(c_, [(0, 0.5), (0.55, th * 1.5), (1, 0.5)]), col, band)


def sky(c, band=None):
    """Her iris, enlarged. She stands where its pupil would be. Its bands run dark at the top to pale at the bottom, and curve like the bands in
    her eye: ovals one inside another, the darkest innermost. Its catch-lights are small and far off, one high up, the little flecks low on the right."""
    cx = 768
    c.drawRect(skia.Rect.MakeLTRB(-4000, -4000, 5000, 5000), skia.Paint(Color4f=tone(SKY[-1], band)))
    for i, bottom in enumerate((1400, 1180, 960, 740, 520, 300, 60)):
        col = SKY[len(SKY) - 2 - i]
        rx, ry = 1300 + (bottom + 200) * 1.05, 1500 + (bottom + 200) * 0.40
        p = skia.Path()
        p.addOval(skia.Rect.MakeLTRB(cx + 60 - rx, bottom - 2 * ry, cx + 60 + rx, bottom))
        c.drawPath(p, skia.Paint(AntiAlias=True, Color4f=tone(col, band)))
    white = tone("#F2FCFB", band)
    for x, y, r in ((1960, -360, 48), (2470, 760, 34), (2370, 830, 20), (2570, 860, 14), (2460, 900, 11)):
        c.drawCircle(x, y, r, skia.Paint(AntiAlias=True, Color4f=white))


# ---- the bar, torn up by the same wind
def torn_pieces(bar):
    """Pieces cut from the real bar's own drawing (src/art/bar.py), kept as vector pictures so their torn edges stay crisp at any size: a torn outline clips the bar's own marker
    strokes and handwriting. Each has a front and a plain back, and where it starts, how far it goes per unit of the wind's run, its size, angle, spin and flip."""
    rng = np.random.default_rng(14)
    th, ln = bar.thick, bar.length
    adv = th * 0.66 * 1.22
    hw = ln / 2

    def jag(a, b, amp, n):
        a, b = np.array(a, float), np.array(b, float)
        nrm = np.array([-(b - a)[1], (b - a)[0]]) / (np.linalg.norm(b - a) + 1e-6)
        out = [a]
        for i in range(1, n):
            f = (i + rng.uniform(-0.3, 0.3)) / n
            out.append(a + (b - a) * f + nrm * rng.uniform(-amp, amp))
        out.append(b)
        return out

    def marker(a, b):
        """The bar's own long edge: a marker stroke, gently uneven. Only the sides that were torn are jagged."""
        a, b = np.array(a, float), np.array(b, float)
        k = max(3, int(np.linalg.norm(b - a) / 90))
        q = [a + (b - a) * i / k + (0, rng.uniform(-5, 5) if 0 < i < k else 0) for i in range(k + 1)]
        return list(FS.spline(q, 6))

    def cut(x0, x1, y0, y1, tl=True, tr=True):
        amp = (y1 - y0) * 0.085
        top, bot = marker((x0, y0), (x1, y0)), marker((x1, y1), (x0, y1))
        right = jag((x1, y0), (x1, y1), amp if tr else 2, 11 if tr else 2)
        left = jag((x0, y1), (x0, y0), amp if tl else 2, 11 if tl else 2)
        pts = np.array(top + right[1:] + bot[1:] + left[1:-1])
        # the paper torn along with the ink: a thin pale edge on the torn sides
        pale = np.array(top + [q + (rng.uniform(3, 8), 0) for q in right[1:-1]] + bot + [q + (-rng.uniform(3, 8), 0) for q in left[1:-1]])
        ink_c, back_c = skia.Color4f(0.035, 0.035, 0.05, 1), skia.Color4f(0x24 / 255, 0x28 / 255, 0x36 / 255, 1)
        pics = []
        for front in (True, False):
            rec = skia.PictureRecorder()
            cv = rec.beginRecording(skia.Rect.MakeLTRB(x0 - 60, y0 - 60, x1 + 60, y1 + 60))
            cv.save()
            cv.clipPath(path_of(pale), True)
            cv.drawRect(skia.Rect.MakeLTRB(x0 - 60, y0 - 2, x1 + 60, y1 + 2), skia.Paint(AntiAlias=True, Color4f=tone("#F6F3EA")))
            cv.restore()
            cv.save()
            cv.clipPath(path_of(pts), True)
            # the marker, solid: nothing of the sky shows through a piece
            cv.drawRect(skia.Rect.MakeLTRB(x0 - 60, y0 - 60, x1 + 60, y1 + 60), skia.Paint(AntiAlias=True, Color4f=ink_c if front else back_c))
            if front:
                cv.rotate(-bar.angle)
                cv.translate(-bar.cx, -bar.cy)
                bar.draw(cv, progress=0.0, write=1.0)
            cv.restore()
            pics.append(rec.finishRecordingAsPicture())
        return pics, ((x0 + x1) / 2, (y0 + y1) / 2)

    # In screen pixels, seconds from the start of the shot (bust) or from the band's return (close). "女A" goes first and "少" just behind it on the same line of the wind:
    # each about 200 px, out from behind her head into the open sky on her right, so for a good second they read 少女A beside her, as she opens her eyes. Then they are gone.
    P = dict(bust=[], close=[])
    wa, sh = cut(-adv * 0.46, adv * 1.52, -th * 0.47, th * 0.47), cut(-adv * 1.52, -adv * 0.49, -th * 0.47, th * 0.47)
    scrap_r, scrap_l = cut(adv * 1.56, adv * 1.56 + 190, -th * 0.30, th * 0.06), cut(-adv * 1.56 - 150, -adv * 1.56, -th * 0.16, th * 0.20)
    P["bust"].append(dict(img=wa, s=0.60, p=(1090, 330), v=(610, -82), r0=0.0, a=-8, sp=-3.0, fl=(0.0, 0.04), front=False))
    P["bust"].append(dict(img=sh, s=0.60, p=(760, 440), v=(640, -92), r0=0.0, a=-5, sp=4.0, fl=(0.0, 0.05), front=False))
    # a blank scrap on her other side going in behind her, and one low down coming out from behind her scarf into the pale sky
    P["bust"].append(dict(img=scrap_l, s=0.80, p=(-160, 250), v=(1050, -50), r0=0.10, a=-6, sp=22.0, fl=(0.6, 0.7), front=False))
    P["bust"].append(dict(img=scrap_r, s=0.90, p=(800, 985), v=(980, -120), r0=0.95, a=-14, sp=30.0, fl=(0.3, 0.9), front=False))
    # the close-up, in its own picture's pixels: the sky is only at the edges, so scraps of the torn bar go by behind her hair, in and out between its blown clumps. Nothing crosses her face
    P["close"].append(dict(img=scrap_l, s=0.95, p=(1120, 600), v=(760, -150), r0=0.62, a=-6, sp=34.0, fl=(0.1, 0.8), front=False))
    P["close"].append(dict(img=scrap_r, s=0.72, p=(1170, 240), v=(700, -110), r0=0.92, a=-16, sp=-40.0, fl=(0.4, 1.0), front=False))
    P["close"].append(dict(img=scrap_l, s=0.70, p=(1130, 830), v=(820, -190), r0=1.16, a=8, sp=46.0, fl=(0.7, 0.9), front=False))
    return P


def draw_pieces(c, pieces, run, wind, near=False):
    for k in pieces:
        r = run - k["r0"]
        if r < 0 or k["front"] != near:
            continue
        x, y = k["p"][0] + k["v"][0] * r, k["p"][1] + k["v"][1] * r
        if not -500 < x < 2420:
            continue
        # it rides up and down on the wind a little, less as the wind dies
        y += 12 * math.sin(r * 4.0 + k["p"][0]) * min(1.0, 1.2 * wind)
        fl = math.cos(2 * math.pi * (k["fl"][0] + k["fl"][1] * r))
        (front, back), (mx, my) = k["img"]
        c.save()
        c.translate(x, y)
        c.rotate(k["a"] + k["sp"] * r)
        c.scale(k["s"], k["s"] * max(abs(fl), 0.16))
        c.translate(-mx, -my)
        c.drawPicture(front if fl >= 0 else back)
        c.restore()
