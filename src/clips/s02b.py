"""30.07-37.43, the shoe lockers: students crowd round one cell; the sky greys, it rains, the lights go out with them in it until only her cell is lit, and their phones.
Then the camera goes into the phone of the boy crouching by it, until its photo of her loafers is all there is. The screen's edges draw back and what lay round it is a weekly's page: the photo has been printed. s02c carries that page away to where it hangs in the train."""
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
import shared_lockers as S  # noqa: E402
import crisp  # noqa: E402
import cutout as C  # noqa: E402
import s01b  # noqa: E402

ROOT = K.ROOT
PUSH = (36.72, 37.12)         # into the phone
PRINT = (37.12, S.T1)         # the screen's edges draw back; the photo goes to dots
HOLD_N = 416                  # the frame the push happens in: between 36.4 and 37.2 the boy holds still, and all the lights that are going out have gone
CROP = (260, 320, 800, 450)   # round the phone: what stays in view once the push is under way, enlarged properly
SCREEN_BG = "#CDEFFB"         # the phone's screen in the 3D shot
PW, PH = 1920, 1920           # the photo's sheet: its blue goes on far enough to fill the panel when it is printed
SCREEN_H = 1040               # how much of it the phone's screen shows, from the middle
SHOE_INK = "#A84E27"          # the press's fourth ink: her shoes keep their brown
AD_W, AD_H = 1456, 1000       # the hanging ad's layout (tex_s02.her_ad)
PANEL = (40, 166, 610, AD_H - 206)
PAGE_S = E.W / AD_W           # the page once it fills the frame
PAGE_Y = -30.0
GOTH = "ZenKakuGothicNew-Black"
GB = "ZenKakuGothicNew-Bold"
MIN = "ShipporiMinchoB1-ExtraBold"
LOAFERS = ROOT / "assets" / "gen" / "cut" / "x01_loafers_cell.png"
BOY_HANDS = ROOT / "assets" / "gen" / "cut" / "h47_boy_phone.png"     # his hands and phone drawn for real, in place: they go over the frame when the camera is this close
PHOTO_K = 0.70                # the photo's size on the page, screen pixels to its own, once it sits in the panel
PRESS_CELL = 11.0             # the press's dots, in the photo's pixels
FINE_PITCH = 3.6              # dots closer than this on the screen beat against the pixels: there the page goes to the tones they add up to
FLAT_T = 36.92                # from here, with her cell out of view, the frame round the phone is flat paint with clean edges: enlarged this far, the frame's own lines have nothing left in them
FLAT_K = 3


def draw_photo(c):
    """The phone's photo of her cell, the same layout as the little one in the 3D shot (tex_s02.screen_cell): her loafers, the cell's frame, and above them her name scribbled out."""
    E.rect(c, 0, 0, PW, PH, SCREEN_BG)
    cw = min(PW * 0.86, SCREEN_H * 1.05)
    ch = cw * 0.78
    x0, y0 = (PW - cw) / 2, (PH - ch) / 2
    t = cw * 0.025
    for r in ((x0, y0, cw, t), (x0, y0 + ch - t, cw, t), (x0, y0, t, ch), (x0 + cw - t, y0, t, ch)):
        E.rect(c, *r, E.INK)
    sy, sh = y0 + ch * 0.07, ch * 0.055
    for k, (a, b) in enumerate(((0.08, 0.86), (0.05, 0.93), (0.11, 0.90))):
        E.rect(c, x0 + cw * a, sy + k * sh, cw * (b - a), sh * 1.15, E.INK)
    im = cv2.imread(str(LOAFERS), cv2.IMREAD_UNCHANGED)[214:848, 297:1238]
    icon = E.np_to_image(np.dstack([im[..., 2::-1], im[..., 3]]))
    iw = cw * 0.82
    ih = iw * icon.height() / icon.width()
    c.drawImageRect(icon, skia.Rect.MakeXYWH(x0 + (cw - iw) / 2, y0 + ch - t - ih - ch * 0.02, iw, ih), E.SAMPLING)


def snapshot(w, h, fn):
    s = skia.Surface(w, h)
    c = s.getCanvas()
    c.clear(E.col(E.PAPER))
    fn(c)
    return s.makeImageSnapshot().toarray(colorType=skia.ColorType.kRGBA_8888_ColorType, alphaType=skia.AlphaType.kOpaque_AlphaType)[..., :3].astype(np.float32) / 255


def flatten_frame(bgr):
    """The frame as flat paint: each area one of a few of its own colours, the edges between them drawn again smooth at FLAT_K times the size."""
    ms = cv2.pyrMeanShiftFiltering(bgr, 7, 13)
    lab = cv2.cvtColor(ms, cv2.COLOR_BGR2LAB).astype(np.float32)
    n = 10
    cv2.setRNGSeed(7)
    _, lb, _ = cv2.kmeans(lab.reshape(-1, 3), n, None, (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 40, 0.5), 3, cv2.KMEANS_PP_CENTERS)
    lb = lb.reshape(bgr.shape[:2])
    pal = np.array([bgr[lb == i].mean(0) for i in range(n)], np.float32)
    k = FLAT_K * 2
    hot = np.stack([cv2.GaussianBlur(cv2.resize((lb == i).astype(np.float32), None, fx=k, fy=k, interpolation=cv2.INTER_CUBIC), (0, 0), k * 0.75) for i in range(n)], -1)
    return cv2.resize(pal[hot.argmax(-1)], None, fx=0.5, fy=0.5, interpolation=cv2.INTER_AREA).astype(np.uint8)


def printed(rgb, cell=PRESS_CELL):
    """The same photo on a cheap press: three plates in dots, its ink solid. The film's own print (s01b.make_cover)."""
    h, w = rgb.shape[:2]
    ink = np.clip((0.24 - rgb.max(-1)) / 0.08, 0, 1).astype(np.float32)
    shoe = np.clip((rgb[..., 0] - rgb[..., 2] - 0.12) / 0.08, 0, 1).astype(np.float32)
    k = np.clip((0.48 - rgb.max(-1)) / 0.48, 0, 1).astype(np.float32) * (1 - ink)
    cy = np.clip(1 - rgb[..., 0] - k, 0, 1).astype(np.float32) * (1 - shoe) * 1.25
    s = skia.Surface(w, h)
    c = s.getCanvas()
    c.clear(E.col(E.PAPER))
    for p, color, ang, mult in ((shoe * 0.86, SHOE_INK, 0.0, False), (cy, E.CYAN, 15.0, True), (k, E.INK, 45.0, False)):
        b = cv2.GaussianBlur(p, (0, 0), cell * 0.5)
        s01b.dots(c, b, 1.0, cell, ang, (0, 0, w, h), 1.0, color, multiply=mult)
    c.drawImage(s01b.line_plate(ink, np.zeros_like(ink)), 0, 0)
    return s.makeImageSnapshot().toarray(colorType=skia.ColorType.kRGBA_8888_ColorType, alphaType=skia.AlphaType.kOpaque_AlphaType)[..., :3].astype(np.float32) / 255


def page_type(c):
    """The page round the panel: the same layout as every hanging ad in the train (tex_s02.her_ad)."""
    E.rect(c, 0, 0, AD_W, AD_H, E.PAPER)
    E.rect(c, 0, 0, AD_W, 132, E.INK)
    E.fit("週刊ライト", GOTH, 460, 88).draw(c, 40, 66, E.RIN, ax=0)
    E.fit("11月5日号 定価480円", GB, 420, 44).draw(c, AD_W - 40, 68, E.PAPER, ax=1)
    # in a vertical line a Latin A lies on its side: the full-width letter stands up like the kana round it
    E.fit("少女Ａの靴箱", MIN, 250, AD_H - 210, vertical=True).draw(c, AD_W - 175, 170 + (AD_H - 210) / 2, E.INK)
    E.fit("本誌だけが撮った一枚", GOTH, 120, AD_H - 250, vertical=True).draw(c, AD_W - 410, 190, E.INK, ay=0.0)
    E.rect(c, 690, 170, 110, 110, E.RIN)
    E.fit("独占", GOTH, 90, 90).draw(c, 745, 225, E.INK)
    E.fit("少女A", MIN, 130, 130).draw(c, 745, 375, E.INK)
    for k in range(5):
        E.rect(c, 700, 480 + k * 56, 90, 8, "#8C9095")


def panel_border(c, x, y, w, h, th):
    E.rect(c, x, y, w, th, E.INK)
    E.rect(c, x, y + h - th, w, th, E.INK)
    E.rect(c, x, y, th, h, E.INK)
    E.rect(c, x + w - th, y, th, h, E.INK)


def make_page(print_rgb):
    """The finished page, photo printed in its panel. 2 pixels to the page unit."""
    k = 2
    s = skia.Surface(AD_W * k, AD_H * k)
    c = s.getCanvas()
    c.scale(k, k)
    page_type(c)
    px, py, pw, ph = PANEL
    c.save()
    c.clipRect(skia.Rect.MakeXYWH(px, py, pw, ph))
    u = PHOTO_K / PAGE_S
    c.translate(px + pw / 2, py + ph / 2)
    c.scale(u, u)
    c.translate(-PW / 2, -PH / 2)
    arr = (print_rgb * 255 + 0.5).astype(np.uint8)
    c.drawImage(E.np_to_image(np.dstack([arr, np.full(arr.shape[:2], 255, np.uint8)])), 0, 0, E.SAMPLING_DOWN)
    c.restore()
    panel_border(c, px, py, pw, ph, 6)
    return s.makeImageSnapshot()


class PageArt:
    """What both sides of the cut share: the photo, flat and printed, and the page."""

    def __init__(self):
        self.flat = snapshot(PW, PH, draw_photo)
        self.print = printed(self.flat)
        self.page = make_page(self.print)
        # the same page seen from far off: the same tones, no dots. The photo's ink stays sharp
        ink = np.clip((0.24 - self.flat.max(-1)) / 0.08, 0, 1)[..., None]
        ink = cv2.GaussianBlur(ink, (0, 0), 1.0)[..., None]
        self.page_far = make_page(cv2.GaussianBlur(self.print, (0, 0), PRESS_CELL * 0.8) * (1 - ink) + self.flat * ink)
        # the dots of the press, on one lattice: where the print has come through yet
        yy, xx = np.mgrid[0:PH, 0:PW].astype(np.float32)
        a = math.radians(45.0)
        pitch = 34.0
        self.lattice = 0.5 + 0.25 * (np.cos(2 * np.pi * (xx * math.cos(a) + yy * math.sin(a)) / pitch) + np.cos(2 * np.pi * (-xx * math.sin(a) + yy * math.cos(a)) / pitch))

    def page_at(self, scale):
        """The page to draw at this many screen pixels to one of its own."""
        pitch = PRESS_CELL * PHOTO_K / PAGE_S * 2 * scale
        return self.page if pitch >= FINE_PITCH else self.page_far

    def photo_at(self, v):
        """The photo with the print coming through it in hard dots: v = 0 flat, 1 all print."""
        if v <= 0:
            arr = self.flat
        elif v >= 1:
            arr = self.print
        else:
            m = np.clip((v * 1.04 - self.lattice) * 18 + 0.5, 0, 1)[..., None]
            arr = self.flat * (1 - m) + self.print * m
        a8 = (arr * 255 + 0.5).astype(np.uint8)
        return E.np_to_image(np.dstack([a8, np.full(a8.shape[:2], 255, np.uint8)]))


def page_quad():
    """The page's corners on the screen once it fills the frame."""
    w, h = AD_W * PAGE_S, AD_H * PAGE_S
    return [(0.0, PAGE_Y), (w, PAGE_Y), (w, PAGE_Y + h), (0.0, PAGE_Y + h)]


class Lockers(seq3d.Seq3D):
    name = "s02b"
    shot = "lockers"
    t0, t1 = S.T0, S.T1
    lines = (4, 5, 6, 7)

    def setup(self):
        super().setup()
        self.hold = None

    def prepare(self):
        """Only a clip that reaches the push needs these."""
        bgr = cv2.imread(str(ROOT / "work" / "render" / "lockers_png" / f"f{HOLD_N:05d}.png"))
        rgba = np.dstack([bgr[..., ::-1], np.full(bgr.shape[:2], 255, np.uint8)])
        self.hold = E.np_to_image(rgba)
        # the screen, as the frame has it
        roi = bgr[500:640, 500:720].astype(np.int32)
        m = (roi[..., 0] > 220) & (roi[..., 1] > 190) & (roi[..., 2] > 150)
        box = cv2.boxPoints(cv2.minAreaRect(np.column_stack(np.nonzero(m)[::-1]).astype(np.float32))) + np.array([500, 500])
        order = np.argsort(box[:, 1])
        top, bot = box[order[:2]], box[order[2:]]
        tl, tr = top[np.argsort(top[:, 0])]
        bl, br = bot[np.argsort(bot[:, 0])]
        self.quad = [tuple(float(v) for v in q) for q in (tl, tr, br, bl)]
        self.tilt = math.degrees(math.atan2(tr[1] - tl[1], tr[0] - tl[0]))
        self.centre = tuple(float(v) for v in (tl + tr + br + bl) / 4)
        qw, qh = float(np.linalg.norm(tr - tl)), float(np.linalg.norm(bl - tl))
        self.qw, self.qh = qw, qh
        self.full = max(E.W / qw, E.H / qh) * 1.04
        self.photo_scale = qw * self.full / PW
        x, y, w, h = CROP
        cache = ROOT / "work" / "cache" / "s02b_phone_crisp.png"
        if cache.exists():
            big = cv2.imread(str(cache), cv2.IMREAD_UNCHANGED)
        else:
            big = crisp.upscale(np.dstack([rgba[y:y + h, x:x + w, :3].astype(np.float32) / 255, np.ones((h, w), np.float32)]), 4)
            cv2.imwrite(str(cache), big)
        self.big = E.np_to_image(big)
        cache = ROOT / "work" / "cache" / "s02b_phone_flat.png"
        if cache.exists():
            flat = cv2.imread(str(cache))
        else:
            flat = flatten_frame(bgr[y:y + h, x:x + w])
            cv2.imwrite(str(cache), flat)
        self.flat_paint = E.np_to_image(np.dstack([flat[..., ::-1], np.full(flat.shape[:2], 255, np.uint8)]))
        # the drawn hands: their screen goes, and is laid exactly on the frame's. Its outline made fresh at the new size
        im, mask = C.key_magenta(C.load(BOY_HANDS))
        pts = np.column_stack(np.nonzero((mask > 0.5) & (C.load(BOY_HANDS)[..., 3] > 0.5))[::-1]).astype(np.float32)
        box = cv2.boxPoints(cv2.minAreaRect(pts))
        order = np.argsort(box[:, 1])
        top, bot = box[order[:2]], box[order[2:]]
        tl, tr = top[np.argsort(top[:, 0])]
        bl, br = bot[np.argsort(bot[:, 0])]
        self.boy_centre = tuple(float(v) for v in (tl + tr + br + bl) / 4)
        self.boy_tilt = math.degrees(math.atan2(tr[1] - tl[1], tr[0] - tl[0]))
        self.boy_k = self.qw / float(np.linalg.norm(tr - tl))
        # whatever is left of the green goes, and whatever the outline mixed with the keys is ink: nothing but the drawing's own colours may reach the edge
        green = (im[..., 1] > np.maximum(im[..., 0], im[..., 2]) + 0.04) & (im[..., 3] < 1.0) | (im[..., 1] > np.maximum(im[..., 0], im[..., 2]) + 0.12)
        im[green, 3] = 0
        edge = cv2.dilate((im[..., 3] < 0.9).astype(np.uint8), np.ones((3, 3), np.uint8)).astype(bool)
        tinted = np.minimum(im[..., 0], im[..., 2]) - im[..., 1] > 0.10
        im[edge | (tinted & (mask > 0.02)), :3] = np.array((0x11, 0x1A, 0x36), np.float32) / 255
        # the same light as the frame the drawing goes over: its skin and its dark, as the frame has them at the back of his hand
        sample = np.median(bgr[580:596, 508:526, ::-1].reshape(-1, 3), axis=0).astype(np.float32) / 255
        cx0, cy0 = self.boy_centre
        px, py = int(cx0 + (517 - self.centre[0]) / self.boy_k), int(cy0 + (588 - self.centre[1]) / self.boy_k)
        own = np.median(im[py - 12:py + 12, px - 12:px + 12, :3].reshape(-1, 3), axis=0)
        im[..., :3] = np.clip(im[..., :3] * (sample / np.maximum(own, 0.02)), 0, 1)
        hands = crisp.upscale(np.dstack([im[..., :3], np.ones(im.shape[:2], np.float32)]), 3)
        al = cv2.GaussianBlur(cv2.resize(im[..., 3], None, fx=3, fy=3, interpolation=cv2.INTER_CUBIC), (0, 0), 2.0)
        hands[..., 3] = (np.clip((al - 0.5) * 5 + 0.5, 0, 1) * 255 + 0.5).astype(np.uint8)
        self.boy = E.np_to_image(hands)
        self.art = PageArt()
        self.flat_img = self.art.photo_at(0.0)

    def draw_push(self, c, t):
        x = E.seg(t, *PUSH)
        z = math.exp(math.log(self.full) * E.ease_io(x, 2.3))
        w = (z - 1) / (self.full - 1)
        cx, cy = self.centre
        c.save()
        c.translate(cx + (960 - cx) * w, cy + (540 - cy) * w)
        c.rotate(-self.tilt * w)
        c.scale(z, z)
        c.translate(-cx, -cy)
        c.drawImage(self.hold, 0, 0, E.SAMPLING)
        bx, by, bw, bh = CROP
        c.save()
        c.clipRect(skia.Rect.MakeXYWH(bx + 2, by + 2, bw - 4, bh - 4))
        c.translate(bx, by)
        if t < FLAT_T:
            c.scale(0.25, 0.25)
            c.drawImage(self.big, 0, 0, E.SAMPLING_DOWN)
        else:
            c.scale(1 / FLAT_K, 1 / FLAT_K)
            c.drawImage(self.flat_paint, 0, 0, E.SAMPLING)
        c.restore()
        if t >= FLAT_T:
            c.save()
            c.translate(cx, cy)
            c.rotate(self.tilt - self.boy_tilt)
            c.scale(self.boy_k / 3, self.boy_k / 3)
            c.translate(-self.boy_centre[0] * 3, -self.boy_centre[1] * 3)
            c.drawImage(self.boy, 0, 0, E.SAMPLING_DOWN if z * self.boy_k < 3 else E.SAMPLING)
            c.restore()
        # the screen itself is always the real photo, at any size, in a clean edge of the phone's own dark
        c.save()
        c.translate(cx, cy)
        c.rotate(self.tilt)
        E.rect(c, -self.qw / 2 - 3.2, -self.qh / 2 - 3.2, self.qw + 6.4, self.qh + 6.4, "#1A2342", radius=2.5)
        c.restore()
        c.save()
        c.concat(E.quad_matrix((PW, SCREEN_H), self.quad))
        c.clipRect(skia.Rect.MakeWH(PW, SCREEN_H))
        c.translate(0, -(PH - SCREEN_H) / 2)
        c.drawImage(self.flat_img, 0, 0, E.SAMPLING_DOWN if z < 8 else E.SAMPLING)
        c.restore()
        c.restore()

    def draw_print(self, c, t):
        v = E.ease_io(E.seg(t, *PRINT), 1.8)
        c.clear(E.col(E.PAPER))
        # the page has lain under the screen all along
        c.save()
        c.translate(0, PAGE_Y)
        c.scale(PAGE_S / 2, PAGE_S / 2)
        c.drawImage(self.art.page, 0, 0, E.SAMPLING_DOWN)
        c.restore()
        px, py, pw, ph = PANEL
        x0, y0, x1, y1 = px * PAGE_S, PAGE_Y + py * PAGE_S, (px + pw) * PAGE_S, PAGE_Y + (py + ph) * PAGE_S
        s0 = self.photo_scale
        s = E.lerp(s0, PHOTO_K, v)
        # the window's edges start just outside the frame
        a = (-40.0, -40.0, E.W + 40.0, E.H + 40.0)
        wx0, wy0, wx1, wy1 = E.lerp(a[0], x0, v), E.lerp(a[1], y0, v), E.lerp(a[2], x1, v), E.lerp(a[3], y1, v)
        c.save()
        c.clipRect(skia.Rect.MakeLTRB(wx0, wy0, wx1, wy1))
        c.translate((wx0 + wx1) / 2, (wy0 + wy1) / 2)
        c.scale(s, s)
        c.translate(-PW / 2, -PH / 2)
        c.drawImage(self.art.photo_at(v), 0, 0, E.SAMPLING_DOWN)
        c.restore()
        th = 6 * PAGE_S
        panel_border(c, wx0, wy0, wx1 - wx0, wy1 - wy0, th)

    def overlay(self, c, t):
        if t >= PUSH[0]:
            if self.hold is None:
                self.prepare()
            if t < PRINT[0]:
                self.draw_push(c, t)
            else:
                self.draw_print(c, t)
        super().overlay(c, t)
