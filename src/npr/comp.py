"""Paints a frame from Blender's data passes, by the same rules as the character art:
flat colour, one hard-edged shadow tone per material, thick-thin ink line.

No soft light anywhere. Time-varying looks (cold, snow) live in `Look`, so the 3D never needs
re-rendering to change the grade.

Material pass_index:
  0 painted surface    1 unlit backdrop (takes the grade)    2 cut-out character
  3 no ink, unlit, no grade (snow, small print)    4 graphic colour: ink yes, shading yes, no cold grade
  5 flat sky: unlit, no grade, surrounding objects still get their ink

With PAINT_GPU=1 the array work of paint() and ink_lines() runs on the graphics card (see the end of this
file). Same interface, same picture. The CPU path below stays the default and is the automatic fallback.
"""
import os
from dataclasses import dataclass, field

import cv2
import numpy as np
import OpenEXR

INK = np.array([0.075, 0.075, 0.095], np.float32)  # display-referred


def linear_to_srgb(c):
    return np.where(c <= 0.0031308, c * 12.92, 1.055 * np.power(np.maximum(c, 1e-6), 1 / 2.4) - 0.055)


def read_exr(path):
    """Returns {pass: array}. Works with Blender's multilayer naming (View Layer.Pass.X)."""
    names = {"Object Index": "IndexOB", "Material Index": "IndexMA", "Diffuse Direct": "DiffDir",
             "Diffuse Color": "DiffCol"}
    out, group = {}, {}
    with OpenEXR.File(str(path), separate_channels=True) as f:
        for part in f.parts:
            for name, c in part.channels.items():
                bits = name.split(".")
                key, comp = bits[-2], bits[-1]
                group.setdefault(names.get(key, key), {})[comp] = c.pixels
    # the beauty pass is never looked at, only its alpha: not keeping it saves memory, so more painters fit
    combined = group.pop("Combined", None)
    if combined is not None:
        out["Alpha"] = combined["A"]
    for key in list(group):
        comps = group.pop(key)
        order = [k for k in ("R", "G", "B", "A", "X", "Y", "Z", "V") if k in comps]
        if len(order) == 1:
            out[key] = comps[order[0]]
        else:
            out[key] = np.stack([comps.pop(k) for k in order], -1)
    return out


def _value_noise(h, w, cell, seed):
    rng = np.random.default_rng(seed)
    gh, gw = h // cell + 2, w // cell + 2
    g = rng.random((gh, gw), dtype=np.float32)
    return np.clip(cv2.resize(g, (w, h), interpolation=cv2.INTER_CUBIC), 0, 1)


_noise_cache = {}


def noise(h, w, cell, seed):
    k = (h, w, cell, seed)
    if k not in _noise_cache:
        _noise_cache[k] = _value_noise(h, w, cell, seed)
    return _noise_cache[k]


def world_noise(pos, scale, seed=0.0):
    """Smooth noise from world position: static on the surfaces, not on the screen."""
    p = pos[..., :3] * scale + seed
    n = (np.sin(p[..., 0] * 1.27 + 3.1 * np.sin(p[..., 1] * 0.73 + seed)) +
         np.sin(p[..., 1] * 1.61 + 2.3 * np.sin(p[..., 2] * 0.91 + 1.7)) +
         np.sin(p[..., 2] * 1.13 + 2.7 * np.sin(p[..., 0] * 0.67 + 0.4))) / 6 + 0.5
    return n.astype(np.float32)


@dataclass
class Look:
    shadow_tint: tuple = (0.84, 0.80, 0.86)    # lit colour x tint = the one shadow tone
    light_threshold: float = 0.10              # hard terminator (fraction of the sun's light)
    cold: float = 0.0                          # 0 warm afternoon .. 1 frozen
    snow: float = 0.0                          # 0 none .. 1 most upward surfaces buried
    line_px: float = 2.4                       # ink width at final 1080p scale
    line_near: float = 1.35                    # near lines thicker
    line_alpha: float = 1.0
    line_min: float = 0.34
    line_fade: tuple = None                    # (d0, d1): ink fades out between these distances
    unlit_gain: float = 1.0
    live: dict = field(default_factory=dict)   # {object_id: (origin, u_axis_end, v_axis_end, rgba array)}
    force_lit: list = field(default_factory=list)   # object ids treated as fully lit
    no_ink_ids: list = field(default_factory=list)  # objects that never get scene ink (cut-out cards)
    freeze: list = field(default_factory=list)      # [(point, radius)]: frozen regions spreading from impacts
    freeze_box: tuple = None                        # frozen regions cannot leave this box
    ink_fade_box: tuple = None                      # (lo, hi, d0, d1): ink inside this box fades between d0 and d1
    freeze_lut: object = None                     # object id -> song time it freezes
    time: float = 0.0
    town_id: int = 0                                # this object gets painted windows and roof plant
    town_h: float = 1.0                             # current height scale of the town
    town_base: float = 0.0                          # street level
    town_detail: float = 1.0
    edge_m: float = 0.0                             # also ink depth steps bigger than this many metres
    bright_ice: bool = False                        # frozen surfaces stay luminous even with no sun on them


# The fully frozen room is three colours: paper white, cyan and ink.
COLD_LIT = np.array([1.02, 1.05, 1.08], np.float32)
COLD_SH = np.array([0.74, 0.92, 1.04], np.float32)


def apply_live(base, ob, pos, live):
    """Paint an image onto a planar object through the position pass, so it sits in the scene exactly."""
    for oid, (o, u, v, tex) in live.items():
        m = np.abs(ob - oid) < 0.5
        if not m.any():
            continue
        o_, u_, v_ = map(lambda a: np.array(a, np.float32), (o, u, v))
        ua, va = u_ - o_, v_ - o_
        rel = pos - o_
        uu = (rel @ ua) / (ua @ ua)
        vv = (rel @ va) / (va @ va)
        th, tw = tex.shape[:2]
        mapx = (uu * tw).astype(np.float32)
        mapy = (vv * th).astype(np.float32)
        s = cv2.remap(tex, mapx, mapy, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
        a = s[..., 3:4]
        new = base * (1 - a) + s[..., :3] * a
        base = np.where(m[..., None], new, base)
    return base


def mend_ink(e, ss):
    """Root cause of the dashed lines (door panels, name plates, 2026-11-06): a crease narrower than a pixel is only hit by some of a pixel's
    three samples, so the normal test fires in runs along a line that should be whole. Short thin runs are joined to what lies along their own
    direction; a speck that still has nothing near it was never a line and goes. Works on the edge mask, at render resolution."""
    u8 = e.astype(np.uint8)
    n, lab, st, _ = cv2.connectedComponentsWithStats(u8, connectivity=8)
    if n < 2:
        return e
    w_, h_, area = st[:, cv2.CC_STAT_WIDTH], st[:, cv2.CC_STAT_HEIGHT], st[:, cv2.CC_STAT_AREA]
    long_max = int(round(34 * ss))
    across = int(round(2.5 * ss))
    flat = (np.minimum(w_, h_) <= across) & (np.maximum(w_, h_) <= long_max)
    flat[0] = False
    if not flat.any():
        return e
    k = int(round(9 * ss)) | 1
    is_h, is_v = flat & (w_ >= h_), flat & (h_ > w_)
    out = u8.copy()
    for table, ksize in ((is_h, (k, 3)), (is_v, (3, k))):
        if not table.any():
            continue
        cand = table[lab].astype(np.uint8)
        kern = cv2.getStructuringElement(cv2.MORPH_RECT, ksize)
        closed = cv2.morphologyEx(u8, cv2.MORPH_CLOSE, kern)
        near = cv2.dilate(cand, kern)
        out |= closed & near
    n, lab, st, _ = cv2.connectedComponentsWithStats(out, connectivity=8)
    speck = np.maximum(st[:, cv2.CC_STAT_WIDTH], st[:, cv2.CC_STAT_HEIGHT]) < int(round(5 * ss))
    speck[0] = False
    if speck.any():
        out = out & (~speck[lab]).astype(np.uint8)
    return out > 0


def close_gaps(mask):
    """Her card's outline, with the narrow gaps between her parts filled: a desk edge seen through the slit between arm and body is only two black crumbs."""
    k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (41, 41))
    return cv2.morphologyEx(mask.astype(np.uint8), cv2.MORPH_CLOSE, k)


def ink_lines(ob_id, depth, normal, skip_mask, pos, ss, look, seed=0, skip_wide=None):
    """Ink from object id changes, depth jumps and creases; width varies along the stroke like a brush."""
    a = _try_gpu(_ink_lines_from_numpy, ob_id, depth, normal, skip_mask, pos, ss, look, seed, skip_wide)
    if a is not None:
        return a
    h, w = ob_id.shape
    idi = np.round(ob_id).astype(np.int32)
    e = np.zeros((h, w), bool)
    e[:-1, :] |= idi[:-1, :] != idi[1:, :]
    e[:, :-1] |= idi[:, :-1] != idi[:, 1:]
    d = np.where(np.isfinite(depth) & (depth < 1e8), depth, 1e6)
    logd = np.log(np.maximum(d, 1e-3)).astype(np.float32)
    dz = np.zeros((h, w), np.float32)
    dz[:-1, :] = np.abs(logd[:-1, :] - logd[1:, :])
    dzx = np.zeros((h, w), np.float32)
    dzx[:, :-1] = np.abs(logd[:, :-1] - logd[:, 1:])
    # second difference catches creases on a single object and ignores grazing planes
    lap = np.abs(cv2.Laplacian(logd, cv2.CV_32F, ksize=1))
    e |= (dz > 0.035) & (lap > 0.012)
    e |= (dzx > 0.035) & (lap > 0.012)
    n = normal[..., :3]
    nn = np.zeros((h, w), np.float32)
    nn[:-1, :] = 1 - np.sum(n[:-1, :] * n[1:, :], -1)
    nx = np.zeros((h, w), np.float32)
    nx[:, :-1] = 1 - np.sum(n[:, :-1] * n[:, 1:], -1)
    e |= (nn > 0.22) | (nx > 0.22)
    if look.edge_m:
        # from far away a building's height is a tiny part of the distance: judge the step in metres
        da = np.zeros((h, w), np.float32)
        da[:-1, :] = np.abs(d[:-1, :] - d[1:, :])
        db = np.zeros((h, w), np.float32)
        db[:, :-1] = np.abs(d[:, :-1] - d[:, 1:])
        e |= (da > look.edge_m) | (db > look.edge_m)
    bg = ~np.isfinite(depth) | (depth > 1e8)
    if skip_mask is not None:
        # a cut-out's soft alpha edge must not pick up stray ink: she has her own outline
        grow = cv2.dilate(close_gaps(skip_mask), np.ones((9, 9), np.uint8)) > 0
        e &= ~grow
    if skip_wide is not None:
        # snow and print never pick up stray ink at their edges
        e &= ~(cv2.dilate(skip_wide.astype(np.uint8), np.ones((9, 9), np.uint8)) > 0)
    e &= ~bg
    e = mend_ink(e, ss)
    # Lines stay straight and clean like the character's; only their pressure varies. The pressure is
    # stuck to the objects (world space), so it travels with them instead of swimming under the camera.
    dist = cv2.distanceTransform((1 - e.astype(np.uint8)), cv2.DIST_L2, 3)
    p = np.where(bg[..., None], 0.0, np.nan_to_num(pos, posinf=0, neginf=0)).astype(np.float32)
    press = 0.55 + 0.95 * world_noise(p, 1.9, seed + 1.0) ** 1.2
    flutter = 0.92 + 0.16 * world_noise(p, 13.0, seed + 2.0)
    # nearer lines are heavier, far lines thin out
    near = np.clip(1.25 - 0.32 * np.log1p(np.where(bg, 50.0, d)), look.line_min, 1.0) * look.line_near
    width = look.line_px * ss * 0.5 * press * flutter * near
    a = np.clip(width - dist + 0.5, 0, 1).astype(np.float32)
    a = a * look.line_alpha
    if look.line_fade is not None:
        d0, d1 = look.line_fade
        a = a * np.clip((d1 - d) / max(d1 - d0, 1e-3), 0, 1).astype(np.float32)
    return a


def paint(passes, look, ss=1.5, seed=0):
    rgba = _try_gpu(_paint_gpu, passes, look, ss, seed)
    if rgba is not None:
        return rgba
    col = passes["DiffCol"][..., :3].astype(np.float32)
    light = passes["DiffDir"][..., :3].astype(np.float32)
    depth = passes["Depth"].astype(np.float32)
    normal = passes["Normal"][..., :3].astype(np.float32)
    pos = passes["Position"][..., :3].astype(np.float32)
    ob = passes["IndexOB"].astype(np.float32)
    ma = np.round(passes["IndexMA"]).astype(np.int32)
    alpha = passes["Alpha"].astype(np.float32) if "Alpha" in passes else np.ones(depth.shape, np.float32)
    h, w = depth.shape
    base = linear_to_srgb(np.clip(col, 0, 1)).astype(np.float32)
    if look.live:
        base = apply_live(base, ob, pos, look.live)
    lit_amount = light.mean(-1)
    unlit = ma == 1
    char = ma == 2
    noink = ma == 3
    graphic = ma == 4
    sky = ma == 5
    lit = lit_amount > look.light_threshold
    for oid in look.force_lit:
        lit = lit | (np.abs(ob - oid) < 0.5)
    tint = np.array(look.shadow_tint, np.float32)
    # Inside the shadow tone each plane still takes one flat value by where it faces, the way a
    # background painter separates planes. Flat surfaces stay flat, so no gradient ever appears.
    plane = (0.93 + 0.07 * np.clip(normal[..., 2], 0, 1)        # up-facing lighter
             - 0.11 * np.clip(-normal[..., 2], 0, 1)            # down-facing darker
             - 0.06 * np.abs(normal[..., 1]))                   # front and back walls a touch darker
    plane = plane[..., None].astype(np.float32)
    shadow = base * tint * plane
    # cold pushes hue to ice but keeps value structure, so the room freezes rather than turns grey
    lit_tone = base
    frozen = np.zeros((h, w), bool)
    if look.freeze:
        # The room freezes in hard-edged patches spreading from where each word struck. There is never
        # a blended, greyed-out in-between: every pixel is either still warm or already ice.
        p0 = np.nan_to_num(pos, posinf=1e4, neginf=-1e4)
        # large, simple lobes only: fine noise on this edge reads as mould and damp, not as cold
        wob = (world_noise(p0, 0.9, 3.0) - 0.5) * 1.6 + (world_noise(p0, 2.3, 7.0) - 0.5) * 0.4
        for pt, rad in look.freeze:
            if rad <= 0:
                continue
            dist = np.sqrt(((p0 - np.array(pt, np.float32)) ** 2).sum(-1))
            frozen |= dist + wob < rad
        if look.freeze_box is not None:
            (bx0, by0, bz0), (bx1, by1, bz1) = look.freeze_box
            frozen &= ((p0[..., 0] > bx0) & (p0[..., 0] < bx1) & (p0[..., 1] > by0) & (p0[..., 1] < by1) &
                       (p0[..., 2] > bz0) & (p0[..., 2] < bz1))
    if look.freeze_lut is not None:
        # things freeze whole: each object turns to ice at its own moment, on a blow, and stays that way
        ids = np.clip(np.round(ob).astype(np.int32), 0, len(look.freeze_lut) - 1)
        frozen = look.freeze_lut[ids] <= look.time
    if look.town_id and look.town_detail > 0:
        # buildings are not boxes: ribbons of window on the walls, plant and tanks on the roofs, all fixed to the world
        m = np.abs(ob - look.town_id) < 0.5
        nz = np.abs(normal[..., 2])
        far = np.clip((1400.0 - depth) / 600.0, 0, 1) * look.town_detail
        wall = m & (nz < 0.3)
        z_ = (pos[..., 2] - look.town_base) / max(look.town_h, 0.05)
        u_ = np.where(np.abs(normal[..., 1]) > np.abs(normal[..., 0]), pos[..., 0], pos[..., 1])
        win = wall & (np.mod(z_, 3.0) > 1.0) & (np.mod(z_, 3.0) < 2.3) & (np.mod(u_, 2.8) > 0.35) & (z_ > 0.8)
        glass = np.array([0.42, 0.56, 0.66], np.float32)
        k_ = (win * far)[..., None].astype(np.float32)
        base = base * (1 - k_) + glass * k_
        roof = m & (normal[..., 2] > 0.9) & (pos[..., 2] > look.town_base + 0.5)
        cx_, cy_ = pos[..., 0] / 5.0, pos[..., 1] / 5.0
        ix_, iy_ = np.floor(cx_), np.floor(cy_)
        hs_ = np.mod(np.sin(ix_ * 12.9898 + iy_ * 78.233) * 43758.5453, 1.0)
        unit = roof & (hs_ > 0.55) & (np.abs(cx_ - ix_ - 0.5) < 0.10 + 0.14 * hs_) & (np.abs(cy_ - iy_ - 0.5) < 0.12)
        k_ = (unit * far * 0.42)[..., None].astype(np.float32)
        base = base * (1 - k_) + base * 0.62 * k_
        # the town's colours are held up so far away it stays a painting, and does not go grey
        gm = base.mean(-1, keepdims=True)
        base = np.where(m[..., None], gm + (base - gm) * (1 + 0.9 * look.town_detail), base)
        lit_tone = base
        shadow = base * tint * plane
    if look.cold > 0 or look.freeze or look.freeze_lut is not None:
        g = base.mean(-1, keepdims=True)
        # paper white, cyan and ink: light values go to paper, while dark things stay dark
        v = np.interp(g, [0.0, 0.35, 0.60, 1.0], [0.10, 0.40, 0.80, 0.97]).astype(np.float32)
        cold_lit = (v + 0.05) * COLD_LIT
        cold_sh = v * COLD_SH * plane
        if look.bright_ice:
            # A frozen room with no sun in it must stay luminous: paper and cyan, planes told apart by value,
            # dark only where a thing is really dark. Otherwise it reads as an untextured grey model.
            v = np.interp(g, [0.0, 0.30, 0.55, 1.0], [0.08, 0.40, 0.86, 0.99]).astype(np.float32)
            ice_plane = (0.91 + 0.09 * np.clip(normal[..., 2], 0, 1) - 0.20 * np.clip(-normal[..., 2], 0, 1)
                         - 0.09 * np.abs(normal[..., 1]) - 0.03 * np.abs(normal[..., 0]))[..., None].astype(np.float32)
            cold_lit = (v + 0.04) * COLD_LIT
            cold_sh = v * np.array([0.84, 0.96, 1.04], np.float32) * ice_plane
        k = np.full((h, w, 1), look.cold, np.float32) if not (look.freeze or look.freeze_lut is not None) else frozen[..., None].astype(np.float32)
        k = np.where(graphic[..., None] | sky[..., None], 0.0, k).astype(np.float32)
        lit_tone = base * (1 - k) + cold_lit * k
        shadow = shadow * (1 - k) + cold_sh * k
    # printed and coloured things keep one shadow rule everywhere, so a word block is the same colour from shot to shot
    shadow = np.where(graphic[..., None], base * np.array([0.80, 0.84, 0.92], np.float32) * plane, shadow)
    img = np.where(lit[..., None], lit_tone, shadow)
    # snow settles on everything that faces up, with a hard edge
    if look.snow > 0:
        up = np.clip(normal[..., 2], 0, 1)
        f = (world_noise(pos, 2.3) * 0.55 + world_noise(pos, 9.0, 2.0) * 0.30 + world_noise(pos, 31.0, 5.0) * 0.15)
        th = 1.05 - look.snow * 0.85
        # no snow on printed things: her newspaper has to stay readable as the last warm patch in the room
        drift = (up > 0.8) & (f > th) & ~unlit & ~char & ~noink & ~graphic
        if look.freeze or look.freeze_lut is not None:
            drift = drift & frozen
        snow_lit = np.array([0.94, 0.97, 1.0], np.float32)
        snow_sh = np.array([0.90, 0.96, 1.0], np.float32) if look.bright_ice else np.array([0.70, 0.79, 0.95], np.float32)
        snow = np.where(lit[..., None], snow_lit, snow_sh)
        img = np.where(drift[..., None], snow, img)
    img = np.where(unlit[..., None], lit_tone * look.unlit_gain, img)
    # The character keeps her own painted colour: she is the one warm thing left in the room.
    img = np.where(char[..., None], base, img)
    img = np.where(noink[..., None] | sky[..., None], base, img)
    # ink
    skip = noink.copy()
    for oid in look.no_ink_ids:
        skip |= np.abs(ob - oid) < 0.5
    lines = ink_lines(ob, depth, normal, char, pos, ss, look, seed, skip_wide=skip)
    if look.ink_fade_box is not None:
        # a room full of small furniture seen from far away: its fine lines would pack into noise, so they leave first
        (bx0, by0, bz0), (bx1, by1, bz1), d0, d1 = look.ink_fade_box
        p0 = np.nan_to_num(pos, posinf=1e4, neginf=-1e4)
        inside = ((p0[..., 0] > bx0) & (p0[..., 0] < bx1) & (p0[..., 1] > by0) & (p0[..., 1] < by1) &
                  (p0[..., 2] > bz0) & (p0[..., 2] < bz1))
        fade = np.clip((d1 - np.nan_to_num(depth, posinf=1e6)) / max(d1 - d0, 1e-3), 0, 1).astype(np.float32)
        lines = np.where(inside, lines * fade, lines)
    img = img * (1 - lines[..., None]) + INK * lines[..., None]
    rgba = np.dstack([np.clip(img, 0, 1), alpha])
    if ss != 1.0:
        rgba = cv2.resize(rgba, (int(round(w / ss)), int(round(h / ss))), interpolation=cv2.INTER_AREA)
    return rgba


# ------------------------------------------------- the same painting on the graphics card
# Everything below mirrors the functions above line by line, in float32 like NumPy's own promotion rules give
# (a Python float never widens a float32 array). Three things stay on the CPU on purpose: the thresholds and
# sampling cv2 already does fast (Laplacian, distanceTransform, remap, the final area resize), and the roof hash,
# where sin() is multiplied by 43758 and so a last-bit difference between NumPy's sin and CUDA's would be a
# different roof. np.interp works in float64, so its stand-in here does too.
# torch is imported on first use: a Pool's parent, and any process without PAINT_GPU=1, never load it.

_gpu_state = {"tried": False, "torch": None}


def _gpu():
    """torch if PAINT_GPU=1 and CUDA really works in this process, else None."""
    if os.environ.get("PAINT_GPU") != "1":
        return None
    if not _gpu_state["tried"]:
        _gpu_state["tried"] = True
        try:
            import torch
            if not torch.cuda.is_available():
                raise RuntimeError("CUDA is not available")
            torch.set_num_threads(1)   # torch only moves arrays here; its CPU thread pool would just sit idle
            torch.zeros(1, device="cuda")
            _gpu_state["torch"] = torch
        except Exception as e:
            print(f"PAINT_GPU: painting on the CPU: {e!r}", flush=True)
    return _gpu_state["torch"]


def _try_gpu(fn, *args):
    """fn's result, or None when the caller should paint on the CPU instead. Running out of video memory costs one frame
    the CPU's time; any other failure sends the rest of this process to the CPU. Either way the picture is the same."""
    th = _gpu()
    if th is None:
        return None
    try:
        return fn(th, *args)
    except Exception as e:
        out_of_memory = isinstance(e, th.cuda.OutOfMemoryError)
        print(f"PAINT_GPU: this frame goes to the CPU{'' if out_of_memory else ', and all later ones'}: {e!r}", flush=True)
        if not out_of_memory:
            _gpu_state["torch"] = None
    th.cuda.empty_cache()
    return None


def _up(th, a):
    return th.from_numpy(np.asarray(a, np.float32)).to("cuda")


def _vec(th, v):
    return th.tensor(v, dtype=th.float32, device="cuda")


def _linear_to_srgb_gpu(th, c):
    return th.where(c <= 0.0031308, c * 12.92, 1.055 * th.pow(c.clamp(min=1e-6), 1 / 2.4) - 0.055)


def _world_noise_gpu(th, pos, scale, seed=0.0):
    p = pos[..., :3] * scale + seed
    return (th.sin(p[..., 0] * 1.27 + 3.1 * th.sin(p[..., 1] * 0.73 + seed)) +
            th.sin(p[..., 1] * 1.61 + 2.3 * th.sin(p[..., 2] * 0.91 + 1.7)) +
            th.sin(p[..., 2] * 1.13 + 2.7 * th.sin(p[..., 0] * 0.67 + 0.4))) / 6 + 0.5


def _interp_gpu(th, x, xp, fp):
    """np.interp for fixed knots, in float64 as NumPy does it; the callers cast back to float32 as the CPU path does."""
    d = x.double()
    out = th.full_like(d, fp[0])
    for j in range(len(xp) - 1):
        out = th.where(d >= xp[j], (fp[j + 1] - fp[j]) / (xp[j + 1] - xp[j]) * (d - xp[j]) + fp[j], out)
    out = th.where(d >= xp[-1], th.full_like(d, fp[-1]), out)
    return th.where(th.isnan(d), d, out).float()


def _grow_9_gpu(th, m):
    """cv2.dilate with a 9x9 square: outside the image counts as empty, as cv2's default border does for dilate."""
    return th.nn.functional.max_pool2d(m.float()[None, None], 9, 1, 4)[0, 0] > 0


def _ink_lines_gpu(th, ob_id, depth, normal, skip_mask, pos, ss, look, seed=0, skip_wide=None):
    h, w = ob_id.shape
    idi = th.round(ob_id).to(th.int32)
    e = th.zeros((h, w), dtype=th.bool, device="cuda")
    e[:-1, :] |= idi[:-1, :] != idi[1:, :]
    e[:, :-1] |= idi[:, :-1] != idi[:, 1:]
    del idi
    d = th.where(th.isfinite(depth) & (depth < 1e8), depth, 1e6)
    logd = th.log(d.clamp(min=1e-3))
    dz = th.zeros((h, w), device="cuda")
    dz[:-1, :] = th.abs(logd[:-1, :] - logd[1:, :])
    dzx = th.zeros((h, w), device="cuda")
    dzx[:, :-1] = th.abs(logd[:, :-1] - logd[:, 1:])
    crease = th.from_numpy(np.abs(cv2.Laplacian(logd.cpu().numpy(), cv2.CV_32F, ksize=1)) > 0.012).to("cuda")
    e |= (dz > 0.035) & crease
    e |= (dzx > 0.035) & crease
    del logd, dz, dzx, crease
    n = normal[..., :3]
    nn = th.zeros((h, w), device="cuda")
    nn[:-1, :] = 1 - (n[:-1, :] * n[1:, :]).sum(-1)
    nx = th.zeros((h, w), device="cuda")
    nx[:, :-1] = 1 - (n[:, :-1] * n[:, 1:]).sum(-1)
    e |= (nn > 0.22) | (nx > 0.22)
    del nn, nx
    if look.edge_m:
        da = th.zeros((h, w), device="cuda")
        da[:-1, :] = th.abs(d[:-1, :] - d[1:, :])
        db = th.zeros((h, w), device="cuda")
        db[:, :-1] = th.abs(d[:, :-1] - d[:, 1:])
        e |= (da > look.edge_m) | (db > look.edge_m)
        del da, db
    bg = ~th.isfinite(depth) | (depth > 1e8)
    if skip_mask is not None:
        e &= ~_grow_9_gpu(th, th.from_numpy(close_gaps(skip_mask.cpu().numpy()) > 0).to("cuda"))
    if skip_wide is not None:
        e &= ~_grow_9_gpu(th, skip_wide)
    e &= ~bg
    dist = cv2.distanceTransform(1 - mend_ink(e.cpu().numpy(), ss).astype(np.uint8), cv2.DIST_L2, 3)
    del e
    p = th.where(bg[..., None], 0.0, th.nan_to_num(pos, nan=0.0, posinf=0.0, neginf=0.0))
    press = 0.55 + 0.95 * _world_noise_gpu(th, p, 1.9, seed + 1.0) ** 1.2
    flutter = 0.92 + 0.16 * _world_noise_gpu(th, p, 13.0, seed + 2.0)
    del p
    near = (1.25 - 0.32 * th.log1p(th.where(bg, 50.0, d))).clamp(look.line_min, 1.0) * look.line_near
    width = look.line_px * ss * 0.5 * press * flutter * near
    del press, flutter, near, bg
    a = (width - th.from_numpy(dist).to("cuda") + 0.5).clamp(0, 1)
    del width
    a = a * look.line_alpha
    if look.line_fade is not None:
        d0, d1 = look.line_fade
        a = a * ((d1 - d) / max(d1 - d0, 1e-3)).clamp(0, 1)
    return a


def _ink_lines_from_numpy(th, ob_id, depth, normal, skip_mask, pos, ss, look, seed, skip_wide):
    """ink_lines for a painter that does its own colour with NumPy."""
    return _ink_lines_gpu(th, _up(th, ob_id), _up(th, depth), _up(th, normal), None if skip_mask is None else th.from_numpy(skip_mask).to("cuda"),
                          _up(th, pos), ss, look, seed, None if skip_wide is None else th.from_numpy(skip_wide).to("cuda")).cpu().numpy()


def _apply_live_gpu(th, base, ob, pos, live):
    for oid, (o, u, v, tex) in live.items():
        m = th.abs(ob - oid) < 0.5
        if not m.any():
            continue
        o_, u_, v_ = _vec(th, o), _vec(th, u), _vec(th, v)
        ua, va = u_ - o_, v_ - o_
        rel = pos - o_
        uu = (rel * ua).sum(-1) / (ua * ua).sum()
        vv = (rel * va).sum(-1) / (va * va).sum()
        del rel
        th_, tw = tex.shape[:2]
        s = cv2.remap(tex, (uu * tw).cpu().numpy(), (vv * th_).cpu().numpy(), cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
        del uu, vv
        s = _up(th, s)
        a = s[..., 3:4]
        base = th.where(m[..., None], base * (1 - a) + s[..., :3] * a, base)
        del s, a, m
    return base


def _roof_hash(th, ix, iy, roof):
    """np.mod(np.sin(...) * 43758.5453, 1.0) on the roof pixels, worked out by NumPy so every roof gets the very same value."""
    hs = th.zeros_like(ix)
    if roof.any():
        a, b = ix[roof].cpu().numpy(), iy[roof].cpu().numpy()
        hs[roof] = th.from_numpy(np.mod(np.sin(a * 12.9898 + b * 78.233) * 43758.5453, 1.0)).to("cuda")
    return hs


def _paint_gpu(th, passes, look, ss, seed):
    col = _up(th, passes["DiffCol"][..., :3])
    light = _up(th, passes["DiffDir"][..., :3])
    depth = _up(th, passes["Depth"])
    normal = _up(th, passes["Normal"][..., :3])
    pos = _up(th, passes["Position"][..., :3])
    ob = _up(th, passes["IndexOB"])
    ma = th.round(_up(th, passes["IndexMA"])).to(th.int32)
    alpha = passes["Alpha"].astype(np.float32) if "Alpha" in passes else np.ones(passes["Depth"].shape, np.float32)
    h, w = depth.shape
    base = _linear_to_srgb_gpu(th, col.clamp(0, 1))
    del col
    if look.live:
        base = _apply_live_gpu(th, base, ob, pos, look.live)
    lit_amount = light.mean(-1)
    del light
    unlit, char, noink, graphic, sky = ma == 1, ma == 2, ma == 3, ma == 4, ma == 5
    del ma
    lit = lit_amount > look.light_threshold
    del lit_amount
    for oid in look.force_lit:
        lit = lit | (th.abs(ob - oid) < 0.5)
    tint = _vec(th, look.shadow_tint)
    plane = (0.93 + 0.07 * normal[..., 2].clamp(0, 1)
             - 0.11 * (-normal[..., 2]).clamp(0, 1)
             - 0.06 * th.abs(normal[..., 1]))[..., None]
    shadow = base * tint * plane
    lit_tone = base
    frozen = th.zeros((h, w), dtype=th.bool, device="cuda")
    if look.freeze:
        p0 = th.nan_to_num(pos, nan=0.0, posinf=1e4, neginf=-1e4)
        wob = (_world_noise_gpu(th, p0, 0.9, 3.0) - 0.5) * 1.6 + (_world_noise_gpu(th, p0, 2.3, 7.0) - 0.5) * 0.4
        for pt, rad in look.freeze:
            if rad <= 0:
                continue
            dist = th.sqrt(((p0 - _vec(th, pt)) ** 2).sum(-1))
            frozen |= dist + wob < rad
        del wob
        if look.freeze_box is not None:
            (bx0, by0, bz0), (bx1, by1, bz1) = look.freeze_box
            frozen &= ((p0[..., 0] > bx0) & (p0[..., 0] < bx1) & (p0[..., 1] > by0) & (p0[..., 1] < by1) &
                       (p0[..., 2] > bz0) & (p0[..., 2] < bz1))
        del p0
    if look.freeze_lut is not None:
        ids = th.round(ob).to(th.int32).clamp(0, len(look.freeze_lut) - 1).long()
        frozen = th.from_numpy(look.freeze_lut <= look.time).to("cuda")[ids]
        del ids
    if look.town_id and look.town_detail > 0:
        m = th.abs(ob - look.town_id) < 0.5
        nz = th.abs(normal[..., 2])
        far = ((1400.0 - depth) / 600.0).clamp(0, 1) * look.town_detail
        wall = m & (nz < 0.3)
        z_ = (pos[..., 2] - look.town_base) / max(look.town_h, 0.05)
        u_ = th.where(th.abs(normal[..., 1]) > th.abs(normal[..., 0]), pos[..., 0], pos[..., 1])
        zm = th.remainder(z_, 3.0)
        win = wall & (zm > 1.0) & (zm < 2.3) & (th.remainder(u_, 2.8) > 0.35) & (z_ > 0.8)
        del nz, wall, z_, u_, zm
        k_ = (win * far)[..., None]
        base = base * (1 - k_) + _vec(th, (0.42, 0.56, 0.66)) * k_
        del win
        roof = m & (normal[..., 2] > 0.9) & (pos[..., 2] > look.town_base + 0.5)
        cx_, cy_ = pos[..., 0] / 5.0, pos[..., 1] / 5.0
        ix_, iy_ = th.floor(cx_), th.floor(cy_)
        hs_ = _roof_hash(th, ix_, iy_, roof)
        unit = roof & (hs_ > 0.55) & (th.abs(cx_ - ix_ - 0.5) < 0.10 + 0.14 * hs_) & (th.abs(cy_ - iy_ - 0.5) < 0.12)
        del roof, cx_, cy_, ix_, iy_, hs_
        k_ = (unit * far * 0.42)[..., None]
        base = base * (1 - k_) + base * 0.62 * k_
        del unit, far, k_
        gm = base.mean(-1, keepdim=True)
        base = th.where(m[..., None], gm + (base - gm) * (1 + 0.9 * look.town_detail), base)
        del gm, m
        lit_tone = base
        shadow = base * tint * plane
    if look.cold > 0 or look.freeze or look.freeze_lut is not None:
        g = base.mean(-1, keepdim=True)
        v = _interp_gpu(th, g, [0.0, 0.35, 0.60, 1.0], [0.10, 0.40, 0.80, 0.97])
        cold_lit = (v + 0.05) * _vec(th, COLD_LIT.tolist())
        cold_sh = v * _vec(th, COLD_SH.tolist()) * plane
        if look.bright_ice:
            v = _interp_gpu(th, g, [0.0, 0.30, 0.55, 1.0], [0.08, 0.40, 0.86, 0.99])
            ice_plane = (0.91 + 0.09 * normal[..., 2].clamp(0, 1) - 0.20 * (-normal[..., 2]).clamp(0, 1)
                         - 0.09 * th.abs(normal[..., 1]) - 0.03 * th.abs(normal[..., 0]))[..., None]
            cold_lit = (v + 0.04) * _vec(th, COLD_LIT.tolist())
            cold_sh = v * _vec(th, (0.84, 0.96, 1.04)) * ice_plane
            del ice_plane
        del g, v
        if look.freeze or look.freeze_lut is not None:
            k = frozen[..., None].float()
        else:
            k = th.full((h, w, 1), look.cold, dtype=th.float32, device="cuda")
        k = th.where(graphic[..., None] | sky[..., None], 0.0, k)
        lit_tone = base * (1 - k) + cold_lit * k
        shadow = shadow * (1 - k) + cold_sh * k
        del k, cold_lit, cold_sh
    shadow = th.where(graphic[..., None], base * _vec(th, (0.80, 0.84, 0.92)) * plane, shadow)
    del plane
    img = th.where(lit[..., None], lit_tone, shadow)
    del shadow
    if look.snow > 0:
        up = normal[..., 2].clamp(0, 1)
        f = (_world_noise_gpu(th, pos, 2.3) * 0.55 + _world_noise_gpu(th, pos, 9.0, 2.0) * 0.30 + _world_noise_gpu(th, pos, 31.0, 5.0) * 0.15)
        drift = (up > 0.8) & (f > 1.05 - look.snow * 0.85) & ~unlit & ~char & ~noink & ~graphic
        del up, f
        if look.freeze or look.freeze_lut is not None:
            drift = drift & frozen
        snow_lit = _vec(th, (0.94, 0.97, 1.0))
        snow_sh = _vec(th, (0.90, 0.96, 1.0) if look.bright_ice else (0.70, 0.79, 0.95))
        img = th.where(drift[..., None], th.where(lit[..., None], snow_lit, snow_sh), img)
        del drift
    del frozen, lit
    img = th.where(unlit[..., None], lit_tone * look.unlit_gain, img)
    del lit_tone
    img = th.where(char[..., None], base, img)
    img = th.where(noink[..., None] | sky[..., None], base, img)
    del base, unlit, graphic, sky
    skip = noink
    for oid in look.no_ink_ids:
        skip = skip | (th.abs(ob - oid) < 0.5)
    lines = _ink_lines_gpu(th, ob, depth, normal, char, pos, ss, look, seed, skip_wide=skip)
    del ob, normal, char, noink, skip
    if look.ink_fade_box is not None:
        (bx0, by0, bz0), (bx1, by1, bz1), d0, d1 = look.ink_fade_box
        p0 = th.nan_to_num(pos, nan=0.0, posinf=1e4, neginf=-1e4)
        inside = ((p0[..., 0] > bx0) & (p0[..., 0] < bx1) & (p0[..., 1] > by0) & (p0[..., 1] < by1) &
                  (p0[..., 2] > bz0) & (p0[..., 2] < bz1))
        fade = ((d1 - th.nan_to_num(depth, nan=0.0, posinf=1e6)) / max(d1 - d0, 1e-3)).clamp(0, 1)
        lines = th.where(inside, lines * fade, lines)
        del p0, inside, fade
    del depth, pos
    img = img * (1 - lines[..., None]) + _vec(th, INK.tolist()) * lines[..., None]
    del lines
    rgba = np.dstack([img.clamp(0, 1).cpu().numpy(), alpha])
    del img
    if ss != 1.0:
        rgba = cv2.resize(rgba, (int(round(w / ss)), int(round(h / ss))), interpolation=cv2.INTER_AREA)
    return rgba
