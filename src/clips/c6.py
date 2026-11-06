"""Clip 6: she takes the bar off herself. Empty eyes, one bar long. Then the light arrives a syllable at a time."""
import json
import math
import os
import sys
from pathlib import Path

import cv2
import numpy as np
import skia

sys.path.insert(0, str(Path(__file__).parent))
import common as K  # noqa: E402
import engine as E  # noqa: E402
import bar as B  # noqa: E402
import cel  # noqa: E402
import crisp  # noqa: E402
import cutout as C  # noqa: E402
import eye_anim as EA  # noqa: E402
import finale as F  # noqa: E402
import handkit as HK  # noqa: E402
from timeline import beat_time  # noqa: E402

ROOT = K.ROOT
T0, T1 = 193.93, 206.0
# paintings of the opened eyes: file, and the part of the face picture it covers
_MAG = (384, 207, 1152, 719)
_FULL = (0, 0, 1536, 1024)
EYE_SOURCES = {"api_a_0": ("work/eye/api_a_0.png", _FULL), "e03": ("assets/gen/raw/e03_paintover.png", _FULL),
               "v2_glass_0": ("work/eye/v2_glass_0.png", _MAG), "v2_glass_1": ("work/eye/v2_glass_1.png", _MAG),
               "v2_stroke_0": ("work/eye/v2_stroke_0.png", _MAG), "v2_stroke_1": ("work/eye/v2_stroke_1.png", _MAG),
               "v3_a_0": ("work/eye/v3_a_0.png", _MAG), "v3_a_1": ("work/eye/v3_a_1.png", _MAG),
               "v3_c_0": ("work/eye/v3_c_0.png", _MAG), "v3_c_1": ("work/eye/v3_c_1.png", _MAG)}
EYE_SOURCES["v4_a1_1"] = ("work/eye/v4_a1_1.png", _MAG)
EYE_SOURCES["v4_a0"] = ("work/eye/v4_a0.png", _MAG)
EYE_DEFAULT = "v4_a1_1"   # chosen after three rounds of blind judging; see docs/进度.md
TAKE = 195.77
# her hand wiping: one drawing made from her character sheet (assets/gen/cut/h50_wipe.png; work/eye/key6/gen_a3.py), at its widest no wider than her cuff, as on the sheet. The back of her left hand is towards us;
# she comes up from below, so only her hand crosses her face, never her forearm. Everything below the knuckles is that drawing, untouched; the
# fingers are the same drawing bent along their length (see hand_bend), so they trail and relax without the hand ever changing into another picture.
HAND_S = 0.86
HAND_AX = np.array((-0.45, -0.89)) / math.hypot(0.45, 0.89)
HAND_PERP = np.array((0.89, -0.45)) / math.hypot(0.45, 0.89)
HAND_O = np.array((800.0, 690.0))
# anchor = a point on the hand's far (right) outline, where the bar's centre line crosses it
HAND_AT = (677.0, 300.0)
# along the axis, in the drawing's pixels (larger = nearer the tips): where the fingers bend from, and where the lines between them come to an end
KNUCKLE_C, LINES_END_C = -560.0, -425.0
FINGER_L = 320.0
BEND_STEP = 3
HAND_LIGHT = (0.215, 0.275, 0.44)


def hand_clean(h):
    """The lines between the fingers are short and near the tips only: what lies inside the outline is painted out below that, each stroke coming to a
    point. The line of her thumb stays. Navy reads as a heavy black band in the dark: it is lifted clear of the ink."""
    h = h.copy()
    rgb, al = h[..., :3], h[..., 3]
    H_, W_ = al.shape
    yy, xx = np.mgrid[0:H_, 0:W_].astype(np.float32)
    c = xx * HAND_AX[0] + yy * HAND_AX[1]
    v = xx * HAND_PERP[0] + yy * HAND_PERP[1] - (HAND_O @ HAND_PERP)
    sil = cv2.erode((al > 0.5).astype(np.uint8), cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (27, 27)))
    ink = (rgb.max(-1) < 0.5).astype(np.uint8)
    # how deep inside a stroke each pixel is, negative in the soft fringe outside it: the painting-out eats in from the edges, so the stroke thins to a point
    depth = cv2.distanceTransform(ink, cv2.DIST_L2, 5) - cv2.distanceTransform(1 - ink, cv2.DIST_L2, 5)
    skin = np.median(rgb[(rgb[..., 0] > 0.95) & (rgb[..., 2] < 0.92) & (rgb[..., 2] > 0.75) & (al > 0.9)], axis=0)
    need = -3.0 + 9.0 * np.clip((LINES_END_C + 45 - c) / 90, 0, 1) + (c < LINES_END_C - 45) * 100
    gone = np.clip(need - depth, 0, 1) * ((sil > 0) & (depth < 12) & (c > -800) & (v < 30))
    gone = cv2.GaussianBlur(gone.astype(np.float32), (0, 0), 0.6)[..., None]
    rgb[...] = rgb * (1 - gone) + skin * gone
    nv = np.clip((rgb[..., 2] - rgb[..., 0] - 0.03) / 0.08, 0, 1)[..., None] * (rgb.max(-1) < 0.6)[..., None]
    rgb[...] = rgb + (np.array((0x50, 0x5C, 0x90), np.float32) / 255 - np.array((0x29, 0x2F, 0x52), np.float32) / 255) * nv
    return h


def hand_bend(h, deg):
    """The fingers curve along their length: deg is how far the tips have turned, positive towards her thumb (they trail as the hand is dragged left), negative
    forwards (they relax). A bend, not a stretch: lengths along the fingers and the widths of lines stay as drawn."""
    H_, W_ = h.shape[:2]
    yy, xx = np.mgrid[0:H_, 0:W_].astype(np.float32)
    v0 = -12.0     # the middle of the fingers
    base = KNUCKLE_C - HAND_O @ HAND_AX
    U = (xx - HAND_O[0]) * HAND_AX[0] + (yy - HAND_O[1]) * HAND_AX[1] - base
    V = (xx - HAND_O[0]) * HAND_PERP[0] + (yy - HAND_O[1]) * HAND_PERP[1] - v0
    th = math.radians(deg)
    us = np.linspace(0, FINGER_L * 1.6, 400)
    ang = th * (us / FINGER_L) ** 1.6
    su = np.r_[0, np.cumsum(np.cos(ang[:-1]) * np.diff(us))]
    sv = np.r_[0, np.cumsum(np.sin(ang[:-1]) * np.diff(us))]
    u = np.maximum(U, 0).copy()
    v = V.copy()
    for _ in range(7):
        a = np.interp(u, us, ang)
        eu, ev = U - np.interp(u, us, su), V - np.interp(u, us, sv)
        ca, sa = np.cos(a), np.sin(a)
        u = np.clip(u + eu * ca + ev * sa, 0, us[-1])
        v = -eu * sa + ev * ca
    m = U > 0
    u_, v_ = np.where(m, u, U), np.where(m, v, V)
    mx = HAND_O[0] + (u_ + base) * HAND_AX[0] + (v_ + v0) * HAND_PERP[0]
    my = HAND_O[1] + (u_ + base) * HAND_AX[1] + (v_ + v0) * HAND_PERP[1]
    return cv2.remap(h, mx.astype(np.float32), my.astype(np.float32), cv2.INTER_CUBIC, borderMode=cv2.BORDER_CONSTANT, borderValue=(0, 0, 0, 0)).clip(0, 1)


LIGHT = K.syllable_times(55, "bo")[0]
LAST = 200.38
HOOK_DROP = 200.90
CUT = 201.40
SCALE = 1080 / 1024
OX = (1920 - 1536 * SCALE) / 2

# The band comes back at CUT. Same drawing (p05), same camera: her colour comes out of her eyes in hard steps, on twos. She stays this close, in full colour, for a second and a half: the camera
# creeping in, the wind rising through her hair drawing by drawing, the words and scraps of the bar carried past, the sky's streaks running at the edges, the glints in her eyes going on and off.
# The wind gets too strong: she shuts her eyes (Codex's drawings), and with them shut, on a beat, a hard cut to the bust portrait, drawn whole by Codex (assets/gen/end, made by
# work/eye/key6/build_end.py and build_a3.py). Her eyes open on the next beat, already holding the light from the close-up. 少 and 女A fly past. She blinks once, her head tilting a little under the
# blink, and a beat later the small smile comes up and stays, for about 1.8 s to the end of the shot. The wind never quite stops: to the end it blows her hair and the scarf's end together.
F_CUT = int(round(CUT * E.FPS))
F_BUST = int(round(beat_time(438) * E.FPS))     # 202.497
F_OPEN = int(round(beat_time(439) * E.FPS))     # 202.959: her eyes are open on this frame
F_BLINK = int(round((beat_time(440) + beat_time(441)) / 2 * E.FPS))    # 203.651: the lids are down on this frame
F_SMILE = int(round((beat_time(441) + beat_time(442)) / 2 * E.FPS))    # 204.113: one beat after the blink, as it has always been
# how long each drawing of the wind stays, for the drawings in layout3.json: the close-up runs from F_CUT to F_BUST, and the bust's last one is up before the blink
CLOSE_HOLDS = (4, 3, 3, 3, 3, 3, 3, 3, 3, 3, 2)
BUST_HOLDS = (4, 4, 4, 4, 4, 5, 7, 10)
# the close-up's lids, in frames before the cut, on twos. And the bust's lids before F_OPEN
CLOSE_LIDS = (("half", 6), ("near", 4), ("closed", 2))
OPEN_LIDS = (("half", 2),)
# the steps of the light: the iris's own ramp, dark and light ends. Each colour passes through these before it is her own
BANDS = [("#0B5C72", "#35A7BC"), ("#2A97AE", "#C2F0F0")]
LIGHT_STEPS = 6   # steps of two frames: full colour by about 0.35 s
BAND_DT = 0.7     # in steps of two frames
# the light's front: one oval, the shape of her iris, round the point between her eyes. It already holds both eyes when it first shows,
# so there is never a shape round each eye. Before it, on the first step, only the whites of her eyes
LIGHT_R0, LIGHT_V, LIGHT_ASPECT = 430.0, 173.0, 1.3
# the bust on screen: the point between her eyes is held here, the scale creeping up; picture at or under 1:1 so the lines stay crisp
BUST_AT = (770.0, 640.0, 770.0, 676.0)   # screen x, y at the cut, x, y at the end
BUST_S = (0.93, 0.975)
SKY_S = 0.55

SYL = [s["t"] for s in K.LYRICS[55]["syl"]][:11]
EYES = [(543.5, 463.5), (992.5, 463.5)]
RX, RY = 80.5, 105.5


def paint_close(raw):
    """The close-up's drawing as the film shows it, from a cut-out of Codex's picture: returns it before its cel tones, after them, and after them at twice the size."""
    # one dark smudge the generator left under the lower hair clip: only that, painted out in the hair's colour
    im = raw.copy()
    # the cut-out keeps its magenta key under zero alpha, which resizing would bleed into the edges: make it the ink's black
    im[im[..., 3] == 0, :3] = 0
    for Y in range(200, 227):
        for X in range(362, 409):
            if 3 * (Y - 150) > 76 + 0.449 * 3 * (X - 300) and raw[Y, X, :3].mean() < 0.6:
                im[Y, X, :3] = cel.tone("#FEDF56")
    im0 = im.copy()
    im = cel.add_cel(im, drop=34, hair_inset=30)
    # the whites of the eyes get one clean hard edge, like everything else in the drawing
    wh = np.zeros(im.shape[:2], np.uint8)
    for ex, ey in EYES:
        cv2.ellipse(wh, (int(ex), int(ey)), (175, 150), 0, 0, 360, 1, -1)
    lum0 = im[..., :3].mean(-1)
    w_ = np.clip((cv2.GaussianBlur(im[..., 2], (0, 0), 1.5) - 0.925) * 40 + 0.5, 0, 1)[..., None]
    skin_ = np.median(im[(wh > 0) & cel.near(im[..., :3], "#FDE8DA", 0.05)][:, :3], axis=0)
    hard = skin_ * (1 - w_) + np.array([1.0, 1.0, 1.0], np.float32) * w_
    im[..., :3] = np.where(((wh > 0) & (lum0 > 0.62))[..., None], hard, im[..., :3])
    # worked at twice size, so the slow push towards the eyes stays crisp; no unsharp mask, which rings every line in white (docs/问题根因清单.md)
    big = crisp.upscale(im, k=2).astype(np.float32) / 255
    return im0, im, big


def lid_layer(patch, im0, im1):
    """Codex's eyes laid into a close-up drawing before its colour steps, so her hair's shadow falls on the new skin the same way. Only what changed is kept: uint8 at twice the size, and its corner."""
    a = patch[..., 3:4]
    raw2 = im0.copy()
    raw2[..., :3] = raw2[..., :3] * (1 - a) + patch[..., :3] * a
    out = cel.add_cel(raw2, drop=34, hair_inset=30)
    changed = cv2.dilate((np.abs(out[..., :3] - im1[..., :3]).max(-1) > 0.004).astype(np.uint8), np.ones((5, 5), np.uint8))
    changed |= (a[..., 0] > 0).astype(np.uint8)
    ys, xs = np.nonzero(changed)
    x0, x1, y0, y1 = max(xs.min() - 8, 0), xs.max() + 8, max(ys.min() - 8, 0), ys.max() + 8
    out[..., 3] = cv2.GaussianBlur(changed.astype(np.float32), (0, 0), 0.7) * out[..., 3]
    return crisp.upscale(out[y0:y1, x0:x1], k=2), (int(x0), int(y0))


class OpenEye(E.Clip):
    name = "c6"
    t0, t1 = T0, T1

    def setup(self):
        raw = C.load(ROOT / "assets" / "gen" / "cut" / "p05_face_close.png")
        self.im0, im, big = paint_close(raw)
        self.full = E.np_to_image(big)
        # before the band returns she is one colour, the colour of a dark room; only her eyes are not
        self.dark = E.np_to_image(K.duotone(big))
        self.big, self.im1 = big, im
        # exact iris shape, from the picture itself
        r, g, b = im[..., 0], im[..., 1], im[..., 2]
        ir = ((g > r + 0.12) & (b > r + 0.12) & (g < 0.72)).astype(np.float32)
        ir = cv2.morphologyEx(ir, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
        ir = cv2.GaussianBlur(ir, (0, 0), 0.8)
        src_path, region = EYE_SOURCES[os.environ.get("C6_EYE", EYE_DEFAULT)]
        self.anim = EA.EyeAnim(cv2.imread(str(ROOT / src_path)), region, ir, EYES, SYL, SYL[10], CUT)
        # the eye areas, for the eyelid when she blinks: lash, white and iris, but not hair or skin
        skin_or_hair = cel.near(raw[..., :3], "#FDE8DA", 0.08) | cel.near(raw[..., :3], "#FEDB52", 0.12) | (raw[..., 3] < 0.5)
        eye = (~skin_or_hair).astype(np.uint8)
        keep = np.zeros(eye.shape, np.uint8)
        for ex, ey in EYES:
            box = np.zeros(eye.shape, np.uint8)
            box[int(ey - 165):int(ey + 130), int(ex - 185):int(ex + 185)] = 1
            n_, lab, st, _ = cv2.connectedComponentsWithStats(eye & box, connectivity=8)
            if n_ > 1 and lab[int(ey), int(ex)] > 0:
                comp = (lab == lab[int(ey), int(ex)]).astype(np.uint8)
                # hair outlines touch the lash: only what lies inside an oval round the eye counts as the eye
                oval_m = np.zeros(eye.shape, np.uint8)
                cv2.ellipse(oval_m, (int(ex), int(ey - 8)), (158, 146), 0, 0, 360, 1, -1)
                keep |= comp & oval_m
        k_ = cv2.dilate(keep, np.ones((5, 5), np.uint8)).astype(np.float32)
        k_ = cv2.GaussianBlur(k_, (0, 0), 0.8)
        emask = np.zeros((*k_.shape, 4), np.float32)
        emask[..., :3] = 1
        emask[..., 3] = k_
        self.eye_mask = E.np_to_image(emask)
        lum = im[..., :3].mean(-1)
        spec = json.loads((ROOT / "assets" / "gen" / "bars.json").read_text(encoding="utf-8"))["p05_face_close"]
        self.bar = B.Bar(*spec)
        self.bar_blank = B.Bar(*spec, text=False) if False else None
        self.spec = spec
        # her hand. The sleeve runs on past the edge of the picture, soft cloth easing out towards the elbow
        self.hand0 = hand_clean(C.load(ROOT / "assets" / "gen" / "cut" / "h50_wipe.png"))
        self.arm = self._hand_layers(HK.extrude(self.hand0, (0.45, 0.89), loose=0.5))
        self.wipe = {}
        self.build_final()
        self.lyric = K.Strip("何番目でも", K.chars_of(54, "何番目でも"), size=44)
        self.lyric1 = K.Strip("何番目でも", [K.LYRICS[54]["chars"][i]["t"] for i in range(5)], size=44)
        self.sung = K.Strip("僕が僕であるために", K.chars_of(55, "僕が僕であるために"), size=76, pad=20)
        self.q = E.Type("？", "ShipporiMinchoB1-ExtraBold", 76)
        # bar drawn once to a strip, so it can be peeled as a single piece of tape
        cx, cy, ln, th, ang, _ = spec
        self.strip_w, self.strip_h = int(ln * 1.1), int(th * 1.5)
        surf = skia.Surface(self.strip_w, self.strip_h)
        cv_ = surf.getCanvas()
        cv_.clear(skia.Color4f(0, 0, 0, 0))
        cv_.save()
        cv_.translate(self.strip_w / 2 - cx, self.strip_h / 2 - cy)
        self.bar.draw(cv_)
        cv_.restore()
        self.strip = surf.makeImageSnapshot()
        arr = self.strip.toarray(colorType=skia.ColorType.kRGBA_8888_ColorType, alphaType=skia.AlphaType.kUnpremul_AlphaType).copy()
        arr[..., 0], arr[..., 1], arr[..., 2] = 0x24, 0x28, 0x36   # its back is a plain dark grey
        self.strip_back = E.np_to_image(arr)
        self.strip_cx, self.strip_cy, self.strip_ang = cx, cy, ang
        self.strip_np = self.strip.toarray(colorType=skia.ColorType.kRGBA_8888_ColorType, alphaType=skia.AlphaType.kUnpremul_AlphaType).copy()
        self.pieces = F.torn_pieces(self.bar)
        # only the pieces with her handwriting on them: 女A and 少. A blank scrap of black is just a dirty speck on the sky
        self.pieces["bust"] = self.pieces["bust"][:2]

    def face(self, c, t):
        c.save()
        c.translate(OX, 0)
        c.scale(SCALE / 2, SCALE / 2)
        c.drawImage(self.dark if t < CUT else self.full, 0, 0, E.SAMPLING_DOWN)
        c.restore()

    def eyes(self, c, t):
        """The finishing stroke: see eye_anim.py. The irises are worked at twice picture size to stay sharp."""
        for i in range(2):
            rgba, (ox, oy) = self.anim.frame(i, t)
            img = E.np_to_image(rgba)
            c.save()
            c.translate(OX, 0)
            c.scale(SCALE, SCALE)
            c.translate(ox, oy)
            c.scale(1 / EA.SS, 1 / EA.SS)
            c.drawImage(img, 0, 0, E.SAMPLING_DOWN)
            c.restore()

    def draw_bar_flat(self, c, clip_left=None, clip_right=None):
        """Bar in screen coordinates, optionally only the part between two image x positions (along the bar)."""
        cx, cy, ang = self.strip_cx, self.strip_cy, self.strip_ang
        c.save()
        c.translate(OX, 0)
        c.scale(SCALE, SCALE)
        c.translate(cx, cy)
        c.rotate(ang)
        if clip_left is not None or clip_right is not None:
            c.clipRect(skia.Rect.MakeLTRB(clip_left if clip_left is not None else -5000, -2000,
                                          clip_right if clip_right is not None else 5000, 2000))
        c.translate(-self.strip_w / 2, -self.strip_h / 2)
        c.drawImage(self.strip, 0, 0, E.SAMPLING)
        c.restore()

    def take_off(self, c, t):
        """She wipes it off herself. The bar is marker ink: her hand drags across it, right to left, the opposite way to how
        it was scrawled on, and the ink comes away under it. So the ink ends under her hand, and shows only as a slight
        unevenness along the hand's far outline. Her hand comes up from below, so her eyes come clear beside it, and it leans
        over as it crosses, as a hand does when the elbow stays low. Hand and ink move on twos."""
        L = self.spec[2]
        front0 = L * 0.5 + 150                           # all of the bar's far end is under her fingers: none of it pops away
        end_x = OX + (self.strip_cx + front0) * SCALE
        start_y = self.spec[1] * SCALE
        hs = HAND_S
        q = math.floor(t * 15) / 15
        if q < TAKE:
            self.draw_bar_flat(c)
            u = E.seg(q, TAKE - 0.60, TAKE - 0.10)
            if u > 0:
                k = E.ease_out(u, 2.6)
                self.wipe_hand(c, 0, E.lerp(end_x + 330, end_x, k), E.lerp(start_y + 860, start_y, k), hs, E.lerp(12, 7, k))
            return
        u = (q - TAKE) / 0.46
        if u >= 1.6:
            return
        e = E.ease_io(min(u, 1.0), 1.5)
        front = front0 - (front0 + L * 0.5 + 250) * e    # where the hand is on the bar's centre line, in the strip's own pixels
        rot = 7 - 23 * e
        # the fingers ride a shallow arc; after the fast part they trail behind the hand, then catch up
        tx = OX + (self.strip_cx + front) * SCALE
        ty = start_y - 26 * math.sin(math.pi * e)
        # the fingers lag as the hand speeds up, then swing on past straight as it stops
        key = 24 * E.ease_io(E.clamp01(e / 0.22), 2.0) * (1 - E.ease_io(E.clamp01((e - 0.55) / 0.45), 2.0)) - 8 * E.ease_io(E.clamp01((e - 0.75) / 0.25), 2.0)
        if u < 1.0:
            h, w = self.strip_np.shape[:2]
            cx, cy, ang = self.strip_cx, self.strip_cy, self.strip_ang
            # her hand's far outline, in the strip's own pixels: how far the ink has gone along each row
            r_, a_ = math.radians(rot), math.radians(-ang)
            p = (self.hand_pose(key)["outline"] - np.array(HAND_AT, np.float32)) * hs
            sx = (p[:, 0] * math.cos(r_) - p[:, 1] * math.sin(r_) + tx - OX) / SCALE - cx
            sy = (p[:, 0] * math.sin(r_) + p[:, 1] * math.cos(r_) + ty) / SCALE - cy
            ex = sx * math.cos(a_) - sy * math.sin(a_) + w / 2
            ey = sx * math.sin(a_) + sy * math.cos(a_) + h / 2
            far = np.full(h, -1e9, np.float32)
            rows = np.round(ey).astype(int)
            ok = (rows >= 0) & (rows < h)
            np.maximum.at(far, rows[ok], ex[ok])
            have = np.flatnonzero(far > -1e8)
            far = np.interp(np.arange(h), have, far[have]) if len(have) else np.full(h, w + 500.0)
            far = cv2.GaussianBlur(far.astype(np.float32).reshape(-1, 1), (0, 0), 6).ravel()
            xs = np.arange(w, dtype=np.float32)[None, :]
            # the ink ends under her hand. Nothing shows past it, nothing floats free
            edge = far[:, None] - 16
            layer = self.strip_np.copy()
            layer[..., :3][xs > far[:, None] - 24] = (9, 9, 13)
            layer[..., 3] = (layer[..., 3] * np.clip((edge - xs) / 2.5, 0, 1)).astype(np.uint8)
            img_ = E.np_to_image(layer)
            c.save()
            c.translate(OX, 0)
            c.scale(SCALE, SCALE)
            c.translate(cx, cy)
            c.rotate(ang)
            c.translate(-w / 2, -h / 2)
            c.drawImage(img_, 0, 0, E.SAMPLING)
            c.restore()
        if u > 1.0:
            # then it falls away, down the way the arm came, the fingers relaxing
            v = min((u - 1.0) / 0.6, 1.0)
            tx += 330 * v ** 1.7
            ty += 1050 * v ** 1.7
            rot += 10 * v
            key = -8 - 14 * min(v / 0.5, 1.0)
        self.wipe_hand(c, key, tx, ty, hs, rot)

    def _hand_layers(self, h):
        sh = np.zeros(h.shape, np.float32)
        sh[..., :3] = (0.015, 0.02, 0.05)
        sh[..., 3] = h[..., 3]
        # a tone darker than her face, so the hand reads as a shape in front of it, and not as part of it
        return E.np_to_image(K.duotone(h, light=HAND_LIGHT)), E.np_to_image(sh)

    def hand_pose(self, bend):
        """The drawing with its fingers bent, and its outline. Poses come in small steps and are kept."""
        key = int(round(bend / BEND_STEP)) * BEND_STEP
        v = self.wipe.get(key)
        if v is None:
            h = hand_bend(self.hand0, key)
            cs, _ = cv2.findContours((h[..., 3] > 0.5).astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
            # only the fingers change: the picture is cut to them, and lies over the arm's picture
            yy, xx = np.mgrid[0:h.shape[0], 0:h.shape[1]].astype(np.float32)
            f = h.copy()
            f[..., 3] *= np.clip((xx * HAND_AX[0] + yy * HAND_AX[1] - KNUCKLE_C - 4) / 3, 0, 1)
            img, sh = self._hand_layers(f)
            v = self.wipe[key] = dict(img=img, sh=sh, outline=np.concatenate(cs)[:, 0].astype(np.float32))
        return v

    def wipe_hand(self, c, bend, x, y, hs, rot=0.0):
        v = self.hand_pose(bend)
        arm, arm_sh = self.arm
        ax, ay = HAND_AX
        cc = KNUCKLE_C + 8
        px, py = -ay, ax
        x0, y0 = ax * cc, ay * cc
        # the arm's picture holds the straight fingers too: only what lies below the knuckles is used
        below = F.path_of([(x0 + px * 6000, y0 + py * 6000), (x0 - px * 6000, y0 - py * 6000),
                           (x0 - px * 6000 - ax * 6000, y0 - py * 6000 - ay * 6000), (x0 + px * 6000 - ax * 6000, y0 + py * 6000 - ay * 6000)])

        def pics(a, f):
            c.save()
            c.rotate(rot)
            c.scale(hs, hs)
            c.translate(-HAND_AT[0], -HAND_AT[1])
            c.save()
            c.clipPath(below, True)
            c.drawImage(a, 0, 0, E.SAMPLING)
            c.restore()
            c.drawImage(f, 0, 0, E.SAMPLING)
            c.restore()
        c.save()
        c.translate(x + 12, y + 18)
        c.saveLayer(skia.Rect.MakeLTRB(-4000, -4000, 6000, 6000), skia.Paint(Alphaf=0.42))
        pics(arm_sh, v["sh"])
        c.restore()
        c.restore()
        c.save()
        c.translate(x, y)
        pics(arm, v["img"])
        c.restore()

    def build_final(self):
        """The ending. Close-up: p05's own colours, its irises, and Codex's closed eyes laid into it. Bust: Codex's pictures, registered on the master."""
        big = self.big
        crop = big
        lum = crop[..., :3].mean(-1)
        self.band_faces = []
        for dk, lt in BANDS:
            d, l_ = [np.array([int(h[i:i + 2], 16) for i in (1, 3, 5)], np.float32) / 255 for h in (dk, lt)]
            out = (d[None, None] + (l_ - d)[None, None] * lum[..., None]) * np.clip(lum[..., None] / 0.15, 0, 1)
            self.band_faces.append(E.np_to_image(np.dstack([out, crop[..., 3]])))
        # when the light arrives at each pixel, in steps of two frames
        yy, xx = np.mgrid[0:1024, 0:1536].astype(np.float32)
        R = np.hypot(xx - 768, (yy - 463) / LIGHT_ASPECT)
        T = 1 + np.maximum(R - LIGHT_R0, 0) / LIGHT_V
        small = self.im1
        wh = (small[..., :3].min(-1) > 0.72) & (small[..., 2] >= small[..., 0] - 0.02)
        ov = np.zeros((1024, 1536), np.uint8)
        for ex, ey in EYES:
            cv2.ellipse(ov, (int(ex), int(ey)), (175, 150), 0, 0, 360, 1, -1)
        wh = cv2.morphologyEx((wh & (ov > 0)).astype(np.uint8), cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
        T[wh > 0] = -3.0
        self.arrive = T.astype(np.float32)
        self.band_mask_cache = {}
        end = ROOT / "assets" / "gen" / "end"
        del self.big, self.im0, self.im1
        # the bust
        info = json.loads((end / "layout.json").read_text(encoding="utf-8"))
        a3 = json.loads((end / "layout3.json").read_text(encoding="utf-8"))
        self.bust_c = info["centre"]
        load = lambda name: E.np_to_image(cv2.imread(str(end / (name + ".png")), cv2.IMREAD_UNCHANGED)[..., [2, 1, 0, 3]])
        self.wind_seq = []
        f = F_BUST
        for (n, _), hold in zip(a3["wind"], BUST_HOLDS):
            self.wind_seq.append((f, n))
            f += hold
        names = [n for n, _ in a3["wind"]] + [n for n, _ in a3["loop"]] + [a3["t1a"], a3["t1b"]]
        self.wind_imgs = {k: load(k) for k in dict.fromkeys(names)}
        self.loop_seq = []
        f = F_BLINK + 8
        while f <= int(T1 * E.FPS) + 3:
            for n, hold in a3["loop"]:
                self.loop_seq.append((f, n))
                f += hold
        self.a3 = a3
        self.patches = {k: (load(k), tuple(v)) for k, v in {**info["patches"], **a3["patches"]}.items()}
        self.strike = info["strike"]
        # the close-up's wind: whole drawings, and her lids over the last of them
        self.close_seq = []
        f = F_CUT
        for (n, _), hold in zip(a3["close_wind"], CLOSE_HOLDS):
            self.close_seq.append((f, n))
            f += hold
        self.close_imgs = {k: load(k) for k in dict.fromkeys(n for n, _ in a3["close_wind"] if n)}
        self.lids = {k: (load(f"lid_{k}"), tuple(v)) for k, v in a3["close_lids"].items()}
        self.fly_np = None
        # the wind's strength and how far it has carried the sky's streaks, on twos: it rises until she shuts her eyes, falls away over the next second or so, and goes on as a steady breeze
        n_ = int((T1 - CUT) * E.FPS) // 2 + 4
        self.wind_w, self.wind_ph = np.zeros(n_), np.zeros(n_)
        ph = 0.0
        d_up = (F_BUST - F_CUT) / E.FPS
        for i in range(n_):
            q = i * 2 / E.FPS
            w = 0.55 + 0.45 * min(q / d_up, 1.0) ** 1.5 if q < d_up else 0.42 + 0.58 * math.exp(-(q - d_up) / 0.75)
            self.wind_w[i], self.wind_ph[i] = w, ph
            ph += (0.3 + 1.3 * w) * 2 / E.FPS

    def wind_at(self, fr):
        """Wind for the sky: 1 is the gust. phase is how far it has carried the streaks. On twos."""
        i = max(fr - F_CUT, 0) // 2
        return float(self.wind_w[i]), float(self.wind_ph[i])

    def sky_scene(self, c, wind, phase, band=None, run=None):
        F.sky(c, band)
        F.streaks(c, wind, phase, band)
        if run is not None:
            F.draw_pieces(c, self.pieces, run, wind)

    def close_cam(self, c, fr):
        """From exactly where the push-in ended, the same camera as the dark close-up, going on creeping in, so slowly it is hardly a move."""
        push = 1.22 + 0.055 * ((fr - F_CUT) / (F_BUST - F_CUT)) ** 1.6
        s0, ex0, ey0 = push * SCALE, 960 + push * (OX + 768 * SCALE - 960), 486 + push * (463 * SCALE - 486)
        c.translate(ex0, ey0)
        c.scale(s0, s0)
        c.translate(-768, -463)

    def band_mask(self, n, k):
        key = (n, k)
        m = self.band_mask_cache.get(key)
        if m is None:
            if len(self.band_mask_cache) > 12:
                self.band_mask_cache.clear()
            a = np.clip((n - k * BAND_DT - self.arrive) * 120 + 0.5, 0, 1)
            rgba = np.zeros((*a.shape, 4), np.uint8)
            rgba[..., :3] = 255
            rgba[..., 3] = (a * 255 + 0.5).astype(np.uint8)
            m = E.np_to_image(rgba)
            self.band_mask_cache[key] = m
        return m

    def irises(self, c, t):
        for i in range(2):
            rgba, (ox, oy) = self.anim.frame(i, t)
            img = E.np_to_image(rgba)
            c.save()
            c.translate(ox, oy)
            c.scale(1 / EA.SS, 1 / EA.SS)
            c.drawImage(img, 0, 0, E.SAMPLING_DOWN)
            c.restore()

    def draw_close(self, c, t, fr):
        wind, phase = self.wind_at(fr)
        n = (fr - F_CUT) // 2
        c.clear(E.col("#05070D"))
        c.save()
        self.close_cam(c, fr)

        def pic(img):
            c.save()
            c.scale(0.5, 0.5)
            c.drawImage(img, 0, 0, E.SAMPLING_DOWN)
            c.restore()
        # the drawing of the wind at this frame; the first steps of the light are still the still drawing
        drawing = self.full
        for f, nm in self.close_seq:
            if f > fr:
                break
            drawing = self.close_imgs[nm] if nm else self.full
        # the arrival: dark picture, then one step of the light after another over it, each cut by its own hard edge
        if n < LIGHT_STEPS:
            pic(self.dark)
            for k, b in enumerate(BANDS):
                c.saveLayer(skia.Rect.MakeWH(1536, 1024), skia.Paint())
                self.sky_scene(c, wind, phase, b)
                pic(self.band_faces[k])
                c.drawImage(self.band_mask(n, k), 0, 0, E.SAMPLING, skia.Paint(BlendMode=skia.BlendMode.kDstIn))
                c.restore()
            c.saveLayer(skia.Rect.MakeWH(1536, 1024), skia.Paint())
            self.sky_scene(c, wind, phase)
            pic(drawing)
            c.drawImage(self.band_mask(n, len(BANDS)), 0, 0, E.SAMPLING, skia.Paint(BlendMode=skia.BlendMode.kDstIn))
            c.restore()
        else:
            # no scraps of the bar here: at the edge of the frame, behind her hair, all they can be is black specks. They come in after the cut to the portrait
            self.sky_scene(c, wind, phase)
            pic(drawing)
        self.irises(c, t)
        # the wind is too strong: the lids come down, Codex's drawings laid into the close-up
        left = F_BUST - fr
        for st, m in CLOSE_LIDS:
            if m - 2 < left <= m:
                img, (x0, y0) = self.lids[st]
                c.save()
                c.translate(x0, y0)
                c.scale(0.5, 0.5)
                c.drawImage(img, 0, 0, E.SAMPLING_DOWN)
                c.restore()
        c.restore()
        # the words go with the wind
        self.fly(c, fr - F_CUT)

    def bust_cam(self, u):
        """Screen position of the point between her eyes and the scale, u from 0 at the cut to 1 at the end: a very slow move that never quite stops."""
        s = E.lerp(BUST_S[0], BUST_S[1], u)
        return E.lerp(BUST_AT[0], BUST_AT[2], u), E.lerp(BUST_AT[1], BUST_AT[3], u), s

    def draw_bust(self, c, t, fr):
        wind, phase = self.wind_at(fr)
        u = (fr - F_BUST) / max(T1 * E.FPS - F_BUST, 1)
        x, y, s = self.bust_cam(u)
        tt = (fr - F_BUST) // 2 * 2 / E.FPS
        c.clear(E.col("#05070D"))
        # the sky behind her, in the sky's own scale; and what the wind carries past her, in screen pixels
        c.save()
        c.translate(x, y)
        k = SKY_S * s / BUST_S[0]
        c.scale(k, k)
        c.translate(-768, -463)
        self.sky_scene(c, wind, phase)
        c.restore()
        F.draw_pieces(c, self.pieces["bust"], tt, wind)
        c.save()
        c.translate(x, y)
        c.scale(s, s)
        c.translate(-self.bust_c[0], -self.bust_c[1])

        def patch(key):
            img, (px, py) = self.patches[key]
            c.drawImage(img, px, py, E.SAMPLING)

        def whole(seq):
            name = seq[0][1]
            for f, n in seq:
                if f > fr:
                    break
                name = n
            c.drawImage(self.wind_imgs[name], 0, 0, E.SAMPLING)
            return name
        b = fr - F_BLINK
        if b < -2:
            # upright. Her eyes shut, then opening on the beat, the light already in them; the mouth a calm flat line
            name = whole(self.wind_seq)
            if fr < F_OPEN:
                state = "closed"
                for st, m in OPEN_LIDS:
                    if F_OPEN - fr <= m:
                        state = st
                patch("eye_" + state + "@" + name)
            else:
                patch(self.strike["stroke"][-1])
                for st, at in self.strike["glints"]:
                    # they stay wet: a fleck goes out for a moment now and then
                    if at < 8 or (int((fr - F_OPEN) / 5) * 7 + at) % 6:
                        patch(st)
            patch("mouth_flat")
        elif b < 0:
            name = self.wind_seq[-1][1]
            c.drawImage(self.wind_imgs[name], 0, 0, E.SAMPLING)
            patch("eye_half@" + name)
            patch("mouth_flat")
        elif b < 2:
            c.drawImage(self.wind_imgs[self.a3["t1a"]], 0, 0, E.SAMPLING)   # her head moves while her lids are down: these two are whole drawings, shut eyes and flat mouth
        elif b < 4:
            c.drawImage(self.wind_imgs[self.a3["t1b"]], 0, 0, E.SAMPLING)
        else:
            # her head has come to rest, a little to one side
            whole(self.loop_seq)
            if b < 6:
                patch("t_closed")
            elif b < 8:
                patch("t_half")
            m = fr - F_SMILE
            if m < 0:
                patch("t_flat")
            elif m < 4:
                patch("t_mid")
        c.restore()
        F.draw_pieces(c, self.pieces["bust"], tt, wind, near=True)

    def draw_finale(self, c, t):
        fr = int(round(t * E.FPS))
        if fr < F_BUST:
            self.draw_close(c, t, fr)
        else:
            self.draw_bust(c, t, fr)

    def grab_words(self):
        # the words: at the moment the band hits, the wind takes them. Kept as one strip of paper, in screen pixels
        surf = skia.Surface(E.W, E.H)
        cv_ = surf.getCanvas()
        cv_.clear(skia.Color4f(0, 0, 0, 0))
        self.words(cv_, CUT - 0.01)
        arr = surf.makeImageSnapshot().toarray(colorType=skia.ColorType.kRGBA_8888_ColorType, alphaType=skia.AlphaType.kUnpremul_AlphaType).copy()
        ys, xs = np.nonzero(arr[..., 3] > 0)
        self.fly_box = (int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1)
        x0, y0, x1, y1 = self.fly_box
        self.fly_np = arr[y0:y1, x0:x1]

    def fly(self, c, df):
        """The strip of words at the moment the band hits it: it stays one piece, bends, lifts and is gone to the right, on twos."""
        if self.fly_np is None:
            self.grab_words()
        q = df // 2 * 2 / E.FPS
        x0, y0, x1, y1 = self.fly_box
        if q <= 0:
            c.drawImage(E.np_to_image(self.fly_np), x0, y0, E.SAMPLING)
            return
        h, w = self.fly_np.shape[:2]
        pad = 240
        bend = 150 * min(q / 0.5, 1.0) ** 1.4
        xs = (np.arange(w, dtype=np.float32) / w)
        off = bend * (xs - 0.15) ** 2 * (1 - 0.25 * np.sin(q * 12 + xs * 5))
        mx, my = np.meshgrid(np.arange(w, dtype=np.float32), np.arange(h + 2 * pad, dtype=np.float32))
        my = my - pad + off[None, :]
        img = cv2.remap(self.fly_np, mx, my.astype(np.float32), cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=(0, 0, 0, 0))
        c.save()
        c.translate(x0 + w * 0.2 + 2500 * q ** 1.4, y0 + h / 2 - 300 * q ** 1.3)
        c.rotate(-34 * q ** 1.2)
        c.translate(-w * 0.2, -h / 2 - pad)
        c.drawImage(E.np_to_image(img), 0, 0, E.SAMPLING)
        c.restore()

    def draw(self, c, t):
        if t >= CUT:
            self.draw_finale(c, t)
            return
        c.clear(E.col("#05070D"))
        # the shot is never completely still: as the light rises the camera closes on her eyes
        push = 1 + 0.02 * E.seg(t, T0, LIGHT) + 0.20 * E.ease_io(E.seg(t, LIGHT - 0.3, CUT), 2.0)
        c.save()
        c.translate(960, 486)
        c.scale(push, push)
        c.translate(-960, -486)
        self.face(c, t)
        self.eyes(c, t)
        if t < TAKE + 0.9:
            self.take_off(c, t)
        c.restore()
        self.words(c, t)

    def words(self, c, t):
        # first bar: "何番目でも", then the same again over the empty eyes
        if t < K.LYRICS[55]["start"] - 0.02:
            ch = K.LYRICS[54]["chars"]
            first = [ch[i]["t"] for i in range(5)]
            second = [ch[i]["t"] for i in range(5, 10)]
            if t < second[0]:
                self.lyric1.times = first
            else:
                self.lyric1.times = second
            self.lyric1.draw(c, 960, 1030, t, ax=0.5)
        else:
            y = 1010
            self.sung.draw(c, 820, y, t, ax=0.5)
            x = 820 + self.sung.ty.w / 2 + 44
            if t >= LAST + 0.02:
                # the tape has room for the three dots from the start, so it never changes shape
                g = self.q
                h_ = 76 + 20 * 1.3
                E.rect(c, x - 42, y - h_ / 2, 190, h_, E.PAPER)
                r = 6.5
                dot_y = y + g.h / 2 - r
                if t < HOOK_DROP:
                    g.draw(c, x, y, E.INK)
                else:
                    # only the hook falls; its point stays behind and becomes the first of the dots
                    fall = t - HOOK_DROP
                    if fall < 0.34:
                        c.save()
                        c.clipRect(skia.Rect.MakeLTRB(x - 60, y - g.h, x + 60, y + g.h / 2 - r * 3 + 760 * fall ** 2))
                        c.translate(0, 760 * fall ** 2)
                        c.clipRect(skia.Rect.MakeLTRB(x - 60, y - g.h, x + 60, dot_y - r * 1.7))
                        g.draw(c, x, y, E.INK)
                        c.restore()
                    for dx, dt in zip((x, x + 42, x + 84), (HOOK_DROP, 201.04, 201.20)):
                        if t >= dt:
                            c.drawCircle(dx, dot_y, r, skia.Paint(AntiAlias=True, Color4f=E.col(E.INK)))
