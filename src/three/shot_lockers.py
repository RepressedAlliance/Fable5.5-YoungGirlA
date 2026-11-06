"""The entrance hall and its shoe lockers, seen from outside through the open side, past the pillars."""
import json
import math
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import bpy  # noqa: E402
import crowdkit  # noqa: E402
import kit  # noqa: E402
import setkit  # noqa: E402
from kit import box, cyl, mat, plane  # noqa: E402
from setkit import TEX, loft, wall_plane  # noqa: E402
import shared_crowd as C  # noqa: E402
import shared_lockers as S  # noqa: E402

UID_SKY = 9101
UID_APRON = 9102
UID_HER_PLATE = 9103
UID_CEIL = 9104
UID_HER_SHOES = 9105
PLATE_COLS, PLATE_ROWS = 8, 12
CUT_DIR = kit.ROOT / "assets" / "gen" / "cut"
UW_BOX = (194, 1333, 169, 888)
LOAFER_BOX = (297, 1238, 214, 848)


def materials(warm):
    wc = (lambda a, b: b if warm else a)
    return {
        "steel": mat("lsteel", wc("#DDD6BF", "#E4D8BD")),
        "back": mat("lback", wc("#B6AC94", "#B8A88E")),
        "rail": mat("lrail", wc("#C6BDA2", "#D3C5A7")),
        "wall": mat("lwall", wc("#E9E6D8", "#F2E8D2")),
        "wain": mat("lwain", wc("#B2A98E", "#C4AE88")),
        "pillar": mat("lpillar", wc("#E7E1CE", "#EDE2CA")),
        "pillar_low": mat("lpillar_low", wc("#8F8F7E", "#B09A78")),
        "ceil": mat("lceil", wc("#ECEBE2", "#F1E9D6"), kind=1),
        "upper": mat("lupper", wc("#E0DBC9", "#EDE2CA"), kind=1),
        "lamp": mat("llamp", "#FBFAF2", kind=1),
        "lampbase": mat("llampbase", "#C9CCC6", kind=1),
        "floor": mat("lfloor", "#AEB5AE", tex=TEX / "hall_floor.png", repeat=(14, 2.4)),
        "umb4": mat("lumb4", "#B8413C"),
        "apron": mat("lapron", "#B9BCB6", tex=TEX / "apron.png", repeat=(8, 3)),
        "gutter": mat("lgutter", "#6E737B"),
        "grate": mat("lgrate", "#3A3D45"),
        "plates": mat("lplates", "#F6F3EA", kind=4, tex=TEX / "plates.png"),
        "duck": mat("lduck", wc("#B99A6C", "#CBA874")),
        "duck_dark": mat("lduck_dark", "#7C6444"),
        "white": mat("lwhite", "#F4F2E8"),
        "toe": mat("ltoe", "#1E9CC8"),
        "shoesole": mat("lsole", "#C9C6B8"),
        "brown": mat("lbrown", "#8A4E2C"),
        "brown_d": mat("lbrown_d", "#5F3218"),
        "brown_m": mat("lbrown_m", "#74421F"),
        "shoe_in": mat("lshoe_in", "#2A1A12"),
        "umb": mat("lumb", "#3A3D45"),
        "umb2": mat("lumb2", "#2A6E8E"),
        "umb3": mat("lumb3", "#F0EAD6"),
        "stand": mat("lstand", "#8D9299"),
        "sky": mat("lsky", "#03C3FB", kind=5),
        "frame": mat("lframe", "#BFC4BE"),
        "cork": mat("lcork", "#A98B62"),
        "clock": mat("lclock", "#F6F3EA"),
        "dark": mat("ldark", "#24262C"),
        "mat": mat("lmat", wc("#3F4C50", "#5A5A4E")),
        "yard": mat("lyard", wc("#B9BCB6", "#CFC6AE")),
        "block": mat("lblock", wc("#D9DAD2", "#EDE2CA")),
        "blockroof": mat("lblockroof", "#6E737B"),
        "blockwin": mat("lblockwin", wc("#7D8F9B", "#8FA6AE")),
        "tree": mat("ltree", wc("#5D8F73", "#7FA765")),
        "trunk": mat("ltrunk", "#6E5A48"),
    }


def _outline(l, w, ty=0.0, n=16):
    """Plan outline of a shoe, toe at -y: rounder at the toe, narrower at the waist, rounded heel."""
    pts = []
    for k in range(n):
        a = 2 * math.pi * k / n
        cx, sy = math.cos(a), math.sin(a)
        wid = w * (0.82 if sy > 0 else 1.0)
        pts.append((wid * cx, l * sy + ty))
    return pts


def _soft(ob):
    for p in ob.data.polygons:
        p.use_smooth = True
    return ob


def shoe(x, y, z, yaw, sole_m, body_m, inner_m, heel_m=None, strap_m=None, uid=None, cap_m=None):
    """One shoe, in the round: low at the toe, rising to the collar, a dark opening at the heel end. yaw 0 = toe towards -y."""
    rot = (0, 0, yaw)
    out = []
    out.append(loft("sole", [(0.0, _outline(0.122, 0.044)), (0.012, _outline(0.122, 0.044))], sole_m, (x, y, z), rot, uid=uid))
    out.append(_soft(loft("body", [(0.012, _outline(0.118, 0.041)), (0.030, _outline(0.114, 0.040)), (0.042, _outline(0.098, 0.036, 0.016)),
                                   (0.052, _outline(0.076, 0.031, 0.040)), (0.059, _outline(0.064, 0.029, 0.052))], body_m, (x, y, z), rot, uid=uid)))
    out.append(loft("opening", [(0.0, _outline(0.05, 0.021, 0.056)), (0.002, _outline(0.05, 0.021, 0.056))], inner_m, (x, y, z + 0.0585), rot, uid=uid))
    c, si = math.cos(yaw), math.sin(yaw)
    w = lambda lx, ly, lz: (x + lx * c - ly * si, y + lx * si + ly * c, z + lz)
    if heel_m is not None:
        out.append(box("heelblock", w(0, 0.082, 0.0), (0.07, 0.07, 0.024), heel_m, rot=rot, uid=uid))
    if cap_m is not None:
        # an indoor shoe's coloured rubber toe, hugging the front of the body
        out.append(_soft(loft("cap", [(0.012, _outline(0.070, 0.0445, -0.052)), (0.024, _outline(0.067, 0.0425, -0.052)),
                                      (0.036, _outline(0.056, 0.0375, -0.056)), (0.047, _outline(0.036, 0.026, -0.058))], cap_m, (x, y, z), rot, uid=uid)))
    if strap_m is not None:
        # the saddle strap lying across the vamp, with its slot
        out.append(box("strap", w(0, -0.024, 0.0455), (0.072, 0.036, 0.008), strap_m, rot=(-0.48, 0, yaw), uid=uid))
        out.append(box("slot", w(0, -0.024, 0.0505), (0.034, 0.010, 0.004), inner_m, rot=(-0.48, 0, yaw), uid=uid))
    return out


def uwabaki(M, x, y, z, parts):
    """A pair of white indoor shoes with the coloured band across the instep, put away the same way as everyone's."""
    yaw = -0.5 + random.Random(int(x * 97 + z * 311)).uniform(-0.1, 0.1)
    for dx, dy in ((-0.062, -0.015), (0.058, 0.015)):
        parts += shoe(x + dx, y + dy, z, yaw, M["shoesole"], M["white"], M["shoe_in"], cap_m=M["toe"])


def bank_cell_plate_z(tier):
    return S.PLINTH + (tier + 1) * S.CH - S.LIP / 2


def bank(M, her_state):
    """The whole bank is one mesh for the frame; plates are one mesh of quads off the atlas."""
    z_of = lambda k: S.PLINTH + k * S.CH
    parts = []
    w = S.COLS * S.CW
    xc = S.X0 + w / 2
    yc = S.DEPTH / 2
    # plinth, top, back, verticals, shelves
    parts.append(box("plinth", (xc, yc, S.PLINTH / 2), (w, S.DEPTH, S.PLINTH), M["rail"]))
    for k in range(S.TIERS + 1):
        parts.append(box("shelf", (xc, yc, z_of(k)), (w + 0.02, S.DEPTH, 0.014), M["steel"]))
    for i in range(S.COLS + 1):
        parts.append(box("upright", (S.X0 + i * S.CW, yc, S.PLINTH + S.TIERS * S.CH / 2), (0.012, S.DEPTH, S.TIERS * S.CH), M["steel"]))
    parts.append(box("back", (xc, S.DEPTH - 0.004, S.PLINTH + S.TIERS * S.CH / 2), (w, 0.008, S.TIERS * S.CH), M["back"]))
    # the rail under each shelf that holds the plates: a lip across the top of the cell below it
    for k in range(1, S.TIERS + 1):
        # flush with the shelf's front: a step of 2 mm is thinner than a pixel, and came out as a row of ink crumbs
        parts.append(box("lip", (xc, 0.006, z_of(k) - S.LIP / 2), (w + 0.02, 0.012, S.LIP), M["rail"]))
    kit.join(parts, "bank")
    # the roof cornice
    box("cornice", (xc, yc, S.TOP + 0.03), (w + 0.05, S.DEPTH + 0.04, 0.05), M["rail"])
    # plates: one quad per cell, its name off the atlas. Her cell is skipped.
    rnd = random.Random(31)
    items = []
    du, dv = 1 / PLATE_COLS, 1 / PLATE_ROWS
    pw, ph = 0.232, 0.039
    y = -0.0035
    her_col, her_tier = S.HER
    names = list(range(PLATE_COLS * PLATE_ROWS))
    perm = list(names)
    random.Random(7).shuffle(perm)
    for k in range(S.TIERS):
        for i in range(S.COLS):
            if (i, k) == (her_col, her_tier):
                continue
            rnd.choice(names)   # kept, so the shoes stay where they were
            # walking along the bank the same name only comes back after 16 columns, and never in the same frame
            n = perm[(i * S.TIERS + k) % len(names)]
            u0, v0 = (n % PLATE_COLS) * du, 1 - (n // PLATE_COLS + 1) * dv
            cx = S.X0 + (i + 0.5) * S.CW
            zc = bank_cell_plate_z(k)
            c = ((cx - pw / 2, y, zc - ph / 2), (cx + pw / 2, y, zc - ph / 2), (cx + pw / 2, y, zc + ph / 2), (cx - pw / 2, y, zc + ph / 2))
            items.append((c, ((u0, v0), (u0 + du, v0), (u0 + du, v0 + dv), (u0, v0 + dv))))
    setkit.quads("plates", items, M["plates"])
    # her plate
    cx = (S.HER_X0 + S.HER_X1) / 2
    zc = bank_cell_plate_z(her_tier)
    name = "plate_black" if her_state == "black" else "plate_torn"
    pm = kit.mat(name, "#F6F3EA", kind=4, tex=TEX / f"{name}.png", alpha_tex=True)
    # the texture has a margin around the plate proportional to it
    sx = pw * 512 / (512 - 72)
    sz = ph * 180 / (180 - 72)
    wall_plane("her_plate", (cx, y - 0.001, zc), sx, sz, pm, uid=UID_HER_PLATE)
    # shoes in the other cells: modelled, for the long slide when they are seen from the side and small; drawn, the same design as on her feet, once the cells face the lens
    shoes = []
    items = []
    bx0, bx1, by0, by1 = UW_BOX
    pw_ = 0.215
    k_ = pw_ / (bx1 - bx0)
    for k in range(S.TIERS):
        for i in range(S.COLS):
            if (i, k) == (her_col, her_tier):
                continue
            if rnd.random() < 0.62:
                x_, y_ = S.X0 + (i + 0.5) * S.CW + rnd.uniform(-0.012, 0.012), 0.16 + rnd.uniform(-0.012, 0.012)
                z_ = z_of(k) + 0.007
                uwabaki(M, x_, y_, z_, shoes)
                flip = (i * 7 + k * 3) % 5 == 0
                u0, u1 = bx0 / 1536, bx1 / 1536
                v0, v1 = 1 - by1 / 1024, 1 - by0 / 1024
                if flip:
                    u0, u1 = u1, u0
                h_ = (by1 - by0) * k_
                items.append((((x_ - pw_ / 2, y_, z_), (x_ + pw_ / 2, y_, z_), (x_ + pw_ / 2, y_, z_ + h_), (x_ - pw_ / 2, y_, z_ + h_)), ((u0, v0), (u1, v0), (u1, v1), (u0, v1))))
    solid = kit.join(shoes, "shoes")
    cards = setkit.quads("shoe_cards", items, mat("uwabaki_card", "#FFFFFF", tex=CUT_DIR / "x02_uwabaki_cell.png", alpha_tex=True))
    for nd in cards.data.materials[0].node_tree.nodes:
        if nd.type == "TEX_IMAGE":
            nd.extension = "CLIP"
    return solid, cards


class HerLoafers:
    """The pair she carries at 214.5, drawn, standing in her cell: a card that faces the lens, with a hard shadow on the cell's floor, so it is the same pair in both places."""

    def __init__(self, M):
        cx, z = (S.HER_X0 + S.HER_X1) / 2, S.PLINTH + S.HER[1] * S.CH + 0.0072
        self.p = (cx, 0.15, z)
        x0, x1, y0, y1 = LOAFER_BOX
        # the pair fills most of the cell's 30 cm
        self.card = setkit.Figure(CUT_DIR / "x01_loafers_cell.png", "her_loafers", 0.225 / (x1 - x0), y1 - 8, (x0 + x1) // 2, sun=None, img_wh=(1536, 1024), uid=UID_HER_SHOES)
        m = mat("loafer_shadow", "#7B6647", kind=3)
        self.shadow = []
        for dx in (-0.056, 0.058):
            ob = cyl("loafer_shadow", (cx + dx + 0.006, 0.160, z + 0.0005), (cx + dx + 0.006, 0.160, z + 0.0009), 0.058, m, seg=20, uid=UID_HER_SHOES + 1)
            ob.scale = (1.0, 0.72, 1.0)
            ob.visible_shadow = False
            self.shadow.append(ob)

    def place(self, eye, on=True):
        self.card.show(on)
        for ob in self.shadow:
            ob.hide_render = not on
        if on:
            self.card.place(self.p, eye)


def hall(M, warm=True):
    w0, w1 = S.X0 - 8, S.X0 + S.COLS * S.CW + 8
    wx = (w0 + w1) / 2
    L = w1 - w0
    # floors
    plane("floor", (wx, (S.EAVE_Y + S.DEPTH + 0.4) / 2, 0.0), L, S.DEPTH + 0.4 - S.EAVE_Y, M["floor"])
    # outside: wet concrete up to the camera, with a drain along the edge of the hall
    plane("apron", (wx, S.EAVE_Y - 8, -0.05), L, 16, M["apron"], uid=UID_APRON)
    box("step", (wx, S.EAVE_Y + 0.05, -0.026), (L, 0.10, 0.05), M["gutter"])
    plane("gutter", (wx, S.EAVE_Y - 0.13, -0.049), L, 0.16, M["grate"])
    # the wall behind the bank
    y_b = S.DEPTH + 0.1
    box("back_low", (wx, y_b + 0.1, 0.9), (L, 0.2, 1.8), M["wall"])
    box("wain", (wx, y_b - 0.006, 0.45), (L, 0.012, 0.9), M["wain"])
    # high windows above the bank: real openings, the sky behind them
    box("back_top", (wx, y_b + 0.1, 2.66), (L, 0.2, 0.2), M["upper"])
    n = int(L / 2.4)
    for i in range(n + 1):
        box("win_pier", (w0 + i * 2.4, y_b + 0.1, 2.18), (0.24, 0.2, 0.76), M["wall"])
        box("win_frame", (w0 + i * 2.4 + 1.2, y_b + 0.1, 2.18), (0.04, 0.05, 0.76), M["frame"])
    box("sill", (wx, y_b - 0.03, 1.81), (L, 0.09, 0.04), M["frame"])
    box("win_rail", (wx, y_b + 0.1, 2.18), (L, 0.05, 0.04), M["frame"])
    plane("sky", (wx, 60, 8), 800, 200, M["sky"], rot=(math.pi / 2, 0, 0), uid=UID_SKY)
    # what is out past the pillars, now that we look along the hall from inside: the yard, its wall, the next block, trees, sky
    plane("sky_out", (wx, -160, 20), 1200, 300, M["sky"], rot=(math.pi / 2, 0, 0), uid=UID_SKY)
    plane("sky_end", (160, -60, 20), 500, 300, M["sky"], rot=(math.pi / 2, 0, math.pi / 2), uid=UID_SKY)
    plane("yard_far", (40, S.EAVE_Y - 60, -0.06), 400, 120, M["yard"], uid=UID_APRON)
    box("hall_end", (w1, (S.EAVE_Y + y_b) / 2, S.HALL_H / 2), (0.2, y_b - S.EAVE_Y + 0.5, S.HALL_H), M["wall"])
    box("yard_wall", (40, -24.5, 0.7), (400, 0.25, 1.4), M["wall"])
    box("yard_cap", (40, -24.5, 1.44), (400, 0.34, 0.08), M["gutter"])
    box("far_block", (24, -36, 5.0), (120, 8, 10), M["block"])
    box("far_block_roof", (24, -36, 10.1), (121, 8.6, 0.25), M["blockroof"])
    for fl in (2.0, 5.2, 8.0):
        xw = -30.0
        while xw < 80:
            box("far_win", (xw, -31.97, fl), (2.0, 0.04, 1.3), M["blockwin"])
            xw += 3.4
    for tx_, ty_, r_ in ((-2.0, -22.0, 2.0), (4.0, -22.5, 2.4), (11.0, -22.0, 2.1), (19.0, -22.5, 2.6)):
        cyl("tree_t", (tx_, ty_, -0.05), (tx_, ty_, 2.4), 0.14, M["trunk"], seg=6)
        for dx_, dz_, k_ in ((0, 0.9, 0.86), (-0.62, 0.45, 0.62), (0.66, 0.5, 0.58)):
            setkit.blob("tree_c", (tx_ + dx_ * r_, ty_, 2.4 + dz_ * r_), (r_ * k_, r_ * k_, r_ * k_ * 0.85), M["tree"])
    # ceiling and the lamp rows
    plane("ceil", (wx, (S.EAVE_Y + y_b) / 2, S.HALL_H), L, y_b - S.EAVE_Y + 0.3, M["ceil"], uid=UID_CEIL)
    x = S.X0 - 2.0
    while x < S.X0 + S.COLS * S.CW + 2:
        for y_ in (-0.9, -2.1):
            box("lamp_base", (x, y_, S.HALL_H - 0.03), (1.3, 0.2, 0.05), M["lampbase"])
            box("lamp", (x, y_ - 0.045, S.HALL_H - 0.075), (1.22, 0.05, 0.05), M["lamp"])
            box("lamp", (x, y_ + 0.045, S.HALL_H - 0.075), (1.22, 0.05, 0.05), M["lamp"])
        x += 2.5
    # the facade above the hall's open side and its pillars
    box("beam", (wx, S.EAVE_Y, S.HALL_H + 0.39), (L, 0.5, 0.8), M["upper"])
    box("upper_wall", (wx, S.EAVE_Y + 0.4, 6.2), (L, 0.2, 6.4), M["upper"])
    x = -15.4
    while x < 14:
        pil = box("pillar", (x, S.EAVE_Y, S.HALL_H / 2), (0.46, 0.46, S.HALL_H), M["pillar"])
        pil.visible_shadow = False
        # a painted dado and a school notice, so a pillar passing the lens is a pillar and not a grey slab
        low = box("pillar_foot", (x, S.EAVE_Y, 0.45), (0.47, 0.47, 0.9), M["pillar_low"])
        low.visible_shadow = False
        foot = box("pillar_foot", (x, S.EAVE_Y, 0.06), (0.52, 0.52, 0.12), M["gutter"])
        foot.visible_shadow = False
        x += 4.0
    # things that belong in a shoe hall: duckboards, an umbrella stand and its umbrellas, a clock, notices
    y_d = -0.62
    for i in range(7):
        xa = -7.0 + i * 2.1
        parts = []
        for k in range(6):
            parts.append(box("slat", (xa, y_d - 0.3 + k * 0.12, 0.05), (1.9, 0.09, 0.02), M["duck"]))
        for dx in (-0.8, 0.0, 0.8):
            parts.append(box("runner", (xa + dx, y_d, 0.02), (0.05, 0.68, 0.04), M["duck_dark"]))
        kit.join(parts, "duckboard")
    for (xs, ys) in ((-3.1, -1.3), (5.8, -1.3)):
        if warm:
            box("stand_top", (xs, ys, 0.62), (0.95, 0.26, 0.03), M["stand"])
        else:
            # a rack with holes: the umbrellas stand through it
            for dy in (-0.12, 0.12):
                box("stand_rail", (xs, ys + dy, 0.62), (0.95, 0.02, 0.025), M["stand"])
            for k in range(6):
                box("stand_bar", (xs - 0.45 + k * 0.18, ys, 0.62), (0.015, 0.26, 0.025), M["stand"])
        box("stand_mid", (xs, ys, 0.26), (0.95, 0.26, 0.03), M["stand"])
        box("stand_bot", (xs, ys, 0.03), (0.95, 0.26, 0.06), M["stand"])
        for dx in (-0.46, 0.46):
            for dy in (-0.12, 0.12):
                cyl("stand_leg", (xs + dx, ys + dy, 0.03), (xs + dx, ys + dy, 0.62), 0.012, M["stand"], seg=5)
        rr = random.Random(int(xs * 10))
        for i in range(5):
            ux = xs - 0.36 + i * 0.18
            lean = rr.uniform(-0.05, 0.05)
            # a furled umbrella: narrow at the tip in the stand, full under the handle, a hooked handle on top
            colour = M[rr.choice(("umb", "umb2", "umb3", "umb4"))]
            body = setkit.cone("umb", (ux, ys, 0.06), 0.008, 0.034, 0.68, colour, rot=(0, lean * 1.45, 0), seg=8)
            if not warm:
                # round, so its facets take no ink, and closed at the top under the handle: not a cup on a stick
                setkit.cone("umb_top", (ux + lean * 0.985, ys, 0.74), 0.034, 0.008, 0.05, colour, rot=(0, lean * 1.45, 0), seg=14)
                for pg in body.data.polygons:
                    pg.use_smooth = True
            hx = ux + lean
            cyl("umb_h", (hx, ys, 0.73), (hx, ys, 0.84), 0.007, M["dark"], seg=5)
            cyl("umb_c", (hx, ys, 0.84), (hx + 0.022, ys, 0.875), 0.007, M["dark"], seg=5)
            cyl("umb_c", (hx + 0.022, ys, 0.875), (hx + 0.05, ys, 0.855), 0.007, M["dark"], seg=5)
    # a rubber mat on the floor at the edge
    plane("floormat", (S.HER_X0 - 3.0, -2.45, 0.004), 4.0, 0.7, M["mat"])
    plane("floormat", (S.HER_X0 + 3.4, -2.45, 0.004), 4.0, 0.7, M["mat"])


def build_set(warm=False):
    M = materials(warm)
    hall(M, warm)
    M["_shoes"] = bank(M, "torn" if warm else "black")
    if warm:
        # real afternoon sun: the pillars throw their shadows into the hall
        for o in bpy.context.scene.collection.objects:
            if o.name.startswith("pillar"):
                o.visible_shadow = True
        # this set is only ever seen square on
        M["_shoes"][0].hide_render = True
    return M


def school_bag(x, y, z, yaw, colour, trim):
    """A school bag set down on its base, with its two handles up."""
    c, si = math.cos(yaw), math.sin(yaw)
    w = lambda lx, ly, lz: (x + lx * c - ly * si, y + lx * si + ly * c, z + lz)
    box("bag", w(0, 0, 0.14), (0.38, 0.13, 0.28), colour, rot=(0, 0, yaw))
    box("bag_flap", w(0, -0.068, 0.20), (0.38, 0.006, 0.16), trim, rot=(0, 0, yaw))
    for dy in (-0.04, 0.04):
        pts = [w(-0.08, dy, 0.28), w(-0.07, dy, 0.36), w(0.0, dy, 0.39), w(0.07, dy, 0.36), w(0.08, dy, 0.28)]
        setkit.tube("bag_handle", setkit.chaikin(pts, 2), 0.007, trim, seg=5)


def rucksack(x, y, z, colour, trim):
    setkit.blob("sack", (x, y, z + 0.22), (0.17, 0.11, 0.23), colour)
    setkit.blob("sack_pocket", (x, y - 0.10, z + 0.14), (0.12, 0.04, 0.10), trim)


def leaning_umbrella(x, y0, colour, dark):
    """Furled, its tip on the floor and its handle against the front of the lockers. It has been out in the rain."""
    top = (x + 0.05, -0.005, 0.86)
    rot = (-math.atan2(-y0 + top[1], top[2]), math.atan2(0.05, 0.86), 0)
    body = setkit.cone("umb_lean", (x, y0, 0.0), 0.006, 0.032, 0.74, colour, rot=rot, seg=14)
    for pg in body.data.polygons:
        pg.use_smooth = True
    # the top of the furled cloth closes in on the shaft, and the handle runs on from it
    k = 0.74 / math.hypot(-y0 + top[1], top[2])
    a = (x + 0.05 * k, y0 + (-y0 + top[1]) * k, top[2] * k)
    setkit.cone("umb_lean_top", a, 0.032, 0.008, 0.045, colour, rot=rot, seg=14)
    cyl("umb_lean_h", a, top, 0.007, dark, seg=5)
    ob = kit.cyl("umb_wet", (x, y0, 0.0005), (x, y0, 0.0012), 0.065, kit.mat("lwet", "#8D9799", kind=3), seg=16)
    ob.scale = (1.0, 0.7, 1.0)
    ob.visible_shadow = False


def slips(M):
    """Notes stuck on the lockers: thin paper, a shadow under it, a little crooked. Thickest round her cell, a trail of them along the bank."""
    tex = TEX / "hall_slips.png"
    m = kit.mat("hall_slips", "#F6F3EA", kind=4, tex=tex)
    shade = kit.mat("hall_slip_shadow", "#7E7666", kind=3)
    r = random.Random(13)
    her_col, her_tier = S.HER
    spots = [(her_col - 1, her_tier + 1, 0.2), (her_col + 1, her_tier + 1, -0.3), (her_col - 1, her_tier, -0.1), (her_col + 1, her_tier, 0.25), (her_col - 2, her_tier + 2, 0.1), (her_col, her_tier + 2, -0.2),
             (her_col + 2, her_tier + 1, 0.15), (her_col + 2, her_tier + 3, -0.1), (her_col - 3, her_tier, 0.2), (her_col + 3, her_tier + 2, 0.05), (her_col - 1, her_tier + 3, -0.25), (her_col + 1, her_tier + 4, 0.1)]
    while len(spots) < 38:
        col, tier = r.randrange(4, S.COLS - 2), r.randrange(0, S.TIERS)
        # nothing covers her cell, or the inked-out name above it: that is what they have come to see
        if col != her_col or abs(tier - her_tier) > 1:
            spots.append((col, tier, r.uniform(-0.3, 0.3)))
    items, under = [], []
    for k, (col, tier, turn) in enumerate(spots):
        x0, x1, z0, z1 = S.cell_box(col, tier)
        cx = (x0 + x1) / 2 + r.uniform(-0.03, 0.03)
        # it hangs from the rail above the cell, over the top of the opening
        cz = z1 - S.LIP - 0.018 + r.uniform(-0.012, 0.012)
        w, h = 0.135, 0.084
        c_, s_ = math.cos(turn * 0.5), math.sin(turn * 0.5)
        n = k % 12
        u0, v1 = (n % 4) / 4, 1 - (n // 4) / 3
        u1, v0 = u0 + 1 / 4, v1 - 1 / 3
        q = lambda dx, dz, y: (cx + dx * c_ - dz * s_, y, cz + dx * s_ + dz * c_)
        y = -0.012
        items.append(((q(-w / 2, -h / 2, y), q(w / 2, -h / 2, y), q(w / 2, h / 2, y), q(-w / 2, h / 2, y)), ((u0, v0), (u1, v0), (u1, v1), (u0, v1))))
        d = 0.007
        qs = lambda dx, dz, y: (cx + d + dx * c_ - dz * s_, y, cz - d + dx * s_ + dz * c_)
        y = -0.008
        under.append(((qs(-w / 2, -h / 2, y), qs(w / 2, -h / 2, y), qs(w / 2, h / 2, y), qs(-w / 2, h / 2, y)), ((0, 0), (1, 0), (1, 1), (0, 1))))
    setkit.quads("slips", items, m).visible_shadow = False
    setkit.quads("slip_shadow", under, shade).visible_shadow = False


def dress(M):
    """The hall is used: bags put down, umbrellas stood against the lockers, notes stuck on."""
    navy, teal, tan, grey = mat("lbag0", "#26304F"), mat("lbag1", "#2A6E8E"), mat("lbag2", "#A98B62"), mat("lbag3", "#3A3D45")
    trim = mat("lbagtrim", "#1A1E30")
    cell = S.HER_C[0]
    for x, y, z, yaw, colour in ((cell - 1.55, -0.72, 0.062, 0.3, navy), (cell + 2.05, -0.60, 0.062, -0.2, navy), (-2.55, -0.60, 0.062, 0.15, teal), (0.42, -0.58, 0.062, -0.35, navy),
                                 (-4.55, -0.62, 0.062, 0.1, navy), (4.25, -0.65, 0.062, 0.25, tan), (6.2, -0.60, 0.062, -0.15, navy)):
        school_bag(x, y, z, yaw, colour, trim)
    for x, y, z, colour in ((cell - 1.82, -0.45, 0.062, grey), (cell + 2.42, -0.45, 0.062, teal), (-0.72, -0.46, 0.062, grey), (5.5, -0.45, 0.062, grey)):
        rucksack(x, y, z, colour, trim)
    for x, colour in ((-3.72, M["umb2"]), (-1.15, M["umb"]), (0.05, M["umb4"]), (cell - 1.62, M["umb"]), (cell + 1.88, M["umb2"]), (4.9, M["umb3"]), (6.75, M["umb"])):
        leaning_umbrella(x, -0.26, colour, M["dark"])
    slips(M)


def hall_pos(p, t):
    return p["x"], p["y"]


def build():
    sc = kit.reset()
    kit.setup_render(sc, 1920, 1080, ss=S.SS, fps=60, samples=3, threads=12)
    crowdkit.more_bounces(sc)
    sc.render.use_persistent_data = True
    M = build_set(False)
    dress(M)
    loafers = HerLoafers(M)
    M["_shoes"][1].hide_render = True
    kit.sun(sc, S.SUN)
    cam = kit.camera(sc, lens=30.0, clip_end=3000)
    ids = {"sky": UID_SKY, "apron": UID_APRON, "her_plate": UID_HER_PLATE, "ceil": UID_CEIL, "her_shoes": UID_HER_SHOES, "crowd": crowdkit.UID_CROWD}
    (kit.ROOT / "work" / "render" / "lockers_ids.json").write_text(json.dumps(ids))
    crowd = crowdkit.Crowd(S.people(), S.SUN, hall_pos)
    return sc, cam, loafers, M["_shoes"], crowd


def set_frame(t, sc, cam, loafers, shoes, crowd):
    eye, tg, up = S.camera_at(t)
    setkit.set_camera(cam, eye, tg, up, lens=S.lens_at(t))
    loafers.place(eye)
    crowd.place(t, eye)
    # the swap happens in the dark, part way round the turn
    front = t >= S.CARDS_FROM
    shoes[0].hide_render = front
    shoes[1].hide_render = not front


if __name__ == "__main__":
    setkit.run(kit.set_args(), S, build, set_frame)
