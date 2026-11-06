"""The school gate. Rows of cameras on tripods, microphones, chairs, sandbags, cables and cups, and everybody who came, all aimed at a shut door."""
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
from setkit import TEX, blob, chaikin, cone, tube, wall_plane  # noqa: E402
import shared_crowd as C  # noqa: E402
import shared_gate as S  # noqa: E402

UID_SKY = 9001
UID_YARD = 9002
UID_TAPE = (9010, 9011)
UID_PLATE = 9012
UID_CROWN = 9026
UID_FAR = (9020, 9021, 9022, 9023, 9024, 9025)   # the school reads as a bright flat painting, far behind
UID_THIN = 9040     # tripod legs and cables: two lines of ink on something this thin made a black spider's leg of it


def materials(warm):
    wc = (lambda a, b: b if warm else a)
    return {
        "road": mat("road", wc("#DADBD5", "#CFC9BC")),
        "patch": mat("patch", wc("#C9CBC6", "#D6CCB6")),
        "walk": mat("walk", wc("#EDEBE2", "#E4DDCB")),
        "line": mat("line", "#F8F6EE"),
        "wall": mat("gwall", wc("#EDECE3", "#F2EADA")),
        "pil": mat("gpil", wc("#C9CCC6", "#D8CBB0")),
        "cap": mat("gcap", wc("#6E737B", "#7A6E62")),
        "post": mat("gpost", wc("#E8E7DF", "#EFE6D4")),
        "yard": mat("gyard", wc("#D9CFB2", "#E6CFA0")),
        "path": mat("gpath", wc("#E8E4D6", "#F0E6CE")),
        "hedge": mat("ghedge", wc("#4F9270", "#7FA765")),
        "bar": mat("gbar", "#1D1F26"),
        "track": mat("gtrack", "#55585F"),
        "iron": mat("giron", "#8D9299"),
        "dark": mat("gdark", "#24262C"),
        "lens": mat("glens", "#3A3D45"),
        "glass": mat("gglass", "#7FA9C4"),
        "leg": mat("gleg", "#5E636B"),
        "sand": mat("gsand", "#3C4A4C"),
        "sand2": mat("gsand2", "#4F5D50"),
        "cable": mat("gcable", "#15161B"),
        "paper": mat("gcup", "#F6F3EA"),
        "cupband": mat("gcupband", "#03C3FB"),
        "seat": mat("gseat", "#40505F"),
        "chair": mat("gchair", "#B2B8BA"),
        "case": mat("gcase", "#2C2F36"),
        "mic3": mat("gmic3", "#5B6068"),
        "foam": mat("gfoam", "#2A2C33"),
        "tree": mat("gtree", wc("#5FA277", "#7FA765")),
        "trunk": mat("gtrunk", "#6E5A48"),
        "sky": mat("gsky", "#03C3FB", kind=5),
        "facade": mat("gfacade", "#E3E4DC", tex=TEX / ("facade_warm.png" if warm else "facade.png")),
        "school": mat("gschool", wc("#E3E4DC", "#EFE7D2")),
        "roof": mat("groof", wc("#5B6068", "#6B6258")),
        "white": mat("gwhite", "#F6F3EA"),
        "mark": mat("gmark", "#8E8D84"),
    }


def tripod(M, g, name):
    """Three legs out to the ground, a spreader and a centre column. Feet are on the road."""
    r = 0.40 if g["h"] < 1.4 else 0.43
    hub = g["h"] - 0.20
    yaw, _ = S.aim_angles(g)
    feet = []
    for k in range(3):
        a = yaw + g["turn"] + k * 2 * math.pi / 3
        fx, fy = g["x"] + r * math.sin(a), g["y"] + r * math.cos(a)
        feet.append((fx, fy))
        cyl("leg", (g["x"] + 0.04 * math.sin(a), g["y"] + 0.04 * math.cos(a), hub), (fx, fy, 0.012), 0.019, M["leg"], seg=6, uid=UID_THIN)
        # the lower, thinner section of the leg ends in a dark foot
        cyl("foot", (fx, fy, 0.012), (fx, fy, 0.05), 0.024, M["dark"], seg=6)
        mid = 0.42
        cyl("spread", (g["x"], g["y"], hub * (1 - mid) * 0.9), (g["x"] + r * mid * math.sin(a), g["y"] + r * mid * math.cos(a), hub * (1 - mid)), 0.007, M["iron"], seg=4)
    cyl("column", (g["x"], g["y"], hub * 0.5), (g["x"], g["y"], g["h"]), 0.02, M["iron"], seg=6)
    cyl("hub", (g["x"], g["y"], hub - 0.03), (g["x"], g["y"], hub + 0.03), 0.055, M["dark"], seg=8)
    return feet


def camera_rig(M, g):
    yaw, pitch = S.aim_angles(g)
    rot = (pitch, 0, -yaw)
    w = lambda *v: S.local_to_world(g, *v)
    box("plate", w(0, -0.02, 0.02), (0.12, 0.22, 0.03), M["iron"], rot=rot)
    if g["kind"] == "video":
        box("body", w(0, -0.03, 0.135), (0.13, 0.34, 0.19), M["dark"], rot=rot)
        box("batt", w(0, -0.235, 0.125), (0.11, 0.07, 0.16), M["lens"], rot=rot)
        box("eyecup", w(-0.095, 0.05, 0.235), (0.055, 0.17, 0.055), M["lens"], rot=rot)
        box("handle", w(0, -0.03, 0.262), (0.03, 0.2, 0.02), M["lens"], rot=rot)
        box("h1", w(0, 0.05, 0.24), (0.02, 0.02, 0.03), M["lens"], rot=rot)
        box("h2", w(0, -0.11, 0.24), (0.02, 0.02, 0.03), M["lens"], rot=rot)
        cyl("lens", w(0, 0.13, 0.13), w(0, 0.42, 0.13), 0.058, M["lens"], seg=10)
        cyl("hood", w(0, 0.42, 0.13), w(0, 0.50, 0.13), 0.085, M["dark"], seg=10)
        cyl("glass", w(0, 0.495, 0.13), w(0, 0.503, 0.13), 0.066, M["glass"], seg=10)
        cyl("topmic", w(0.05, -0.02, 0.27), w(0.05, 0.2, 0.27), 0.012, M["foam"], seg=6)
        cyl("pan", w(0.055, -0.08, 0.025), w(0.13, -0.56, -0.09), 0.009, M["iron"], seg=4)
    else:
        box("body", w(0, -0.005, 0.085), (0.15, 0.085, 0.105), M["dark"], rot=rot)
        box("grip", w(0.075, 0.0, 0.08), (0.035, 0.095, 0.095), M["lens"], rot=rot)
        box("prism", w(0, -0.01, 0.15), (0.06, 0.06, 0.03), M["lens"], rot=rot)
        cyl("lens", w(0, 0.03, 0.08), w(0, 0.21, 0.08), 0.042, M["lens"], seg=10)
        cyl("hood", w(0, 0.21, 0.08), w(0, 0.27, 0.08), 0.055, M["dark"], seg=10)
        cyl("glass", w(0, 0.268, 0.08), w(0, 0.273, 0.08), 0.04, M["glass"], seg=10)
        # the flash on the hot shoe, with its white window facing the door
        box("fl_neck", w(0, -0.005, 0.18), (0.05, 0.05, 0.035), M["dark"], rot=rot)
        box("fl_head", w(0, 0.01, 0.222), (0.075, 0.05, 0.05), M["dark"], rot=rot)
        box("fl_win", w(0, 0.036, 0.222), (0.066, 0.004, 0.04), M["white"], rot=rot)


def sandbag(M, x, y, k=0):
    blob("sandbag", (x, y, 0.055), (0.17, 0.08, 0.06), M["sand" if k % 3 else "sand2"]).rotation_euler = (0, 0, k * 1.3)


def chair(M, x, y, yaw):
    c, s = math.cos(yaw), math.sin(yaw)
    w = lambda lx, ly, lz: (x + lx * c - ly * s, y + lx * s + ly * c, lz)
    for dx in (-0.2, 0.2):
        cyl("cf", w(dx, 0.20, 0.008), w(dx, -0.20, 0.84), 0.009, M["chair"], seg=5)
        cyl("cr", w(dx * 0.86, -0.21, 0.008), w(dx * 0.86, 0.17, 0.44), 0.009, M["chair"], seg=5)
    cyl("cb", w(-0.2, 0.2, 0.05), w(0.2, 0.2, 0.05), 0.007, M["chair"], seg=5)
    box("seat", w(0, 0.0, 0.45), (0.40, 0.38, 0.018), M["seat"], rot=(0, 0, yaw))
    box("back", w(0, -0.17, 0.76), (0.40, 0.018, 0.15), M["seat"], rot=(math.radians(-25), 0, yaw))


def cup(M, x, y, z=0.0, fallen=None):
    if fallen is None:
        cone("cup", (x, y, z), 0.028, 0.04, 0.095, M["paper"])
    else:
        c = cone("cup", (x, y, z + 0.034), 0.028, 0.04, 0.095, M["paper"])
        c.rotation_euler = (math.pi / 2 - 0.1, 0, fallen)


def ladder(M, x, y, yaw):
    """A press stepladder, opened, feet on the road: four treads on one side, braces on the other."""
    c, s = math.cos(yaw), math.sin(yaw)
    w = lambda lx, ly, lz: (x + lx * c - ly * s, y + lx * s + ly * c, lz)
    top = 1.25
    for dx0, dx1 in ((-0.27, -0.19), (0.27, 0.19)):
        cyl("lf", w(dx0, -0.48, 0.01), w(dx1, 0.0, top), 0.018, M["iron"], seg=5)
        cyl("lb", w(dx0, 0.46, 0.01), w(dx1, 0.0, top), 0.016, M["iron"], seg=5)
    for k in range(4):
        h = (k + 1) * top / 5
        ly = -0.48 * (1 - h / top)
        hw = 0.27 + (0.19 - 0.27) * h / top
        box("step", w(0, ly, h), (2 * hw, 0.10, 0.018), M["track"], rot=(0, 0, yaw))
    for h in (0.45, 0.85):
        ly = 0.46 * (1 - h / top)
        hw = 0.27 + (0.19 - 0.27) * h / top
        cyl("brace", w(-hw, ly, h), w(hw, ly, h), 0.009, M["iron"], seg=4)
    box("top", w(0, 0, top + 0.012), (0.44, 0.24, 0.024), M["dark"], rot=(0, 0, yaw))


def case(M, x, y, yaw, size=(0.6, 0.38, 0.32)):
    box("case", (x, y, size[2] / 2), size, M["case"], rot=(0, 0, yaw))
    box("case_lid", (x, y, size[2] * 0.72), (size[0] * 1.02, size[1] * 1.02, 0.015), M["iron"], rot=(0, 0, yaw))


def cable(M, pts, k):
    """It lies where it fell: never a straight line along the road. Through the air down a tripod (points given with a height) it is left as it is."""
    r = random.Random(100 + k)
    out = []
    for a, b in zip(pts, pts[1:]):
        out.append(a)
        if len(a) == 2 and len(b) == 2 and math.hypot(b[0] - a[0], b[1] - a[1]) > 0.8:
            n = int(math.hypot(b[0] - a[0], b[1] - a[1]) / 0.7)
            for i in range(1, n):
                u = i / n
                out.append((a[0] + (b[0] - a[0]) * u + (0.11 if i % 2 else -0.11) * r.uniform(0.4, 1.3), a[1] + (b[1] - a[1]) * u))
    out.append(pts[-1])
    pts = [(p[0], p[1], p[2] if len(p) > 2 else 0.012 + 0.002 * (k % 5)) for p in out]
    tube("cable", chaikin(pts, 3), 0.0065, M["cable"], seg=5, uid=UID_THIN)


# Each station's own microphone on its own stand, spread right across the front of the crowd, a clear lane left down the
# middle. Grey and black only: anything coloured gathered at a shut gate reads as flowers left there.
MIC_STANDS = ((-3.55, -3.7, 1.04, 2), (-2.45, -2.75, 1.28, 1), (-1.35, -3.85, 1.16, 2), (1.05, -2.95, 1.22, 1),
              (2.05, -3.95, 1.02, 2), (3.0, -2.7, 1.32, 1), (4.0, -3.6, 1.12, 1))


def mics(M):
    """Stands with a microphone or two, aimed at the door, each with a plain station cube."""
    r = random.Random(9)
    for k, (x0, y0, h, n) in enumerate(MIC_STANDS):
        for j in range(3):
            a = 0.6 + k + j * 2 * math.pi / 3
            cyl("mleg", (x0, y0, 0.42), (x0 + 0.34 * math.sin(a), y0 + 0.34 * math.cos(a), 0.012), 0.011, M["iron"], seg=5)
        cyl("mpole", (x0, y0, 0.36), (x0, y0, h), 0.012, M["iron"], seg=6)
        if k % 2 == 0:
            sandbag(M, x0 + 0.34 * math.sin(0.6 + k), y0 + 0.34 * math.cos(0.6 + k), k + 1)
        hub = (x0, y0, h)
        dx, dy = -x0 * 0.45, -y0
        d = math.hypot(dx, dy)
        dx, dy = dx / d, dy / d
        for i in range(n):
            sp = (i - (n - 1) / 2) * 0.13
            ln = 0.34 + 0.06 * r.random()
            tip = (x0 + dx * ln - dy * sp, y0 + dy * ln + dx * sp, h + 0.10 + 0.05 * i)
            cyl("marm", hub, tip, 0.008, M["foam"], seg=5)
            f = [hub[j] + (tip[j] - hub[j]) * 0.62 for j in range(3)]
            s = r.choice((0.075, 0.085, 0.07))
            box("mflag", tuple(f), (s, s, s), M["mic3"])
            blob("mhead", tip, (0.036, 0.05, 0.036), M["foam"])
        cable(M, [(x0, y0 - 0.05), (x0 * 1.15, y0 - 2.5), (x0 * 1.5 + 0.4, -12.0), (x0 * 2.0, -19.0)], k)
    # two boom poles on their own stands, each resting on its stand's head and reaching out towards its own end of the door
    for sx, x_ in ((-1, -2.05), (1, 1.85)):
        y_ = -3.5
        for k in range(3):
            a = k * 2 * math.pi / 3 + sx
            cyl("bleg", (x_, y_, 0.6), (x_ + 0.45 * math.sin(a), y_ + 0.45 * math.cos(a), 0.012), 0.012, M["iron"], seg=5)
        cyl("bpole", (x_, y_, 0.5), (x_, y_, 1.7), 0.016, M["iron"], seg=6)
        tip = (x_ * 0.78, -1.5, 1.92)
        piv = (x_, y_, 1.71)
        back = tuple(piv[j] - (tip[j] - piv[j]) * 0.32 for j in range(3))
        cyl("boom", back, tip, 0.012, M["iron"], seg=5)
        blob("zep", (tip[0], tip[1] + 0.05, tip[2]), (0.07, 0.17, 0.07), M["foam"])
        sandbag(M, x_ + 0.45 * math.sin(sx), y_ + 0.45 * math.cos(sx), 2)
        cable(M, [(x_, y_ + 0.1), (x_ * 1.5, y_ - 2.5), (x_ * 2.2, -11.5), (x_ * 3, -18)], 3)


def tape(M, z, sag, skew=0.0, uid=None):
    """Barrier tape tied from post to post, in front of the door, hanging a little."""
    n = 16
    m = kit.mat("tape", E_TAPE, kind=4, tex=TEX / "tape.png", repeat=(1, 1))
    x0, x1 = -S.DOOR_W / 2 - 0.05, S.DOOR_W / 2 + 0.05
    y = -0.325
    h = 0.20
    items = []
    tex_len = 1.6
    for i in range(n):
        a, b = i / n, (i + 1) / n
        xa, xb = x0 + (x1 - x0) * a, x0 + (x1 - x0) * b
        za = z + skew * (a - 0.5) - sag * (1 - (2 * a - 1) ** 2)
        zb = z + skew * (b - 0.5) - sag * (1 - (2 * b - 1) ** 2)
        ua, ub = (xa - x0) / tex_len, (xb - x0) / tex_len
        items.append((((xa, y, za - h / 2), (xb, y, zb - h / 2), (xb, y, zb + h / 2), (xa, y, za + h / 2)),
                      ((ua, 0), (ub, 0), (ub, 1), (ua, 1))))
    return setkit.quads("tape", items, m, uid=uid)


E_TAPE = "#FEE45F"


def build_set(M, warm=False):
    """Everything that does not move. warm: the same place in an ordinary afternoon, gear gone, door slid open."""
    sc = bpy.context.scene
    # ground
    plane("road", (0, -60, 0), 300, 120, M["road"])
    plane("walk", (0, -0.9, 0.004), 300, 1.8, M["walk"])
    box("curb", (0, -1.84, 0.03), (300, 0.1, 0.06), M["pil"])
    plane("yard", (0, 60, 0.0), 300, 120, M["yard"], uid=UID_YARD)
    # road surface: patches and a manhole, so it is a road and not a floor
    plane("seam", (0, -7.6, 0.003), 300, 0.035, M["pil"])
    cyl("manhole", (-1.6, -14.0, 0.0), (-1.6, -14.0, 0.006), 0.36, M["iron"], seg=24)
    cyl("manhole2", (-1.6, -14.0, 0.006), (-1.6, -14.0, 0.008), 0.30, M["track"], seg=24)
    # a white line, slightly across, as in the photograph
    plane("roadline", (0, -17.2, 0.005), 60, 0.16, M["line"], rot=(0, 0, 0.05))
    # the wall either side, with its coping and piers
    for sx in (-1, 1):
        xa, xb = S.DOOR_W / 2 + 1.05, 46.0
        cx = sx * (xa + xb) / 2
        box("wall", (cx, 0, 0.925), (xb - xa, 0.24, 1.85), M["wall"])
        box("coping", (cx, 0, 1.91), (xb - xa, 0.34, 0.12), M["cap"])
        pieces = int((xb - xa) / 1.45)
        for i in range(1, pieces):
            box("pier", (sx * (xa + i * 1.45), -0.13, 0.925), (0.09, 0.03, 1.85), M["pil"])
    # gate posts
    for sx in (-1, 1):
        cx = sx * (S.DOOR_W / 2 + 0.525)
        box("post", (cx, 0, 1.45), (1.05, 0.6, 2.9), M["post"])
        box("postcap", (cx, 0, 2.96), (1.25, 0.78, 0.14), M["cap"])
    # name plate on the right post
    plate = mat("plate_s" if warm else "plate_m", "#F6F3EA", kind=4, tex=TEX / ("plate_school.png" if warm else "plate_mosaic.png"))
    wall_plane("plate", (S.DOOR_W / 2 + 0.525, -0.308, 1.62), 0.62, 1.93, plate, uid=UID_PLATE)
    # the door: closely set bars, top and bottom rails, on a track
    parts = []
    y = 0.36
    dx = -S.DOOR_W if warm else 0.0
    # slid open it stands behind the wall: its spikes are lower than the coping, or three black posts show along the wall's top
    top = 1.78 if warm else 2.16
    parts.append(box("rail_t", (dx, y, top - 0.22), (S.DOOR_W, 0.07, 0.11), M["bar"]))
    parts.append(box("rail_b", (dx, y, 0.14), (S.DOOR_W, 0.07, 0.13), M["bar"]))
    for i in range(18):
        x = dx - S.DOOR_W / 2 + 0.10 + i * (S.DOOR_W - 0.2) / 17
        parts.append(box("bar", (x, y, top / 2 + 0.05), (0.06, 0.05, top - 0.1), M["bar"]))
    for x in (-1.6, 1.6):
        parts.append(box("wheel", (dx + x, y, 0.04), (0.12, 0.06, 0.08), M["track"]))
    kit.join(parts, "door")
    box("track", (-S.DOOR_W / 2, y, 0.004), (S.DOOR_W * 2.2, 0.08, 0.008), M["track"])
    # behind: a low school, with its clock
    fy = 40.0
    plane("facade", (0, fy, 5.25), 90, 10.5, M["facade"], rot=(math.pi / 2, 0, 0), uid=UID_FAR[0])
    box("school", (0, fy + 8, 5.25), (90, 15.9, 10.5), M["school"], uid=UID_FAR[1])
    box("roofband", (0, fy + 8, 10.7), (91, 16.8, 0.45), M["roof"], uid=UID_FAR[2])
    box("tower", (0, fy - 1.0, 7.2), (12.5, 2.0, 14.4), M["school"], uid=UID_FAR[3])
    box("towercap", (0, fy - 1.0, 14.55), (13.4, 2.5, 0.45), M["roof"], uid=UID_FAR[2])
    cf = fy - 2.04
    cyl("clock_rim", (0, cf + 0.03, 11.2), (0, cf - 0.02, 11.2), 2.0, M["bar"], seg=40, uid=UID_FAR[4])
    cyl("clock", (0, cf - 0.02, 11.2), (0, cf - 0.04, 11.2), 1.66, M["white"], seg=40, uid=UID_FAR[5])
    box("hour", (0.5, cf - 0.06, 10.95), (1.05, 0.02, 0.2), M["bar"], rot=(0, -0.45, 0), uid=UID_FAR[4])
    box("minute", (0.0, cf - 0.06, 12.0), (0.15, 0.02, 1.5), M["bar"], uid=UID_FAR[4])
    # the entrance at the foot of the tower: a porch and glass doors
    box("porch", (0, fy - 3.2, 3.15), (7.0, 2.4, 0.3), M["roof"], uid=UID_FAR[2])
    for sx in (-1, 1):
        box("porch_col", (sx * 3.2, fy - 4.0, 1.5), (0.4, 0.4, 3.0), M["school"], uid=UID_FAR[1])
    box("entry", (0, fy - 2.06, 1.5), (5.4, 0.02, 3.0), M["glass"], uid=UID_FAR[2])
    for i in range(5):
        box("entry_bar", (-2.4 + i * 1.2, fy - 2.09, 1.5), (0.08, 0.03, 3.0), M["iron"])
    for o in bpy.context.scene.collection.objects:
        if o.pass_index in UID_FAR:
            o.visible_shadow = False
    # the yard: a paved path up from the gate, a hedge inside the wall, a bicycle shed, trees, a flagpole
    plane("path", (0, 19.5, 0.003), 6.0, 39, M["path"])
    for sx in (-1, 1):
        box("hedge", (sx * 14.0, 1.0, 0.45), (20.0, 0.9, 0.9), M["hedge"])
    box("shed_roof", (-16.0, 15.0, 2.3), (12.0, 3.2, 0.12), M["roof"])
    for i in range(5):
        cyl("shed_post", (-21.5 + i * 2.75, 13.7, 0), (-21.5 + i * 2.75, 13.7, 2.25), 0.05, M["iron"], seg=6)
        cyl("shed_post", (-21.5 + i * 2.75, 16.3, 0), (-21.5 + i * 2.75, 16.3, 2.25), 0.05, M["iron"], seg=6)
    for n_, (x, y_, r_) in enumerate(((-10.5, 30.0, 2.3), (-24.0, 31.0, 2.8), (12.0, 31.0, 2.4), (25.0, 29.0, 2.9), (-34.0, 27.0, 3.2), (36.0, 26.0, 3.0))):
        cyl("trunk", (x, y_, 0), (x, y_, 2.6), 0.2, M["trunk"], seg=7)
        # a tree is several masses, not one ball; the crown is one flat colour, as in the town
        for dx_, dz_, k_ in ((0, 0.9, 0.86), (-0.62, 0.45, 0.62), (0.66, 0.5, 0.58), (0.1, 1.5, 0.55)):
            crown = blob("crown", (x + dx_ * r_, y_, 2.6 + dz_ * r_), (r_ * k_, r_ * k_, r_ * k_ * 0.85), M["tree"], uid=UID_CROWN + n_)
            crown.visible_shadow = False
    cyl("flagpole", (9.0, 12.0, 0), (9.0, 12.0, 8.0), 0.05, M["iron"], seg=6)
    blob("flagball", (9.0, 12.0, 8.07), (0.09, 0.09, 0.09), M["iron"])
    # sky
    plane("sky", (0, 400, 40), 1800, 500, M["sky"], rot=(math.pi / 2, 0, 0), uid=UID_SKY)


def build_gear(M):
    r = random.Random(23)
    cables = []
    rigs = []
    for i, g in enumerate(S.GEAR):
        feet = tripod(M, g, f"tp{i}")
        # the camera on its head can turn: everything of the rig hangs from a pivot on the tripod's axis
        before = set(bpy.context.scene.collection.objects)
        camera_rig(M, g)
        made = set(bpy.context.scene.collection.objects) - before
        piv = bpy.data.objects.new("rig_pivot", None)
        bpy.context.scene.collection.objects.link(piv)
        piv.location = (g["x"], g["y"], 0.0)
        bpy.context.view_layer.update()
        inv = piv.matrix_world.inverted()
        for o in made:
            o.parent = piv
            o.matrix_parent_inverse = inv
        rigs.append(piv)
        # sandbags on most tripod feet
        if i % 3 != 2:
            f = feet[i % 3]
            sandbag(M, f[0], f[1], i)
        cables.append((g, feet))
    # cables: down a leg, along the road, away over the kerb of the shot
    for i, (g, feet) in enumerate(cables):
        if g["kind"] != "video":
            continue
        f = feet[(i + 1) % 3]
        hand = 1 if g["x"] > 0 else -1
        away = (f[0] + r.uniform(-0.4, 0.4), f[1] - 0.8)
        cable(M, [(g["x"], g["y"], g["h"] - 0.1), ((g["x"] + f[0]) / 2, (g["y"] + f[1]) / 2, (g["h"] - 0.1) * 0.45), (f[0], f[1], 0.03), (away[0], away[1], 0.014)], i)
        cable(M, [(away[0], away[1], 0.014), (g["x"] + hand * r.uniform(1.0, 2.2), -13.0 + r.uniform(-0.6, 0.6)), (g["x"] * 1.3 + hand * 3.0, -15.5 + r.uniform(-0.5, 0.5)), (g["x"] * 1.6 + hand * 6.5, -24.0)], i)
    mics(M)
    # folding chairs, left as they were: some between the rows, some at the back
    for x, y_, yaw in ((-2.6, -8.2, 0.25), (-1.7, -8.3, -0.1), (2.4, -8.2, -0.3), (-3.6, -13.0, 0.15), (-2.8, -13.3, -0.05), (2.6, -13.5, -0.2), (3.45, -13.1, 0.3)):
        chair(M, x, y_, yaw)
    # stepladders between the back-row tripods
    ladder(M, -3.9, -10.9, 1.05)
    ladder(M, 3.3, -11.2, -0.95)
    # cases
    case(M, -4.4, -7.3, 0.5)
    case(M, 4.5, -7.2, -0.3, (0.7, 0.42, 0.34))
    case(M, 3.9, -7.7, -0.8, (0.44, 0.3, 0.26))
    # a cable drum
    cyl("drum_a", (-3.0, -13.6, 0.03), (-3.0, -13.6, 0.05), 0.26, M["dark"], seg=20)
    cyl("drum_b", (-3.0, -13.6, 0.05), (-3.0, -13.6, 0.28), 0.17, M["cable"], seg=20)
    cyl("drum_c", (-3.0, -13.6, 0.28), (-3.0, -13.6, 0.30), 0.26, M["dark"], seg=20)
    # paper cups, some on the seats, some on the road, a couple on their side
    for (x, y_) in ((-1.7, -8.3), (2.4, -8.2), (-2.8, -13.3)):
        cup(M, x, y_, 0.459)
    for x, y_, f in ((-4.6, -7.5, None), (-4.45, -7.65, None), (1.4, -5.2, 0.8), (3.1, -8.6, None), (-1.2, -9.8, 1.9), (-0.7, -7.2, None), (0.5, -8.6, None), (5.1, -6.2, None),
                     (-6.4, -10.9, None), (0.9, -13.2, None), (2.2, -14.6, 2.4), (-2.0, -15.4, None), (4.8, -15.0, None), (-7.5, -14.2, 0.4)):
        cup(M, x, y_, 0.0, fallen=f)
    # the barrier
    tape(M, 1.42, 0.12, uid=UID_TAPE[0])
    tape(M, 0.86, 0.07, skew=0.14, uid=UID_TAPE[1])
    return rigs


def lit_ids():
    return {"sky": UID_SKY, "yard": UID_YARD, "lit": list(UID_TAPE) + [UID_PLATE] + list(UID_FAR) + [UID_CROWN + i for i in range(6)]}


def gate_pos(p, t):
    if p["gear"] is not None:
        return C.gear_pos(p, S, t)
    if p["walk"]:
        return C.walk_pos(p, t)
    return p["x"], p["y"]


def build():
    sc = kit.reset()
    kit.setup_render(sc, 1920, 1080, ss=S.SS, fps=60, samples=3, threads=12)
    crowdkit.more_bounces(sc)
    sc.render.use_persistent_data = True
    M = materials(False)
    build_set(M, warm=False)
    rigs = build_gear(M)
    kit.sun(sc, S.SUN)
    cam = kit.camera(sc, lens=S.LENS, clip_end=3000)
    ids = lit_ids()
    ids["crowd"] = crowdkit.UID_CROWD
    ids["thin"] = UID_THIN
    (kit.ROOT / "work" / "render").mkdir(parents=True, exist_ok=True)
    (kit.ROOT / "work" / "render" / "gate_ids.json").write_text(json.dumps(ids))
    crowd = crowdkit.Crowd(C.gate_people(S), S.SUN, gate_pos, tilt=0.75)
    return sc, cam, rigs, crowd


def set_frame(t, sc, cam, rigs, crowd):
    eye, tg, up = S.camera_at(t)
    setkit.set_camera(cam, eye, tg, up)
    r = math.radians(S.pan_at(t))
    for piv in rigs:
        piv.rotation_euler = (0, 0, r)
    crowd.place(t, eye)


if __name__ == "__main__":
    setkit.run(kit.set_args(), S, build, set_frame)
