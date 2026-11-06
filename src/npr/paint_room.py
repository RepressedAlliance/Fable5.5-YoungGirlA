"""Paints the dark bedroom: deep blue flat tones by the step she has adapted to, the door's wedge as a hard pale shape, ink over all.

comp.ink_lines draws the lines; the tones here are the room's own, since this is the one place in the film with no sun.
"""
import json
import math
import sys
from functools import lru_cache
from pathlib import Path

import cv2
import numpy as np
import skia

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "src" / "npr"), str(ROOT / "src" / "three"), str(ROOT / "src" / "clips"), str(ROOT / "src" / "art")]
import comp  # noqa: E402
import engine as E  # noqa: E402
import shared_room as S  # noqa: E402


def hx(h):
    h = h.lstrip("#")
    return np.array([int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)], np.float32)


# room tones per adaptation step: (darkest thing, palest thing, how much of a thing's own hue survives, ink alpha)
ROOM = [
    (hx("#04060F"), hx("#04060F"), 0.0, 0.0),
    (hx("#060A1B"), hx("#1A2654"), 0.0, 0.0),
    (hx("#070C22"), hx("#2C3B7C"), 0.05, 0.85),
    (hx("#080E27"), hx("#3F5294"), 0.12, 1.0),
]
# the wedge by step: near the door, middle, far end
WEDGE = [
    (hx("#8A97BE"), hx("#8A97BE"), hx("#8A97BE")),
    (hx("#7584B2"), hx("#5F6E9A"), hx("#4C5A86")),
    (hx("#C3C8CE"), hx("#7F8AAC"), hx("#596796")),
    (hx("#F7EBCB"), hx("#A8A3A4"), hx("#616E9A")),       # hot only right by the door: it should read as a sliver of light in a dark room
]
WEDGE_R = (0.20, 0.47)     # bands parallel to the door, the way light under a door falls away
INK = hx("#04050E")


@lru_cache(1)
def sheet_tex():
    """The sheet she gets back: the two crayon flowers, small handwritten パッパ beside them, an old fold. RGBA float."""
    import s03
    w, h = 1536, 1086
    surf = skia.Surface(w, h)
    c = surf.getCanvas()
    c.clear(E.col("#F6F3EA"))
    flowers = E.load_image(ROOT / "assets" / "gen" / "raw" / "k01_flowers.png")
    p = skia.Paint(AntiAlias=True)
    p.setBlendMode(skia.BlendMode.kMultiply)
    c.drawImage(flowers, 0, -14, E.SAMPLING, p)
    s03.draw_pappa(c, 1120, 950, 76, E.INK, seed=4)
    # the fold it was once carried in
    c.drawLine(w / 2, 0, w / 2, h, skia.Paint(AntiAlias=True, Color4f=E.col("#8A8778", 0.45), StrokeWidth=2.2))
    arr = surf.makeImageSnapshot().toarray(colorType=skia.ColorType.kRGBA_8888_ColorType, alphaType=skia.AlphaType.kOpaque_AlphaType)
    return arr.astype(np.float32) / 255


@lru_cache(1)
def calendar_tex():
    """A plain school-year calendar: a big month number and a grid of days."""
    w, h = 400, 620
    surf = skia.Surface(w, h)
    c = surf.getCanvas()
    c.clear(E.col("#EDE7D3"))
    E.Type("11", "ZenKakuGothicNew-Black", 120).draw(c, w / 2, 110, "#2A2C36")
    for r in range(6):
        for k in range(7):
            x, y = 34 + k * 48, 240 + r * 58
            col = "#B23A3F" if k == 0 else "#2A2C36"
            E.rect(c, x, y, 26, 26, col)
    arr = surf.makeImageSnapshot().toarray(colorType=skia.ColorType.kRGBA_8888_ColorType, alphaType=skia.AlphaType.kOpaque_AlphaType)
    return arr.astype(np.float32) / 255


@lru_cache(1)
def poster_tex():
    """A band poster with no people on it: big flat shapes."""
    w, h = 560, 780
    surf = skia.Surface(w, h)
    c = surf.getCanvas()
    c.clear(E.col("#D8D2C0"))
    c.drawCircle(280, 300, 190, skia.Paint(AntiAlias=True, Color4f=E.col("#3A3E50")))
    E.rect(c, 0, 520, w, 120, "#3A3E50")
    E.rect(c, 40, 680, 300, 26, "#3A3E50")
    E.rect(c, 40, 724, 190, 18, "#3A3E50")
    arr = surf.makeImageSnapshot().toarray(colorType=skia.ColorType.kRGBA_8888_ColorType, alphaType=skia.AlphaType.kOpaque_AlphaType)
    return arr.astype(np.float32) / 255


@lru_cache(1)
def screen_tex():
    """Her phone's lock screen: notifications stacking up, one red badge. Red is only for notification marks."""
    w, h = 264, 568
    surf = skia.Surface(w, h)
    c = surf.getCanvas()
    c.clear(E.col("#BFD4F2"))
    E.rect(c, 40, 44, w - 80, 40, "#E8EEF8")
    for i in range(7):
        y = 112 + i * 64
        E.rect(c, 16, y, w - 32, 56, "#F6F3EA", radius=8)
        # each one is a picture of her with the bar over the eyes, and a line of words
        E.rect(c, 24, y + 8, 40, 40, "#8FA0BC")
        E.rect(c, 24, y + 20, 40, 11, "#16182A")
        E.rect(c, 74, y + 13, w - 124 - (i * 23) % 50, 9, "#3A3E50")
        E.rect(c, 74, y + 32, w - 150 - (i * 37) % 60, 7, "#6E7686")
    c.drawCircle(w - 30, 112, 25, skia.Paint(AntiAlias=True, Color4f=E.col(E.RED)))
    arr = surf.makeImageSnapshot().toarray(colorType=skia.ColorType.kRGBA_8888_ColorType, alphaType=skia.AlphaType.kOpaque_AlphaType)
    return arr.astype(np.float32) / 255


def live_for(t, ids):
    live = {}
    if "poster" in ids:
        live[ids["poster"]] = ((-1.23, -0.003, 1.94), (-0.67, -0.003, 1.94), (-1.23, -0.003, 1.16), poster_tex())
    if "calendar" in ids:
        a = math.radians(S.calendar_drop(t))
        ca, sa = math.cos(a), math.sin(a)
        px, pz = -0.565, 1.70

        def pt(dx, dz):
            # rotation about y, the way the mesh turns about its pin
            return (px + dx * ca + dz * sa, -0.003, pz - dx * sa + dz * ca)

        live[ids["calendar"]] = (pt(-0.012, 0.012), pt(0.25, 0.012), pt(-0.012, -0.40), calendar_tex())
    if "screen" in ids and S.phone_on(t):
        a = math.radians(S.phone_turn(t))
        ca, sa = math.cos(a), math.sin(a)
        px, py = -0.70, -1.17

        def pp(dx, dy):
            return (px + dx * ca - dy * sa, py + dx * sa + dy * ca, 0.01)

        # top of the screen is the end away from the plug
        live[ids["screen"]] = (pp(0.02 + 0.033, -0.074 - 0.071), pp(0.02 - 0.033, -0.074 - 0.071), pp(0.02 + 0.033, -0.074 + 0.071), screen_tex())
    for i in range(len(S.SHEETS)):
        k = f"sheet{i}"
        if k in ids:
            ax = S.sheet_axes(i, t)
            if ax:
                live[ids[k]] = (*ax, sheet_tex())
    return live


def floorboards(pos, depth, f_px):
    """Boards run towards the door. Fixed to the world, a value per board, a dark joint between them, never a stripe however close the camera lies to it."""
    w = 0.135
    u = pos[..., 0] / w
    i = np.floor(u)
    off = np.mod(i * 0.37, 1.0) * 1.8
    j = np.floor((pos[..., 1] + off) / 1.8)
    h = np.mod(np.sin(i * 12.9898 + j * 78.233) * 43758.5453, 1.0)
    val = 0.86 + 0.28 * np.floor(h * 4) / 3
    du = np.abs(u - np.round(u)) * w
    dv = np.abs(np.mod(pos[..., 1] + off, 1.8))
    half = np.minimum(0.0022, 2.0 * np.minimum(depth, 100.0) / f_px)
    joint = ((du < half) | (dv < half) | (dv > 1.8 - half)) & (pos[..., 1] < 0.0)
    return val.astype(np.float32), joint


def floor_shadow_mask(t):
    """Painted hard shadows on the floor, in world metres, 1 mm a pixel: x from -1 to 2, y from -1.5 to 1.5."""
    m = np.zeros((3000, 3000), np.uint8)
    polys = S.foot_shadows(t) + S.corridor_shadows(t) + S.hand_shadow(t) + S.pace_shadows(t)
    for poly in polys:
        pts = np.array([((x + 1.0) * 1000, (y + 1.5) * 1000) for x, y in poly], np.float32)
        cv2.fillPoly(m, [np.round(pts * 16).astype(np.int32)], 255, lineType=cv2.LINE_AA, shift=4)
    return m


def paint_time(exr, t, ids):
    ss = S.SS
    p = comp.read_exr(exr)
    col = p["DiffCol"][..., :3].astype(np.float32)
    light = p["DiffDir"][..., 0].astype(np.float32)
    depth = p["Depth"].astype(np.float32)
    normal = p["Normal"][..., :3].astype(np.float32)
    pos = np.nan_to_num(p["Position"][..., :3].astype(np.float32), posinf=1e4, neginf=-1e4)
    ob = p["IndexOB"].astype(np.float32)
    ma = np.round(p["IndexMA"]).astype(np.int32)
    L_ = S.level(t)
    # shadow cards: flat on a floor or wall, they take that surface's id so no ink ever finds them
    card = ma == 6
    card_floor = card & (pos[..., 2] < 0.01)
    ob = np.where(card_floor, float(ids["floor"]), np.where(card, float(ids["wall_door"]), ob)).astype(np.float32)
    normal = np.where(card_floor[..., None], np.array([0, 0, 1], np.float32), np.where(card[..., None], np.array([0, -1, 0], np.float32), normal)).astype(np.float32)
    base = comp.linear_to_srgb(np.clip(col, 0, 1)).astype(np.float32)
    # the floor is painted boards; printed things go on by world position so they sit in the scene
    floor = np.abs(ob - ids["floor"]) < 0.5
    val, joint = floorboards(pos, depth, S.lens_at(t) / 36 * 1920 * ss)
    base = np.where(floor[..., None], base * val[..., None], base)
    live = live_for(t, ids)
    if live:
        base = comp.apply_live(base, ob, pos, live)
    g = (base * np.array([0.3, 0.55, 0.15], np.float32)).sum(-1, keepdims=True)
    lo, hi, sat, ink_a = ROOM[L_]
    # each plane one flat value by where it faces, as a background painter would separate them
    n = normal
    # plus one hard terminator from the window side, so a mound of cloth has a lit side and a dark side and no gradient
    moon = np.array([-0.72, 0.28, 0.62], np.float32)
    dm = (n * moon).sum(-1)
    plane = np.where(dm > 0.18, 1.0, 0.70) * (1.0 - 0.30 * np.clip(-n[..., 2], 0, 1))
    plane = np.where(np.abs(n[..., 1]) > 0.9, 0.80, plane)                 # the door wall stays one calm plane
    plane = plane[..., None].astype(np.float32)
    # curtains: pleats fixed to the cloth, two values and a fold line, so they read as cloth from this flat angle
    for key in ("curtain_a", "curtain_b"):
        if key in ids:
            cm = np.abs(ob - ids[key]) < 0.5
            ph = np.mod((pos[..., 1] + 3.0) / 0.094, 1.0)
            plane = np.where(cm[..., None], np.where(ph[..., None] < 0.5, 1.0, 0.72), plane)
    # hard cast shadow in the dark: one step down
    plane = plane * np.where(card[..., None], 0.62, 1.0)
    v = np.clip(g * plane, 0, 1) ** 1.05
    dark = lo + (hi - lo) * v + (base - g) * sat * (0.4 + v)
    # in the shots right up against the door it is a dark mass, and the light and the metal stand out from it
    shot = S.shot_at(t)[1]
    if shot in ("gap", "lever", "panel", "upper") and "door" in ids:
        k_ = {"gap": 0.42, "lever": 0.62, "panel": 0.72, "upper": 0.80}[shot]
        leaf_ = np.abs(ob - ids["door"]) < 0.5
        dark = np.where(leaf_[..., None], lo + (dark - lo) * k_, dark)
        if shot == "gap":
            dark = lo + (dark - lo) * 0.7
    # metal: one hard light from above, one dark underneath
    for key in ("lever", "rose"):
        if key in ids and L_ >= 2:
            mm = np.abs(ob - ids[key]) < 0.5
            mm &= g[..., 0] > 0.2
            top = (n[..., 2] > 0.25) | ((n[..., 1] < -0.85) & (key == "rose"))
            tone = np.where(top[..., None], hx("#B7C4EA"), hx("#232E60"))
            dark = np.where(mm[..., None], tone, dark)
    # the wedge: hard bands, nearer the door paler; no gradient anywhere
    w0, w1, w2 = WEDGE[L_]
    fm = floor_shadow_mask(t)
    # sampled smoothly and cut at half, so the edge stays clean however close the camera is
    fx = np.clip((pos[..., 0] + 1.0) * 1000, 0, 2999).astype(np.float32)
    fy = np.clip((pos[..., 1] + 1.5) * 1000, 0, 2999).astype(np.float32)
    painted_shadow = (cv2.remap(fm, fx - 0.5, fy - 0.5, cv2.INTER_LINEAR) > 127) & (pos[..., 2] < 0.03) & (light > 1e-3)
    lit = (light > 1e-3) & ~painted_shadow
    r = -pos[..., 1]
    band = np.where(r[..., None] < WEDGE_R[0], w0, np.where(r[..., None] < WEDGE_R[1], w1, w2))
    lit_tone = band * (0.60 + 0.62 * g)
    sheet_kind = ma == 4
    if L_ == 3:
        # the only colour in the room: paper in the light keeps its crayon
        lit_tone = np.where(sheet_kind[..., None], base * np.array([1.0, 0.97, 0.88], np.float32), lit_tone)
    # the strip of corridor floor seen through the gap
    corridor = pos[..., 1] > 0.0
    lit_tone = np.where((corridor & floor)[..., None], hx("#FFF4D6") if L_ else hx("#C4CCE4"), lit_tone)
    # the corridor beyond: one warm wall, one darker skirting
    if L_:
        far = pos[..., 1] > 0.5
        lit_tone = np.where((far & ~floor)[..., None], hx("#EFE3C2"), lit_tone)
        if "corr_skirt" in ids:
            lit_tone = np.where((np.abs(ob - ids["corr_skirt"]) < 0.5)[..., None], hx("#BCAA86"), lit_tone)
    # the foot of the door frame, lit from the corridor, is not paper white
    if "casing" in ids:
        lit_tone = np.where((np.abs(ob - ids["casing"]) < 0.5)[..., None], hx("#9C947F") if L_ == 3 else hx("#5C6484"), lit_tone)
    img = np.where(lit[..., None], lit_tone, dark)
    # a painted shadow is one flat deep tone; paper under it keeps only its marks, no colour (nothing goes purple)
    if painted_shadow.any():
        deep = lo + (hi - lo) * np.clip(g * 0.55, 0, 1) ** 1.2
        img = np.where(painted_shadow[..., None], deep, img)
    # step 1 shows the door and the light, nothing else
    if L_ == 1:
        keep = np.zeros(ob.shape, bool)
        for key in ("door", "casing", "lever", "rose"):
            if key in ids:
                keep |= np.abs(ob - ids[key]) < 0.5
        img = np.where((~keep & ~lit & ~painted_shadow)[..., None], lo, img)
    # step 0: nothing but the strip
    if L_ == 0:
        img = np.where((lit & corridor)[..., None], lit_tone, lo)
    # the slit in the curtains and the window behind it, a cold line that also lays a thin band on the floor
    unlit = ma == 1
    if L_ >= 1:
        win = np.abs(ob - ids.get("window_id", -1)) < 0.5
        tone = {1: hx("#2A3866"), 2: hx("#5F76B0"), 3: hx("#A9C4EC")}[L_]
        win_mask = unlit & (np.abs(pos[..., 0] - S.X0) < 0.02)
        img = np.where(win_mask[..., None], tone, img)
    else:
        win_mask = None
    # the same slit lays one thin cold line on the floor, away from the window, the way hard moonlight would
    if L_ >= 2:
        along = pos[..., 0] - S.X0
        centre = -0.62 - 0.46 * along
        half = 0.008 + 0.016 * along
        slitband = floor & (np.abs(pos[..., 1] - centre) < half) & (along < 0.98) & ~lit
        img = np.where(slitband[..., None], img + hx("#5C7BC4") * (0.55 if L_ == 3 else 0.28), img)
    # phone: its screen and two hard pools of its light on the floor around it
    if S.phone_on(t) and L_ >= 1:
        a = math.radians(S.phone_turn(t))
        px = -0.70 + 0.02 * math.cos(a) + 0.074 * math.sin(a)
        py = -1.17 + 0.02 * math.sin(a) - 0.074 * math.cos(a)
        rp = np.hypot((pos[..., 0] - px), (pos[..., 1] - py))
        low = pos[..., 2] < 0.20
        for rad, k in ((0.36, 0.10), (0.20, 0.17)):
            m = (rp < rad) & low & ~lit
            img = np.where(m[..., None], img + hx("#6E8FD0") * k, img)
        scr = np.abs(ob - ids["screen"]) < 0.5
        img = np.where(scr[..., None], base, img)
    elif "screen" in ids:
        pass
    # floor joints
    j_alpha = 0.55 if L_ >= 2 else 0.0
    if j_alpha:
        jm = (joint & floor)[..., None].astype(np.float32) * j_alpha
        img = img * (1 - jm) + INK * jm
    # a knock shakes the door against its latch: for a moment a line of the corridor's light shows down the edge
    da = abs(math.radians(S.door_angle(t)))
    if L_ == 3 and da > 0.004 and "door" in ids:
        leaf = np.abs(ob - ids["door"]) < 0.5
        edge = S.HINGE[0] + (S.DOOR_EDGE - S.HINGE[0]) * math.cos(da)
        w = min(0.03, 0.72 * math.sin(da) * 0.75)
        # the leaf has jumped off its frame: open most on the latch side, a wedge along the top, a hairline down the hinges (the hinges themselves stand in front of it)
        along = np.clip((pos[..., 0] - S.HINGE[0]) / S.DW, 0, 1)
        slit_ = leaf & (pos[..., 2] > S.GAP) & ((pos[..., 0] > edge - w) | (pos[..., 0] < S.HINGE[0] + 0.002 + w * 0.32) | (pos[..., 2] > S.DOOR_H - 0.018 - w * 0.6 * along))
        img = np.where(slit_[..., None], hx("#FFF4D6"), img)
    # paper lies flat: a shadow of a few pixels, hard, on the side away from the lamp
    if sheet_kind.any():
        px = max(2, int(round(S.lens_at(t) / 22.0 * 1.6 * ss)))
        sk = sheet_kind.astype(np.uint8)
        moved = cv2.warpAffine(sk, np.float32([[1, 0, px * 0.5], [0, 1, px]]), (sk.shape[1], sk.shape[0]), flags=cv2.INTER_NEAREST)
        sh_ = (moved > 0) & ~sheet_kind & (pos[..., 2] < 0.02)
        img = np.where(sh_[..., None], img * 0.45 + INK * 0.55, img)
    # the shoes stand against the light: what faces us nearly black but still brown leather, and one hard warm rim along whatever the lamp behind them can reach
    feet_m = np.zeros(ob.shape, bool)
    for key in ("foot0", "foot1"):
        if key in ids:
            feet_m |= np.abs(ob - ids[key]) < 0.5
    if feet_m.any():
        rim = base * 0.62 + hx("#F7EBCB") * 0.24
        shade = base * 0.46 + INK * 0.45
        tone = np.where((light > 1e-3)[..., None], rim, shade)
        tone = np.where((ma == 7)[..., None], hx("#120B0B"), tone)      # the stitched line of the apron
        img = np.where(feet_m[..., None], tone, img)
    # ink
    if ink_a > 0 or L_ == 1:
        look = comp.Look(line_px=2.6, line_near=1.3, line_min=0.8, edge_m=0.0)
        lines = comp.ink_lines(ob, depth, normal, None, pos, ss, look, seed=3)
        # on the shoes: the outline, and where one part meets another. Not every crease of the leather.
        if feet_m.any():
            inner = cv2.erode(feet_m.astype(np.uint8), np.ones((5, 5), np.uint8)) > 0
            code = np.round(base.sum(-1) * 40).astype(np.float32)
            parts_edge = cv2.morphologyEx(code, cv2.MORPH_GRADIENT, np.ones((3, 3), np.uint8)) > 0
            parts_edge &= ~(cv2.dilate((ma == 7).astype(np.uint8), np.ones((5, 5), np.uint8)) > 0)
            lines = np.where(inner, parts_edge.astype(np.float32), lines)
        cur = np.zeros(ob.shape, bool)
        for key in ("curtain_a", "curtain_b"):
            if key in ids:
                cur |= np.abs(ob - ids[key]) < 0.5
        if cur.any():
            # the pleats' overlaps sit right on the ink threshold and come out dashed: inside the curtains the ink is the fold itself
            inner = cv2.erode(cur.astype(np.uint8), np.ones((7, 7), np.uint8)) > 0
            fold = np.mod((pos[..., 1] + 3.0) / 0.094, 1.0) < 0.085
            lines = np.where(inner, fold.astype(np.float32), lines)
        # the lit floor needs its lines most; in the dark they are what gives things away
        alpha = np.where(lit, 1.0, ink_a).astype(np.float32) * lines
        if L_ == 1:
            alpha = np.where(lit, lines, 0.0).astype(np.float32)
        img = img * (1 - alpha[..., None]) + INK * alpha[..., None]
    h, w = depth.shape
    out = cv2.resize(np.clip(img, 0, 1), (int(round(w / ss)), int(round(h / ss))), interpolation=cv2.INTER_AREA)
    return out


if __name__ == "__main__":
    shot = sys.argv[2] if len(sys.argv) > 2 else "room"
    ids = json.loads((ROOT / "work" / "render" / f"{shot}_ids.json").read_text())
    d = Path(sys.argv[1])
    out = ROOT / "work" / "qc" / shot
    out.mkdir(parents=True, exist_ok=True)
    for f in sorted(d.glob("t*.exr")):
        t = float(f.stem[1:])
        rgb = E.paper_grain(paint_time(f, t, ids), 0.010)
        cv2.imwrite(str(out / f"{f.stem}.png"), (rgb[..., ::-1] * 255 + 0.5).astype(np.uint8))
        print(f.stem, flush=True)
