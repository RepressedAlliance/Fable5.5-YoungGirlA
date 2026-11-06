"""The finishing stroke. A finished painting of the irises is taken apart so the light can arrive in order:

  empty, flat eye
  each sung syllable lets the light rise one step: the deep shapes appear first, the bright ones last
  tiny flecks come on one at a time
  on the last syllable the main highlight is painted in a single stroke, heavy end first, and the pupil
  contracts in response, the way a living eye does
  after that the light on the eye is wet: flecks twinkle, the lower light moves very slightly

Everything is worked at twice picture resolution so it stays sharp at full-screen size.
"""
import math

import cv2
import numpy as np

import engine as E

SS = 2


def smooth(x):
    x = np.clip(x, 0, 1)
    return x * x * (3 - 2 * x)


class EyeAnim:
    def __init__(self, source, region, iris_mask, eyes, syllables, stroke_t, cut_t):
        """source: BGR painting. region: (x0, y0, x1, y1) of the picture it covers. iris_mask: float, picture size."""
        self.syl = syllables
        self.stroke_t = stroke_t
        self.cut_t = cut_t
        x0, y0, x1, y1 = region
        scale = SS * (x1 - x0) / source.shape[1]
        src = cv2.resize(source, None, fx=scale, fy=scale, interpolation=cv2.INTER_AREA if scale < 1 else cv2.INTER_CUBIC)
        src = src[..., ::-1].astype(np.float32) / 255
        self.eyes = []
        for ex, ey in eyes:
            bx0, by0, bx1, by1 = int(ex - 100), int(ey - 125), int(ex + 100), int(ey + 125)
            F = src[(by0 - y0) * SS:(by1 - y0) * SS, (bx0 - x0) * SS:(bx1 - x0) * SS].copy()
            M = cv2.resize(iris_mask[by0:by1, bx0:bx1], (F.shape[1], F.shape[0]), interpolation=cv2.INTER_CUBIC)
            self.eyes.append(self._analyse(F, np.clip(M, 0, 1), (bx0, by0)))

    def _analyse(self, F, M, origin):
        lum = F.mean(-1)
        # highlights are pure white paint. The bright rim at the bottom of the eye is pale teal: its red is low.
        white = ((F[..., 0] > 0.86) & (M > 0.5)).astype(np.uint8)
        white = cv2.morphologyEx(white, cv2.MORPH_OPEN, np.ones((2, 2), np.uint8))
        n, lab, st, cen = cv2.connectedComponentsWithStats(white, connectivity=8)
        # the long white line at the very bottom of the eye belongs to the rim of light, not the highlights
        for i in range(1, n):
            if cen[i][1] > F.shape[0] * 0.72 and st[i, 2] > 2.5 * st[i, 3]:
                white[lab == i] = 0
        n, lab, st, cen = cv2.connectedComponentsWithStats(white, connectivity=8)
        comps = sorted(range(1, n), key=lambda i: -st[i, 4])
        # highlight alpha: soft edge taken from the painting itself
        a_all = np.clip((F[..., 0] - 0.40) / 0.45, 0, 1) * (M > 0.1)
        grown = cv2.dilate(white, np.ones((9, 9), np.uint8))
        inp = cv2.inpaint((F * 255).astype(np.uint8), grown, 7, cv2.INPAINT_TELEA).astype(np.float32) / 255
        a_all = a_all * (grown > 0)
        # What lies under the highlights is unknown, and a smeared guess shows before the stroke lands. Rebuild it
        # cleanly: the upper tone of the iris, and the pupil as an ellipse fitted to the part that can be seen.
        # the pupil is darker than the deep band above it: go by the darkness at its own centre
        hh, ww = F.shape[:2]
        centre = np.median(F[int(hh * 0.46):int(hh * 0.54), int(ww * 0.46):int(ww * 0.54)].mean(-1))
        visible_dark = ((F.mean(-1) < centre + 0.022) & (M > 0.9) & (grown == 0)).astype(np.uint8)
        visible_dark = cv2.morphologyEx(visible_dark, cv2.MORPH_OPEN, np.ones((7, 7), np.uint8))
        nd, labd = cv2.connectedComponents(visible_dark, connectivity=8)
        mid = labd[int(hh * 0.5), int(ww * 0.5)]
        visible_dark = (labd == mid).astype(np.uint8) if mid > 0 else visible_dark
        cn = cv2.findContours(visible_dark, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)[-2]
        if cn:
            big = max(cn, key=cv2.contourArea)
            if len(big) >= 5:
                # only trust the contour points away from any highlight
                pts = np.array([p for p in big[:, 0] if cv2.dilate(grown, np.ones((7, 7), np.uint8))[p[1], p[0]] == 0], np.int32)
                if len(pts) >= 5:
                    (ecx, ecy), (ea, eb), eang = cv2.fitEllipse(pts)
                    print("pupil", round(ecx), round(ecy), round(ea), round(eb), "of", ww, hh, flush=True)
                    under = np.zeros(F.shape[:2], np.uint8)
                    cv2.ellipse(under, ((ecx, ecy), (ea, eb), eang), 1, -1)
                    pupil_col = np.median(F[(under > 0) & (grown == 0)], axis=0)
                    # the iris's tone bands are continued under both the highlight and the pupil, then the pupil is
                    # drawn back on as one clean shape
                    hole = cv2.dilate(((under > 0) | (grown > 0)).astype(np.uint8), np.ones((7, 7), np.uint8))
                    bands = cv2.inpaint((F * 255).astype(np.uint8), hole, 11, cv2.INPAINT_TELEA).astype(np.float32) / 255
                    aa = cv2.GaussianBlur(under.astype(np.float32), (0, 0), 1.0)[..., None]
                    inp = bands * (1 - aa) + pupil_col.astype(np.float32) * aa
        parts = []
        for rank, i in enumerate(comps):
            m = cv2.dilate((lab == i).astype(np.uint8), np.ones((7, 7), np.uint8)).astype(np.float32)
            parts.append((m, tuple(cen[i]), int(st[i, 4])))
        main = parts[0] if parts else None
        second = parts[1] if len(parts) > 1 else None
        flecks = parts[2:]
        # stroke order for the main highlight: along its long axis, from the heavier end
        order = None
        if main is not None:
            ys, xs = np.nonzero(lab == comps[0])
            pts = np.stack([xs, ys], 1).astype(np.float32)
            c = pts.mean(0)
            u, s, vt = np.linalg.svd(pts - c, full_matrices=False)
            ax = vt[0]
            # both eyes alike: the brush lands at the top of the stroke and comes down
            if ax[1] < 0:
                ax = -ax
            pr = (pts - c) @ ax
            H, W = F.shape[:2]
            yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
            # the front of the stroke is round, like the tip of a loaded brush
            s_ = pts[int(np.argmin(pr))]
            d_ = np.hypot(xx - s_[0], yy - s_[1])
            order = d_ / max(float(np.hypot(*(pts - s_).T).max()), 1.0)
        # pupil: darkest large blob
        dark = (cv2.GaussianBlur(inp.mean(-1), (0, 0), 2) < 0.16).astype(np.uint8)
        n2, lab2, st2, cen2 = cv2.connectedComponentsWithStats(dark & (M > 0.5).astype(np.uint8))
        if n2 > 1:
            j = 1 + int(np.argmax(st2[1:, 4]))
            pc = cen2[j]
            pr_ = math.sqrt(st2[j, 4] / math.pi)
        else:
            pc = (F.shape[1] / 2, F.shape[0] / 2)
            pr_ = 60.0
        H, W = F.shape[:2]
        yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
        return dict(F=F, M=M, base=inp, a=a_all, main=main, second=second, flecks=flecks, order=order, pupil=(pc, pr_),
                    origin=origin, xx=xx, yy=yy, lum=np.maximum(inp.mean(-1), 0.02))

    def tide(self, t):
        """0 at the first syllable, 1 at the last: holds between syllables, moves in a quick step on each."""
        n = 0
        for i in range(1, len(self.syl)):
            if t >= self.syl[i]:
                n = i
        if n == 0:
            return 0.0
        return (n - 1 + E.ease_out((t - self.syl[n]) / 0.07, 3)) / (len(self.syl) - 1)

    def level(self, t):
        """How high the light has risen: the first eight syllables only move the darks; the last three bring the light."""
        # starts at the brightness of the empty eye: the light only ever goes up, the iris never dims first
        steps = [0.30, 0.32, 0.34, 0.36, 0.39, 0.42, 0.46, 0.51, 0.60, 0.76, 1.0]
        L = None
        for s, v in zip(self.syl, steps):
            if t >= s:
                u = E.clamp01((t - s) / 0.05)
                L = v if L is None else L + (v - L) * u
        return L

    def frame(self, i, t):
        """RGBA picture (uint8) of one iris at time t, and where its top-left goes in picture coordinates."""
        e = self.eyes[i]
        H, W = e["F"].shape[:2]
        L = self.level(t)
        if L is None:
            # still empty: one flat dead colour
            out = np.zeros((H, W, 4), np.float32)
            out[..., :3] = np.array([0x1C, 0x6A, 0x80], np.float32) / 255
            out[..., 3] = e["M"]
            return (out * 255 + 0.5).astype(np.uint8), e["origin"]
        pc, pr = e["pupil"]
        # pupil: wide open in the dark, and it closes down when the light strikes
        u = E.ease_out((t - self.stroke_t) / 0.16, 2.6) if t >= self.stroke_t else 0.0
        s = 1.5 + (1.0 - 1.5) * u
        dx, dy = e["xx"] - pc[0], e["yy"] - pc[1]
        r = np.sqrt(dx * dx + dy * dy * 0.72) / (pr * 2.7)
        f = 1 / s + (1 - 1 / s) * smooth(r)
        mapx = pc[0] + dx * f
        mapy = pc[1] + dy * f
        # wet: after the stroke, the light in the lower eye moves as if held in water
        if t >= self.stroke_t:
            w = E.clamp01((t - self.stroke_t) / 0.5)
            low = smooth((e["yy"] - H * 0.52) / (H * 0.22))
            mapx = mapx + w * low * 1.7 * np.sin(e["yy"] * 0.055 + t * 4.3 + i * 1.3)
            mapy = mapy + w * low * 1.1 * np.sin(e["xx"] * 0.042 + t * 3.1 + i * 2.1)
        rgb = cv2.remap(e["base"], mapx.astype(np.float32), mapy.astype(np.float32), cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
        lum = np.maximum(rgb.mean(-1), 0.02)
        p = self.tide(t)
        if p < 1:
            # The light rises one hard step per sung syllable. Above the waterline the eye is still held down;
            # below it the painting has its full colour. The waterline curves with the eyeball.
            L0 = 0.30
            scaled = rgb * np.minimum(1.0, L0 / lum)[..., None]
            teal = np.array([0x21, 0x8E, 0xA3], np.float32) / 255
            target = teal * (L0 / teal.mean())
            k = np.clip((lum - L0) / 0.25, 0, 1)[..., None]
            dim = scaled * (1 - k) + target * k
            dx = (e["xx"] - W / 2) / (W / 2)
            line = H * (0.93 - 0.52 * p) + 0.13 * H * (1 - dx * dx) - 0.02 * H
            m = np.clip((e["yy"] - line) / 1.6, 0, 1)[..., None] if p > 0 else np.zeros((H, W, 1), np.float32)
            rgb = dim * (1 - m) + rgb * m
        a = e["a"]
        white = np.array([1.0, 1.0, 1.0], np.float32)
        # flecks come on one at a time on the syllable before the stroke, then twinkle
        n = max(1, len(e["flecks"]))
        start = self.syl[9]
        for k, (m, cen, area) in enumerate(e["flecks"]):
            tk = start + (self.stroke_t - start) * k / n
            if t < tk:
                continue
            v = E.clamp01((t - tk) / 0.05)
            if t >= self.cut_t:
                # twinkle: drawings held on threes, never a smooth pulse
                phase = int((t - self.cut_t) * 10 + k * 3.7)
                v *= 1.0 if (phase * 7 + k) % 5 else 0.0   # a glint is on or off, never a grey ghost of itself
            al = (a * m * v)[..., None]
            rgb = rgb * (1 - al) + white * al
        # the second dab lands just after the stroke
        if e["second"] is not None and t >= self.stroke_t + 0.09:
            v = 1.0
            al = (a * e["second"][0] * v)[..., None]
            rgb = rgb * (1 - al) + white * al
        # the stroke: painted in one movement, heavy end first
        if e["main"] is not None and t >= self.stroke_t:
            front = E.ease_out((t - self.stroke_t) / 0.13, 2.0) * 1.06
            reveal = np.clip((front - e["order"]) / 0.012, 0, 1)   # the wet edge of the stroke is hard
            al = (a * e["main"][0] * reveal)[..., None]
            rgb = rgb * (1 - al) + white * al
        out = np.dstack([np.clip(rgb, 0, 1), e["M"]])
        return (out * 255 + 0.5).astype(np.uint8), e["origin"]
