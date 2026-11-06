"""Shared by the clips: finished 3D frames as backgrounds, and the sung lyric strip."""
import json
import os
import sys
from functools import lru_cache
from pathlib import Path

import cv2
import numpy as np
import skia

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "src" / "three"), str(ROOT / "src" / "art")]
import engine as E  # noqa: E402

LYRICS = json.loads((ROOT / "work" / "analysis" / "lyrics_timed.json").read_text(encoding="utf-8"))


def seq_frame(shot, t, t0):
    """Finished 3D frame for time t: two 60 fps renders are averaged when both exist, a 180-degree-plus shutter."""
    if os.environ.get("SEQ_TEST"):
        # look-development: use the nearest test still
        fs = sorted((ROOT / "work" / "qc" / shot).glob("t*.png"))
        best = min(fs, key=lambda f: abs(float(f.stem[1:]) - t))
        return cv2.imread(str(best))
    d = ROOT / "work" / "render" / f"{shot}_png"
    n = int(round((t - t0) * 60))
    n -= n % 2
    return cv2.imread(str(d / f"f{n:05d}.png"))


def duotone(rgba, dark=(0.020, 0.030, 0.065), light=(0.36, 0.45, 0.66)):
    """A dark room: luminance mapped between two blues, so hair and skin share one night colour. Ink stays black."""
    out = rgba.copy()
    g = rgba[..., :3].mean(-1, keepdims=True)
    d, l = np.array(dark, np.float32), np.array(light, np.float32)
    out[..., :3] = d + (l - d) * np.clip(g, 0, 1) ** 1.2
    return out


def affine_blur(im, m0, m1, max_samples=120, soft=False):
    """Real motion blur for a known camera move: the frame is swept from affine m0 to m1 (2x3, around the identity).
    Enough samples are taken that no step is over 1.5 px, so moving edges streak and never show as separate copies.
    soft: a shutter that opens and closes (Hann weights), so a thin line streaks into one soft band, not into two edges."""
    corners = np.array([[0, 0, 1], [im.shape[1], 0, 1], [0, im.shape[0], 1], [im.shape[1], im.shape[0], 1]], np.float32)
    span = np.abs(corners @ (np.asarray(m1, np.float32) - np.asarray(m0, np.float32)).T).max()
    k = int(min(max_samples, np.ceil(span / 1.0)))
    if k < 2:
        return im
    acc = np.zeros(im.shape, np.float32)
    total = 0.0
    for i in range(k):
        u = (i + 0.5) / k
        m = np.asarray(m0, np.float32) * (1 - u) + np.asarray(m1, np.float32) * u
        w = float(np.sin(np.pi * u) ** 2) if soft else 1.0
        acc += w * cv2.warpAffine(im, m, (im.shape[1], im.shape[0]), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
        total += w
    return (acc / total + 0.5).astype(np.uint8)


def soft_frame(clip, t):
    """E.Clip.frame_rgb with a shutter that opens and closes: the sub-frames are Hann weighted, so a fast edge streaks
    into one soft band and does not print as a hard-ended box or as counted copies. Asks clip.blur(t) for the count."""
    n = clip.blur(t)
    acc = None
    surf = skia.Surface(E.W, E.H)
    total = 0.0
    for i in range(n):
        u = (i + 0.5) / n
        st = t + (u - 0.5) * (clip.shutter / E.FPS) if n > 1 else t
        for cut in clip.cuts:
            if st < cut <= t:
                st = cut
            elif t < cut <= st:
                st = cut - 1e-4
        c = surf.getCanvas()
        c.clear(skia.Color4f(0, 0, 0, 1))
        clip.draw(c, st)
        arr = surf.makeImageSnapshot().toarray(colorType=skia.ColorType.kRGBA_8888_ColorType,
                                               alphaType=skia.AlphaType.kOpaque_AlphaType)[..., :3]
        w = float(np.sin(np.pi * u) ** 2) if n > 1 else 1.0
        acc = arr.astype(np.float32) * w if acc is None else acc + arr * w
        total += w
    rgb = clip.post(acc / (total * 255.0), t)
    return E.paper_grain(rgb, clip.grain)


# ---- the one trending list of the film: sections 06, 08 and 09 all read their numbers from here ----
TREND_COUNTS = [9820000, 8740000, 7610000, 6520000, 5480000, 4710000, 4020000, 3510000, 3060000, 2680000, 2390000, 2140000,
                1880000, 1670000, 1510000, 1360000, 1240000, 1120000, 1060000, 1040000, 1030000, 1020000, 1010000, 999000, 991000]
TREND_LAST = 847        # the length of the list. Past 100 the list prints no rank at all: 圏外


def trend_count(rank):
    """Posts for the topic at this rank among the ordinary topics of section 06. 982万 down to 3."""
    if rank <= len(TREND_COUNTS):
        return TREND_COUNTS[max(rank, 1) - 1]
    k = ((rank - len(TREND_COUNTS)) / (TREND_LAST - len(TREND_COUNTS))) ** 0.55
    return int(np.exp(np.log(TREND_COUNTS[-1]) * (1 - k) + np.log(3.0) * k) + 0.5)


def trend_rank(count):
    """Where a topic with this many posts stands in that list."""
    lo, hi = 1, TREND_LAST + 1
    while lo < hi:
        mid = (lo + hi) // 2
        if trend_count(mid) > count:
            lo = mid + 1
        else:
            hi = mid
    return lo


def count_text(n):
    """Posts as the list prints them."""
    if n >= 10000000:
        return f"{n // 10000:,}万件"
    if n >= 1000000:
        return f"{n / 10000:.0f}万件"
    if n >= 10000:
        return f"{n / 10000:.3g}万件"
    return f"{n:,}件"


class Strip:
    """One sung line: paper tape with black text. The tape grows with the words, glyphs appear as they are sung."""

    def __init__(self, text, times, size=44, font="ShipporiMinchoB1-ExtraBold", tracking=2.0, pad=16):
        self.ty = E.Type(text, font, size, tracking=tracking)
        self.times = times
        self.pad = pad
        self.size = size
        self.text = text

    def draw(self, c, x, y, t, ax=0.0, color=E.INK, paper=E.PAPER, tail=0.08):
        shown = [g for g in self.ty.run.glyphs if g.cluster < len(self.times) and self.times[g.cluster] <= t]
        if not shown:
            return
        last = shown[-1]
        b = last.path.computeTightBounds()
        # tape end eases along to the newest glyph
        target = last.x + b.right() - self.ty.l
        full = self.ty.w
        x0 = x - full * ax - self.pad
        h = self.size + self.pad * 1.3
        E.rect(c, x0, y - h / 2, target + self.pad * 2, h, paper)
        dx = x0 + self.pad - self.ty.l
        dy = y - self.ty.t - self.ty.h / 2
        for g in shown:
            c.drawPath(E.typo.glyph_path(g, dx=dx, dy=dy), skia.Paint(AntiAlias=True, Color4f=E.col(color)))


def chars_of(line_idx, text):
    """Time of each character of `text`, matched in order within the sung line (searched from its end)."""
    ch = LYRICS[line_idx]["chars"]
    out = []
    i = len(ch) - 1
    for c in reversed(text):
        while i >= 0 and ch[i]["c"] != c:
            i -= 1
        out.append(ch[i]["t"] if i >= 0 else (out[-1] if out else 0.0))
        i -= 1
    return list(reversed(out))


def syllable_times(line_idx, sound):
    return [s["t"] for s in LYRICS[line_idx]["syl"] if s["text"].strip() == sound]
