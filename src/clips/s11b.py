"""Section 11b: nobody writes any more. The words stamp themselves, a syllable at a time, in the same block type as the first 寒い: a face, a side, a thin ink line, and real depth.
First small and alone on the floor seen from above, more and larger as the camera goes back. Then the room from above: the type lies on its floor, under what stands there, and rows of it fill the door.
Close on the door the rows come thick and big. Back in the room door and floor are full. Then a wall of sheets printing themselves, each new word bigger than the last, until the last is too big for the screen and the camera goes in through its stroke.
That dark is the floor; one sheet lies on it, パッパ prints itself. The hand pushes it out under the door. The shadow of the two feet in the gap does not go away."""
import math
import sys
from pathlib import Path

import cv2
import numpy as np
import skia

sys.path.insert(0, str(Path(__file__).parent))
import common as K  # noqa: E402
import engine as E  # noqa: E402
import handkit  # noqa: E402
import cutout as C  # noqa: E402
import shared_room as S  # noqa: E402
import s03  # noqa: E402

ROOT = K.ROOT
F0, F1 = 5597, 5818
T0, T1 = F0 / 30, F1 / 30
HITS = (K.syllable_times(51, "sa") + K.syllable_times(52, "sa") + K.syllable_times(53, "sa"))[:14]
DOOR_AT = HITS[5]
WALL_AT = HITS[10]
PUSH_AT = 192.75
# the push is a run of drawings of the arm on twos: it starts lifted and bent, settles flat on the floor, and pushes. The sheet goes along under it without a break. Then the paper is taken from the other side.
# (from what frame, drawing, the picture, its scale). The hand is the same length in every picture, so its scale decides how near it is: it comes up to size as the arm settles.
PUSH_POSES = ((5783, "a", "h45_push_a", 0.82), (5787, "a2a", "h46_push_a2a", 0.86), (5789, "a2b", "h46_push_a2b", 0.90), (5791, "ab1", "h46_push_ab1", 0.95),
              (5793, "ab2", "h46_push_ab2", 1.0), (5795, "b", "h45_push_b", 1.0), (5799, "bc", "h46_push_bc", 0.97), (5801, "c", "h46_push_c", 1.0))
PUSH_K = {key: k for _, key, _, k in PUSH_POSES}
PUSH_RUN = (192.75, 193.52, -0.56, 0.62)     # trailing edge of the sheet, in the floor units of the Push camera, from and to
TAKEN = (193.53, 193.73)

PAPER = "#DDE2EA"
PAPER_DOOR = "#C7CEDD"
WALL_INK = "#6C7893"
# the same night as the 3D room
FLOOR = "#1A2450"
FLOOR_LINE = "#101735"
DOOR = "#2A3770"
WALL = "#10183A"
LIGHT = "#F7EBCB"
SHADOW_A = 0.34
SHEET_W, SHEET_H = 720, 1000     # floor view, world pixels
SHEET_PX = (432, 600)
PLATES = ROOT / "work" / "render" / "s11b_plates"
# Stills from room2, rendered once: the room from above (floor and door in one picture), three angled views of the door, the room again. work/qc/groupD/plate3d holds the same numbers. room*_over.png is what stands in front of the floor and the door
ROOM_VIEWS = {5: ((S.XD + 0.35, -2.75, 2.35), (S.XD - 0.05, -0.80, 0.45), (0, 0, 1), 24.0),
              6: ((S.XD - 0.55, -1.05, 0.45), (S.XD + 0.02, 0.0, 0.90), (0, 0, 1), 40.0),
              7: ((S.XD + 0.55, -1.00, 2.00), (S.XD - 0.01, 0.0, 1.45), (0, 0, 1), 42.0),
              8: ((S.XD - 0.35, -0.95, 0.22), (S.XD + 0.02, 0.0, 0.24), (0, 0, 1), 34.0),
              9: ((S.XD - 0.45, -2.75, 2.35), (S.XD + 0.05, -0.70, 0.50), (0, 0, 1), 23.0)}
# hit, then where it ends up on the last view of the floor, and its em there
FLOOR_SET = ((0, 860, 440, 40),
             (1, 1085, 360, 70),
             (2, 720, 640, 105), (2, 1200, 640, 105),
             (3, 240, 390, 170), (3, 1680, 390, 170), (3, 1200, 140, 170),
             (4, 240, 140, 235), (4, 720, 140, 235), (4, 1680, 140, 235), (4, 240, 640, 235), (4, 1680, 640, 235), (4, 240, 890, 235), (4, 720, 890, 235), (4, 1200, 890, 235), (4, 1680, 890, 235))
# hit, height of the row on the door in metres, which of its two columns
DOOR_SET = ((5, 0.65, (0, 1)),
            (6, 0.885, (0,)), (6, 1.12, (0, 1)),
            (7, 1.355, (0, 1)), (7, 1.59, (0, 1)),
            (8, 0.415, (0, 1)), (8, 0.18, (0, 1)),
            (9, 1.825, (0, 1)))
# hit (-1: there already), how far out from the door the row lies, its em, and where each word sits along it. The type is drawn out a little along its depth, as lettering on a road is, because it is seen at a slant
ROOM_FLOOR = ((-1, 2.35, 0.55, (-0.62, 0.50)),
              (-1, 1.72, 0.42, (-0.78, 0.08, 0.94)),
              (-1, 1.22, 0.33, (-0.92, -0.26, 1.02)),
              (5, 0.80, 0.26, (-1.00, -0.44, 1.14)),
              (7, 0.42, 0.20, (-0.98, -0.52)),
              (9, 0.42, 0.20, (1.16,)),
              (9, 1.05, 0.26, (0.40,)))
# s11a dives into the pile under the door and ends looking straight down at it: this section starts on that same paper. World units here are the pile's own, seen from above.
PILE_UNIT = SHEET_H / S.SHEET_W        # world units to the metre: a sheet's long side is 1000
PILE_AT = (0.3535, -0.542)             # the floor point in the middle of the frame: the widest stretch of the light on the pile (measured, work/gen/trans_a/pile.py)
PILE_S0 = 2.0                          # one sheet is as wide as the frame, and all of it is in the light
PILE_TINT = (1.0, 0.97, 0.88)          # paper in the light, as paint_room has it
# the colours of the room on a sheet, by how much light it gets. The drawing's crayon stays what it is, only darker
NIGHT_DOOR = (0.86, 0.87, 0.95)
NIGHT_LOW = (0.60, 0.63, 0.78)
NIGHT_PUSH = (0.50, 0.54, 0.70)
# the arm in the room: cloth and skin keep apart, as in every dark room of the film
NIGHT_CLOTH = (0.50, 0.56, 0.78)
NIGHT_SKIN = (0.70, 0.62, 0.70)
NIGHT_HAND = ("#AE8E97", "#7E6A90")          # skin in the room's light, and its one shadow: the orange of the drawn shadow does not survive the night
DOOR_RIM = "#E9D6B4"                         # the door's low light, off the bright strip of floor, on the underside and ends of what reaches it
FONT = "ShipporiMinchoB1-ExtraBold"
FACE, SIDE = "#0B9BDC", "#04506F"       # the block type of the first 寒い
LAST_FACE, LAST_SIDE = FLOOR, "#0B9BDC"  # the last one is the colour of the floor: the camera goes in through it and comes out on the floor
RUSH = (191.42, 191.74)                 # into the stroke of the last 寒
VP = (1100.0, 1750.0)                   # flat views: the camera's axis meets the floor below the frame, so every block shows its side under its face
# the wall: hit, then x, y, em, in screen pixels. Each hit bigger than the last and on top of it; the last, in the colour of the floor, is what the camera goes through
WALL_SET = ((10, (345, 170, 245), FACE, SIDE), (10, (960, 170, 245), FACE, SIDE), (10, (1575, 170, 245), FACE, SIDE),
            (11, (500, 560, 410), FACE, SIDE), (11, (1420, 560, 410), FACE, SIDE),
            (12, (960, 500, 640), FACE, SIDE),
            (13, (960, 545, 905), LAST_FACE, LAST_SIDE))
SHEET_LAND = (191.74, 191.86)           # the sheet comes up out of the dark
PA = (191.83, 192.06, 192.52)           # パ ッ パ on お ね が


def floor_to_world(x, y):
    return (x - PILE_AT[0]) * PILE_UNIT, -(y - PILE_AT[1]) * PILE_UNIT


def screen_to_floor(sx, sy, view):
    cx, cy, s = view
    wx, wy = cx + (sx - 960) / s, cy + (sy - 500) / s
    return wx / PILE_UNIT + PILE_AT[0], -wy / PILE_UNIT + PILE_AT[1]


def pile_image():
    """A sheet, as the 3D painter has it in the light (paint_room.sheet_tex): the two crayon flowers, small パッパ, an old fold."""
    w, h = 1536, 1086
    surf = skia.Surface(w, h)
    c = surf.getCanvas()
    c.clear(E.col("#F6F3EA"))
    p = skia.Paint(AntiAlias=True)
    p.setBlendMode(skia.BlendMode.kMultiply)
    c.drawImage(E.load_image(ROOT / "assets" / "gen" / "raw" / "k01_flowers.png"), 0, -14, E.SAMPLING, p)
    s03.draw_pappa(c, 1120, 950, 76, E.INK, seed=4)
    c.drawLine(w / 2, 0, w / 2, h, skia.Paint(AntiAlias=True, Color4f=E.col("#8A8778", 0.45), StrokeWidth=2.2))
    tint = skia.Paint(Color4f=skia.Color4f(*PILE_TINT, 1.0))
    tint.setBlendMode(skia.BlendMode.kMultiply)
    c.drawRect(skia.Rect.MakeWH(w, h), tint)
    return surf.makeImageSnapshot()


def hex3(h):
    c = E.col(h)
    return np.array([c.fR, c.fG, c.fB], np.float32)


def night(im, cloth=NIGHT_CLOTH, skin=NIGHT_SKIN):
    """Her hand and sleeve in this room's light. Mapped to one blue by brightness, skin and sleeve came out the same colour and the hand read as a glove; left nearly as drawn, they were daylight in the dark. So each is graded on its own: flat paint goes down towards the room, the skin stays warmer than the cloth, ink stays ink."""
    out = im.copy()
    # the skin's edge pixels, mixed with the ink, count as skin
    raw = (((im[..., 0] - im[..., 2]) > 0.075) & (im[..., 0] > 0.55)).astype(np.uint8)
    n, lab, st, _ = cv2.connectedComponentsWithStats(raw, connectivity=8)
    hand = (lab == 1 + int(np.argmax(st[1:, 4]))).astype(np.uint8)      # the hand is the one large patch of skin; warm specks on the cloth are not skin
    is_skin = cv2.dilate(hand, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7))).astype(np.float32)[..., None]
    out[..., :3] = im[..., :3] * np.array(cloth, np.float32)
    # the skin: its two painted tones go to the room's two; what is mixed with the ink along a line stays that dark
    lo, hi = hex3(NIGHT_HAND[1]), hex3(NIGHT_HAND[0])
    k = np.clip((cv2.GaussianBlur(im[..., 1], (0, 0), 2.0) - 0.795) / 0.022, 0, 1)[..., None]     # the drawn shadow has a soft edge: here it is one hard shape
    tone = (lo + (hi - lo) * k) * np.clip(im[..., :3].max(-1, keepdims=True) / 0.72, 0, 1)
    out[..., :3] = out[..., :3] * (1 - is_skin) + tone * is_skin
    return out


def door_rim(im):
    """Light from the bright strip on the floor: a hard crescent on the underside and the ends of the fingers, following the drawing's own shape. Alone, to go over the hand once it is in that light."""
    skin = (((im[..., 0] - im[..., 2]) > 0.075) & (im[..., 0] > 0.55)).astype(np.uint8)
    n, lab, st, _ = cv2.connectedComponentsWithStats(skin, connectivity=8)
    skin = (lab == 1 + int(np.argmax(st[1:, 4]))).astype(np.uint8)
    solid = cv2.morphologyEx(skin, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (15, 15)))
    moved = cv2.warpAffine(solid, np.float32([[1, 0, -15], [0, 1, -5]]), (solid.shape[1], solid.shape[0]), flags=cv2.INTER_NEAREST)
    rim = cv2.GaussianBlur(((solid > 0) & (moved == 0)).astype(np.float32), (0, 0), 0.8)
    rim = np.clip((rim - 0.5) * 4 + 0.5, 0, 1) * np.clip((im[..., :3].max(-1) - 0.55) / 0.2, 0, 1) * (im[..., 3] > 0.9)
    out = np.zeros(im.shape, np.float32)
    out[..., :3] = hex3(DOOR_RIM)
    out[..., 3] = rim
    return out


def carry_on(im, side, more):
    """The picture stops where the arm reaches its edge: the sleeve is carried on past it as loose plain cloth (handkit.extrude), so it always leaves the frame in one piece and never as a stiff board. Returns the new picture and the shift of the old one."""
    if side == "left":
        out, off = carry_on(im[:, ::-1].copy(), "right", more)
        return out[:, ::-1].copy(), (more, off[1])
    if side == "bottom":
        out, off = carry_on(np.transpose(im, (1, 0, 2)).copy(), "right", more)
        return np.transpose(out, (1, 0, 2)).copy(), (off[1], off[0])
    # going off to the right: the direction is that of the sleeve's middle over the last stretch before the edge
    h, w = im.shape[:2]
    y1 = np.where(im[:, w - 3, 3] > 0.5)[0]
    y0 = np.where(im[:, w - 120, 3] > 0.5)[0]
    slope = float((y1.min() + y1.max()) - (y0.min() + y0.max())) / 2 / 117.0
    # room for the cloth to go up or down, and for it to widen
    top = int(max(0.0, -slope) * more + 0.35 * more * 0.5) + 8
    bottom = int(max(0.0, slope) * more + 0.35 * more * 0.5) + 8
    pad = np.zeros((h + top + bottom, w, 4), im.dtype)
    pad[top:top + h] = im
    # extrude finds the sleeve on the picture's far edge: trim the picture so that edge is where it stops
    out = handkit.extrude(pad, (1.0, slope), pad=more, loose=0.5)[:pad.shape[0]]
    # only what lies past the edge is new: elsewhere the picture stays exactly as it was drawn
    out[:, :w - 3] = pad[:, :w - 3]
    return out, (0, top)


def glyph(ch):
    return E.Type(ch, FONT, 400.0)


class Word:
    """Set type that prints itself, one syllable at a time. Size is the em of the first character in world units.
    kind "ink": black, flat, as printed on a sheet. "block": the first 寒い: a face, a side, a thin ink line. Either way it lands: it arrives large and with depth, and settles in a tenth of a second."""

    def __init__(self, x, y, size, rot, times, text="寒い", kind="ink", vertical=True, face=FACE, side=SIDE, tilt=0.0, ink=E.INK):
        self.x, self.y, self.size, self.rot, self.kind, self.ink = x, y, size, rot, kind, ink
        self.face, self.side, self.tilt = face, side, tilt
        self.glyphs = []
        n = len(text)
        advs = [size * (0.74 if ch == "ッ" else 0.98) for ch in text]
        pos = np.cumsum([0.0] + [(a_ + b_) / 2 for a_, b_ in zip(advs, advs[1:])])
        pos = pos - pos[-1] / 2
        for i, ch in enumerate(text):
            k = 0.90 if ch in "いッ" else 1.0
            self.glyphs.append((glyph(ch), (0.0, float(pos[i])) if vertical else (float(pos[i]), 0.0), size * k / 400.0, times[i]))
        self.t0 = times[0]

    def draw(self, c, t):
        if t < self.t0:
            return
        c.save()
        c.translate(self.x, self.y)
        c.rotate(self.rot)
        if self.tilt:
            c.skew(self.tilt, 0)
        for ty, (gx, gy), k, tg in self.glyphs:
            age = t - tg
            if age < 0:
                continue
            u = E.seg(age, 0.0, 0.10)
            land = (1 - u) ** 2
            s_ = k * (1 + 0.55 * land)
            if self.kind == "ink":
                ty.draw(c, gx, gy, self.ink, scale=s_)
                continue
            # the depth is along the light: lower right. In the glyph's own units, so it scales with it
            d = 400 * (0.062 + 0.22 * land)
            n = max(3, int(d / 2.2))
            line = 9.0
            c.save()
            c.translate(gx, gy)
            c.scale(s_, s_)
            paint_ink = skia.Paint(AntiAlias=True, Color4f=E.col(E.INK), Style=skia.Paint.kStroke_Style, StrokeWidth=line, StrokeJoin=skia.Paint.kRound_Join)
            paint_side = skia.Paint(AntiAlias=True, Color4f=E.col(self.side))
            c.translate(-(ty.l + ty.w / 2), -(ty.t + ty.h / 2))
            for layer in range(n, -1, -1):
                f = layer / n
                c.save()
                c.translate(0.62 * d * f, 0.78 * d * f)
                c.drawPath(ty.path, paint_ink)
                c.restore()
            for layer in range(n, 0, -1):
                f = layer / n
                c.save()
                c.translate(0.62 * d * f, 0.78 * d * f)
                c.drawPath(ty.path, paint_side)
                c.restore()
            c.translate(ty.l + ty.w / 2, ty.t + ty.h / 2)
            ty.draw(c, 0, 0, self.face, stroke=(E.INK, line))
            c.restore()
        c.restore()


class Cam:
    """A pinhole at 1920 x 1080, the same as Blender's for these stills. plane() is the matrix from a plane's own units to the screen."""

    def __init__(self, eye, target, up, lens):
        e = np.array(eye, np.float64)
        fw = np.array(target, np.float64) - e
        fw /= np.linalg.norm(fw)
        r = np.cross(fw, np.array(up, np.float64))
        r /= np.linalg.norm(r)
        d = np.cross(fw, r)
        f = lens / 36 * 1920
        self.A = np.vstack([f * r + 960 * fw, f * d + 540 * fw, fw])
        self.b = -self.A @ e

    def project(self, p):
        q = self.A @ np.array(p, np.float64) + self.b
        return float(q[0] / q[2]), float(q[1] / q[2])

    def plane(self, o, ex, ey):
        H = np.column_stack([self.A @ np.array(ex, np.float64), self.A @ np.array(ey, np.float64), self.A @ np.array(o, np.float64) + self.b])
        H = H / H[2, 2]
        return skia.Matrix.MakeAll(*[float(v) for v in H.flatten()])


def about(m, fac):
    """The flat views' depth: the matrix m seen from nearer the vanishing point, so the raised face slides away from it."""
    return skia.Matrix.Concat(skia.Matrix.Translate(VP[0], VP[1]), skia.Matrix.Concat(skia.Matrix.Scale(fac, fac), skia.Matrix.Concat(skia.Matrix.Translate(-VP[0], -VP[1]), m)))


def flat_frame(m, s_):
    # a nearer camera shows the same block deeper: the height it is seen from goes with the zoom
    return lambda h: about(m, 1 + h * min(s_, 1.6) / 1000.0)


class Stamp:
    """Block type lying on a surface: a word set straight, each syllable landing on its own time. x, y, em are in the surface's units. frame(h) gives the matrix from those units at height h above the surface to the screen, so its depth is real: side faces close on the vanishing point, as in the 3D 寒い."""

    def __init__(self, x, y, em, times, text="寒い", face=FACE, side=SIDE, depth=0.07, stretch=1.0, row=0):
        self.x, self.y, self.em, self.face, self.side, self.depth, self.stretch, self.row = x, y, em, face, side, depth, stretch, row
        self.glyphs = []
        advs = [0.98 for ch in text]
        pos = np.cumsum([0.0] + [(a_ + b_) / 2 for a_, b_ in zip(advs, advs[1:])])
        pos = pos - pos[-1] / 2
        for i, ch in enumerate(text):
            self.glyphs.append((glyph(ch), float(pos[i]), 0.92 if ch in "いッ" else 1.0, times[i]))
        self.t0 = times[0]

    def draw(self, c, t, frame):
        for ty, gx, k, tg in self.glyphs:
            age = t - tg
            if age < 0:
                continue
            land = (1 - E.seg(age, 0.0, 0.10)) ** 2
            s_ = k * self.em / 400.0 * (1 + 0.55 * land)
            h = self.em * self.depth * (1 + 2.5 * land)
            cx, cy = self.x + gx * self.em, self.y
            # how far the face stands from the surface on the screen says how many layers it takes for the side to be smooth
            a, b, d = frame(0).mapXY(cx, cy), frame(h).mapXY(cx, cy), frame(0).mapXY(cx + 1, cy)
            spread = math.hypot(a.x() - b.x(), a.y() - b.y())
            unit = math.hypot(d.x() - a.x(), d.y() - a.y())       # screen pixels per surface unit
            n = int(min(max(spread / 1.2, 2), 240))
            # one line weight whatever the size: a little heavier on the big ones, as in the 3D 寒い
            line = (1.9 + 0.0055 * self.em * unit) / max(s_ * unit, 1e-6)
            local = skia.Matrix.Concat(skia.Matrix.Translate(cx, cy), skia.Matrix.Concat(skia.Matrix.Scale(s_, s_ * self.stretch), skia.Matrix.Translate(-(ty.l + ty.w / 2), -(ty.t + ty.h / 2))))
            ink = skia.Paint(AntiAlias=True, Color4f=E.col(E.INK), Style=skia.Paint.kStroke_Style, StrokeWidth=line, StrokeJoin=skia.Paint.kRound_Join)
            side = skia.Paint(AntiAlias=True, Color4f=E.col(self.side))
            face = skia.Paint(AntiAlias=True, Color4f=E.col(self.face))
            for paint, last in ((ink, 0), (side, 1)):
                for layer in range(0, n + 1 - last):
                    c.save()
                    c.setMatrix(skia.Matrix.Concat(frame(h * layer / n), local))
                    c.drawPath(ty.path, paint)
                    c.restore()
            c.save()
            c.setMatrix(skia.Matrix.Concat(frame(h), local))
            c.drawPath(ty.path, ink)
            c.drawPath(ty.path, face)
            c.restore()


def jolt(t, hits, amp=9.0, seed=5):
    """Every landing shakes the camera a little: where to, and how much nearer. It settles in a fifth of a second."""
    last = None
    n = 0
    for i, h in enumerate(hits):
        if t >= h:
            last, n = h, i
    if last is None:
        return 0.0, 0.0, 1.0
    f = math.exp(-(t - last) * 15.0)
    a = (n * 2.399 + seed)
    return amp * f * math.cos(a), amp * f * math.sin(a), 1.0 + 0.016 * f


def poly(pts):
    p = skia.Path()
    p.moveTo(float(pts[0][0]), float(pts[0][1]))
    for q in pts[1:]:
        p.lineTo(float(q[0]), float(q[1]))
    p.close()
    return p


def fill(col, a=1.0):
    return skia.Paint(AntiAlias=True, Color4f=E.col(col, a))


def ink_line(w, col=E.INK):
    return skia.Paint(AntiAlias=True, Color4f=E.col(col), Style=skia.Paint.kStroke_Style, StrokeWidth=w, StrokeJoin=skia.Paint.kRound_Join)


# ---- camera of the push shot: lying on the floor, looking along the door. Units are 21.6 cm: the camera is at height H ----
PS = 1.0                         # the hand picture's scale
PH, PF = 0.37, 2046.0
GAP_H = 0.25                     # the same 5.5 cm as in the 3D room: a shoe can be seen through it
REACH = 0.85
UNIT = 0.216
FEET = ((2.75, -1), (4.10, 1))   # where each shoe stands along the door, and which side of it is its outside: the sheet goes out between them
TOE_GAP = 0.043                  # toe caps right up behind the door's plane, metres
LAMP = (5.63, 3.575, 0.54)
LOAFER_TONES = dict(upper=("#3A2318", "#7D6248"), strap=("#311C13", "#6B5340"), sole=("#120E0E", "#120E0E"))


class Push:
    """Projection anchored on the picture: the sheet in h03_push has its own vanishing point, and the room takes it over."""

    def __init__(self, x0, y0, nudge):
        self.x0, self.y0 = x0, y0
        tip = (x0 + PS * 1640 + nudge, y0 + PS * 700)
        self.yh = y0 + PS * 467
        self.vx = tip[0] - (tip[1] - self.yh) / PH

    def on_floor(self, x, z):
        """x = 1 is the door's plane; smaller is further into the room."""
        return self.vx + PF * x / z, self.yh + PF * PH / z

    def on_door(self, z, y):
        return self.vx + PF / z, self.yh + PF * (PH - y) / z


def make_snow(n=150, seed=23):
    rng = np.random.default_rng(seed)
    order = rng.random(n)
    return [(rng.uniform(-60, 1980), rng.uniform(0, 1200), rng.uniform(38, 140), rng.uniform(1.8, 5.5) * (1.0 + 1.1 * rng.random() ** 4), rng.uniform(0, math.tau), o) for o in order]


class Wall(E.Clip):
    name = "s11b"
    t0, t1 = T0, T1
    cuts = tuple(HITS[5:10]) + (WALL_AT, RUSH[1]) + tuple((row[0] - 0.5) / 30 for row in PUSH_POSES)
    shutter = 0.35

    def setup(self):
        self.tape51 = K.Strip("寒い寒い寒い寒い寒い", K.chars_of(51, "寒い寒い寒い寒い寒い"), size=44)
        self.tape52 = K.Strip("寒い寒い寒い寒い寒い", K.chars_of(52, "寒い寒い寒い寒い寒い"), size=44)
        self.tape53 = K.Strip("寒い寒い寒い寒いお願いだから", K.chars_of(53, "寒い寒い寒い寒いお願いだから"), size=44)
        # 寒 on the sung さ and い on むい, word by word
        ch = K.chars_of(51, "寒い寒い寒い寒い寒い") + K.chars_of(52, "寒い寒い寒い寒い寒い") + K.chars_of(53, "寒い寒い寒い寒い")
        self.syl = [(ch[i], ch[i + 1]) for i in range(0, len(ch), 2)]
        self.make_hands()
        self.make_flowers()
        self.layout_floor()
        self.layout_door()
        self.layout_wall()
        self.layout_push()
        self.flower_sheet_img = None
        self.shoes_img = None
        self.snow = make_snow()

    def draw_snow(self, c, t):
        # none on the first word, nearly all of it by the last
        last = 0
        for k, h in enumerate(HITS):
            if t >= h:
                last = k
        have = (last / 13.0) ** 1.3
        white = fill("#FFFFFF")
        q = math.floor(t * 15 + 1e-6) / 15
        for x, y, v, r, ph, o in self.snow:
            if o > have:
                continue
            yy = (y + v * q) % 1200 - 60
            xx = x + 14 * math.sin(q * 1.3 + ph)
            c.drawCircle(xx, yy, r, white)

    # ---- pictures ----
    def make_hands(self):
        self.push = {}
        for _, key, name, _ in PUSH_POSES:
            im = C.load(ROOT / "assets" / "gen" / "cut" / f"{name}.png")
            im, off = carry_on(im, "left", 1200)
            ys, xs = np.where(im[..., 3] > 0.5)
            i = xs.argmax()
            # where the fingertips touch: the lowest point near the tip
            near = xs > xs.max() - 120
            self.push[key] = (E.np_to_image(night(im)), float(xs[i]), float(ys[near].max()), E.np_to_image(door_rim(im)))

    def make_flowers(self):
        raw = cv2.imread(str(ROOT / "assets" / "gen" / "raw" / "k01_flowers.png"))[..., ::-1].astype(np.float32) / 255
        raw = raw[60:980, 60:1480]
        ink = np.clip(1 - raw.min(-1) * 0.5 - raw.mean(-1) * 0.5, 0, 1)
        # the front, as it is
        a = np.clip(ink * 3, 0, 1)
        self.flowers = E.np_to_image(np.dstack([raw, a]))
        # the back: the same flowers, mirrored, showing faintly through the paper
        tone = np.full(raw.shape, 0.36, np.float32)
        tone[..., 2] = 0.46
        self.show_through = E.np_to_image(np.dstack([tone, (np.clip(ink * 2.4, 0, 1) * 0.12)])[:, ::-1])

    def paper(self, c, w, h, color=PAPER, back=True):
        E.rect(c, 0, 0, w, h, color)
        if back:
            s = w * 0.90 / self.show_through.width()
            E.draw_image(c, self.show_through, w / 2, h * 0.42, s)

    def sheet_raster(self, word=None, color=PAPER, front=False, ws=1.0, k=1.0, tone=None):
        """word is a size: 寒い set small and upright in the middle of the sheet."""
        pw, ph = int(SHEET_PX[0] * k), int(SHEET_PX[1] * k)
        surf = skia.Surface(pw, ph)
        c = surf.getCanvas()
        s = pw / SHEET_W
        c.scale(s, s)
        if front:
            E.rect(c, 0, 0, SHEET_W, SHEET_H, color)
            E.draw_image(c, self.flowers, SHEET_W / 2, SHEET_H * 0.44, SHEET_W * 0.92 / self.flowers.width())
        else:
            self.paper(c, SHEET_W, SHEET_H, color)
        if word is not None:
            Word(SHEET_W / 2, SHEET_H / 2, word * ws, 0.0, (-9.0, -9.0)).draw(c, 0.0)
        if tone is not None:
            p = skia.Paint(Color4f=skia.Color4f(*tone, 1.0))
            p.setBlendMode(skia.BlendMode.kMultiply)
            c.drawRect(skia.Rect.MakeWH(SHEET_W, SHEET_H), p)
        return surf.makeImageSnapshot()

    def put_sheet(self, c, img, cx, cy, rot, s, shadow=None):
        w, h = SHEET_W * s, SHEET_H * s
        c.save()
        c.translate(cx, cy)
        c.rotate(rot)
        if shadow:
            a = math.radians(-rot)
            dx, dy = shadow[0] * math.cos(a) - shadow[1] * math.sin(a), shadow[0] * math.sin(a) + shadow[1] * math.cos(a)
            E.rect(c, -w / 2 + dx, -h / 2 + dy, w, h, E.INK, SHADOW_A)
        c.scale(w / img.width(), h / img.height())
        c.drawImage(img, -img.width() / 2, -img.height() / 2, E.SAMPLING_DOWN)
        c.restore()
        c.save()
        c.translate(cx, cy)
        c.rotate(rot)
        c.drawRect(skia.Rect.MakeXYWH(-w / 2, -h / 2, w, h), ink_line(max(1.4, 3.0 * s)))
        c.restore()

    # ---- floor: the first five ----
    def layout_floor(self):
        self.floor_pos = [(0, 0, -1.5), (690, -170, 3.0), (-480, 640, -4.5), (610, 890, 5.5), (1290, 420, -8.0)]
        self.pile = pile_image()
        self.pile_quads = []
        for i in range(len(S.SHEETS)):
            tl, tr, bl = S.sheet_axes(i, S.T2)
            br = (tr[0] + bl[0] - tl[0], tr[1] + bl[1] - tl[1], tl[2])
            self.pile_quads.append([floor_to_world(p[0], p[1]) for p in (tl, tr, br, bl)])
        # the ones that came under the door and are still flower side up
        self.flower_pos = [(-760, -240, 9.0), (150, -950, -12.0), (-1250, 500, 16.0), (1420, -700, -7.0), (-250, 1500, 6.0), (1500, 1320, 13.0)]
        self.blank = None
        # Set out on the final view, in screen pixels: the first alone in the middle, each hit further out and bigger, nothing on top of anything. All straight, like the boards.
        cx, cy, s_ = self.floor_view(HITS[5], jolt_=False)
        self.floor_words = []
        for i, sx, sy, em in FLOOR_SET:
            self.floor_words.append(Stamp(cx + (sx - 960) / s_, cy + (sy - 500) / s_, em / s_, self.syl[i]))

    def floor_view(self, t, jolt_=True):
        """One continuous move back from the first sheet, and each landing jolts it."""
        k = E.ease_io(E.seg(t, HITS[0] - 0.05, HITS[5]), 1.5)
        s_ = math.exp(math.log(PILE_S0) + (math.log(0.56) - math.log(PILE_S0)) * k)
        dx, dy, z = jolt(t, HITS[:5], 7.0) if jolt_ else (0.0, 0.0, 1.0)
        return (0 + 0 * k - dx / s_, 0 + 40 * k - dy / s_, s_ * z)

    def floor_transform(self, c, view):
        cx, cy, s = view
        c.translate(960, 500)
        c.scale(s, s)
        c.translate(-cx, -cy)

    def floor_matrix(self, view):
        cx, cy, s = view
        return skia.Matrix.Concat(skia.Matrix.Translate(960, 500), skia.Matrix.Concat(skia.Matrix.Scale(s, s), skia.Matrix.Translate(-cx, -cy)))

    def draw_floor_base(self, c, view, flowers=True):
        c.clear(E.col(FLOOR))
        s = view[2]
        x0 = view[0] - 960 / s
        x1 = view[0] + 960 / s
        y0 = view[1] - 560 / s
        y1 = view[1] + 600 / s
        c.save()
        self.floor_transform(c, view)
        step = 330
        for k in range(int(math.floor(y0 / step)), int(math.ceil(y1 / step)) + 1):
            E.rect(c, x0, k * step, x1 - x0, 6, FLOOR_LINE)
        if flowers:
            if self.flower_sheet_img is None:
                self.flower_sheet_img = self.sheet_raster(color=PAPER, front=True, tone=NIGHT_LOW)
            for x, y, r in self.flower_pos:
                self.put_sheet(c, self.flower_sheet_img, x, y, r, 1.0, shadow=(14, 18))
        c.restore()

    def draw_floor(self, c, t):
        view = self.floor_view(t)
        self.draw_floor_base(c, view, flowers=False)
        c.save()
        self.floor_transform(c, view)
        # the pile the camera came down on, every sheet with its crayon
        for q in self.pile_quads:
            c.drawPath(poly([(x + 14, y + 18) for x, y in q]), fill(E.INK, SHADOW_A))
            c.save()
            c.concat(E.quad_matrix((self.pile.width(), self.pile.height()), q))
            c.drawImage(self.pile, 0, 0, E.SAMPLING_DOWN)
            c.restore()
            c.drawPath(poly(q), ink_line(3.0))
        c.restore()
        fr = flat_frame(self.floor_matrix(view), view[2])
        for w in self.floor_words:
            w.draw(c, t, fr)

    # ---- the room: the next five. Stills from room2, with the door's sheets and the type on the door's plane and the floor, in metres, under whatever stands in front of them ----
    def layout_door(self):
        rng = np.random.default_rng(12)
        self.door_blank = self.sheet_raster(color=PAPER, front=True, tone=NIGHT_DOOR)
        self.hole_plate = E.load_image(PLATES / "hole.png")
        self.views = {}
        for i, n in ((5, 0), (6, 1), (7, 2), (8, 3), (9, 4)):
            self.views[i] = (E.load_image(PLATES / f"room{n}.png"), E.load_image(PLATES / f"room{n}_over.png"), Cam(*ROOM_VIEWS[i]))
        # the door is papered with blank sheets; the handle stays clear
        cols = (-0.225, 0.0, 0.225)
        rows = (0.27, 0.63, 0.99, 1.35, 1.71)
        self.door_sheets = [(S.XD + x + rng.uniform(-0.008, 0.008), z + rng.uniform(-0.008, 0.008), rng.uniform(-3.0, 3.0)) for z in rows for x in cols if not (x > 0.1 and z == 0.99)]
        rng.shuffle(self.door_sheets)
        # rows of type on the door, two to a row. Each new shot sees the rows it has just landed beside the ones already there.
        col = (-0.186, 0.186)
        self.door_words = []
        for i, z, xs in DOOR_SET:
            for k in xs:
                self.door_words.append(Stamp(col[k], -z, 0.19, self.syl[i], depth=0.13, row=z))
        self.door_words.sort(key=lambda w: -w.row)
        # the floor: far rows small, near rows big, and a way left clear down the middle for the light from the gap
        self.room_floor = []
        for i, y, em, xs in ROOM_FLOOR:
            for x in xs:
                self.room_floor.append(Stamp(x, y, em, self.syl[i] if i >= 0 else (-9.0, -9.0), depth=0.09, stretch=1.18, row=y))
        self.room_floor.sort(key=lambda w: w.row)

    def draw_door_sheet(self, c, cam, x, z, r):
        img = self.door_blank
        w, h = 0.27, 0.27 * SHEET_H / SHEET_W
        ca, sa = math.cos(math.radians(r)), math.sin(math.radians(r))

        def corner(u, v):
            return cam.project((x + u * ca + v * sa, 0.0, z - u * sa + v * ca))

        cs = [corner(-w / 2, h / 2), corner(w / 2, h / 2), corner(w / 2, -h / 2), corner(-w / 2, -h / 2)]
        unit = math.hypot(cs[1][0] - cs[0][0], cs[1][1] - cs[0][1]) / w
        off = (0.006 * unit, 0.010 * unit)
        c.drawPath(poly([(a + off[0], b + off[1]) for a, b in cs]), fill(E.INK, SHADOW_A))
        c.save()
        c.concat(E.quad_matrix((img.width(), img.height()), cs))
        c.drawImage(img, 0, 0, E.SAMPLING_DOWN)
        c.restore()
        c.drawPath(poly(cs), ink_line(max(1.2, 0.0026 * unit)))
        # a strip of tape holds it up
        c.drawPath(poly([corner(-0.032, h / 2 + 0.012), corner(0.032, h / 2 + 0.012), corner(0.032, h / 2 - 0.012), corner(-0.032, h / 2 - 0.012)]), fill("#8E97AB"))

    def draw_door(self, c, t, i):
        plate, over, cam = self.views[i]
        dx, dy, z_ = jolt(t, HITS[5:10], 10.0)
        J = skia.Matrix.Concat(skia.Matrix.Translate(960 + dx, 540 + dy), skia.Matrix.Concat(skia.Matrix.Scale(z_ * 1.012, z_ * 1.012), skia.Matrix.Translate(-960, -540)))
        c.save()
        c.setMatrix(J)
        c.drawImage(plate, 0, 0, E.SAMPLING_DOWN)
        for x, z, r in self.door_sheets:
            self.draw_door_sheet(c, cam, x, z, r)
        c.restore()
        floor = lambda h: skia.Matrix.Concat(J, cam.plane((0.0, 0.0, h), (1, 0, 0), (0, -1, 0)))
        door = lambda h: skia.Matrix.Concat(J, cam.plane((S.XD, -h, 0.0), (1, 0, 0), (0, 0, -1)))
        if i in (5, 9):
            for w in self.room_floor:
                w.draw(c, t, floor)
        for w in self.door_words:
            w.draw(c, t, door)
        c.save()
        c.setMatrix(J)
        c.drawImage(over, 0, 0, E.SAMPLING_DOWN)
        c.restore()

    # ---- the wall ----
    def layout_wall(self):
        surf = skia.Surface(E.W, E.H)
        c = surf.getCanvas()
        c.clear(E.col(PAPER_DOOR))
        rng = np.random.default_rng(77)
        sw, sh = 300, 396
        rows, cols = 3, 7
        # one gap is left, and through it the door and its handle
        c.drawImage(self.hole_plate, 0, 0)
        cells = [(i, j) for j in range(rows) for i in range(cols) if (i, j) != (4, 1)]
        rng.shuffle(cells)
        self.wall_ink = []
        # the sheets are blank, and they print themselves: first a few, then more, then all of them
        hit_of = [10] * 7 + [11] * 7 + [12] * 6
        for n, (i, j) in enumerate(cells):
            x = 130 + i * (E.W - 260) / (cols - 1) + rng.uniform(-14, 14)
            y = 180 + j * (E.H - 360) / (rows - 1) + rng.uniform(-10, 10)
            r = rng.uniform(-5, 5)
            c.save()
            c.translate(x, y)
            c.rotate(r)
            E.rect(c, -sw / 2 + 5, -sh / 2 + 7, sw, sh, E.INK, 0.45)
            E.rect(c, -sw / 2, -sh / 2, sw, sh, PAPER if n % 3 else PAPER_DOOR)
            E.draw_image(c, self.flowers, 0, -sh * 0.06, sw * 0.92 / self.flowers.width())
            c.drawRect(skia.Rect.MakeXYWH(-sw / 2, -sh / 2, sw, sh), ink_line(2.2))
            c.restore()
            self.wall_ink.append(Word(x, y, sw * rng.uniform(0.40, 0.56), r, self.syl[hit_of[n]], ink=WALL_INK))
        self.wall_img = surf.makeImageSnapshot()
        self.wall_words = [Stamp(*p, self.syl[i], face=fc, side=sd) for i, p, fc, sd in WALL_SET]
        # where the camera goes in: the widest place in the last 寒, found by measuring it
        last = self.wall_words[-1]
        ty, gx, k_, _ = last.glyphs[0]
        ms = skia.Surface(E.W, E.H)
        mc = ms.getCanvas()
        mc.clear(skia.Color4f(0, 0, 0, 1))
        mc.translate(last.x + gx * last.em, last.y)
        ty.draw(mc, 0, 0, E.PAPER, scale=k_ * last.em / 400.0)
        mask = ms.makeImageSnapshot().toarray(colorType=skia.ColorType.kRGBA_8888_ColorType, alphaType=skia.AlphaType.kOpaque_AlphaType)[..., 0]
        dist = cv2.distanceTransform((mask > 128).astype(np.uint8), cv2.DIST_L2, 5)
        y_, x_ = np.unravel_index(int(dist.argmax()), dist.shape)
        self.rush_at = (float(x_), float(y_))
        self.rush_k = 1160.0 / float(dist.max())

    def draw_wall(self, c, t):
        c.clear(E.col(PAPER_DOOR))
        dx, dy, z_ = jolt(t, HITS[10:14], 14.0)
        k = 1.0
        fx, fy = 960.0, 540.0
        if t >= RUSH[0]:
            u = E.seg(t, *RUSH)
            k = math.exp(math.log(self.rush_k) * u ** 1.8)
            fx, fy = self.rush_at
            f = E.ease_out(min(u * 1.6, 1.0), 1.6)
            fx, fy = 960 + (fx - 960) * f, 540 + (fy - 540) * f
            fx, fy = min(max(fx, 960 / k), E.W - 960 / k), min(max(fy, 540 / k), E.H - 540 / k)
        M = skia.Matrix.Concat(skia.Matrix.Translate(960 + dx, 540 + dy), skia.Matrix.Concat(skia.Matrix.Scale(z_ * k, z_ * k), skia.Matrix.Translate(-fx, -fy)))
        c.save()
        c.setMatrix(M)
        c.drawImage(self.wall_img, 0, 0, E.SAMPLING_DOWN)
        for w in self.wall_ink:
            w.draw(c, t)
        c.restore()
        fr = flat_frame(M, z_)
        for w in self.wall_words:
            w.draw(c, t, fr)

    # ---- one sheet: パッパ. It comes up out of the dark of the stroke; it lies across, the way it will go under the door ----
    def draw_last_sheet(self, c, t):
        u = E.ease_out(E.seg(t, *SHEET_LAND), 2.4)
        s_ = 0.86 * math.exp(math.log(0.18) * (1 - u)) * (1 + 0.035 * E.seg(t, SHEET_LAND[1], PUSH_AT))
        view = (0.0, 20.0, s_)
        self.draw_floor_base(c, view)
        dx, dy, z_ = jolt(t, PA, 8.0)
        c.save()
        c.translate(dx, dy)
        self.floor_transform(c, view)
        for x, y, r, size in ((-1010, -620, 5.0, 300), (1020, -640, -4.0, 300), (-1080, 560, -6.0, 300), (1090, 590, 7.0, 300), (20, -1040, 3.0, 300), (-40, 1000, -3.0, 300)):
            self.put_sheet(c, self.floor_img(size), x, y, r, 1.0, shadow=(14, 18))
        c.rotate(-2.0)
        sw, sh = SHEET_H, SHEET_W
        E.rect(c, -sw / 2 + 14, -sh / 2 + 18, sw, sh, E.INK, SHADOW_A)
        E.rect(c, -sw / 2, -sh / 2, sw, sh, PAPER)
        c.drawRect(skia.Rect.MakeXYWH(-sw / 2, -sh / 2, sw, sh), ink_line(3.0))
        self.pappa_word.draw(c, t)
        c.restore()

    def floor_img(self, size):
        if not hasattr(self, "_floor_imgs"):
            self._floor_imgs = {}
        if size not in self._floor_imgs:
            self._floor_imgs[size] = self.sheet_raster(None, color=PAPER, front=True, k=1.6, tone=NIGHT_LOW)
        return self._floor_imgs[size]

    # ---- under the door ----
    def layout_push(self):
        self.push_x0, self.push_y0 = -200.0, 110.0
        self.P = Push(self.push_x0, self.push_y0, 30.0)
        rng = np.random.default_rng(31)
        # the door is covered, right down to the gap
        self.push_door = []
        for row in range(7):
            for col in range(5):
                z0 = 1.65 + col * 0.98 + rng.uniform(-0.05, 0.05)
                y0 = 0.16 + row * 1.40 + rng.uniform(-0.05, 0.05)
                self.push_door.append((z0, y0, self.sheet_raster(None, color=PAPER, front=True, tone=NIGHT_PUSH)))
        self.push_floor = []
        for n in range(16):
            z = 1.5 + n * 0.42
            x = rng.uniform(-3.8, -0.55) if z < 3.0 else rng.uniform(-3.4, -0.7)
            self.push_floor.append((x, z, rng.uniform(-40, 40), self.sheet_raster(None, color=PAPER, front=True, tone=NIGHT_LOW)))
        self.push_floor.sort(key=lambda s: -s[1])
        self.pappa_word = Word(0.0, 0.0, 340.0, 0.0, PA, text="パッパ", vertical=False)
        self.word_on_sheet = Word(0.0, 0.0, 150.0, 0.0, (-9.0, -9.0, -9.0), text="パッパ", vertical=False)

    def sheet_on_floor(self, c, img, x, d, rot, project, w=0.21, h=0.297):
        a = math.radians(rot)
        ca, sa = math.cos(a), math.sin(a)
        cs = []
        for u, v in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
            lx, ly = u * w / 2, v * h / 2
            cs.append(project(x + lx * ca - ly * sa, d + lx * sa + ly * ca))
        c.save()
        c.concat(E.quad_matrix((img.width(), img.height()), cs))
        c.drawImage(img, 0, 0, E.SAMPLING_DOWN)
        c.restore()
        c.drawPath(poly(cs), ink_line(1.6))

    def make_push_shoes(self):
        """The same two loafers as in the 3D room, standing just behind the door, seen from the floor on the room side. Flat tones: a dark side, and one warm rim towards the lamp behind them.
        Filled without antialiasing at three times the size and then reduced, so no seam can show between the facets."""
        P = self.P
        K_ = 3
        rgb = np.zeros((E.H * K_, E.W * K_, 3), np.uint8)
        mask = np.zeros((E.H * K_, E.W * K_), np.uint8)

        def proj(q):
            return P.vx + PF * q[0] / q[1], P.yh + PF * (PH - q[2]) / q[1]

        def pix(pts):
            return np.round(np.array(pts, np.float64) * K_ * 16).astype(np.int32)

        def tone(col):
            h = col.lstrip("#")
            return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))

        heel = TOE_GAP + S.SHOE_LEN
        a_ = math.radians(S.STANCE_SPLAY)
        for zc, side in reversed(FEET):
            sh = S.loafer(S.SHOE_LEN, side)

            def place(p_):
                xs, ys, zs = p_
                x_ = xs * math.cos(a_) - ys * side * math.sin(a_)
                y_ = ys * math.cos(a_) + xs * side * math.sin(a_)
                return 1 + (heel + y_) / UNIT, zc + x_ / UNIT, zs / UNIT

            one = np.zeros(mask.shape, np.uint8)
            # the ankle going up out of sight behind the door
            ax = 1 + (heel - 0.058) / UNIT
            ankle = pix([proj((ax, zc - 0.16, 0.2)), proj((ax, zc + 0.16, 0.2)), proj((ax, zc + 0.16, 1.2)), proj((ax, zc - 0.16, 1.2))])
            cv2.fillConvexPoly(rgb, ankle, tone("#20243A"), cv2.LINE_8, 4)
            cv2.fillConvexPoly(one, ankle, 255, cv2.LINE_8, 4)
            quads = []
            for kind in ("sole", "upper", "strap"):
                rings = [[place(p_) for p_ in ring] for ring in sh[kind]]
                for r0, r1 in zip(rings, rings[1:]):
                    centre = [sum(v) / (2 * len(r0)) for v in zip(*(r0 + r1))]
                    for k in range(len(r0)):
                        q = (r0[k], r0[(k + 1) % len(r0)], r1[(k + 1) % len(r0)], r1[k])
                        m = [sum(v) / 4 for v in zip(*q)]
                        e1 = [y - x for x, y in zip(q[0], q[2])]
                        e2 = [y - x for x, y in zip(q[1], q[3])]
                        n = (e1[1] * e2[2] - e1[2] * e2[1], e1[2] * e2[0] - e1[0] * e2[2], e1[0] * e2[1] - e1[1] * e2[0])
                        if sum(x * (y - w) for x, y, w in zip(n, m, centre)) < 0:
                            n = tuple(-v for v in n)
                        # only what turns up and towards the lamp catches it: a rim, not a whole side of the shoe
                        to_lamp = [y - w for y, w in zip(LAMP, m)]
                        nl = math.sqrt(sum(v * v for v in n)) or 1.0
                        lit = sum(x * y for x, y in zip(n, to_lamp)) / (nl * math.sqrt(sum(v * v for v in to_lamp))) > 0.02 and n[2] / nl > 0.45
                        quads.append((m[0] ** 2 + m[1] ** 2 + (PH - m[2]) ** 2, kind, lit, pix([proj(v) for v in q])))
            quads.sort(key=lambda s_: -s_[0])
            for _, kind, lit, pts in quads:
                cv2.fillConvexPoly(rgb, pts, tone(LOAFER_TONES[kind][1 if lit else 0]), cv2.LINE_8, 4)
                cv2.fillConvexPoly(one, pts, 255, cv2.LINE_8, 4)
            cv2.polylines(rgb, [pix([proj(place(q)) for q in sh["seam"]])], False, tone("#120B0B"), 2 * K_, cv2.LINE_8, 4)
            # one thin ink outline round the whole shoe
            edge = cv2.dilate(one, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * 2 * K_ + 1, 2 * 2 * K_ + 1))) > 0
            edge &= one == 0
            ink = np.array([int(E.INK.lstrip("#")[i:i + 2], 16) for i in (0, 2, 4)], np.uint8)
            rgb[edge & (mask == 0)] = ink
            mask |= edge.astype(np.uint8) * 255 | one
        premul = cv2.resize(rgb.astype(np.float32) * (mask[..., None] > 0), (E.W, E.H), interpolation=cv2.INTER_AREA) / 255
        alpha = cv2.resize((mask > 0).astype(np.float32), (E.W, E.H), interpolation=cv2.INTER_AREA)
        return E.np_to_image(np.dstack([premul / np.maximum(alpha[..., None], 1e-3), alpha]).astype(np.float32))

    def draw_push(self, c, t):
        P = self.P
        c.clear(E.col(WALL))
        # the far wall, the floor, and the wall the door is in
        back_z = 9.0
        by = P.on_floor(0, back_z)[1]
        E.rect(c, 0, by - 30, E.W, 30, "#232E60")
        E.rect(c, 0, by, E.W, E.H - by, FLOOR)
        # floorboards run away from us
        for xx in np.arange(-14, 1.0, 1.5):
            a = P.on_floor(xx, 1.3)
            b = P.on_floor(xx, back_z)
            c.drawLine(a[0], a[1], b[0], b[1], skia.Paint(AntiAlias=True, Color4f=E.col(FLOOR_LINE), StrokeWidth=2.5))
        # what comes through the gap: a low wedge of light on the floor, the two shoes' shadows lying in it
        door_near, door_far = 1.45, 5.70

        def thrown(z, reach):
            mid = (door_near + door_far) / 2
            return P.on_floor(1 - reach, mid + (z - mid) * (1 + reach * 0.35))

        c.drawPath(poly([P.on_floor(1, door_near), P.on_floor(1, door_far), thrown(door_far, REACH), thrown(door_near, REACH)]), fill("#8F8E9C"))
        c.drawPath(poly([P.on_floor(1, door_near), P.on_floor(1, door_far), thrown(door_far, 0.30), thrown(door_near, 0.30)]), fill("#D8CDAF"))
        # the sheets lie on the floor further back; the light does not reach them
        for x, z, r, img in self.push_floor:
            self.sheet_on_floor(c, img, x, z, r, P.on_floor, w=0.97, h=1.37)
        # the gap itself: light all along it, except for the shoes standing behind it
        gap = poly([P.on_door(door_near, GAP_H), P.on_door(door_far, GAP_H), P.on_door(door_far, 0), P.on_door(door_near, 0)])
        c.drawPath(gap, fill(LIGHT))
        # each shoe's shadow: one clean band out from under its toe, through the gap and across the light, the same as in the room
        for zc, side in FEET:
            toe = 1 + TOE_GAP / UNIT + 0.2
            c.drawPath(poly([P.on_floor(toe, zc - 0.20), P.on_floor(toe, zc + 0.20), P.on_floor(1, zc + 0.22), thrown(zc + 0.34, REACH), thrown(zc - 0.34, REACH), P.on_floor(1, zc - 0.22)]), fill("#151D46"))
        c.save()
        c.clipPath(gap, True)
        if self.shoes_img is None:
            self.shoes_img = self.make_push_shoes()
        c.drawImage(self.shoes_img, 0, 0)
        c.restore()
        # the door: everything on its plane from the gap up
        top = -0.2

        def d(z, y):
            return P.on_door(z, y)

        far_top = (d(door_far, 0)[0], top)
        c.drawPath(poly([(P.vx, P.yh), d(door_far + 0.02, 0), (d(door_far + 0.02, 0)[0], -10), (P.vx, -10)]), fill(WALL))
        c.drawPath(poly([d(door_far, GAP_H), d(door_near - 1.2, GAP_H), (2600, -10), (d(door_far, 0)[0], -10)]), fill(DOOR))
        c.save()
        c.clipPath(poly([d(door_far, GAP_H), d(door_near - 1.2, GAP_H), (2600, -10), (d(door_far, 0)[0], -10)]), True)
        for z0, y0_, img in sorted(self.push_door, key=lambda s: -s[0]):
            cs = [d(z0, y0_ + 1.37), d(z0 - 0.97, y0_ + 1.37), d(z0 - 0.97, y0_), d(z0, y0_)]
            c.save()
            c.concat(E.quad_matrix((img.width(), img.height()), cs))
            c.drawImage(img, 0, 0, E.SAMPLING_DOWN)
            c.restore()
            c.drawPath(poly(cs), ink_line(1.8))
        c.restore()
        a, b = d(door_far, GAP_H), d(door_near - 1.2, GAP_H)
        c.drawLine(a[0], a[1], b[0], b[1], ink_line(4.0))
        c.drawLine(far_top[0], -10, a[0], a[1], ink_line(3.5))

        # ---- the sheet and the arm. The sheet is a real shape on the floor: what has passed the door's plane is under the door and gone. ----
        tw = T0 + math.floor((t - T0) * 15 + 1e-6) / 15     # on twos: the arm is three drawings
        pose = PUSH_POSES[0][1]
        for f_, key, _, _ in PUSH_POSES:
            if t >= (f_ - 0.5) / 30:
                pose = key
        xt = PUSH_RUN[2] + (PUSH_RUN[3] - PUSH_RUN[2]) * E.ease_io(E.seg(tw, PUSH_RUN[0], PUSH_RUN[1]), 1.5)
        # then it goes on without her: somebody on the other side has taken it
        hand_xt = xt
        xt = xt + (1.08 - xt) * E.seg(tw, TAKEN[0], TAKEN[1]) ** 2
        z0, z1 = 3.02, 3.72           # near and far edge of the sheet along the door
        ln = 1.12                     # its length, along the way it goes
        if xt < 1.0:
            front = xt + ln
            c.save()
            c.clipPath(poly([P.on_floor(1, 1.2), P.on_floor(1, 9), (-2000, by), (-2000, 1400), (P.on_floor(1, 1.2)[0], 1400)]), True)
            # its shadow on the floor, a few pixels, on the side away from the door's light
            sq = [P.on_floor(xt, z0), P.on_floor(front, z0), P.on_floor(front, z1), P.on_floor(xt, z1)]
            c.drawPath(poly([(x_ - 5, y_ + 4) for x_, y_ in sq]), fill(E.INK, 0.7))
            c.drawPath(poly(sq), fill(PAPER))
            c.drawPath(poly(sq), ink_line(2.4))
            # パッパ flat on it, the way she wrote it, along the sheet
            m0, m1 = xt + 0.14, xt + ln - 0.12
            quad = [P.on_floor(m0, z1 - 0.10), P.on_floor(m1, z1 - 0.10), P.on_floor(m1, z0 + 0.04), P.on_floor(m0, z0 + 0.04)]
            c.save()
            c.concat(E.quad_matrix((460, 200), quad))
            c.translate(230, 100)
            self.word_on_sheet.draw(c, 0.0)
            c.restore()
            c.restore()
        # the arm: three drawings. Fingertips on the sheet's near end, on the floor; a hard shadow lies under it.
        img, nx, ny, rim = self.push[pose]
        tip = P.on_floor(hand_xt + 0.27, (z0 + z1) / 2 - 0.12)
        sh = fill(E.INK, 0.55)
        c.drawPath(poly([(tip[0] + 6, tip[1] + 3), (tip[0] - 520, tip[1] + 3), (tip[0] - 1400, tip[1] + 34), (tip[0] - 1400, tip[1] + 58), (tip[0] - 520, tip[1] + 16)]), sh)
        c.save()
        c.translate(tip[0], tip[1])
        c.scale(PUSH_K[pose], PUSH_K[pose])
        c.drawImage(img, -nx * PS, -ny * PS, E.SAMPLING_DOWN)
        c.restore()
        # the fingers that have come over the bright strip by the door catch its light from below
        xl = P.on_floor(0.70, (z0 + z1) / 2)[0]
        if tip[0] > xl - 60:
            c.save()
            c.clipPath(poly([(xl + 70, tip[1] - 400), (E.W + 10, tip[1] - 400), (E.W + 10, tip[1] + 100), (xl - 22, tip[1] + 100)]), True)
            c.translate(tip[0], tip[1])
            c.scale(PUSH_K[pose], PUSH_K[pose])
            c.drawImage(rim, -nx * PS, -ny * PS, E.SAMPLING_DOWN)
            c.restore()

    # ---- which shot ----
    def draw(self, c, t):
        if t >= PUSH_AT:
            self.draw_push(c, t)
        elif t >= RUSH[1]:
            self.draw_last_sheet(c, t)
        elif t >= WALL_AT:
            self.draw_wall(c, t)
        elif t < DOOR_AT:
            self.draw_floor(c, t)
        else:
            i = 5
            for k in range(5, 10):
                if t >= HITS[k]:
                    i = k
            self.draw_door(c, t, i)
        if t < PUSH_AT:
            self.draw_snow(c, t)
        if t < HITS[5]:
            self.tape51.draw(c, 960, 1034, t, ax=0.5)
        elif t < WALL_AT:
            self.tape52.draw(c, 960, 1034, t, ax=0.5)
        else:
            self.tape53.draw(c, 960, 1034, t, ax=0.5)

    def blur(self, t):
        # no shutter here: a few prints of a hard-edged word only make a staircase
        return 1
