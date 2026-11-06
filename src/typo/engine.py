"""Glyph-level Japanese typesetting: HarfBuzz shaping + Skia outlines.

Every glyph comes back as its own path with a pen position, so lyric animation can move,
reveal, scale or distort characters one by one. Vertical text uses HarfBuzz "ttb"
direction with the font's vertical metrics and the vert/vrt2 features, which gives the
proper vertical forms of small kana, long-vowel marks, brackets and punctuation.

Coordinates: pixels, y down. A run's origin is the top-left of its first em box for
vertical text and the baseline start for horizontal text.
"""
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path

import numpy as np
import skia
import uharfbuzz as hb

FONT_DIR = Path(__file__).resolve().parents[2] / "assets" / "fonts" / "ttf"


def font_path(name):
    p = Path(name)
    if p.is_file():
        return p
    hits = sorted(FONT_DIR.glob(f"{name}*"))
    if not hits:
        raise FileNotFoundError(name)
    return hits[0]


@lru_cache(maxsize=None)
def _hb_font(path, variations):
    blob = hb.Blob.from_file_path(str(path))
    face = hb.Face(blob)
    f = hb.Font(face)
    if variations:
        f.set_variations(dict(variations))
    return f, face.upem


@lru_cache(maxsize=None)
def _sk_typeface(path, variations):
    tf = skia.Typeface.MakeFromFile(str(path))
    if variations:
        axes = []
        for tag, val in variations:
            axes.append(skia.FontArguments.VariationPosition.Coordinate(
                int.from_bytes(tag.encode(), "big"), float(val)))
        args = skia.FontArguments()
        args.setVariationDesignPosition(skia.FontArguments.VariationPosition(
            skia.FontArguments.VariationPosition.Coordinates(axes)))
        tf = tf.makeClone(args)
    return tf


@dataclass
class Glyph:
    gid: int
    cluster: int          # index into the source string
    char: str
    x: float              # pen position (glyph origin) in run space
    y: float
    path: skia.Path = field(repr=False)
    adv: float = 0.0


@dataclass
class Run:
    text: str
    glyphs: list
    size: float
    vertical: bool
    width: float          # extent across the reading direction (vertical: column width)
    length: float         # extent along the reading direction

    def bounds(self):
        r = skia.Rect.MakeEmpty()
        for g in self.glyphs:
            b = g.path.computeTightBounds()
            r.join(b.makeOffset(g.x, g.y))
        return r


def shape(text, font="NotoSansJP", size=64.0, vertical=False, features=None,
          variations=None, tracking=0.0):
    """Shape `text` into positioned glyph paths."""
    if not text:
        return Run(text, [], size, vertical, size if vertical else 0.0, 0.0 if vertical else size)
    path = font_path(font)
    var = tuple(sorted((variations or {}).items()))
    hbf, upem = _hb_font(str(path), var)
    buf = hb.Buffer()
    buf.add_str(text)
    buf.guess_segment_properties()
    if vertical:
        buf.direction = "ttb"
    feats = {"kern": True}
    if vertical:
        feats.update({"vert": True, "vrt2": True})
    feats.update(features or {})
    hb.shape(hbf, buf, feats)
    scale = size / upem
    skf = skia.Font(_sk_typeface(str(path), var), size)
    skf.setEdging(skia.Font.Edging.kAntiAlias)
    skf.setSubpixel(True)
    skf.setHinting(skia.FontHinting.kNone)
    glyphs = []
    pen_x = pen_y = 0.0
    for info, pos in zip(buf.glyph_infos, buf.glyph_positions):
        gid = info.codepoint
        gp = skf.getPath(gid) or skia.Path()
        if vertical:
            # HarfBuzz already subtracts the vertical origin (top-centre of the em box)
            # from the offsets, so pen + offset is the glyph's drawing origin. The pen
            # runs down the column's centre line; x = 0 is the column's left edge.
            gx = pen_x + pos.x_offset * scale + size / 2
            gy = pen_y - pos.y_offset * scale
            adv = -pos.y_advance * scale + tracking
            glyphs.append(Glyph(gid, info.cluster, text[info.cluster], gx, gy, gp, adv))
            pen_y += adv
        else:
            gx = pen_x + pos.x_offset * scale
            gy = pen_y - pos.y_offset * scale
            adv = pos.x_advance * scale + tracking
            glyphs.append(Glyph(gid, info.cluster, text[info.cluster], gx, gy, gp, adv))
            pen_x += adv
    if vertical:
        return Run(text, glyphs, size, True, size, pen_y)
    return Run(text, glyphs, size, False, pen_x, size)


def glyph_path(g, scale=1.0, dx=0.0, dy=0.0, rot=0.0, pivot=None):
    """Glyph outline transformed: scaled/rotated about its em-box centre (or `pivot`)."""
    p = skia.Path(g.path)
    b = g.path.computeTightBounds()
    cx, cy = pivot if pivot else (b.centerX(), b.centerY())
    m = skia.Matrix()
    m.preTranslate(g.x + dx + cx, g.y + dy + cy)
    if rot:
        m.preRotate(rot)
    if scale != 1.0:
        m.preScale(scale, scale)
    m.preTranslate(-cx, -cy)
    p.transform(m)
    return p


class Canvas:
    """RGBA float canvas backed by a Skia raster surface (premultiplied, sRGB 8-bit)."""

    def __init__(self, w, h):
        self.w, self.h = w, h
        self.surface = skia.Surface(w, h)
        self.c = self.surface.getCanvas()
        self.c.clear(skia.Color4f(0, 0, 0, 0))

    def fill_path(self, path, rgba, aa=True):
        p = skia.Paint(AntiAlias=aa, Color4f=skia.Color4f(*rgba))
        self.c.drawPath(path, p)

    def stroke_path(self, path, rgba, width, join=skia.Paint.kRound_Join):
        p = skia.Paint(AntiAlias=True, Color4f=skia.Color4f(*rgba), Style=skia.Paint.kStroke_Style,
                       StrokeWidth=width, StrokeJoin=join)
        self.c.drawPath(path, p)

    def array(self):
        """Straight-alpha float32 RGBA (0..1)."""
        img = self.surface.makeImageSnapshot()
        a = img.toarray(colorType=skia.ColorType.kRGBA_8888_ColorType,
                        alphaType=skia.AlphaType.kUnpremul_AlphaType).astype(np.float32) / 255.0
        return a


def draw_run(cv, run, x, y, rgba=(1, 1, 1, 1), stroke=None, upto=None):
    """Draw a run at (x, y). `upto`: only glyphs whose cluster < upto (reveal)."""
    for g in run.glyphs:
        if upto is not None and g.cluster >= upto:
            continue
        p = glyph_path(g, dx=x, dy=y)
        if stroke:
            cv.stroke_path(p, stroke[0], stroke[1])
        cv.fill_path(p, rgba)
