"""Clip 3 overlay on the 3D shot: words left behind, the rising count, her dot, the map's lettering."""
import math
import os
import sys
from pathlib import Path

import numpy as np
import skia

sys.path.insert(0, str(Path(__file__).parent))
import common as K  # noqa: E402
import engine as E  # noqa: E402
import shared_c3 as S  # noqa: E402

COUNTS = [12, 38, 104, 361, 1208, 3921, 11840, 40277, 96512, 182930, 310488, 512096, 788341, 984201]
FULL = [1 + 0] * 0
WORD_FONT = "ShipporiMinchoB1-ExtraBold"
LABELS = [  # world x, y, name, size
    (-340, -500, "東都駅", 26), (420, 980, "東都川", 24), (-1050, 420, "青葉町", 30), (900, -300, "緑ヶ丘", 30),
    (-300, 1250, "川向こう", 22), (1250, 760, "南町三丁目", 22), (-1240, -760, "北町", 26), (-40, -1010, "大通り", 20),
]
GROUND = -7.6


def fmt(n):
    if n >= 10000:
        return f"{n / 10000:.1f}万"
    return f"{n:,}"


class Tooi(E.Clip):
    name = "c3"
    t0, t1 = S.T0, S.T1

    def setup(self):
        # the whole of line 22: the push towards her happens under it
        self.strip_voice = K.Strip("ああ君の君の君の声が", K.chars_of(22, "ああ君の君の君の声が"), size=46)
        self.strip_hurt = K.Strip("傷つけないで", K.chars_of(25, "傷つけないで"), size=30, pad=10)
        self.word = E.Type("遠い", WORD_FONT, 140)
        self.tag = E.Type("リポスト", "ZenKakuGothicNew-Bold", 30)
        self.school = E.Type("文", "ZenKakuGothicNew-Black", 24)
        self.head = E.load_image(K.ROOT / "assets" / "gen" / "her_head.png")
        tt = S.HIT_T[0]
        while 1.2 / S.distance_at(tt) * (S.LENS / 36) * 1920 >= S.ICON_AT:
            tt += 0.01
        self.t_icon = tt

    def her_screen(self, t):
        # the mark grows out of where her head is, then settles on the spot where she sits
        k = E.clamp01((t - self.t_icon) / 0.5) if hasattr(self, "t_icon") else 0.0
        return S.project((S.HER_HEAD[0], S.HER_HEAD[1] + 0.2 * k, 1.1 - 0.35 * k), t)

    def frame_rgb(self, t):
        im = K.seq_frame("c3", t, self.t0)
        # the camera backs straight away from her, and she is the centre of the frame: a zoom blur about the centre
        dt = 0.15 / E.FPS / 2   # a short shutter: enough to take off the strobing, not enough to smear the drawing
        d = S.distance_at(t)
        s0, s1 = d / S.distance_at(t - dt), d / S.distance_at(t + dt)

        def zoom(s):
            return np.array([[s, 0, 960 * (1 - s)], [0, s, 540 * (1 - s)]], np.float32)

        if not os.environ.get("SEQ_TEST"):
            im = K.affine_blur(im, zoom(s0), zoom(s1))
        arr = np.dstack([im[..., ::-1], np.full(im.shape[:2], 255, np.uint8)])
        surf = skia.Surface(E.W, E.H)
        c = surf.getCanvas()
        c.drawImage(E.np_to_image(arr), 0, 0)
        self.overlay(c, t)
        out = surf.makeImageSnapshot().toarray(colorType=skia.ColorType.kRGBA_8888_ColorType,
                                               alphaType=skia.AlphaType.kOpaque_AlphaType)[..., :3]
        return E.paper_grain(out.astype(np.float32) / 255, self.grain)

    def overlay(self, c, t):
        hp = self.her_screen(t)
        hx, hy = (hp[0], hp[1]) if hp else (960, 540)
        d = S.distance_at(t)
        # the line before the words
        if t < S.HIT_T[0] + 0.1:
            self.strip_voice.draw(c, 90, 960, t)
        # map lettering appears as the town sinks
        k = E.seg(t, S.STOP + 0.5, S.FLAT_END)
        if k > 0:
            for i, (x, y, name, size) in enumerate(LABELS):
                p = S.project((x, y, GROUND), t)
                if not p:
                    continue
                if k < 0.1 * (i + 1) * 0.9:
                    continue
                E.Type(name, "ZenKakuGothicNew-Medium", size * 1.25).draw(c, p[0], p[1], "#3A3F4A", stroke=("#F6F3EA", 5))
                E.Type(name, "ZenKakuGothicNew-Medium", size * 1.25).draw(c, p[0], p[1], "#3A3F4A")
        # the words stay where they were sung, spiralling away and never landing on her
        for i, ht in enumerate(S.HIT_T):
            if t < ht:
                continue
            di = S.distance_at(ht + 0.02)
            ratio = max(d / di, 1.0)
            pop = E.ease_out((t - ht) / 0.10, 3)
            size = 1.05 * (ratio ** -0.62) * (0.8 + 0.2 * pop)
            if size * 140 < 15:
                continue
            ang = 2.3 * i + 0.55 * math.log(ratio)
            r = 330 + 90 * (i % 3)
            rad = r * (ratio ** -0.20)
            x = 960 + math.cos(ang) * rad * 1.5
            y = 520 + math.sin(ang) * rad * 0.82
            self.word.draw(c, x, y, E.CYAN, scale=size, stroke=(E.INK, 6 / max(size, 0.2)))
            self.word.draw(c, x, y, E.CYAN, scale=size)
        # repost counter
        idx = -1
        for i, ht in enumerate(S.HIT_T):
            if t >= ht:
                idx = i
        if t >= S.HIT_T[0] - 0.4:
            n = COUNTS[max(idx, 0)]
            bump = 1 + 0.10 * (1 - E.ease_out((t - S.HIT_T[max(idx, 0)]) / 0.16)) if idx >= 0 else 1.0
            E.rect(c, 60, 56, 430, 104, E.PAPER)
            self.tag.draw(c, 80, 72, E.INK, ax=0, ay=0)
            num = E.Type(fmt(n), "ZenKakuGothicNew-Black", 58)
            num.draw(c, 470, 148, E.INK, ax=1, ay=1, scale=bump)
        # her dot: takes over once she is too small to read, then never shrinks
        fig_h = 1.2 / (hp[2] if hp else 1) * (S.LENS / 36) * 1920 if hp else 999
        if t >= self.t_icon:
            # from here on she is a tiny picture of her own head, bar and all, cut out like a map pin
            pop = E.ease_out((t - self.t_icon) / 0.25, 3)
            E.draw_image(c, self.head, hx, hy, (64 + 34 * pop) / self.head.height(), ax=0.5, ay=0.62)
        if t >= S.STOP - 0.1:
            k2 = E.seg(t, S.STOP + 0.5, S.FLAT_END)
            if k2 > 0.25:
                # the map's school symbol sits beside her
                c.drawCircle(hx - 76, hy, 21, skia.Paint(AntiAlias=True, Color4f=E.col(E.PAPER)))
                c.drawCircle(hx - 76, hy, 21, skia.Paint(AntiAlias=True, Color4f=E.col("#3A3F4A"), Style=skia.Paint.kStroke_Style, StrokeWidth=3))
                self.school.draw(c, hx - 76, hy, "#3A3F4A")
            self.strip_hurt.draw(c, hx + 66, hy + 2, t)
