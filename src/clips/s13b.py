"""The form. Her name field is printed 少女A. She strikes it out and straight away writes 鏡音リン beside it, stroke by stroke in the real order, the pen
on the line all the way along each stroke and lifted between them: slowly at first, faster as she goes. She lifts the pen; we read it; black. The camera pushes in while she writes, then draws back a little and ends framing the struck-out name, the new name and the seal."""
import math
import sys
from pathlib import Path

import cv2
import numpy as np
import skia
from PIL import Image, ImageDraw, ImageFont
from scipy.spatial import cKDTree

sys.path.insert(0, str(Path(__file__).parent))
import common as K  # noqa: E402
import engine as E  # noqa: E402
import cutout as C  # noqa: E402
import handkit as HK  # noqa: E402
from bar import _catmull  # noqa: E402
from timeline import bar_time  # noqa: E402
import s07x as S07  # noqa: E402

ROOT = K.ROOT
T0, T1 = 6660 / 30, 7149 / 30
# the bars after 222: nothing here happens off the bar
B = [bar_time(n) for n in range(121, 130)]       # 223.73, 225.58, 227.42, 229.27, 231.11, 232.96, 234.81, 236.65, ...
BEAT = (B[1] - B[0]) / 4
# the note with the two flowers comes on first, under her left hand; the pen arrives as that hand goes
NOTE_IN = (B[0], B[0] + 0.34)
NOTE_LIFT = (B[0] + 0.92, B[0] + 1.30)
HAND_S = 0.60              # picture pixels to sheet pixels: the same drawings all the way in, only the camera gets nearer
LEFT_S = 0.60              # her other hand, which only puts the note down
SLEEVE_LOOSE = 0.5         # the sleeve past the picture's edge eases wider towards the elbow, see handkit.extrude
SLEEVE_PAD = 1900          # how far it is carried on, in picture pixels: far enough that its end, fill and outline, is off the screen at any distance the camera comes to
# the camera. Before the note: it reads the sheet, top right to the printed name, then pulls back
READ = [(T0, 2.30, 1535.0, 212.0), (T0 + 0.46, 2.30, 1470.0, 212.0), (T0 + 1.00, 1.75, 620.0, 468.0), (T0 + 1.26, 1.72, 628.0, 468.0), (B[0] + 0.12, 1.0, 960.0, 540.0)]
STRIKE = B[2] + 2 * BEAT   # 228.34: the point comes down on the printed name
LINE1_END = STRIKE + 0.70  # the first line, then the pen is carried back, set down on the bar, and the second
LINE2 = (B[3], B[3] + 2 * BEAT / 2)
STRUCK = LINE2[1]          # both lines are through it
# after the strike-out it pushes in, whatever is being written stays in the frame, and once the pen is off the name it draws back a little, to end on the struck-out 少女A and 鏡音リン together
PUSH_T = STRUCK - 0.10
S_WIDE = 1.045
# the writing hand needs room to the right of the point: while ン is written the view reaches past it, and at the end it holds all of the struck-out name, the new name and the seal
CAM_KEYS = ((231.0, 1.34, 1040.0, 512.0), (233.9, 1.42, 1100.0, 496.0), (235.9, 1.45, 1225.0, 488.0), (236.9, 1.45, 1345.0, 486.0), (237.8, 1.25, 1025.0, 474.0), (T1 + 0.6, 1.24, 1030.0, 472.0))

PRINT = "#0AA5D8"          # the form's own printing: the film's cyan, a shade heavier so small type holds on white
RULE = E.CYAN
LIGHT = (0.70, 0.71)       # where every shadow falls, hand and pen alike: to the lower right
SHADE = "#2A3A4C"

# where things are on the sheet
NAME_Y = 468               # middle of the name row
NAME_X0, NAME_X1 = 372, 856
BESIDE = (1032, 500)       # the fixed point of the slow move while the sheet is wide
# What she writes, in the empty part of the name row. The shape of the ink is a pen hand (Klee One, a textbook-style pen lettering face). The strokes below are its centre lines, traced on a 100 box,
# in the order they are written, checked one by one against KanjiVG. The point runs along them and the ink appears behind it, so the shape is good and the writing is real.
KIN = [   # 金 on the left of 鏡: 8 strokes
    ([(27, 18), (25.5, 24.5), (21, 35), (14.5, 46.5), (7, 60)], 0.45),      # left sweep
    ([(28.5, 27), (35, 33), (39.5, 38.5)], 0.0),                          # right, short
    ([(19.5, 47), (29, 46.2), (38.5, 45.2)], 0.0),                        # first bar
    ([(11, 60), (22, 59.5), (42, 58.3)], 0.0),                            # second bar
    ([(26.8, 47.5), (26.6, 65), (26.3, 88)], 0.0),                        # upright
    ([(16, 67), (18.5, 74), (20.5, 81.5)], 0.0),                          # left dot
    ([(38, 65), (36, 73), (31.5, 81.5)], 0.25),                           # right dot, falling to the left
    ([(9.5, 92.5), (25, 88.5), (44, 82.3)], 0.35),                        # the rising bar
]
KYOU = [  # 竟 on the right of 鏡: 11 strokes
    ([(62, 15.5), (63.6, 19), (63.4, 26)], 0.0),                          # 立: the dot
    ([(44.5, 28.5), (60, 27.8), (84, 25.8)], 0.0),                        # bar
    ([(53, 31.5), (57, 36), (60.5, 40.5)], 0.0),                          # short, falling right
    ([(72, 29.5), (70.5, 34), (66, 41)], 0.2),                            # short, falling left
    ([(41, 44), (50, 44.6), (70, 43.5), (90, 42)], 0.0),                  # long bar
    ([(46, 51.5), (49, 58), (50.5, 74), (50.7, 76)], 0.0),                # 日: left
    ([(51, 54.5), (70, 53.3), (81, 52.8), (80.7, 60), (78.8, 74.5)], 0.0),  # top and right, one stroke with a corner
    ([(52, 63.2), (65, 62.6), (78, 61.8)], 0.0),                          # middle
    ([(50.5, 73.5), (66, 72.7), (82, 72.2)], 0.0),                        # bottom
    ([(59, 75.5), (56, 84), (49, 91.5), (34, 98.5)], 0.5),                # 儿: left sweep
    ([(70, 75), (69.8, 88), (71.5, 93), (75, 95.2), (83, 95.7), (89, 93.5), (91, 88), (92.7, 77.5)], 0.22),  # down, along and the flick up
]
ON = [    # 音: 9 strokes
    ([(45, 14.5), (48.5, 18), (49, 27)], 0.0),
    ([(17.5, 29.5), (30, 30), (60, 28.5), (81, 27)], 0.0),
    ([(33, 34), (38, 40), (42.5, 47)], 0.0),
    ([(64, 32), (62, 38), (56.5, 47.5)], 0.2),
    ([(6, 51), (15, 52), (50, 50.7), (93, 48.8)], 0.0),
    ([(26.5, 61.5), (28.5, 65), (31, 90), (32, 96)], 0.0),                  # 日: left
    ([(31, 64.5), (52, 63.8), (72, 62.8), (70.2, 76), (68.8, 93)], 0.0),  # top and right
    ([(33, 78.3), (50, 77.8), (67, 77.1)], 0.0),
    ([(32.5, 93), (50, 92.5), (73, 92)], 0.0),
]
RI = [    # リ: 2 strokes
    ([(33.5, 26), (36.5, 30), (36.6, 50), (36.5, 66)], 0.0),
    ([(60.5, 24), (64.3, 30), (64.5, 48), (62.5, 64), (58.5, 76), (50.5, 87), (42, 94), (34, 98.5)], 0.5),
]
N_ = [    # ン: 2 strokes
    ([(21, 35), (31, 39), (43, 46)], 0.0),
    ([(23, 83.5), (32, 83), (47, 77), (62, 66.5), (76, 54.5), (87, 42)], 0.55),
]
# (character, strokes, left, top, box, turn in degrees): 鏡 the largest, the kana smaller and a little under the line's middle, as a person writes them
NAME = (("鏡", (*KIN, *KYOU), 887.0, 322.0, 268.0, -0.9), ("音", ON, 1142.0, 338.0, 240.0, 0.5), ("リ", RI, 1323.0, 351.0, 215.0, -1.0), ("ン", N_, 1439.0, 349.0, 215.0, -0.6))
INK_FONT = ROOT / "assets" / "fonts" / "ttf" / "KleeOne-Regular.ttf"
INK_K = 3                  # the ink is kept three times the sheet's size: the camera comes close
INK_BOX = (870, 300, 800, 330)   # the part of the sheet it can fall in
FAST_FROM = 1               # from 音 on the pen moves too fast to change drawing for each stroke: one grip, the height of the point tells the lifts
KEY_HOLD = 5                # frames: the shortest a drawing of the hand is shown
HAND_GIVE = 0.2             # how much of the lag between wrist and point is taken up by stretching the picture
# when each character is written, by the bars: 鏡 slowly, then each one faster
NAME_T = ((230.02, 233.64), (B[5] + 2 * BEAT, B[6] + 2 * BEAT), (B[6] + 2 * BEAT + 0.22, B[7] - 0.13), (B[7], B[7] + 0.46))
LIFTED = (NAME_T[-1][1], NAME_T[-1][1] + 0.42)   # the pen goes up and away, off the name
REST = (1572.0, 662.0)     # where the point ends up: the hand lies to its right, clear of the name and the seal
NOTE_C = (800.0, 792.0)    # the note, lying on the form below the name
NOTE_W, NOTE_H = 436, 306
NOTE_ROT = -5.0


def load_hand(name):
    rgba = C.load(ROOT / "assets" / "gen" / "cut" / f"{name}.png").copy()
    # specks of the green it was drawn on, shut in between the fingers and under the pen's clip
    r, g, b = rgba[..., 0], rgba[..., 1], rgba[..., 2]
    rgba[(g > r + 0.14) & (g > b + 0.14), 3] = 0
    return rgba


def cuff_centre(rgba):
    """Where the navy cuff band is: what stays put from one drawing of this hand to the next."""
    r, g, b = rgba[..., 0], rgba[..., 1], rgba[..., 2]
    m = (b > r + 0.08) & (b > 0.2) & (b < 0.5) & (rgba[..., 3] > 0.9)
    ys, xs = np.nonzero(m)
    return float(xs.mean()), float(ys.mean())


def pen_tip(rgba, band=6):
    """The pen is the leftmost thing in every one of these drawings: its point is the first solid column."""
    a = rgba[..., 3] > 0.6
    x = int(np.nonzero(a.any(0))[0][0])
    ys = np.nonzero(a[:, x:x + band].any(1))[0]
    return float(x), float(ys.mean())


def scrawl(a, b, seed, n=26, amp=2.2):
    """A ruled line by a hand: nearly straight, a little wander, slightly heavier in the middle."""
    rng = np.random.default_rng(seed)
    t = np.linspace(0, 1, n)
    wob = np.convolve(rng.normal(0, 1, n + 6), np.ones(7) / 7, mode="valid")[:n] * amp * 2.2
    x = a[0] + (b[0] - a[0]) * t
    y = a[1] + (b[1] - a[1]) * t + wob + 3.0 * np.sin(t * math.pi)
    return np.column_stack([x, y])


class Form(E.Clip):
    name = "s13b"
    t0, t1 = T0, T1
    grain = 0.010
    shutter = 0.2

    def setup(self):
        self.cuts = ()
        self.h = {}
        base = None
        for key, name in (("rest", "h44_rest"), ("write", "h44_write"), ("lift", "h44_lift"), ("tight", "h44_tight")):
            raw = load_hand(name)
            tip = pen_tip(raw)
            cuff = cuff_centre(raw)
            v = (cuff[0] - tip[0], cuff[1] - tip[1])
            base = base or v
            self.base_v = base
            # the same hand: changing drawing moves the fingers and the pen, and never the wrist or the sleeve
            turn = math.degrees(math.atan2(base[1], base[0]) - math.atan2(v[1], v[0]))
            size = math.hypot(*base) / math.hypot(*v)
            raw = HK.extrude(raw, (1.0, 0.72), pad=SLEEVE_PAD, loose=SLEEVE_LOOSE)
            self.h[key] = dict(img=E.np_to_image(raw), tip=tip, turn=turn, size=size)
        # her other hand: it comes in from the lower left, so its sleeve is carried on that way
        self.left = {}
        for key, name in (("press", "h42_a"), ("away", "h42_b")):
            raw = load_hand(name)
            a_ = raw[..., 3] > 0.6
            ys, xs = np.nonzero(a_[:260])
            # the fingertip nearest the upper right is what holds the note down
            k_ = int(np.argmax(xs - ys))
            ft = (float(xs[k_] + 1000), float(ys[k_]))
            ex = HK.extrude(raw[:, ::-1], (1.0, 0.9), pad=SLEEVE_PAD, loose=SLEEVE_LOOSE)[:, ::-1]
            self.left[key] = dict(img=E.np_to_image(np.ascontiguousarray(ex)), tip=ft)
        self.form = self.bake_form(1)
        self.form_big = self.bake_form(3)
        self.note = self.bake_note()
        self.line1 = scrawl((NAME_X0 - 26, NAME_Y - 24), (NAME_X1 + 30, NAME_Y - 30), 5)
        self.line2 = scrawl((NAME_X0 - 18, NAME_Y + 26), (NAME_X1 + 34, NAME_Y + 17), 9)
        self.make_ink()
        self.time_strokes()
        self.script = self.build_script()
        self.make_path()

    def time_strokes(self):
        """Each character has its time from NAME_T; inside it a stroke takes its share by length, and each lift by how far the pen has to go."""
        for ci, (t0, t1) in enumerate(NAME_T):
            ss = [x for x in self.strokes if x["ci"] == ci]
            em = NAME[ci][4]
            n = len(ss)
            w = []
            for i, st in enumerate(ss):
                # the first strokes of a word are the careful ones
                care = 1.0 + (0.40 if ci == 0 else 0.15) * (1 - i / max(n - 1, 1))
                draw = (st["L"] / em * 1.0 + 0.10) * care
                gap = 0.0
                if i:
                    d = float(np.hypot(*(st["pts"][0] - ss[i - 1]["pts"][-1])))
                    gap = (d / em * 0.35 + 0.085) * care
                w.append((gap, draw))
            k = (t1 - t0) / sum(a + b for a, b in w)
            t = t0
            for st, (gap, draw) in zip(ss, w):
                st["t0"] = t + gap * k
                st["t1"] = st["t0"] + draw * k
                t = st["t1"]

    def tip_at(self, q):
        """Where the point is once she is writing, how high, and which drawing: on the stroke while it is down, and carried between strokes."""
        ss = self.strokes
        for i, st in enumerate(ss):
            if q < st["t0"]:
                a = ss[i - 1]["pts"][-1] if i else self.after_strike
                t0 = ss[i - 1]["t1"] if i else self.after_strike_t
                u = E.ease_io(E.seg(q, t0, st["t0"]), 1.4)
                b = st["pts"][0]
                d = float(np.hypot(*(b - a)))
                z = min(10.0 + d * 0.11, 34.0) * math.sin(math.pi * u)
                return "write" if st["ci"] >= FAST_FROM else "lift", tuple(a + (b - a) * u), z
            if q < st["t1"]:
                u = E.ease_io(E.seg(q, st["t0"], st["t1"]), 1.2)
                pts = st["pts"]
                dv = pts[-1] - pts[0]
                # the fingers close on a stroke pulled down, and stay as they are on a stroke drawn across
                key = "tight" if abs(dv[1]) > abs(dv[0]) and st["ci"] < FAST_FROM else "write"
                return key, self.at(pts, u), 0.0
        u = E.ease_io(E.seg(q, *LIFTED), 1.6)
        a = ss[-1]["pts"][-1]
        b = np.array(REST)
        return "lift" if u < 1 else "rest", tuple(a + (b - a) * u), 44.0 * math.sin(math.pi * min(u, 1.0) * 0.5)

    def make_path(self):
        """The hand does not slide rigidly with the point: the wrist follows the point's path lazily, and the hand turns round it a little. So small strokes are made by the fingers and the wrist travels along the line."""
        t0 = self.after_strike_t
        n = int((T1 + 0.5 - t0) * 30) + 1
        tips = np.array([self.tip_at(t0 + i / 30)[1] for i in range(n)])
        pad = np.concatenate([np.repeat(tips[:1], 30, 0), tips, np.repeat(tips[-1:], 30, 0)])

        def low(sig):
            ker = np.exp(-0.5 * (np.arange(-30, 31) / (sig * 30)) ** 2)
            ker /= ker.sum()
            return np.stack([np.convolve(pad[:, k], ker, mode="valid") for k in (0, 1)], -1)

        self.path_t0 = t0
        # the wrist's path against the hand's own, itself smoothed: the point jumps from stroke to stroke in two or three frames, and the hand's turn must not jump with it
        self.path_lag = low(0.35) - low(0.12)
        # a drawing shown for only a few frames is the picture flickering: anything shorter than this stays the drawing it was
        keys = [self.tip_at(t0 + i / 30)[0] for i in range(n)]
        i = 1
        while i < n:
            if keys[i] != keys[i - 1]:
                j = i
                while j < n and keys[j] == keys[i]:
                    j += 1
                if j - i < KEY_HOLD and j < n:
                    keys[i:j] = [keys[i - 1]] * (j - i)
                else:
                    i = j
                    continue
            i += 1
        self.key_tab = keys

    def hand_pose(self, q):
        """How much the hand is turned and stretched at this moment, from how far the point is from where the wrist would like it."""
        i = int(round((q - self.path_t0) * 30))
        i = min(max(i, 0), len(self.path_lag) - 1)
        lag = self.path_lag[i] * 0.55
        v = np.array(self.base_v) * HAND_S
        o = v + lag
        turn = math.degrees(math.atan2(o[1], o[0]) - math.atan2(v[1], v[0]))
        # a hand does not change size: it may only give a very little along its own length
        return turn, 1.0 + (float(np.hypot(*o) / np.hypot(*v)) - 1.0) * HAND_GIVE

    def make_ink(self):
        """Every pixel of the name belongs to one stroke and sits at one point along it. A pixel where two strokes cross goes to the one written first, so nothing has a gap waiting for a later stroke."""
        bx, by, bw, bh = INK_BOX
        k = INK_K
        self.strokes = []
        alpha = np.zeros((bh * k, bw * k), np.float32)
        lab = np.full(alpha.shape, -1, np.int16)
        par = np.zeros(alpha.shape, np.float32)
        for ci, (ch, strokes, x0, y0, em, turn) in enumerate(NAME):
            box = int(em * k)
            font = ImageFont.truetype(str(INK_FONT), int(box * 0.96))
            im = Image.new("L", (box, box), 0)
            ImageDraw.Draw(im).text((box / 2, box / 2), ch, font=font, fill=255, anchor="mm")
            M = cv2.getRotationMatrix2D((box / 2, box / 2), -turn, 1.0)
            g = cv2.warpAffine(np.asarray(im), M, (box, box), flags=cv2.INTER_CUBIC).astype(np.float32) / 255
            ca, sa = math.cos(math.radians(turn)), math.sin(math.radians(turn))
            first = len(self.strokes)
            for pts, taper in strokes:
                q = []
                for u, v in pts:
                    u_, v_ = u / 100 - 0.5, v / 100 - 0.5
                    q.append((x0 + em * 0.5 + em * (u_ * ca - v_ * sa), y0 + em * 0.5 + em * (u_ * sa + v_ * ca)))
                dense = _catmull(q, 24)
                seg_ = np.hypot(*(dense[1:] - dense[:-1]).T)
                self.strokes.append(dict(pts=dense, ci=ci, L=float(seg_.sum()), u=np.concatenate([[0], np.cumsum(seg_)]) / max(seg_.sum(), 1e-3)))
            ys, xs = np.nonzero(g > 0.003)
            sx, sy = x0 + xs / k, y0 + ys / k        # the pixels of this character, on the sheet
            P = np.column_stack([sx, sy])
            best = np.full(len(P), -1, np.int32)
            near = np.full(len(P), 1e9, np.float32)
            nu = np.zeros(len(P), np.float32)
            near_i = np.zeros(len(P), np.int32)
            nu_near = np.zeros(len(P), np.float32)
            R = em * 0.032                           # a little over half the width of the pen's line
            for i in range(first, len(self.strokes)):
                st = self.strokes[i]
                d, idx = cKDTree(st["pts"]).query(P)
                closer = d < near
                near[closer] = d[closer]
                near_i[closer] = i
                nu_near[closer] = st["u"][idx[closer]]
                take = (best < 0) & (d <= R)
                best[take] = i
                nu[take] = st["u"][idx[take]]
            none = best < 0
            best[none] = near_i[none]
            nu[none] = nu_near[none]
            gx = np.round((sx - bx) * k).astype(int)
            gy = np.round((sy - by) * k).astype(int)
            alpha[gy, gx] = np.maximum(alpha[gy, gx], g[ys, xs])
            lab[gy, gx] = best
            par[gy, gx] = nu
        self.ink_y, self.ink_x = np.nonzero(lab >= 0)
        self.ink_a = (alpha[self.ink_y, self.ink_x] * 255 + 0.5).astype(np.uint8)
        self.ink_l = lab[self.ink_y, self.ink_x]
        self.ink_u = par[self.ink_y, self.ink_x]
        self.ink_shape = alpha.shape
        ic = np.array([int(E.INK.lstrip("#")[i:i + 2], 16) for i in (0, 2, 4)], np.uint8)
        self.ink_rgb = ic
        self.ink_cache = (None, None)

    def ink_image(self, t):
        """The ink so far: each stroke as far as the point has got along it. How far each stroke has got is all that changes from frame to frame."""
        prog = np.full(len(self.strokes), -1.0, np.float32)
        for i, st in enumerate(self.strokes):
            if t > st["t0"]:
                prog[i] = E.ease_io(E.seg(t, st["t0"], st["t1"]), 1.2)
        key = prog.tobytes()
        if self.ink_cache[0] == key:
            return self.ink_cache[1]
        rgba = np.zeros((*self.ink_shape, 4), np.uint8)
        rgba[..., :3] = self.ink_rgb
        show = prog[self.ink_l] >= self.ink_u
        rgba[self.ink_y[show], self.ink_x[show], 3] = self.ink_a[show]
        im = E.np_to_image(rgba)
        self.ink_cache = (key, im)
        return im

    def bake_note(self):
        """The sheet with the two crayon flowers from section 02 and the door: once folded, the code word small in the corner."""
        k = 2
        surf = skia.Surface(NOTE_W * k, NOTE_H * k)
        c = surf.getCanvas()
        c.scale(k, k)
        c.clear(E.col("#FBF8EE"))
        # the fold: the lower half takes the light a shade differently, and a hard line where it was folded
        E.rect(c, 0, NOTE_H * 0.52, NOTE_W, NOTE_H * 0.48, "#EFEBDD")
        E.rect(c, 0, NOTE_H * 0.52 - 1, NOTE_W, 2, "#CFCAB8")
        fl = E.load_image(ROOT / "assets" / "gen" / "raw" / "k01_flowers.png")
        pa = skia.Paint(AntiAlias=True)
        pa.setBlendMode(skia.BlendMode.kMultiply)
        fw = NOTE_W - 40
        c.drawImageRect(fl, skia.Rect.MakeXYWH(20, 8, fw, fw * fl.height() / fl.width()), E.SAMPLING_DOWN, pa)
        S07.draw_strokes(c, S07.pappa_strokes(), NOTE_W - 96, NOTE_H - 42, 24, 2.6, 1.0)
        for r_ in (skia.Rect.MakeXYWH(0, 0, NOTE_W, NOTE_H),):
            c.drawRect(r_, skia.Paint(AntiAlias=True, Color4f=E.col("#9C988A"), Style=skia.Paint.kStroke_Style, StrokeWidth=1.6))
        return surf.makeImageSnapshot()

    def bake_form(self, k):
        """The sheet itself: nothing on it moves, so it is drawn once; k times larger for the close-up."""
        surf = skia.Surface(E.W * k, E.H * k)
        c = surf.getCanvas()
        c.scale(k, k)
        c.clear(E.col(E.PAPER))

        def hline(x0, x1, y, w=3.0, col=RULE):
            E.rect(c, x0, y - w / 2, x1 - x0, w, col)

        def vline(x, y0, y1, w=3.0, col=RULE):
            E.rect(c, x - w / 2, y0, w, y1 - y0, col)

        fx0, fx1 = 92, 1828
        lab_w = 232
        # head of the sheet
        E.Type("届出書", "ShipporiMinchoB1-ExtraBold", 74, tracking=26).draw(c, 960, 92, PRINT)
        E.Type("記入日　　　　年　　　月　　　日", "ZenKakuGothicNew-Medium", 30).draw(c, fx1, 150, PRINT, ax=1)
        # section band
        top = 194
        E.rect(c, fx0, top, fx1 - fx0, 58, RULE)
        E.Type("本人記入欄", "ZenKakuGothicNew-Black", 34, tracking=10).draw(c, fx0 + 30, top + 29, E.PAPER, ax=0)
        E.Type("※ 本人が自分で記入してください", "ZenKakuGothicNew-Bold", 26).draw(c, fx1 - 30, top + 29, E.PAPER, ax=1)
        rows = [("ふりがな", 252, 340), ("氏名", 340, 610), ("生年月日", 610, 712), ("住所", 712, 900), ("備考", 900, 1200)]
        # label column, tinted
        E.rect(c, fx0, 252, lab_w, 1200 - 252, "#DDF1F4")
        for lab, y0, y1 in rows:
            hline(fx0, fx1, y0)
            size = 62 if lab == "氏名" else 32
            tr = 22 if lab == "氏名" else 4
            E.Type(lab, "ZenKakuGothicNew-Bold", size, tracking=tr).draw(c, fx0 + lab_w / 2, (y0 + min(y1, 1040)) / 2 if lab != "備考" else y0 + 60, PRINT)
        vline(fx0, top, 1200, 5)
        vline(fx1, top, 1200, 5)
        vline(fx0 + lab_w, 252, 1200)
        hline(fx0, fx1, 610, 5)
        hline(fx0, fx1, 340, 2)
        E.Type("〒", "ZenKakuGothicNew-Medium", 32).draw(c, fx0 + lab_w + 30, 745, PRINT, ax=0)
        E.Type("年　　　　　月　　　　　日", "ZenKakuGothicNew-Medium", 32).draw(c, fx0 + lab_w + 640, 661, PRINT, ax=0.5)
        # the seal, as on every form of this kind
        c.drawCircle(1732, 475, 44, skia.Paint(AntiAlias=True, Color4f=E.col(RULE), Style=skia.Paint.kStroke_Style, StrokeWidth=3))
        E.Type("印", "ZenKakuGothicNew-Medium", 34).draw(c, 1732, 475, PRINT)
        # the name, printed on it already: printed, in the black of the bar
        name = E.fit("少女A", "ShipporiMinchoB1-ExtraBold", NAME_X1 - NAME_X0, 190, max_size=200)
        name.draw(c, NAME_X0, NAME_Y, E.INK, ax=0, ay=0.5)
        # the sun through the window: a hard line across the sheet, the lower left in shade
        p = skia.Path()
        p.moveTo(-10, 610)
        p.lineTo(620, 1090)
        p.lineTo(-10, 1090)
        p.close()
        c.drawPath(p, skia.Paint(AntiAlias=True, Color4f=E.col(SHADE, 0.13)))
        return surf.makeImageSnapshot()

    # ---- the camera ----
    def camera(self, t):
        """How near, and which point of the sheet is at the middle of the screen."""
        if t < READ[-1][0]:
            for (t0, s0, x0, y0), (t1, s1, x1, y1) in zip(READ, READ[1:]):
                if t < t1:
                    u = E.ease_io(E.seg(t, t0, t1), 2.2) if t1 - t0 > 0.5 else E.seg(t, t0, t1)
                    return math.exp(math.log(s0) + (math.log(s1) - math.log(s0)) * u), x0 + (x1 - x0) * u, y0 + (y1 - y0) * u
        if t < PUSH_T:
            s_ = math.exp(math.log(S_WIDE) * E.seg(t, READ[-1][0], PUSH_T))
            return s_, BESIDE[0] + (960 - BESIDE[0]) / s_, BESIDE[1] + (540 - BESIDE[1]) / s_
        # one long move, smoothed so that it never stops at a key
        if not hasattr(self, "cam_tab"):
            x0, y0 = BESIDE[0] + (960 - BESIDE[0]) / S_WIDE, BESIDE[1] + (540 - BESIDE[1]) / S_WIDE
            keys = np.array(((PUSH_T - 0.6, S_WIDE, x0, y0), (PUSH_T, S_WIDE, x0, y0)) + CAM_KEYS)
            ts = np.arange(PUSH_T - 0.6, T1 + 0.6, 1 / 60)
            tab = np.stack([np.interp(ts, keys[:, 0], np.log(keys[:, 1])), np.interp(ts, keys[:, 0], keys[:, 2]), np.interp(ts, keys[:, 0], keys[:, 3])], -1)
            sig = 0.55 * 60
            ker = np.exp(-0.5 * (np.arange(-120, 121) / sig) ** 2)
            ker /= ker.sum()
            pad = np.concatenate([np.repeat(tab[:1], 120, 0), tab, np.repeat(tab[-1:], 120, 0)])
            self.cam_ts = ts
            self.cam_tab = np.stack([np.convolve(pad[:, k], ker, mode="valid") for k in range(3)], -1)
        L, x, y = [float(np.interp(t, self.cam_ts, self.cam_tab[:, k])) for k in range(3)]
        # it takes over from the slow move without a step: the difference at the join melts away
        w = 1 - E.ease_io(E.seg(t, PUSH_T, PUSH_T + 1.6), 2.0)
        L0, x0, y0 = [float(np.interp(PUSH_T, self.cam_ts, self.cam_tab[:, k])) for k in range(3)]
        xb, yb = BESIDE[0] + (960 - BESIDE[0]) / S_WIDE, BESIDE[1] + (540 - BESIDE[1]) / S_WIDE
        return math.exp(L + (math.log(S_WIDE) - L0) * w), x + (xb - x0) * w, y + (yb - y0) * w

    # ---- the pen ----
    def build_script(self):
        """(from, to, drawing, tip from, tip to, height from, height to, turn from, turn to, how much it trembles)."""
        high = (NAME_X1 + 66.0, NAME_Y - 84.0)
        over = (NAME_X1 - 70.0, NAME_Y - 118.0)
        over_m = (NAME_X0 + 250.0, NAME_Y - 112.0)
        over2 = (NAME_X0 + 80.0, NAME_Y - 104.0)
        l1, l2 = tuple(self.line1[0]), tuple(self.line2[0])
        e1, e2 = tuple(self.line1[-1]), tuple(self.line2[-1])
        t = NOTE_LIFT[0] + 0.16
        sc = []

        def add(t1, key, a, b, z0, z1, br=0.0, r0=0.0, r1=None):
            nonlocal t
            sc.append((t, t1, key, a, b, z0, z1, r0, r0 if r1 is None else r1, br))
            t = t1

        off = (high[0] + 620.0, high[1] + 760.0)
        # it comes in as the other hand goes, all the way to the bar: no empty sheet between them
        add(B[1], "rest", off, high, 150, 150)
        # along the printed name, from its end to its start, reading it: it stops over each part, on the beat
        add(B[1] + 2 * BEAT, "rest", high, over, 150, 128)
        add(B[2], "rest", over, over_m, 128, 128)
        add(B[2] + BEAT, "rest", over_m, over2, 128, 128)
        add(STRIKE, "rest", over2, over2, 128, 128, 1.0)
        # down on to the start of the line, and the two strokes: one grip all along, the arm swinging from the elbow
        add(STRIKE + 0.20, "write", over2, l1, 128, 0, 0.0, 0.0, -5.0)
        add(LINE1_END, "stroke1", l1, e1, 0, 0, 0.0, -5.0, 5.0)
        # the hand is lifted, carried back, set down
        add(LINE2[0], "lift", e1, l2, 0, 0, 0.0, 5.0, -5.0)
        add(LINE2[1], "stroke2", l2, e2, 0, 0, 0.0, -5.0, 5.0)
        # and straight on: everything after this is tip_at
        self.after_strike = np.array(e2)
        self.after_strike_t = t
        return sc

    def state(self, t):
        """Which drawing, where its tip is, how high, how turned, how it trembles. Before the writing on fifteens, like everything her hand does here; writing, on every frame, or a short stroke would be two jumps."""
        if t >= self.after_strike_t:
            q = math.floor(t * 30 + 1e-6) / 30
            key, tip, z = self.tip_at(q)
            key = self.key_tab[min(max(int(round((q - self.path_t0) * 30)), 0), len(self.key_tab) - 1)]
            turn, stretch = self.hand_pose(q)
            # how she comes off the strike-out: its turn fades out over the first lift
            fade = 5.0 * (1 - E.seg(q, self.after_strike_t, self.strokes[0]["t0"]))
            return key, tip, z, turn + fade, 1.0 if t >= LIFTED[1] else 0.0, q, stretch
        q = math.floor(t * 15 + 1e-6) / 15
        for t0, t1, key, a, b, z0, z1, r0, r1, br in self.script:
            if q < t1:
                u = E.ease_io(E.seg(q, t0, t1), 1.6)
                if t1 - t0 < 0.4 and a[0] > 1800:
                    u = E.ease_out(E.seg(q, t0, t1), 2.0)
                if key in ("stroke1", "stroke2"):
                    u = E.ease_io(E.seg(q, t0, t1), 1.3)
                    tip = self.at(self.line1 if key == "stroke1" else self.line2, u)
                    return "write", tip, 0.0, r0 + (r1 - r0) * u, 0.0, q, 1.0
                z = z0 + (z1 - z0) * u
                x, y = a[0] + (b[0] - a[0]) * u, a[1] + (b[1] - a[1]) * u
                if key == "lift" and z0 == z1 == 0:
                    z = 34.0 * math.sin(math.pi * u)     # carried over, off the paper
                r = r0 + (r1 - r0) * u
                return key, (x, y), z, r, br, q, 1.0
        return "write", tuple(self.after_strike), 0.0, 5.0, 0.0, q, 1.0

    def at(self, pts, u):
        i = u * (len(pts) - 1)
        k = min(int(i), len(pts) - 2)
        return tuple(pts[k] + (pts[k + 1] - pts[k]) * (i - k))

    def draw_hand(self, c, q, key, tip, z, rot, breath, scale=HAND_S, stretch=1.0):
        v = self.h[key]
        # hands are never quite still, and this one is holding its breath
        bx = 1.8 * math.sin(q * 2.9 + 0.4) * breath
        by = 1.4 * math.sin(q * 2.1) * breath
        x, y = tip[0] + bx, tip[1] + by
        rot = rot + v["turn"]
        scale = scale * v["size"] * stretch
        # the shadow: one shape, all falling the same way. The higher it is the further it falls, and the further back
        # from the tip, the higher the hand is off the paper, so the further that part falls too
        lx, ly = LIGHT
        c.save()
        c.translate(x + lx * z, y + ly * z)
        c.rotate(rot)
        c.concat(skia.Matrix.MakeAll(1 + lx * 0.05, 0, 0, ly * 0.05, 1, 0, 0, 0, 1))
        c.scale(scale, scale)
        c.translate(-v["tip"][0], -v["tip"][1])
        p = skia.Paint(AntiAlias=True, ColorFilter=skia.ColorFilters.Blend(E.col(SHADE, 0.42), skia.BlendMode.kSrcIn))
        c.drawImage(v["img"], 0, 0, E.SAMPLING_DOWN, p)
        c.restore()
        c.save()
        c.translate(x, y)
        c.rotate(rot)
        c.scale(scale, scale)
        c.translate(-v["tip"][0], -v["tip"][1])
        c.drawImage(v["img"], 0, 0, E.SAMPLING_DOWN)
        c.restore()

    # ---- the note, and the hand that puts it down ----
    def note_place(self, t):
        """Where the note is, and her left hand on it: slid in on twelves, pressed, and the hand lifted off."""
        q = math.floor(t * 12) / 12
        u = E.ease_out(E.seg(q, *NOTE_IN), 2.2)
        cx = NOTE_C[0] - 620 * (1 - u)
        cy = NOTE_C[1] + 500 * (1 - u)
        return cx, cy, q

    def draw_note(self, c, t):
        if t < NOTE_IN[0]:
            return
        cx, cy, q = self.note_place(t)
        # its shadow: thin, it lies flat
        c.save()
        c.translate(cx + 5, cy + 6)
        c.rotate(NOTE_ROT)
        E.rect(c, -NOTE_W / 2, -NOTE_H / 2, NOTE_W, NOTE_H, SHADE, 0.30)
        c.restore()
        c.save()
        c.translate(cx, cy)
        c.rotate(NOTE_ROT)
        c.drawImageRect(self.note, skia.Rect.MakeXYWH(-NOTE_W / 2, -NOTE_H / 2, NOTE_W, NOTE_H), E.SAMPLING_DOWN)
        c.restore()
        if t >= NOTE_LIFT[1]:
            return
        # two fingertips on the note's lower left
        fx, fy = cx - 150, cy + 66
        if t < NOTE_LIFT[0]:
            v, z, dx, dy = self.left["press"], 12.0, 0.0, 0.0
        else:
            w = E.ease_in(E.seg(q, *NOTE_LIFT), 1.8)
            v, z, dx, dy = self.left["away"], 12.0 + 120.0 * w, -760.0 * w, 620.0 * w
        lx, ly = LIGHT
        s_ = LEFT_S
        for img, ox, oy, paint in ((v["img"], lx * z, ly * z, skia.Paint(AntiAlias=True, ColorFilter=skia.ColorFilters.Blend(E.col(SHADE, 0.42), skia.BlendMode.kSrcIn))), (v["img"], 0, 0, None)):
            c.save()
            c.translate(fx + dx + ox, fy + dy + oy)
            c.scale(s_, s_)
            c.translate(-v["tip"][0], -v["tip"][1])
            c.drawImage(img, 0, 0, E.SAMPLING_DOWN, paint)
            c.restore()

    def ink_line(self, c, pts, u, width=6.0):
        """What the ballpoint has laid down so far."""
        if u <= 0:
            return
        n = len(pts)
        path = skia.Path()
        i_end = u * (n - 1)
        path.moveTo(*pts[0])
        for i in range(1, int(i_end) + 1):
            path.lineTo(*pts[i])
        path.lineTo(*self.at(pts, u))
        c.drawPath(path, skia.Paint(AntiAlias=True, Color4f=E.col(E.INK), Style=skia.Paint.kStroke_Style, StrokeWidth=width,
                                    StrokeCap=skia.Paint.kRound_Cap, StrokeJoin=skia.Paint.kRound_Join))

    def strokes_done(self, q):
        out = []
        for name in ("stroke1", "stroke2"):
            t0, t1 = [(x[0], x[1]) for x in self.script if x[2] == name][0]
            out.append(E.ease_io(E.seg(q, t0, t1), 1.3))
        return out

    def draw(self, c, t):
        if t >= T1:
            c.clear(E.col("#000000"))
            return
        s_, fx, fy = self.camera(t)
        c.clear(E.col(E.PAPER))
        c.save()
        c.translate(960, 540)
        c.scale(s_, s_)
        c.translate(-fx, -fy)
        if s_ > 1.25:
            c.save()
            c.scale(1 / 3, 1 / 3)
            c.drawImage(self.form_big, 0, 0, E.SAMPLING_DOWN)
            c.restore()
        else:
            c.drawImage(self.form, 0, 0, E.SAMPLING)
        q = math.floor(t * 15 + 1e-6) / 15
        d1, d2 = self.strokes_done(q)
        self.ink_line(c, self.line1, d1)
        self.ink_line(c, self.line2, d2)
        self.draw_note(c, t)
        if t > self.strokes[0]["t0"]:
            bx, by, bw, bh = INK_BOX
            c.drawImageRect(self.ink_image(math.floor(t * 30 + 1e-6) / 30), skia.Rect.MakeXYWH(bx, by, bw, bh), E.SAMPLING_DOWN)
        if q >= self.script[0][0]:
            key, tip, z, rot, breath, _, stretch = self.state(t)
            self.draw_hand(c, q, key, tip, z, rot, breath, stretch=stretch)
        c.restore()

    def blur(self, t):
        return 8 if READ[1][0] <= t <= READ[-1][0] else 1
