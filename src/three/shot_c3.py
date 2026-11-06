"""Clip 3: she has been sitting in the frozen room all along. The camera backs away until she is a dot on a map."""
import json
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import bpy  # noqa: E402
from mathutils import Matrix, Vector  # noqa: E402
import city  # noqa: E402
import classroom  # noqa: E402
import kit  # noqa: E402
import shared_c2 as C2  # noqa: E402
import shared_c3 as S  # noqa: E402
import shot_c2 as SC2  # noqa: E402

ROOT = kit.ROOT
CHAR = ROOT / "assets" / "gen" / "final" / "p02_seated_high.png"
# Under the slow push she does not stay stiff: her head sinks a little on the bar's middle beat and stays down. Same pose, seat and framing;
# (picture, from this song time). HER_CARDS holds the cards, each with the same id as the first, so the painter treats them alike.
BOWS = ((ROOT / "assets" / "gen" / "final" / "p24_seated_half.png", 86.18), (ROOT / "assets" / "gen" / "final" / "p23_seated_bow.png", 86.31))
HER_CARDS = []
# metres per image pixel; the figure is 1485 px tall from bow to shoes
PX = 0.00095
LAP_PX = 950           # image row at the lap
IMG_W, IMG_H = 1024, 1536
CEILING = []
# The word that stood on the desk straight behind her: seen edge-on from this end of the room it grew out of her head, and its crack stuck out either side of her neck.
# It stands on a desk well to the side instead, turned to this shot's lens. Nothing stands behind her, in line with the camera.
MOVED = {3: dict(p=(*C2.desk_xy(3, 4), 0.725), size=0.85, face=(-0.8, 9.0, 1.6))}


def char_material():
    return kit.mat("her", "#FFFFFF", kind=2, tex=CHAR, alpha_tex=True)


def facing_matrix(center, forward, up_hint):
    f = Vector(forward).normalized()
    r = Vector(up_hint).cross(f).normalized()
    u = f.cross(r)
    m = Matrix((r, u, f)).transposed().to_4x4()
    m.translation = Vector(center)
    return m


def page_shadow():
    """One unbroken hard shadow beside the newspaper on the desk top: the page's outline slid away from the sun, cut off
    at the desk's edge where a corner hangs over."""
    ca, sa = math.cos(C2.PAGE_ANGLE), math.sin(C2.PAGE_ANGLE)
    hw, hh = C2.PAGE_W * 0.503, C2.PAGE_H * 0.506
    slide = (0.04, -0.02)   # along the sun; the +x side hangs over the edge, so it is the far edge that shows it
    poly = [(C2.PAGE_C[0] + dx * ca - dy * sa + slide[0], C2.PAGE_C[1] + dx * sa + dy * ca + slide[1]) for dx, dy in ((-hw, -hh), (hw, -hh), (hw, hh), (-hw, hh))]
    dx, dy = C2.her_desk()
    for axis, limit, keep_lo in ((0, dx - 0.31, False), (0, dx + 0.31, True), (1, dy - 0.22, False), (1, dy + 0.22, True)):
        out = []
        for a, b in zip(poly, poly[1:] + poly[:1]):
            ina = a[axis] <= limit if keep_lo else a[axis] >= limit
            inb = b[axis] <= limit if keep_lo else b[axis] >= limit
            if ina:
                out.append(a)
            if ina != inb:
                k = (limit - a[axis]) / (b[axis] - a[axis])
                out.append((a[0] + (b[0] - a[0]) * k, a[1] + (b[1] - a[1]) * k))
        poly = out
    me = bpy.data.meshes.new("page_shadow")
    me.from_pydata([(x, y, 0.7154) for x, y in poly], [], [tuple(range(len(poly)))])
    me.update()
    ob = kit._link("page_shadow", me, material=kit.mat("page_shadow", "#A3C0D9", kind=3))
    ob.visible_shadow = False


def build():
    sc = kit.reset()
    kit.setup_render(sc, 1920, 1080, ss=S.SS, fps=60, samples=3, threads=12)
    sc.render.use_persistent_data = True
    sc.render.film_transparent = True
    M, desks = classroom.build(ceiling=False)
    # The chair of the desk in front of hers stood between the lens and her and read as her own chair. It has been pulled
    # out into the aisle and left there, so what is under her is her own chair and her feet on the floor.
    fx, fy = classroom.desk_pos(classroom.HER[0], classroom.HER[1] - 1)
    front_chair = desks[(classroom.HER[0], classroom.HER[1] - 1)][1]
    front_chair.location = (fx + 0.62, fy - 0.30, 0.42)
    front_chair.rotation_euler = (0, 0, -0.55)
    # Nothing stands straight behind her in this push either: the post of the chair one row back ran down the edge of her hair as a broken line, and a bag left in a cubby sat behind her bow like a box on her head.
    # The chair has been left out in the aisle and the bag lies a few cubbies along. Same objects, same ids.
    back_chair = desks[(classroom.HER[0], classroom.HER[1] + 1)][1]
    back_chair.location = (back_chair.location.x + 0.80, back_chair.location.y + 0.06, back_chair.location.z)
    back_chair.rotation_euler = (0, 0, 0.45)
    bpy.data.objects["bag"].location.x += 3 * 0.46
    sun = kit.sun(sc, S.SUN)
    cam = kit.camera(sc, lens=S.LENS, clip_end=40000)
    # her newspaper, and everything the last clip nailed up
    page, under = classroom.newspaper(C2.PAGE_C, C2.PAGE_W, C2.PAGE_H, C2.PAGE_ANGLE, kit.mat("page", "#EDE7D3", kind=4), kit.mat("page_under", "#DDD6C0", kind=4))
    ids = {"page": page.pass_index, "under": under.pass_index, "board": bpy.data.objects["board"].pass_index}
    page_shadow()
    crack_mat = kit.mat("crack", "#17171D", kind=4)
    e_last, _, u_last = C2.camera_at(C2.HIT_T[-1])
    for i, h in enumerate(C2.HITS):
        h = {**h, **MOVED.get(i, {})}
        # blocks that would stand between the camera and her are left out of this angle. The word on her newspaper is
        # printed flat on the page from this angle (paint_c3): a thin block seen this low is only ink and side
        if i in (0, 1, 4, 10, 11):
            continue
        if abs(h["p"][0] - S.HER_XY[0]) < 1.5 and h["p"][1] > S.HER_XY[1] and h["p"][2] < 1.0:
            continue
        e0, _, u0 = C2.camera_at(C2.HIT_T[i])
        s = SC2.make_slab(i, h)
        s.matrix_world = SC2.surface_matrix(h, e0, u0)
        # a crack stops at the edge of what it cracks, as in clip 2: past a desk's edge it is a black line in the air, and past the window's rails it runs on over the wall
        c = SC2.crack_mesh(i, 100 + i, crack_mat, SC2.desk_limit(h) if h.get("on_desk") else SC2.window_limit(h) if h["n"][0] > 0.5 else None)
        n = Vector(h["n"]).normalized()
        c.rotation_mode = "QUATERNION"
        c.rotation_quaternion = n.to_track_quat("Z", "Y")
        c.location = Vector(h["p"]) + n * 0.006
        c.scale = (h["size"] * h.get("crack", 0.55),) * 3
    # falling snow
    import bmesh
    import random
    r = random.Random(5)
    bm = bmesh.new()
    placed = 0
    while placed < 900:
        x, y, z = r.uniform(-3.7, 3.7), r.uniform(0.1, 9.1), r.uniform(0, 3.0)
        # nothing between the lens and her
        if -3.8 < x < 1.6 and 2.4 < y < 9.2:
            continue
        placed += 1
        bmesh.ops.create_icosphere(bm, subdivisions=2, radius=r.uniform(0.006, 0.015), matrix=Matrix.Translation((x, y, z)))
    me = bpy.data.meshes.new("snow")
    bm.to_mesh(me)
    bm.free()
    snow_mat = kit.mat("snow_chip", "#FBFDFF", kind=3)
    flakes = [kit._link("snow_a", me, (0, 0, 0), material=snow_mat), kit._link("snow_b", me.copy(), (0, 0, 3.0), material=snow_mat)]
    for f in flakes:
        f.visible_shadow = False
    # her: a card that always faces the camera, plus an unseen card facing the sun that casts her shadow
    mat_her = char_material()
    w, h_ = IMG_W * PX, IMG_H * PX
    her = kit.plane("her", (0, 0, 0), w, h_, mat_her)
    her.visible_shadow = False
    ids["her"] = her.pass_index
    shadow = kit.plane("her_shadow", (0, 0, 0), w, h_, mat_her)
    shadow.visible_camera = False
    # her shadow card stands where she sits and faces the sun
    sun_v = Vector(S.SUN).normalized()
    fwd = (-sun_v).normalized()
    shadow.matrix_world = facing_matrix((S.HER_XY[0], S.HER_XY[1] - 0.05, 0.66), fwd, (0, 0, 1))
    # a soft-less contact patch under her shoes, in the tone of the room's shadow, so her feet stand on the floor
    contact = kit.cyl("contact", (S.HER_XY[0], S.HER_XY[1] + 0.08, 0.004), (S.HER_XY[0], S.HER_XY[1] + 0.08, 0.006), 0.11,
                      kit.mat("contact", "#A3C0D9", kind=3), seg=24)
    contact.visible_shadow = False
    contact.scale = (1.35, 0.62, 1.0)
    city.build_school()
    keep_out = {her.name, shadow.name}
    school_objs = [o for o in sc.collection.objects if o.parent is None and o.type in ("MESH", "EMPTY") and o.name not in keep_out]
    town, ground = city.build_town(school_box=(-85, 45, -70, 110))
    # the school and the room inside it press flat with the town when it turns into a map
    root = bpy.data.objects.new("press", None)
    sc.collection.objects.link(root)
    root.location = (0, 0, city.GROUND)
    bpy.context.view_layer.update()
    inv = root.matrix_world.inverted()
    for o in school_objs:
        o.parent = root
        o.matrix_parent_inverse = inv
    sky = bpy.data.objects["sky"]
    ids["town"] = town.pass_index
    # the push from the far end of the room looks up under the ceiling. Only the camera sees it, and only before the
    # first word, so the light and everything after that stay as they were. Made last, so no other object's id moves.
    before = set(sc.collection.objects)
    kit.box("ceil_push", (0, classroom.D / 2, classroom.H + 0.1), (classroom.W + 0.4, classroom.D + 0.4, 0.2), M["ceil"])
    classroom.ceiling_fixtures(M)
    for o in set(sc.collection.objects) - before:
        o.visible_shadow = False
        CEILING.append(o)
    # the bowed pictures: made last, so no other object's id moves
    HER_CARDS.append((her, S.T0))
    for k, (pic, t_from) in enumerate(BOWS):
        card = kit.plane(f"her_bow{k}", (0, 0, 0), w, h_, kit.mat(f"her_bow{k}", "#FFFFFF", kind=2, tex=pic, alpha_tex=True), uid=her.pass_index)
        card.visible_shadow = False
        HER_CARDS.append((card, t_from))
    (ROOT / "work" / "render").mkdir(parents=True, exist_ok=True)
    (ROOT / "work" / "render" / "c3_ids.json").write_text(json.dumps(ids))
    return sc, cam, her, root, town, sky, flakes


def set_frame(t, sc, cam, her, root, town, sky, flakes):
    for o in CEILING:
        o.hide_render = t >= S.HIT_T[0]
    eye, target, up = S.camera_at(t)
    z = (Vector(eye) - Vector(target)).normalized()
    x = Vector(up).cross(z).normalized()
    y = z.cross(x)
    cam.rotation_mode = "QUATERNION"
    cam.matrix_world = Matrix.Translation(eye) @ Matrix((x, y, z)).transposed().to_4x4()
    # her card is perpendicular to the view axis through her, tilted to face the camera
    el = math.radians(S.elevation_at(t))
    az = math.radians(S.azimuth_at(t))
    n = Vector((math.cos(el) * math.sin(az), math.cos(el) * math.cos(az), math.sin(el)))
    up_h = Vector((0, 0, 1))
    r = up_h.cross(n).normalized()
    u = n.cross(r)
    # the lap stays fixed in the chair; the rest of the card hangs from there. The lap is below the image's
    # centre, so the centre of the card is above the lap, and then her shoes reach the floor.
    lap_to_center = (LAP_PX - IMG_H / 2) * PX
    lap = Vector((S.HER_XY[0], S.HER_XY[1], 0.55))
    center = lap + u * lap_to_center
    m = Matrix((r, u, n)).transposed().to_4x4()
    m.translation = center
    sky.hide_render = eye[2] > 3.15
    # the small mark takes over from the figure (see clips/c3.py)
    gone = 1.2 / S.distance_at(t) * (S.LENS / 36) * 1920 < S.ICON_AT - 40
    now = [card for card, t_from in HER_CARDS if t >= t_from][-1]
    for card, _ in HER_CARDS:
        card.matrix_world = m
        card.hide_render = gone or card is not now
    fl = S.flatten_at(t)
    root.scale = (1, 1, max(min(fl, 1.0), 1e-3))
    for f in flakes:
        f.hide_render = t > S.STOP
    fall = -(t - S.T0) * 0.55
    for k, f in enumerate(flakes):
        f.location.z = (fall + 3.0 * k) % 6.0 - 3.0
    city.set_mapmix(S.mapmix_at(t), S.flatten_at(t), town)


def main():
    args = kit.set_args()
    out = Path(args[0]).resolve()
    out.mkdir(parents=True, exist_ok=True)
    state = build()
    if args[1] == "todo":
        frames = json.loads(Path(args[2]).read_text())
        items = [(S.T0 + f / 60.0, out / f"f{f:05d}.exr") for f in frames]
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
