"""2D frame engine: Skia on the CPU, motion blur from real sub-frames, ordered parallel render to ffmpeg."""
import math
import multiprocessing as mp
import os
import subprocess
import sys
import time
from functools import lru_cache
from pathlib import Path

import cv2
import numpy as np
import skia

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from typo import engine as typo  # noqa: E402

W, H = 1920, 1080
FPS = 30

CYAN = "#03C3FB"
INK = "#0A0A0F"
PAPER = "#F6F3EA"
RIN = "#FEE45F"
RED = "#E5162E"


def col(h, a=1.0):
    h = h.lstrip("#")
    return skia.Color4f(int(h[0:2], 16) / 255, int(h[2:4], 16) / 255, int(h[4:6], 16) / 255, a)


# ---- easing ----
def clamp01(x):
    return max(0.0, min(1.0, x))


def seg(t, a, b):
    return clamp01((t - a) / max(b - a, 1e-6))


def ease_out(x, p=3):
    return 1 - (1 - clamp01(x)) ** p


def ease_in(x, p=3):
    return clamp01(x) ** p


def ease_io(x, p=3):
    x = clamp01(x)
    return 0.5 * (2 * x) ** p if x < 0.5 else 1 - 0.5 * (2 * (1 - x)) ** p


def lerp(a, b, u):
    return a + (b - a) * u


def back_out(x, s=1.4):
    x = clamp01(x) - 1
    return x * x * ((s + 1) * x + s) + 1


# ---- images ----
_images = {}


def np_to_image(rgba):
    """Float or uint8 straight-alpha RGBA to a premultiplied Skia image."""
    if rgba.dtype != np.uint8:
        rgba = (np.clip(rgba, 0, 1) * 255 + 0.5).astype(np.uint8)
    rgba = np.array(rgba, dtype=np.uint8, order="C")
    return skia.Image.fromarray(rgba, colorType=skia.ColorType.kRGBA_8888_ColorType,
                                alphaType=skia.AlphaType.kUnpremul_AlphaType)


def load_image(path):
    k = str(path)
    if k not in _images:
        bgra = cv2.imread(k, cv2.IMREAD_UNCHANGED)
        if bgra.shape[2] == 3:
            bgra = np.dstack([bgra, np.full(bgra.shape[:2], 255, np.uint8)])
        _images[k] = np_to_image(bgra[..., [2, 1, 0, 3]])
    return _images[k]


SAMPLING = skia.SamplingOptions(skia.CubicResampler.Mitchell())
SAMPLING_DOWN = skia.SamplingOptions(skia.FilterMode.kLinear, skia.MipmapMode.kLinear)


def draw_image(c, img, x=0, y=0, sx=1.0, sy=None, ax=0.5, ay=0.5, rot=0.0, alpha=1.0, paint=None):
    """Place an image with its anchor (ax, ay, fractions) at (x, y)."""
    sy = sx if sy is None else sy
    c.save()
    c.translate(x, y)
    if rot:
        c.rotate(rot)
    c.scale(sx, sy)
    c.translate(-img.width() * ax, -img.height() * ay)
    p = paint or skia.Paint(AntiAlias=True)
    if alpha < 1:
        p = skia.Paint(p)
        p.setAlphaf(alpha)
    samp = SAMPLING if max(abs(sx), abs(sy)) >= 0.7 else SAMPLING_DOWN
    c.drawImage(img, 0, 0, samp, p)
    c.restore()


def quad_matrix(wh, quad):
    """Perspective matrix mapping a (w, h) rect to four points (tl, tr, br, bl)."""
    w, h = wh
    m = skia.Matrix()
    src = [skia.Point(0, 0), skia.Point(w, 0), skia.Point(w, h), skia.Point(0, h)]
    dst = [skia.Point(*p) for p in quad]
    m.setPolyToPoly(src, dst)
    return m


# ---- type ----
_shape_cache = {}


def shape(text, font="ShipporiMinchoB1-ExtraBold", size=64.0, vertical=False, tracking=0.0, variations=None):
    k = (text, font, round(size, 2), vertical, round(tracking, 2), tuple(sorted((variations or {}).items())))
    if k not in _shape_cache:
        _shape_cache[k] = typo.shape(text, font, size, vertical, variations=variations, tracking=tracking)
    return _shape_cache[k]


class Type:
    """A measured block of text. Size is computed to fit, never hard-coded blind."""

    def __init__(self, text, font="ShipporiMinchoB1-ExtraBold", size=64.0, vertical=False, tracking=0.0, variations=None):
        self.run = shape(text, font, size, vertical, tracking, variations)
        self.text = text
        b = self.run.bounds()
        self.l, self.t, self.r, self.b = b.left(), b.top(), b.right(), b.bottom()
        self.w, self.h = self.r - self.l, self.b - self.t
        self.path = skia.Path()
        for g in self.run.glyphs:
            self.path.addPath(typo.glyph_path(g))

    def draw(self, c, x, y, color=INK, ax=0.5, ay=0.5, alpha=1.0, scale=1.0, rot=0.0, stroke=None, skew=0.0):
        """Draws so that the tight bounds' anchor (ax, ay) lands at (x, y)."""
        c.save()
        c.translate(x, y)
        if rot:
            c.rotate(rot)
        if skew:
            c.skew(skew, 0)
        if scale != 1.0:
            c.scale(scale, scale)
        c.translate(-(self.l + self.w * ax), -(self.t + self.h * ay))
        if stroke:
            c.drawPath(self.path, skia.Paint(AntiAlias=True, Color4f=col(stroke[0], alpha),
                                             Style=skia.Paint.kStroke_Style, StrokeWidth=stroke[1],
                                             StrokeJoin=skia.Paint.kRound_Join))
        c.drawPath(self.path, skia.Paint(AntiAlias=True, Color4f=col(color, alpha)))
        c.restore()


def fit_size(text, font, box_w, box_h, vertical=False, tracking=0.0, max_size=600, min_size=6, variations=None):
    """Largest size at which the text's tight bounds fit in the box."""
    lo, hi = min_size, max_size
    for _ in range(12):
        mid = (lo + hi) / 2
        b = typo.shape(text, font, mid, vertical, variations=variations, tracking=tracking).bounds()
        if b.width() <= box_w and b.height() <= box_h:
            lo = mid
        else:
            hi = mid
    return lo


def fit(text, font, box_w, box_h, vertical=False, tracking=0.0, max_size=600, variations=None):
    return Type(text, font, round(fit_size(text, font, box_w, box_h, vertical, tracking, max_size, variations=variations), 1),
                vertical, tracking, variations)


def rect(c, x, y, w, h, color, alpha=1.0, radius=0.0):
    p = skia.Paint(AntiAlias=True, Color4f=col(color, alpha))
    if radius:
        c.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(x, y, w, h), radius, radius), p)
    else:
        c.drawRect(skia.Rect.MakeXYWH(x, y, w, h), p)


# ---- printing ----
_grain = None


def paper_grain(rgb, amount=0.010):
    """The same paper tooth on every frame of the film: 2D and 3D go through it alike."""
    global _grain
    if _grain is None:
        rng = np.random.default_rng(404)
        a = rng.random((H // 2 + 1, W // 2 + 1), dtype=np.float32)
        b = rng.random((H // 5 + 1, W // 5 + 1), dtype=np.float32)
        _grain = (cv2.resize(a, (W, H), interpolation=cv2.INTER_LINEAR) * 0.7 +
                  cv2.resize(b, (W, H), interpolation=cv2.INTER_CUBIC) * 0.5 - 0.6)
    return np.clip(rgb + (_grain[..., None] * amount * 2), 0, 1)


class Clip:
    """Subclass: set t0, t1 (song seconds) and implement draw(c, t). `blur(t)` says how many sub-frames."""
    name = "clip"
    t0 = 0.0
    t1 = 1.0
    grain = 0.010
    cuts = ()
    shutter = 0.5

    def setup(self):
        pass

    def draw(self, c, t):
        raise NotImplementedError

    def blur(self, t):
        return 1

    def post(self, rgb, t):
        return rgb

    def frame_rgb(self, t):
        n = self.blur(t)
        acc = None
        surf = skia.Surface(W, H)
        for i in range(n):
            # shutter 180 degrees, centred on the frame time
            st = t + ((i + 0.5) / n - 0.5) * (self.shutter / FPS) if n > 1 else t
            # a shutter never spans a hard cut: that would print two different shots into one frame
            for cut in self.cuts:
                if st < cut <= t:
                    st = cut
                elif t < cut <= st:
                    st = cut - 1e-4
            c = surf.getCanvas()
            c.clear(skia.Color4f(0, 0, 0, 1))
            self.draw(c, st)
            arr = surf.makeImageSnapshot().toarray(colorType=skia.ColorType.kRGBA_8888_ColorType,
                                                   alphaType=skia.AlphaType.kOpaque_AlphaType)[..., :3]
            acc = arr.astype(np.float32) if acc is None else acc + arr
        rgb = acc / (n * 255.0)
        rgb = self.post(rgb, t)
        return paper_grain(rgb, self.grain)


# ---- parallel render ----
_clip = None


def _init(module, cls):
    global _clip
    os.environ.setdefault("OMP_NUM_THREADS", "1")
    cv2.setNumThreads(1)
    import importlib
    sys.path.insert(0, str(ROOT / "src" / "clips"))
    m = importlib.import_module(module)
    _clip = getattr(m, cls)()
    _clip.setup()


def _render(i):
    t = _clip.t0 + i / FPS
    rgb = _clip.frame_rgb(t)
    return i, (rgb * 255 + 0.5).astype(np.uint8).tobytes()


def render_clip(module, cls, out, workers=6, start=None, end=None, step=1, crf=12):
    """Encode frames to an intermediate file. start/end in song seconds for partial previews."""
    import importlib
    sys.path.insert(0, str(ROOT / "src" / "clips"))
    m = importlib.import_module(module)
    clip = getattr(m, cls)
    a = int(round(((start if start is not None else clip.t0) - clip.t0) * FPS))
    b = int(round(((end if end is not None else clip.t1) - clip.t0) * FPS))
    idx = list(range(a, b, step))
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    cmd = ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
           "-s", f"{W}x{H}", "-r", str(FPS // step), "-i", "-", "-c:v", "libx264", "-preset", "medium",
           "-crf", str(crf), "-pix_fmt", "yuv420p", "-color_primaries", "bt709", "-color_trc", "bt709",
           "-colorspace", "bt709", "-vf", "scale=out_color_matrix=bt709:out_range=tv", str(out)]
    ff = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    t0 = time.time()
    ctx = mp.get_context("spawn")
    # workers are replaced now and then, so memory a long render slowly gathers goes back to the system
    with ctx.Pool(workers, initializer=_init, initargs=(module, cls), maxtasksperchild=60) as pool:
        # batches, so finished frames can never pile up in memory faster than the encoder takes them
        n = 0
        size = workers * 2
        for s_ in range(0, len(idx), size):
            for i, data in pool.imap(_render, idx[s_:s_ + size]):
                ff.stdin.write(data)
                if n % 30 == 0:
                    print(f"{cls} {n}/{len(idx)} {time.time() - t0:.0f}s", flush=True)
                n += 1
    ff.stdin.close()
    ff.wait()
    print(f"DONE {out} {len(idx)} frames in {time.time() - t0:.0f}s", flush=True)


def still(module, cls, times, out_dir, scale=1.0):
    """Debug stills at given song times."""
    import importlib
    sys.path.insert(0, str(ROOT / "src" / "clips"))
    m = importlib.import_module(module)
    clip = getattr(m, cls)()
    clip.setup()
    Path(out_dir).mkdir(parents=True, exist_ok=True)
    for t in times:
        rgb = clip.frame_rgb(t)
        im = (rgb * 255 + 0.5).astype(np.uint8)[..., ::-1]
        if scale != 1.0:
            im = cv2.resize(im, None, fx=scale, fy=scale, interpolation=cv2.INTER_AREA)
        cv2.imwrite(str(Path(out_dir) / f"{clip.name}_{t:07.3f}.png"), im)
