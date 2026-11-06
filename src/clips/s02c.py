"""37.43-44.80, the packed carriage: every head down over a phone or a weekly with her on the cover, her picture swinging in the ads overhead, rain and light going by.
It opens on the page that s02b printed: the page flies back and up and hangs there, one of the ads. It ends with the rider whose view this is lowering their eyes: two hands lift a phone into the shot and the camera goes into its screen, dark, a keyboard: s02d."""
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
import shared_train as S  # noqa: E402
import shared_cam  # noqa: E402
import crisp  # noqa: E402
import cutout as C  # noqa: E402
import s02b  # noqa: E402
import s02d  # noqa: E402

ROOT = K.ROOT
HANG = (S.T0, S.T0 + 0.56)        # the page flies to its place. It lands on the first long note
LIFT = (43.96, 44.34)             # the hands come up
INTO = (44.28, S.T1)              # the camera goes into the screen
PHONE = ROOT / "assets" / "gen" / "cut" / "p46_commuter_phone.png"
SCREEN = (368, 270, 800, 382)     # the magenta in that picture
P0 = 0.84                         # its size in the frame once it is up
K_BIG = 3                         # the picture is enlarged properly once, for the push
UI_TOP = s02d.KEY_Y - 742 + 166   # the top of the interface shown in the phone: its screen is wider than the frame, so a little of the empty part above the bar is left out
UI_K = SCREEN[2] / E.W            # picture pixels to interface pixels


def ad_corners(t):
    """The left ad of the first row, as shot_train hangs it: on its pivot, swinging with the carriage. Corners in the world: tl, tr, br, bl."""
    s = S.sway(t)
    a, b = math.radians(6.5) * s, math.radians(4.5) * s
    ca, sa, cb, sb = math.cos(a), math.sin(a), math.cos(b), math.sin(b)

    def world(x, z):
        # rotation about x, then y (Blender's XYZ order), of a point in the plane y = 0
        y1, z1 = -sa * z, ca * z
        x2, z2 = cb * x + sb * z1, -sb * x + cb * z1
        return -0.40 + x2, S.AD_ROWS[0] + y1, S.AD_PIVOT + z2

    top = S.AD_TOP - S.AD_PIVOT
    w = S.AD_W / 2
    return [world(-w, top), world(w, top), world(w, top - S.AD_H), world(-w, top - S.AD_H)]


class Train(seq3d.Seq3D):
    name = "s02c"
    shot = "train"
    t0, t1 = S.T0, S.T1
    cuts = S.CUTS
    lines = (8, 9, 10, 11)

    def setup(self):
        super().setup()
        self.art = None
        self.ui = None

    # ---- the page ----
    def ad_quad(self, t):
        return [S.project(p, t)[:2] for p in ad_corners(t)]

    def draw_ad(self, c, t):
        """Until the shot ends this ad is the page: it is the one thing in the carriage that came from the lockers."""
        if self.art is None:
            self.art = s02b.PageArt()
        q1 = self.ad_quad(t)
        u = E.ease_out(E.seg(t, *HANG), 3.0)
        if u >= 1:
            q = q1
        else:
            q0 = s02b.page_quad()
            s0 = abs(q0[1][0] - q0[0][0])
            s1 = math.hypot(q1[1][0] - q1[0][0], q1[1][1] - q1[0][1])
            k = math.exp(math.log(s1 / s0) * u)
            w = (k - 1) / (s1 / s0 - 1)
            q = [(a[0] + (b[0] - a[0]) * w, a[1] + (b[1] - a[1]) * w) for a, b in zip(q0, q1)]
        img = self.art.page_at(math.hypot(q[1][0] - q[0][0], q[1][1] - q[0][1]) / self.art.page.width())
        c.save()
        c.concat(E.quad_matrix((img.width(), img.height()), q))
        c.drawImage(img, 0, 0, E.SAMPLING_DOWN)
        c.restore()
        if u < 1:
            p = skia.Path()
            p.moveTo(*q[0])
            for v in q[1:]:
                p.lineTo(*v)
            p.close()
            c.drawPath(p, skia.Paint(AntiAlias=True, Color4f=E.col(E.INK), Style=skia.Paint.kStroke_Style, StrokeWidth=2.5, StrokeJoin=skia.Paint.kRound_Join))

    # ---- the phone ----
    def phone_ready(self):
        if self.ui is not None:
            return
        self.ui = s02d.Drafts()
        self.ui.setup()
        cache = ROOT / "work" / "cache" / "p46_commuter_phone_x3.png"
        if cache.exists():
            big = cv2.imread(str(cache), cv2.IMREAD_UNCHANGED)
        else:
            im = C.load(PHONE)
            # the screen goes, a little past its own edge, and whatever was mixed with the key along the outlines is ink
            im, mask = C.key_magenta(im)
            near = cv2.dilate((mask > 0.02).astype(np.uint8), np.ones((5, 5), np.uint8)).astype(bool)
            # only what the key has really tinted: painting a fixed width black put a row of beads along the inside of a thin line
            tinted = np.minimum(im[..., 0], im[..., 2]) - im[..., 1] > 0.02
            im[near & tinted & (im[..., 3] > 0), :3] = 0.03
            edge = (im[..., 3] < 0.98)
            im[edge, :3] = np.minimum(im[edge, :3], 0.05)
            big = crisp.upscale(np.dstack([im[..., :3], np.ones(im.shape[:2], np.float32)]), K_BIG)
            # the outline against the key is made fresh at the new size: enlarged with the paint, its pixels came out as a row of beads
            al = cv2.resize(im[..., 3], None, fx=K_BIG, fy=K_BIG, interpolation=cv2.INTER_CUBIC)
            al = cv2.GaussianBlur(al, (0, 0), K_BIG * 0.8)
            big[..., 3] = (np.clip((al - 0.5) * 5 + 0.5, 0, 1) * 255 + 0.5).astype(np.uint8)
            cv2.imwrite(str(cache), big[..., [2, 1, 0, 3]])
            big = big[..., [2, 1, 0, 3]]
        self.phone = E.np_to_image(np.dstack([big[..., 2::-1], big[..., 3]]))
        self.pic_w, self.pic_h = big.shape[1] / K_BIG, big.shape[0] / K_BIG

    def draw_phone(self, c, t):
        self.phone_ready()
        # where it ends: s02d's first frame, the interface at its close framing
        d = self.ui
        sa = 1.90
        px_ = 118 + 960 / sa
        p1 = sa / UI_K
        x1 = 960 - sa * px_ - p1 * SCREEN[0]
        y1 = 540 - sa * 700 + sa * UI_TOP - p1 * SCREEN[1]
        # where it rests
        x0 = 960 - P0 * (SCREEN[0] + SCREEN[2] / 2)
        y0 = E.H + 6 - P0 * self.pic_h
        p = math.exp(E.lerp(math.log(P0), math.log(p1), E.ease_io(E.seg(t, *INTO), 1.9)))
        w = (p - P0) / (p1 - P0)
        rise = (1 - E.ease_out(E.seg(t, *LIFT), 2.8)) * (self.pic_h * P0 + 40)
        sw = S.sway(t - 0.12) * (1 - w)
        x, y = x0 + (x1 - x0) * w + 7 * sw, y0 + (y1 - y0) * w + rise + 3 * sw
        # the interface, in the screen
        sx, sy, sw_, sh_ = SCREEN
        c.save()
        c.translate(x, y)
        c.scale(p, p)
        c.save()
        # the screen's dark goes on under the bezel, so no background can show along the hole's edge
        E.rect(c, sx - 12, sy - 12, sw_ + 24, sh_ + 24, s02d.BG)
        c.clipRect(skia.Rect.MakeXYWH(sx - 3, sy - 3, sw_ + 6, sh_ + 6))
        c.translate(sx, sy)
        c.scale(UI_K, UI_K)
        c.translate(0, -UI_TOP)
        st = d.state(t)
        d.compose(c, t, st)
        d.keyboard(c, t, st)
        c.restore()
        # the hands and the phone round it
        c.scale(1 / K_BIG, 1 / K_BIG)
        c.drawImage(self.phone, 0, 0, E.SAMPLING_DOWN if p < K_BIG else E.SAMPLING)
        c.restore()

    def overlay(self, c, t):
        if t < S.CUTS[0]:
            self.draw_ad(c, t)
        if t >= LIFT[0]:
            self.draw_phone(c, t)
        super().overlay(c, t)
