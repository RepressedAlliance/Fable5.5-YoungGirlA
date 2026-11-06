"""Her dark bedroom, seen from the floor. One real lamp stands low in the corridor, so light only comes in under the door.

Blender writes data passes; src/npr/paint_room.py paints them. args: OUTDIR t1 t2 ... or OUTDIR todo FILE.json
"""
import json
import math
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import bmesh  # noqa: E402
import bpy  # noqa: E402
from mathutils import Euler, Matrix, Vector  # noqa: E402
import kit  # noqa: E402
import shared_room as S  # noqa: E402

ROOT = kit.ROOT


class Parts:
    """Many boxes and prisms in one mesh, one ink id. Vertices are relative to `pivot`, so moving things turn around the right point."""

    def __init__(self, name, mats, pivot=(0, 0, 0)):
        self.name = name
        self.mats = mats
        self.pivot = Vector(pivot)
        self.bm = bmesh.new()

    def box(self, c, size, m=0, rot=(0, 0, 0)):
        made = bmesh.ops.create_cube(self.bm, size=1.0)["verts"]
        mw = Matrix.Translation(Vector(c) - self.pivot) @ Euler(rot).to_matrix().to_4x4() @ Matrix.Diagonal((*size, 1))
        for v in made:
            v.co = mw @ v.co
        for f in {f for v in made for f in v.link_faces}:
            f.material_index = m
        return self

    def lohi(self, lo, hi, m=0):
        return self.box([(a + b) / 2 for a, b in zip(lo, hi)], [abs(b - a) for a, b in zip(lo, hi)], m)

    def cyl(self, p0, p1, r, m=0, seg=10):
        p0, p1 = Vector(p0), Vector(p1)
        d = p1 - p0
        made = bmesh.ops.create_cone(self.bm, cap_ends=True, segments=seg, radius1=r, radius2=r, depth=d.length)["verts"]
        q = d.to_track_quat("Z", "Y").to_matrix().to_4x4()
        mw = Matrix.Translation((p0 + p1) / 2 - self.pivot) @ q
        for v in made:
            v.co = mw @ v.co
        for f in {f for v in made for f in v.link_faces}:
            f.material_index = m
        return self

    def prism(self, pts, y0, y1, m=0):
        """Polygon in the x-z plane, extruded from y0 to y1."""
        a = [self.bm.verts.new(Vector((x, y0, z)) - self.pivot) for x, z in pts]
        b = [self.bm.verts.new(Vector((x, y1, z)) - self.pivot) for x, z in pts]
        faces = [self.bm.faces.new(a), self.bm.faces.new(list(reversed(b)))]
        n = len(pts)
        for i in range(n):
            faces.append(self.bm.faces.new((a[(i + 1) % n], a[i], b[i], b[(i + 1) % n])))
        for f in faces:
            f.material_index = m
        return self

    def slab(self, pts, z0, z1, m=0):
        """Polygon in the x-y plane, extruded from z0 to z1 (a piece of folded cloth, a futon)."""
        a = [self.bm.verts.new(Vector((x, y, z0)) - self.pivot) for x, y in pts]
        b = [self.bm.verts.new(Vector((x, y, z1)) - self.pivot) for x, y in pts]
        faces = [self.bm.faces.new(list(reversed(a))), self.bm.faces.new(b)]
        n = len(pts)
        for i in range(n):
            faces.append(self.bm.faces.new((a[i], a[(i + 1) % n], b[(i + 1) % n], b[i])))
        for f in faces:
            f.material_index = m
        return self

    def make(self, parent=None, uid=None):
        bmesh.ops.recalc_face_normals(self.bm, faces=self.bm.faces)
        me = bpy.data.meshes.new(self.name)
        self.bm.to_mesh(me)
        self.bm.free()
        for mt in self.mats:
            me.materials.append(mt)
        loc = self.pivot
        ob = kit._link(self.name, me, tuple(loc), (0, 0, 0), None, parent, uid)
        return ob


def loft(parts, rings, m=0):
    made = [[parts.bm.verts.new(Vector(p)) for p in ring] for ring in rings]
    for a_, b_ in zip(made, made[1:]):
        for k in range(len(a_)):
            f = parts.bm.faces.new((a_[k], a_[(k + 1) % len(a_)], b_[(k + 1) % len(a_)], b_[k]))
            f.material_index = m
    for ring in (made[0], made[-1]):
        f = parts.bm.faces.new(ring)
        f.material_index = m


def shoe(parts, length, side, m_upper, m_sole, m_strap, m_seam):
    """A penny loafer, heel at the origin, toe towards -y, on the floor: sole with its heel block, moccasin toe with a stitched apron, saddle strap with its slot."""
    sh = S.loafer(length, side)
    loft(parts, sh["upper"], m_upper)
    loft(parts, sh["sole"], m_sole)
    loft(parts, sh["strap"], m_strap)
    for a_, b_ in zip(sh["seam"], sh["seam"][1:]):
        parts.cyl(a_, b_, 0.0017, m_seam, 6)
    x, y, z = sh["slot"]
    parts.lohi((x - 0.012, y - 0.0055, z - 0.002), (x + 0.012, y + 0.0055, z + 0.0012), m_seam)
    return parts


def blob(cx, cy, rx, ry, seed, n=14, wob=0.16):
    r = random.Random(seed)
    out = []
    for i in range(n):
        a = i / n * math.tau
        k = 1 + r.uniform(-wob, wob)
        out.append((cx + math.cos(a) * rx * k, cy + math.sin(a) * ry * k))
    return out


def cloth(name, mats, cx, cy, rx, ry, h, seed, z0=0.0, m=0, rings=10, segs=40, fk=(3.0, 6.0)):
    """A dropped piece of cloth as a height field: soft outline, a low mound, a few sharp folds that ink will find."""
    r = random.Random(seed)
    a1, a2, a3 = r.uniform(0, 6), r.uniform(0, 6), r.uniform(0, 6)
    folds = [(r.uniform(0, math.tau), r.uniform(*fk), r.uniform(0, 6)) for _ in range(3)]

    def edge(th):
        return 1 + 0.17 * math.sin(2 * th + a1) + 0.09 * math.sin(3 * th + a2) + 0.05 * math.sin(5 * th + a3)

    verts = [(cx, cy, 0)]
    for i in range(1, rings + 1):
        rho = i / rings
        for j in range(segs):
            th = j / segs * math.tau
            e = edge(th)
            u, v = rho * e * math.cos(th), rho * e * math.sin(th)
            z = (1 - rho ** 2.6) ** 0.6
            f = 0.0
            for fa, fk, fp in folds:
                f += abs(math.sin(fk * (u * math.cos(fa) + v * math.sin(fa)) + fp)) - 0.6
            z = z * (0.82 + 0.34 * f / 3)
            verts.append((cx + rx * u, cy + ry * v, z0 + h * max(z, 0)))
    verts[0] = (cx, cy, z0 + h * 0.9)
    faces = []
    for j in range(segs):
        faces.append((0, 1 + j, 1 + (j + 1) % segs))
    for i in range(rings - 1):
        for j in range(segs):
            a = 1 + i * segs + j
            b = 1 + i * segs + (j + 1) % segs
            faces.append((a, a + segs, b + segs, b))
    # the rim comes down to the surface
    n0 = len(verts)
    for j in range(segs):
        x, y, _ = verts[1 + (rings - 1) * segs + j]
        verts.append((x, y, z0))
    for j in range(segs):
        a = 1 + (rings - 1) * segs + j
        b = 1 + (rings - 1) * segs + (j + 1) % segs
        faces.append((a, n0 + j, n0 + (j + 1) % segs, b))
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], faces)
    me.update()
    me.materials.append(mats[m])
    return kit._link(name, me)


def strip(parts, path, w0, w1, z0, z1, m=0):
    """A flat sleeve or strap: polygon following a path, with its width going from w0 to w1."""
    left, right = [], []
    n = len(path)
    for i, (x, y) in enumerate(path):
        ax, ay = path[max(i - 1, 0)]
        bx, by = path[min(i + 1, n - 1)]
        dx, dy = bx - ax, by - ay
        L_ = math.hypot(dx, dy) or 1
        w = (w0 + (w1 - w0) * i / (n - 1)) / 2
        left.append((x - dy / L_ * w, y + dx / L_ * w))
        right.append((x + dy / L_ * w, y - dx / L_ * w))
    parts.slab(left + right[::-1], z0, z1, m)


def tube(name, mats, path, w0, w1, h, m=0, cuff=None):
    """A limp sleeve: a flattened tube lying on the floor along a smooth path. `cuff`: material of the last stretch."""
    n = len(path)
    pts = []
    for i in range(n - 1):
        p0, p1 = path[max(i - 1, 0)], path[i]
        p2, p3 = path[i + 1], path[min(i + 2, n - 1)]
        for k in range(6):
            u = k / 6
            pts.append(tuple(0.5 * ((2 * b) + (c - a) * u + (2 * a - 5 * b + 4 * c - d) * u * u + (3 * b - a - 3 * c + d) * u ** 3)
                             for a, b, c, d in zip(p0, p1, p2, p3)))
    pts.append(path[-1])
    segs = 10
    verts, faces, fm = [], [], []
    N = len(pts)
    for i, (x, y) in enumerate(pts):
        ax, ay = pts[max(i - 1, 0)]
        bx, by = pts[min(i + 1, N - 1)]
        dx, dy = bx - ax, by - ay
        L_ = math.hypot(dx, dy) or 1
        nx, ny = -dy / L_, dx / L_
        w = (w0 + (w1 - w0) * i / (N - 1)) / 2
        for j in range(segs):
            a = j / segs * math.tau
            verts.append((x + nx * w * math.cos(a), y + ny * w * math.cos(a), h * (0.5 + 0.5 * math.sin(a)) ** 0.7))
    for i in range(N - 1):
        for j in range(segs):
            a = i * segs + j
            b = i * segs + (j + 1) % segs
            faces.append((a, b, b + segs, a + segs))
            fm.append(1 if (cuff is not None and i >= N - 4) else 0)
    faces.append(tuple(range(segs)))
    fm.append(0)
    faces.append(tuple((N - 1) * segs + j for j in range(segs)))
    fm.append(1 if cuff is not None else 0)
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], faces)
    me.update()
    me.materials.append(mats[m])
    if cuff is not None:
        me.materials.append(mats[cuff])
    for poly, k in zip(me.polygons, fm):
        poly.material_index = k
    return kit._link(name, me)


def catmull(path, k=6):
    out = []
    n = len(path)
    for i in range(n - 1):
        p0, p1 = path[max(i - 1, 0)], path[i]
        p2, p3 = path[i + 1], path[min(i + 2, n - 1)]
        for q in range(k):
            u = q / k
            out.append(tuple(0.5 * ((2 * b) + (c - a) * u + (2 * a - 5 * b + 4 * c - d) * u * u + (3 * b - a - 3 * c + d) * u ** 3)
                             for a, b, c, d in zip(p0, p1, p2, p3)))
    out.append(path[-1])
    return out


SHADOW_DIR = (1.1, -0.45)   # how far a shadow falls on the floor per metre of height, away from the window


def hull(pts):
    pts = sorted(set(pts))

    def half(seq):
        out = []
        for p in seq:
            while len(out) >= 2 and (out[-1][0] - out[-2][0]) * (p[1] - out[-2][1]) - (out[-1][1] - out[-2][1]) * (p[0] - out[-2][0]) <= 0:
                out.pop()
            out.append(p)
        return out

    a, b = half(pts), half(pts[::-1])
    return a[:-1] + b[:-1]


def floor_shadow(card, foot, h, z=0.0009):
    """Hard shadow on the floor: the footprint swept along the shadow direction."""
    moved = [(x + SHADOW_DIR[0] * h, y + SHADOW_DIR[1] * h) for x, y in foot]
    v = [card.bm.verts.new((x, y, z)) for x, y in hull(list(foot) + moved)]
    card.bm.faces.new(v)


def rect_pts(x0, y0, x1, y1):
    return [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]


def build(with_sheets):
    sc = kit.reset()
    kit.setup_render(sc, 1920, 1080, ss=S.SS, fps=60, samples=3, threads=12)
    sc.render.use_persistent_data = True
    M = {
        "floor": kit.mat("floor", "#8A6B4E"),
        "wall": kit.mat("wall", "#ABA99F"),
        "trim": kit.mat("trim", "#EFECE2"),
        "door": kit.mat("door", "#D9D3C4"),
        "metal": kit.mat("metal", "#8D8F96"),
        "dark": kit.mat("darkthing", "#2A2C36"),
        "wood": kit.mat("wood", "#A58760"),
        "woodd": kit.mat("woodd", "#6E563E"),
        "pale": kit.mat("pale", "#EDE7D3"),
        "curtain": kit.mat("curtain", "#8F97A8"),
        "curtain2": kit.mat("curtain2", "#79818F"),
        "window": kit.mat("window", "#A8BCE0", kind=1),
        "futon": kit.mat("futon", "#D8D5CC"),
        "blanket": kit.mat("blanket", "#7D86A0"),
        "hood": kit.mat("hood", "#5E6A86"),
        "hood2": kit.mat("hood2", "#48516A"),
        "skirt": kit.mat("skirtcloth", "#343748"),
        "red": kit.mat("redthing", "#B23A3F"),
        "tie": kit.mat("tie", "#E9C33A"),
        "bag": kit.mat("bag", "#3A3E50"),
        "bottle": kit.mat("bottle", "#9BB7CC"),
        "cap": kit.mat("cap", "#E2E2DA"),
        "b0": kit.mat("b0", "#7A4048"),
        "b1": kit.mat("b1", "#3F5F7F"),
        "b2": kit.mat("b2", "#B7A36E"),
        "b3": kit.mat("b3", "#4B6B55"),
        "b4": kit.mat("b4", "#C8C2B4"),
        "b5": kit.mat("b5", "#5C5470"),
        "sh_floor": kit.mat("sh_floor", "#8A6B4E", kind=6),
        "sh_wall": kit.mat("sh_wall", "#ABA99F", kind=6),
    }
    ids = {}
    bk = [M["b0"], M["b1"], M["b2"], M["b3"], M["b4"], M["b5"]]

    # ---- shell ----
    floor = Parts("floor", [M["floor"]])
    floor.lohi((-1.7, -3.8, -0.06), (1.8, 1.6, 0.0))
    ids["floor"] = floor.make().pass_index
    xl, xr = S.XD - S.DW / 2, S.XD + S.DW / 2
    wall = Parts("walls", [M["wall"]])
    wall.lohi((S.X0, 0, 0), (xl, 0.12, S.HT))                       # door wall, left of the door
    wall.lohi((xr, 0, 0), (S.X1, 0.12, S.HT))                       # right of the door
    wall.lohi((xl, 0, S.DOOR_H), (xr, 0.12, S.HT))                  # above the door
    ids["wall_door"] = wall.make().pass_index
    cards = Parts("cards", [M["sh_floor"]])
    side_l = Parts("wall_l", [M["wall"]]).lohi((S.X0 - 0.1, S.YBACK, 0), (S.X0, 0.12, S.HT)).make()
    side_r = Parts("wall_r", [M["wall"]]).lohi((S.X1, S.YBACK, 0), (S.X1 + 0.1, 0.12, S.HT)).make()
    Parts("wall_b", [M["wall"]]).lohi((S.X0, S.YBACK - 0.1, 0), (S.X1, S.YBACK, S.HT)).make()
    Parts("ceiling", [M["trim"]]).lohi((S.X0 - 0.1, S.YBACK - 0.1, S.HT), (S.X1 + 0.1, 0.12, S.HT + 0.1)).make()
    # corridor: walls close it so the light has nowhere else to go, and nothing else is out there
    Parts("corr", [M["wall"]]).lohi((-1.7, 1.5, 0), (1.8, 1.6, S.HT)).make()
    ids["corr_skirt"] = Parts("corr_skirt", [M["woodd"]]).lohi((-1.7, 1.49, 0), (1.8, 1.5, 0.07)).make().pass_index
    # skirting board along the three visible walls, stopping at the door casing
    sk = Parts("skirting", [M["trim"]])
    sk.lohi((S.X0, -0.014, 0), (xl - 0.07, 0, 0.075))
    sk.lohi((xr + 0.07, -0.014, 0), (S.X1, 0, 0.075))
    sk.lohi((S.X0, S.YBACK, 0), (S.X0 + 0.014, 0, 0.075))
    sk.lohi((S.X1 - 0.014, S.YBACK, 0), (S.X1, 0, 0.075))
    sk.make()

    # ---- door frame and casing ----
    cas = Parts("casing", [M["trim"]])
    cas.lohi((xl - 0.07, -0.016, 0), (xl, 0.0, S.DOOR_H + 0.07))
    cas.lohi((xr, -0.016, 0), (xr + 0.07, 0.0, S.DOOR_H + 0.07))
    cas.lohi((xl, -0.016, S.DOOR_H), (xr, 0.0, S.DOOR_H + 0.07))
    cas.lohi((xl, 0, 0), (xl + 0.015, 0.12, S.DOOR_H))              # jambs inside the opening
    cas.lohi((xr - 0.015, 0, 0), (xr, 0.12, S.DOOR_H))
    cas.lohi((xl, 0, S.DOOR_H - 0.015), (xr, 0.12, S.DOOR_H))
    # door stops: no light gets round the sides or over the top, only under it
    cas.lohi((xl, S.DOOR_T, S.GAP + 0.002), (xl + 0.03, S.DOOR_T + 0.014, S.DOOR_H))
    cas.lohi((xr - 0.03, S.DOOR_T, S.GAP + 0.002), (xr, S.DOOR_T + 0.014, S.DOOR_H))
    cas.lohi((xl, S.DOOR_T, S.DOOR_H - 0.03), (xr, S.DOOR_T + 0.014, S.DOOR_H))
    ids["casing"] = cas.make().pass_index

    # ---- door: the hinge line is its origin, so a knock turns it about the hinges ----
    hx, hy = S.HINGE
    dx1 = xr - 0.015 - 0.003
    door = Parts("door", [M["door"], M["trim"], M["metal"]], pivot=(hx, hy, 0))
    door.lohi((hx + 0.002, 0.0, S.GAP), (dx1, S.DOOR_T, S.DOOR_H - 0.018))
    # two raised panels, the way a cheap interior door has them
    for z0, z1 in ((0.20, 0.92), (1.10, 1.82)):
        a, b = hx + 0.12, dx1 - 0.12
        t = 0.014
        door.lohi((a, -0.006, z0), (b, 0.0, z0 + t), 1)
        door.lohi((a, -0.006, z1 - t), (b, 0.0, z1), 1)
        door.lohi((a, -0.006, z0), (a + t, 0.0, z1), 1)
        door.lohi((b - t, -0.006, z0), (b, 0.0, z1), 1)
    d_ob = door.make()
    ids["door"] = d_ob.pass_index
    # hinges stay on the frame side
    hin = Parts("hinges", [M["metal"]])
    for z in (0.28, 1.0, 1.72):
        hin.lohi((hx - 0.016, -0.009, z - 0.05), (hx + 0.016, 0.0, z + 0.05))
        hin.cyl((hx, -0.011, z - 0.05), (hx, -0.011, z + 0.05), 0.0055, 0, 6)
    hin.make()
    # the lever is on the door, and turns about its own spindle
    lx, lz = S.LEVER
    lev = Parts("lever", [M["metal"]], pivot=(0, 0, 0))
    lev.cyl((0, 0.0, 0), (0, -0.046, 0), 0.0095, 0, 16)
    # the handle: a round bar going back towards the hinge, its end turned slightly to the door
    pts = [(0.008, -0.046, 0.0), (-0.03, -0.054, 0.0), (-0.085, -0.054, 0.0), (-0.112, -0.047, 0.0), (-0.122, -0.038, 0.0)]
    for a_, b_ in zip(pts, pts[1:]):
        lev.cyl(a_, b_, 0.0085, 0, 12)
    lev_ob = lev.make(parent=d_ob)
    lev_ob.location = (lx - hx, -hy, lz)
    ids["lever"] = lev_ob.pass_index
    rose = Parts("rose", [M["metal"], M["dark"]], pivot=(hx, hy, 0))
    rose.cyl((lx, 0.0, lz), (lx, -0.008, lz), 0.03, 0, 24)
    for a_ in (0.0, math.pi):
        rose.cyl((lx + 0.021 * math.cos(a_), -0.008, lz + 0.021 * math.sin(a_)), (lx + 0.021 * math.cos(a_), -0.0092, lz + 0.021 * math.sin(a_)), 0.0028, 1, 8)
    rose.cyl((lx, 0.0, lz - 0.115), (lx, -0.007, lz - 0.115), 0.024, 0, 20)     # the lock
    rose.lohi((lx - 0.005, -0.021, lz - 0.115 - 0.018), (lx + 0.005, -0.007, lz - 0.115 + 0.018), 1)   # thumb turn
    rose_ob = rose.make(parent=None)
    rose_ob.parent = d_ob
    rose_ob.location = (0, 0, 0)
    ids["rose"] = rose_ob.pass_index

    # ---- the lamp ----
    ld = bpy.data.lights.new("lamp", "POINT")
    ld.energy = 60.0
    ld.shadow_soft_size = 0.0
    ld.color = (1, 1, 1)
    lp = bpy.data.objects.new("lamp", ld)
    sc.collection.objects.link(lp)
    lp.location = S.LIGHT

    # ---- feet in the corridor: seen only through the gap, from the floor. Their shadow in the room is painted, from S.foot_shadows ----
    feet = []
    for i in range(2):
        f = Parts(f"foot{i}", [kit.mat("loafer", "#6A3F24"), kit.mat("loafer_sole", "#1A1411"), kit.mat("loafer_strap", "#54301B"), kit.mat("loafer_seam", "#1E110B", kind=7), kit.mat("sock", "#20243A")])
        shoe(f, S.SHOE_LEN, 1 if i else -1, 0, 1, 2, 3)
        f.cyl((0, -0.058, 0.045), (0, -0.054, 0.30), 0.034, 4, 16)     # ankle
        f.cyl((0, -0.054, 0.30), (0, -0.05, 0.9), 0.045, 4, 16)        # calf
        ob = f.make()
        ob.visible_shadow = False
        # leather is round: the terminator of the lamp behind should be one clean curve, not a staircase of facets. The sole keeps its hard edges.
        for poly in ob.data.polygons:
            poly.use_smooth = poly.material_index in (0, 2, 3, 4)
        ids[f"foot{i}"] = ob.pass_index
        feet.append(ob)

    # ---- left wall: window behind closed curtains, one thin slit where they do not quite meet ----
    win_y0, win_y1 = -1.45, -0.20
    slit = -0.62
    Parts("window", [M["window"]]).lohi((S.X0 - 0.004, win_y0, 0.78), (S.X0 + 0.001, win_y1, 2.12)).make()
    for name, y0, y1, n, m in (("curtain_a", win_y0 - 0.12, slit - 0.011, 9, M["curtain"]), ("curtain_b", slit + 0.011, win_y1 + 0.08, 5, M["curtain2"])):
        me = bpy.data.meshes.new(name)
        verts, faces = [], []
        steps = n * 8
        for i in range(steps + 1):
            y = y0 + (y1 - y0) * i / steps
            x = S.X0 + 0.065 + 0.022 * math.sin(i / 8 * math.tau)
            verts += [(x, y, 0.035), (x, y, 2.16)]
            if i:
                k = (i - 1) * 2
                faces.append((k, k + 2, k + 3, k + 1))
        me.from_pydata(verts, [], faces)
        me.update()
        me.materials.append(m)
        ids[name] = kit._link(name, me).pass_index
    rail = Parts("rail", [M["metal"]])
    rail.cyl((S.X0 + 0.065, win_y0 - 0.2, 2.18), (S.X0 + 0.065, win_y1 + 0.16, 2.18), 0.012)
    for y in (win_y0 - 0.12, win_y1 + 0.1):
        rail.lohi((S.X0, y - 0.01, 2.17), (S.X0 + 0.07, y + 0.01, 2.19))
    rail.make()

    # ---- door wall: light switch, outlet, poster, calendar, her uniform on a hook ----
    pl = Parts("plates", [M["trim"], M["dark"]])
    pl.lohi((xr + 0.10, -0.008, 0.98), (xr + 0.18, 0, 1.10))
    pl.lohi((xr + 0.122, -0.013, 1.012), (xr + 0.158, -0.008, 1.068), 1)     # the rocker of the light switch
    pl.lohi((-0.66, -0.008, 0.20), (-0.56, 0, 0.32))
    pl.make()
    charger = Parts("charger", [M["pale"], M["dark"]])
    charger.lohi((-0.635, -0.038, 0.235), (-0.585, -0.008, 0.285))
    # the cable leaves the charger, drops to the floor, and wanders to the phone
    route = [(-0.61, -0.038, 0.255), (-0.61, -0.055, 0.17), (-0.615, -0.07, 0.004), (-0.80, -0.27, 0.004), (-0.87, -0.52, 0.004),
             (-0.92, -0.80, 0.004), (-0.80, -1.02, 0.004), (-0.70, -1.17, 0.004)]
    floor_run = catmull(route[2:], 6)
    for a, b in zip(route[:3], route[1:3]):
        charger.cyl(a, b, 0.0034, 1, 5)
    for a, b in zip(floor_run, floor_run[1:]):
        charger.cyl(a, b, 0.0034, 1, 5)
    charger.make()
    poster = kit.plane("poster", (-0.95, -0.003, 1.55), 0.56, 0.78, kit.mat("poster", "#B9B4A8"), rot=(math.pi / 2, 0, 0))
    ids["poster"] = poster.pass_index
    # calendar hangs from two pins; when one lets go it turns about the other
    cal_pin = (-0.565, -0.006, 1.70)
    cal = Parts("calendar", [M["pale"]], pivot=cal_pin)
    cal.lohi((cal_pin[0] - 0.012, -0.006, cal_pin[2] - 0.40), (cal_pin[0] + 0.25, -0.003, cal_pin[2] + 0.012))
    cal_ob = cal.make()
    ids["calendar"] = cal_ob.pass_index
    pins = Parts("pins", [M["red"]])
    pins.cyl((cal_pin[0], 0, cal_pin[2]), (cal_pin[0], -0.012, cal_pin[2]), 0.006, 0, 6)
    pins.cyl((cal_pin[0] + 0.238, 0, cal_pin[2]), (cal_pin[0] + 0.238, -0.012, cal_pin[2]), 0.006, 0, 6)   # stays in the wall when the paper tears off it
    pins.make()

    # uniform: hook on the wall, hanger, sailor blouse with collar and tie, skirt over the bar. All swings about the hook.
    hook = (xr + 0.44, -0.03, 1.86)
    hk = Parts("hook", [M["metal"]])
    hk.lohi((hook[0] - 0.02, -0.006, hook[2] - 0.035), (hook[0] + 0.02, 0, hook[2] + 0.015))
    hk.cyl((hook[0], 0, hook[2] - 0.012), (hook[0], -0.042, hook[2] - 0.012), 0.005, 0, 6)
    hk.make()
    uni = Parts("uniform", [M["pale"], M["dark"], M["tie"], M["woodd"], M["skirt"]], pivot=hook)
    y = hook[1]
    hx0, hz = hook[0], hook[2]
    # blouse
    uni.prism([(hx0 - 0.20, hz - 0.08), (hx0 - 0.30, hz - 0.14), (hx0 - 0.33, hz - 0.46), (hx0 - 0.235, hz - 0.47), (hx0 - 0.205, hz - 0.30),
               (hx0 - 0.195, hz - 0.68), (hx0 + 0.195, hz - 0.68), (hx0 + 0.205, hz - 0.30), (hx0 + 0.235, hz - 0.47), (hx0 + 0.33, hz - 0.46),
               (hx0 + 0.30, hz - 0.14), (hx0 + 0.20, hz - 0.08), (hx0 + 0.04, hz - 0.055), (hx0 - 0.04, hz - 0.055)], y - 0.012, y + 0.002, 0)
    # collar: a dark V-shaped flap
    uni.prism([(hx0 - 0.145, hz - 0.075), (hx0 - 0.20, hz - 0.20), (hx0, hz - 0.34), (hx0 + 0.20, hz - 0.20), (hx0 + 0.145, hz - 0.075),
               (hx0 + 0.04, hz - 0.055), (hx0, hz - 0.14), (hx0 - 0.04, hz - 0.055)], y - 0.018, y - 0.0105, 1)
    uni.prism([(hx0 - 0.03, hz - 0.30), (hx0 + 0.03, hz - 0.30), (hx0 + 0.045, hz - 0.45), (hx0, hz - 0.42), (hx0 - 0.045, hz - 0.45)], y - 0.024, y - 0.0165, 2)
    # sleeve cuffs
    uni.prism([(hx0 - 0.33, hz - 0.42), (hx0 - 0.235, hz - 0.43), (hx0 - 0.235, hz - 0.47), (hx0 - 0.33, hz - 0.46)], y - 0.018, y - 0.0105, 1)
    uni.prism([(hx0 + 0.33, hz - 0.42), (hx0 + 0.235, hz - 0.43), (hx0 + 0.235, hz - 0.47), (hx0 + 0.33, hz - 0.46)], y - 0.018, y - 0.0105, 1)
    # hanger wire and wooden shoulders
    uni.cyl((hx0, y - 0.0, hz - 0.012), (hx0, y - 0.0, hz - 0.055), 0.0035, 3, 5)
    uni.prism([(hx0 - 0.21, hz - 0.095), (hx0, hz - 0.05), (hx0 + 0.21, hz - 0.095), (hx0 + 0.21, hz - 0.115), (hx0, hz - 0.07), (hx0 - 0.21, hz - 0.115)], y - 0.004, y + 0.004, 3)
    # a blouse on a hanger hangs in folds: a few hard ink lines, drawn as the thinnest raised strips, so that it is cloth and not a card
    for pts_ in (((hx0 - 0.12, hz - 0.36), (hx0 - 0.145, hz - 0.50), (hx0 - 0.115, hz - 0.66)), ((hx0 + 0.13, hz - 0.33), (hx0 + 0.105, hz - 0.46), (hx0 + 0.14, hz - 0.64)),
                 ((hx0 - 0.03, hz - 0.50), (hx0 - 0.015, hz - 0.67)), ((hx0 - 0.285, hz - 0.20), (hx0 - 0.265, hz - 0.40)), ((hx0 + 0.285, hz - 0.20), (hx0 + 0.27, hz - 0.38))):
        for a_, b_ in zip(pts_, pts_[1:]):
            uni.cyl((a_[0], y - 0.0125, a_[1]), (b_[0], y - 0.0125, b_[1]), 0.0014, 1, 5)
    uni_ob = uni.make()
    ids["uniform"] = uni_ob.pass_index
    us = Parts("uniform_shadow", [M["sh_wall"]], pivot=hook)
    ox, oz = 0.04, -0.03
    pts = [(hx0 - 0.20 + ox, hz - 0.08 + oz), (hx0 - 0.30 + ox, hz - 0.14 + oz), (hx0 - 0.33 + ox, hz - 0.46 + oz), (hx0 - 0.235 + ox, hz - 0.47 + oz), (hx0 - 0.205 + ox, hz - 0.30 + oz),
           (hx0 - 0.195 + ox, hz - 0.68 + oz), (hx0 + 0.195 + ox, hz - 0.68 + oz), (hx0 + 0.205 + ox, hz - 0.30 + oz), (hx0 + 0.235 + ox, hz - 0.47 + oz), (hx0 + 0.33 + ox, hz - 0.46 + oz),
           (hx0 + 0.30 + ox, hz - 0.14 + oz), (hx0 + 0.20 + ox, hz - 0.08 + oz)]
    us.bm.faces.new([us.bm.verts.new(Vector((x, -0.001, z)) - us.pivot) for x, z in pts])
    us_ob = us.make()

    # ---- right wall: low bookshelf ----
    shelf_x0, shelf_x1 = S.X1 - 0.27, S.X1
    shelf_y0, shelf_y1 = -1.05, -0.28
    sh = Parts("shelf", [M["wood"], M["woodd"]])
    th = 0.018
    sh.lohi((shelf_x0, shelf_y0, 0), (shelf_x1, shelf_y0 + th, 0.96))
    sh.lohi((shelf_x0, shelf_y1 - th, 0), (shelf_x1, shelf_y1, 0.96))
    for z in (0.03, 0.34, 0.65, 0.945):
        sh.lohi((shelf_x0, shelf_y0, z), (shelf_x1, shelf_y1, z + th))
    sh.lohi((shelf_x1 - 0.01, shelf_y0, 0), (shelf_x1, shelf_y1, 0.96), 1)
    sh.make()
    floor_shadow(cards, rect_pts(shelf_x0, shelf_y0, shelf_x1, shelf_y1), 0.96)
    books = Parts("books", bk + [M["pale"]])
    r = random.Random(11)
    tip_book = None
    for z, fill in ((0.048, 0.96), (0.358, 0.82), (0.668, 0.60)):
        y = shelf_y0 + th + 0.004
        end = shelf_y0 + th + (shelf_y1 - shelf_y0 - 2 * th) * fill
        while y < end:
            w = r.uniform(0.016, 0.042)
            h = r.uniform(0.17, 0.265)
            dp = r.uniform(0.15, 0.20)
            books.lohi((shelf_x0 + 0.03, y, z), (shelf_x0 + 0.03 + dp, y + w, z + h), r.randrange(6))
            y += w + 0.0015
        if z > 0.6:
            tip_book = (shelf_x0 + 0.03, y + 0.003, z)
    books.make()
    # the last book on the top row stands free; a knock tips it over against the shelf side.
    tb = Parts("tip_book", [bk[0]], pivot=(tip_book[0], tip_book[1], tip_book[2]))
    tb.lohi((tip_book[0], tip_book[1], tip_book[2]), (tip_book[0] + 0.18, tip_book[1] + 0.03, tip_book[2] + 0.24))
    tb_ob = tb.make()
    # on the shelf top: a clock lying where it was left, and a box
    top = Parts("shelf_top", [M["dark"], M["pale"], M["b4"]])
    top.cyl((S.X1 - 0.14, -0.60, 0.963 + 0.0), (S.X1 - 0.14, -0.60, 0.963 + 0.03), 0.06, 0, 16)
    top.lohi((S.X1 - 0.20, -0.95, 0.963), (S.X1 - 0.04, -0.75, 1.05), 2)
    top.make()

    # ---- on the floor ----
    # stack of textbooks at the right edge of the wedge; the top one slides
    stack = Parts("stack", bk[:2] + [M["pale"], bk[3]])
    sx, sy = 0.90, -0.62
    z = 0.0
    r2 = random.Random(3)
    for i, (w, d, h, m) in enumerate(((0.27, 0.36, 0.034, 0), (0.25, 0.34, 0.028, 1), (0.24, 0.33, 0.04, 3), (0.25, 0.31, 0.024, 0))):
        rz = r2.uniform(-0.09, 0.09)
        stack.box((sx + r2.uniform(-0.012, 0.012), sy + r2.uniform(-0.012, 0.012), z + h / 2), (w, d, h - 0.012), 2, (0, 0, rz))
        stack.box((sx, sy, z + 0.003), (w + 0.006, d + 0.006, 0.006), m, (0, 0, rz))
        stack.box((sx, sy, z + h - 0.003), (w + 0.006, d + 0.006, 0.006), m, (0, 0, rz))
        z += h
    stack.make()
    floor_shadow(cards, rect_pts(sx - 0.14, sy - 0.18, sx + 0.14, sy + 0.18), 0.13)
    stack_top = z
    top_book = Parts("top_book", [bk[1], M["pale"]], pivot=(sx, sy, stack_top))
    top_book.box((sx, sy, stack_top + 0.014), (0.21, 0.29, 0.022), 1, (0, 0, 0.1))
    top_book.box((sx, sy, stack_top + 0.0025), (0.216, 0.296, 0.005), 0, (0, 0, 0.1))
    top_book.box((sx, sy, stack_top + 0.0255), (0.216, 0.296, 0.005), 0, (0, 0, 0.1))
    tb2 = top_book.make()

    # a hoodie dropped on the floor, left of the wedge: body in a heap, hood, limp sleeves flung out
    hm = [M["hood"], M["hood2"], M["dark"]]
    cloth("hoodie", hm, -0.47, -0.60, 0.23, 0.16, 0.075, 5, fk=(2.2, 4.5))
    cloth("hoodie_hood", hm, -0.50, -0.46, 0.125, 0.085, 0.07, 9, z0=0.0, m=1, fk=(1.5, 3.0))
    tube("sleeve_r", hm, [(-0.30, -0.64), (-0.23, -0.665), (-0.165, -0.72), (-0.125, -0.80)], 0.10, 0.075, 0.042, 0, cuff=1)
    tube("sleeve_l", hm, [(-0.64, -0.63), (-0.72, -0.70), (-0.80, -0.70), (-0.86, -0.665)], 0.10, 0.072, 0.040, 0, cuff=1)
    floor_shadow(cards, blob(-0.47, -0.58, 0.25, 0.20, 5, n=20, wob=0.05), 0.07)
    # an open book on its face-up pages, near the far end of the wedge
    ob_ = Parts("open_book", [M["pale"], bk[5]])
    bx, by = -0.25, -1.05
    ob_.box((bx, by, 0.0025), (0.37, 0.25, 0.005), 1, (0, 0, 0.16))
    c_, s_ = math.cos(0.16), math.sin(0.16)
    for k, rot in ((-1, 0.075), (1, -0.075)):
        ob_.box((bx + k * 0.088 * c_, by + k * 0.088 * s_, 0.012), (0.17, 0.235, 0.014), 0, (rot * s_, rot * c_, 0.16))
    ob_.make()
    floor_shadow(cards, rect_pts(bx - 0.18, by - 0.12, bx + 0.18, by + 0.12), 0.02)
    # phone on the floor, screen up: it turns about the end the cable plugs into
    pv = (-0.70, -1.17, 0.0)
    ph = Parts("phone", [M["dark"]], pivot=pv)
    ph.box((pv[0] + 0.02, pv[1] - 0.074, 0.0045), (0.074, 0.152, 0.009))
    ph_ob = ph.make()
    ids["phone"] = ph_ob.pass_index
    screen = Parts("screen", [kit.mat("screen", "#16182A", kind=1)], pivot=pv)
    screen.box((pv[0] + 0.02, pv[1] - 0.074, 0.0095), (0.066, 0.142, 0.001))
    sc_ob = screen.make()
    ids["screen"] = sc_ob.pass_index
    # a pen: its origin rolls, the clip and the print on it show that it turns
    pen = Parts("pen", [M["b1"], M["pale"], M["dark"]])
    pr = 0.0045
    pen.cyl((-0.07, 0, 0), (0.045, 0, 0), pr, 0, 6)
    pen.cyl((0.045, 0, 0), (0.07, 0, 0), pr * 0.7, 1, 6)
    pen.lohi((-0.06, -0.0015, pr), (-0.022, 0.0015, pr + 0.0025), 2)
    pen_ob = pen.make()
    pen_ob.visible_shadow = False     # thin and low: at this lamp its long shadow would only read as a black blot on the light
    PEN0 = (0.56, -0.16, pr)
    # a plastic bottle standing on the floor, left of the door where she can see it; it falls over towards the room
    bx0, by0, br = -0.22, -0.14, 0.03
    bot = Parts("bottle", [M["bottle"], M["cap"]], pivot=(bx0, by0 - br, 0))
    bot.cyl((bx0, by0, 0.0), (bx0, by0, 0.155), br, 0, 12)
    bot.cyl((bx0, by0, 0.155), (bx0, by0, 0.175), br * 0.55, 0, 12)
    bot.cyl((bx0, by0, 0.175), (bx0, by0, 0.195), br * 0.5, 1, 12)
    bot_ob = bot.make()
    bs0 = Parts("bottle_sh0", [M["sh_floor"]])
    floor_shadow(bs0, blob(bx0, by0, br, br, 1, n=10, wob=0.0), 0.19)
    bs0 = bs0.make()
    bs1 = Parts("bottle_sh1", [M["sh_floor"]])
    floor_shadow(bs1, rect_pts(bx0 - br, by0 - br - 0.195, bx0 + br, by0 - br), 0.05)
    bs1 = bs1.make()
    # school bag standing on the floor, its top leaning back on the wall: it turns about its bottom wall-side edge
    gx, gy = -1.0, -0.095
    bag = Parts("bag", [M["bag"], M["dark"], M["metal"]], pivot=(gx, gy, 0))
    bag.lohi((gx - 0.20, gy - 0.11, 0.0), (gx + 0.20, gy, 0.31))
    bag.lohi((gx - 0.205, gy - 0.118, 0.13), (gx + 0.205, gy - 0.10, 0.315), 1)     # flap
    bag.lohi((gx - 0.018, gy - 0.122, 0.135), (gx + 0.018, gy - 0.112, 0.19), 2)    # clasp
    for dx in (-0.07, 0.07):
        bag.lohi((gx + dx - 0.007, gy - 0.062, 0.31), (gx + dx + 0.007, gy - 0.048, 0.375), 1)
    bag.lohi((gx - 0.077, gy - 0.062, 0.365), (gx + 0.077, gy - 0.048, 0.38), 1)    # handle, on the bag
    bag_ob = bag.make()
    bag_ob.rotation_euler = (-0.26, 0, 0)
    floor_shadow(cards, rect_pts(gx - 0.20, gy - 0.11, gx + 0.20, gy), 0.30)

    # the futon she got up from: a mattress with the quilt thrown back on it, a mass at the left of her view
    fu = Parts("futon", [M["futon"]])
    fu.slab([(-1.33, -3.2), (-0.66, -3.2), (-0.62, -3.15), (-0.62, -1.72), (-0.66, -1.66), (-1.33, -1.66)], 0.0, 0.085)
    fu.make()
    cloth("quilt", [M["blanket"]], -1.02, -2.32, 0.42, 0.62, 0.17, 21, z0=0.085)
    floor_shadow(cards, rect_pts(-1.33, -3.2, -0.62, -1.66), 0.10)

    # a low table on the right, with what was left on it
    tab = Parts("table", [M["wood"], M["woodd"], M["pale"], M["b0"]])
    tx0, tx1, ty0, ty1 = 0.50, 1.32, -2.34, -1.66
    tab.lohi((tx0, ty0, 0.32), (tx1, ty1, 0.35))
    for x, y in ((tx0 + 0.06, ty0 + 0.06), (tx1 - 0.06, ty0 + 0.06), (tx0 + 0.06, ty1 - 0.06), (tx1 - 0.06, ty1 - 0.06)):
        tab.lohi((x - 0.024, y - 0.024, 0), (x + 0.024, y + 0.024, 0.32), 1)
    tab.box((0.86, -1.96, 0.356), (0.21, 0.29, 0.012), 2, (0, 0, -0.2))
    tab.cyl((0.68, -1.86, 0.35), (0.68, -1.86, 0.44), 0.038, 3, 18)
    tab.cyl((0.68, -1.86, 0.44), (0.68, -1.86, 0.4405), 0.031, 0, 18)    # the tea inside, seen from above
    for a_, b_ in (((0.712, -1.875, 0.425), (0.742, -1.885, 0.425)), ((0.742, -1.885, 0.425), (0.742, -1.885, 0.375)), ((0.742, -1.885, 0.375), (0.712, -1.875, 0.375))):
        tab.cyl(a_, b_, 0.0055, 3, 6)
    tab_ob = tab.make()
    tab_sh = Parts("table_sh", [M["sh_floor"]])
    floor_shadow(tab_sh, rect_pts(tx0, ty0, tx1, ty1), 0.33)
    tab_sh = tab_sh.make()

    # ---- sheets ----
    sheets = []
    if with_sheets:
        pm = kit.mat("sheet", "#F6F3EA", kind=4)
        for i in range(len(S.SHEETS)):
            nx, ny = 8, 6
            me = bpy.data.meshes.new(f"sheet{i}")
            rr = random.Random(i * 7 + 1)
            lift = [rr.uniform(0, 0.0002) for _ in range(4)]
            verts, faces = [], []
            for b in range(ny + 1):
                for a in range(nx + 1):
                    u, v = a / nx, b / ny
                    corner = (lift[0] * (1 - u) ** 4 * (1 - v) ** 4 + lift[1] * u ** 4 * (1 - v) ** 4 +
                              lift[2] * u ** 4 * v ** 4 + lift[3] * (1 - u) ** 4 * v ** 4)
                    verts.append(((u - 0.5) * S.SHEET_W, (v - 0.5) * S.SHEET_H, corner))
            for b in range(ny):
                for a in range(nx):
                    k = b * (nx + 1) + a
                    faces.append((k, k + 1, k + nx + 2, k + nx + 1))
            me.from_pydata(verts, [], faces)
            me.update()
            me.materials.append(pm)
            ob = kit._link(f"sheet{i}", me)
            ob.visible_shadow = False       # at this low lamp a millimetre of paper throws two centimetres of shadow: the painter gives it a few pixels instead
            ids[f"sheet{i}"] = ob.pass_index
            sheets.append(ob)

    ids["cards"] = cards.make().pass_index
    cam = kit.camera(sc, lens=S.LENS, clip_end=100)
    state = dict(table=(tab_ob, tab_sh), sc=sc, cam=cam, bs0=bs0, bs1=bs1, us=us_ob, door=d_ob, lever=lev_ob, feet=feet, cal=cal_ob, uni=uni_ob, tb=tb_ob, top_book=tb2,
                 phone=ph_ob, screen=sc_ob, pen=pen_ob, pen0=PEN0, bottle=bot_ob, sheets=sheets)
    return state, ids


def set_frame(t, st):
    eye, target, up = S.camera_at(t)
    z = (Vector(eye) - Vector(target)).normalized()
    x = Vector(up).cross(z).normalized()
    y = z.cross(x)
    cam = st["cam"]
    cam.rotation_mode = "QUATERNION"
    cam.matrix_world = Matrix.Translation(eye) @ Matrix((x, y, z)).transposed().to_4x4()
    cam.data.lens = S.lens_at(t)
    for ob in st["table"]:
        ob.hide_render = S.shot_at(t)[1] == "plate"    # the stills from across the room look over where the table is
    st["door"].rotation_euler = (0, 0, math.radians(S.door_angle(t)))
    st["lever"].rotation_euler = (0, math.radians(-S.lever_dip(t)), 0)
    for ob, (fx, fy, fz, head) in zip(st["feet"], S.feet_at(t)):
        ob.location = (fx, fy, fz)
        ob.rotation_euler = (0, 0, math.radians(-head))
    st["cal"].rotation_euler = (0, math.radians(S.calendar_drop(t)), 0)
    st["uni"].rotation_euler = (0, math.radians(S.uniform_swing(t)), 0)
    st["us"].rotation_euler = st["uni"].rotation_euler
    st["tb"].rotation_euler = (math.radians(-S.shelf_tip(t)), 0, 0)
    st["top_book"].location.y = -0.62 - S.book_slide(t)
    pa = math.radians(S.phone_turn(t))
    st["phone"].rotation_euler = (0, 0, pa)
    st["screen"].rotation_euler = (0, 0, pa)
    x0, y0, z0 = st["pen0"]
    d = S.pen_roll(t)
    st["pen"].location = (x0, y0 - d, z0)
    st["pen"].rotation_euler = (-d / z0, 0, 0)
    fall = S.bottle_fall(t)
    st["bottle"].rotation_euler = (math.radians(fall), 0, 0)
    st["bs0"].hide_render = fall > 45
    st["bs1"].hide_render = fall <= 45
    for i, ob in enumerate(st["sheets"]):
        p = S.sheet_pose(i, t)
        ob.hide_render = p is None
        if p:
            ob.location = p[:3]
            ob.rotation_euler = (0, 0, math.radians(p[3]))


def run(shared, shot, with_sheets):
    args = kit.set_args()
    out = Path(args[0]).resolve()
    out.mkdir(parents=True, exist_ok=True)
    st, ids = build(with_sheets)
    (ROOT / "work" / "render").mkdir(parents=True, exist_ok=True)
    (ROOT / "work" / "render" / f"{shot}_ids.json").write_text(json.dumps(ids))
    if args[1] == "todo":
        frames = json.loads(Path(args[2]).read_text())
        items = [(shared.T0 + f / 60.0, out / f"f{f:05d}.exr") for f in frames]
    else:
        items = [(float(a), out / f"t{float(a):07.3f}.exr") for a in args[1:]]
    sc = st["sc"]
    for t, path in items:
        if path.exists():
            continue
        set_frame(t, st)
        tmp = path.with_suffix(".tmp.exr")
        sc.render.filepath = str(tmp)
        bpy.ops.render.render(write_still=True)
        tmp.rename(path)
        print("RENDERED", path.name, flush=True)


if __name__ == "__main__":
    run(S, "room", False)
