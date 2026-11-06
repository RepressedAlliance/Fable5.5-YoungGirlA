"""Section 11, first half: the knocking has stopped; sheets of paper slide in under the door. Finished 3D frames plus the lyric tape.
From 183 s the camera sinks slowly towards the pile in the light, and at the end dives into it, tilting over until it looks straight down: the frame is all paper, and that is where s11b begins, on the first sung さ. The push is done on the finished frames: the floor's own perspective is undone, as a real camera's would be. The paper in the light is drawn again at every size from the same picture the 3D painter used, on the same corners, so it stays sharp. Past VEC_K the floor is drawn again too, with the 3D painter's own tones (paint_room), its boards, the light's real outline and the painted shadows of the feet: enlarged, the frame's edges were stair-steps and its dark paper was mush. Only what stands on the floor still comes from the frame."""
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
import crisp  # noqa: E402
import s10  # noqa: E402
import s11b  # noqa: E402
import shared_room2 as S  # noqa: E402

ROOT = K.ROOT
DIVE0 = 183.0
DIVE_POW = 3.6      # most of the way is covered in the last half second
VEC_K = 1.32        # from this enlargement on the floor is drawn, not enlarged
SS = 2              # the floor's boards and bands are worked out at this many samples a pixel
FRAME_LINE = 3.5    # how wide the frame draws its ink on paper in the dark
# paint_room at this level of the room: the tones of the dark, of the three bands of light, and of the ink
LO, HI, SAT = np.array((0x08, 0x0E, 0x27), np.float32) / 255, np.array((0x3F, 0x52, 0x94), np.float32) / 255, 0.12
BANDS = np.array(((0xF7, 0xEB, 0xCB), (0xA8, 0xA3, 0xA4), (0x61, 0x6E, 0x9A)), np.float32) / 255
BAND_R = (0.20, 0.47)
INK = np.array((0x04, 0x05, 0x0E), np.float32) / 255
SLIT = np.array((0x5C, 0x7B, 0xC4), np.float32) / 255 * 0.55
FLOOR_COL = np.array((0.25415212, 0.14702728, 0.07618539), np.float64)      # linear, from the render's colour pass
TINT = np.array(s11b.PILE_TINT, np.float32)
# the door's light on the floor, as the renderer has it (work/gen/trans_b/wedge.py). World metres.
WEDGE = ((0.754, -0.812), (-0.141, -0.812), (-0.155, -0.81), (-0.168, -0.784), (-0.163, -0.77), (-0.191, -0.736), (-0.19, -0.72), (-0.213, -0.7), (-0.247, -0.681), (-0.249, -0.669), (-0.243, -0.666),
         (-0.228, -0.674), (-0.174, -0.718), (-0.137, -0.789), (-0.125, -0.788), (-0.114, -0.78), (-0.099, -0.735), (-0.092, -0.682), (-0.098, -0.635), (-0.134, -0.552), (-0.161, -0.517), (-0.193, -0.493),
         (-0.194, -0.488), (-0.165, -0.407), (-0.156, -0.394), (-0.157, -0.385), (-0.016, 0.0), (0.716, 0.0), (0.817, -0.278), (0.813, -0.318), (0.787, -0.398), (0.778, -0.407), (0.773, -0.42), (0.775, -0.436),
         (0.761, -0.718), (0.756, -0.725))


def floor_homography(t):
    a = np.array([[0.1, -0.1], [0.7, -0.1], [0.7, -1.1], [0.1, -1.1]], np.float32)
    b = np.array([S.project((x, y, 0.0015), t)[:2] for x, y in a], np.float32)
    return cv2.getPerspectiveTransform(a, b)


def apply(h, pts):
    return cv2.perspectiveTransform(np.array(pts, np.float64).reshape(-1, 1, 2), h).reshape(-1, 2)


def srgb(x):
    return np.where(x <= 0.0031308, 12.92 * x, 1.055 * np.power(np.maximum(x, 1e-6), 1 / 2.4) - 0.055)


def grey(a):
    return (a * np.array((0.3, 0.55, 0.15), a.dtype)).sum(-1, keepdims=True)


def as_image(a):
    a8 = (np.clip(a, 0, 1) * 255 + 0.5).astype(np.uint8)
    return E.np_to_image(np.dstack([a8, np.full(a8.shape[:2], 255, np.uint8)]))


def on_screen(surf):
    return surf.makeImageSnapshot().toarray(colorType=skia.ColorType.kRGBA_8888_ColorType, alphaType=skia.AlphaType.kOpaque_AlphaType)[..., :3].astype(np.float32) / 255


def fill_polys(polys, h):
    m = np.zeros((E.H, E.W), np.uint8)
    for p in polys:
        q = apply(h, p)
        cv2.fillPoly(m, [np.round(np.clip(q, -30000, 30000) * 16).astype(np.int32)], 255, lineType=cv2.LINE_AA, shift=4)
    return m.astype(np.float32)[..., None] / 255


class Room2(E.Clip):
    name = "s11a"
    t0, t1 = S.T0, S.T1
    cuts = S.CLOSE

    def setup(self):
        self.tape = s10.tape(50, "合言葉を繰り返すだけ")
        self.paper = None

    def prepare(self):
        self.paper = s11b.pile_image()
        # the same sheet in the other two lights of the room: out of the door's light altogether, and in the shadow of her feet. The painter's own sums.
        base = self.paper.toarray(colorType=skia.ColorType.kRGBA_8888_ColorType, alphaType=skia.AlphaType.kOpaque_AlphaType)[..., :3].astype(np.float32) / 255 / TINT
        base = np.clip(base, 0, 1)
        g = grey(base)
        v = np.clip(g, 0, 1) ** 1.05
        self.sheet_dark = as_image(LO + (HI - LO) * v + (base - g) * SAT * (0.4 + v))
        self.sheet_deep = as_image(LO + (HI - LO) * np.clip(g * 0.55, 0, 1) ** 1.2)
        # where it ends: the floor as s11b's first frame has it, and the patch of floor that then fills the screen
        view = s11b.Wall.floor_view(None, self.t1, False)
        self.view = view
        corners = [(0.0, 0.0), (E.W, 0.0), (E.W, E.H), (0.0, E.H)]
        self.end_px = np.array(corners, np.float64)
        self.end_floor = np.array([s11b.screen_to_floor(x, y, view) for x, y in corners], np.float64)
        self.floor_srgb = srgb(FLOOR_COL).astype(np.float32)

    def dive(self, t, f):
        """The warp from this frame to the screen at time t, and how much it has enlarged."""
        x = E.seg(t, DIVE0, self.t1)
        a = apply(f, self.end_floor)
        b = self.end_px
        ratio = np.linalg.norm(b[1] - b[0]) / np.linalg.norm(a[1] - a[0])
        k = math.exp(math.log(ratio) * x ** DIVE_POW)
        w = (k - 1) / (ratio - 1)
        cur = a + (b - a) * w
        return cv2.getPerspectiveTransform(a.astype(np.float32), cur.astype(np.float32)), k, w

    def lit_mask(self, im):
        """Where the frame has light on paper. The painter keeps a sheet's crayon only in the light; green stems and ink are closed over."""
        m = (im[..., 2] > 150).astype(np.uint8)
        m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (9, 9)))
        # stems and pieces of crayon that are still holes: the light has no small holes in it, a shadow is big
        n, lab, st, _ = cv2.connectedComponentsWithStats(1 - m, connectivity=4)
        small = np.nonzero(st[:, 4] < 1500)[0]
        m[np.isin(lab, small)] = 1
        return cv2.GaussianBlur(m.astype(np.float32), (0, 0), 0.8)

    def warp_frame(self, im, D, k):
        """The frame under the warp. Past 1.5 times it is enlarged by crisp first, only the part that shows."""
        if k < 1.5:
            return cv2.warpPerspective(im, D, (E.W, E.H), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
        inv = np.linalg.inv(D)
        q = apply(inv, self.end_px)
        x0, y0 = int(max(q[:, 0].min() - 24, 0)), int(max(q[:, 1].min() - 24, 0))
        x1, y1 = int(min(q[:, 0].max() + 24, E.W)), int(min(q[:, 1].max() + 24, E.H))
        if x1 - x0 < 8 or y1 - y0 < 8:
            x0, y0, x1, y1 = 0, 0, E.W, E.H
        crop = im[y0:y1, x0:x1].astype(np.float32) / 255
        ks = min(4, int(math.ceil(k)))
        big = crisp.upscale(np.dstack([crop, np.ones(crop.shape[:2], np.float32)]), ks)[..., :3]
        M = D @ np.array([[1, 0, x0], [0, 1, y0], [0, 0, 1]], np.float64) @ np.array([[1 / ks, 0, 0], [0, 1 / ks, 0], [0, 0, 1]], np.float64)
        return cv2.warpPerspective(big, M, (E.W, E.H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)

    def standing(self, t):
        """What in the frame is not floor or paper on it: it stays the frame's. Made once from the render's passes (index, position), kept as a small file."""
        n = int(round((t - self.t0) * 60))
        n -= n % 2
        d = ROOT / "work" / "cache" / "room2_standing"
        f = d / f"f{n:05d}.png"
        if f.exists():
            return cv2.imread(str(f), cv2.IMREAD_GRAYSCALE)
        sys.path.insert(0, str(ROOT / "src" / "npr"))
        import comp
        p = comp.read_exr(ROOT / "work" / "render" / "room2_exr" / f"f{n:05d}.exr")
        ob = np.round(p["IndexOB"]).astype(np.int32)
        ma = np.round(p["IndexMA"]).astype(np.int32)
        pos = np.nan_to_num(p["Position"][..., :3], posinf=1e4, neginf=-1e4)
        ids = json.loads((ROOT / "work" / "render" / "room2_ids.json").read_text())
        flat = (ob == ids["floor"]) | ((ob >= ids["sheet0"]) & (ob <= ids["sheet12"]))
        flat &= (ma != 6) & (pos[..., 1] < 0.0)
        out = cv2.resize((~flat).astype(np.uint8) * 255, (E.W, E.H), interpolation=cv2.INTER_AREA)
        d.mkdir(parents=True, exist_ok=True)
        cv2.imwrite(str(f), out)
        return out

    def floor_tones(self, inv, ppm):
        """The painter's floor at every pixel: in the light, in the feet's shadow, in the dark. inv: screen to floor. ppm: screen pixels to the metre."""
        w_, h_ = E.W * SS, E.H * SS
        xx, yy = np.meshgrid((np.arange(w_) + 0.5) / SS, (np.arange(h_) + 0.5) / SS)
        w = inv[2, 0] * xx + inv[2, 1] * yy + inv[2, 2]
        X = (inv[0, 0] * xx + inv[0, 1] * yy + inv[0, 2]) / w
        Y = (inv[1, 0] * xx + inv[1, 1] * yy + inv[1, 2]) / w
        # boards (paint_room.floorboards): fixed to the world, one value each, a joint between them
        bw = 0.135
        u = X / bw
        i = np.floor(u)
        off = np.mod(i * 0.37, 1.0) * 1.8
        j = np.floor((Y + off) / 1.8)
        h = np.mod(np.sin(i * 12.9898 + j * 78.233) * 43758.5453, 1.0)
        val = (0.86 + 0.28 * np.floor(h * 4) / 3).astype(np.float32)
        half = 0.9 / ppm
        dv = np.mod(Y + off, 1.8)
        joint = (((np.abs(u - np.round(u)) * bw < half) | (dv < half) | (dv > 1.8 - half)) & (Y < 0)).astype(np.float32)[..., None] * 0.55
        base = val[..., None] * self.floor_srgb
        g = grey(base)
        v = np.clip(g, 0, 1) ** 1.05
        dark = LO + (HI - LO) * v + (base - g) * SAT * (0.4 + v)
        # the cold line the slit in the curtains lays on the floor
        along = X - S.X0
        slit = (np.abs(Y - (-0.62 - 0.46 * along)) < 0.008 + 0.016 * along) & (along < 0.98)
        dark = np.where(slit[..., None], dark + SLIT, dark)
        deep = LO + (HI - LO) * np.clip(g * 0.55, 0, 1) ** 1.2
        r = -Y
        band = np.where((r < BAND_R[0])[..., None], BANDS[0], np.where((r < BAND_R[1])[..., None], BANDS[1], BANDS[2]))
        lit = band * (0.60 + 0.62 * g)
        return [cv2.resize((a * (1 - joint) + INK * joint).astype(np.float32), (E.W, E.H), interpolation=cv2.INTER_AREA) for a in (lit, deep, dark)]

    def draw_vector(self, c, t, im, D, k, w):
        H = D @ floor_homography(t)
        ppm = float(np.linalg.norm(apply(H, [(0.3, -0.5)]) - apply(H, [(0.4, -0.5)]))) * 10
        layers = self.floor_tones(np.linalg.inv(H), ppm)
        # the sheets lie on all three, each in its own version of itself; the light decides afterwards which you see
        lit_line = max(1.6, 1.2 * k ** 0.75)
        # the frame's ink on the sheets in the dark is heavy: start from it and thin down to the sheets' own line as the camera arrives
        dark_line = lit_line + (FRAME_LINE * VEC_K - lit_line) * (1 - E.ease_io(E.seg(k, VEC_K, 3.0), 1.4))
        px = max(2, int(round(S.lens_at(t) / 22.0 * 1.6 * 1.5))) / 1.5 * k
        ex, ey = 14 * self.view[2], 18 * self.view[2]      # s11b's shadow, at the end
        sx, sy = px * 0.5 + (ex - px * 0.5) * w, px + (ey - px) * w
        shadow = 0.55 + (s11b.SHADOW_A - 0.55) * w
        tops = []
        for layer, tex, line in zip(layers, (self.paper, self.sheet_deep, self.sheet_dark), (lit_line, dark_line, dark_line)):
            surf = skia.Surface(E.W, E.H)
            lc = surf.getCanvas()
            lc.drawImage(as_image(layer), 0, 0)
            for i in range(len(S.SHEETS)):
                ax = S.sheet_axes(i, t)
                if ax is None:
                    continue
                tl, tr, bl = ax
                br = (tr[0] + bl[0] - tl[0], tr[1] + bl[1] - tl[1], tl[2])
                q = apply(D, [S.project(p, t)[:2] for p in (tl, tr, br, bl)])
                lc.drawPath(s11b.poly([(x_ + sx, y_ + sy) for x_, y_ in q]), s11b.fill(E.INK, shadow))
                lc.save()
                lc.concat(E.quad_matrix((tex.width(), tex.height()), [tuple(v) for v in q]))
                lc.drawImage(tex, 0, 0, E.SAMPLING_DOWN)
                lc.restore()
                lc.drawPath(s11b.poly(q), s11b.ink_line(line))
            tops.append(on_screen(surf))
        # the light's real outline, and the shadow her feet lay in it, exactly as the painter cut them
        wedge = fill_polys([WEDGE], H)
        feet = fill_polys(S.foot_shadows(t) + S.corridor_shadows(t) + S.hand_shadow(t) + S.pace_shadows(t), H)
        rgb = tops[0] * wedge * (1 - feet) + tops[1] * wedge * feet + tops[2] * (1 - wedge)
        # what stands on the floor, and the far side of the door, are the frame's
        st = self.standing(t)
        if st.max() > 0:
            m = cv2.warpPerspective(st, D, (E.W, E.H), flags=cv2.INTER_LINEAR, borderValue=0).astype(np.float32) / 255
            if m.max() > 0.02:
                m = np.clip((cv2.GaussianBlur(m, (0, 0), max(0.7, k * 0.6)) - 0.42) * 5 + 0.5, 0, 1)[..., None]
                rgb = rgb * (1 - m) + self.warp_frame(im[..., ::-1].copy(), D, k).astype(np.float32) / 255 * m
        c.drawImage(as_image(rgb), 0, 0)

    def draw_dive(self, c, t, im):
        if self.paper is None:
            self.prepare()
        D, k, w = self.dive(t, floor_homography(t))
        if k >= VEC_K:
            self.draw_vector(c, t, im, D, k, w)
            return
        base = self.warp_frame(im[..., ::-1].copy(), D, k).astype(np.float32) / 255
        mask = cv2.warpPerspective(self.lit_mask(im), D, (E.W, E.H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
        mask = np.clip((mask - 0.5) * max(3.0, k) + 0.5, 0, 1)
        # the sheets, on their own corners, under the same warp
        surf = skia.Surface(E.W, E.H)
        lc = surf.getCanvas()
        lc.clear(skia.Color4f(0, 0, 0, 0))
        line = max(1.6, 1.2 * k ** 0.75)
        for i in range(len(S.SHEETS)):
            ax = S.sheet_axes(i, t)
            if ax is None:
                continue
            tl, tr, bl = ax
            br = (tr[0] + bl[0] - tl[0], tr[1] + bl[1] - tl[1], tl[2])
            q = apply(D, [S.project(p, t)[:2] for p in (tl, tr, br, bl)])
            lc.save()
            lc.concat(E.quad_matrix((self.paper.width(), self.paper.height()), [tuple(v) for v in q]))
            lc.drawImage(self.paper, 0, 0, E.SAMPLING_DOWN)
            lc.restore()
            lc.drawPath(s11b.poly(q), s11b.ink_line(line))
        layer = surf.makeImageSnapshot().toarray(colorType=skia.ColorType.kRGBA_8888_ColorType, alphaType=skia.AlphaType.kPremul_AlphaType).astype(np.float32) / 255
        a = (layer[..., 3] * mask)[..., None]
        # premultiplied: the sheet's own edge stays clean
        rgb = base * (1 - a) + layer[..., :3] * mask[..., None]
        c.drawImage(as_image(rgb), 0, 0)

    def draw(self, c, t):
        im = K.seq_frame("room2", t, self.t0)
        if t >= DIVE0:
            self.draw_dive(c, t, im)
        else:
            s10.blit(c, im)
        self.tape.draw(c, 960, s10.TAPE_Y, t, ax=0.5, color=s10.TAPE_INK, paper=s10.TAPE_PAPER)
