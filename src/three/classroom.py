"""The empty classroom. Facing the blackboard (+y): windows on the left (-x), corridor on the right (+x)."""
import math
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import bpy  # noqa: E402
import kit  # noqa: E402
from kit import box, cyl, mat, plane  # noqa: E402

TEX = kit.ROOT / "assets" / "tex"

W, D, H = 7.6, 9.2, 3.0
X0, X1, Y0, Y1 = -W / 2, W / 2, 0.0, D
COLS, ROWS = 6, 5
HER = (1, 3)


def desk_pos(col, row):
    """col 0 is next to the windows, row 0 is the front row."""
    x = X0 + 1.05 + col * ((W - 2.1) / (COLS - 1))
    y = Y1 - 2.85 - row * 1.02
    return x, y


def materials():
    return {
        "wall": mat("wall", "#F2ECD9", tex=TEX / "wall.png"),
        "wain": mat("wain", "#C8A66F"),
        "ceil": mat("ceil", "#F5F2E6"),
        "floor": mat("floor", "#C48B50", tex=TEX / "floor.png"),
        "top": mat("desk_top", "#E5B56E", tex=TEX / "desktop.png"),
        "steel": mat("steel", "#5F6E78"),
        "seat": mat("seat", "#C89C63"),
        # kind 4: the blackboard never freezes. It stays the one dark, solid thing in the room, so chalk reads on it.
        "board": mat("board", "#2E5A4B", kind=4, tex=TEX / "board.png"),
        "frame": mat("frame", "#8A6946"),
        "alu": mat("alu", "#D5D9D4"),
        "curtain": mat("curtain", "#D9D6C4"),
        "locker": mat("locker", "#C4C9C2"),
        "dark": mat("dark", "#2A2C33"),
        "door": mat("door", "#A67E54"),
        "notice": mat("notice", "#9A7B55"),
        "white": mat("white", "#F3F1E8"),
        "paper1": mat("paper1", "#F2EEDD"),
        "paper2": mat("paper2", "#EAD9A8"),
        "paper3": mat("paper3", "#CFE0D8"),
        "lamp": mat("lamp", "#F7F6EE"),
        "sky": mat("sky", "#03C3FB", kind=5),
    }


_rand = random.Random(41)


def desk(M, col, row, name, fixed=False):
    """Nobody lines their desk up exactly: small offsets, and chairs left however they were left."""
    x, y = desk_pos(col, row)
    jx, jy, pull, turn = 0.0, 0.0, 0.0, 0.0
    if not fixed:
        jx, jy = _rand.uniform(-0.07, 0.07), _rand.uniform(-0.09, 0.09)
        pull = _rand.uniform(-0.05, 0.22) ** 1
        turn = _rand.uniform(-0.28, 0.28)
    x += jx
    y += jy
    # A real school desk: top, and under it a book box whose opening faces the chair (students face +y).
    # The side towards the blackboard is closed by a panel; you only see into it from the student's side.
    bz0, bz1 = 0.555, 0.685
    w, dep = 0.56, 0.38
    parts = [
        box("t", (x, y, 0.70), (0.62, 0.44, 0.03), M["top"]),
        box("box_bottom", (x, y + 0.01, bz0), (w, dep, 0.012), M["steel"]),
        box("box_front", (x, y + 0.01 + dep / 2, (bz0 + bz1) / 2), (w, 0.012, bz1 - bz0), M["steel"]),
        box("box_l", (x - w / 2, y + 0.01, (bz0 + bz1) / 2), (0.012, dep, bz1 - bz0), M["steel"]),
        box("box_r", (x + w / 2, y + 0.01, (bz0 + bz1) / 2), (0.012, dep, bz1 - bz0), M["steel"]),
        # bag hook on the side
        box("hook", (x + 0.325, y - 0.05, 0.655), (0.03, 0.012, 0.05), M["steel"]),
    ]
    for dx in (-0.28, 0.28):
        for dy in (-0.19, 0.19):
            parts.append(cyl("l", (x + dx, y + dy, 0), (x + dx, y + dy, 0.69), 0.011, M["steel"], seg=6))
    # a footrest bar between the legs, on the blackboard side
    parts.append(cyl("bar", (x - 0.28, y + 0.19, 0.18), (x + 0.28, y + 0.19, 0.18), 0.008, M["steel"], seg=6))
    # some people left things in their desks: visible only from the chair side
    if not fixed and _rand.random() < 0.28:
        parts.append(box("books", (x + _rand.uniform(-0.12, 0.12), y + 0.02, bz0 + 0.035), (0.21, 0.28, 0.055),
                         _rand.choice([M["paper1"], M["paper3"], M["door"]])))
    d = kit.join(parts, name)
    # the chair belongs just behind the desk (students face +y)
    cy = -0.46 - pull
    ch = [
        box("s", (0, 0, 0.42), (0.38, 0.36, 0.02), M["seat"]),
        box("b", (0, -0.19, 0.72), (0.36, 0.015, 0.2), M["seat"]),
    ]
    for dx in (-0.17, 0.17):
        ch.append(cyl("l", (dx, 0.16, 0), (dx, 0.16, 0.41), 0.01, M["steel"], seg=6))
        ch.append(cyl("l", (dx, -0.17, 0), (dx, -0.17, 0.82), 0.01, M["steel"], seg=6))
    c = kit.join(ch, name + "_chair")
    c.location = (x, y + cy, 0.42)   # the joined chair keeps its seat's origin, 0.42 m off the floor
    c.rotation_euler = (0, 0, turn)
    return d, c


def shell(M, include_ceiling=True):
    """Walls have real openings: sunlight comes through the windows only."""
    wt = 0.2
    box("floor", (0, D / 2, -0.1), (W + 2 * wt, D + 2 * wt, 0.2), M["floor"])
    # stretch floor uv
    plane("floor_top", (0, D / 2, 0.002), W, D, M["floor"])
    if include_ceiling:
        box("ceil", (0, D / 2, H + 0.1), (W + 2 * wt, D + 2 * wt, 0.2), M["ceil"])
    # front and rear wall
    box("wall_front", (0, Y1 + wt / 2, H / 2), (W + 2 * wt, wt, H), M["wall"])
    box("wall_rear", (0, Y0 - wt / 2, H / 2), (W + 2 * wt, wt, H), M["wall"])
    # corridor wall, with a door gap at front and rear and high windows
    xr = X1 + wt / 2
    box("wall_corr_low", (xr, D / 2, 1.0), (wt, D, 2.0), M["wall"])
    box("wall_corr_top", (xr, D / 2, 2.8), (wt, D, 0.4), M["wall"])
    for yy in (1.5, 3.7, 5.9, 7.7):
        box("corr_pier", (xr, yy, 2.2), (wt, 0.55, 0.4), M["wall"])
    # window wall: sill, head and piers
    xl = X0 - wt / 2
    box("win_sill", (xl, D / 2, 0.45), (wt, D, 0.9), M["wall"])
    box("win_head", (xl, D / 2, 2.8), (wt, D, 0.4), M["wall"])
    pier_y = [0.2, 3.25, 6.3, 9.0]
    for yy in pier_y:
        box("win_pier", (xl, yy, 1.65), (wt, 0.4, 1.5), M["wall"])
    # aluminium window frames
    for a, b in ((0.4, 3.05), (3.45, 6.1), (6.5, 8.8)):
        mid = (a + b) / 2
        box("wf", (xl + 0.0, a + 0.02, 1.65), (0.05, 0.04, 1.5), M["alu"])
        box("wf", (xl + 0.0, b - 0.02, 1.65), (0.05, 0.04, 1.5), M["alu"])
        box("wf", (xl + 0.0, mid, 1.65), (0.05, 0.05, 1.5), M["alu"])
        box("wf", (xl, mid, 0.92), (0.05, b - a, 0.04), M["alu"])
        box("wf", (xl, mid, 2.38), (0.05, b - a, 0.04), M["alu"])
        box("wf", (xl, mid, 1.9), (0.04, b - a, 0.025), M["alu"])
    # gathered curtains at each pier: a row of soft folds is reduced to three flat slats
    for yy in pier_y[1:-1]:
        for k, off in enumerate((-0.28, -0.14, 0.0, 0.14, 0.28)):
            box("cur", (X0 + 0.11 + 0.025 * (k % 2), yy + off, 1.62), (0.07, 0.13, 1.6), M["curtain"])
    # wainscot and baseboards
    box("wain_rear", (0, Y0 + 0.012, 0.45), (W, 0.024, 0.9), M["wain"])
    box("wain_corr", (X1 - 0.012, D / 2, 0.45), (0.024, D, 0.9), M["wain"])
    box("wain_front", (0, Y1 - 0.012, 0.45), (W, 0.024, 0.9), M["wain"])
    box("base_win", (X0 + 0.012, D / 2, 0.45), (0.024, D, 0.9), M["wain"])
    # sky backdrop, far outside the windows
    # outside the windows there is nothing but the song's flat cyan
    plane("sky", (X0 - 30, D / 2, 5), 300, 200, M["sky"], rot=(math.pi / 2, 0, -math.pi / 2))


def front_wall(M):
    y = Y1 - 0.02
    box("bb_frame", (0, y, 1.62), (4.7, 0.03, 1.32), M["frame"])
    plane("board", (0, y - 0.02, 1.62), 4.56, 1.18, M["board"], rot=(math.pi / 2, 0, math.pi))
    box("chalk_tray", (0, y - 0.07, 0.99), (4.6, 0.11, 0.03), M["frame"])
    box("eraser", (1.2, y - 0.07, 1.02), (0.13, 0.05, 0.035), M["dark"])
    box("chalk", (0.7, y - 0.07, 1.015), (0.08, 0.012, 0.012), M["white"])
    box("chalk", (0.55, y - 0.05, 1.015), (0.07, 0.012, 0.012), M["paper2"])
    # podium
    box("podium", (0.0, Y1 - 1.05, 0.5), (1.1, 0.5, 1.0), M["door"])
    box("podium_top", (0.0, Y1 - 1.05, 1.01), (1.2, 0.58, 0.03), M["top"])
    box("step", (0.0, Y1 - 0.65, 0.09), (W - 0.5, 1.2, 0.18), M["floor"])
    # clock
    cyl("clock", (0, y - 0.0, 2.65), (0, y - 0.05, 2.65), 0.18, M["white"], seg=24)
    cyl("clock_rim", (0, y + 0.0, 2.65), (0, y - 0.03, 2.65), 0.2, M["dark"], seg=24)
    box("hand", (0.05, y - 0.06, 2.68), (0.11, 0.004, 0.012), M["dark"], rot=(0, -0.6, 0))
    box("hand", (-0.0, y - 0.06, 2.72), (0.012, 0.004, 0.15), M["dark"])
    # speaker
    box("speaker", (2.8, y - 0.04, 2.6), (0.36, 0.08, 0.26), M["door"])
    # notices either side of the board
    box("nb", (3.05, y - 0.005, 1.5), (0.8, 0.02, 1.05), M["notice"])
    box("p", (2.87, y - 0.018, 1.7), (0.3, 0.004, 0.42), M["paper1"])
    box("p", (3.22, y - 0.018, 1.75), (0.26, 0.004, 0.32), M["paper2"])
    box("p", (3.02, y - 0.018, 1.2), (0.46, 0.004, 0.32), M["paper3"])


def rear_wall(M):
    y = Y0 + 0.2
    # two rows of open cubby lockers
    nx, nz = 13, 3
    cw, ch, cd = 0.46, 0.3, 0.36
    x0 = -(nx - 1) * cw / 2
    parts = []
    for i in range(nx + 1):
        parts.append(box("v", (x0 + (i - 0.5) * cw, y, 0.45 + nz * ch / 2), (0.015, cd, nz * ch), M["locker"]))
    for k in range(nz + 1):
        parts.append(box("h", (x0 + (nx - 1) * cw / 2, y, 0.45 + k * ch), (nx * cw + 0.015, cd, 0.015), M["locker"]))
    parts.append(box("back", (x0 + (nx - 1) * cw / 2, Y0 + 0.02, 0.45 + nz * ch / 2), (nx * cw, 0.02, nz * ch), M["dark"]))
    parts.append(box("foot", (x0 + (nx - 1) * cw / 2, y, 0.22), (nx * cw, cd, 0.45), M["locker"]))
    kit.join(parts, "lockers")
    # a few forgotten things
    box("bag", (x0 + 2 * cw, y + 0.02, 0.45 + 1.5 * ch), (0.3, 0.2, 0.2), M["steel"])
    box("bag", (x0 + 7 * cw, y + 0.02, 0.45 + 0.5 * ch), (0.3, 0.2, 0.22), M["door"])
    # notice board on the upper rear wall
    box("nb2", (0, Y0 + 0.012, 2.25), (5.2, 0.02, 0.9), M["notice"])
    box("p", (-1.9, Y0 + 0.024, 2.3), (0.42, 0.004, 0.6), M["paper1"])
    box("p", (-1.1, Y0 + 0.024, 2.25), (0.6, 0.004, 0.42), M["paper3"])
    box("p", (0.2, Y0 + 0.024, 2.3), (0.42, 0.004, 0.6), M["paper2"])
    box("p", (1.3, Y0 + 0.024, 2.3), (0.42, 0.004, 0.6), M["paper1"])
    box("p", (2.05, Y0 + 0.024, 2.2), (0.42, 0.004, 0.42), M["paper3"])


def corridor_wall(M):
    x = X1 - 0.03
    # two sliding doors in the corridor wall, each with a frame, a small pane and a recessed handle
    glass = kit.mat("door_glass", "#BFD4D6")
    for cy in (8.0, 0.95):
        box("door_frame", (x + 0.012, cy, 1.0), (0.012, 1.02, 2.04), M["alu"])
        box("door", (x - 0.012, cy, 0.99), (0.03, 0.94, 1.98), M["door"])
        box("door_pane", (x - 0.03, cy, 1.5), (0.008, 0.46, 0.56), glass)
        box("door_handle", (x - 0.03, cy - 0.34, 1.0), (0.012, 0.05, 0.16), M["dark"])
    # transom panes over the corridor wall, under their frames
    for yy in (2.6, 4.8, 6.8):
        box("transom", (X1 + 0.02, yy, 2.3), (0.02, 1.6, 0.56), glass)
    # curtain rail above the windows
    box("curtain_rail", (X0 + 0.11, D / 2, 2.44), (0.03, D - 0.3, 0.03), M["alu"])
    box("corr_floor", (X1 + 1.6, D / 2, -0.1), (3, D + 4, 0.2), kit.mat("corr_floor", "#9FA7A1", kind=1))
    box("corr_wall", (X1 + 3.1, D / 2, 1.5), (0.2, D + 4, 3), kit.mat("corr_wall", "#D9D8CC", kind=1))


def ceiling_fixtures(M):
    for x in (-1.9, 1.9):
        for y in (1.8, 4.6, 7.4):
            box("lamp_base", (x, y, H - 0.03), (0.22, 1.25, 0.06), M["white"])
            box("lamp_tube", (x - 0.05, y, H - 0.08), (0.04, 1.2, 0.04), M["lamp"])
            box("lamp_tube", (x + 0.05, y, H - 0.08), (0.04, 1.2, 0.04), M["lamp"])


def build(ceiling=True):
    M = materials()
    shell(M, include_ceiling=ceiling)
    front_wall(M)
    rear_wall(M)
    corridor_wall(M)
    if ceiling:
        ceiling_fixtures(M)
    desks = {}
    for c in range(COLS):
        for r in range(ROWS):
            desks[(c, r)] = desk(M, c, r, f"desk_{c}_{r}", fixed=(c, r) == HER)
    settle_chairs(desks, fixed=(HER,))
    return M, desks


# ---------------------------------------------------------------- nothing stands in anything else
# 2026-11-17: chairs were left wherever the random pull and turn put them, and a pulled-out chair's back went into the
# front of the desk behind it. Every chair is now checked against every desk and every other chair, on the floor plan.
DESK_HALF = (0.31, 0.22)                   # the desk top, around its centre
CHAIR_BOX = (-0.19, 0.19, -0.205, 0.19)    # the chair's footprint around its seat origin: x0, x1, y0 (back), y1 (front)
CHAIR_BACK = (-0.205, -0.17)               # the strip the back and its posts take up
LEGS = [(dx, dy) for dx in (-0.28, 0.28) for dy in (-0.19, 0.19)]
GAP = 0.025


def _corners(cx, cy, ang, x0, x1, y0, y1):
    ca, sa = math.cos(ang), math.sin(ang)
    return [(cx + x * ca - y * sa, cy + x * sa + y * ca) for x, y in ((x0, y0), (x1, y0), (x1, y1), (x0, y1))]


def _apart(a, b, gap=GAP):
    """True when two convex polygons on the floor are at least gap apart along some axis (separating axis test)."""
    for poly in (a, b):
        for (x0, y0), (x1, y1) in zip(poly, poly[1:] + poly[:1]):
            nx, ny = y0 - y1, x1 - x0
            ln = math.hypot(nx, ny)
            nx, ny = nx / ln, ny / ln
            pa = [x * nx + y * ny for x, y in a]
            pb = [x * nx + y * ny for x, y in b]
            if max(pa) + gap <= min(pb) or max(pb) + gap <= min(pa):
                return True
    return False


def _inside(p, poly, margin):
    """p within poly grown by margin."""
    for (x0, y0), (x1, y1) in zip(poly, poly[1:] + poly[:1]):
        nx, ny = y1 - y0, x0 - x1
        ln = math.hypot(nx, ny)
        if ((p[0] - x0) * nx + (p[1] - y0) * ny) / ln > margin:
            return False
    return True


def _desk_xy(d):
    """A desk's centre: a joined desk keeps the origin of its first part, the top, which is centred on the desk."""
    return (d.location.x, d.location.y)


def chair_ok(key, cx, cy, ang, desks_xy, chairs):
    me = _corners(cx, cy, ang, *CHAIR_BOX)
    back = _corners(cx, cy, ang, CHAIR_BOX[0], CHAIR_BOX[1], *CHAIR_BACK)
    for k, (dx, dy) in desks_xy.items():
        top = _corners(dx, dy, 0.0, -DESK_HALF[0], DESK_HALF[0], -DESK_HALF[1], DESK_HALF[1])
        if k == key:
            # its own desk: the seat may go in under the top, but the back stays out and no leg of either meets one of the other
            if not _apart(back, top):
                return False
            if any(_inside((dx + lx, dy + ly), me, 0.03) for lx, ly in LEGS):
                return False
        elif not _apart(me, top):
            return False
    for k, (ox, oy, oa) in chairs.items():
        if k != key and not _apart(me, _corners(ox, oy, oa, *CHAIR_BOX)):
            return False
    return True


def settle_chairs(desks, fixed=()):
    """Moves each chair that stands in something by the least it takes, trying first to straighten it, then to slide it.
    Chairs whose key is in fixed are obstacles only. Returns the keys of chairs that were moved."""
    desks_xy = {k: _desk_xy(d) for k, (d, c) in desks.items()}
    chairs = {k: (c.location.x, c.location.y, c.rotation_euler.z) for k, (d, c) in desks.items()}
    moved = []
    steps = [i * 0.03 for i in range(-8, 9)]
    for _ in range(3):
        for k, (d, c) in desks.items():
            if k in fixed:
                continue
            cx, cy, ang = chairs[k]
            if chair_ok(k, cx, cy, ang, desks_xy, chairs):
                continue
            best = None
            for f in (1.0, 0.5, 0.0):
                for sx in steps:
                    for sy in steps:
                        cost = math.hypot(sx, sy) + abs(ang) * (1 - f) * 0.4
                        if best is not None and cost >= best[0]:
                            continue
                        if chair_ok(k, cx + sx, cy + sy, ang * f, desks_xy, chairs):
                            best = (cost, cx + sx, cy + sy, ang * f)
            if best is None:
                raise RuntimeError(f"no clear place for the chair of desk {k}")
            chairs[k] = best[1:]
            c.location.x, c.location.y = best[1], best[2]
            c.rotation_euler.z = best[3]
            moved.append(k)
    return moved



def newspaper(page_c, w, h, angle, top_mat, under_mat):
    """A folded newspaper lying on a desk: a fold across the middle, corners that lift, a sheet under it showing."""
    import numpy as np
    def sheet(name, sx, sy, dz, lift, mat_, off=(0.0, 0.0), rot=0.0):
        nx, ny = 40, 28
        verts, faces = [], []
        for j in range(ny + 1):
            for i in range(nx + 1):
                u, v = i / nx * 2 - 1, j / ny * 2 - 1
                z = dz
                # the fold: a soft ridge along the middle, as a folded paper never lies quite flat
                z += lift * 0.75 * np.exp(-(v / 0.10) ** 2)
                # one long edge bows up; two corners curl
                z += lift * 0.9 * max(0.0, abs(v) - 0.72) ** 2 * 11
                z += lift * 2.2 * max(0.0, (u + v) / 2 - 0.62) ** 2 * 9
                z += lift * 1.6 * max(0.0, (-u + v) / 2 - 0.70) ** 2 * 9
                verts.append((u * sx / 2, v * sy / 2, float(z)))
        for j in range(ny):
            for i in range(nx):
                a = j * (nx + 1) + i
                faces.append((a, a + 1, a + nx + 2, a + nx + 1))
        me = bpy.data.meshes.new(name)
        me.from_pydata(verts, [], faces)
        me.update()
        for p in me.polygons:
            p.use_smooth = True
        return kit._link(name, me, (page_c[0] + off[0], page_c[1] + off[1], page_c[2]), (0, 0, angle + rot), mat_)
    under = sheet("page_under", w * 1.006, h * 1.012, 0.0005, 0.006, under_mat, off=(0.006, -0.004), rot=0.012)
    top = sheet("page", w, h, 0.0030, 0.011, top_mat)
    return top, under
