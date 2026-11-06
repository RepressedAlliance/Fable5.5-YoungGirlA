"""22.70-30.07, the school gate. It opens by coming back out of the dots of the photo everybody passed round: the same lattice, on the
singer's first word, but what the dots print by now is the gate itself, and they close up until they are the real thing. Hard dots
all the way: nothing dissolves. Then the flashes go off on every beat, and all the lenses turn together."""
import math
import sys
from pathlib import Path

import cv2
import numpy as np
import skia

sys.path.insert(0, str(Path(__file__).parent))
import common as K  # noqa: E402
import engine as E  # noqa: E402
import seq3d  # noqa: E402
import s01b as P  # noqa: E402
import shared_gate as S  # noqa: E402

BACK = 23.24                 # the camera is back at the full frame
REAL0, REAL1 = 23.00, 23.32  # the real picture opens up through the dots
PITCH_END = 0.50             # the dots end this fine, compared with the photo's at Z_GATE


def star(c, x, y, r, color):
    """A hard, flat flash: eight long points, no glow."""
    p = skia.Path()
    n = 8
    for i in range(n * 2):
        a = math.pi * i / n + 0.2
        rr = r * (1.0 if i % 2 == 0 else 0.22) * (1.0 if i % 4 != 0 else 1.35)
        q = (x + rr * math.cos(a), y + rr * math.sin(a))
        if i == 0:
            p.moveTo(*q)
        else:
            p.lineTo(*q)
    p.close()
    c.drawPath(p, skia.Paint(AntiAlias=True, Color4f=E.col(color)))


def zoom_back(t):
    """Photo-to-screen zoom on the way out: fast off the apex, settling exactly on the frame."""
    x = E.seg(t, P.T_END, BACK)
    return math.exp(math.log(P.Z_GATE) + (math.log(P.Z_APEX) - math.log(P.Z_GATE)) * (1 - x) ** 2.6)


def fineness(z):
    """1 at the apex, where the lattice is the photo's own, down to PITCH_END at the full frame."""
    w = math.log(z / P.Z_GATE) / math.log(P.Z_APEX / P.Z_GATE)
    return PITCH_END + (1 - PITCH_END) * w


class Gate(seq3d.Seq3D):
    name = "s02a"
    shot = "gate"
    t0, t1 = S.T0, S.T1
    lines = (0, 1, 2, 3)

    def setup(self):
        super().setup()
        still = P.gate_still()
        self.lines = P.line_art(still)
        self.plates = P.separations(still)
        self.k_tone = P.separations(P.without_lines(still, self.lines))[2]

    def print_frame(self, frame, t):
        """The gate in print, seen through the camera at this moment; frame is the real picture of this moment, float RGB, 1080p."""
        z = zoom_back(t)
        q = fineness(z)
        fx, fy = P.focus(z)
        # photo units at the middle of the frame map like this: photo = TARGET + (pixel - centre) * GATE_M
        toframe = 1 / P.GATE_M
        cell = P.CELL * q
        ye, cy, k = self.plates
        # as we come out, the solid lines come back through dots of their own, and the black plate gives up what it had been carrying for them
        broken = P.line_break(z)
        k = self.k_tone + (k - self.k_tone) * broken
        sig = cell * 0.62 * toframe
        plates = {"y": cv2.GaussianBlur(ye, (0, 0), sig), "c": cv2.GaussianBlur(cy, (0, 0), sig), "k": cv2.GaussianBlur(k, (0, 0), sig)}
        surf = skia.Surface(E.W, E.H)
        c = surf.getCanvas()
        c.clear(E.col(E.PAPER))
        boost = 1.0 + (P.BOOST_APEX - 1) * (1 - E.ease_out(E.seg(t, P.T_END, P.T_END + 0.25), 2))
        vw, vh = E.W / z, E.H / z
        for n, color, ang in P.PLATES:
            a = math.radians(ang)
            co, si = math.cos(a), math.sin(a)
            xs, ys = [], []
            # the lattice is the photo's own at q = 1, and closes up around the point the camera is on
            rect = [(fx - vw / 2 - cell, fy - vh / 2 - cell), (fx + vw / 2 + cell, fy - vh / 2 - cell), (fx - vw / 2 - cell, fy + vh / 2 + cell), (fx + vw / 2 + cell, fy + vh / 2 + cell)]
            base = [((rx - fx * (1 - q)) / q, (ry - fy * (1 - q)) / q) for rx, ry in rect]
            us = [(x * co + y * si) / P.CELL for x, y in base]
            ws = [(-x * si + y * co) / P.CELL for x, y in base]
            ii, jj = np.meshgrid(np.arange(int(min(us)) - 2, int(max(us)) + 3), np.arange(int(min(ws)) - 2, int(max(ws)) + 3))
            lx = P.CELL * (ii * co - jj * si)
            ly = P.CELL * (ii * si + jj * co)
            px = fx * (1 - q) + q * lx
            py = fy * (1 - q) + q * ly
            sx = 960 + (px - fx) * z
            sy = 540 + (py - fy) * z
            keep = (sx > -cell * z) & (sx < E.W + cell * z) & (sy > -cell * z) & (sy < E.H + cell * z)
            px, py, sx, sy = px[keep], py[keep], sx[keep], sy[keep]
            mx = np.clip((960 + (px - P.TARGET[0]) * toframe).astype(int), 0, E.W - 1)
            my = np.clip((540 + (py - P.TARGET[1]) * toframe).astype(int), 0, E.H - 1)
            cov = plates[n][my, mx]
            floor = 0.16 if n == "y" else 0.05
            on = cov > floor
            rs = cell * z * 0.72 * np.sqrt(cov[on]) * boost
            path = skia.Path()
            for x, y, r in zip(sx[on].tolist(), sy[on].tolist(), rs.tolist()):
                path.addCircle(x, y, r)
            c.drawPath(path, P.dot_paint(color, n == "c"))
        arr = surf.makeImageSnapshot().toarray(colorType=skia.ColorType.kRGBA_8888_ColorType, alphaType=skia.AlphaType.kOpaque_AlphaType)[..., :3]
        out = arr.astype(np.float32) / 255
        real = E.seg(t, REAL0, REAL1)
        if real <= 0 and broken >= 1:
            return out
        Z = z / P.Z_GATE
        sf, tf = 960 + (fx - P.TARGET[0]) * toframe, 540 + (fy - P.TARGET[1]) * toframe
        mat = np.array([[Z, 0, 960 - Z * sf], [0, Z, 540 - Z * tf]], np.float32)
        pitch = cell * z
        a = math.radians(45.0)
        yy, xx = np.mgrid[:E.H, :E.W].astype(np.float32)
        u = ((xx - 960) * math.cos(a) + (yy - 540) * math.sin(a)) / pitch
        v = (-(xx - 960) * math.sin(a) + (yy - 540) * math.cos(a)) / pitch
        screen = 0.5 + 0.25 * (np.cos(2 * np.pi * u) + np.cos(2 * np.pi * v))
        if broken < 1:
            ink = cv2.warpAffine(self.lines, mat, (E.W, E.H), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE) if Z > 1.0005 else self.lines
            ink = np.clip((ink - 0.5) * 2.5 + 0.5, 0, 1)
            m = (ink * np.clip((screen - (1 - (1 - broken) * 1.05)) * pitch / 1.6 + 0.5, 0, 1))[..., None]
            out = out * (1 - m) + np.array([10, 10, 15], np.float32) / 255 * m
        if real <= 0:
            return out
        # the real picture opens up through dots of its own, on the black plate's lattice, until there is nothing else left
        seen = cv2.warpAffine(frame, mat, (E.W, E.H), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE) if Z > 1.0005 else frame
        cover = E.ease_io(real, 1.6) * 1.05
        hard = np.clip((screen - (1 - cover)) * pitch / 1.6 + 0.5, 0, 1)[..., None]
        return out * (1 - hard) + seen * hard

    def overlay(self, c, t):
        for ft, idx in S.FLASHES:
            d = t - ft
            if not (-1e-3 <= d < 2 / 30 - 1e-3) or t < REAL1:
                continue
            p = S.project(S.flash_head(S.GEAR[idx], t), t)
            if not p or not (-200 < p[0] < 2120 and -200 < p[1] < 1280):
                continue
            # the size follows how near the camera is
            k = (1.0 if d < 1 / 30 - 1e-3 else 0.55) * min(1.5, 16.0 / p[2])
            star(c, p[0], p[1], 118 * k, E.INK)
            star(c, p[0], p[1], 100 * k, E.PAPER)
        super().overlay(c, t)

    def frame_rgb(self, t):
        if t >= REAL1:
            return super().frame_rgb(t)
        im = K.seq_frame(self.shot, t, self.t0)
        rgb = self.print_frame(im[..., ::-1].astype(np.float32) / 255, t)
        arr = np.dstack([(np.clip(rgb, 0, 1) * 255 + 0.5).astype(np.uint8), np.full(im.shape[:2], 255, np.uint8)])
        surf = skia.Surface(E.W, E.H)
        c = surf.getCanvas()
        c.drawImage(E.np_to_image(arr), 0, 0)
        self.overlay(c, t)
        out = surf.makeImageSnapshot().toarray(colorType=skia.ColorType.kRGBA_8888_ColorType, alphaType=skia.AlphaType.kOpaque_AlphaType)[..., :3]
        return E.paper_grain(out.astype(np.float32) / 255, self.grain)
