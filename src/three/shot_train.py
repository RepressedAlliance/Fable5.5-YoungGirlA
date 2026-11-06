"""A train carriage in the rain, full. Weekly magazine ads with her picture hang the whole length of it, all swinging together, and everyone below them has her in their hands."""
import json
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import bmesh  # noqa: E402
import bpy  # noqa: E402
import crowdkit  # noqa: E402
import kit  # noqa: E402
import setkit  # noqa: E402
from kit import box, cyl, mat, plane  # noqa: E402
from setkit import TEX, tube  # noqa: E402
import shared_crowd as C  # noqa: E402
import shared_train as S  # noqa: E402

UID_WIN = (9201, 9202)
UID_END = 9203

# on the right of each row the photo is towards the aisle, clear of the straps: the two the close-ups look at hang there
HER_ADS = [f"ad_her_{i:02d}" for i in (1, 0, 3, 2, 5, 4, 7, 6, 9, 8)]
# the ordinary world's ads: nothing about her any more
OTHER_ADS = ["ad_other_onsen", "ad_other_soda", "ad_other_english", "ad_other_condo", "ad_other_movie"]


def materials(warm):
    wc = (lambda a, b: b if warm else a)
    return {
        "wall": mat("twall", wc("#ECE9DC", "#F1E7D1")),
        "low": mat("tlow", wc("#DEDBCD", "#E7DAC0")),
        "floor": mat("tfloor", wc("#8E979B", "#A69D90")),
        "strip": mat("tstrip", wc("#A7AEB0", "#BDB2A0")),
        "seat": mat("tseat", wc("#1B86AD", "#2F93AC")),
        "seat_d": mat("tseat_d", wc("#136A8C", "#21768D")),
        "under": mat("tunder", "#4A4F58"),
        "side": mat("tside", wc("#D3D3C6", "#DDD0B6")),
        "steel": mat("tsteel", "#B4BBBD"),
        "door": mat("tdoor", wc("#C5CBCB", "#D3CAB8")),
        "doorline": mat("tdoorline", "#5F666C"),
        "yellow": mat("tyellow", "#FEE45F"),
        "ceil": mat("tceil", wc("#F2F0E6", "#F4EEDE"), kind=1),
        "cove": mat("tcove", wc("#E6E4D8", "#EFE6D2"), kind=1),
        "lamp": mat("tlamp", "#FEFDF6", kind=1),
        "vent": mat("tvent", "#C9CCC6", kind=1),
        "ventline": mat("tventline", "#8E9396", kind=1),
        "rack": mat("track", "#A9B0B3"),
        "band": mat("tband", wc("#EDEBE0", "#EDE5D0")),
        "ring": mat("tring", "#F6F3EA"),
        "rail": mat("trail", "#AEB5B8"),
        "win": mat("twin", "#3F5A78", kind=5),
        "end": mat("tend", wc("#3B5573", "#CDE9F2"), kind=5),
        "dark": mat("tdark", "#24262C"),
        "sticker": mat("tsticker", "#F6F3EA"),
    }


def pipe(name, a, b, r, material):
    """A round pipe, shaded round: its facets must not pick up ink of their own."""
    ob = cyl(name, a, b, r, material, seg=10)
    for pg in ob.data.polygons:
        pg.use_smooth = True
    return ob


def side(M, s):
    """One long wall with real window openings, doors in it, seats and racks along it."""
    xw = s * (S.HW + 0.03)
    # a continuous sill and head, cut only at the doors
    cuts = [0.0]
    for a, b in S.DOORS:
        cuts += [a, b]
    cuts.append(S.LEN)
    for i in range(0, len(cuts), 2):
        a, b = cuts[i], cuts[i + 1]
        box("low", (xw, (a + b) / 2, 0.45), (0.06, b - a, 0.90), M["low"])
        box("sill", (s * (S.HW - 0.01), (a + b) / 2, 0.905), (0.05, b - a, 0.022), M["steel"])
        # piers between the windows
        n = max(1, int(round((b - a) / 1.75)))
        for k in range(n + 1):
            y = a + (b - a) * k / n
            box("pier", (xw, y, 1.36), (0.06, 0.22, 0.92), M["wall"])
        for k in range(n):
            y = a + (b - a) * (k + 0.5) / n
            box("sash", (xw, y, 1.36), (0.03, 0.035, 0.92), M["steel"])
        box("sash_h", (xw, (a + b) / 2, 1.62), (0.03, b - a, 0.025), M["steel"])
    box("head", (xw, S.LEN / 2, 1.93), (0.06, S.LEN, 0.22), M["wall"])
    # doors: two stainless leaves, each with a tall pane; a yellow strip at the threshold; a line where they meet
    for a, b in S.DOORS:
        c = (a + b) / 2
        leaf = (b - a) / 2
        for sgn in (-1, 1):
            cy = c + sgn * leaf / 2
            box("leaf_low", (s * S.HW, cy, 0.47), (0.04, leaf - 0.01, 0.94), M["door"])
            box("leaf_top", (s * S.HW, cy, 1.91), (0.04, leaf - 0.01, 0.26), M["door"])
            box("leaf_edge", (s * S.HW, cy + sgn * (leaf / 2 - 0.08), 1.36), (0.04, 0.14, 0.86), M["door"])
            box("leaf_edge", (s * S.HW, cy - sgn * (leaf / 2 - 0.08), 1.36), (0.04, 0.14, 0.86), M["door"])
        box("door_gap", (s * (S.HW - 0.022), c, 1.02), (0.006, 0.012, 2.04), M["doorline"])
        plane("threshold", (s * (S.HW - 0.18), c, 0.004), 0.36, b - a, M["yellow"])
        # a notice stuck to each leaf, and the door's own small screen above it
        box("door_note", (s * (S.HW - 0.024), a + 0.32, 1.02), (0.004, 0.16, 0.16), M["sticker"])
        box("door_note", (s * (S.HW - 0.024), b - 0.32, 1.02), (0.004, 0.16, 0.16), M["sticker"])
        box("door_screen", (s * (S.HW - 0.03), c, 2.0), (0.02, 0.6, 0.14), M["dark"])
    # benches
    for a, b in S.BENCHES:
        c, ln = (a + b) / 2, b - a
        box("seat", (s * 1.16, c, 0.405), (0.50, ln, 0.10), M["seat"])
        box("seatback", (s * (S.HW - 0.045), c, 0.68), (0.07, ln, 0.44), M["seat"])
        box("under", (s * 1.2, c, 0.18), (0.40, ln, 0.34), M["under"])
        n = int(ln / 0.46)
        for k in range(1, n):
            y = a + ln * k / n
            box("seat_line", (s * 1.14, y, 0.457), (0.46, 0.012, 0.004), M["seat_d"])
            box("seat_line", (s * (S.HW - 0.082), y, 0.68), (0.004, 0.012, 0.42), M["seat_d"])
        for yy in (a, b):
            if 0.5 < yy < S.LEN - 0.3:
                # the seat end: a bent grab pipe, not a wall
                ya = yy
                pipe("end_rail", (s * 1.40, ya, 0.78), (s * 0.86, ya, 0.78), 0.016, M["rail"])
                box("side_panel", (s * 1.16, ya, 0.40), (0.50, 0.03, 0.12), M["side"])
                pipe("stanchion", (s * 0.86, yy, 0.0), (s * 0.86, yy, S.STRAP_Z), 0.018, M["rail"])
        # the rack above the seats: rods along, brackets across
        for k in range(4):
            box("rack_rod", (s * (S.HW - 0.05 - k * 0.09), c, 1.86), (0.012, ln - 0.1, 0.012), M["rack"]).visible_shadow = False
        n = max(2, int(ln / 1.4))
        for k in range(n + 1):
            y = a + 0.05 + (ln - 0.1) * k / n
            box("rack_arm", (s * (S.HW - 0.17), y, 1.875), (0.36, 0.02, 0.02), M["rack"]).visible_shadow = False
    # sky and passing things are painted on this, right outside the glass
    side_uid = UID_WIN[0] if s < 0 else UID_WIN[1]
    plane("window", (s * (S.HW + 0.08), S.LEN / 2, 1.3), S.LEN + 4, 2.4, M["win"], rot=(math.pi / 2, 0, math.pi / 2), uid=side_uid)


def cove(M, s, warm):
    """The slope from the wall head to the ceiling, with its row of long ads."""
    x0, z0, x1, z1 = s * S.HW, 2.04, s * 0.80, S.CEIL
    kit.box("wallhead", (s * (S.HW + 0.005), S.LEN / 2, 2.03), (0.03, S.LEN, 0.04), M["wall"])
    setkit.quads("cove", [(((x0, 0, z0), (x1, 0, z1), (x1, S.LEN, z1), (x0, S.LEN, z0)), ((0, 0), (1, 0), (1, 1), (0, 1)))], M["cove"])
    names = [f"long_other_{i}" for i in range(3)] if warm else [f"long_her_{i}" for i in range(6)]
    ln, h = 0.92, 0.23
    y = 0.8
    i = 0
    nx, nz = x1 - x0, z1 - z0
    d = math.hypot(nx, nz)
    nx, nz = nx / d, nz / d
    # a little in front of the slope, so it does not fight it
    off = (-nz * s * -1 * 0.004, 0.004)
    while y < S.LEN - 1:
        m = kit.mat(f"long_{names[i % len(names)]}", "#FFFFFF", kind=1, tex=TEX / f"{names[i % len(names)]}.png")
        p0 = (x0 + nx * 0.08, z0 + nz * 0.08)
        p1 = (x0 + nx * (0.08 + h), z0 + nz * (0.08 + h))
        # read from inside the car: on the left wall the text runs towards +y, on the right towards -y
        ya, yb = (y, y + ln) if s < 0 else (y + ln, y)
        q = ((p0[0], ya, p0[1] - 0.006), (p0[0], yb, p0[1] - 0.006), (p1[0], yb, p1[1] - 0.006), (p1[0], ya, p1[1] - 0.006))
        setkit.quads("long_ad", [(q, ((0, 0), (1, 0), (1, 1), (0, 1)))], m)
        # a thin frame strip above and below
        y += ln + 0.22
        i += 1


def ceiling(M):
    plane("ceil", (0, S.LEN / 2, S.CEIL), 1.62, S.LEN, M["ceil"])
    # two lines of lamps
    for sx in (-1, 1):
        y = 0.4
        while y < S.LEN - 0.4:
            box("lamp", (sx * 0.56, y + 0.6, S.CEIL - 0.015), (0.10, 1.2, 0.03), M["lamp"])
            box("lamp_end", (sx * 0.56, y + 0.0, S.CEIL - 0.012), (0.12, 0.05, 0.024), M["vent"])
            y += 1.45
    # the air duct along the middle, with its slots
    box("vent", (0, S.LEN / 2, S.CEIL - 0.012), (0.34, S.LEN, 0.024), M["vent"])
    y = 0.3
    while y < S.LEN:
        box("slot", (0, y, S.CEIL - 0.027), (0.26, 0.05, 0.004), M["ventline"])
        y += 0.42


def end_wall(M):
    y = S.LEN + 0.03
    box("end_l", (-0.95, y, S.CEIL / 2), (0.94, 0.06, S.CEIL), M["wall"])
    box("end_r", (0.95, y, S.CEIL / 2), (0.94, 0.06, S.CEIL), M["wall"])
    box("end_top", (0, y, 2.15), (1.0, 0.06, 0.34), M["wall"])
    box("end_door", (0, y - 0.01, 0.58), (0.96, 0.04, 1.16), M["door"])
    box("end_door_a", (-0.38, y - 0.01, 1.56), (0.2, 0.04, 0.8), M["door"])
    box("end_door_b", (0.38, y - 0.01, 1.56), (0.2, 0.04, 0.8), M["door"])
    box("end_door_c", (0, y - 0.01, 1.95), (0.96, 0.04, 0.08), M["door"])
    plane("end_pane", (0, y + 0.3, 1.5), 1.2, 1.4, M["end"], rot=(math.pi / 2, 0, 0), uid=UID_END)


def floor(M):
    plane("floor", (0, S.LEN / 2, 0), S.HW * 2 + 0.2, S.LEN, M["floor"])
    plane("floorstrip", (0, S.LEN / 2, 0.002), 1.04, S.LEN, M["strip"])
    # seams across
    y = 0.0
    while y < S.LEN:
        box("seam", (0, y, 0.003), (1.04, 0.012, 0.002), M["floor"])
        y += 1.2


def strap_mesh(M):
    """The band and the ring of one strap, hanging from the origin."""
    parts = []
    parts.append(box("band", (0, 0, -0.10), (0.026, 0.006, 0.20), M["band"]))
    parts.append(box("clip", (0, 0, -0.012), (0.036, 0.03, 0.03), M["rail"]))
    # the triangle-round ring
    pts = []
    for k in range(97):
        a = 2 * math.pi * k / 96
        pts.append((0.056 * math.sin(a), 0.0, -0.26 + 0.058 * math.cos(a)))
    ring = tube("ring", pts, 0.0085, M["ring"], seg=16)
    for pg in ring.data.polygons:
        pg.use_smooth = True
    parts.append(ring)
    ob = kit.join(parts, "strap_proto")
    return ob


def build_set(warm=False):
    """Returns what swings: ad pivots and strap objects."""
    sc = bpy.context.scene
    M = materials(warm)
    floor(M)
    ceiling(M)
    end_wall(M)
    for s in (-1, 1):
        side(M, s)
        cove(M, s, warm)
    # strap rails, with their hangers from the ceiling
    for s in (-1, 1):
        pipe("strap_rail", (s * S.STRAP_X, 0, S.STRAP_Z), (s * S.STRAP_X, S.LEN, S.STRAP_Z), 0.014, M["rail"])
        y = 0.8
        while y < S.LEN:
            cyl("hanger", (s * S.STRAP_X, y, S.STRAP_Z), (s * S.STRAP_X * 0.98, y, S.CEIL), 0.008, M["rail"], seg=5)
            y += 1.9
    proto = strap_mesh(M)
    me = proto.data
    bpy.data.objects.remove(proto)
    straps = []
    uid = 9300
    for s in (-1, 1):
        for a, b in S.BENCHES:
            y = a + 0.15
            while y < b - 0.1:
                # no strap hangs where an ad's rail crosses: the swinging paper would go through the ring
                if min(abs(y - r) for r in S.AD_ROWS) < 0.14:
                    y += 0.33
                    continue
                ob = bpy.data.objects.new("strap", me)
                sc.collection.objects.link(ob)
                ob.location = (s * S.STRAP_X, y, S.STRAP_Z)
                ob.pass_index = uid
                uid += 1
                straps.append(ob)
                y += 0.33
    # the hanging ads
    names = OTHER_ADS if warm else HER_ADS
    pivots = []
    clip = M["dark"]
    i = 0
    for ry in S.AD_ROWS:
        cyl("ad_rail", (-0.86, ry, S.AD_PIVOT), (0.86, ry, S.AD_PIVOT), 0.008, M["rail"], seg=6)
        for sx in (-0.86, 0.86):
            cyl("ad_rail_h", (sx, ry, S.AD_PIVOT), (sx * 0.96, ry, S.CEIL), 0.007, M["rail"], seg=5)
        for sx in (-1, 1):
            piv = bpy.data.objects.new("ad_pivot", None)
            sc.collection.objects.link(piv)
            piv.location = (sx * 0.40, ry, S.AD_PIVOT)
            name = names[i % len(names)]
            m = kit.mat(f"ad_{name}", "#FFFFFF", kind=1, tex=TEX / f"{name}.png")
            dz = S.AD_TOP - S.AD_PIVOT
            a = kit.plane(f"ad", (0, 0, dz - S.AD_H / 2), S.AD_W, S.AD_H, m, rot=(math.pi / 2, 0, 0), parent=piv)
            a.visible_shadow = True
            box("ad_clip", (0, -0.002, dz + 0.012), (S.AD_W + 0.012, 0.012, 0.03), clip, parent=piv)
            box("ad_clip_b", (0, -0.001, dz - S.AD_H - 0.004), (S.AD_W + 0.004, 0.006, 0.012), clip, parent=piv)
            cyl("ad_hook", (-0.2, 0, 0), (-0.2, 0, dz + 0.02), 0.004, M["rail"], parent=piv, seg=4)
            cyl("ad_hook", (0.2, 0, 0), (0.2, 0, dz + 0.02), 0.004, M["rail"], parent=piv, seg=4)
            pivots.append(piv)
            i += 1
    return pivots, straps


def swing(t, pivots, straps):
    s = S.sway(t)
    # the ads are stiff paper on a short hanger, the straps are longer and looser: the same swing, different reach
    for p in pivots:
        p.rotation_euler = (math.radians(6.5) * s, math.radians(4.5) * s, 0)
    for k, o in enumerate(straps):
        o.rotation_euler = (math.radians(3.0) * s, math.radians(11.0) * s, 0)


def train_pos(p, t):
    return p["x"], p["y"]


def build():
    sc = kit.reset()
    kit.setup_render(sc, 1920, 1080, ss=S.SS, fps=60, samples=3, threads=12)
    crowdkit.more_bounces(sc)
    sc.render.use_persistent_data = True
    pivots, straps = build_set(False)
    kit.sun(sc, S.SUN)
    cam = kit.camera(sc, lens=S.LENS, clip_end=200)
    ids = {"win": list(UID_WIN), "end": UID_END, "crowd": crowdkit.UID_CROWD}
    (kit.ROOT / "work" / "render" / "train_ids.json").write_text(json.dumps(ids))
    people = C.train_people(S)
    # where someone holds a strap the strap is in their drawing
    for ob in straps:
        s_ = 1 if ob.location.x > 0 else -1
        if any(abs(ob.location.y - y) < 0.25 for y in C.hidden_strap_ys(people, s_)):
            ob.hide_render = True
    crowd = crowdkit.Crowd(people, S.SUN, train_pos)
    return sc, cam, pivots, straps, crowd


def set_frame(t, sc, cam, pivots, straps, crowd):
    eye, tg, up = S.camera_at(t)
    setkit.set_camera(cam, eye, tg, up, lens=S.lens_at(t))
    swing(t, pivots, straps)
    crowd.place(t, eye)


if __name__ == "__main__":
    setkit.run(kit.set_args(), S, build, set_frame)
