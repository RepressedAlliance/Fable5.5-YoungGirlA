"""Clip 4 overlay: lyric track, and at the end the thin lines growing out of every bar."""
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
import shared_c4 as S  # noqa: E402

LINES = [(28, "契り集め持ってきた"), (29, "契り集め持ってきた"), (30, "あの日の間違いを"), (31, "飲み込むのが苦しくて"), (32, "朽ちるまでの愛憎を")]


class Rin14(E.Clip):
    name = "c4"
    t0, t1 = S.T0, S.T1

    def setup(self):
        self.strips = [(K.LYRICS[i]["start"], K.LYRICS[i]["end"], K.Strip(tx, K.chars_of(i, tx), size=46)) for i, tx in LINES]
        self.meta = S.meta()
        self.ids = json.loads((K.ROOT / "work" / "render" / "c4_ids.json").read_text())
        self.ends = {}
        for r, cell in zip(S.RUMOURS, S.ORDER):
            name = r[0]
            m = self.meta[name]
            cen = self.ids[name]["center"]
            fx, fy, fl, ft, ang = m["bar"]
            w, h = m["w_m"], m["h_m"]
            def world(u, v):
                return (cen[0] - w / 2 + u * w, cen[1], cen[2] + h / 2 - v * h)
            a = math.radians(ang)
            hw = fl * 0.47
            self.ends[cell] = (world(fx - hw * math.cos(a), fy - hw * math.sin(a) * (w / h)),
                               world(fx + hw * math.cos(a), fy + hw * math.sin(a) * (w / h)), ft * h)

    def frame_rgb(self, t):
        im = K.seq_frame("c4", t, self.t0)
        # the wall is a plane, so the camera's move across it is known exactly: three points on it give the sweep
        # a short shutter that opens and closes: these moves are so fast that a longer or a square one doubles every
        # outline and steps the type; the soft one streaks each edge into one band
        dt = 0.15 / E.FPS / 2
        pts = [(-1.5, 0, -1.0), (1.5, 0, -1.0), (0.0, 0, 1.0)]
        ex, _, ez = S.camera_at(t)[0]
        pts = [(p[0] + ex, p[1], p[2] + ez) for p in pts]
        now = np.float32([S.project(p, t)[:2] for p in pts])
        m0 = cv2.getAffineTransform(now, np.float32([S.project(p, t - dt)[:2] for p in pts]))
        m1 = cv2.getAffineTransform(now, np.float32([S.project(p, t + dt)[:2] for p in pts]))
        # the last six are hard cuts, every frame sharp; so is the frame either side of any other hard cut
        if not (S.KEY[8] - 0.03 <= t < S.PULL_START or any(abs(t - k) < 0.03 for k in S.HARD_CUTS)):
            im = K.affine_blur(im, m0, m1, soft=True)
        arr = np.dstack([im[..., ::-1], np.full(im.shape[:2], 255, np.uint8)])
        surf = skia.Surface(E.W, E.H)
        c = surf.getCanvas()
        c.drawImage(E.np_to_image(arr), 0, 0)
        self.overlay(c, t)
        out = surf.makeImageSnapshot().toarray(colorType=skia.ColorType.kRGBA_8888_ColorType,
                                               alphaType=skia.AlphaType.kOpaque_AlphaType)[..., :3]
        return E.paper_grain(out.astype(np.float32) / 255, self.grain)

    def line(self, c, p0, p1, u, width):
        a = S_project(p0, self._t)
        b = S_project(p1, self._t)
        if not a or not b:
            return
        x1 = a[0] + (b[0] - a[0]) * u
        y1 = a[1] + (b[1] - a[1]) * u
        c.drawLine(a[0], a[1], x1, y1, skia.Paint(AntiAlias=True, Color4f=E.col("#0A0A0F"), StrokeWidth=width,
                                                  StrokeCap=skia.Paint.kButt_Cap))

    def overlay(self, c, t):
        self._t = t
        u = E.ease_io(E.seg(t, 111.75, 112.25), 2.5)
        if u > 0:
            w = 6.0
            cw = S.CELL_W
            # every row: bars reach for each other, the line stops either side of the empty cell
            for r in range(S.ROWS):
                for col in range(S.COLS - 1):
                    a, b = (col, r), (col + 1, r)
                    if a == S.EMPTY or b == S.EMPTY:
                        continue
                    if a in self.ends and b in self.ends:
                        ra = self.ends[a][1]
                        lb = self.ends[b][0]
                        # one unbroken black line from bar to bar: every rumour on the row gets blacked out with it
                        mid = ((ra[0] + lb[0]) / 2, (ra[1] + lb[1]) / 2, (ra[2] + lb[2]) / 2)
                        self.line(c, ra, mid, u, w)
                        self.line(c, lb, mid, u, w)
            # either side of the empty cell the line runs up to its frame and stops dead
            ex, ez = S.cell_center(*S.EMPTY)
            left = self.ends[(1, 1)][1]
            right = self.ends[(3, 1)][0]
            self.line(c, left, (ex - cw / 2 + 0.03, left[1], left[2]), u, w)
            self.line(c, right, (ex + cw / 2 - 0.03, right[1], right[2]), u, w)
            # the first and last card in each row reach to the edge of the wall too
        if t > 111.6:
            # a cursor waits under "from the person herself"; nobody has typed anything
            ex, ez = S.cell_center(*S.EMPTY)
            p = S_project((ex - S.CELL_W * 0.30, 0.0, ez - S.CELL_H * 0.5 + S.CELL_H * 0.385), t)
            if p and int((t - 111.6) / 0.24) % 2 == 0:
                sc = S.LENS / 36 * 1920 / p[2]
                E.rect(c, p[0], p[1] - 0.26 * sc, 0.06 * sc, 0.26 * sc, E.RED)
        # lyric track: always the same place
        for a, b, st in self.strips:
            if a - 0.01 <= t < min(b + 0.05, S.T1):
                st.draw(c, 960, 1034, t, ax=0.5)


def S_project(p, t):
    return S.project(p, t)
