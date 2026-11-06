"""早い: the attention chart is the horizon. She runs down it, headlines overtake her, a new peak rises at her feet.

The run is a real cycle of drawings on the music, eight drawings to two strides: on the beat a foot lands, then the middle of the
stride, the push-off, and the flight. She stays with the camera and the ground runs under her at the speed her legs take it, so she
runs and does not hop: the drawings' own feet are as far apart as the ground travels. Head height is one smooth line through all of them.
The camera eases from framing to framing. Everything she wears is the same in every drawing."""
import datetime
import json
import math
import sys
from pathlib import Path

import cv2
import numpy as np
import skia

sys.path.insert(0, str(Path(__file__).parent))
import common as K  # noqa: E402
import engine as E  # noqa: E402
from timeline import bar_time, beat_index  # noqa: E402

ROOT = K.ROOT
T0, T1 = 3989 / 30, 4435 / 30
# bar lines: 135.110, 136.956, 138.802
CUT_G2, CUT_G3, CUT_G4 = bar_time(73), bar_time(74), bar_time(75)
BEAT = (CUT_G3 - CUT_G2) / 4
FIRST_BEAT = bar_time(72)    # 133.264: the first footfall
HITS = (K.syllable_times(39, "ha") + K.syllable_times(40, "ha") + K.syllable_times(41, "ha"))[:14]
OI = K.syllable_times(41, "o")[0]        # 追 of 追いつけないよ: she stands
RISE = [OI] + K.syllable_times(41, "i")[-1:] + K.syllable_times(41, "tsu") + K.syllable_times(41, "ke") + K.syllable_times(41, "nai")
KENGAI = K.syllable_times(41, "nai")[0]
TRAIN_LEN = 0.30                          # seconds a train takes to cross
SWAP = 0.15                               # the cut behind the train, when it is covering the most
TRAIN_SHUTTER = 0.04                      # a shutter this short keeps a headline readable

SKY = E.CYAN
GROUND = E.PAPER
GROUND_SHADE = "#10506F"                  # the sheet in the new peak's shadow: one flat colour, hard edged
GRID_SKY = "#5AD6FC"
GRID_GROUND = "#C8E6EE"
GRID_SHADE = "#1C6583"
LABEL = "#6FAFC2"

# every train: the headline the eye catches, and what is coupled before and after it
TRAINS = [
    ("少女B", "急上昇", "新証言", "ShipporiMinchoB1-ExtraBold", E.INK, E.PAPER),
    ("少女C", "話題沸騰", "独占", "ShipporiMinchoB1-ExtraBold", E.PAPER, E.INK),
    ("新しい炎上", "速報", "拡散中", "ZenKakuGothicNew-Black", E.INK, E.PAPER),
    ("別の話題", "今週の", "トレンド", "ZenKakuGothicNew-Black", E.PAPER, E.INK),
    ("少女B", "続報", "本人談", "ShipporiMinchoB1-ExtraBold", E.INK, E.PAPER),
    ("次の標的", "特集", "徹底追跡", "ZenKakuGothicNew-Black", E.PAPER, E.INK),
    ("少女D", "新事実", "急浮上", "ShipporiMinchoB1-ExtraBold", E.INK, E.PAPER),
    ("人気俳優が結婚", "速報", "祝福", "ZenKakuGothicNew-Black", E.PAPER, E.INK),
    ("猫の動画", "癒やし", "百万再生", "ZenKakuGothicNew-Black", E.INK, E.PAPER),
    ("今夜の炎上", "拡散中", "謝罪", "ShipporiMinchoB1-ExtraBold", E.PAPER, E.INK),
    ("少女E", "新証言", "独占", "ShipporiMinchoB1-ExtraBold", E.INK, E.PAPER),
    ("誰かの失言", "速報", "物議", "ZenKakuGothicNew-Black", E.PAPER, E.INK),
    ("新商品", "行列", "完売", "ZenKakuGothicNew-Black", E.INK, E.PAPER),
    ("次の話題", "次", "次へ", "ShipporiMinchoB1-ExtraBold", E.PAPER, E.INK),
]
LINES = [(38, "ああ遠い夢を追いかけてさ", T0, 140.36), (39, "早い早い早い早い早い", 140.36, 142.21),
         (40, "早い早い早い早い早い", 142.21, 144.05), (41, "早い早い早い早い追いつけないよ", 144.05, T1 + 1)]

SUN = 0.44     # slope of the hard shadow's edge, falling to the lower left: the sun is high on the right

# the cycles: a foot lands, mid stride, push-off, flight; then the same on the other foot
STRONG = ["g61_run", "g11_run", "g62_run", "g12_run", "g63_run", "g13_run", "g64_run", "g14_run"]
WILD = ["g71_run", "g51_run", "g72_run", "g52_run", "g73_run", "g53_run", "g74_run", "g54_run"]   # flat out: arms pumping, not held out like wings
TIRED = ["g35_run", "g31_run", "g36_run", "g32_run", "g37_run", "g33_run", "g38_run", "g34_run"]
TIRED4 = ["g31_run", "g32_run", "g33_run", "g34_run"]      # seen one at a time between the trains
# the stumble, in beats from the bar line: the toe catches, she pitches forward, the front foot slams down on the third beat, she gets up
TRIPS = [("g21_trip", 0.0), ("g25_trip", 0.72), ("g22_trip", 1.08), ("g26_trip", 1.44), ("g23_trip", 2.0), ("g29_trip", 2.20), ("g29b_trip", 2.36), ("g30_trip", 2.52), ("g27_trip", 2.72), ("g24_trip", 3.22), ("g28_trip", 3.72)]
# how far the stumble carries her body forward of where the camera is, in screen pixels, by drawing
TRIP_LURCH = {"g21_trip": 0, "g25_trip": 50, "g22_trip": 110, "g26_trip": 150, "g23_trip": 150, "g29_trip": 138, "g29b_trip": 125, "g30_trip": 112, "g27_trip": 100, "g24_trip": 50, "g28_trip": 15}
STAND = "g41_stand"
# (time, size, screen x of her head, screen y of the camera's height on the fall, tilt): the camera moves between these, and never jumps
VIEWS = ((T0, 0.66, 900.0, 862.0, 0.0), (CUT_G2, 0.76, 1040.0, 930.0, 0.0), (CUT_G3, 0.70, 1020.0, 836.0, 4.0), (CUT_G4, 0.60, 920.0, 846.0, 0.0))
VIEW_EASE = (-0.20, 0.42)      # each move starts this long before the bar line and ends this long after it
HEAD = 155.0   # the length of her bar in the running drawings: every drawing is scaled to it
# the numbers, the same as in sections 06 and 09
COUNT_TOP = 12040000
COUNT_END = 35000     # where she stops: the very bottom of the top hundred
FIRST_DAY = datetime.date(2026, 11, 21)   # the day after the date on the weeklies: this is the summit

# On a slope a long stride throws the back foot far up the hill, and standing on it would lift her a head's height every step, which reads as hopping.
# So she leans with the fall of the chart, the whole drawing turned about her head, as far as this share of the slope and no further than this many degrees
LEAN_SLOPE, LEAN_MAX = 0.75, 15.0
RUN_SPEED = (1340, 1640, 420)   # first run, flat out, worn out: measured from the feet in the drawings
TRIP = [1e9, 1e9]     # where in the world she stumbles: the chart ticks back up there and catches her toe


def base(x):
    """The long fall of her attention, without its day-to-day zigzag. x in world units, y downwards. Always falling."""
    x = np.asarray(x, np.float64)
    fall = 0.30 * x + 230 * np.sin(x / 1700.0) + 70 * np.sin(x / 690.0 + 1.0) - 70 * np.sin(1.0)
    fall = fall - 0.42 * np.clip(x - TRIP[0], 0, TRIP[1] - TRIP[0])
    climb = -x * 0.74     # the way up to the summit, left of x = 0
    return np.where(x >= 0, fall, climb)


class Step:
    """One drawing on screen."""
    __slots__ = ("t0", "t1", "pose", "kind", "S", "X", "FY", "tilt", "z", "wx", "top", "rank", "off0", "off1", "y0", "y1", "lift", "hop", "ride", "run")

    def __init__(self, t0, pose, kind, S, X, FY, tilt=0.0, z=None, hop=0.0):
        self.t0, self.pose, self.kind, self.S, self.X, self.FY, self.tilt, self.z, self.hop = t0, pose, kind, S, X, FY, tilt, z, hop
        self.t1 = None
        self.wx = self.top = self.rank = None
        self.off0 = self.off1 = self.y0 = self.y1 = self.lift = 0.0
        self.ride = None      # behind the trains: how far (world) her foot may go with the ground before she stays with the camera
        self.run = False      # in the open: she stays with the camera, her height comes from the smooth line in self.run_y


class Fast(E.Clip):
    name = "s08"
    t0, t1 = T0, T1
    shutter = 0.12

    def setup(self):
        spec = json.loads((ROOT / "assets" / "gen" / "bars.json").read_text(encoding="utf-8"))
        self.poses = {}
        for n in dict.fromkeys(STRONG + WILD + [q[0] for q in TRIPS] + TIRED + TIRED4 + [STAND]):
            bgra = cv2.imread(str(ROOT / "assets" / "gen" / "final" / f"{n}.png"), cv2.IMREAD_UNCHANGED)
            # a speck of the green the picture was generated on, shut in between hair and scarf
            b_, g_, r_ = [bgra[..., i].astype(np.int32) for i in range(3)]
            bgra[(g_ > r_ + 40) & (g_ > b_ + 40), 3] = 0
            img = E.np_to_image(bgra[..., [2, 1, 0, 3]])
            a = bgra[..., 3] > 128
            h, w = a.shape
            # the lowest painted row of every few columns: nothing she wears may go through the line
            cols = np.arange(0, w, 6)
            low = np.array([np.nonzero(a[:, x])[0].max() if a[:, x].any() else -1 for x in cols], np.float64)
            keep = low >= 0
            # the same figure in the shadow of the peak: one flat step down in blue, no gradient
            dark = None
            if n == STAND:
                dark = bgra.copy()
                dark[..., :3] = (dark[..., :3].astype(np.float32) * np.array([0.60, 0.46, 0.34], np.float32)).astype(np.uint8)
                dark = E.np_to_image(dark[..., [2, 1, 0, 3]])
            norm = 1.0 if n == STAND else HEAD / spec[n][2] * (1.05 if n == "g29b_trip" else 1.0)   # that drawing came out a little small: her head keeps its size from one to the next
            k = int(np.argmax(low[keep]))
            self.poses[n] = dict(img=img, dark=dark, cols=cols[keep], low=low[keep],
                                 w=w, h=h, norm=norm, head=float(spec[n][0]), heady=float(spec[n][1]), bottom=low[keep].max(), foot=float(cols[keep][k]),
                                 right=float(cols[keep].max()))

        self.steps = self.build_steps()
        self.cuts = tuple(s.t0 for s in self.steps[1:])
        self.step_t = np.array([s.t0 for s in self.steps])

        # world position over time: the ground travels while she is in the air and almost stops under a planted foot
        zs = sorted(s.z for s in self.steps if s.z is not None)
        zs = [HITS[0] - 0.16] + zs
        dt = 1 / 240
        ts = np.arange(T0 - 0.05, T1 + 0.05, dt)
        v = np.zeros_like(ts)
        for i, t in enumerate(ts):
            if t < HITS[0]:
                # in the open the ground runs at one speed: a body in a run hardly changes speed, and the drawings' feet are spaced for it
                v[i] = self.mean_speed(t) / self.view_at(t, None)[0]
                continue
            if t >= zs[-1]:
                continue
            k = int(np.searchsorted(zs, t, side="right") - 1)
            gait = 1 - math.cos(math.tau * (t - zs[k]) / (zs[k + 1] - zs[k]))
            if t >= HITS[0]:
                gait = gait * gait / 1.5    # all of it behind the train; she is seen in the still moment
            st_ = self.step_at(t)
            v[i] = self.mean_speed(t) / self.view_at(t, st_)[0] * gait
        self.wt = ts
        self.wx = 560 + np.cumsum(v) * dt - v[0] * dt
        self.xend = float(np.interp(OI, ts, self.wx))
        TRIP[0] = float(np.interp(CUT_G3, ts, self.wx)) - 300
        TRIP[1] = float(np.interp(CUT_G4, ts, self.wx)) + 300

        # the chart itself: irregular, and no segment is ever level
        rng = np.random.default_rng(1404)
        xs = [0.0]
        x = 0.0
        while x < self.wx[-1] + 26000:
            x += float(rng.uniform(230, 560))
            xs.append(x)
        x = 0.0
        left = []
        while x > -9000:
            x -= float(rng.uniform(260, 640))
            left.append(x)
        xs = np.array(sorted(left) + xs, np.float64)
        sign = 1
        ys = base(xs).copy()
        for i in range(len(xs)):
            if xs[i] == 0:
                ys[i] = -30    # the summit
                continue
            sign = -sign
            # a foot lands on this line: it stays a jagged chart, but not one she would have to climb every step
            calm = 0.35 if TRIP[0] < xs[i] < TRIP[1] else (0.62 if xs[i] > 0 else 1.2)
            ys[i] += sign * float(rng.uniform(26, 92)) * calm
        for i in range(1, len(xs)):
            dx = xs[i] - xs[i - 1]
            if abs(ys[i] - ys[i - 1]) / dx < 0.09:
                ys[i] = ys[i - 1] + 0.11 * dx
        # where she stops the slope is gentle under her shoes, gentle but never level
        keep = (xs < self.xend - 240) | (xs > self.xend + 240)
        y_a = float(np.interp(self.xend - 240, xs, ys))
        y_b = max(float(np.interp(self.xend + 240, xs, ys)), y_a + 60)
        ins = np.searchsorted(xs[keep], self.xend - 240)
        xs, ys = np.insert(xs[keep], ins, [self.xend - 240, self.xend + 240]), np.insert(ys[keep], ins, [y_a, y_b])
        # and nothing after it sits higher than that, so there is no step at her toes
        after = xs > self.xend + 240
        ys[after] = np.maximum(ys[after], y_b + 0.11 * (xs[after] - (self.xend + 240)))
        self.lx, self.ly = xs, ys
        self.ymax = float(np.interp(self.xend, xs, ys))
        self.place_steps()

        # the new peak, in fractions of its width and height, from her toes rightwards
        self.peak = [(0.00, 0.00), (0.05, 0.075), (0.10, 0.045), (0.17, 0.19), (0.23, 0.15), (0.32, 0.36), (0.37, 0.31),
                     (0.47, 0.55), (0.52, 0.51), (0.66, 0.80), (0.70, 0.77), (0.82, 1.00), (0.94, 0.84), (0.98, 0.87),
                     (1.10, 0.63), (1.16, 0.70), (1.34, 0.48), (1.6, 0.40)]
        self.b_name = E.fit("少女B", "ShipporiMinchoB1-ExtraBold", 170, 470, vertical=True, max_size=220)
        self.b_rank = E.Type("1位", "ZenKakuGothicNew-Black", 66)
        self.b_count = E.Type("1,480万件", "ZenKakuGothicNew-Bold", 40)      # the same number as the top of the list a moment later

        # rank plate
        self.pl_head = E.Type("話題ランキング", "ZenKakuGothicNew-Bold", 26, tracking=2)
        self.pl_name = E.Type("少女A", "ShipporiMinchoB1-ExtraBold", 40)
        self.pl_i = E.Type("位", "ShipporiMinchoB1-ExtraBold", 54)
        self.pl_big = {str(r): E.Type(str(r), "ShipporiMinchoB1-ExtraBold", 112) for r in range(1, 101)}
        self.pl_out = E.Type("圏外", "ShipporiMinchoB1-ExtraBold", 112)

        self.tag = E.Type("少女A", "ShipporiMinchoB1-ExtraBold", 54)
        self.tag2 = E.Type("最高 1,204万件", "ZenKakuGothicNew-Bold", 28)
        self.grid_lab = {}
        self.day_lab = {}

        self.strips = [(a, b, K.Strip(tx, K.chars_of(i, tx), size=46)) for i, tx, a, b in LINES]

        # trains
        self.trains = []
        rng = np.random.default_rng(88)
        for i, (hl, front, back, font, bg, fg) in enumerate(TRAINS):
            h = float(rng.uniform(640, 730))
            y = 860 - h + float(rng.uniform(40, 80))
            key_w = 1560 - i * 26
            side_w = 1040 - i * 26
            main = E.fit(hl, font, key_w - 150, h * 0.64, max_size=560)
            cars = [(side_w, fg, bg, E.fit(back, font, side_w - 190, h * 0.40, max_size=260), None),
                    (key_w, bg, fg, main, E.fit(f"{(i % 3) + 1}位　{hl}　トレンド入り", "ZenKakuGothicNew-Bold", key_w - 200, 40, max_size=34)),
                    (side_w, fg, bg, E.fit(front, font, side_w - 190, h * 0.40, max_size=260), None)]
            self.trains.append(dict(y=y, h=h, cars=cars, alert=("速報" in (front, back))))
        self.alert = E.Type("速報", "ZenKakuGothicNew-Black", 44)
        self._ft = None
        self._train_img = None

    # ---- the drawings, on the music ----
    def build_steps(self):
        s = []

        def cycle(names, t_from, t_to, q, hop):
            """Four drawings to a stride, each q long; the foot lands on the first of them."""
            n = 0
            t = t_from
            while t < t_to - 1e-6:
                st = Step(t, names[n % 8], "f" if n % 4 == 3 else "c", 0.0, 0.0, 0.0, hop=hop if n % 4 == 3 else 0.0)
                st.run = True
                s.append(st)
                n += 1
                t += q

        # she leaves the summit in mid air
        s.append(Step(T0, STRONG[7], "f", 0.0, 0.0, 0.0, hop=60))
        s[-1].run = True
        cycle(STRONG, FIRST_BEAT, CUT_G2, BEAT / 4, 46)
        cycle(WILD, CUT_G2, CUT_G3, BEAT / 4, 56)
        # the toe catches: falling, catching herself, getting up
        for nm, b in TRIPS:
            st = Step(CUT_G3 + b * BEAT, nm, "c", 0.0, 0.0, 0.0)
            st.run = True
            s.append(st)
        # worn out: heavy steps, a foot down every two beats
        swaps = [h + SWAP for h in HITS]
        cycle(TIRED, CUT_G4, swaps[0], BEAT / 2, 10)
        # the trains: a drawing behind each one, smaller each time. The ground rushes behind the train and nearly
        # stands still in the moment she can be seen
        sc = 0.60
        for i, sw in enumerate(swaps):
            sc *= 0.885
            nm = TIRED4[(i + 1) % 4]
            s.append(Step(sw, nm, "c" if (i + 1) % 2 == 0 else "f", sc, E.lerp(920, 700, i / 13), E.lerp(850, 862, i / 13),
                          z=HITS[i] + 0.32, hop=30))
            s[-1].ride = 60.0 / sc
        s.append(Step(HITS[-1] + 0.32 + 0.02, TIRED4[3], "f", sc, 700, 862, hop=30))
        s[-1].ride = 0.0
        s.append(Step(OI, STAND, "c", 0.15, 660, 850, z=OI))
        for a, b in zip(s, s[1:]):
            a.t1 = b.t0
        s[-1].t1 = T1 + 1
        return s

    def view_at(self, t, st):
        """Size, screen x, screen y and tilt of the view. In the open it eases from one framing to the next; behind the trains it is the step's own."""
        if st is not None and not st.run:
            return st.S, st.X, st.FY, st.tilt
        v = VIEWS[0][1:]
        for a, b in zip(VIEWS, VIEWS[1:]):
            u = E.ease_io(E.seg(t, b[0] + VIEW_EASE[0], b[0] + VIEW_EASE[1]), 2.0)
            if u <= 0:
                break
            v = tuple(E.lerp(x, y, u) for x, y in zip(a[1:], b[1:]))
        return v

    def mean_speed(self, t):
        """Screen pixels a second. The ground goes as fast as the drawings' feet are apart, so they do not skate."""
        if t < FIRST_BEAT:
            return 760     # the long あ: she only just sets off
        if t < 133.9:
            return E.lerp(760, RUN_SPEED[0], E.ease_io(E.seg(t, FIRST_BEAT, 133.9), 2))
        if t < CUT_G2 - 0.2:
            return RUN_SPEED[0]
        if t < CUT_G3 - 0.2:
            return E.lerp(RUN_SPEED[0], RUN_SPEED[1], E.seg(t, CUT_G2 - 0.2, CUT_G2 + 0.4))
        if t < CUT_G4:
            return E.lerp(RUN_SPEED[1], 90, E.ease_out(E.seg(t, CUT_G3 - 0.2, CUT_G3 + 0.9), 2))    # the toe has caught: the ground all but stops
        if t < HITS[0]:
            return E.lerp(90, RUN_SPEED[2], E.seg(t, CUT_G4, CUT_G4 + 0.5))
        if t < OI:
            return E.lerp(1350, 1900, E.seg(t, HITS[0], OI))
        return 0.0

    def step_at(self, t):
        i = int(np.searchsorted(self.step_t, t, side="right") - 1) if hasattr(self, "step_t") else None
        if i is None:
            for st in reversed(self.steps):
                if t >= st.t0:
                    return st
            return self.steps[0]
        return self.steps[max(i, 0)]

    def wx_at(self, t):
        return float(np.interp(min(t, OI), self.wt, self.wx))

    def top_w(self, pose, her_x):
        """The highest the top of the picture can be (world y) with nothing she wears going through the line."""
        n = pose["norm"]
        col_w = her_x + (pose["cols"] - pose["head"]) * n
        return float(np.min(self.line_y(col_w) - pose["low"] * n))

    def foot_y(self, pose, her_x):
        """World y of the line under the foot that lands."""
        return float(self.line_y(her_x + (pose["foot"] - pose["head"]) * pose["norm"]))

    def place_steps(self):
        """Every planted foot keeps its one spot on the line; flights arc from where one foot was to where the next lands."""
        steps = self.steps
        for st in steps:
            if st.run:
                st.wx = self.wx_at(st.t0)
                continue
            if st.z is None and st.ride is not None:
                continue
            if st.z is not None:
                st.wx = self.wx_at(st.z)
                st.top = self.top_w(self.poses[st.pose], st.wx)
        anchored = [s for s in steps if s.z is not None]
        for st in steps:
            if st.run or (st.z is None and st.ride is not None):
                continue
            if st.z is not None:
                if st.kind == "f":
                    st.top -= st.hop      # seen for a moment only, a little off the ground
                continue
            prev = next((s for s in reversed(anchored) if s.t0 < st.t0), None)
            nxt = next((s for s in anchored if s.t0 > st.t0), None)
            pose = self.poses[st.pose]
            st.off0 = (prev.wx - self.wx_at(st.t0)) if prev else 0.0
            st.off1 = (nxt.wx - self.wx_at(st.t1)) if nxt else 0.0

            def clear(u):
                return self.top_w(pose, self.wx_at(E.lerp(st.t0, st.t1, u)) + E.lerp(st.off0, st.off1, u))

            # from just off the line here to just off the line there; whatever the zigzag does between, she goes over it
            st.y0, st.y1 = clear(0.0), clear(1.0)
            st.lift = 0.0
            for u in np.linspace(0.1, 0.9, 9):
                u = float(u)
                st.lift = max(st.lift, (self.flight_top(st, u) - clear(u)) / math.sin(math.pi * u))
        self.make_run_height()
        # the plate: the number she is on, read off the axis at each footfall, never going back up
        best = 1
        for st in steps:
            x = st.wx if st.wx is not None else self.wx_at(st.t0)
            r = K.trend_rank(self.count_at(float(self.line_y(x))))
            # she keeps the top for her first strides off the summit
            best = max(best, min(r, 99)) if st.t0 > FIRST_BEAT + 1.5 * BEAT else 1
            st.rank = best

    def run_x(self, st, t):
        """World x of her head in the open: with the camera, and in the stumble thrown forward of it."""
        x = self.wx_at(t)
        if st.pose in TRIP_LURCH:
            x += TRIP_LURCH[st.pose] / self.view_at(t, st)[0]
        return x

    def head_req(self, pose, x, lean):
        """World y of her head with whatever she wears just standing on the chart, the drawing turned by lean degrees about the head."""
        n = pose["norm"]
        a = math.radians(lean)
        rx, ry = (pose["cols"] - pose["head"]) * n, (pose["low"] - pose["heady"]) * n
        xr = x + rx * math.cos(a) - ry * math.sin(a)
        yr = rx * math.sin(a) + ry * math.cos(a)
        return float(np.min(self.line_y(xr) - yr))

    def lean_at(self, st, t):
        return float(np.interp(t, self.run_t, self.run_lean)) if st.run else 0.0

    def make_run_height(self):
        """World y of her head at every moment of the run, as one smooth line: whatever each drawing's foot needs in order to stand on the chart, plus the flight, without the jolts."""
        ts = np.arange(T0, HITS[0] + SWAP + 0.3, 1 / 120)
        ys = np.empty(len(ts))
        # the lean follows the long fall, not the zigzag
        wxs = np.array([self.wx_at(t) for t in ts])
        slope = (base(wxs + 500.0) - base(wxs - 500.0)) / 1000.0
        self.run_lean = np.minimum(np.degrees(np.arctan(np.maximum(slope, 0.0) * LEAN_SLOPE)), LEAN_MAX)
        for i, t in enumerate(ts):
            st = self.step_at(t)
            if not st.run:
                ys[i] = ys[i - 1]
                continue
            ys[i] = self.head_req(self.poses[st.pose], self.run_x(st, t), self.run_lean[i]) - st.hop
        sig = 0.045 * 120
        r = int(sig * 3)
        ker = np.exp(-0.5 * (np.arange(-r, r + 1) / sig) ** 2)
        ker /= ker.sum()
        pad = np.r_[np.full(r, ys[0]), ys, np.full(r, ys[-1])]
        self.run_t, self.run_y = ts, np.convolve(pad, ker, "valid")

    def flight_top(self, st, u):
        return E.lerp(st.y0, st.y1, u) - st.hop * (0.35 + 2.6 * u * (1 - u)) - st.lift * math.sin(math.pi * u)

    def her_place(self, st, t):
        """Where the drawing is at time t: world x of her head, world y of the picture's top."""
        pose = self.poses[st.pose]
        if st.run:
            x = self.run_x(st, t)
            head = float(np.interp(t, self.run_t, self.run_y))
            # the smooth line may not push anything she wears through the chart
            head = min(head, self.head_req(pose, x, self.lean_at(st, t)) + 6.0)
            return x, head - pose["heady"] * pose["norm"]
        if st.ride is not None:
            wx = self.wx_at(t)
            off = (st.wx - wx) if st.wx is not None else 0.0
            if st.wx is not None and abs(off) <= st.ride:
                return st.wx, st.top
            # the ground is rushing, behind the train: she stays with the camera, on the line
            x = wx + float(np.clip(off, -st.ride, st.ride))
            return x, self.top_w(pose, x) - (st.hop if st.kind == "f" else 0.0)
        if st.z is not None:
            return st.wx, st.top
        u = E.seg(t, st.t0, st.t1)
        x = self.wx_at(t) + E.lerp(st.off0, st.off1, u)
        return x, min(self.flight_top(st, u), self.top_w(pose, x) - 3.0)

    # ---- numbers ----
    def count_at(self, y):
        """The axis runs on a log-like scale from her peak to the bottom of the top hundred, so its numbers agree with the list."""
        k = max(y + 30.0, 0.0) / max(self.ymax + 30.0, 1.0)
        return COUNT_TOP * (COUNT_END / COUNT_TOP) ** (k ** 0.85)

    def line_y(self, x):
        return np.interp(x, self.lx, self.ly)

    def cam(self, wx):
        """The camera rides the fall itself, a little behind her middle: where her trailing foot is, not the zigzag."""
        return float(base(wx - 350))

    # ---- chart ----
    def draw_world(self, c, t, S, X, FY, wx, cam_y, x0, x1):
        sx = lambda wxx: X + (wxx - wx) * S
        sy = lambda wyy: FY + (wyy - cam_y) * S
        i0 = max(np.searchsorted(self.lx, x0) - 1, 0)
        i1 = min(np.searchsorted(self.lx, x1) + 1, len(self.lx) - 1)
        line = skia.Path()
        line.moveTo(sx(self.lx[i0]), sy(self.ly[i0]))
        for i in range(i0 + 1, i1 + 1):
            line.lineTo(sx(self.lx[i]), sy(self.ly[i]))
        ground = skia.Path(line)
        ground.lineTo(sx(self.lx[i1]), 6000)
        ground.lineTo(sx(self.lx[i0]), 6000)
        ground.close()
        self._ground = ground

        c.clear(E.col(SKY))
        # the grid carries on through the sky: all of this is printed on one sheet
        step_u = 1000.0
        if S < 0.30:
            step_u = 2000.0
        k0, k1 = int(x0 // step_u), int(x1 // step_u) + 1
        for k in range(k0, k1 + 1):
            xp = sx(k * step_u)
            E.rect(c, xp - 1.5, -300, 3, 2400, GRID_SKY)
        g_step = 1000.0 if S >= 0.3 else 2000.0
        vy0, vy1 = cam_y - (FY + 500) / S, cam_y + (1600 - FY) / S
        for k in range(int(vy0 // g_step), int(vy1 // g_step) + 1):
            E.rect(c, -600, sy(k * g_step) - 1.5, 3200, 3, GRID_SKY)

        c.drawPath(ground, skia.Paint(AntiAlias=True, Color4f=E.col(GROUND)))
        c.save()
        c.clipPath(ground, True)
        self.ground_grid(c, sx, sy, (k0, k1, step_u, vy0, vy1, g_step), GRID_GROUND)
        c.restore()
        return line, sx, sy, (k0, k1, step_u, vy0, vy1, g_step)

    def ground_grid(self, c, sx, sy, grid, color):
        k0, k1, step_u, vy0, vy1, g_step = grid
        for k in range(k0, k1 + 1):
            E.rect(c, sx(k * step_u) - 1.5, -300, 3, 2400, color)
        for k in range(int(vy0 // g_step), int(vy1 // g_step) + 1):
            E.rect(c, -600, sy(k * g_step) - 1.5, 3200, 3, color)

    def date_labels(self, c, grid, sx, color):
        """The date along the foot of the chart: a real calendar, the day after the date on the weeklies at the summit."""
        k0, k1, step_u, *_ = grid
        c.save()
        c.clipPath(self._ground, True)
        for k in range(k0, k1 + 1):
            d = FIRST_DAY + datetime.timedelta(days=k * int(step_u / 1000))
            s = f"{d.month}月{d.day}日"
            if s not in self.day_lab:
                self.day_lab[s] = E.Type(s, "ZenKakuGothicNew-Bold", 26)
            self.day_lab[s].draw(c, sx(k * step_u) + 10, 962, color, ax=0, ay=0.5)
        c.restore()

    def count_labels(self, c, grid, sy):
        """The count up the right-hand edge."""
        k0, k1, step_u, vy0, vy1, g_step = grid
        for k in range(int(vy0 // g_step), int(vy1 // g_step) + 1):
            wy = k * g_step
            if wy < -30:
                continue
            n = self.count_at(wy)
            v = n / 10000
            s = f"{round(v, -1):,.0f}万件" if v >= 100 else (f"{v:.0f}万件" if v >= 10 else f"{v:.1f}万件")
            if s not in self.grid_lab:
                self.grid_lab[s] = E.Type(s, "ZenKakuGothicNew-Bold", 26)
            self.grid_lab[s].draw(c, 1890, sy(wy) - 8, "#0A5C78", ax=1, ay=1)

    def draw_shadow(self, c, pose, s_img, hx, top, foot_x, ground_y, lean=0.0):
        """Her own hard shadow lies on the sheet, thrown down and to the left by the same high sun as the peak's."""
        c.save()
        c.clipPath(self._ground, True)
        # reflect about the ground, squash, shear to the left
        c.translate(foot_x, ground_y)
        c.concat(skia.Matrix.MakeAll(1, 0.62, 0, 0, -0.34, 0, 0, 0, 1))
        c.translate(-foot_x, -ground_y)
        p = skia.Paint(AntiAlias=True, ColorFilter=skia.ColorFilters.Blend(E.col("#A2BBC7"), skia.BlendMode.kSrcIn))
        c.translate(hx, top + pose["heady"] * s_img)
        c.rotate(lean)
        c.scale(s_img, s_img)
        c.translate(-pose["head"], -pose["heady"])
        c.drawImage(pose["img"], 0, 0, E.SAMPLING_DOWN, p)
        c.restore()

    def draw(self, c, t):
        st = self.step_at(t)
        S, X, FY, tilt = self.view_at(t, st)
        pose = self.poses[st.pose]
        s_img = S * pose["norm"]
        wx = self.wx_at(t)
        cam_y = self.cam(wx)
        x0 = wx - (X + 500) / S
        x1 = wx + (E.W - X + 500) / S

        c.save()
        if tilt:
            c.translate(X, FY)
            c.rotate(tilt)
            c.translate(-X, -FY)
        line, sx, sy, grid = self.draw_world(c, t, S, X, FY, wx, cam_y, x0, x1)
        self.date_labels(c, grid, sx, LABEL)
        # (not once the new peak stands: it is on another scale altogether, and carries its own number)
        if t < OI:
            self.count_labels(c, grid, sy)

        her_x, top_w = self.her_place(st, t)
        hx = sx(her_x)
        top = sy(top_w)
        lean = self.lean_at(st, t)
        a_ = math.radians(lean)
        fx_, fy_ = (pose["foot"] - pose["head"]) * s_img, (pose["bottom"] - pose["heady"]) * s_img
        foot_x = hx + fx_ * math.cos(a_) - fy_ * math.sin(a_)
        ground_y = sy(float(self.line_y(wx + (foot_x - X) / S)))

        wedge = self.wedge(t, X, FY, S) if t >= OI else None
        if wedge is not None:
            self.draw_peak_shadow(c, wedge, sx, sy, grid)
        # (inside the peak's shadow her own shadow has nothing left to darken)
        if wedge is not None:
            c.save()
            c.clipPath(wedge, skia.ClipOp.kDifference, True)
        self.draw_shadow(c, pose, s_img, hx, top, foot_x, ground_y, lean)
        if wedge is not None:
            c.restore()

        # the line: a thick ink line, thinner the further away we are
        lw = max(7.0, 15.0 * math.sqrt(S / 0.7))
        c.drawPath(line, skia.Paint(AntiAlias=True, Color4f=E.col(E.INK), Style=skia.Paint.kStroke_Style, StrokeWidth=lw,
                                    StrokeJoin=skia.Paint.kMiter_Join))
        # the data points on the line
        if S > 0.3:
            i0 = max(np.searchsorted(self.lx, x0) - 1, 0)
            i1 = min(np.searchsorted(self.lx, x1) + 1, len(self.lx) - 1)
            for i in range(i0, i1 + 1):
                if i % 3 == 0:
                    c.drawCircle(sx(self.lx[i]), sy(self.ly[i]), lw * 0.95, skia.Paint(AntiAlias=True, Color4f=E.col(E.INK)))
                    c.drawCircle(sx(self.lx[i]), sy(self.ly[i]), lw * 0.45, skia.Paint(AntiAlias=True, Color4f=E.col(E.PAPER)))
        # the summit she is leaving still has her name on it
        sumx, sumy = sx(0.0), sy(-30.0)
        if -600 < sumx < 2200:
            self.draw_tag(c, sumx, sumy, S)
        left = hx - pose["head"] * s_img
        c.save()
        c.translate(hx, top + pose["heady"] * s_img)
        c.rotate(lean)
        c.translate(-hx, -(top + pose["heady"] * s_img))
        E.draw_image(c, pose["img"], left, top, s_img, ax=0.0, ay=0.0)
        c.restore()
        if wedge is not None:
            # the edge of the shadow climbs up her, hard, as the peak rises
            c.save()
            c.clipPath(wedge, True)
            E.draw_image(c, pose["dark"], left, top, s_img, ax=0.0, ay=0.0)
            c.restore()
        c.restore()

        if t >= OI:
            self.draw_peak(c, t, X, FY, S)
        self.draw_trains(c, t)
        self.draw_plate(c, st, t)
        for a, b, strip in self.strips:
            if a <= t < b:
                strip.draw(c, 960, 1034, t, ax=0.5)

    def draw_tag(self, c, x, y, S):
        k = 1.0
        w, h = 300 * k, 136 * k
        bx, by = x - w - 30, y - h - 70
        E.rect(c, bx, by, w, h, E.INK)
        tri = skia.Path()
        tri.moveTo(bx + w - 70, by + h - 1)
        tri.lineTo(bx + w - 16, by + h - 1)
        tri.lineTo(x - 3, y - 6)
        tri.close()
        c.drawPath(tri, skia.Paint(AntiAlias=True, Color4f=E.col(E.INK)))
        self.tag.draw(c, bx + w / 2, by + 50, E.PAPER)
        self.tag2.draw(c, bx + w / 2, by + 104, E.RIN)

    # ---- the new peak ----
    def height_at(self, t):
        """Stage by stage, on the sung syllables."""
        stops = [0.13, 0.28, 0.52, 0.74, 1.0]
        h = 0.0
        for k, (tm, v) in enumerate(zip(RISE, stops)):
            if t >= tm:
                prev = stops[k - 1] if k else 0.0
                h = E.lerp(prev, v, E.ease_out(E.seg(t, tm, tm + 0.20), 3))
        return h

    def peak_geom(self, X, FY, S):
        pose = self.poses[STAND]
        toe = X + (pose["right"] - pose["head"]) * S * pose["norm"]   # just past her toes
        return toe + 12, 960.0, 1010.0

    def peak_path(self, t, X, FY, S, wx, cam_y):
        x0, w, hh = self.peak_geom(X, FY, S)
        hf = self.height_at(t)
        pts = []
        for u, v in self.peak:
            xp = x0 + u * w
            yb = FY + (self.line_y(wx + (xp - X) / S) - cam_y) * S
            pts.append((xp, yb - v * hf * hh))
        return pts

    def wedge(self, t, X, FY, S):
        wx = self.xend
        base_y = self.cam(wx)
        pts = self.peak_path(t, X, FY, S, wx, base_y)
        sx, sy = min(pts, key=lambda p: p[1])
        w = skia.Path()
        w.moveTo(sx, sy)
        w.lineTo(sx - 4000, sy + 4000 * SUN)
        w.lineTo(sx - 4000, 6000)
        w.lineTo(E.W + 300, 6000)
        w.lineTo(E.W + 300, FY + (float(self.line_y(wx + (E.W + 300 - X) / S)) - base_y) * S)
        w.lineTo(sx, FY + (float(self.line_y(wx + (sx - X) / S)) - base_y) * S)
        w.close()
        return w

    def draw_peak_shadow(self, c, wedge, sx, sy, grid):
        """The peak's shadow lies on the sheet and nowhere else: one flat opaque colour with a hard edge. Not on the sky."""
        c.save()
        c.clipPath(self._ground, True)
        c.clipPath(wedge, True)
        c.drawPaint(skia.Paint(Color4f=E.col(GROUND_SHADE)))
        self.ground_grid(c, sx, sy, grid, GRID_SHADE)
        c.restore()
        c.save()
        c.clipPath(wedge, True)
        self.date_labels(c, grid, sx, "#8FC4D6")
        c.restore()

    def draw_peak(self, c, t, X, FY, S):
        wx = self.xend
        cam_y = self.cam(wx)
        pts = self.peak_path(t, X, FY, S, wx, cam_y)
        mass = skia.Path()
        mass.moveTo(*pts[0])
        for p in pts[1:]:
            mass.lineTo(*p)
        # it stands on her line, which carries on falling underneath it
        for xp in np.arange(pts[-1][0], pts[0][0], -40.0):
            mass.lineTo(float(xp), FY + (float(self.line_y(wx + (xp - X) / S)) - cam_y) * S)
        mass.close()
        c.drawPath(mass, skia.Paint(AntiAlias=True, Color4f=E.col(E.INK)))
        # her name stays on the mass and rises with it
        sx, sy = min(pts, key=lambda p: p[1])
        c.save()
        c.clipPath(mass, True)
        self.b_name.draw(c, sx, sy + 215, E.PAPER, ax=0.5, ay=0.0)
        self.b_rank.draw(c, sx, sy + 215 + self.b_name.h + 34, E.PAPER, ax=0.5, ay=0.0)
        self.b_count.draw(c, sx, sy + 215 + self.b_name.h + 34 + 84, E.RIN, ax=0.5, ay=0.0)
        c.restore()

    # ---- trains ----
    def train_tail(self, i, t, total):
        u = (t - HITS[i]) / TRAIN_LEN
        # slow through the middle so the headline can be caught; less and less as they speed up
        a = E.lerp(0.16, 0.86, i / 13)
        v = a * u + (1 - a) * (0.5 + 4 * (u - 0.5) ** 3)
        # the tail starts off screen left, the nose finishes off screen right; centred at v = 0.5
        margin = 260
        return E.lerp(-total - margin, E.W + margin, v)

    def train_layer(self, i, t):
        """The train for this frame, once, with its real streak: it only ever moves sideways, so the streak is a soft
        sideways blur of its exact length, which never shows as counted copies of the type."""
        tr = self.trains[i]
        total = sum(car[0] + 14 for car in tr["cars"])
        tail = self.train_tail(i, t, total)
        surf = skia.Surface(E.W, E.H)
        c = surf.getCanvas()
        c.clear(skia.Color4f(0, 0, 0, 0))
        y, hh = tr["y"], tr["h"]
        c.translate(0, y + hh)
        c.skew(-0.16, 0)
        c.translate(0, -(y + hh))
        E.rect(c, tail, y + hh, total, 34, "#06222E")
        x = tail
        for w, bg, fg, ty, sub in tr["cars"]:
            E.rect(c, x, y, w, hh, bg)
            # a double rule top and bottom, like a printed masthead
            E.rect(c, x + 26, y + 26, w - 52, 8, fg)
            E.rect(c, x + 26, y + hh - 34, w - 52, 8, fg)
            E.rect(c, x + 26, y + 44, w - 52, 3, fg)
            E.rect(c, x + 26, y + hh - 47, w - 52, 3, fg)
            ty.draw(c, x + w / 2, y + hh * (0.46 if sub else 0.5), fg)
            if sub:
                sub.draw(c, x + w / 2, y + hh - 92, fg)
            # the coupling to the next car
            E.rect(c, x + w, y + hh * 0.46, 14, hh * 0.08, E.INK)
            x += w + 14
        if tr["alert"]:
            ax_, ay_ = tail + tr["cars"][0][0] + 40, y + 70
            E.rect(c, ax_, ay_, 140, 70, E.RED)
            self.alert.draw(c, ax_ + 70, ay_ + 35, E.PAPER)
        d = 1 / E.FPS * TRAIN_SHUTTER
        run = abs(self.train_tail(i, t + d / 2, total) - self.train_tail(i, t - d / 2, total))
        n = int(run + 1) | 1
        if n < 3:
            return surf.makeImageSnapshot()
        arr = surf.makeImageSnapshot().toarray(colorType=skia.ColorType.kRGBA_8888_ColorType, alphaType=skia.AlphaType.kPremul_AlphaType)
        kern = np.sin(np.pi * (np.arange(n) + 0.5) / n) ** 2
        kern = (kern / kern.sum()).reshape(1, -1)
        out = cv2.filter2D(arr, -1, kern, borderType=cv2.BORDER_CONSTANT)
        return skia.Image.fromarray(np.array(out, dtype=np.uint8, order="C"), colorType=skia.ColorType.kRGBA_8888_ColorType,
                                    alphaType=skia.AlphaType.kPremul_AlphaType)

    def draw_trains(self, c, t):
        ft = self._ft if self._ft is not None else t
        for i, h in enumerate(HITS):
            if not (h <= ft < h + TRAIN_LEN):
                continue
            if self._train_img is None or self._train_img[0] != ft:
                self._train_img = (ft, self.train_layer(i, ft))
            c.drawImage(self._train_img[1], 0, 0)

    # ---- rank ----
    def draw_plate(self, c, st, t):
        x, y, w, h = 56, 44, 470, 170
        E.rect(c, x, y, w, h, E.INK)
        self.pl_head.draw(c, x + 24, y + 28, E.PAPER, ax=0, ay=0.5)
        self.pl_name.draw(c, x + 24, y + 100, E.RIN, ax=0, ay=0.5)
        if t >= KENGAI:
            self.pl_out.draw(c, x + w - 24, y + 100, E.PAPER, ax=1, ay=0.5, scale=0.92)
        else:
            self.pl_i.draw(c, x + w - 24, y + 142, E.PAPER, ax=1, ay=1)
            self.pl_big[str(st.rank)].draw(c, x + w - 24 - self.pl_i.w - 10, y + 142, E.PAPER, ax=1, ay=1)

    def blur(self, t):
        if t >= OI:
            return 6 if t < RISE[-1] + 0.25 else 1
        return 20

    def frame_rgb(self, t):
        self._ft = t
        return K.soft_frame(self, t)
