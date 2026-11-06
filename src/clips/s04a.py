"""Section 04a: the shadow on the table was this newspaper. It drops past the lens, sinks turning through the classroom,
and we follow it down until it lies on her desk in exactly the framing of the first frame of clip 2.

The sheet is drawn in 2D: it is the same mesh as classroom.newspaper at rest, seen by the same camera as
shared_c2.camera_at, so at rest the two line up to the pixel. The room under it is the real one: stills rendered and
painted exactly like clip 2 (src/three/shot_fallplate.py, assets/tex/fall), so the floor and the desk do not change colour
at the cut. Coordinates are the "page frame": X to the right of the final frame, Y down it, Z up, origin at the centre of
the resting page.
"""
import math
import sys
from pathlib import Path

import numpy as np
import skia

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / "src" / "npr"), str(ROOT / "src" / "three")]
sys.path.insert(0, str(Path(__file__).parent))
import common as K  # noqa: E402
import engine as E  # noqa: E402
import paint_c2 as PC  # noqa: E402
import shared_c2 as C2  # noqa: E402
import shot_fallplate as FP  # noqa: E402

F0, F1 = 1996, 2079
T0, T1 = F0 / 30, F1 / 30
LENS_K = 26.0 / 36.0 * 1920
HW, HH = C2.PAGE_W / 2, C2.PAGE_H / 2
_CA, _SA = math.cos(C2.PAGE_ANGLE), math.sin(C2.PAGE_ANGLE)
LAND = 69.16             # the sheet is lying still from here on
SWAP = 66.665            # the sheet covers the whole frame: the table behind it can go
TAPE_UNDER = 67.75       # from here the falling sheet passes over the tape, so the tape leaves under it
GROUND_Z = -C2.PAGE_C[2]
DESK_Z = 0.715 - C2.PAGE_C[2]
SEAT_Z = 0.42 - C2.PAGE_C[2]
# the planes of the sheet are shaded as on the table of the last clip
_SHADE_SLIDE = 0.55 * np.array([0.615, 0.789])
SUN = np.array([-_SHADE_SLIDE[0], -_SHADE_SLIDE[1], 1.0]) / math.sqrt(1 + 0.55 ** 2)
# the room's own low sun (shared_c2.sun_dir_at at the start of clip 2), in the page frame: metres of slide per metre of height
_s = C2.sun_dir_at(C2.T0)
_p = (-(_s[0] * _CA + _s[1] * _SA), -_s[0] * _SA + _s[1] * _CA)
SLIDE = np.array(_p) / -_s[2]
DESK_SHADOW = (0.93, 0.86, 0.82)   # clip 2's shadow tint on the desk
SHADE_AT = 0.80          # a plane turned this far from the sun drops to the one shadow tone
SHADE = (0.80, 0.84, 0.92)   # the same tint comp.py gives printed things
UNDER_TONE = "#B1B4B1"   # the under sheet, in the top sheet's shade: measured from clip 2


class Curve:
    """Monotone cubic through points (t, y): no overshoot, no corners."""

    def __init__(self, pts):
        self.x = np.array([p[0] for p in pts], float)
        self.y = np.array([p[1] for p in pts], float)
        h = np.diff(self.x)
        d = np.diff(self.y) / h
        m = np.zeros_like(self.y)
        m[0], m[-1] = d[0], d[-1]
        for i in range(1, len(m) - 1):
            if d[i - 1] * d[i] > 0:
                w1, w2 = 2 * h[i] + h[i - 1], h[i] + 2 * h[i - 1]
                m[i] = (w1 + w2) / (w1 / d[i - 1] + w2 / d[i])
        self.m, self.h = m, h

    def __call__(self, t):
        t = min(max(t, self.x[0]), self.x[-1])
        i = min(int(np.searchsorted(self.x, t, side="right")) - 1, len(self.h) - 1)
        s = (t - self.x[i]) / self.h[i]
        a, b, ma, mb = self.y[i], self.y[i + 1], self.m[i] * self.h[i], self.m[i + 1] * self.h[i]
        return (2 * s ** 3 - 3 * s ** 2 + 1) * a + (s ** 3 - 2 * s ** 2 + s) * ma + (-2 * s ** 3 + 3 * s ** 2) * b + (s ** 3 - s ** 2) * mb


# height of the sheet above where it will rest, and how far the camera stays above the sheet
Z_PAPER = Curve([(T0, 3.30), (66.8, 2.76), (67.4, 1.80), (68.0, 0.85), (68.5, 0.28), (68.9, 0.05), (LAND, 0.0), (70.0, 0.0)])
GAP = Curve([(T0, 0.130), (66.60, 0.170), (66.70, 0.25), (67.0, 0.72), (67.45, 1.50), (67.8, 1.42), (68.2, 0.98), (68.6, 0.66), (69.0, 0.44), (69.30, 0.366)])
YAW = Curve([(T0, 15.0), (66.70, 11.0), (67.2, -14.0), (67.8, -34.0), (68.4, 11.0), (68.85, 3.0), (LAND, 0.0), (70.0, 0.0)])
# The sheet is nearly flat, so the whole of it crosses the shadow threshold at once and the page would flip colour in two
# frames. These hold the far part back, so the edge of the shadow travels across the page instead: from the top of the
# picture down as it leaves the shade (about 13 frames), and across as it enters it (about 6).
LEAVE = Curve([(67.9, 0.0), (68.22, 0.085), (68.32, 0.15), (68.42, 0.15), (68.7, 0.0)])
ENTER = Curve([(66.72, 0.0), (66.87, 0.12), (66.97, 0.075), (67.1, 0.0)])


def c2_gap(t):
    """Clip 2's own slow push, carried back a little, so the move is already going when the cut comes."""
    return 0.366 + 0.046 / (C2.RISE_START - C2.T0) * (C2.T0 - t)


def gap_at(t):
    u = E.seg(t, 69.0, C2.T0)
    return GAP(t) * (1 - u) + c2_gap(t) * u if t < C2.T0 else c2_gap(t)


def flutter_at(t):
    """0 at rest; 1 in open air."""
    return C2.smooth(E.seg(t, T0, 66.95)) * (1 - C2.smooth(E.seg(t, 67.9, LAND - 0.02)))


def pose(t):
    """Where the sheet is: centre, rotation matrix (paper to page frame), bend and crease amounts."""
    a = flutter_at(t)
    ph = math.tau * (t - T0) / 2.3
    roll = math.radians(27) * a * math.sin(ph)
    pitch = math.radians(21) * a * math.cos(ph * 0.8 + 0.7)
    yaw = math.radians(YAW(t))
    # a falling leaf slides towards the side it leans to, a quarter of a swing later
    sway = 0.34 * a
    x = sway * math.sin(ph - 1.15)
    y = sway * 0.72 * math.cos(ph * 0.8 - 0.45) - 0.05 * a
    # at the start it comes in from the top right, where its shadow came from
    k = 1 - C2.smooth(E.seg(t, T0, 66.64))
    x += 0.215 * k
    y -= 0.175 * k
    cy, sy = math.cos(yaw), math.sin(yaw)
    cr, sr = math.cos(roll), math.sin(roll)
    cp, sp = math.cos(pitch), math.sin(pitch)
    rz = np.array([[cy, -sy, 0], [sy, cy, 0], [0, 0, 1.0]])
    ry = np.array([[cr, 0, sr], [0, 1, 0], [-sr, 0, cr]])
    rx = np.array([[1, 0, 0], [0, cp, -sp], [0, sp, cp]])
    bend = 0.030 * a * math.sin(ph * 1.3 + 0.4)
    crease = 0.024 * a
    return np.array([x, y, Z_PAPER(t)]), rx @ ry @ rz, bend, crease


def sheet_points(u, v, sx, sy, dz, lift, bend, crease):
    """Same surface as classroom.newspaper, with the air's bend added. u, v in -1..1; returns paper coordinates."""
    # classroom builds with local x = -X; the corner terms below are written in its u
    ul = -u
    z = dz + lift * 0.75 * np.exp(-(v / 0.10) ** 2)
    z = z + lift * 0.9 * np.maximum(0.0, np.abs(v) - 0.72) ** 2 * 11
    z = z + lift * 2.2 * np.maximum(0.0, (ul + v) / 2 - 0.62) ** 2 * 9
    z = z + lift * 1.6 * np.maximum(0.0, (-ul + v) / 2 - 0.70) ** 2 * 9
    z = z + bend * (v * v - 1 / 3) - crease * np.abs(v)
    return np.stack([u * sx / 2, v * sy / 2, z], -1)


def world_to_page(wx, wy, wz):
    dx, dy = wx - C2.PAGE_C[0], wy - C2.PAGE_C[1]
    lx, ly = dx * _CA + dy * _SA, -dx * _SA + dy * _CA
    return np.array([-lx, ly, wz - C2.PAGE_C[2]], float)


def poly_path(pts, close=True):
    p = skia.Path()
    p.moveTo(float(pts[0][0]), float(pts[0][1]))
    for q in pts[1:]:
        p.lineTo(float(q[0]), float(q[1]))
    if close:
        p.close()
    return p


class PaperFall(E.Clip):
    name = "s04a"
    t0, t1 = T0, T1
    shutter = 0.3

    def setup(self):
        base = PC.page_base()
        self.tex = E.np_to_image(np.dstack([base[..., :3], np.full(base.shape[:2], 255, np.uint8)]))
        self.tw, self.th = PC.PAGE_PX
        self._digging = None
        line = K.LYRICS[18]
        syl = {s["text"].strip(): s["t"] for s in reversed(line["syl"])}   # first time each sound is sung
        self.tape = K.Strip("ああ　時に", [syl["aa"], syl["aa"], syl["to"], syl["to"], syl["ni"]], size=46)
        self.tape_times = syl
        # the two sheets' grids at rest resolution, and the texture coordinates of the top one
        self.nx, self.ny = 40, 28
        us = np.linspace(-1, 1, self.nx + 1)
        vs = np.linspace(-1, 1, self.ny + 1)
        self.uu, self.vv = np.meshgrid(us, vs)
        # + 0.5: comp.apply_live samples by texel index, Skia by texel edge
        tx = (self.uu + 1) / 2 * self.tw + 0.5
        ty = (self.vv + 1) / 2 * self.th + 0.5
        self.texs = [skia.Point(float(a), float(b)) for a, b in zip(tx.ravel(), ty.ravel())]
        idx = []
        for j in range(self.ny):
            for i in range(self.nx):
                a = j * (self.nx + 1) + i
                b, c, d = a + 1, a + self.nx + 2, a + self.nx + 1
                idx += [a, b, c, a, c, d]
        self.idx = idx
        self.plates = [(h, E.load_image(FP.PLATES / f"h{h:05.3f}.png")) for h in sorted(FP.HEIGHTS)]
        dx, dy = C2.her_desk()
        self.desk = [world_to_page(dx + a, dy + b, 0.715) for a, b in ((-0.31, -0.22), (0.31, -0.22), (0.31, 0.22), (-0.31, 0.22))]

    def digging(self):
        if self._digging is None:
            import s03
            self._digging = s03.Digging()
            self._digging.setup()
        return self._digging

    def blur(self, t):
        if t < 66.85:
            return 24
        if t >= LAND:
            return 1
        return 8

    # ---- projection ----
    def project(self, p, t):
        """p: (..., 3) in the page frame. Straight-down camera over the page's centre, always on the same heading."""
        h = Z_PAPER(t) + gap_at(t)
        p = np.asarray(p, float)
        z = np.maximum(h - p[..., 2], 0.012)
        return np.stack([960 + LENS_K * p[..., 0] / z, 540 + LENS_K * p[..., 1] / z], -1)

    def cast(self, p, plane_z):
        """The shadow of a point on a horizontal plane."""
        p = np.asarray(p, float)
        lift = (p[..., 2] - plane_z)[..., None]
        out = p.copy()
        out[..., :2] = p[..., :2] + SLIDE * lift
        out[..., 2] = plane_z
        return out

    # ---- the room ----
    def draw_room(self, c, t):
        """The rendered room from the nearest height at or above the sheet's camera, scaled about the point straight below."""
        h = Z_PAPER(t) + gap_at(t)
        hk, im = self.plates[-1]
        for hh, ii in self.plates:
            if hh >= h - 0.004:
                hk, im = hh, ii
                break
        # what has to stay in register: the desk at the end, the floor and the desks together while it is high up
        zref = -0.35 * C2.smooth((h - 0.6) / 0.8)
        k = max((hk - zref) / (h - zref), 1.0)
        c.save()
        c.translate(960, 540)
        c.scale(k, k)
        c.translate(-960, -540)
        c.drawImage(im, 0, 0, skia.SamplingOptions(skia.FilterMode.kLinear), skia.Paint())
        c.restore()

    def draw_paper_shadow(self, c, t, top_edge):
        """The low sun throws the sheet's shadow far across the room; it only meets her desk in the last moments, sliding in
        along the desk top until it lies under the sheet."""
        desk_path = poly_path(self.project(np.array(self.desk), t))
        paint = skia.Paint(AntiAlias=True, Color4f=skia.Color4f(*DESK_SHADOW, 1.0), BlendMode=skia.BlendMode.kMultiply)
        c.save()
        c.clipPath(desk_path, True)
        c.drawPath(poly_path(self.project(self.cast(top_edge, DESK_Z), t)), paint)
        c.restore()

    # ---- the sheet ----
    def edge_of(self, pts):
        """Boundary of a grid of points, in order."""
        return np.concatenate([pts[0, :], pts[1:, -1], pts[-1, -2::-1], pts[-2:0:-1, 0]], 0)

    def sheet_world(self, t, u, v, sx, sy, dz, lift, off=(0.0, 0.0), rot=0.0):
        center, R, bend, crease = pose(t)
        p = sheet_points(u, v, sx, sy, dz, lift, bend, crease)
        if rot or off[0] or off[1]:
            ca, sa = math.cos(rot), math.sin(rot)
            q = p.copy()
            q[..., 0] = p[..., 0] * ca - p[..., 1] * sa + off[0]
            q[..., 1] = p[..., 0] * sa + p[..., 1] * ca + off[1]
            p = q
        return p @ R.T + center

    def shade_row(self, t, v):
        """How far above the shadow threshold the sheet is along the row v (ignoring small corner curls)."""
        center, R, bend, crease = pose(t)
        dzdv = (bend * 2 * v - crease * np.sign(v)) * (2 / C2.PAGE_H)
        n = np.stack([np.zeros_like(v), -dzdv, np.ones_like(v)], -1)
        n = n / np.linalg.norm(n, axis=-1, keepdims=True)
        return (n @ R.T) @ SUN - SHADE_AT - LEAVE(t) * np.maximum(v, 0.0) ** 1.5 + ENTER(t) * (v + 1) / 2

    def draw_shade(self, c, t):
        """Hard-edged bands of the one shadow tone, across the sheet, moving as it turns."""
        if t >= LAND - 0.1:
            return
        vs = np.linspace(-1, 1, 113)
        s = self.shade_row(t, vs)
        if (s >= 0).all():
            return
        us = np.linspace(-1, 1, 21)
        paint = skia.Paint(AntiAlias=True, Color4f=skia.Color4f(*SHADE, 1.0), BlendMode=skia.BlendMode.kMultiply)
        i = 0
        n = len(vs)
        while i < n:
            if s[i] >= 0:
                i += 1
                continue
            j = i
            while j + 1 < n and s[j + 1] < 0:
                j += 1
            v0 = vs[i] if i == 0 else vs[i - 1] + (vs[i] - vs[i - 1]) * s[i - 1] / (s[i - 1] - s[i])
            v1 = vs[j] if j == n - 1 else vs[j] + (vs[j + 1] - vs[j]) * s[j] / (s[j] - s[j + 1])
            mid = np.concatenate([[v0], vs[i:j + 1], [v1]])
            a = self.sheet_world(t, us, np.full_like(us, v0), C2.PAGE_W, C2.PAGE_H, 0.0030, 0.011)
            b = self.sheet_world(t, np.ones_like(mid), mid, C2.PAGE_W, C2.PAGE_H, 0.0030, 0.011)
            d = self.sheet_world(t, us[::-1], np.full_like(us, v1), C2.PAGE_W, C2.PAGE_H, 0.0030, 0.011)
            f = self.sheet_world(t, -np.ones_like(mid), mid[::-1], C2.PAGE_W, C2.PAGE_H, 0.0030, 0.011)
            c.drawPath(poly_path(self.project(np.concatenate([a, b, d, f], 0), t)), paint)
            i = j + 1

    def draw_sheets(self, c, t):
        a = flutter_at(t)
        # the under sheet: as classroom.newspaper at rest, and a little loose in the air
        off = ((-0.006 * _CA - 0.004 * _SA) - 0.006 * a, (0.006 * _SA - 0.004 * _CA) + 0.005 * a)
        under = self.sheet_world(t, self.uu, self.vv, C2.PAGE_W * 1.006, C2.PAGE_H * 1.012, 0.0005 - 0.004 * a, 0.006, off=off, rot=-(0.012 + 0.035 * a))
        top = self.sheet_world(t, self.uu, self.vv, C2.PAGE_W, C2.PAGE_H, 0.0030, 0.011)
        gap = gap_at(t)
        line = max(1.8, min(5.0, 5.0 * 0.366 / gap))
        ink = skia.Paint(AntiAlias=True, Color4f=E.col(E.INK), Style=skia.Paint.kStroke_Style, StrokeWidth=line, StrokeJoin=skia.Paint.kRound_Join)
        path_u = poly_path(self.project(self.edge_of(under), t))
        c.drawPath(path_u, skia.Paint(AntiAlias=True, Color4f=E.col(UNDER_TONE)))
        c.drawPath(path_u, ink)
        tex = self.tex
        if t >= 69.2:
            pt = PC.page_tex(t)
            tex = E.np_to_image(np.dstack([pt[..., :3], np.ones(pt.shape[:2], np.float32)]))
        pts = self.project(top, t).reshape(-1, 2)
        pos = [skia.Point(float(x), float(y)) for x, y in pts]
        v = skia.Vertices(skia.Vertices.kTriangles_VertexMode, pos, self.texs, None, self.idx)
        scale = LENS_K / gap * C2.PAGE_W / self.tw
        samp = E.SAMPLING_DOWN if scale < 0.9 else skia.SamplingOptions(skia.FilterMode.kLinear)
        shader = tex.makeShader(skia.TileMode.kClamp, skia.TileMode.kClamp, samp)
        c.drawVertices(v, skia.Paint(AntiAlias=True, Shader=shader))
        self.draw_shade(c, t)
        c.drawPath(poly_path(self.project(self.edge_of(top), t)), ink)

    def draw(self, c, t):
        top_edge = None
        if t < SWAP:
            self.digging().draw_stage(c, t)
        else:
            self.draw_room(c, t)
            top_edge = self.edge_of(self.sheet_world(t, self.uu, self.vv, C2.PAGE_W, C2.PAGE_H, 0.0030, 0.011))
            self.draw_paper_shadow(c, t, top_edge)
        if t >= TAPE_UNDER:
            self.tape.draw(c, 960, 1034, t, ax=0.5)
        self.draw_sheets(c, t)
        if t < TAPE_UNDER:
            self.tape.draw(c, 960, 1034, t, ax=0.5)
