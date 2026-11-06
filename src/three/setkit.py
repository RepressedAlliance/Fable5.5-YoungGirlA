"""Blender helpers shared by the gate, lockers, train and outro sets."""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import bmesh  # noqa: E402
import bpy  # noqa: E402
from mathutils import Matrix, Vector  # noqa: E402
import kit  # noqa: E402

TEX = kit.ROOT / "assets" / "tex" / "s02"


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
        self.card.matrix_world = self.matrix(p, (eye[0] - p[0], eye[1] - p[1]))
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
