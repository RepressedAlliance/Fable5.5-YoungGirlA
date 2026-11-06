"""Clip 2 painter: EXR passes to finished frames, with the newspaper and the chalk writing live."""
import json
import math
import os
import re
import sys
from pathlib import Path

import cv2
import numpy as np
import skia

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "src" / "npr"), str(ROOT / "src" / "three")]
import comp  # noqa: E402
import engine as E  # noqa: E402
import shared_c2 as S  # noqa: E402

PAGE_PX = (1200, 840)   # width, height of the live page
BOARD_PX = (2736, 708)
_cache = {}


def freeze_lut():
    if "lut" not in _cache:
        _cache["lut"] = S.freeze_table(json.loads((ROOT / "work" / "render" / "c2_objects.json").read_text()))
    return _cache["lut"]


def _lines():
    return S.L


def page_base():
    if "page" in _cache:
        return _cache["page"]
    w, h = PAGE_PX
    surf = skia.Surface(w, h)
    c = surf.getCanvas()
    c.clear(E.col("#EDE7D3"))
    # masthead
    E.rect(c, 40, 34, w - 80, 6, E.INK)
    E.Type("日刊 東都新聞", "ShipporiMinchoB1-ExtraBold", 40).draw(c, 42, 66, E.INK, ax=0, ay=0)
    E.Type("第2万1408号", "ZenKakuGothicNew-Regular", 16).draw(c, w - 44, 66, E.INK, ax=1, ay=0)
    E.rect(c, 40, 118, w - 80, 2, E.INK)
    # the photograph: her with the bar, printed coarsely in the page
    img = E.load_image(ROOT / "assets" / "gen" / "final" / "p01_bust_front.png")
    px, py, pw, ph = 40, 134, 400, 520
    E.rect(c, px, py, pw, ph, "#CFC7AF")
    c.save()
    c.clipRect(skia.Rect.MakeXYWH(px, py, pw, ph))
    E.draw_image(c, img, px + pw / 2, py + 40, 0.40, ax=0.5, ay=0.0)
    c.restore()
    c.drawRect(skia.Rect.MakeXYWH(px, py, pw, ph), skia.Paint(Color4f=E.col(E.INK), Style=skia.Paint.kStroke_Style, StrokeWidth=2, AntiAlias=True))
    # small body text columns, real text at reading size, in vertical setting
    body = ("関係者によると少女Aはあの日の朝いつも通り家を出たという。同級生の一人は普通の子だったと話すが、"
            "別の同級生はいつかこうなると思っていたと語る。近所の住民は挨拶のできるいい子だったと話した。"
            "学校側は取材に応じていない。少女Aをめぐっては様々な情報が飛び交っており、インターネット上では"
            "真偽不明の書き込みが相次いでいる。専門家は思春期特有の問題だと指摘する。一方で別の専門家は"
            "そうした見方に疑問を呈している。少女Aの本当の姿はいまだ分かっていない。本人の話を聞いた者はいない。")
    E.fit("同級生「普通の子だった」　別の同級生「いつかやると」", "ZenKakuGothicNew-Black", w - 530, 40, max_size=30).draw(c, 480, 268, E.INK, ax=0, ay=0)
    E.rect(c, 480, 316, w - 520, 3, E.INK)
    cols = 15
    x = w - 60
    step = 44
    per = 20
    i = 0
    y0 = 336
    while cols > 0 and i < len(body):
        t = body[i:i + per]
        i += per
        E.Type(t, "ShipporiMincho-Medium", 24, vertical=True).draw(c, x, y0, E.INK, ax=0.5, ay=0)
        x -= step
        cols -= 1
    # caption under the photo
    E.Type("写真：少女A（関係者提供）", "ZenKakuGothicNew-Regular", 18).draw(c, 42, 670, E.INK, ax=0, ay=0)
    img_arr = surf.makeImageSnapshot().toarray(colorType=skia.ColorType.kRGBA_8888_ColorType,
                                               alphaType=skia.AlphaType.kOpaque_AlphaType)
    _cache["page"] = img_arr
    return img_arr


def flat_word(c):
    """The first word and its strip, flat on the page in the block's place: the block's size, centre and tilt."""
    c.save()
    c.translate(600, 389)
    c.rotate(-7)
    word = E.Type("寒い", "ShipporiMinchoB1-ExtraBold", 306)
    # one hard shadow tone, then ink, then the colour, like every other printed thing
    word.draw(c, 11, 11, "#8E8A78", stroke=("#8E8A78", 15))
    word.draw(c, 0, 0, E.INK, stroke=(E.INK, 15))
    word.draw(c, 0, 0, E.CYAN)
    c.translate(0, 190)
    E.rect(c, -287, -24, 590, 68, "#8E8A78")
    E.rect(c, -295, -34, 590, 68, E.PAPER)
    c.drawRect(skia.Rect.MakeXYWH(-295, -34, 590, 68), skia.Paint(AntiAlias=True, Color4f=E.col(E.INK), Style=skia.Paint.kStroke_Style, StrokeWidth=3))
    E.fit("少女A、あの日の足取り", "ZenKakuGothicNew-Bold", 540, 50).draw(c, 0, 0, E.INK)
    c.restore()


def flat_crack(c):
    """The first word's crack, printed where the block's crack was, so that nothing jumps when the block goes flat."""
    h = S.HITS[0]
    scale = h["size"] * 0.55
    ca, sa = math.cos(S.PAGE_ANGLE), math.sin(S.PAGE_ANGLE)
    w, ph = PAGE_PX
    paint = skia.Paint(AntiAlias=True, Color4f=E.col("#17171D"))
    for spoke in S.crack_spokes(100):
        path = skia.Path()
        for k, (x, y) in enumerate(spoke):
            wx, wy = x * scale, y * scale
            dx, dy = wx * ca + wy * sa, -wx * sa + wy * ca
            px, py = (S.PAGE_W / 2 - dx) / S.PAGE_W * w, (dy + S.PAGE_H / 2) / S.PAGE_H * ph
            (path.moveTo if k == 0 else path.lineTo)(px, py)
        path.close()
        c.drawPath(path, paint)


def page_tex(t):
    """The sung words print themselves across the headline area, character by character."""
    base = page_base()
    h, w = base.shape[:2]
    surf = skia.Surface(w, h)
    c = surf.getCanvas()
    c.clear(skia.Color4f(0, 0, 0, 0))
    im = E.np_to_image(np.dstack([base[..., :3], np.full((h, w), 255, np.uint8)]))
    c.drawImage(im, 0, 0)
    line = _lines()[18]
    # only the second half of the phrase falls in this clip
    chars = [ch for ch in line["chars"]]
    text = line["text"]
    start = text.index("時", 3) if False else None
    show = "「時に躓いたって」"
    # time of each visible char, taken from the singing
    ts = {}
    want = list("時に躓いたって")
    idx = [i for i, ch in enumerate(chars) if ch["c"] == "時"]
    begin = idx[-1]
    seq = [ch for ch in chars[begin:] if ch["c"] not in "「」"]
    size_box = (w - 500, 310)
    run = _headline()
    x0, y0 = 480, 150
    for g in run.run.glyphs:
        cidx = g.cluster
        ch = show[cidx]
        if ch == "「":
            tt = seq[0]["t"] - 0.05
        elif ch == "」":
            tt = seq[-1]["t"] + 0.25
        else:
            tt = seq[min(cidx - 1, len(seq) - 1)]["t"]
        if t < tt:
            continue
        # the glyph lands with a very short print-on
        a = E.clamp01((t - tt) / 0.04)
        c.save()
        p = E.typo.glyph_path(g, dx=x0 - run.l, dy=y0 - run.t)
        c.drawPath(p, skia.Paint(AntiAlias=True, Color4f=E.col(E.INK, a)))
        c.restore()
    if t >= S.WORD_FLAT_T:
        if t < 900:      # (the next clip keeps the page without it)
            flat_crack(c)
        flat_word(c)
    arr = surf.makeImageSnapshot().toarray(colorType=skia.ColorType.kRGBA_8888_ColorType,
                                           alphaType=skia.AlphaType.kUnpremul_AlphaType)
    return arr.astype(np.float32) / 255


def _headline():
    if "head" not in _cache:
        w, h = PAGE_PX
        _cache["head"] = E.fit("「時に躓いたって」", "ShipporiMinchoB1-ExtraBold", w - 520, 190)
    return _cache["head"]


def _chalk_font():
    if "chalk" not in _cache:
        _cache["chalk"] = E.fit("言い寄らないで", "YujiBoku-Regular", BOARD_PX[0] * 0.44, BOARD_PX[1] * 0.50)
    return _cache["chalk"]


def board_tex(t):
    """Chalk writes the last words by itself on the free half of the board."""
    w, h = BOARD_PX
    line = _lines()[21]
    chars = [c for c in line["chars"] if c["c"] not in "寒"]
    # after the four samui, the words start
    txt = "言い寄らないで"
    cs = [c for c in line["chars"] if c["c"] in txt][-len(txt):] if False else None
    seq, i = [], 0
    for c in line["chars"]:
        if i < len(txt) and c["c"] == txt[i] and (i > 0 or c["t"] > 78.5):
            seq.append(c["t"])
            i += 1
    if not seq or t < seq[0]:
        return None
    surf = skia.Surface(w, h)
    c = surf.getCanvas()
    c.clear(skia.Color4f(0, 0, 0, 0))
    ty = _chalk_font()
    x0 = w * 0.53 - ty.l
    y0 = h * 0.50 - ty.t - ty.h / 2
    rng = np.random.default_rng(3)
    for g in ty.run.glyphs:
        if g.cluster >= len(seq):
            continue
        tt = seq[g.cluster]
        if t < tt:
            continue
        b = g.path.computeTightBounds()
        reveal = E.ease_out((t - tt) / 0.30, 2)
        c.save()
        c.clipRect(skia.Rect.MakeLTRB(x0 + g.x + b.left() - 3, y0 + g.y + b.top() - 3,
                                      x0 + g.x + b.right() + 3, y0 + g.y + b.top() + b.height() * reveal + 3))
        p = E.typo.glyph_path(g, dx=x0, dy=y0)
        c.drawPath(p, skia.Paint(AntiAlias=True, Color4f=E.col("#F6F8F2")))
        # a chalk line has real width: the brush font is thin, and from the back of a room it must still read
        c.drawPath(p, skia.Paint(AntiAlias=True, Color4f=E.col("#F6F8F2"), Style=skia.Paint.kStroke_Style, StrokeWidth=7,
                                 StrokeJoin=skia.Paint.kRound_Join))
        c.restore()
    arr = surf.makeImageSnapshot().toarray(colorType=skia.ColorType.kRGBA_8888_ColorType,
                                           alphaType=skia.AlphaType.kUnpremul_AlphaType).astype(np.float32) / 255
    # chalk has tooth: hard flecks where the stick skipped
    n = comp.noise(h, w, 3, 77) * 0.6 + comp.noise(h, w, 9, 78) * 0.4
    arr[..., 3] = arr[..., 3] * np.where(n < 0.16, 0.0, 1.0)
    return arr


def look_at(t, ids):
    live = {}
    if "page" in ids:
        o, u_end, v_end = S.page_uv_axes()
        live[ids["page"]] = (o, u_end, v_end, page_tex(t))
    bt = board_tex(t)
    if bt is not None:
        by = 9.18 - 0.02
        live[ids["board"]] = ((-2.28, by, 2.21), (2.28, by, 2.21), (-2.28, by, 1.03), bt)
    # until the first block lands the page must read as flat print: no light falling across it
    force = [ids["page"]] if "page" in ids and t < S.RISE_START - 0.02 else []
    # and once the word lies flat on it, the page is one clean bright sheet in the frozen room, as in the next clip
    if "page" in ids and t >= S.PAGE_CLEAN_T:
        force = [ids["page"], ids.get("under", -1)]
    # once the sun has gone, the board holds its own colour and the chalk on it stays pure white
    if t > 78.4:
        force = force + [ids["board"]]
    # warm, clean afternoon shadow on the part of the room that has not frozen yet
    return comp.Look(snow=S.snow_at(t), live=live, line_px=3.0, line_near=1.25, force_lit=force, freeze_lut=freeze_lut(), time=t,
                     bright_ice=True, shadow_tint=(0.93, 0.86, 0.82))


def _hex(h):
    h = h.lstrip("#")
    return np.array([int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)], np.float32)


def _ramp(v, stops):
    """Flat colour by value, along a run of hand-picked colours: the hue moves as the value drops, so nothing goes grey."""
    xs = [a for a, _ in stops]
    cs = np.stack([_hex(c) for _, c in stops])
    return np.stack([np.interp(v, xs, cs[:, k]) for k in range(3)], -1).astype(np.float32)


# Colour of the frozen room. value 0 is ink dark, 1 is the white of the wall. The look-development runs compared four colour plans at
# full size (clear ice, lavender, the song's cyan, cold pink); this one takes the ice for the light planes and the lavender for the deep ones.
PAL = dict(lit=[(0, "#1E2358"), (.30, "#6B74D6"), (.55, "#C9E6FB"), (.85, "#F0FAFF"), (1, "#FCFEFF")],
           sh=[(0, "#1A1F50"), (.30, "#5462BE"), (.45, "#8496E2"), (.62, "#A4C0F2"), (.85, "#BDE0F8"), (1, "#D2EEFC")],
           wood_lit=[(0, "#5C4A5E"), (.45, "#BC9078"), (.75, "#E2BC96")],
           wood_sh=[(0, "#463B5A"), (.45, "#9C8490"), (.75, "#BEA6A2")])
# What has not frozen yet is warm all through: left alone the desks' steel and the shelves are neutral grey, and her desk, the warmest thing in the room, had a grey body.
WARM_STEEL = [(0, "#241A22"), (.2, "#4A3236"), (.42, "#8B5E4C"), (.6, "#B98A68"), (.8, "#E2C6A0"), (1, "#F6ECD8")]
WARM_SHADOW = (0.98, 0.88, 0.79)
SNOW_WHITE = "#FBFEFF"
FROST = "#F6FCFF"
PANE_FROST = ("#F4FCFF", "#CFE6FB")
# Outside the windows, far to near. Before the cold reaches it each thing has its summer colour; each freezes on a blow. Paler towards the horizon, so the
# windows have depth, give way to what is in the room, and the cyan of the words stands out against them.
OUT = dict(sky0=("#03C3FB", "#2FCBFB", "#74DAFB", "#BCEEFC"), sky1=("#35C2F5", "#74D5F7", "#ADE6FA", "#DDF5FD"),
           cloud=("#F7FDFF", "#CFE3FA"),
           hill0=("#6FB4B8", "#8EC9C4"), hill1=("#B3C4F2", "#F2FAFF"),
           town0=("#D9C7AC", "#B9765E", "#A8B8AE", "#C9B59A"), town1=("#9FB2EC", "#F7FCFF", "#7F92E2", "#B4C4F2"),
           tree0=("#2F7E62", "#58A873", "#5E4C48", "#7DB89C", "#A3D0AE"), tree1=("#6474D4", "#FBFEFF", "#4B58B4", "#9BAEEA", "#EFF8FF"))
BEAM = 0.18      # how much of the white a shaft of light in the air adds


def _objects():
    """Object tables the painter needs, by id: name, and the rectangle of each desk's top."""
    if "objs" not in _cache:
        objs = json.loads((ROOT / "work" / "render" / "c2_objects.json").read_text())
        n = max(o["id"] for o in objs) + 2
        rect = np.zeros((n, 4), np.float32)
        is_desk = np.zeros(n, bool)
        is_word = np.zeros(n, bool)
        for o in objs:
            name = o["name"].split(".")[0]
            is_word[o["id"]] = re.fullmatch(r"w\d+", name) is not None
            if name.startswith("desk_") and not name.endswith("_chair"):
                # the top is 0.62 by 0.44; the bag hook sticks out on the +x side only
                rect[o["id"]] = (o["lo"][0], o["lo"][0] + 0.62, o["lo"][1], o["lo"][1] + 0.44)
                is_desk[o["id"]] = True
        _cache["objs"] = ({o["name"]: o["id"] for o in objs}, rect, is_desk)
        _cache["is_word"] = is_word
    return _cache["objs"]


def _tri(u):
    return np.abs(np.mod(u, 1.0) - 0.5) * 2


def _teeth(s, seed):
    """A row of sharp uneven ice teeth along an edge: 0..1 by position along it."""
    return 0.50 * _tri(s * 5.3 + seed) + 0.32 * _tri(s * 13.7 + seed * 2.1) + 0.18 * _tri(s * 31.0 + seed * 0.7)


def desk_frost(ioid, pos, normal, t):
    """Frost grows in from the edges of each desk top from the moment that desk froze: hard, toothed, whiter at the corners."""
    _, rect, is_desk = _objects()
    lut = freeze_lut()
    ids = np.clip(ioid, 0, len(is_desk) - 1)
    m = is_desk[ids] & (normal[..., 2] > 0.9) & (pos[..., 2] > 0.69)
    if not m.any():
        return m
    r = rect[ids]
    g = np.clip((t - lut[np.clip(ids, 0, len(lut) - 1)]) / 1.5, 0, 1).astype(np.float32)
    g = 1 - (1 - g) ** 2
    dx = np.minimum(pos[..., 0] - r[..., 0], r[..., 1] - pos[..., 0])
    dy = np.minimum(pos[..., 1] - r[..., 2], r[..., 3] - pos[..., 1])
    along = np.where(dx < dy, pos[..., 1], pos[..., 0])
    seed = ids * 0.37
    reach = (0.012 + 0.085 * _teeth(along, seed)) * g
    corner = np.sqrt(dx * dx + dy * dy)
    ang = np.arctan2(dy, dx + 1e-4)
    return m & (g > 0) & ((np.minimum(dx, dy) < reach) | (corner < (0.05 + 0.13 * _tri(ang * 2.6 + seed)) * g))


_PANES = ((0.42, 3.03), (3.47, 6.08), (6.52, 8.78))


def pane_frost(pos, sky, t, eye):
    """Frost on the window panes, read off the view ray where it crosses the glass. Two flat tones, from the corners and the bottom edge."""
    out0 = np.zeros(sky.shape, bool)
    out1 = np.zeros(sky.shape, bool)
    g = S.ease_out(S.seg(t, S.HIT_T[5], S.T1 - 0.3), 1.7)
    if g <= 0 or not sky.any():
        return out0, out1
    X = -3.82
    k = (X - eye[0]) / (pos[..., 0][sky] - eye[0])
    y = eye[1] + (pos[..., 1][sky] - eye[1]) * k
    z = eye[2] + (pos[..., 2][sky] - eye[2]) * k
    # each window is two sashes, so each sash has its own corners
    sash_lo, sash_hi = [], []
    for a, b in _PANES:
        mid = (a + b) / 2
        sash_lo += [a, mid]
        sash_hi += [mid, b]
    sash_lo, sash_hi = np.array(sash_lo, np.float32), np.array(sash_hi, np.float32)
    i = np.clip(np.searchsorted(sash_lo, y) - 1, 0, len(sash_lo) - 1)
    dy = np.minimum(y - sash_lo[i], sash_hi[i] - y)
    zb, zt = 0.94, 2.36
    bar = 1.91
    low = z < bar
    dz = np.where(low, z - zb, np.minimum(z - bar, zt - z))
    bottom = np.where(low, z - zb, z - bar)
    seed = i * 1.3
    teeth = _teeth(y * 0.55, seed)
    teeth2 = _teeth(y * 0.55 + 0.21, seed + 2.0)
    corner = np.sqrt(np.maximum(dy, 0) ** 2 + np.maximum(dz, 0) ** 2)
    ang = np.arctan2(dz, dy + 1e-4)
    fan = _tri(ang * 3.1 + seed)
    near = (bottom < (0.015 + 0.15 * teeth) * g) | (corner < (0.09 + 0.05 * fan) * g)
    far = (bottom < (0.03 + 0.25 * teeth2) * g) | (corner < (0.15 + 0.08 * fan) * g)
    out0[sky] = near
    out1[sky] = far
    return out0, out1


def _blocks(y, cell, seed, n=97):
    """Same value along each stretch of a street: 0..1 per block, and the block's number."""
    i = np.floor(y / cell).astype(np.int64)
    tab = np.random.default_rng(seed).random(n).astype(np.float32)
    return tab[np.mod(i, n)], i


def _trees(seed, gap):
    """Cedars along the edge of the grounds: (y, foot z, height, half width)."""
    key = ("trees", seed)
    if key not in _cache:
        r = np.random.default_rng(seed)
        rows = []
        y = -60.0
        while y < 80.0:
            y += r.uniform(*gap)
            rows.append((y, r.uniform(-4.2, -3.2), r.uniform(6.0, 7.6), r.uniform(1.5, 2.0)))
        _cache[key] = np.array(rows, np.float32)
    return _cache[key]


def _cedars(y, z, trees):
    """Three tiers each. Returns where the trees are, and which part of that is the upper, lit or snow-laden, side of a tier."""
    body = np.zeros(len(y), bool)
    cap = np.zeros(len(y), bool)
    trunk = np.zeros(len(y), bool)
    for cy, z0, ht, hw in trees:
        near = np.abs(y - cy) < hw * 1.05
        if not near.any():
            continue
        dy = np.abs(y - cy)
        for k, (b, u, wid) in enumerate(((0.16, 0.62, 1.0), (0.42, 0.84, 0.78), (0.66, 1.0, 0.54))):
            zb, zu = z0 + ht * b, z0 + ht * u
            f = (zu - z) / (zu - zb)
            tier = near & (f > 0) & (f < 1) & (dy < hw * wid * f)
            body |= tier
            # the snow's lower edge hangs in teeth, cut off by the tier below
            cap |= tier & (f < 0.60 + 0.20 * _tri((y - cy) * 2.3 + k * 0.4))
        trunk |= (dy < hw * 0.10) & (z < z0 + ht * 0.2)
    return body, cap & body, trunk


def _clouds():
    if "clouds" not in _cache:
        r = np.random.default_rng(31)
        rows = []
        for y in np.arange(-900.0, 900.0, 165.0):
            y0 = y + r.uniform(-50, 50)
            z0 = r.uniform(22, 46)
            for k in range(4):
                rows.append((y0 + k * r.uniform(16, 26), z0 + r.uniform(0, 3), r.uniform(20, 34), r.uniform(3.5, 7.5)))
        _cache["clouds"] = np.array(rows, np.float32)
    return _cache["clouds"]


def outside(pos, glass, t, eye):
    """What is seen through the glass, worked out from the view ray, far to near: sky in flat bands, clouds, hills, the town, the trees in the school grounds.
    Each is at its own distance, so it all slides against the window bars as the camera moves. No ink: it stays behind the room."""
    out = np.zeros(pos.shape, np.float32)
    d = (pos[glass] - eye).astype(np.float32)
    if not len(d):
        return out
    dx = np.minimum(d[:, 0], -1e-3)
    def at(X):
        k = (X - eye[0]) / dx
        return eye[1] + d[:, 1] * k, eye[2] + d[:, 2] * k
    cold0, cold1, cold2 = t >= S.HIT_T[5], t >= S.HIT_T[6], t >= S.HIT_T[7]
    # sky
    y, z = at(-220.0)
    bands = OUT["sky1"] if cold0 else OUT["sky0"]
    wob = 1.6 * np.sin(y * 0.021) + 1.0 * np.sin(y * 0.053 + 1.3)
    rgb = np.broadcast_to(_hex(bands[3]), d.shape).copy()
    for lim, col in ((12.0, bands[2]), (22.0, bands[1]), (34.0, bands[0])):
        rgb[z + wob > lim] = _hex(col)
    # clouds: flat shapes with a shaded belly, drifting very slowly
    cl = _clouds()
    yy = y - 2.2 * t
    body = np.zeros(len(d), bool)
    belly = np.zeros(len(d), bool)
    for cy, cz, ry, rz in cl:
        near = np.abs(yy - cy) < ry
        if near.any():
            e = ((yy - cy) / ry) ** 2
            body |= near & (e + ((z - cz) / rz) ** 2 < 1)
            belly |= near & (e + ((z - cz - rz * 0.42) / rz) ** 2 < 1)
    rgb[body] = _hex(OUT["cloud"][1])
    rgb[body & belly] = _hex(OUT["cloud"][0])
    # hills
    h = 7.5 + 5.0 * np.sin(y * 0.017 + 0.6) + 2.6 * np.sin(y * 0.047 + 2.1) + 1.0 * np.sin(y * 0.13)
    m = z < h
    hc = OUT["hill1"] if cold0 else OUT["hill0"]
    rgb[m] = _hex(hc[0])
    if cold0:
        cap = m & (h - z < 2.2 + 1.8 * _tri(y * 0.06))
    else:
        cap = m & (z < h - 2.5 - 1.5 * _tri(y * 0.05))
    rgb[cap] = _hex(hc[1])
    # the town: flat roofs along the street
    y, z = at(-58.0)
    v, i = _blocks(y, 6.5, 3)
    v2, _ = _blocks(y, 6.5, 4)
    h = -1.0 + 5.2 * v
    m = z < h
    tc = OUT["town1"] if cold1 else OUT["town0"]
    rgb[m] = np.where((v2 > 0.5)[..., None], _hex(tc[0]), _hex(tc[3]))[m]
    win = m & (np.mod(y, 1.25) < 0.62) & (np.mod(z, 1.3) < 0.62) & (z < h - 0.9)
    rgb[win] = _hex(tc[2])
    roof = m & (h - z < (0.42 + 0.30 * _tri(y * 0.9) if cold1 else 0.55))
    rgb[roof] = _hex(tc[1])
    # the cedars at the edge of the school grounds, a far row and a near row
    k = OUT["tree1"] if cold2 else OUT["tree0"]
    for X, seed, gap, tones in ((-34.0, 25, (4.5, 7.5), (k[3], k[4], k[3])), (-20.0, 23, (6.0, 11.0), (k[0], k[1], k[2]))):
        y, z = at(X)
        body, cap, trunk = _cedars(y, z, _trees(seed, gap))
        rgb[trunk] = _hex(tones[2])
        rgb[body] = _hex(tones[0])
        rgb[cap] = _hex(tones[1])
    out[glass] = rgb
    return out


def word_footing(pos, normal, t):
    """Where a word stands on a desk: a hard shadow on the desk top, running from the foot of its strip back under it. Without it the words hover."""
    m = np.zeros(pos.shape[:2], bool)
    top = (normal[..., 2] > 0.9) & (np.abs(pos[..., 2] - S.DESK_TOP_Z) < 0.012)
    if not top.any():
        return m
    for i, h in enumerate(S.HITS):
        if not h.get("on_desk") or t < S.HIT_T[i]:
            continue
        p = np.array(h["p"][:2], np.float32)
        fx, fy = h["face"][0] - p[0], h["face"][1] - p[1]
        n = math.hypot(fx, fy)
        fx, fy = fx / n, fy / n
        dx, dy = pos[..., 0] - p[0], pos[..., 1] - p[1]
        along = dx * -fy + dy * fx
        front = dx * fx + dy * fy
        wave = 0.018 * _tri(along * 7.0 + i)
        m |= top & (np.abs(along) < h["size"] * 0.56) & (front < 0.050 + wave) & (front > -0.20 - 0.05 * _tri(along * 3.0 + i * 0.4))
    return m


def beams(depth_small, eye, ray_small, sun):
    """Shafts of light standing in the air: does the view ray pass through the sun coming in at a window before it hits something? Flat, hard-edged.
    Worked out exactly: where a point on the ray came through the window plane is linear in its distance along the ray, so each limit is one cut."""
    L = np.array(sun, np.float32)
    X = -3.8
    hit = np.zeros(depth_small.shape, bool)
    # the point at distance d came through the window at y = ay + by d, z = az + bz d
    ax, bx = eye[0], ray_small[..., 0]
    k0, k1 = (ax - X) / L[0], bx / L[0]
    ay, by = eye[1] - L[1] * k0, ray_small[..., 1] - L[1] * k1
    az, bz = eye[2] - L[2] * k0, ray_small[..., 2] - L[2] * k1

    def clip(lo, hi, a, b, val_lo, val_hi):
        """narrow [lo, hi] to where val_lo < a + b d < val_hi"""
        safe = np.where(np.abs(b) < 1e-6, 1e-6, b)
        d0, d1 = (val_lo - a) / safe, (val_hi - a) / safe
        return np.maximum(lo, np.minimum(d0, d1)), np.minimum(hi, np.maximum(d0, d1))

    for pa, pb in _PANES:
        mid = (pa + pb) / 2
        for y0, y1 in ((pa, mid - 0.025), (mid + 0.025, pb)):
            lo = np.full(depth_small.shape, 0.4, np.float32)
            hi = depth_small.copy()
            lo, hi = clip(lo, hi, ay, by, y0, y1)
            lo, hi = clip(lo, hi, az, bz, 0.94, 2.36)
            # and only on the room's side of the glass
            lo = np.where(bx < 0, lo, np.maximum(lo, (X - ax) / np.where(np.abs(bx) < 1e-6, 1e-6, bx)))
            hi = np.where(bx < 0, np.minimum(hi, (X - ax) / np.where(np.abs(bx) < 1e-6, -1e-6, bx)), hi)
            hit |= hi > lo
    return hit.astype(np.float32)


# ---- snow is painted, so it can have a near, a middle and a far layer, and go behind things by the depth pass
def _snow_cloud():
    if "snow" not in _cache:
        r = np.random.default_rng(11)
        rows = []
        # (count, radius m, speed m/s, tone 0 pale .. 1 white), inside the room
        for n, rad, sp, tone in ((1100, 0.0055, 0.34, 0.0), (380, 0.0095, 0.48, 1.0), (70, 0.015, 0.66, 1.0)):
            a = np.column_stack([r.uniform(-3.7, 3.7, n), r.uniform(0.1, 9.1, n), r.uniform(0, 3.0, n), np.full(n, rad), np.full(n, sp), np.full(n, tone),
                                 r.uniform(0, 6.28, n), r.uniform(0, 3.4, n), r.uniform(0.75, 1.25, n)])
            rows.append(a)
        # and a far layer outside, seen through the glass
        n = 420
        rows.append(np.column_stack([r.uniform(-11, -4.2, n), r.uniform(-4, 13, n), r.uniform(-1, 4.5, n), np.full(n, 0.016), np.full(n, 0.42), np.full(n, 1.0),
                                     r.uniform(0, 6.28, n), r.uniform(0, 3.4, n), r.uniform(0.75, 1.25, n)]))
        _cache["snow"] = np.vstack(rows).astype(np.float64)
    return _cache["snow"]


def snow_mask(t, depth, w, h, ss):
    """Flat white flakes, drawn at render size. Returns (white, pale) masks, 0..1."""
    white = np.zeros((h, w), np.uint8)
    pale = np.zeros((h, w), np.uint8)
    if t < S.HIT_T[5]:
        return white.astype(np.float32), pale.astype(np.float32)
    c = _snow_cloud()
    e, tg, up = S.camera_at(t)
    e, tg, up = np.array(e), np.array(tg), np.array(up)
    f = tg - e
    f /= np.linalg.norm(f)
    rgt = np.cross(f, up)
    rgt /= np.linalg.norm(rgt)
    u = np.cross(rgt, f)
    age = t - S.HIT_T[5] - c[:, 7]       # each flake starts at the ceiling a little later than the last
    show = age > 0
    span = 3.2
    z = c[:, 2] - c[:, 4] * age
    z = np.where(show, 3.0 - np.mod(3.0 - z, span), -9)
    swayx = 0.05 * np.sin(age * 0.9 * c[:, 8] + c[:, 6]) + 0.06 * age
    swayy = 0.04 * np.cos(age * 0.7 * c[:, 8] + c[:, 6])
    x = c[:, 0] + swayx
    y = c[:, 1] + swayy
    rel = np.column_stack([x, y, z]) - e
    zc = rel @ f
    k = 26.0 / 36.0 * w
    sx = (rel @ rgt) / np.maximum(zc, 1e-3) * k + w / 2
    sy = -(rel @ u) / np.maximum(zc, 1e-3) * k + h / 2
    rad = c[:, 3] / np.maximum(zc, 1e-3) * k
    keep = show & (zc > 0.45) & (sx > -40) & (sx < w + 40) & (sy > -40) & (sy < h + 40)
    for i in np.nonzero(keep)[0]:
        px, py = int(sx[i]), int(sy[i])
        if 0 <= px < w and 0 <= py < h and depth[py, px] < zc[i] - 0.03:
            continue
        r_ = float(min(rad[i], 8.5 * ss))
        if r_ < 0.7:
            r_ = 0.7
        tgt = white if c[i, 5] > 0.5 else pale
        shift = 4
        cen = (int(sx[i] * (1 << shift)), int(sy[i] * (1 << shift)))
        cv2.circle(tgt, cen, int(r_ * (1 << shift)), 255, -1, cv2.LINE_AA, shift)
    return white.astype(np.float32) / 255, pale.astype(np.float32) / 255


def paint_ice(p, t, ids):
    """comp.paint's own order, with the frozen room coloured by PAL. comp.paint stays as it is: other shots use it."""
    look = look_at(t, ids)
    ss = S.SS
    col = p["DiffCol"][..., :3].astype(np.float32)
    light = p["DiffDir"][..., :3].astype(np.float32)
    depth = p["Depth"].astype(np.float32)
    normal = p["Normal"][..., :3].astype(np.float32)
    pos = np.nan_to_num(p["Position"][..., :3].astype(np.float32), posinf=1e4, neginf=-1e4)
    ob = p["IndexOB"].astype(np.float32)
    ma = np.round(p["IndexMA"]).astype(np.int32)
    h, w = depth.shape
    base = comp.linear_to_srgb(np.clip(col, 0, 1)).astype(np.float32)
    base = comp.apply_live(base, ob, pos, look.live)
    noink, graphic, sky = ma == 3, ma == 4, ma == 5
    lit = light.mean(-1) > look.light_threshold
    for oid in look.force_lit:
        lit |= np.abs(ob - oid) < 0.5
    nz, ny = normal[..., 2], normal[..., 1]
    nx = normal[..., 0]
    up, down = np.clip(nz, 0, 1), np.clip(-nz, 0, 1)
    plane = (0.93 + 0.07 * up - 0.11 * down - 0.06 * np.abs(ny))[..., None].astype(np.float32)
    # the part not yet frozen: a warm clean afternoon
    warm_base = np.where((((base.max(-1) - base.min(-1)) < 0.14) & (base[..., 2] >= base[..., 0] - 0.02))[..., None], _ramp(base.mean(-1), WARM_STEEL), base)
    warm = np.where(lit[..., None], warm_base, warm_base * np.array(WARM_SHADOW, np.float32) * (0.5 + 0.5 * plane))
    lut = look.freeze_lut
    ioid = np.clip(np.round(ob).astype(np.int32), 0, len(lut) - 1)
    frozen = lut[ioid] <= t
    g = base.mean(-1)
    # each plane keeps its own flat value, as a background painter separates them
    v = g - 0.16 * down - 0.05 * np.abs(ny) - 0.015 * np.abs(nx) - 0.02 * (1 - up)
    ice = np.where(lit[..., None], _ramp(v + 0.05, PAL["lit"]), _ramp(v, PAL["sh"]))
    names, _, _ = _objects()
    floor = np.isin(ioid, [names[k] for k in ("floor", "floor_top", "step")])
    wood = np.where(lit[..., None], _ramp(g, PAL["wood_lit"]), _ramp(g, PAL["wood_sh"]))
    ice = np.where(floor[..., None], wood, ice)
    img = np.where(frozen[..., None] & ~graphic[..., None] & ~sky[..., None], ice, warm)
    # the words keep their pure cyan even in shadow: shaded, they went dull against the window. The newspaper and the board take the shadow as before.
    _objects()
    word = _cache["is_word"][np.clip(ioid, 0, len(_cache["is_word"]) - 1)]
    img = np.where(graphic[..., None], np.where((lit | word)[..., None], base, base * np.array([0.80, 0.84, 0.92], np.float32) * plane), img)
    # snow settles on what faces up, with a hard edge. On the floor it lies in long drifts, so some of the wood is still there at the end.
    if look.snow > 0:
        f = comp.world_noise(pos, 2.3) * 0.55 + comp.world_noise(pos, 9.0, 2.0) * 0.30 + comp.world_noise(pos, 31.0, 5.0) * 0.15
        stretched = pos * np.array([0.55, 1.5, 1.0], np.float32)
        fl = comp.world_noise(stretched, 2.0, 4.0) * 0.7 + comp.world_noise(stretched, 7.0, 9.0) * 0.3
        th = np.where(floor, 0.72 - look.snow * 0.24, 1.05 - look.snow * 0.85)
        drift = (up > 0.8) & (np.where(floor, fl, f) > th) & ~noink & ~graphic & frozen & ~sky
        snow_sh = _ramp(np.full((h, w), 1.0, np.float32), PAL["sh"])
        img = np.where(drift[..., None], np.where(lit[..., None], _hex(SNOW_WHITE), snow_sh), img)
    # frost on the desk tops, on top of the snow
    fr = desk_frost(ioid, pos, normal, t) & frozen
    img = np.where(fr[..., None], np.where(lit[..., None], _hex(FROST), _hex("#E2F5FE")), img)
    foot = word_footing(pos, normal, t) & ~graphic & ~noink & ~sky
    img = np.where(foot[..., None], img * np.array([0.50, 0.52, 0.78], np.float32), img)
    eye = np.array(S.camera_at(t)[0], np.float32)
    img = np.where(noink[..., None] | sky[..., None], base, img)
    # the paper strips are the same material kind as the sky; only the sky itself is seen through glass
    glass = np.abs(ob - names["sky"]) < 0.5
    view = outside(pos, glass, t, eye)
    img = np.where(glass[..., None], view, img)
    near, far = pane_frost(pos, glass, t, eye)
    img = np.where(far[..., None], _hex(PANE_FROST[1]), img)
    img = np.where(near[..., None], _hex(PANE_FROST[0]), img)
    # shafts of light in the air, once the camera has left the page
    if t > S.RISE_END - 0.3:
        sw, sh_ = w // 2, h // 2
        dsm = cv2.resize(np.where(np.isfinite(depth) & (depth < 1e6), depth, 40.0), (sw, sh_), interpolation=cv2.INTER_NEAREST)
        e, tg, up_ = S.camera_at(t)
        e, tg, up_ = np.array(e, np.float32), np.array(tg, np.float32), np.array(up_, np.float32)
        ff = tg - e
        ff /= np.linalg.norm(ff)
        rr = np.cross(ff, up_)
        rr /= np.linalg.norm(rr)
        uu = np.cross(rr, ff)
        xx = (np.arange(sw, dtype=np.float32) + 0.5 - sw / 2) / (26.0 / 36.0 * sw)
        yy = -(np.arange(sh_, dtype=np.float32) + 0.5 - sh_ / 2) / (26.0 / 36.0 * sw)
        ray = ff + rr * xx[None, :, None] + uu * yy[:, None, None]
        # the depth pass counts along the view axis, so the samples do too
        hit = beams(dsm, e, ray, S.sun_dir_at(t))
        m = cv2.resize(hit, (w, h), interpolation=cv2.INTER_LINEAR)
        kk = ((m > 0.5).astype(np.float32) * BEAM * ~glass)[..., None]
        img = img * (1 - kk) + _hex("#F4FAFF") * kk
    lines = comp.ink_lines(ob, depth, normal, ma == 2, pos, ss, look, 0, skip_wide=noink)
    img = img * (1 - lines[..., None]) + comp.INK * lines[..., None]
    white, pale = snow_mask(t, depth, w, h, ss)
    img = img * (1 - pale[..., None]) + _hex("#D8EEFB") * pale[..., None]
    img = img * (1 - white[..., None]) + _hex(SNOW_WHITE) * white[..., None]
    img = np.clip(img, 0, 1)
    return cv2.resize(img, (int(round(w / ss)), int(round(h / ss))), interpolation=cv2.INTER_AREA)


def paint_time(exr, t, ids):
    return paint_ice(comp.read_exr(exr), t, ids)


if __name__ == "__main__":
    ids = json.loads((ROOT / "work" / "render" / "c2_ids.json").read_text())
    mode = sys.argv[1]
    if mode == "stills":
        d = Path(sys.argv[2])
        out = ROOT / "work" / "qc" / "c2"
        out.mkdir(parents=True, exist_ok=True)
        for f in sorted(d.glob("t*.exr")):
            t = float(f.stem[1:])
            rgb = paint_time(f, t, ids)
            rgb = E.paper_grain(rgb, 0.010)
            cv2.imwrite(str(out / f"{f.stem}.png"), (rgb[..., ::-1] * 255 + 0.5).astype(np.uint8))
            print(f.stem)
