"""Blender helpers shared by the gate, lockers, train and outro sets."""
import json
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import bmesh  # noqa: E402
import bpy  # noqa: E402
from mathutils import Matrix, Vector  # noqa: E402
import kit  # noqa: E402

TEX = kit.ROOT / "assets" / "tex" / "s02"
_BANDS = None


def push_behind(fig, eye, point, normal, inside, margin=0.02, hi=1.6):
    """The other way round from pull_to_lens: a person who sits behind something that must cover them (the back of their chair, seen
    from behind) has their card drawn further from the lens and larger by the same ratio until no painted part of it reaching into
    that thing's plane is on the lens's side of it. Seen from the lens nothing changes; the thing in front can no longer have a
    sliver of the card come through it where the two planes cross (2026-11-18: a broken ink line down her chair back).
    point, normal: the plane of the thing's far face, normal towards the lens. inside(P) -> bool: whether a point of the card lies
    within the thing's extent, measured in its plane. Returns the ratio used."""
    if not fig.bands:
        return 1.0
    M = fig.card.matrix_world.copy()
    W, H = fig.img_wh
    E, P0, N = Vector(eye), Vector(point), Vector(normal).normalized()
    k = 1.0
    for row, c0, c1 in fig.bands:
        ly = (H / 2 - row - 1) * fig.px
        for c in (c0, c1 + 1):
            lx = ((W / 2 - c) if fig.uv_flipped else (c - W / 2)) * fig.px
            P = M @ Vector((lx, ly, 0.0))
            if not inside(P):
                continue
            s_ = (P - P0).dot(N)
            if s_ > -margin:
                denom = -(P - E).dot(N)
                if denom > 1e-6:
                    k = max(k, ((E - P0).dot(N) + margin) / denom)
    k = min(hi, k)
    if k > 1.0001:
        fig.card.matrix_world = Matrix.Translation(E) @ Matrix.Scale(k, 4) @ Matrix.Translation(-E) @ M
    return k


def bands_of(path):
    """Row by row, how far across the drawing its paint reaches (src/art/opaque_bands.py), or None if it is not measured."""
    global _BANDS
    if _BANDS is None:
        f = kit.ROOT / "assets" / "gen" / "opaque_bands.json"
        _BANDS = json.loads(f.read_text()) if f.exists() else {}
    try:
        return _BANDS.get(Path(path).resolve().relative_to(kit.ROOT).as_posix())
    except ValueError:
        return None


def _card_points(fig):
    """World points along the painted outline of a card, row band by row band."""
    M = fig.card.matrix_world
    W, H = fig.img_wh
    for row, c0, c1 in fig.bands:
        ly = (H / 2 - row - 1) * fig.px
        for c in (c0, c1 + 1):
            lx = ((W / 2 - c) if fig.uv_flipped else (c - W / 2)) * fig.px
            yield M @ Vector((lx, ly, 0.0))


def pull_needed(fig, eye, room, margin=0.02):
    """How far towards the lens a card would have to be drawn for no painted part of it to be inside the set (room) or under
    the floor: the ratio of its new distance to its old. 1 when nothing reaches in."""
    if not fig.bands:
        return 1.0
    E = Vector(eye)
    k = 1.0
    for P in _card_points(fig):
        xmin, xmax = room(P.y, P.z)
        if P.z < -0.004:
            # a card set lower than its floor (a sitter lowered onto the seat) comes up out of it the same way
            k = min(k, (E.z - 0.004) / (E.z - P.z))
        if P.x > xmax - margin and P.x > E.x:
            k = min(k, (xmax - margin - E.x) / (P.x - E.x))
        elif P.x < xmin + margin and P.x < E.x:
            k = min(k, (xmin + margin - E.x) / (P.x - E.x))
    return k


def scale_about_eye(fig, eye, k):
    if abs(k - 1.0) > 1e-4:
        E = Vector(eye)
        fig.card.matrix_world = Matrix.Translation(E) @ Matrix.Scale(k, 4) @ Matrix.Translation(-E) @ fig.card.matrix_world


def _view_box(points, E):
    """Horizontal and vertical angle ranges of points seen from E, and their nearest horizontal distance."""
    az, el, dist = [], [], []
    for P in points:
        dx, dy, dz = P.x - E.x, P.y - E.y, P.z - E.z
        h = math.hypot(dx, dy)
        az.append(math.atan2(dx, dy))
        el.append(math.atan2(dz, h))
        dist.append(h)
    return min(az), max(az), min(el), max(el), min(dist)


def pole_box(a, b, r, eye):
    """The view box of a straight pole of radius r from a to b."""
    E = Vector(eye)
    pts = []
    for P in (Vector(a), Vector(b)):
        for ox, oy in ((r, 0), (-r, 0), (0, r), (0, -r)):
            pts.append(P + Vector((ox, oy, 0)))
    return _view_box(pts, E)


def pull_to_lens_all(figs, eye, room, poles=(), lo=0.55, margin=0.02, gap=0.10):
    """pull_to_lens for everyone in a place at once, so that no card is drawn in front of a person or a pole that the lens
    sees in front of it (2026-11-18, second pass: a far passenger's card reached so deep into the bench that pulling it clear
    brought it in front of the people standing in the aisle, and he sat in the air on a standing man's legs; a woman came out in
    front of the bench-end pole). Each card comes only as far as the nearest thing it overlaps that was nearer the lens, less
    `gap`; whatever of the bench still reaches it then is the lesser fault. figs: Figures with .pin (where their feet are).
    poles: [(a, b, radius)]. Returns {fig: ratio}."""
    E = Vector(eye)
    boxes = {}
    for f in figs:
        if f.bands:
            a0, a1, e0, e1, _ = _view_box(list(_card_points(f)), E)
            boxes[f] = (a0, a1, e0, e1, math.hypot(f.pin[0] - E.x, f.pin[1] - E.y))
    occl = list(boxes.values()) + [pole_box(a, b, r, eye) for a, b, r in poles]
    out = {}
    for f, (a0, a1, e0, e1, d) in boxes.items():
        k = max(lo, pull_needed(f, eye, room, margin))
        if k < 0.9999:
            for b0, b1, g0, g1, dq in occl:
                if dq < d - 1e-6 and b0 < a1 and a0 < b1 and g0 < e1 and e0 < g1:
                    k = max(k, min(1.0, (dq + gap) / d))
            scale_about_eye(f, eye, k)
        out[f] = k
    return out


def _view_rows(fig, E):
    """The painted part of a card as seen from E, row band by row band: [(el0, el1, az0, az1)]."""
    M = fig.card.matrix_world
    W, H = fig.img_wh
    out = []
    prev = None
    for row, c0, c1 in fig.bands:
        ly = (H / 2 - row - 1) * fig.px
        pts = []
        for c in (c0, c1 + 1):
            lx = ((W / 2 - c) if fig.uv_flipped else (c - W / 2)) * fig.px
            P = M @ Vector((lx, ly, 0.0))
            dx, dy, dz = P.x - E.x, P.y - E.y, P.z - E.z
            pts.append((math.atan2(dx, dy), math.atan2(dz, math.hypot(dx, dy))))
        el = pts[0][1]
        az0, az1 = min(pts[0][0], pts[1][0]), max(pts[0][0], pts[1][0])
        if prev is not None:
            out.append((min(prev, el), max(prev, el), az0, az1))
        prev = el
    return out


def _rows_overlap(ra, rb):
    for e0, e1, a0, a1 in ra:
        for g0, g1, b0, b1 in rb:
            if e0 < g1 and g0 < e1 and a0 < b1 and b0 < a1:
                return True
    return False


def pull_by(fig, others, eye, dist, gap=0.10):
    """Draw one card `dist` metres nearer the lens along the line of sight, and smaller by the same ratio (unchanged as seen),
    but never in front of another card that was nearer the lens and whose painted rows overlap its own (others: Figures with
    .pin). For someone standing up on a stepladder: his flat card crossed the ladder's top, which then cut across his knee."""
    if not fig.bands:
        return 1.0
    E = Vector(eye)
    d = math.hypot(fig.pin[0] - E.x, fig.pin[1] - E.y)
    d3 = (Vector(fig.pin) - E).length
    k = max(0.5, 1.0 - dist / d3)
    mine = None
    for o in others:
        if o is fig or not o.bands:
            continue
        dq = math.hypot(o.pin[0] - E.x, o.pin[1] - E.y)
        if dq < d and (dq + gap) / d > k:
            if mine is None:
                mine = _view_rows(fig, E)
            if _rows_overlap(mine, _view_rows(o, E)):
                k = min(1.0, (dq + gap) / d)
    scale_about_eye(fig, eye, k)
    return k


def pull_to_lens(fig, eye, room, lo=0.55, margin=0.02):
    """Seen from the lens nothing changes: the card is drawn nearer it and smaller by the same ratio. What changes is that the
    set behind the person's place, the bench they sit on or rise from, can no longer cover any painted part of them.
    A card stands upright at the feet and faces the lens, so half of it reaches back into the bench: a sitter's lap and hips were
    cut by the seat as if they sat inside it (2026-11-18). room(y, z) -> (xmin, xmax): how far across the floor a body may
    reach at that place and height before it is inside the set. Use pull_to_lens_all where other people or poles stand
    in front. Returns the ratio used."""
    k = max(lo, pull_needed(fig, eye, room, margin))
    scale_about_eye(fig, eye, k)
    return k


def quads(name, items, material, uid=None):
    """One mesh of many quads: items are (four corners, four uvs)."""
    verts, faces, uvs = [], [], []
    for corners, uv in items:
        i = len(verts)
        verts += [tuple(p) for p in corners]
        faces.append((i, i + 1, i + 2, i + 3))
        uvs += list(uv)
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], faces)
    me.update()
    layer = me.uv_layers.new(name="UV")
    for lp in me.loops:
        layer.data[lp.index].uv = uvs[lp.vertex_index]
    return kit._link(name, me, (0, 0, 0), (0, 0, 0), material, None, uid)


def wall_plane(name, center, sx, sz, material, facing="-y", uid=None):
    """Upright picture on a wall; reads the right way round from the side it faces."""
    rot = {"-y": (math.pi / 2, 0, 0), "+y": (math.pi / 2, 0, math.pi),
           "+x": (math.pi / 2, 0, math.pi / 2), "-x": (math.pi / 2, 0, -math.pi / 2)}[facing]
    return kit.plane(name, center, sx, sz, material, rot=rot, uid=uid)


def tube(name, pts, r, material, seg=6, uid=None):
    """A cable: a swept polygon along a polyline."""
    pts = [Vector(p) for p in pts]
    verts, faces = [], []
    for i, p in enumerate(pts):
        d = (pts[min(i + 1, len(pts) - 1)] - pts[max(i - 1, 0)]).normalized()
        a = d.cross(Vector((0, 0, 1)))
        if a.length < 1e-4:
            a = Vector((1, 0, 0))
        a.normalize()
        b = d.cross(a).normalized()
        for k in range(seg):
            th = 2 * math.pi * k / seg
            verts.append(tuple(p + (a * math.cos(th) + b * math.sin(th)) * r))
    for i in range(len(pts) - 1):
        for k in range(seg):
            a0, a1 = i * seg + k, i * seg + (k + 1) % seg
            faces.append((a0, a1, a1 + seg, a0 + seg))
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], faces)
    me.update()
    return kit._link(name, me, (0, 0, 0), (0, 0, 0), material, None, uid)


def chaikin(pts, n=2):
    for _ in range(n):
        out = [pts[0]]
        for a, b in zip(pts[:-1], pts[1:]):
            out.append(tuple(0.75 * x + 0.25 * y for x, y in zip(a, b)))
            out.append(tuple(0.25 * x + 0.75 * y for x, y in zip(a, b)))
        out.append(pts[-1])
        pts = out
    return pts


def blob(name, center, size, material, uid=None):
    """Squashed ball, for sandbags and foam mic heads."""
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=10, v_segments=6, radius=1.0)
    for v in bm.verts:
        v.co.x *= size[0]
        v.co.y *= size[1]
        v.co.z *= size[2]
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    return kit._link(name, me, center, (0, 0, 0), material, None, uid)


def cone(name, center, r0, r1, h, material, rot=(0, 0, 0), seg=14, uid=None):
    """Cone frustum standing on `center`: a paper cup."""
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=seg, radius1=r0, radius2=r1, depth=h, matrix=Matrix.Translation((0, 0, h / 2)))
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    return kit._link(name, me, center, rot, material, None, uid)


def loft(name, levels, material, center=(0, 0, 0), rot=(0, 0, 0), uid=None):
    """Stacks of closed outlines, bottom to top: shoes. Each level is (z, [(x, y), ...]), same point count."""
    n = len(levels[0][1])
    verts, faces = [], []
    for z, outline in levels:
        verts += [(x, y, z) for x, y in outline]
    faces.append(tuple(range(n - 1, -1, -1)))
    for i in range(len(levels) - 1):
        for k in range(n):
            a, b = i * n + k, i * n + (k + 1) % n
            faces.append((a, b, b + n, a + n))
    top = (len(levels) - 1) * n
    faces.append(tuple(top + k for k in range(n)))
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], faces)
    me.update()
    return kit._link(name, me, center, rot, material, None, uid)


class Figure:
    """Her cut-out. A card that stays upright and faces the camera, feet on the floor; a second card, unseen,
    faces the sun and throws her shadow from the same feet."""

    def __init__(self, path, name, px, foot_row, centre_col, sun=None, img_wh=(1024, 1536), uid=None, shadow_col=None):
        self.px, self.foot, self.col = px, foot_row, centre_col
        self.shadow_col = centre_col if shadow_col is None else shadow_col   # the foot the shadow grows from, if that is not the centre
        self.w, self.h = img_wh[0] * px, img_wh[1] * px
        self.img_wh = img_wh
        self.bands = bands_of(path)
        self.uv_flipped = False   # set where the caller mirrors the card's picture
        m = kit.mat("her_" + name, "#FFFFFF", kind=2, tex=path, alpha_tex=True)
        # a picture cropped by its bottom edge would otherwise wrap round and draw a faint line along its top
        for nd in m.node_tree.nodes:
            if nd.type == "TEX_IMAGE":
                nd.extension = "CLIP"
        self.card = kit.plane(name, (0, 0, 0), self.w, self.h, m, uid=uid)
        self.card.visible_shadow = False
        self.shadow = None
        if sun is not None:
            self.shadow = kit.plane(name + "_shadow", (0, 0, 0), self.w, self.h, m)
            self.shadow.visible_camera = False
            self.sun = Vector(sun).normalized()

    def matrix(self, p, forward, col=None):
        f = Vector((forward[0], forward[1], 0)).normalized()
        r = Vector((0, 0, 1)).cross(f).normalized()
        u = Vector((0, 0, 1))
        cx = ((self.col if col is None else col) - self.img_wh[0] / 2) * self.px
        cz = (self.foot - self.img_wh[1] / 2) * self.px
        m = Matrix((r, u, f)).transposed().to_4x4()
        m.translation = Vector(p) - r * cx + u * cz
        return m

    def show(self, on):
        self.card.hide_render = not on
        if self.shadow is not None:
            self.shadow.hide_render = not on

    def place(self, p, eye):
        self.pin = tuple(p)
        self.card.matrix_world = self.matrix(p, (eye[0] - p[0], eye[1] - p[1]))
        self.place_shadow(p)

    def place_shadow(self, p):
        if self.shadow is not None:
            self.shadow.matrix_world = self.matrix(p, (-self.sun.x, -self.sun.y), self.shadow_col)


def set_camera(cam, eye, target, up=(0, 0, 1), lens=None):
    z = (Vector(eye) - Vector(target)).normalized()
    x = Vector(up).cross(z).normalized()
    y = z.cross(x)
    cam.rotation_mode = "QUATERNION"
    cam.matrix_world = Matrix.Translation(eye) @ Matrix((x, y, z)).transposed().to_4x4()
    if lens:
        cam.data.lens = lens


def run(args, shared, build_fn, frame_fn):
    """The usual command line: OUTDIR t1 t2 ... for stills, OUTDIR todo FILE.json for lists of frames."""
    import json
    out = Path(args[0]).resolve()
    out.mkdir(parents=True, exist_ok=True)
    if args[1] == "todo":
        frames = json.loads(Path(args[2]).read_text())
        items = [(shared.T0 + f / 60.0, out / f"f{f:05d}.exr") for f in frames]
    else:
        items = [(float(a), out / f"t{float(a):07.3f}.exr") for a in args[1:]]
    state = build_fn()
    sc = state[0]
    for t, path in items:
        if path.exists():
            continue
        frame_fn(t, *state)
        tmp = path.with_suffix(".tmp.exr")
        sc.render.filepath = str(tmp)
        bpy.ops.render.render(write_still=True)
        tmp.rename(path)
        print("RENDERED", path.name, flush=True)
