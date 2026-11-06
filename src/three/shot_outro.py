"""Outro: the four places again, one set built at a time, in the order of her day. She does something small in each; nobody looks at her."""
import json
import math
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import bpy  # noqa: E402
from mathutils import Matrix, Vector  # noqa: E402
import classroom  # noqa: E402
import kit  # noqa: E402
import setkit  # noqa: E402
import shared_gate as G  # noqa: E402
import shared_outro as S  # noqa: E402
import shot_gate  # noqa: E402
import shot_lockers  # noqa: E402
import shot_train  # noqa: E402

CUT = kit.ROOT / "assets" / "gen" / "cut"
EXTRAS = kit.ROOT / "assets" / "gen" / "extras"
UID_HER = 9900
UID_PAPER = 9910
UID_CURTAIN = 9911
TALL, WIDE = (1024, 1536), (1536, 1024)
LEAN_COL = 283       # the middle of her loafers in the sitting lean


def gate_marks(M):
    """Where the tripods stood: three small worn marks each, and a few dark dents from the sandbags."""
    for i, g in enumerate(G.GEAR):
        r = 0.56 if g["h"] < 1.4 else 0.62
        yaw, _ = G.aim_angles(g)
        for k in range(3):
            a = yaw + g["turn"] + k * 2 * math.pi / 3
            fx, fy = g["x"] + r * math.sin(a), g["y"] + r * math.cos(a)
            ob = kit.cyl("mark", (fx, fy, 0.001), (fx, fy, 0.003), 0.075, kit.mat("gmark3", "#A39C8E", kind=3), seg=10)
            ob.visible_shadow = False


def _caster(ob):
    """Seen by the sun only: what stands out of frame behind the lens and throws its shadow into the shot."""
    ob.visible_camera = False
    return ob


def gate_dress(M):
    """An ordinary afternoon leaves marks: a telegraph pole and its wires, a tree over the wall, a mended road, joints in the pavement, stains under the capping, a notice on the post."""
    rnd = random.Random(41)
    by_name = {}
    for o in bpy.context.scene.collection.objects:
        by_name.setdefault(o.name.split(".")[0], []).append(o)
    # the pole's shadow lies across the road towards the gate; its wires are two thin lines along the road
    _caster(kit.cyl("pole", (-5.6, -9.2, 0.0), (-5.6, -9.2, 8.6), 0.13, M["iron"], seg=8))
    _caster(kit.box("polearm", (-5.6, -9.2, 7.9), (1.5, 0.10, 0.10), M["iron"]))
    for z, dy in ((7.9, 0.0), (7.2, 0.5)):
        _caster(kit.cyl("wire", (-40.0, -13.0 + dy, z), (40.0, -13.4 + dy, z - 0.25), 0.013, M["iron"], seg=4))
    # the tree over the left wall: its leaves lie on the left post and the wall; a second one on the road ahead of her
    # (a dense middle with small leaves round its edge, so the shadow's outline is leaves and not blots; it only reaches the top corner of the post)
    for cx, cy, cz, n, sp in ((-9.2, -6.9, 7.9, 70, 0.95), (-5.2, -12.0, 5.0, 60, 1.05)):
        for k in range(n):
            a, b = rnd.uniform(0, 6.283), rnd.uniform(0, 1)
            rr = sp * b ** 0.5
            size = rnd.uniform(0.07, 0.16) if b > 0.35 else rnd.uniform(0.25, 0.42)
            _caster(setkit.blob("leafshade", (cx + rr * math.cos(a), cy + rr * math.sin(a) * 0.8, cz + rnd.uniform(-0.75, 0.75)), (size, size * 0.8, size * 0.75), M["hedge"]))
    # the road: mended patches, cracks, a white edge line
    mend = kit.mat("gmend", "#BEB7A7")
    for x, y, sx, sy, rot in ((1.9, -4.7, 2.3, 1.05, 0.03), (-2.5, -5.6, 1.4, 0.8, -0.05), (-1.0, -3.1, 1.0, 0.5, 0.02)):
        # the road's own id: a mend is a change of tone, it gets no ink
        pl = kit.plane("mend", (x, y, 0.0042), sx, sy, mend, rot=(0, 0, rot), uid=by_name["road"][0].pass_index)
        pl.visible_shadow = False
    kit.plane("edgeline", (0, -2.55, 0.0046), 300, 0.10, kit.mat("gedge", "#E9E2D0"), uid=by_name["road"][0].pass_index)
    crack = kit.mat("gcrack", "#AAA395", kind=3)
    for x0, y0, n in ((0.9, -3.6, 5), (-1.9, -4.4, 4), (2.8, -6.1, 4), (-3.3, -3.0, 4)):
        pts = [(x0, y0, 0.006)]
        for k in range(n):
            a, b, _ = pts[-1]
            pts.append((a + rnd.uniform(0.16, 0.42) * (1 if x0 > 0 else -1), b + rnd.uniform(-0.13, 0.20), 0.006))
        ob = setkit.tube("crack", pts, 0.0042, crack, seg=4)
        ob.visible_shadow = False
    # pavement joints
    joint = kit.mat("gjoint", "#C4BBA6", kind=3)
    for k in range(-14, 15):
        if abs(k * 0.9) < 40:
            kit.box("joint", (k * 0.9 + 0.2, -0.93, 0.0052), (0.018, 1.74, 0.002), joint).visible_shadow = False
    kit.box("joint", (0, -0.93, 0.0052), (40.0, 0.018, 0.002), joint).visible_shadow = False
    # fallen leaves, gathered along the kerb and the foot of the wall
    leaf = (kit.mat("gleaf0", "#B98A4A", kind=3), kit.mat("gleaf1", "#93A059", kind=3), kit.mat("gleaf2", "#A9703C", kind=3))
    for k in range(70):
        if k % 3:
            x, y = rnd.uniform(-6.0, 6.0), rnd.choice((-1.76, -0.08, -1.92, -0.14)) + rnd.uniform(-0.05, 0.05)
        else:
            x, y = rnd.uniform(-5.0, 5.0), rnd.uniform(-7.5, -2.0)
        w_, h_ = rnd.uniform(0.035, 0.065), rnd.uniform(0.018, 0.03)
        lf = kit.plane("leaf", (x, y, 0.0065), w_, h_, leaf[k % 3], rot=(0, 0, rnd.uniform(0, 3.14)))
        lf.visible_shadow = False
    # the posts: the capping has wept, and the concrete keeps its form-tie holes. Given the post's own id, so they get no ink of their own.
    tone = kit.mat("gpost_weep", "#E2D6BD")
    hole = kit.mat("gpost_hole", "#B5A98F", kind=3)
    for post in by_name["post"]:
        cx = post.location[0]
        for k in range(5):
            x, ln, w_ = cx + rnd.uniform(-0.46, 0.46), rnd.uniform(0.22, 0.72), rnd.uniform(0.035, 0.11)
            st = kit.plane("weep", (x, -0.3006, 2.9 - ln / 2), w_, ln, tone, rot=(math.pi / 2, 0, 0), uid=post.pass_index)
            st.visible_shadow = False
        for r_ in range(3):
            for c_ in range(2):
                ob = kit.cyl("tie", (cx - 0.28 + c_ * 0.56, -0.3006, 0.55 + r_ * 0.9), (cx - 0.28 + c_ * 0.56, -0.3012, 0.55 + r_ * 0.9), 0.014, hole, seg=10, uid=post.pass_index)
                ob.visible_shadow = False
    # a notice and an intercom, the things a school's gate really has
    lp = -(G.DOOR_W / 2 + 0.525)
    note = kit.mat("gnotice", "#F6F3EA", kind=4, tex=setkit.TEX / "gate_notice.png")
    setkit.wall_plane("notice", (lp + 0.05, -0.302, 1.32), 0.46, 0.34, note)
    kit.box("intercom", (lp + 0.40, -0.31, 1.22), (0.09, 0.022, 0.15), kit.mat("gintercom", "#8E8D84"))
    kit.box("intercom_b", (lp + 0.40, -0.323, 1.25), (0.05, 0.004, 0.035), kit.mat("gintercom2", "#3A3D45", kind=3))


def chair_backs(M):
    """A school chair's back is a pressed plywood plate on a steel frame, not a blank board: a grip slot, two pressed lines, rivets into the frame."""
    slot = kit.mat("chair_slot", "#4D3A24", kind=3)
    line = kit.mat("chair_press", "#8F6C3C", kind=3)
    rivet = kit.mat("chair_rivet", "#34363D", kind=3)
    for c in range(classroom.COLS):
        for r in range(classroom.ROWS):
            hx, hy = classroom.desk_pos(c, r)
            y = hy - 0.46 - 0.19 - 0.0085
            for z in (0.655, 0.785):
                kit.box("press", (hx, y, z), (0.33, 0.0015, 0.0045), line).visible_shadow = False
            kit.box("grip", (hx, y, 0.745), (0.115, 0.0015, 0.026), slot).visible_shadow = False
            for sx in (-1, 1):
                for z in (0.675, 0.765):
                    kit.cyl("rivet", (hx + sx * 0.165, y + 0.001, z), (hx + sx * 0.165, y - 0.001, z), 0.0065, rivet, seg=8).visible_shadow = False


def place_shadow(f, p, eye, scale=(1.0, 1.0), shift=(0.0, 0.0)):
    """The card she throws her shadow with starts from the foot on the ground, where the drawing has that foot, not from the column the drawing is pinned by.
    scale: its width and height about that foot, for a place whose camera or walls need the shadow's shape to read. shift: moved along the sun, and up."""
    if f.shadow is None:
        return
    to_eye = Vector((eye[0] - p[0], eye[1] - p[1], 0)).normalized()
    r = Vector((0, 0, 1)).cross(to_eye).normalized()
    sun_h = Vector((f.sun.x, f.sun.y, 0)).normalized()
    pin = Vector(p) + r * ((f.shadow_col - f.col) * f.px) + sun_h * shift[0] + Vector((0, 0, shift[1]))
    m = f.matrix(pin, (-f.sun.x, -f.sun.y), f.shadow_col)
    if scale != (1.0, 1.0):
        loc = Vector(((f.shadow_col - f.img_wh[0] / 2) * f.px, -(f.foot - f.img_wh[1] / 2) * f.px, 0))
        m = m @ Matrix.Translation(loc) @ Matrix.Diagonal((scale[0], scale[1], 1, 1)) @ Matrix.Translation(-loc)
    f.shadow.matrix_world = m


class Drawings:
    """A set of her drawings of which one shows at a time."""

    def __init__(self, sun, table, shadow_scale=(1.0, 1.0), shadow_shift=(0.0, 0.0)):
        self.figs = {}
        self.shadow_scale = shadow_scale
        self.shadow_shift = shadow_shift
        for key, (name, px, row, col, wh, *foot) in table.items():
            self.figs[key] = setkit.Figure(CUT / f"{name}.png", f"her_{key}", px, row, col, sun=sun, img_wh=wh, uid=UID_HER, shadow_col=foot[0] if foot else None)

    def show(self, key, p, eye):
        for k, f in self.figs.items():
            f.show(k == key)
        if key in self.figs:
            self.figs[key].place(p, eye)
            place_shadow(self.figs[key], p, eye, self.shadow_scale, self.shadow_shift)


def other_people(scene):
    """Everybody else in this place: drawings on cards like hers, feet on the floor, in the same sun."""
    figs = {}
    for key, (name, px, row, col, wh, foot) in S.people_table(scene).items():
        figs[key] = setkit.Figure(EXTRAS / f"{name}.png", f"extra_{key}", px, row, col, sun=S.SUNS[scene], img_wh=tuple(wh), uid=UID_HER, shadow_col=foot)

    def place(eye, t):
        now = dict(S.people_at(scene, t))
        for k, f in figs.items():
            f.show(k in now)
            if k in now:
                f.place(now[k], eye)
                place_shadow(f, now[k], eye)
    return place


def walk_table(px=S.WALK_PX):
    # the head stays in the same column in all four; the passing drawings stand a little taller
    # her shadow starts from the foot on the ground
    # Pinned by the very bottom of the sole, or the ground cuts the toe off flat: the two long drawings are a little smaller instead, which keeps her head where it was.
    return {i: (f"o11_walk_{c}", px * k, row, 507, TALL, foot) for i, (c, row, k, foot) in enumerate(zip("abcd", (1503, 1500, 1504, 1500), (0.9775, 1.0, 0.9770, 1.0), (529, 465, 451, 525)))}


def her_train():
    # pinned by the middle of her two loafers, each scaled so her head stays one size
    t = {"sit": ("o03_train_sit", 0.00087, 1489, 283, TALL),
         "lean": ("o33_train_lean", 0.00090, 1489, LEAN_COL, TALL),
         "lean2": ("o33_train_lean2", 0.00092, 1484, 516, TALL),
         "rise": ("o31_train_rise", 0.00092, 1484, 516, TALL),
         "up": ("o34_train_up", 0.00103, 1493, 497, TALL),
         "stand": ("o32_train_stand", 0.00108, 1494, 493, TALL)}
    t.update(walk_table())
    d = Drawings(S.SUNS["train"], t)

    def place(eye, tm):
        key, p = S.train_state(tm)
        d.show(key, p, eye)
    return place


def train_hanging(t, pivots, straps):
    """Everything hanging sways with the running train, leans forward as it brakes, swings back and settles."""
    lean, run = S.train_lean(t)
    s = shot_train.S.sway(t) * run
    for p in pivots:
        p.rotation_euler = (math.radians(8.0) * lean, math.radians(4.5) * s + math.radians(3.5) * lean, 0)
    for o in straps:
        o.rotation_euler = (math.radians(12.0) * lean, math.radians(11.0) * s + math.radians(10.0) * lean, 0)


def her_gate():
    # the lens is so low that a shadow on the road is foreshortened to a hair: a wider one reads as her legs, starting from the sole
    d = Drawings(S.SUNS["gate"], walk_table(), shadow_scale=(1.7, 1.0))
    # what is left of the barrier tape, still tied to the right post: it moves at 12 fps in the same breeze
    m = kit.mat("tape", shot_gate.E_TAPE, kind=4, tex=shot_gate.TEX / "tape.png", repeat=(1, 1))
    n, ln, h = 7, 0.62, 0.20
    items = []
    for i in range(n):
        a, b = i / n * ln, (i + 1) / n * ln
        items.append((((a, 0, -h / 2), (b, 0, -h / 2), (b, 0, h / 2), (a, 0, h / 2)),
                      ((1.6 - a / 1.6, 0), (1.6 - b / 1.6, 0), (1.6 - b / 1.6, 1), (1.6 - a / 1.6, 1))))
    scrap = setkit.quads("scrap", items, m)
    x0 = G.DOOR_W / 2 + 0.005

    def flutter(t):
        k = S.scrap_tick(t)
        me = scrap.data
        vs = me.vertices
        for j in range(n):
            for e, q in ((j, (0, 3)), (j + 1, (1, 2))):
                u = e / n
                # it hangs out from the knot, sagging, and the far end lifts and flaps
                wave = math.sin(k * 1.9 - e * 1.15) * u * u
                x = x0 - ln * u * (0.96 - 0.10 * u)
                y = -0.325 + 0.17 * math.sin(k * 0.8 - e * 0.5) * u + 0.05 * wave
                zc = 1.42 - 0.34 * u * u + 0.10 * wave
                for qq, dz in zip(q, (-h / 2, h / 2)):
                    vs[j * 4 + qq].co = (x, y, zc + dz * (1 - 0.15 * u))
        me.update()

    def place(eye, t):
        key, p = S.gate_at(t)
        d.show(key, p, eye)
        flutter(t)
    return place


def her_lockers(M):
    # each drawing has its own scale and is pinned by the toe that is on the board
    t = {k: (nm, px, row, col, WIDE) for k, (nm, px, row, col) in S.LOCK_DRAW.items()}
    for key, nm, row, col, _ in S.LOCK_WALK_DRAW:
        t[key] = (nm, S.LOCK_PX, row, col, WIDE)
    d = Drawings(S.SUNS["lockers"], t, shadow_shift=(S.LOCK_SHADOW_D, S.LOCK_SHADOW_Z))
    shoes = shot_lockers.HerLoafers(M)

    def place(eye, tm):
        key, p = S.lockers_state(tm)
        d.show(key, p, eye)
        shoes.place(eye, S.loafers_home(tm))
    return place


CUR_W, CUR_Z0, CUR_Z1 = 0.74, 0.86, 2.40


def curtain(M, yc):
    """The gathered curtain, as a real sheet of folds, so the wind can take it. One mesh per curtain, moved by hand."""
    nu, nv = 24, 7
    verts = [(0.0, 0.0, 0.0)] * ((nu + 1) * (nv + 1))
    faces = [(i * (nv + 1) + j, (i + 1) * (nv + 1) + j, (i + 1) * (nv + 1) + j + 1, i * (nv + 1) + j + 1) for i in range(nu) for j in range(nv)]
    me = bpy.data.meshes.new("curtain")
    me.from_pydata(verts, [], faces)
    me.update()
    ob = kit._link("curtain", me, (0, 0, 0), (0, 0, 0), M["curtain"], uid=UID_CURTAIN)

    def pose(t):
        g = S.gust_at(t)
        tk = math.floor(t * 12 + 1e-6)
        for i in range(nu + 1):
            u = i / nu
            for j in range(nv + 1):
                v = j / nv        # 0 at the bottom, 1 at the rail
                free = (1 - v) ** 1.7
                # gathered folds, opening out when the wind fills it
                fold = 0.032 * math.sin(u * 18.85) * (1 + 0.5 * g * free)
                reach = g * free * (0.40 + 0.07 * math.sin(tk * 1.3 + u * 5.0)) + g * 0.05 * math.sin(tk * 2.1 + v * 7.0 + u * 3.0) * free
                spread = 1 + 0.25 * g * free
                x = classroom.X0 + 0.13 + fold + reach
                y = yc + (u - 0.5) * CUR_W * spread + g * free * 0.10 * math.sin(tk * 0.9 + v * 3.0)
                z = CUR_Z0 + (CUR_Z1 - CUR_Z0) * v + g * free * 0.14
                me.vertices[i * (nv + 1) + j].co = (x, y, z)
        me.update()
    return pose


DESK_SHADE = "#B9843F"    # the desk top in shadow: what lies on the desk darkens it to this


def paper_on_desk(hx, hy):
    """The sheet on her desk. Its far corner lifts in the wind; a small grid so it bends rather than tilts. Under it, its own hard shadow, moved with it: a sliver along the edge while it
    lies flat, which is all that says it is a sheet lying on a desk and not printed on it, and a real shape once the corner is up."""
    x0, y0 = hx - 0.05, hy - 0.17     # near corner: the sheet lies on the right half of the desk, a little askew
    w, l, rot = 0.21, 0.297, -0.10
    nu, nv = 5, 6
    z = 0.7155 + 0.0015
    co, si = math.cos(rot), math.sin(rot)
    verts = []
    for i in range(nu + 1):
        for j in range(nv + 1):
            a, b = w * i / nu, l * j / nv
            verts.append((x0 + a * co - b * si, y0 + a * si + b * co, z))
    faces = [(i * (nv + 1) + j, (i + 1) * (nv + 1) + j, (i + 1) * (nv + 1) + j + 1, i * (nv + 1) + j + 1) for i in range(nu) for j in range(nv)]
    me = bpy.data.meshes.new("paper")
    me.from_pydata(verts, [], faces)
    me.update()
    ob = kit._link("paper", me, (0, 0, 0), (0, 0, 0), kit.mat("form_paper", "#F8F6EE", kind=0), uid=UID_PAPER)
    me2 = me.copy()
    ob2 = kit._link("paper_shadow", me2, (0, 0, 0), (0, 0, 0), kit.mat("paper_shade", DESK_SHADE, kind=3))
    ob2.visible_shadow = False
    sun = S.SUNS["classroom"]
    kx, ky = sun[0] / -sun[2], sun[1] / -sun[2]
    base = [tuple(v.co) for v in me.vertices]

    def pose(t):
        lift = S.paper_lift(t)
        for i in range(nu + 1):
            for j in range(nv + 1):
                u, v = 1 - i / nu, j / nv      # the corner nearest the window and the board comes up
                d = max(0.0, u + v - 0.9)
                n = i * (nv + 1) + j
                h = lift * 0.10 * d * d
                me.vertices[n].co.z = z + h
                # how far the sun carries that point's shadow along the desk; never less than what shows the sheet's own thickness
                x0, y0, _ = base[n]
                me2.vertices[n].co = (x0 + kx * (h + 0.0028), y0 + ky * (h + 0.0028) - 0.0035, z - 0.0009)
        me.update()
        me2.update()
    return pose


def pen_on_desk(M, hx, hy):
    """Her pen, round enough to read at this size, with a clip and its shadow on the desk."""
    a, b = (hx - 0.20, hy + 0.13, 0.7225), (hx - 0.06, hy + 0.08, 0.7225)
    kit.cyl("pen", a, b, 0.0068, M["dark"], seg=8)
    kit.cyl("pen_cap", a, (a[0] + (b[0] - a[0]) * 0.34, a[1] + (b[1] - a[1]) * 0.34, a[2]), 0.0078, kit.mat("pen_cap", "#3A5A86"), seg=8)
    sun = S.SUNS["classroom"]
    dx, dy = 0.0138 * sun[0] / -sun[2], 0.0138 * sun[1] / -sun[2]
    q = ((a[0] + dx, a[1] + dy - 0.006, 0.7158), (b[0] + dx, b[1] + dy - 0.006, 0.7158), (b[0], b[1] + 0.004, 0.7158), (a[0], a[1] + 0.004, 0.7158))
    setkit.quads("pen_shadow", [(q, ((0, 0), (1, 0), (1, 1), (0, 1)))], kit.mat("paper_shade", DESK_SHADE, kind=3)).visible_shadow = False


def her_room(M):
    hx, hy = classroom.desk_pos(*classroom.HER)
    # the bottom edge of each picture is the small of her back, behind the chair; the rows put her elbow on the desk top
    px = 0.00056
    low = 0.77 / px
    chin = (px, 1023 + low, 768, WIDE)
    mid = (px, 1023 + low, 704, WIDE)
    press = (px, 940 + low, 653, (1672, 941))
    t = {"chin": ("o51_desk_chin", *chin), "wa": ("o54_wind_a", *chin), "wb0": ("o54_wind_b0", *chin), "wb1": ("o54_wind_b1", *chin), "wb2": ("o54_wind_b2", *chin), "wc": ("o54_wind_c", *chin),
         "tblown": ("o58_turn_blown", *chin), "mblown": ("o58_mid_blown", *mid),
         "pblown": ("o58_press_blown", *press), "pwa": ("o57_press_wind_a", *press), "phalf": ("o58_press_half", *press), "pwb": ("o57_press_wind_b", *press), "press": ("o53_desk_press", *press)}
    d = Drawings(S.SUNS["classroom"], t)
    poses = [curtain(M, y) for y in (3.25, 5.0, 6.3)]
    poses.append(paper_on_desk(hx, hy))

    def place(eye, tm):
        d.show(S.desk_drawing(tm), S.HER_ROOM, eye)
        for f in poses:
            f(tm)
    return place


def build_scene(i):
    name = S.SCENES[i]
    sc = kit.reset()
    kit.setup_render(sc, 1920, 1080, ss=S.SS, fps=60, samples=3, threads=12)
    sc.render.use_persistent_data = False
    swing = None
    if name == "gate":
        M = shot_gate.materials(True)
        shot_gate.build_set(M, warm=True)
        gate_marks(M)
        gate_dress(M)
        place = her_gate()
    elif name == "lockers":
        M = shot_lockers.build_set(True)
        # the two duckboards are pushed together here, so the shoes she left have a floor under them
        for k in range(6):
            kit.box("slat", (2.45, -0.62 - 0.3 + k * 0.12, 0.05), (0.198, 0.09, 0.02), M["duck"])
        place = her_lockers(M)
    elif name == "train":
        swing = shot_train.build_set(True)
        place = her_train()
    else:
        M = classroom.materials()
        classroom.shell(M, include_ceiling=True)
        classroom.front_wall(M)
        classroom.rear_wall(M)
        classroom.corridor_wall(M)
        classroom.ceiling_fixtures(M)
        # every desk and chair squared up
        for c in range(classroom.COLS):
            for r in range(classroom.ROWS):
                classroom.desk(M, c, r, f"desk_{c}_{r}", fixed=True)
        # the set's own gathered curtains are boxes: these are replaced by sheets that can move
        for o in list(sc.collection.objects):
            if o.name.startswith("cur") and o.name != "curtain":
                bpy.data.objects.remove(o)
        hx, hy = classroom.desk_pos(*classroom.HER)
        # her bag on the desk's hook, and her pen on the desk
        kit.box("bag", (hx + 0.365, hy - 0.05, 0.47), (0.07, 0.34, 0.25), kit.mat("her_bag", "#26304F"))
        kit.cyl("bag_strap", (hx + 0.34, hy - 0.05, 0.66), (hx + 0.36, hy - 0.13, 0.58), 0.006, M["dark"], seg=5)
        kit.cyl("bag_strap", (hx + 0.34, hy - 0.05, 0.66), (hx + 0.36, hy + 0.03, 0.58), 0.006, M["dark"], seg=5)
        pen_on_desk(M, hx, hy)
        # the rail the curtains hang from
        kit.box("rail", (classroom.X0 + 0.13, classroom.D / 2, CUR_Z1 + 0.015), (0.03, classroom.D - 0.4, 0.03), M["alu"])
        # her chair's top edge drawn as one clean line, since a line right beside her card would be broken up by the painter
        cap = kit.box("chair_top_line", (hx, hy - 0.46 - 0.19 - 0.009, 0.822), (0.372, 0.006, 0.009), kit.mat("chair_line", "#17171D", kind=3))
        cap.visible_shadow = False
        chair_backs(M)
        place = her_room(M)
    people = other_people(name)
    kit.sun(sc, S.SUNS[name])
    cam = kit.camera(sc, lens=S.LENSES[name], clip_end=3000)

    def place_all(eye, t):
        place(eye, t)
        people(eye, t)
    return sc, cam, place_all, swing


def write_ids():
    ids = {"her": UID_HER, "paper": UID_PAPER, "curtain": UID_CURTAIN, "gate": shot_gate.lit_ids(), "train": {"win": list(shot_train.UID_WIN), "end": shot_train.UID_END},
           "lockers": {"her_plate": shot_lockers.UID_HER_PLATE, "her_shoes": shot_lockers.UID_HER_SHOES}}
    (kit.ROOT / "work" / "render" / "outro_ids.json").write_text(json.dumps(ids))


def main():
    args = kit.set_args()
    out = Path(args[0]).resolve()
    out.mkdir(parents=True, exist_ok=True)
    write_ids()
    if args[1] == "todo":
        frames = json.loads(Path(args[2]).read_text())
        items = [(S.T0 + f / 60.0, out / f"f{f:05d}.exr") for f in frames]
    else:
        items = [(float(a), out / f"t{float(a):07.3f}.exr") for a in args[1:]]
    items.sort(key=lambda it: it[0])
    state, current = None, None
    for t, path in items:
        if path.exists():
            continue
        i = S.scene_index(t)
        if i != current:
            state = build_scene(i)
            current = i
        sc, cam, place, swing = state
        eye, tg, up = S.camera_at(t)
        setkit.set_camera(cam, eye, tg, up, lens=S.lens_at(t))
        place(eye, t)
        if swing:
            train_hanging(t, *swing)
        tmp = path.with_suffix(".tmp.exr")
        sc.render.filepath = str(tmp)
        bpy.ops.render.render(write_still=True)
        tmp.rename(path)
        print("RENDERED", path.name, flush=True)


if __name__ == "__main__":
    main()
