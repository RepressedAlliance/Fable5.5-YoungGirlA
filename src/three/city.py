"""School and town around the classroom, built so the ground plan can flatten into a map.

The classroom floor is z=0 on the top floor, so the street level is GROUND. Everything except the
classroom shell is here. Buildings live in one mesh; shrinking its z scale to 0 flattens the town.
Colour comes from two vertex attributes and a mix value, so the town can turn into map colours.
"""
import math
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import bmesh  # noqa: E402
import bpy  # noqa: E402
import numpy as np  # noqa: E402
import kit  # noqa: E402
from kit import box, mat, srgb  # noqa: E402

GROUND = -7.6
EXTENT = 9000.0

BUILDING = ["#F2EDE0", "#EAE4D5", "#E2DDCF", "#DFE5E3", "#EFE6D3"]
ROOF = ["#C9C4B6", "#BDBDB2", "#ADB9BA", "#CDBBA8", "#A3B5BA", "#D5D0C2"]
MAP_BUILDING = "#E6DFCB"
MAP_LAND = "#F2EEDF"
MAP_ROAD = "#FFFFFF"
MAP_MAIN = "#CFE3EA"   # never yellow: yellow belongs to her alone
MAP_BLOCK = "#EFEADB"
MAP_WATER = "#7FD6F2"
MAP_PARK = "#BFE3B0"


def _lin(h):
    return np.array(srgb(h)[:3], np.float32)


def color_material(name, kind=0):
    """Material reading attributes 'c1' and 'c2', mixed by a value node named 'mapmix'."""
    if name in bpy.data.materials:
        return bpy.data.materials[name]
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    m.pass_index = kind
    nt = m.node_tree
    nt.nodes.remove(nt.nodes["Principled BSDF"])
    out = nt.nodes["Material Output"]
    d = nt.nodes.new("ShaderNodeBsdfDiffuse")
    a1 = nt.nodes.new("ShaderNodeAttribute")
    a1.attribute_name = "c1"
    a2 = nt.nodes.new("ShaderNodeAttribute")
    a2.attribute_name = "c2"
    v = nt.nodes.new("ShaderNodeValue")
    v.name = "mapmix"
    v.outputs[0].default_value = 0.0
    mx = nt.nodes.new("ShaderNodeMix")
    mx.data_type = "RGBA"
    nt.links.new(v.outputs[0], mx.inputs[0])
    nt.links.new(a1.outputs[0], mx.inputs[6])
    nt.links.new(a2.outputs[0], mx.inputs[7])
    nt.links.new(mx.outputs[2], d.inputs["Color"])
    nt.links.new(d.outputs[0], out.inputs[0])
    return m


def boxes_mesh(name, boxes, material, uid=None):
    """boxes: list of (x0, y0, z0, x1, y1, z1, c1_hex_top, c1_hex_side, c2_hex). One mesh, per-face colour."""
    n = len(boxes)
    a = np.array([b[:6] for b in boxes], np.float32)
    verts = np.zeros((n * 8, 3), np.float32)
    x0, y0, z0, x1, y1, z1 = a.T
    for i, (xs, ys, zs) in enumerate(((x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0),
                                      (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1))):
        verts[i::8, 0], verts[i::8, 1], verts[i::8, 2] = xs, ys, zs
    # top, four sides (no bottoms)
    q = np.array([[4, 5, 6, 7], [0, 1, 5, 4], [1, 2, 6, 5], [2, 3, 7, 6], [3, 0, 4, 7]], np.int32)
    faces = (q[None, :, :] + (np.arange(n, dtype=np.int32) * 8)[:, None, None]).reshape(-1, 4)
    me = bpy.data.meshes.new(name)
    me.vertices.add(len(verts))
    me.vertices.foreach_set("co", verts.ravel())
    me.loops.add(faces.size)
    me.loops.foreach_set("vertex_index", faces.ravel())
    me.polygons.add(len(faces))
    me.polygons.foreach_set("loop_start", np.arange(0, faces.size, 4, dtype=np.int32))
    me.polygons.foreach_set("use_smooth", np.zeros(len(faces), dtype=bool))
    me.update(calc_edges=True)
    cache = {}

    def c(h):
        if h not in cache:
            cache[h] = _lin(h)
        return cache[h]

    c1 = np.zeros((n * 5, 3), np.float32)
    c2 = np.zeros((n * 5, 3), np.float32)
    for i, b in enumerate(boxes):
        c1[i * 5] = c(b[6])
        c1[i * 5 + 1:i * 5 + 5] = c(b[7])
        c2[i * 5:i * 5 + 5] = c(b[8])
    # per-face colour on the corner domain, so faces stay flat
    for nm, arr in (("c1", c1), ("c2", c2)):
        at = me.color_attributes.new(nm, "FLOAT_COLOR", "CORNER")
        data = np.ones((faces.size, 4), np.float32)
        data[:, :3] = np.repeat(arr, 4, axis=0)
        at.data.foreach_set("color", data.ravel())
    return kit._link(name, me, (0, 0, GROUND), (0, 0, 0), material, uid=uid)


def build_town(seed=7, school_box=(-85, 75, -40, 95)):
    """Returns (buildings_object, ground_object). Town plan in world xy; z relative to street level."""
    r = random.Random(seed)
    M = color_material("town")
    flats = []  # flat things: roads, water, parks, all at street level
    blds = []

    def flat(x0, y0, x1, y1, col, mapcol, z=0.0):
        flats.append((x0, y0, z, x1, y1, z + 0.02, col, col, mapcol))

    # land
    flat(-EXTENT, -EXTENT, EXTENT, EXTENT, "#B7B6AE", MAP_ROAD, -0.30)
    # street grid. Spacing grows away from the middle so detail is near the school.
    def ticks(rng_seed):
        rr = random.Random(rng_seed)
        out = [0.0]
        p = 0.0
        while p < EXTENT:
            d = 62 + rr.random() * 46
            d *= 1 + (p / 2400.0) ** 1.4
            p += d
            out.append(p)
        return sorted([-v for v in out[1:]] + out)

    xs = ticks(seed + 1)
    ys = ticks(seed + 2)
    # the river runs diagonally: y = rx(x)
    def river_y(x):
        return 760 - 0.34 * x + 90 * math.sin(x / 420.0)

    RW = 90
    # rail line, straight east-west at y = -520
    RAIL = -520
    station_x = -340
    for i in range(len(xs) - 1):
        for j in range(len(ys) - 1):
            x0, x1 = xs[i], xs[i + 1]
            y0, y1 = ys[j], ys[j + 1]
            main_x = i % 6 == 0
            main_y = j % 6 == 0
            cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
            dist = math.hypot(cx, cy)
            road = 7 + 0.0035 * dist
            ax0 = x0 + (road * (1.8 if main_x else 1))
            ay0 = y0 + (road * (1.8 if main_y else 1))
            ax1, ay1 = x1, y1
            if ax1 - ax0 < 8 or ay1 - ay0 < 8:
                continue
            ry = river_y(cx)
            if abs(cy - ry) < RW + (y1 - y0) / 2:
                continue
            if abs(cy - RAIL) < 18 + (y1 - y0) / 2:
                continue
            bx0, bx1, by0, by1 = school_box
            if ax1 > bx0 and ax0 < bx1 and ay1 > by0 and ay0 < by1:
                continue
            # block kinds
            h = abs(math.sin(i * 12.9898 + j * 78.233) * 43758.5453) % 1.0
            if h < 0.045:
                flat(ax0, ay0, ax1, ay1, "#A9C49A", MAP_PARK, -0.22)
                continue
            flat(ax0, ay0, ax1, ay1, "#D2CDBC", MAP_BLOCK, -0.22)
            dstation = math.hypot(cx - station_x, cy - RAIL)
            high = max(0.0, 1 - dstation / 800.0)
            if dist > 3200:
                # far blocks are one mass each
                hh = 6 + 8 * r.random()
                top = r.choice(ROOF)
                side = r.choice(BUILDING)
                m = 4
                blds.append((ax0 + m, ay0 + m, 0, ax1 - m, ay1 - m, hh, top, side, MAP_BUILDING))
                continue
            lot = 14 + r.random() * 6 if dist < 900 else 26 + r.random() * 20
            nx = max(1, int((ax1 - ax0) / lot))
            ny = max(1, int((ay1 - ay0) / lot))
            lx = (ax1 - ax0) / nx
            ly = (ay1 - ay0) / ny
            for a in range(nx):
                for b in range(ny):
                    # leave some gaps (gardens, parking)
                    if r.random() < 0.10:
                        continue
                    m = 1.0 + r.random() * 1.5
                    px0 = ax0 + a * lx + m
                    py0 = ay0 + b * ly + m
                    px1 = ax0 + (a + 1) * lx - m
                    py1 = ay0 + (b + 1) * ly - m
                    hh = 6 + r.random() * 5
                    if r.random() < 0.15:
                        hh += 7 + r.random() * 8
                    if r.random() < high ** 2:
                        hh = 22 + r.random() * (30 + 80 * high)
                    top = r.choice(ROOF)
                    side = r.choice(BUILDING)
                    blds.append((px0, py0, 0, px1, py1, hh, top, side, MAP_BUILDING))
    # main roads paint over land
    for i, x in enumerate(xs):
        if i % 6 == 0:
            w = 12 + 0.004 * abs(x)
            flat(x, -EXTENT, x + w, EXTENT, "#DDD8C8", MAP_MAIN, -0.14)
    for j, y in enumerate(ys):
        if j % 6 == 0:
            w = 12 + 0.004 * abs(y)
            flat(-EXTENT, y, EXTENT, y + w, "#DDD8C8", MAP_MAIN, -0.14)
    # the river is one continuous ribbon: built from boxes its banks came out as stairs
    river_x = np.arange(-EXTENT, EXTENT + 1, 25.0)
    rv = [(x, river_y(x) - RW, -0.08) for x in river_x] + [(x, river_y(x) + RW, -0.08) for x in river_x]
    n_r = len(river_x)
    rf = [(i, i + 1, n_r + i + 1, n_r + i) for i in range(n_r - 1)]
    rme = bpy.data.meshes.new("river")
    rme.from_pydata(rv, [], rf)
    rme.update()
    for nm, col_h in (("c1", "#6FB7D3"), ("c2", MAP_WATER)):
        at = rme.color_attributes.new(nm, "FLOAT_COLOR", "CORNER")
        c_ = np.array([*_lin(col_h), 1.0], np.float32)
        at.data.foreach_set("color", np.tile(c_, len(rme.loops)))
    river = kit._link("river", rme, (0, 0, GROUND), (0, 0, 0), M)
    river.visible_shadow = False
    # railway
    flat(-EXTENT, RAIL - 7, EXTENT, RAIL + 7, "#6B6A70", "#4A4A52", -0.10)
    # the school's whole lot lies over the street grid: no road runs under a school
    bx0, bx1, by0, by1 = school_box
    flat(bx0, by0, bx1, by1, "#DCD6C4", "#EDE6CF", -0.06)
    blds.append((station_x - 60, RAIL - 22, 0, station_x + 60, RAIL + 22, 12, "#8FA0A8", "#D5D8D2", "#CFC9B4"))
    ground = boxes_mesh("town_ground", flats, M)
    ground.visible_shadow = False
    town = boxes_mesh("town_blds", blds, M)
    print("town", len(blds), "buildings", len(flats), "flats")
    return town, ground


def build_school():
    """School blocks around the classroom. Classroom interior x -3.8..3.8, y 0..9.2, floor z=0, top floor."""
    wall = mat("sch_wall", "#E7E2D3")
    roofm = mat("sch_roof", "#D3DAD1")
    glass = mat("sch_glass", "#6FA8BE")
    frame = mat("sch_frame", "#CFD3CE")
    x0, x1 = -4.0, 7.2     # outer walls (x1 includes the corridor)
    y0, y1 = -46.0, 55.0
    parts = []
    # lower floors
    parts.append(box("sch_low", ((x0 + x1) / 2, (y0 + y1) / 2, (GROUND - 0.2) / 2), (x1 - x0, y1 - y0, -GROUND - 0.2), wall))
    # top floor either side of our classroom, leaving the classroom's own walls exposed
    for a, b in ((y0, -0.2), (9.4, y1)):
        parts.append(box("sch_top", ((x0 + x1) / 2, (a + b) / 2, 1.6), (x1 - x0, b - a, 3.2), wall))
    # corridor-side outer wall by the classroom
    parts.append(box("sch_top", (x1 - 0.1, 4.6, 1.6), (0.2, 9.8, 3.2), wall))
    school = kit.join(parts, "school")
    # window bands along both long sides, three storeys
    win = []
    for fl in range(3):
        z = GROUND + 1.05 + fl * 2.533
        y = y0 + 1.0
        while y < y1 - 3:
            for sx, off in ((x0, -0.02), (x1, 0.02)):
                if fl == 2 and sx == x0 and -0.3 < y + 1.5 < 9.5:
                    continue
                win.append(box("w", (sx + off, y + 1.4, z + 0.75), (0.04, 2.6, 1.45), glass))
                win.append(box("w", (sx + off * 2, y + 1.4, z + 0.75), (0.03, 0.06, 1.45), frame))
            y += 3.1
    kit.join(win, "school_windows")
    # the roof: pieces either side stay on; `roof_hole` is the part above our classroom
    # the roof stops either side of our classroom: it stays open to the sky, the one frozen room in the school
    box("roof_a", ((x0 + x1) / 2, (y0 - 0.2) / 2, 3.3), (x1 - x0 + 0.6, -0.2 - y0, 0.2), roofm)
    box("roof_b", ((x0 + x1) / 2, (9.4 + y1) / 2, 3.3), (x1 - x0 + 0.6, y1 - 9.4, 0.2), roofm)
    box("roof_c", (x1 - 1.6, 4.6, 3.3), (3.8, 9.6, 0.2), roofm)
    hole = None
    # roof things, so the flat roof has shape and shadows: parapet, tank, stair head, vents, a painted walkway
    box("tank", (1.5, 40.0, 4.8), (3.0, 3.0, 2.4), frame)
    box("stair", (1.5, -30.0, 4.5), (4.0, 5.0, 2.0), wall)
    par = mat("parapet", "#D9D6CB")
    for yy0, yy1 in ((y0, -0.2), (9.4, y1)):
        for xx in (x0 - 0.3, x1 + 0.3):
            box("par", (xx, (yy0 + yy1) / 2, 3.65), (0.25, yy1 - yy0, 0.5), par)
    box("par", ((x0 + x1) / 2, y0, 3.65), (x1 - x0 + 0.6, 0.25, 0.5), par)
    box("par", ((x0 + x1) / 2, y1, 3.65), (x1 - x0 + 0.6, 0.25, 0.5), par)
    # waterproofing seams every couple of metres, the way a real flat roof looks from above
    seam = mat("roof_seam", "#A9B4AC")
    seams = []
    yy = y0 + 1.0
    while yy < y1:
        if not (-0.5 < yy < 9.7):
            seams.append(box("seam", ((x0 + x1) / 2, yy, 3.405), (x1 - x0 + 0.4, 0.06, 0.012), seam))
        yy += 2.2
    kit.join(seams, "roof_seams")
    vent = mat("vent", "#B6BFC0")
    rr = random.Random(11)
    for _ in range(26):
        yy = rr.choice([rr.uniform(y0 + 3, -3), rr.uniform(12, y1 - 3)])
        box("vent", (rr.uniform(x0 + 1.2, x1 - 1.2), yy, 3.75), (rr.uniform(0.9, 1.8), rr.uniform(0.9, 2.4), 0.7), vent)
    walk = mat("roof_walk", "#BFC4BE")
    box("walk", ((x0 + x1) / 2, -22.0, 3.41), (2.2, 40, 0.02), walk)
    box("walk", ((x0 + x1) / 2, 32.0, 3.41), (2.2, 42, 0.02), walk)
    # yard furniture and a row of trees round the edge
    leaf = mat("leaf", "#6E9E62")
    leaf2 = mat("leaf2", "#7FAE6C")
    trunk = mat("trunk", "#6A5240")
    for i in range(44):
        side = i % 4
        k = (i // 4) / 11
        if side == 0:
            tx, ty = -80 + 72 * k, -58
        elif side == 1:
            tx, ty = -80 + 72 * k, 68
        elif side == 2:
            tx, ty = -80, -58 + 126 * k
        else:
            tx, ty = 14 + rr.uniform(-2, 2), 8 + 45 * k
        h_ = rr.uniform(5, 8)
        kit.cyl("tr", (tx, ty, GROUND), (tx, ty, GROUND + h_ * 0.5), 0.28, trunk, seg=5)
        bm = bmesh.new()
        bmesh.ops.create_icosphere(bm, subdivisions=3, radius=rr.uniform(2.4, 3.4))
        me = bpy.data.meshes.new("crown")
        bm.to_mesh(me)
        bm.free()
        # a round crown: smooth normals, so the one hard terminator curves around it
        me.polygons.foreach_set("use_smooth", np.ones(len(me.polygons), dtype=bool))
        me.update()
        kit._link("crown", me, (tx, ty, GROUND + h_), (0, 0, rr.uniform(0, 3)), leaf if i % 3 else leaf2)
    goal = mat("goal", "#F4F1E4")
    for gx, gy in ((-43, -30), (-43, 39)):
        box("goal", (gx, gy, GROUND + 1.3), (7.0, 0.12, 2.5), goal)
    shed = mat("shed", "#90A3A8")
    box("shed", (12, -42, GROUND + 1.3), (5, 22, 2.6), shed)
    box("shed_roof", (12, -42, GROUND + 2.7), (6, 23, 0.2), mat("shed_roof", "#6F8690"))
    # playground on the window side
    ground_z = GROUND + 0.05
    sand = mat("sand", "#E3D1A6")
    box("yard", (-43, 4.5, ground_z), (76, 130, 0.1), sand)
    white = mat("yard_line", "#F4F1E4")
    # a running track drawn as four thin bars and two rounded ends made from short bars
    cx, cy, a_, b_ = -43.0, 4.5, 24.0, 36.0
    pts = []
    for i in range(64):
        t = i / 64 * 2 * math.pi
        pts.append((cx + a_ * math.cos(t), cy + b_ * math.sin(t)))
    lines = []
    for f_ in (1.0, 0.92, 0.84):
        for i in range(64):
            p0, p1 = pts[i], pts[(i + 1) % 64]
            q0 = (cx + (p0[0] - cx) * f_, cy + (p0[1] - cy) * f_)
            q1 = (cx + (p1[0] - cx) * f_, cy + (p1[1] - cy) * f_)
            lines.append(kit.cyl("track", (q0[0], q0[1], ground_z + 0.08), (q1[0], q1[1], ground_z + 0.08), 0.20, white, seg=4))
    # a football pitch inside the track
    for (ax, ay, sx, sy) in ((cx, cy, 26.0, 0.4), (cx, cy - 18, 26.0, 0.4), (cx, cy + 18, 26.0, 0.4), (cx - 13, cy, 0.4, 36.0), (cx + 13, cy, 0.4, 36.0)):
        lines.append(box("pitch", (ax, ay, ground_z + 0.09), (sx, sy, 0.02), white))
    kit.join(lines, "yard_lines")
    # gym and pool
    box("gym", (-40, 92, GROUND + 6), (34, 22, 12), mat("gym", "#BFC8C6"))
    box("gym_roof", (-40, 92, GROUND + 12.2), (35, 23, 0.4), mat("gym_roof", "#7F909A"))
    box("pool_rim", (22, 60, GROUND + 0.25), (30, 15, 0.5), mat("pool_rim", "#D9DBD3"))
    box("pool", (22, 60, GROUND + 0.51), (26, 12, 0.02), mat("pool", "#39B9E0", kind=1))
    return hole


def set_mapmix(value, flatten=None, town=None):
    m = bpy.data.materials.get("town")
    if m:
        m.node_tree.nodes["mapmix"].outputs[0].default_value = value
    if town is not None and flatten is not None:
        town.scale.z = max(flatten, 1e-3)
