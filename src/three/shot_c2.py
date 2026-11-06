"""Clip 2: samui x14. A newspaper pinned to her desk starts the shot; words nail into the empty room.

Run in Blender:  blender -b --python shot_c2.py -- OUTDIR t1 t2 ...     render given song times
                 blender -b --python shot_c2.py -- OUTDIR all [start_n end_n]
Frames are numbered at 60 fps from T0; slow stretches only render every second frame.
"""
import json
import math
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import bmesh  # noqa: E402
import bpy  # noqa: E402
from mathutils import Matrix, Vector  # noqa: E402
import classroom  # noqa: E402
import shared_c2 as S2  # noqa: E402
import kit  # noqa: E402
from kit import box, mat, plane  # noqa: E402
from shared_c2 import (T0, T1, HITS, her_desk, camera_at, cold_at, sun_dir_at, frames_all, SS,
                       PAGE_C, PAGE_W, PAGE_H, HIT_T, GROUP)  # noqa: E402

ROOT = kit.ROOT
FONT_DIR = ROOT / "assets" / "fonts" / "ttf"
HEADLINES = [
    "少女A、あの日の足取り", "同級生が語る「少女A」の素顔", "少女Aの卒業文集を入手", "母校に報道陣が殺到",
    "少女A、SNSに謎の投稿", "専門家「少女Aの心の闇」", "近所の人「普通の子だった」", "「いつかやると思ってた」",
    "少女Aの部屋から何が", "担任は語らず", "少女Aの素顔、徹底検証", "知られざる14年", "少女Aの本当の顔", "少女A、その後",
]
FONTS = ["ShipporiMinchoB1-ExtraBold", "DelaGothicOne-Regular", "ZenKakuGothicNew-Black"]


def font(name):
    return bpy.data.fonts.load(str(FONT_DIR / f"{name}.ttf"), check_existing=True)


def text_mesh(body, fname, size, extrude, name):
    cu = bpy.data.curves.new(name, "FONT")
    cu.body = body
    cu.font = font(fname)
    cu.size = size
    cu.extrude = extrude
    cu.align_x = "CENTER"
    cu.align_y = "CENTER"
    cu.resolution_u = 3
    ob = bpy.data.objects.new(name, cu)
    bpy.context.scene.collection.objects.link(ob)
    dg = bpy.context.evaluated_depsgraph_get()
    me = bpy.data.meshes.new_from_object(ob.evaluated_get(dg))
    bpy.data.objects.remove(ob)
    bpy.data.curves.remove(cu)
    return me


def make_slab(i, h):
    """Word block. Local axes: x right, y up, z towards the viewer. Returns the root empty."""
    root = bpy.data.objects.new(f"slab{i}", None)
    bpy.context.scene.collection.objects.link(root)
    cyan = mat("slab_face", "#03C3FB", kind=4)
    side = mat("slab_side", "#046E8C", kind=4)
    paper = mat("slab_paper", "#F6F3EA", kind=5)
    print_ = mat("slab_print", "#0A0A0F", kind=3)
    s = h["size"]
    fname = FONTS[h.get("font", 0)]
    depth = s * 0.016
    vertical = h.get("vertical", False)
    if vertical:
        ids = []
        for k, ch in enumerate("寒い"):
            me = text_mesh(ch, fname, s * 0.62, depth, f"w{i}{k}")
            ob = kit._link(f"w{i}{k}", me, (0, s * (0.30 - 0.62 * k), 0), (0, 0, 0), cyan, parent=root)
            ids.append(ob)
        strip_c, strip_size = (s * 0.48, 0.0, 0.0), (s * 0.13, s * 1.15)
        rot_t = (0, 0, -math.pi / 2)
    else:
        me = text_mesh("寒い", fname, s * 0.58, depth, f"w{i}")
        # the word's feet stand on the paper strip, so word and strip are one thing
        ob = kit._link(f"w{i}", me, (0, -s * 0.005, 0), (0, 0, 0), cyan, parent=root)
        ids = [ob]
        strip_c, strip_size = (0.0, -s * 0.36, 0.0), (s * 1.12, s * 0.12)
        rot_t = (0, 0, 0)
    for o in ids:
        me = o.data
        me.materials.clear()
        me.materials.append(cyan)
        me.materials.append(side)
        for p in me.polygons:
            p.material_index = 0 if abs(p.normal.z) > 0.8 else 1
    st = plane(f"strip{i}", strip_c, strip_size[0], strip_size[1], paper, parent=root)
    tmesh = text_mesh(HEADLINES[i], "ZenKakuGothicNew-Bold", min(strip_size) * 0.62, 0.0, f"h{i}")
    # fit to strip
    xs = [v.co.x for v in tmesh.vertices] or [1]
    long_side = max(strip_size)
    width = max(xs) - min(xs)
    k = min(1.0, long_side * 0.92 / max(width, 1e-3))
    tobj = kit._link(f"h{i}", tmesh, (strip_c[0], strip_c[1], 0.004), rot_t, print_, parent=root)
    tobj.scale = (k, k, 1)
    tobj.visible_shadow = False   # a printed line has no thickness; only the blocks and the paper throw shadows
    root["base_scale"] = 1.0
    return root


def surface_matrix(h, cam_eye, cam_up):
    """Final pose: tilted off the surface like something thrown, readable from the camera at that moment."""
    p = Vector(h["p"])
    n = Vector(h["n"]).normalized()
    to_cam = (Vector(h.get("face", cam_eye)) - p).normalized()
    w = h.get("w", 0.72)
    f = (n * w + to_cam * (1 - w)).normalized()
    # a word given its own facing stands upright: at the first blows the camera itself is still tipped over the page
    up = Vector((0, 0, 1)) if "face" in h else Vector(cam_up)
    up = (up - f * up.dot(f)).normalized()
    r = up.cross(f).normalized()
    # a little roll so they do not all sit level
    a = math.radians(h.get("roll", 0.0))
    r2 = r * math.cos(a) + up * math.sin(a)
    u2 = up * math.cos(a) - r * math.sin(a)
    m = Matrix((r2, u2, f)).transposed().to_4x4()
    # the point of impact is the middle of the block's lower edge when it stands up, its centre when flush
    off = u2 * (h["size"] * 0.62) * h.get("stand", 0.0)
    m.translation = p + off + f * h["size"] * 0.012
    return m


def crack_mesh(i, seed, material, limit=None):
    bm = bmesh.new()
    for spoke in S2.crack_spokes(seed, limit):
        bm.faces.new([bm.verts.new((x, y, 0)) for x, y in spoke])
    me = bpy.data.meshes.new(f"crack{i}")
    bm.to_mesh(me)
    bm.free()
    return kit._link(f"crack{i}", me, material=material)


def window_limit(h):
    """A crack in the glass stops at the window's top and bottom rails: it does not run on across the wall."""
    q = Vector(h["n"]).normalized().to_track_quat("Z", "Y")
    scale = h["size"] * h.get("crack", 0.55)
    lo, hi = 0.96, 2.34
    z = h["p"][2]
    def limit(ang):
        dz = (q @ Vector((math.cos(ang), math.sin(ang), 0))).z
        room = (hi - z) if dz > 0 else (z - lo)
        return max(room, 0.02) / max(abs(dz), 1e-3) / scale
    return limit


def desk_limit(h):
    """A crack on a desk stops short of the desk's edge: past it there is nothing for it to be a crack in."""
    hw, hd = S2.DESK_HALF
    scale = h["size"] * h["crack"]
    def limit(ang):
        cx, cy = abs(math.cos(ang)), abs(math.sin(ang))
        return min(hw / max(cx, 1e-3), hd / max(cy, 1e-3)) * 0.93 / scale
    return limit


# Desks the camera's orbit passes right over: from there each is only a huge cropped top. Hidden, not deleted, so object ids stay put.
PATH_DESKS = {(5, 1), (5, 2), (5, 3)}


def tidy(desks):
    """The room in order, so the rows draw lines the eye can follow to her desk. classroom.py is left alone: other shots use its room.
    A class keeps its rows straight. The desks next to hers have been pulled away from it, and the rows bend round the gap."""
    r = random.Random(7)
    for (c, row), (d, ch) in desks.items():
        if (c, row) == S2.HER:
            continue
        x, y = S2.desk_xy(c, row)
        pts = [d.matrix_world @ v.co for v in d.data.vertices]
        d.location.x += x - 0.31 - min(p.x for p in pts)
        d.location.y += y - 0.22 - min(p.y for p in pts)
        # chairs pushed in, each a hair differently: people did this, not a machine
        ch.location = (x + r.uniform(-0.012, 0.012), y - 0.46 - r.uniform(0.0, 0.05), 0.42)
        ch.rotation_euler = (0, 0, r.uniform(-0.035, 0.035))
    for key in PATH_DESKS:
        for ob in desks[key]:
            ob.hide_render = True


def build():
    sc = kit.reset()
    kit.setup_render(sc, 1920, 1080, ss=SS, fps=60, samples=3, threads=12)
    sc.render.use_persistent_data = True
    M, desks = classroom.build()
    tidy(desks)
    bpy.context.view_layer.update()
    sun = kit.sun(sc, sun_dir_at(T0))
    cam = kit.camera(sc, lens=26)
    # the newspaper on her desk, one more thing that stays warm
    dx, dy = her_desk()
    page, under = classroom.newspaper(PAGE_C, PAGE_W, PAGE_H, S2.PAGE_ANGLE, mat("page", "#EDE7D3", kind=4), mat("page_under", "#DDD6C0", kind=4))
    ids = {"page": page.pass_index, "under": under.pass_index}
    board = bpy.data.objects["board"]
    ids["board"] = board.pass_index
    # word blocks
    slabs, cracks = [], []
    crack_mat = mat("crack", "#17171D", kind=4)
    for i, h in enumerate(HITS):
        s = make_slab(i, h)
        s.hide_render = True
        slabs.append(s)
        c = crack_mesh(i, 100 + i, crack_mat, desk_limit(h) if h.get("on_desk") else window_limit(h) if h["n"][0] > 0.5 else None)
        n = Vector(h["n"]).normalized()
        q = n.to_track_quat("Z", "Y")
        c.rotation_mode = "QUATERNION"
        c.rotation_quaternion = q
        c.location = Vector(h["p"]) + n * 0.006
        if h.get("on_desk"):
            c.location.z = S2.DESK_TOP_Z + 0.0025    # in the desk's own surface
        c.scale = (h["size"] * h.get("crack", 0.55),) * 3
        c.hide_render = True
        cracks.append(c)
    # The snow is painted now (paint_c2.snow_mask); these stay, never rendered, so that the object ids stay put.
    snow_mat = mat("snow_chip", "#FBFDFF", kind=3)
    r = random.Random(5)
    bm = bmesh.new()
    from shared_c2 import ORBIT_C, ORBIT_R
    placed = 0
    while placed < 800:
        x, y, z = r.uniform(-3.7, 3.7), r.uniform(0.1, 9.1), r.uniform(0, 3.0)
        # keep well clear of the camera's path: near the lens a flake turns into a big white ball
        if abs(math.hypot(x - ORBIT_C[0], y - ORBIT_C[1]) - ORBIT_R) < 1.5:
            continue
        placed += 1
        sz = r.uniform(0.003, 0.012) if r.random() < 0.8 else r.uniform(0.0015, 0.003)
        bmesh.ops.create_icosphere(bm, subdivisions=2, radius=sz, matrix=Matrix.Translation((x, y, z)))
    me = bpy.data.meshes.new("snow")
    bm.to_mesh(me)
    bm.free()
    flakes = [kit._link("snow_a", me, (0, 0, 0), material=snow_mat), kit._link("snow_b", me.copy(), (0, 0, 3.0), material=snow_mat)]
    for f in flakes:
        f.visible_shadow = False
        f.hide_render = True
    # chips of dust knocked out at impact: they burst from round the edge of the word and fly away from it, never across it
    dust_mat = mat("dust", "#F4F1E6", kind=3)
    puffs = []
    for i, h in enumerate(HITS):
        group = []
        rr = random.Random(200 + i)
        for k in range(12):
            bm = bmesh.new()
            bmesh.ops.create_icosphere(bm, subdivisions=1, radius=1.0)
            pm = bpy.data.meshes.new(f"p{i}{k}")
            bm.to_mesh(pm)
            bm.free()
            pob = kit._link(f"p{i}{k}", pm, material=dust_mat)
            pob.visible_shadow = False
            pob.hide_render = True
            ang = (k + rr.uniform(-0.3, 0.3)) / 12 * math.tau
            group.append((pob, ang, rr.uniform(0.7, 1.5), rr.uniform(0.003, 0.0065) * h["size"] ** 0.5))
        puffs.append(group)
    # which desk jumps when hit
    bump = {}
    for i, h in enumerate(HITS):
        if "desk" in h:
            bump[i] = desks[tuple(h["desk"])]
    (ROOT / "work" / "render" / "c2").mkdir(parents=True, exist_ok=True)
    (ROOT / "work" / "render" / "c2_ids.json").write_text(json.dumps(ids))
    # where every object is, so the painter can freeze them one at a time
    objs = []
    for o in sc.collection.objects:
        if o.type == "MESH":
            pts = [o.matrix_world @ Vector(c) for c in o.bound_box]
            lo = [min(p[i] for p in pts) for i in range(3)]
            hi = [max(p[i] for p in pts) for i in range(3)]
            objs.append({"id": o.pass_index, "name": o.name, "lo": lo, "hi": hi})
    (ROOT / "work" / "render" / "c2_objects.json").write_text(json.dumps(objs))
    return sc, cam, sun, slabs, cracks, flakes, puffs, bump


def set_frame(t, sc, cam, sun, slabs, cracks, flakes, puffs, bump):
    eye, target, up = camera_at(t)
    z = (Vector(eye) - Vector(target)).normalized()
    u = Vector(up)
    x = u.cross(z).normalized()
    y = z.cross(x)
    cam.rotation_mode = "QUATERNION"
    cam.matrix_world = Matrix.Translation(eye) @ Matrix((x, y, z)).transposed().to_4x4()
    sun.rotation_mode = "QUATERNION"
    sun.rotation_quaternion = Vector(sun_dir_at(t)).to_track_quat("-Z", "Y")
    FLY = 0.17
    for i, (h, s, c) in enumerate(zip(HITS, slabs, cracks)):
        tin = HIT_T[i]
        if i == 0:
            flat = t >= S2.WORD_FLAT_T
            for ch in s.children:
                ch.hide_render = flat or t < tin - FLY
            if flat:
                s.hide_render = True
                c.hide_render = True
                continue
        e0, t0, u0 = camera_at(tin)
        final = surface_matrix(h, e0, u0)
        if t < tin - FLY:
            s.hide_render = True
            c.hide_render = True
            continue
        s.hide_render = False
        if t >= tin:
            s.matrix_world = final
            s.scale = (1, 1, 1)
            c.hide_render = False
            u_ = min(1.0, (t - tin) / 0.05)
            cs = h["size"] * h.get("crack", 0.55) * (0.4 + 0.6 * u_)
            c.scale = (cs, cs, cs)
        else:
            # flies out from just past the camera, accelerating; stretched along its travel like a drawn smear
            c.hide_render = True
            x_ = (t - (tin - FLY)) / FLY
            ee, tt, uu = camera_at(tin - FLY)
            fwd = (Vector(tt) - Vector(ee)).normalized()
            # starts a good way past the lens, so it never blacks out the frame
            first = i == 0
            start = Vector(ee) + fwd * (0.18 if first else 1.5) + Vector(uu) * (-0.04 if first else -0.25)
            pos = start.lerp(final.translation, x_ ** 2.2)
            # the drawn smear: the block's depth stretched back along its path. The tail never reaches the
            # lens, and shrinks to nothing on arrival, so it reads as a brush drag and not a dark mass.
            remain = (final.translation - pos).length
            depth = max(h["size"] * 0.016, 1e-3)
            from_eye = (pos - Vector(ee)).length
            # (kept short: a longer drag, seen from the side, stops being a word and turns into a ribbon of melted plastic)
            tail = min(remain * 0.14, 0.12 * from_eye, 0.14 * h["size"]) * (1 - x_ ** 3)
            if first:
                tail = min(remain * 0.3, 0.25 * h["size"])
            # In the air the word faces the lens, so it reads as a word coming at us; it only turns to its own angle as it lands.
            # A word flying at its final angle was seen edge-on from up here, and came apart into blue scraps.
            bk = (Vector(ee) - pos).normalized()
            rt = Vector(uu).cross(bk).normalized()
            top = bk.cross(rt)
            q_air = Matrix((rt, top, bk)).transposed().to_quaternion()
            q = final.to_quaternion() if first else q_air.slerp(final.to_quaternion(), S2.smooth(S2.seg(x_, 0.45, 1.0)))
            m = q.to_matrix().to_4x4()
            axis = q @ Vector((0, 0, 1))
            m.translation = pos + axis * (tail * 0.5)
            s.matrix_world = m
            s.scale = (1, 1, 1.0 + tail / (2 * depth))
        # desk jump
    for i, d in bump.items():
        tin = HIT_T[i]
        a = max(0.0, t - tin)
        amp = 0.05 * math.exp(-a * 14) * abs(math.sin(a * 30)) if t >= tin else 0.0
        d[0].location.z = amp
        d[1].location.z = amp * 0.6
    # dust
    for i, group in enumerate(puffs):
        tin = HIT_T[i]
        a = t - tin
        if a < 0 or a > 0.24:
            for ob, *_ in group:
                ob.hide_render = True
            continue
        h = HITS[i]
        e0, t0, u0 = camera_at(tin)
        m = surface_matrix(h, e0, u0)
        x_, y_, z_ = m.col[0].to_3d(), m.col[1].to_3d(), m.col[2].to_3d()
        size = h["size"]
        for ob, ang, speed, r in group:
            ob.hide_render = False
            d = x_ * math.cos(ang) + y_ * math.sin(ang)
            # on an oval just outside the word (which is about 1.2 wide and 0.8 tall, in units of size)
            edge = x_ * (math.cos(ang) * 0.66 * size) + y_ * (math.sin(ang) * 0.46 * size)
            ob.location = m.translation + edge + (d * speed * size + z_ * 0.25 * size) * (a * (1 - a * 1.2))
            sc_ = r * (1 - (a / 0.24) ** 2.5)
            ob.scale = (sc_, sc_, sc_)
    # (snow is painted: paint_c2.snow_mask)


def main():
    args = kit.set_args()
    out = Path(args[0]).resolve()
    out.mkdir(parents=True, exist_ok=True)
    state = build()
    if args[1] == "todo":
        frames = json.loads(Path(args[2]).read_text())
        items = [(T0 + f / 60.0, out / f"f{f:05d}.exr") for f in frames]
    elif args[1] == "all":
        frames = frames_all()
        if len(args) > 3:
            frames = [f for f in frames if int(args[2]) <= f < int(args[3])]
        items = [(T0 + f / 60.0, out / f"f{f:05d}.exr") for f in frames]
    else:
        items = [(float(a), out / f"t{float(a):07.3f}.exr") for a in args[1:]]
    sc = state[0]
    for t, path in items:
        if path.exists():
            continue
        set_frame(t, *state)
        tmp = path.with_suffix(".tmp.exr")
        sc.render.filepath = str(tmp)
        bpy.ops.render.render(write_still=True)
        tmp.rename(path)
        print("RENDERED", path.name, flush=True)


if __name__ == "__main__":
    main()
