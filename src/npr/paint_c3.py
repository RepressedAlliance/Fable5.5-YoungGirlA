"""Clip 3 painter. The same frozen room in the same light as the end of clip 2, seen from the other end; then the same winter over the school and the town.

The room's colour, frost, drifts, flakes, window view and light in the air are clip 2's own (paint_c2), so the cut at 81.31 s is a reverse angle and not a change of
look. Nothing here needs new passes: the kept EXRs of the old render are repainted. As the town presses flat into a map the winter gives way, block by block, to
comp.paint's map colours, so the end of the shot, and what follows it, stay as they were.
"""
import json
import random
import sys
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "src" / "npr"), str(ROOT / "src" / "three")]
import comp  # noqa: E402
import engine as E  # noqa: E402
import paint_c2 as P2  # noqa: E402
import shared_c2 as C2  # noqa: E402
import shared_c3 as S  # noqa: E402

_hex, _ramp, _tri, _teeth = P2._hex, P2._ramp, P2._tri, P2._teeth
PAL, OUT = P2.PAL, P2.OUT

# Object ids of this shot's kept render (shot_c3.build's order). c2 has the ceiling and its lamps before the desks, c3 builds them last.
FLOOR_IDS = (1, 2, 58)
SKY_ID = 49
FIRST_DESK_ID = 110
YARD_LINES_ID = 1226
POOL_ID = 1426
TOWN_GROUND_OFFSET = 1          # the flat town mesh comes just before the buildings
ROOM_BOX = ((-4.05, -0.25, -0.15), (3.95, 9.45, 3.1))

# ---- the winter outside: flat snow on what faces up, warm walls, and the room's lavender in every shadow
SNOW_SH = np.array([0.68, 0.74, 0.95], np.float32)     # a shadow on snow: lit colour times this
WALL_SH = np.array([0.60, 0.58, 0.90], np.float32)     # the warm walls go mauve in shadow, as the room's wood does
WALL = [(0, "#2E2438"), (.30, "#6A4C58"), (.55, "#BC9A84"), (.78, "#EBD7BC"), (.92, "#F6E8D2"), (1, "#FCF1DE")]
SNOW = [(0, "#6474D4"), (.35, "#8FA6EC"), (.55, "#BDD6F8"), (.72, "#DCEFFC"), (.85, "#F4FBFF"), (1, "#FCFEFF")]
PANE = ("#7FD4F8", "#4C74D6")                          # town and school window glass: lit, in shadow
DRIFT = "#E2F2FD"                                      # the second tone of lying snow
CROWN = dict(lit=("#FBFEFF", "#8FA3E8"), sh=("#BDD6F8", "#5B6BCB"))     # a tree under snow, snow and branches, in the colours of the cedars in the window
POOL = "#7FDDFB"
TRACK = "#8FB4F2"                                      # the running track and pitch lines, swept out of the snow in the yard
# The flat town by what it is: (its summer colour, its map colour, its winter colour). Streets and roads are the blue of ploughed snow, blocks are white.
GROUND = (("#B7B6AE", "#FFFFFF", "#CFE4FA"), ("#D2CDBC", "#EFEADB", "#F6FBFF"), ("#DDD8C8", "#CFE3EA", "#B4CAF4"), ("#DCD6C4", "#EDE6CF", "#EEF7FE"),
          ("#A9C49A", "#BFE3B0", "#D4F0EA"), ("#6B6A70", "#4A4A52", "#4C5096"), ("#6FB7D3", "#7FD6F2", "#21BDF5"))
# Roofs by their summer colour. Two keep a trace of warmth under the snow, so from high up the town is a town and not a sheet.
ROOF = (("#C9C4B6", "#EAF5FE"), ("#BDBDB2", "#DCEBFB"), ("#ADB9BA", "#CBE1FA"), ("#CDBBA8", "#F6E6D8"), ("#A3B5BA", "#BDD6F6"), ("#D5D0C2", "#F8FCFF"))
MAP_BUILDING = "#E6DFCB"
_cache = {}


def _srgb_mix(a, b, m):
    """comp shows srgb, the material mixes in linear."""
    def lin(c):
        return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)
    return comp.linear_to_srgb(lin(a) * (1 - m) + lin(b) * m).astype(np.float32)


def _nearest(colours, base, mask):
    """Index of the nearest of these colours, on the masked pixels."""
    d = ((base[mask][:, None, :] - colours[None, :, :]) ** 2).sum(-1)
    return d.argmin(1)


def page_flat():
    if "page" not in _cache:
        _cache["page"] = P2.page_tex(999.0)
    return _cache["page"]


def look_at(t, ids):
    live = {}
    if "page" in ids:
        o, u_end, v_end = C2.page_uv_axes()
        live[ids["page"]] = (o, u_end, v_end, page_flat())
    if "board" not in _cache:
        _cache["board"] = P2.board_tex(999.0)
    live[ids["board"]] = ((-2.28, 9.16, 2.21), (2.28, 9.16, 2.21), (-2.28, 9.16, 1.03), _cache["board"])
    d = S.distance_at(t)
    # ink thins out with the distance, then only the colour plan is left
    # the town is drawn by the same hand as the room: ink on every building until they are too small to hold it
    return comp.Look(snow=0.95, live=live, line_px=3.0, line_near=1.25, line_min=0.62, edge_m=1.5,
                     line_fade=(450.0, 1500.0) if d > 200 else None,
                     freeze=[((0.0, 4.6, 1.5), 30.0)], freeze_box=ROOM_BOX,
                     shadow_tint=(0.74, 0.77, 0.88), no_ink_ids=[ids["her"]] if "her" in ids else [], bright_ice=True,
                     force_lit=[ids["board"], ids["page"], ids.get("under", -1)], town_id=ids.get("town", 0), town_h=max(S.flatten_at(t), 0.01), town_base=-7.6,
                     town_detail=1 - S.mapmix_at(t),
                     ink_fade_box=((-3.78, 0.02, -0.15), (3.78, 9.18, 3.0), 10.0, 32.0))


def desk_table():
    """The rectangle of each desk's top, by object id. classroom.desk's own random sequence and part count, without Blender: the kept passes were made from them."""
    if "desks" in _cache:
        return _cache["desks"]
    r = random.Random(41)
    W, D = 7.6, 9.2
    cols, rows, her = 6, 5, (1, 3)
    next_id = FIRST_DESK_ID
    table = {}
    for c in range(cols):
        for row in range(rows):
            x = -W / 2 + 1.05 + c * ((W - 2.1) / (cols - 1))
            y = D - 2.85 - row * 1.02
            parts = 11
            if (c, row) != her:
                jx, jy = r.uniform(-0.07, 0.07), r.uniform(-0.09, 0.09)
                r.uniform(-0.05, 0.22), r.uniform(-0.28, 0.28)
                x, y = x + jx, y + jy
                if r.random() < 0.28:
                    r.uniform(-0.12, 0.12)
                    r.choice((0, 1, 2))
                    parts += 1
            table[next_id] = (x - 0.31, x + 0.31, y - 0.22, y + 0.22)
            next_id += parts + 6     # the desk's parts, then its chair's
    rect = np.zeros((next_id + 1, 4), np.float32)
    is_desk = np.zeros(next_id + 1, bool)
    for k, v in table.items():
        rect[k] = v
        is_desk[k] = True
    _cache["desks"] = (rect, is_desk, next_id)
    return _cache["desks"]


def desk_frost(ioid, pos, normal):
    """Clip 2's frost on the desk tops, fully grown: hard, toothed, whiter at the corners."""
    rect, is_desk, _ = desk_table()
    ids = np.clip(ioid, 0, len(is_desk) - 1)
    m = is_desk[ids] & (normal[..., 2] > 0.9) & (pos[..., 2] > 0.69)
    if not m.any():
        return m
    r = rect[ids]
    dx = np.minimum(pos[..., 0] - r[..., 0], r[..., 1] - pos[..., 0])
    dy = np.minimum(pos[..., 1] - r[..., 2], r[..., 3] - pos[..., 1])
    along = np.where(dx < dy, pos[..., 1], pos[..., 0])
    seed = ids * 0.37
    reach = 0.012 + 0.085 * _teeth(along, seed)
    corner = np.sqrt(dx * dx + dy * dy)
    ang = np.arctan2(dy, dx + 1e-4)
    return m & ((np.minimum(dx, dy) < reach) | (corner < 0.05 + 0.13 * _tri(ang * 2.6 + seed)))


def remove_chips(p):
    """The render's snow is small white balls, and ink stops well short of each one, so every line in the room came out dashed. The balls are taken out of the
    passes, each pixel filled from the nearest thing behind it, and the snow is painted afterwards, as clip 2's is."""
    chip = (np.round(p["IndexMA"]).astype(np.int32) == 3) & (p["DiffCol"][..., :3].mean(-1) > 0.8)
    if not chip.any():
        return p
    chip = cv2.dilate(chip.astype(np.uint8), np.ones((3, 3), np.uint8))
    _, lab = cv2.distanceTransformWithLabels(chip, cv2.DIST_L2, 3, labelType=cv2.DIST_LABEL_PIXEL)
    clear = chip == 0
    table = np.zeros(lab.max() + 1, np.int64)
    table[lab[clear]] = np.flatnonzero(clear.ravel())
    src = table[lab[chip > 0]]
    out = dict(p)
    for k, v in p.items():
        a = v.copy()
        flat = a.reshape(-1, *a.shape[2:])
        a[chip > 0] = flat[src]
        out[k] = a
    return out


def outside(pos, glass, t, eye):
    """Clip 2's view from its windows, the same sky, clouds, hills, town and cedars, and also the snow on the ground, which clip 2's lower camera never looks down on.
    The camera starts above the window heads here and could not see the sky at all, so the view keeps clip 2's eye height until the rise takes the camera up."""
    out = np.zeros(pos.shape, np.float32)
    if not glass.any():
        return out
    eye = np.array(eye, np.float32)
    # where the ray crosses the glass, from the real eye
    d0 = (pos[glass] - eye).astype(np.float32)
    dx0 = np.minimum(d0[:, 0], -1e-3)
    k = (-3.82 - eye[0]) / dx0
    zg = eye[2] + d0[:, 2] * k
    rise = S.smooth(S.seg(t, S.HIT_T[0], S.HIT_T[0] + 1.0))
    ez = 1.35 + (float(eye[2]) - 1.35) * rise
    d = d0.copy()
    d[:, 2] = (zg - ez) / np.maximum(k, 1e-4)
    dx = dx0

    def at(X):
        q = (X - eye[0]) / dx
        return eye[1] + d[:, 1] * q, ez + d[:, 2] * q

    y, z = at(-220.0)
    bands = OUT["sky1"]
    wob = 1.6 * np.sin(y * 0.021) + 1.0 * np.sin(y * 0.053 + 1.3)
    rgb = np.broadcast_to(_hex(bands[3]), d.shape).copy()
    for lim, col in ((12.0, bands[2]), (22.0, bands[1]), (34.0, bands[0])):
        rgb[z + wob > lim] = _hex(col)
    yy = y - 2.2 * t
    body = np.zeros(len(d), bool)
    belly = np.zeros(len(d), bool)
    for cy, cz, ry, rz in P2._clouds():
        near = np.abs(yy - cy) < ry
        if near.any():
            e = ((yy - cy) / ry) ** 2
            body |= near & (e + ((z - cz) / rz) ** 2 < 1)
            belly |= near & (e + ((z - cz - rz * 0.42) / rz) ** 2 < 1)
    rgb[body] = _hex(OUT["cloud"][1])
    rgb[body & belly] = _hex(OUT["cloud"][0])
    h = 7.5 + 5.0 * np.sin(y * 0.017 + 0.6) + 2.6 * np.sin(y * 0.047 + 2.1) + 1.0 * np.sin(y * 0.13)
    m = z < h
    rgb[m] = _hex(OUT["hill1"][0])
    rgb[m & (h - z < 2.2 + 1.8 * _tri(y * 0.06))] = _hex(OUT["hill1"][1])
    y, z = at(-58.0)
    v, _ = P2._blocks(y, 6.5, 3)
    v2, _ = P2._blocks(y, 6.5, 4)
    h = -1.0 + 5.2 * v
    m = z < h
    tc = OUT["town1"]
    rgb[m] = np.where((v2 > 0.5)[..., None], _hex(tc[0]), _hex(tc[3]))[m]
    rgb[m & (np.mod(y, 1.25) < 0.62) & (np.mod(z, 1.3) < 0.62) & (z < h - 0.9)] = _hex(tc[2])
    rgb[m & (h - z < 0.42 + 0.30 * _tri(y * 0.9))] = _hex(tc[1])
    foot = -3.7
    # the ground runs out from under the school, one flat white
    def ground(mask):
        rgb[mask] = _hex(P2.SNOW_WHITE)
    ground(z < foot)
    k_ = OUT["tree1"]
    for X, seed, gap, tones in ((-34.0, 25, (4.5, 7.5), (k_[3], k_[4], k_[3])), (-20.0, 23, (6.0, 11.0), (k_[0], k_[1], k_[2]))):
        y, z = at(X)
        ground(z < foot)
        body, cap, trunk = P2._cedars(y, z, P2._trees(seed, gap))
        rgb[trunk & (z >= foot)] = _hex(tones[2])
        rgb[body] = _hex(tones[0])
        rgb[cap] = _hex(tones[1])
    y, z = at(-5.0)
    ground(z < foot)
    out[glass] = rgb
    return out


def snow_mask(t, depth, her, w, h, ss):
    """Clip 2's own flakes, in the same places at the same time: they keep falling through the cut. They pass behind her, never across her."""
    white = np.zeros((h, w), np.uint8)
    pale = np.zeros((h, w), np.uint8)
    if t > S.STOP:
        return white.astype(np.float32), pale.astype(np.float32)
    c = P2._snow_cloud()
    e, tg, up = S.camera_at(t)
    e, tg, up = np.array(e), np.array(tg), np.array(up)
    f = tg - e
    f /= np.linalg.norm(f)
    rgt = np.cross(f, up)
    rgt /= np.linalg.norm(rgt)
    u = np.cross(rgt, f)
    age = t - C2.HIT_T[5] - c[:, 7]
    span = 3.2
    z = c[:, 2] - c[:, 4] * age
    z = 3.0 - np.mod(3.0 - z, span)
    x = c[:, 0] + 0.05 * np.sin(age * 0.9 * c[:, 8] + c[:, 6]) + 0.06 * age
    y = c[:, 1] + 0.04 * np.cos(age * 0.7 * c[:, 8] + c[:, 6])
    rel = np.column_stack([x, y, z]) - e
    zc = rel @ f
    k = S.LENS / 36.0 * w
    sx = (rel @ rgt) / np.maximum(zc, 1e-3) * k + w / 2
    sy = -(rel @ u) / np.maximum(zc, 1e-3) * k + h / 2
    rad = c[:, 3] / np.maximum(zc, 1e-3) * k
    keep = (zc > 0.45) & (zc < 30.0) & (sx > -40) & (sx < w + 40) & (sy > -40) & (sy < h + 40)
    for i in np.nonzero(keep)[0]:
        px, py = int(sx[i]), int(sy[i])
        if 0 <= px < w and 0 <= py < h and (depth[py, px] < zc[i] - 0.03 or her[py, px]):
            continue
        r_ = max(float(min(rad[i], 8.5 * ss)), 0.7)
        tgt = white if c[i, 5] > 0.5 else pale
        shift = 4
        cv2.circle(tgt, (int(sx[i] * (1 << shift)), int(sy[i] * (1 << shift))), int(r_ * (1 << shift)), 255, -1, cv2.LINE_AA, shift)
    # nothing painted may lie on her, whatever its size
    white[her] = 0
    pale[her] = 0
    return white.astype(np.float32) / 255, pale.astype(np.float32) / 255


def winter(base, lit, normal, pos, depth, ioid, t, ids):
    """The school and the town under the same snow as the room: white on what faces up, warm walls, lavender shadows, cyan water."""
    h, w = depth.shape
    nz = normal[..., 2]
    up = nz > 0.7
    g = base.mean(-1)
    img = np.where(up[..., None], _ramp(np.clip(g + 0.12, 0, 1), SNOW), _ramp(g, WALL))
    # glass in the school's walls
    blue = (base[..., 2] - base[..., 0] > 0.14) & ~up
    img = np.where(blue[..., None], _hex(PANE[0]), img)
    m = S.mapmix_at(t)
    town_id = ids["town"]
    is_town = ioid == town_id
    is_ground = ioid == town_id - TOWN_GROUND_OFFSET
    is_river = ioid == town_id - 2
    # the flat town
    flat = is_ground | is_river
    if flat.any():
        summer = np.stack([_hex(a) for a, _, _ in GROUND])
        mapped = np.stack([_hex(b) for _, b, _ in GROUND])
        cold = np.stack([_hex(c) for _, _, c in GROUND])
        img[flat] = cold[_nearest(_srgb_mix(summer, mapped, m), base, flat)]
    # roofs
    roof = is_town & up
    if roof.any():
        summer = np.stack([_hex(a) for a, _ in ROOF])
        mapped = _hex(MAP_BUILDING)[None]
        cold = np.stack([_hex(b) for _, b in ROOF])
        img[roof] = cold[_nearest(_srgb_mix(summer, mapped, m), base, roof)]
    # buildings are not boxes: comp.paint's own ribbons of window and roof plant, in the same places, so nothing jumps when the map takes over
    detail = 1 - m
    if detail > 0 and is_town.any():
        look_h = max(S.flatten_at(t), 0.01)
        far = np.clip((1400.0 - depth) / 600.0, 0, 1) * detail
        wall = is_town & (np.abs(nz) < 0.3)
        z_ = (pos[..., 2] + 7.6) / max(look_h, 0.05)
        u_ = np.where(np.abs(normal[..., 1]) > np.abs(normal[..., 0]), pos[..., 0], pos[..., 1])
        win = wall & (np.mod(z_, 3.0) > 1.0) & (np.mod(z_, 3.0) < 2.3) & (np.mod(u_, 2.8) > 0.35) & (z_ > 0.8)
        k_ = (win * far)[..., None].astype(np.float32)
        img = img * (1 - k_) + _hex(PANE[0]) * k_
        cx_, cy_ = pos[..., 0] / 5.0, pos[..., 1] / 5.0
        ix_, iy_ = np.floor(cx_), np.floor(cy_)
        hs_ = np.mod(np.sin(ix_ * 12.9898 + iy_ * 78.233) * 43758.5453, 1.0)
        unit = is_town & (nz > 0.9) & (pos[..., 2] > -7.1) & (hs_ > 0.55) & (np.abs(cx_ - ix_ - 0.5) < 0.10 + 0.14 * hs_) & (np.abs(cy_ - iy_ - 0.5) < 0.12)
        k_ = (unit * far * 0.42)[..., None].astype(np.float32)
        img = img * (1 - k_) + img * np.array([0.72, 0.78, 0.96], np.float32) * k_
    # trees under snow: found by being green and not part of the town's plan
    green = (base[..., 1] > base[..., 0] + 0.04) & (base[..., 1] > base[..., 2] + 0.10) & ~flat & ~is_town
    if green.any():
        # the round crowns carry one load of snow, hanging in teeth like the cedars' in the window: a smooth white cap on a blue ball read as a bauble, stripes as an Easter egg
        ang = np.arctan2(normal[..., 1], normal[..., 0]) / (2 * np.pi)
        laden = nz + 0.34 * (_tri(ang * 9.0) - 0.5) + 0.14 * (_tri(ang * 23.0) - 0.5) > 0.02
        tone = lambda c: np.where(laden[..., None], _hex(c[0]), _hex(c[1]))
        img = np.where(green[..., None], np.where(lit[..., None], tone(CROWN["lit"]), tone(CROWN["sh"])), img)
    # lying snow has its own shape where the camera is near enough to see it: a second flat tone in long hard drifts
    near = up & ~flat & ~green & (depth < 140.0)
    if near.any():
        st = pos * np.array([0.30, 0.16, 1.0], np.float32)
        fl = comp.world_noise(st, 1.0, 21.0) * 0.7 + comp.world_noise(st, 3.7, 22.0) * 0.3
        # (they shrink away with the distance rather than stop at a line)
        lay = fl > 0.56 + 0.5 * np.clip((depth - 70.0) / 70.0, 0, 1)
        # and metre-sized ones right under the lens, as the camera comes out over the roof
        if depth[near].min() < 25.0:
            st = pos * np.array([1.1, 0.55, 1.0], np.float32)
            lay |= comp.world_noise(st, 1.0, 31.0) * 0.7 + comp.world_noise(st, 3.1, 32.0) * 0.3 > 0.55 + 0.5 * np.clip((depth - 14.0) / 11.0, 0, 1)
        img = np.where((near & lay)[..., None], _hex(DRIFT), img)
    # the lines swept across the yard, and the pool, the song's cyan frozen over
    img = np.where((ioid == YARD_LINES_ID)[..., None], _hex(TRACK), img)
    img = np.where((ioid == POOL_ID)[..., None], _hex(POOL), img)
    # the one shadow rule
    sh = np.where((up | flat)[..., None], SNOW_SH, WALL_SH)
    sh = np.where(blue[..., None], _hex(PANE[1]) / _hex(PANE[0]), sh)
    keep_lit = green | (ioid == YARD_LINES_ID) | (ioid == POOL_ID)
    return np.where((lit | keep_lit)[..., None], img, img * sh)


def paint_ice(p, t, ids):
    """paint_c2.paint_ice's order, for this shot: the room is coloured by clip 2's palette, what lies outside it by winter()."""
    look = look_at(t, ids)
    ss = S.SS
    p = remove_chips(p)
    col = p["DiffCol"][..., :3].astype(np.float32)
    light = p["DiffDir"][..., :3].astype(np.float32)
    depth = p["Depth"].astype(np.float32).copy()
    normal = p["Normal"][..., :3].astype(np.float32).copy()
    pos = np.nan_to_num(p["Position"][..., :3].astype(np.float32), posinf=1e4, neginf=-1e4).copy()
    ob = p["IndexOB"].astype(np.float32).copy()
    ma = np.round(p["IndexMA"]).astype(np.int32)
    alpha = p["Alpha"].astype(np.float32)
    h, w = depth.shape
    base = comp.linear_to_srgb(np.clip(col, 0, 1)).astype(np.float32)
    base = comp.apply_live(base, ob, pos, look.live)
    char, noink, graphic, sky = ma == 2, ma == 3, ma == 4, ma == 5
    lit = light.mean(-1) > look.light_threshold
    for oid in look.force_lit:
        lit |= np.abs(ob - oid) < 0.5
    nx, ny, nz = normal[..., 0], normal[..., 1], normal[..., 2]
    up, down = np.clip(nz, 0, 1), np.clip(-nz, 0, 1)
    plane = (0.93 + 0.07 * up - 0.11 * down - 0.06 * np.abs(ny))[..., None].astype(np.float32)
    ioid = np.round(ob).astype(np.int32)
    (bx0, by0, bz0), (bx1, by1, bz1) = ROOM_BOX
    room = (pos[..., 0] > bx0) & (pos[..., 0] < bx1) & (pos[..., 1] > by0) & (pos[..., 1] < by1) & (pos[..., 2] > bz0) & (pos[..., 2] < bz1)
    g = base.mean(-1)
    # the room
    v = g - 0.16 * down - 0.05 * np.abs(ny) - 0.015 * np.abs(nx) - 0.02 * (1 - up)
    ice = np.where(lit[..., None], _ramp(v + 0.05, PAL["lit"]), _ramp(v, PAL["sh"]))
    floor = np.isin(ioid, FLOOR_IDS)
    wood = np.where(lit[..., None], _ramp(g, PAL["wood_lit"]), _ramp(g, PAL["wood_sh"]))
    ice = np.where(floor[..., None], wood, ice)
    # what is outside it
    world = winter(base, lit, normal, pos, depth, ioid, t, ids)
    img = np.where(room[..., None], ice, world)
    # the words keep their pure cyan even in shadow, as in clip 2; the newspaper and the paper strips take the shadow
    word = (base[..., 2] - base[..., 0] > 0.40) & graphic
    img = np.where(graphic[..., None], np.where((lit | word)[..., None], base, base * np.array([0.80, 0.84, 0.92], np.float32) * plane), img)
    # snow lies in the same places as clip 2's: the same world noise from the same positions
    f = comp.world_noise(pos, 2.3) * 0.55 + comp.world_noise(pos, 9.0, 2.0) * 0.30 + comp.world_noise(pos, 31.0, 5.0) * 0.15
    stretched = pos * np.array([0.55, 1.5, 1.0], np.float32)
    fl = comp.world_noise(stretched, 2.0, 4.0) * 0.7 + comp.world_noise(stretched, 7.0, 9.0) * 0.3
    # from high up the wood and the drifts would be confetti, with the ink gone: the snow closes over the floor as the camera leaves
    th = np.where(floor, 0.48 - 1.0 * S.seg(S.distance_at(t), 12.0, 38.0), 1.05 - 0.85)
    drift = (up > 0.8) & (np.where(floor, fl, f) > th) & ~noink & ~graphic & ~char & ~sky & room
    snow_sh = _ramp(np.full((h, w), 1.0, np.float32), PAL["sh"])
    img = np.where(drift[..., None], np.where(lit[..., None], _hex(P2.SNOW_WHITE), snow_sh), img)
    # frost on the desk tops
    fr = desk_frost(ioid, pos, normal) & room & ~graphic & ~char
    img = np.where(fr[..., None], np.where(lit[..., None], _hex(P2.FROST), _hex("#E2F5FE")), img)
    # the flat shadows the render drew in grey: her newspaper's on the desk, her feet's on the floor
    # (only those: the type on the paper strips is in the same material kind, and stays ink)
    flat_sh = noink & (np.abs(base - _hex("#A3C0D9")).max(-1) < 0.06)
    img = np.where(noink[..., None], base, img)
    img = np.where(flat_sh[..., None], np.where((pos[..., 2] > 0.3)[..., None], _hex("#A4C0F2"), _hex("#8478A8")), img)
    # she is the one thing that keeps her own colour; the paper strips are printed, in the same material kind as the sky
    img = np.where(char[..., None] | sky[..., None], base, img)
    eye = np.array(S.camera_at(t)[0], np.float32)
    # what is seen through the glass is clip 2's view, whatever the render had behind it
    k = (-3.82 - eye[0]) / np.minimum(pos[..., 0] - eye[0], -1e-3)
    zg = eye[2] + (pos[..., 2] - eye[2]) * k
    yg = eye[1] + (pos[..., 1] - eye[1]) * k
    skyplane = ioid == SKY_ID
    glass = ((pos[..., 0] < -3.93) & (zg > 0.88) & (zg < 2.42) & (yg > 0.2) & (yg < 9.0) & ~graphic & ~char & ~sky) | skyplane
    view = outside(pos, glass, t, eye)
    img = np.where(glass[..., None], view, img)
    near, far = P2.pane_frost(pos, glass, C2.T1, eye)
    img = np.where(far[..., None], _hex(P2.PANE_FROST[1]), img)
    img = np.where(near[..., None], _hex(P2.PANE_FROST[0]), img)
    # the view has no ink: what stands behind the glass in the render must not draw lines there
    ob[glass] = SKY_ID
    depth[glass] = 30.0
    normal[glass] = (1.0, 0.0, 0.0)
    pos[glass] = (-30.0, 5.0, 5.0)
    # the flat town is all one sheet of paper: the little steps between its layers only ever drew dashes
    town_flat = (ioid == ids["town"] - TOWN_GROUND_OFFSET) | (ioid == ids["town"] - 2)
    normal[town_flat] = (0.0, 0.0, 1.0)
    # shafts of light in the air, while the camera is low enough to look through them
    beam = P2.BEAM * (1 - S.seg(float(eye[2]), 4.0, 8.0))
    if beam > 0:
        sw, sh_ = w // 2, h // 2
        dsm = cv2.resize(np.where(np.isfinite(depth) & (depth < 1e6), depth, 40.0), (sw, sh_), interpolation=cv2.INTER_NEAREST)
        e, tg, up_ = S.camera_at(t)
        e, tg, up_ = np.array(e, np.float32), np.array(tg, np.float32), np.array(up_, np.float32)
        ff = tg - e
        ff /= np.linalg.norm(ff)
        rr = np.cross(ff, up_)
        rr /= np.linalg.norm(rr)
        uu = np.cross(rr, ff)
        kk_ = S.LENS / 36.0 * sw
        xx = (np.arange(sw, dtype=np.float32) + 0.5 - sw / 2) / kk_
        yy = -(np.arange(sh_, dtype=np.float32) + 0.5 - sh_ / 2) / kk_
        ray = ff + rr * xx[None, :, None] + uu * yy[:, None, None]
        hit = P2.beams(dsm, e, ray, S.SUN)
        m = cv2.resize(hit, (w, h), interpolation=cv2.INTER_LINEAR)
        kk = ((m > 0.5).astype(np.float32) * beam * (~glass & ~char & room))[..., None]
        img = img * (1 - kk) + _hex("#F4FAFF") * kk
    # ink
    skip = noink.copy()
    for oid in look.no_ink_ids:
        skip |= np.abs(ob - oid) < 0.5
    skip |= ioid == YARD_LINES_ID
    lines = comp.ink_lines(ob, depth, normal, char, pos, ss, look, 0, skip_wide=skip)
    (bx0, by0, bz0), (bx1, by1, bz1), d0, d1 = look.ink_fade_box
    inside = (pos[..., 0] > bx0) & (pos[..., 0] < bx1) & (pos[..., 1] > by0) & (pos[..., 1] < by1) & (pos[..., 2] > bz0) & (pos[..., 2] < bz1)
    fade = np.clip((d1 - np.nan_to_num(depth, posinf=1e6)) / max(d1 - d0, 1e-3), 0, 1).astype(np.float32)
    lines = np.where(inside, lines * fade, lines)
    img = img * (1 - lines[..., None]) + comp.INK * lines[..., None]
    white, pale = snow_mask(t, depth, char, w, h, ss)
    img = img * (1 - pale[..., None]) + _hex("#D8EEFB") * pale[..., None]
    img = img * (1 - white[..., None]) + _hex(P2.SNOW_WHITE) * white[..., None]
    # beyond the town's edge: snow
    a = alpha[..., None]
    img = img * a + _hex(GROUND[0][2]) * (1 - a)
    img = np.clip(img, 0, 1)
    return cv2.resize(img, (int(round(w / ss)), int(round(h / ss))), interpolation=cv2.INTER_AREA)


def map_paint(p, t, ids):
    """The map colours of the old shot, which the end of the shot and what follows it are built on."""
    rgba = comp.paint(p, look_at(t, ids), ss=S.SS)
    return rgba[..., :3] * rgba[..., 3:4] + np.array([0.78, 0.76, 0.67], np.float32) * (1 - rgba[..., 3:4])


def map_front(p, m):
    """Which of the town has turned into map by now, 0..1 at frame size. A cross-fade of ice blue and paper beige goes grey, so nothing fades: block by block, from the
    edges of the frame in towards the school, each is either still winter or already map."""
    pos = np.nan_to_num(p["Position"][..., :3].astype(np.float32), posinf=1e4, neginf=-1e4)
    ix, iy = np.floor(pos[..., 0] / 64.0), np.floor(pos[..., 1] / 64.0)
    hs = np.mod(np.sin(ix * 12.9898 + iy * 78.233) * 43758.5453, 1.0).astype(np.float32)
    r = np.sqrt((ix * 64.0 + 32.0) ** 2 + (iy * 64.0 + 32.0) ** 2) / 1500.0
    turned = ((1 - np.clip(r, 0, 1)) * 0.78 + hs * 0.22 < m).astype(np.float32)
    h, w = turned.shape
    return cv2.resize(turned, (int(round(w / S.SS)), int(round(h / S.SS))), interpolation=cv2.INTER_AREA)[..., None]


def paint_time(exr, t, ids):
    p = comp.read_exr(exr)
    m = S.mapmix_at(t)
    if m >= 1:
        return map_paint(p, t, ids)
    rgb = paint_ice(p, t, ids)
    if m > 0:
        k = map_front(p, m)
        rgb = rgb * (1 - k) + map_paint(p, t, ids) * k
    return rgb.astype(np.float32)


if __name__ == "__main__":
    ids = json.loads((ROOT / "work" / "render" / "c3_ids.json").read_text())
    d = Path(sys.argv[1])
    out = ROOT / "work" / "qc" / "c3"
    out.mkdir(parents=True, exist_ok=True)
    for f in sorted(d.glob("t*.exr")):
        t = float(f.stem[1:])
        rgb = E.paper_grain(paint_time(f, t, ids), 0.010)
        cv2.imwrite(str(out / f"{f.stem}.png"), (rgb[..., ::-1] * 255 + 0.5).astype(np.uint8))
        print(f.stem, flush=True)
