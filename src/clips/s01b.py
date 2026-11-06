"""Opening, extended: the media machine turns. Weekly magazines slam onto the table, one photo runs through five
phones, the five black bars become one, and the camera pushes into the photo. The photo was taken from where the 3D
camera stands: at Z_GATE it lies exactly on the first frame of the gate. The push goes on into the dots, and on the singer's
first word s02a comes back out of the same dots, on the same lattice, and what they print by then is the gate itself.

The band accents every fourth beat (beats 23, 27, 31, 35, 39, 43, 47): the sections hang on those.
"""
import math
import sys
from pathlib import Path

import cv2
import numpy as np
import skia

sys.path.insert(0, str(Path(__file__).parent))
import common as K  # noqa: E402
import engine as E  # noqa: E402
import bar as B  # noqa: E402
import c1  # noqa: E402
import cutout as C  # noqa: E402
from timeline import beat_time as BT  # noqa: E402

ROOT = K.ROOT
M = "ShipporiMinchoB1-ExtraBold"
GB = "ZenKakuGothicNew-Black"
GD = "ZenKakuGothicNew-Bold"
GM = "ZenKakuGothicNew-Medium"
PEN = "YuseiMagic-Regular"
GREY = "#6C7078"
RULE = "#CFCCC2"

T_FEED = BT(31)    # 14.65  the magazines have become posts: each cover drops into a phone that has come up under it, and lands on the accent
T_DROP = BT(30) + 0.14   # the last cover has stopped shaking the table: the covers lift off it
T_HIT = 0.16             # how long the phones feel the landing
T_STOP = BT(39)    # 18.34  every feed lands in line
T_JOIN = BT(40)    # 18.80  the bars run out and meet
T_PUSH = BT(41)    # 19.26  the camera starts for the gate
T_END = 681 / 30

# ---------------------------------------------------------------- print: three flat inks in dots
CELL = 8.0                      # dot pitch of the feed photo, in photo units
PW, PH = 1536, 1920             # the feed photo
Z0 = 320 / PW                   # photo unit to screen in the phones
FIG_S = 2.3                     # t02 in the photo
HEAD_PX, BAR_PY = 1085.0, 1046.0
RAW_BAR = (452, 410, 205, 86, 0.0, 214)
# the first frame of the 3D gate lies in the photo with its left edge on the photo's, and its centre here:
GATE_M = 1000.0 / E.W           # photo units per pixel of that frame
TARGET = (500.0, 560.0)         # the middle of the frame, in photo units
DOOR = (502.6, 596.5)           # the door, where the camera ends up looking
Z_GATE = 1 / GATE_M             # photo fills the screen and lies on the gate
Z_APEX = 25.0                   # how far into the dots it goes
BOOST_APEX = 1.10


def separations(rgb):
    """Coverage of the yellow, cyan and black plates. The film's own yellow and cyan are full coverage."""
    k = 1 - rgb.max(-1)
    d = np.maximum(1 - k, 1e-3)
    cy = np.clip((1 - rgb[..., 0] - k) / d, 0, 1)
    ye = np.clip((1 - rgb[..., 2] - k) / d / 0.63, 0, 1) * 0.92
    return ye.astype(np.float32), cy.astype(np.float32), k.astype(np.float32)


PLATES = (("y", E.RIN, 0.0), ("c", E.CYAN, 15.0), ("k", E.INK, 45.0))


def line_art(rgb):
    """What in a picture is ink: its lines and its black masses. In print these stay solid; only the tones go to dots."""
    return np.clip((0.24 - rgb.max(-1)) / 0.08, 0, 1).astype(np.float32)


def without_lines(rgb, ink, sig=6.0):
    """The tones the lines were drawn over: fine lines would otherwise blur into grey smudges on the black plate."""
    w = 1 - ink
    num = cv2.GaussianBlur(rgb * w[..., None], (0, 0), sig)
    den = cv2.GaussianBlur(w, (0, 0), sig)
    return lighter(rgb * w[..., None] + np.clip(num / np.maximum(den, 1e-3)[..., None], 0, 1) * ink[..., None])


def lighter(rgb):
    """Greys print a step lighter than they are, so that the lines stand clear of the dots."""
    v = rgb.max(-1, keepdims=True)
    return rgb * (1 - (1 - v) ** 1.6) / np.maximum(v, 1e-3)


def line_break(z):
    """How far the solid lines have gone over to dots at this zoom: 0 is whole lines, 1 is nothing but the three plates."""
    return E.seg(math.log(z), math.log(3.0), math.log(7.0))


def dot_paint(color, multiply):
    p = skia.Paint(AntiAlias=True, Color4f=E.col(color))
    if multiply:
        p.setBlendMode(skia.BlendMode.kMultiply)
    return p


def dots(c, plate, down, cell, ang, rect, boost=1.0, color=E.INK, multiply=False, floor=0.05):
    """One screen of round dots inside rect (x0, y0, x1, y1), in the units of the plate. Dots live on a fixed lattice."""
    x0, y0, x1, y1 = rect
    a = math.radians(ang)
    co, si = math.cos(a), math.sin(a)
    # lattice index ranges that cover the rect after rotation
    us = [(x * co + y * si) / cell for x in (x0, x1) for y in (y0, y1)]
    vs = [(-x * si + y * co) / cell for x in (x0, x1) for y in (y0, y1)]
    ii, jj = np.meshgrid(np.arange(int(min(us)) - 2, int(max(us)) + 3), np.arange(int(min(vs)) - 2, int(max(vs)) + 3))
    xs = cell * (ii * co - jj * si)
    ys = cell * (ii * si + jj * co)
    m = (xs > x0 - cell) & (xs < x1 + cell) & (ys > y0 - cell) & (ys < y1 + cell)
    xs, ys = xs[m], ys[m]
    h, w = plate.shape
    px = np.clip((xs / down).astype(int), 0, w - 1)
    py = np.clip((ys / down).astype(int), 0, h - 1)
    cov = plate[py, px]
    keep = cov > floor
    xs, ys, cov = xs[keep], ys[keep], cov[keep]
    rs = cell * 0.72 * np.sqrt(cov) * boost
    path = skia.Path()
    for x, y, r in zip(xs.tolist(), ys.tolist(), rs.tolist()):
        path.addCircle(x, y, r)
    c.drawPath(path, dot_paint(color, multiply))


def place(rgb, fig, s, x, y, ax, ay):
    """Composite a figure into rgb with raw point (ax, ay) landing on (x, y). Returns the figure's ink mask too."""
    h, w = rgb.shape[:2]
    src = fig
    f = 1.0
    if s < 0.7:
        f = s
        src = cv2.resize(fig, None, fx=s, fy=s, interpolation=cv2.INTER_AREA)
    k = s / f
    mat = np.array([[k, 0, x - s * ax], [0, k, y - s * ay]], np.float32)
    pm = src.copy()
    pm[..., :3] *= pm[..., 3:4]
    out = cv2.warpAffine(pm, mat, (w, h), flags=cv2.INTER_LINEAR if k > 1 else cv2.INTER_AREA,
                         borderMode=cv2.BORDER_CONSTANT, borderValue=(0, 0, 0, 0))
    a = out[..., 3:4]
    res = rgb * (1 - a) + out[..., :3]
    un = out[..., :3] / np.maximum(a, 1e-3)
    ink = a[..., 0] * np.clip((0.24 - un.max(-1)) / 0.08, 0, 1)
    size = max(5, int(11 * s)) | 1
    closed = cv2.morphologyEx((ink > 0.5).astype(np.uint8), cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (size, size)))
    white = closed.astype(np.float32) * a[..., 0] * np.clip((un.min(-1) - 0.45) / 0.3, 0, 1)
    return res, ink, white


def line_plate(ink, white, grow=1):
    """Her lines and the bar's handwriting, solid. Edges are re-sharpened so the plate stays clean when enlarged."""
    h, w = ink.shape
    if grow != 1:
        ink = cv2.resize(ink, (w * grow, h * grow), interpolation=cv2.INTER_CUBIC)
        white = cv2.resize(white, (w * grow, h * grow), interpolation=cv2.INTER_CUBIC)
    ink = np.clip((ink - 0.5) * 2.5 + 0.5, 0, 1)
    white = np.clip((white - 0.5) * 2.5 + 0.5, 0, 1)
    rgba = np.zeros((*ink.shape, 4), np.uint8)
    rgba[..., :3] = np.array([10, 10, 15], np.uint8)
    rgba[white > 0.02, :3] = np.array([246, 243, 234], np.uint8)
    rgba[..., 3] = (np.maximum(ink, white) * 255).astype(np.uint8)
    return E.np_to_image(rgba)


def surface_rgb(w, h, draw):
    s = skia.Surface(w, h)
    c = s.getCanvas()
    c.clear(E.col(E.PAPER))
    draw(c)
    arr = s.makeImageSnapshot().toarray(colorType=skia.ColorType.kRGBA_8888_ColorType, alphaType=skia.AlphaType.kOpaque_AlphaType)
    return arr[..., :3].astype(np.float32) / 255


def poly(c, pts, color):
    p = skia.Path()
    p.moveTo(*pts[0])
    for q in pts[1:]:
        p.lineTo(*q)
    p.close()
    c.drawPath(p, skia.Paint(AntiAlias=True, Color4f=E.col(color)))


# ---------------------------------------------------------------- what is behind her in each photo
def gate_still():
    """The gate with no flash going off: the first frames of the shot are lit by flashes, the photo and the dots are not."""
    return K.seq_frame("gate", T_END + 24 / 60, T_END)[..., ::-1].astype(np.float32) / 255


def gate_photo(frame, tone=False):
    """Behind her: the real gate, the very frame the film goes to, shrunk into the photo. The rest of the print carries it on."""
    fh, fw = int(round(E.H * GATE_M)), int(round(E.W * GATE_M))
    small = cv2.resize(frame, (fw, fh), interpolation=cv2.INTER_AREA)
    x0, y0 = int(round(TARGET[0] - fw / 2)), int(round(TARGET[1] - fh / 2))
    # the road comes on towards us below the frame, with the long shadows of the gate on it
    rgb = surface_rgb(PW, PH, scene_road)
    if tone:
        rgb = lighter(rgb)
    rgb[:y0] = frame[2, 2]
    # the tower has a roof: the frame only just cuts it off
    rgb[y0 - 10:y0, x0 + int(725 * GATE_M):x0 + int(1295 * GATE_M)] = (0.30, 0.31, 0.34)
    rgb[y0:y0 + fh, x0:x0 + fw] = small
    # and the school goes on to the right of it: the same bays again
    span = fw - 328
    x = x0 + fw
    while x < PW:
        n = min(328, PW - x)
        rgb[y0:y0 + fh, x:x + n] = small[:, span:span + n]
        x += n
    return rgb


def gate_lines(ink, grow=2):
    """The gate's solid ink, laid out in the photo like gate_photo lays out the picture. The gear is cut by the frame's lower edge: there the
    line art breaks up into the photo's own black dots, and to the right, where the bays repeat, only the building carries on."""
    fh, fw = int(round(E.H * GATE_M)) * grow, int(round(E.W * GATE_M)) * grow
    small = cv2.resize(ink, (fw, fh), interpolation=cv2.INTER_CUBIC)
    x0, y0 = int(round(TARGET[0] * grow - fw / 2)), int(round(TARGET[1] * grow - fh / 2))
    out = np.zeros((PH * grow, PW * grow), np.float32)
    out[y0:y0 + fh, x0:x0 + fw] = small
    span = fw - 328 * grow
    high = int(fh * 0.46)                # the top of the wall: everything above is building
    x = x0 + fw
    while x < PW * grow:
        n = min(328 * grow, PW * grow - x)
        out[y0:y0 + high, x:x + n] = small[:high, span:span + n]
        x += n
    # hard dots, not a fade
    yy, xx = np.mgrid[:PH * grow, :PW * grow].astype(np.float32)
    a = math.radians(45.0)
    pitch = CELL * grow
    u = (xx * math.cos(a) + yy * math.sin(a)) / pitch
    v = (-xx * math.sin(a) + yy * math.cos(a)) / pitch
    screen = 0.5 + 0.25 * (np.cos(2 * np.pi * u) + np.cos(2 * np.pi * v))
    ramp = np.clip((yy - (y0 + fh - 74 * grow)) / (70.0 * grow), 0, 1)
    return out * np.clip((screen - ramp) * pitch / 1.6 + 0.5, 0, 1)


def scene_road(c, w=PW, h=PH):
    E.rect(c, 0, 0, w, h, "#DADBD5")
    poly(c, [(150, 840), (520, 840), (1040, 1400), (500, 1400)], "#B4B7B6")
    poly(c, [(-10, 1560), (w + 10, 1450), (w + 10, 1500), (-10, 1620)], "#F6F3EA")


def scene_street(c, w, h):
    E.rect(c, 0, 0, w, h, E.CYAN)
    poly(c, [(w * 0.46, h * 0.34), (w * 0.72, h * 0.15), (w * 1.05, h * 0.34)], "#4A5568")
    E.rect(c, w * 0.52, h * 0.33, w * 0.5, h * 0.2, "#DDDFD8")
    E.rect(c, w * 0.6, h * 0.37, w * 0.12, h * 0.1, "#4F6E8E")
    # concrete block wall
    wy = h * 0.46
    E.rect(c, 0, wy, w, h - wy, "#CFD1CB")
    E.rect(c, 0, wy - h * 0.02, w, h * 0.024, "#8C9095")
    bh = h * 0.075
    for j in range(9):
        y = wy + j * bh
        E.rect(c, 0, y, w, 4, "#A4A7A3")
        for i in range(8):
            E.rect(c, (i + (j % 2) * 0.5) * w * 0.22, y, 4, bh, "#A4A7A3")
    # a utility pole, and wires
    E.rect(c, w * 0.80, 0, w * 0.045, h * 0.5, "#3C4047")
    E.rect(c, w * 0.72, h * 0.09, w * 0.2, h * 0.012, "#3C4047")
    for y0, y1 in ((0.06, 0.02), (0.10, 0.06), (0.14, 0.11)):
        poly(c, [(0, h * y0), (w, h * y1), (w, h * y1 + 4), (0, h * y0 + 4)], "#1E2127")


def scene_flash(c, w, h):
    """Night. A flash on a wall right behind her: everything beyond it is black."""
    E.rect(c, 0, 0, w, h, "#10131B")
    E.rect(c, 0, h * 0.1, w, h, "#7C8798")
    E.rect(c, 0, h * 0.1, w, h * 0.02, "#2B3038")
    for x in np.arange(0.17, 1.0, 0.34):
        E.rect(c, w * x, h * 0.1, 5, h, "#5F6978")


def scene_sky(c, w, h):
    E.rect(c, 0, 0, w, h, E.CYAN)
    E.rect(c, 0, h * 0.72, w, h, "#CFD1CB")
    E.rect(c, 0, h * 0.70, w, h * 0.024, "#8C9095")
    for i in range(1, 9):
        E.rect(c, i * w * 0.12, h * 0.72, 12, h * 0.3, "#8C9095")
    E.rect(c, 0, h * 0.60, w, 10, "#3C4047")


# ---------------------------------------------------------------- magazine covers
CW, CH = 700, 960
SS = 1.5
COVERS = [
    # hit beat, landing x, y, rotation: left, right, then on top of both, then left and right again
    dict(beat=23, x=500, y=548, rot=-4.2, fall=0.44,
         mast="週刊東都", mast_font=M, mast_bg=E.INK, mast_fg=E.PAPER,
         art=("t01", scene_street, 1.02, 455, 118, 490, 20),
         big="成績は学年一位", big_x=112, big_y=148, big_box=(150, 760), big_col=E.PAPER, big_key=E.INK,
         kick="少女A 十四歳の素顔", kick_x=232, kick_y=150,
         sub=("元担任が涙の証言", "「あんな良い子はいない」")),
    dict(beat=25, x=1420, y=532, rot=3.6, fall=0.3,
         mast="週刊スクープ", mast_font=GB, mast_bg=E.RIN, mast_fg=E.INK,
         art=("t03", scene_flash, 0.84, 255, 118, 660, 20),
         big="札付きの不良", big_x=590, big_y=150, big_box=(160, 760), big_col=E.RIN, big_key=E.INK,
         kick="夜の街で目撃多数", kick_x=474, kick_y=600,
         sub=("カメラを手で遮った！", "同級生「みんな怖がってた」")),
    dict(beat=27, x=960, y=560, rot=-1.4, fall=0.3,
         mast="女性ジャーナル", mast_font=M, mast_bg=E.PAPER, mast_fg=E.INK,
         art=("t02", scene_street, 0.92, 455, 118, 480, 190),
         big="友達は一人もいない", big_x=112, big_y=146, big_box=(150, 790), big_col=E.PAPER, big_key=E.INK,
         kick="いつも独りで下校", kick_x=232, kick_y=148,
         sub=("近所の主婦が語る", "「挨拶もしない子で…」")),
    dict(beat=29, x=430, y=520, rot=5.2, fall=0.3,
         mast="週刊真相", mast_font=GB, mast_bg=E.INK, mast_fg=E.RIN,
         art=("t01", scene_sky, 1.52, 345, 118, 505, 40),
         big="クラス一の人気者", big_x=606, big_y=150, big_box=(150, 780), big_col=E.RIN, big_key=E.INK,
         kick="友人三十人が語る", kick_x=90, kick_y=470,
         sub=("誕生日には行列が", "「みんなあの子が好き」")),
    dict(beat=30, x=1400, y=556, rot=-3.4, fall=0.26,
         mast="サンデー東都", mast_font=M, mast_bg=E.INK, mast_fg=E.PAPER,
         art=("t03", scene_sky, 1.06, 300, 96, 620, 20),
         big="報道は全部ウソ", big_x=598, big_y=150, big_box=(170, 780), big_col=E.PAPER, big_key=E.INK,
         kick="少女A騒動の真実", kick_x=66, kick_y=150,
         sub=("専門家が徹底検証", "本誌だけが知っている")),
]
for d_ in COVERS:
    d_["hit"] = BT(d_["beat"])

# ---------------------------------------------------------------- the five phones
# which phone each cover drops into: the nearest in landing order. Each is the top post of its feed until the feed first moves.
COL_OF = {3: 0, 0: 1, 2: 2, 4: 3, 1: 4}
HANDLE_OF = {0: "@shukan_toto", 1: "@shukan_scoop", 2: "@josei_journal", 3: "@shukan_shinso", 4: "@sunday_toto"}
POST_Y = 6                      # the post's top below the phone's header
PHONE_W = 340
GAP = (E.W - 5 * PHONE_W) / 6
PHONE_TOP = 34
HEADER = 92
INNER = PHONE_W - 2 * 14
BAR_Y = 522.0
PHONE_X = [GAP + i * (PHONE_W + GAP) for i in range(5)]

# each column: beats on which it jumps, and how many posts each jump travels. Even columns run up, odd ones run down.
JUMPS = [
    ((32, 33, 35, 37, 39), (2, 1, 3, 1, 2)),
    ((32.5, 34, 35, 38, 39), (1, 3, 1, 2, 1)),
    ((32, 33, 35, 36, 39), (3, 1, 1, 2, 2)),
    ((32.5, 33.5, 35.5, 37, 39), (1, 2, 2, 1, 2)),
    ((32, 34, 35, 37.5, 39), (2, 1, 1, 3, 1)),
]
NAMES = ["通りすがり", "ねこ太郎", "匿名希望", "A組の人", "元同級生", "まとめ速報", "おもち", "にわか", "kei", "地元民", "ゆう", "トレンド班"]
HANDLES = ["@torisugari", "@neko_taro", "@anon_0312", "@a_gumi", "@moto_dokyu", "@matome_sokuho", "@omochi22", "@niwaka_", "@kei_kei", "@jimoto_min", "@yuu_14", "@trend_han"]
SAY = ["この子でしょ", "同じ塾だった", "本当はいい子だよ", "校門の前で撮られてる", "拡散希望", "え、普通に子供じゃん", "誰か名前知らない？", "これ別人だよ",
       "親の顔が見たい", "嘘乙", "顔隠しても分かる", "うちの近所", "また少女A", "もう飽きた", "続報まだ？", "かわいそう", "自業自得でしょ", "この写真どこで？",
       "話盛りすぎ", "知らないくせに", "去年転校してきた子", "転校なんてしてない", "ソースは？", "週刊誌で見た"]
LAST = ["本人で確定", "いや別人でしょ", "優等生だったよ", "不良だったよ", "話したこともない"]
AGO = ["1分前", "3分前", "12分前", "28分前", "1時間前"]
KINDS = ["crop", "text", "circle", "text", "quote", "coarse", "text", "crop", "text", "circle", "text", "coarse", "quote", "text", "crop"]


class Card:
    """One post in a phone. Heights are measured so that the feed can stop on any post."""

    def __init__(self, name, handle, say, ago, kind, likes, reposts):
        self.kind = kind
        self.name = E.Type(name, GD, 20)
        self.handle = E.Type(handle, GM, 16)
        self.ago = E.Type(ago, GM, 16)
        self.say = E.fit(say, GM, INNER, 40, max_size=26)
        self.stats = E.Type(f"リポスト {reposts}　　いいね {likes}", GM, 17)
        self.pic_h = {"text": 0, "crop": 190, "circle": 250, "quote": 214, "coarse": 214, "full": PH * Z0, "cover": (PHONE_W - 2 * 14) * CH / CW}[kind]
        self.seed = sum(ord(ch) for ch in name + say) % 1000
        self.head = 58
        self.text_h = 42
        self.h = self.head + self.text_h + (self.pic_h + 10 if self.pic_h else 0) + 44

    def pic_top(self):
        return self.head + self.text_h


def focus(z):
    """The photo point in the middle of the screen once the photo fills it: the frame's middle at Z_GATE, the door when far in."""
    w = E.ease_io(E.seg(math.log(max(z, 1e-3)), math.log(Z_GATE), math.log(6.0)), 2)
    return E.lerp(TARGET[0], DOOR[0], w), E.lerp(TARGET[1], DOOR[1], w)


class MediaMachine(E.Clip):
    name = "s01b"
    t0, t1 = 315 / 30, 681 / 30
    cuts = (T_FEED,)
    shutter = 0.2

    # -------------------------------------------------------- setup
    def setup(self):
        self.fig = {"t01": C.load(ROOT / "assets" / "gen" / "final" / "t01_candid_turn.png"),
                    "t03": C.load(ROOT / "assets" / "gen" / "final" / "t03_candid_hand.png")}
        self.fig["t02"] = self.load_gate_figure()
        self.make_photo()
        self.covers = [self.make_cover(d) for d in COVERS]
        rng = np.random.default_rng(23)
        for d in COVERS:
            d["nudge"] = rng.normal(0, 1, 2)
        self.make_feeds()
        self.long_bar = B.Bar(0, 0, 2500, RAW_BAR[3] * FIG_S * Z0, 0.0, 77, text=False, passes=9)
        self.pen = E.Type("この子", PEN, 26)
        # the end of her fall from the title: the first magazine comes down right behind her
        self.opening = c1.Opening()
        self.opening.setup()

    def load_gate_figure(self):
        """t02 has one eye showing in profile: it gets its bar here, hand-placed like the others (it is not in bars.json)."""
        cut = ROOT / "assets" / "gen" / "cut" / "t02_candid_gate.png"
        if cut.exists():
            im = C.load(cut)
        else:
            im = C.cutout(cv2.imread(str(ROOT / "assets" / "gen" / "raw" / "t02_candid_gate.png"))).astype(np.float32)
        self.raw_bar = B.Bar(*RAW_BAR)
        return B.stamp(im, B.Bar(*RAW_BAR))

    def make_photo(self):
        """The one photo everybody passes around. Tone goes to dots; only her own ink stays solid."""
        still = gate_still()
        lines = line_art(still)
        at = (FIG_S, HEAD_PX, BAR_PY, RAW_BAR[0], RAW_BAR[1])
        rgb, ink, white = place(gate_photo(still), self.fig["t02"], *at)
        tone = place(gate_photo(without_lines(still, lines), True), self.fig["t02"], *at)[0]
        self.ink_img = line_plate(ink, white, 2)
        # the gate's own line art, solid, wherever she does not stand in front of it
        free = place(np.ones_like(rgb), self.fig["t02"], *at)[0] - place(np.zeros_like(rgb), self.fig["t02"], *at)[0]
        free = cv2.resize(free[..., 0], (PW * 2, PH * 2), interpolation=cv2.INTER_LINEAR)
        drawn = np.clip((gate_lines(lines, 2) - 0.5) * 2.5 + 0.5, 0, 1) * np.clip(free, 0, 1)
        arr = np.zeros((*drawn.shape, 4), np.uint8)
        arr[..., :3] = np.array([10, 10, 15], np.uint8)
        arr[..., 3] = (drawn * 255 + 0.5).astype(np.uint8)
        self.gate_ink = E.np_to_image(arr)
        ye, cy, k = separations(rgb)
        k_tone = separations(tone)[2]
        # tone only: her lines must not also spatter the black plate. kf is what the black plate carries once the gate's lines have gone to dots
        mask = 1 - np.clip(ink + white, 0, 1)
        k, k_tone = k * mask, k_tone * mask
        sig = CELL * 0.62
        self.plates = {}
        for n, p in (("y", ye), ("c", cy), ("k", k_tone), ("kf", k)):
            b = cv2.GaussianBlur(p, (0, 0), sig)
            self.plates[n] = cv2.resize(b, (PW // 2, PH // 2), interpolation=cv2.INTER_AREA)
        ss = 2
        s = skia.Surface(PW * ss, PH * ss)
        c = s.getCanvas()
        c.clear(E.col(E.PAPER))
        c.scale(ss, ss)
        self.paint_dots(c, (0, 0, PW, PH))
        c.save()
        c.scale(0.5, 0.5)
        c.drawImage(self.gate_ink, 0, 0, E.SAMPLING_DOWN)
        c.drawImage(self.ink_img, 0, 0, E.SAMPLING_DOWN)
        c.restore()
        self.photo_full = s.makeImageSnapshot()
        arr = self.photo_full.toarray(colorType=skia.ColorType.kRGBA_8888_ColorType, alphaType=skia.AlphaType.kOpaque_AlphaType)
        small = cv2.resize(arr, (int(PW * Z0 * 2), int(PH * Z0 * 2)), interpolation=cv2.INTER_AREA)
        self.photo_small = E.np_to_image(small)
        # a repost of a repost of a screenshot
        tiny = cv2.resize(small, (small.shape[1] // 7, small.shape[0] // 7), interpolation=cv2.INTER_AREA)
        self.photo_coarse = E.np_to_image(cv2.resize(tiny, (small.shape[1], small.shape[0]), interpolation=cv2.INTER_NEAREST))

    def paint_dots(self, c, rect, boost=1.0, broken=0.0):
        for i, (n, color, ang) in enumerate(PLATES):
            plate = self.plates[n]
            if n == "k" and broken > 0:
                plate = plate + (self.plates["kf"] - plate) * broken
            dots(c, plate, 2.0, CELL, ang, rect, boost, color, multiply=(n == "c"), floor=0.16 if n == "y" else 0.05)

    def draw_gate_ink(self, c, rect, broken):
        """The gate's lines: whole, or, going further in, seen only through dots that close up. Hard edges all the way."""
        if broken >= 1:
            return
        if broken <= 0:
            c.save()
            c.scale(0.5, 0.5)
            c.drawImage(self.gate_ink, 0, 0, E.SAMPLING)
            c.restore()
            return
        x0, y0, x1, y1 = rect
        a = math.radians(45.0)
        co, si = math.cos(a), math.sin(a)
        us = [(x * co + y * si) / CELL for x in (x0, x1) for y in (y0, y1)]
        vs = [(-x * si + y * co) / CELL for x in (x0, x1) for y in (y0, y1)]
        ii, jj = np.meshgrid(np.arange(int(min(us)) - 2, int(max(us)) + 3), np.arange(int(min(vs)) - 2, int(max(vs)) + 3))
        r = CELL * 0.75 * math.sqrt(1 - broken)
        path = skia.Path()
        for x, y in zip((CELL * (ii * co - jj * si)).ravel().tolist(), (CELL * (ii * si + jj * co)).ravel().tolist()):
            path.addCircle(x, y, r)
        m = skia.Matrix()
        m.setScale(0.5, 0.5)
        c.drawPath(path, skia.Paint(AntiAlias=True, Shader=self.gate_ink.makeShader(skia.TileMode.kClamp, skia.TileMode.kClamp, E.SAMPLING, m)))

    def make_cover(self, d):
        w, h = int(CW * SS), int(CH * SS)
        fig_name, scene, s, x, y, ax, ay = d["art"]
        rgb = surface_rgb(w, h, lambda c: scene(c, w, h))
        if fig_name == "t03" and scene is scene_flash:
            # the flash throws her shadow hard onto the wall
            sh = self.fig["t03"].copy()
            sh[..., :3] = np.array([0.06, 0.07, 0.11], np.float32)
            rgb = place(rgb, sh, s * SS * 1.03, (x + 74) * SS, (y + 34) * SS, ax, ay)[0]
        rgb, ink, white = place(rgb, self.fig[fig_name], s * SS, x * SS, y * SS, ax, ay)
        ye, cy, k = separations(rgb)
        k = k * (1 - np.clip(ink + white, 0, 1))
        cell = 5.2 * SS
        surf = skia.Surface(w, h)
        c = surf.getCanvas()
        c.clear(E.col(E.PAPER))
        for p, color, ang, mult in ((ye, E.RIN, 0.0, False), (cy, E.CYAN, 15.0, True), (k, E.INK, 45.0, False)):
            b = cv2.GaussianBlur(p, (0, 0), cell * 0.5)
            dots(c, b, 1.0, cell, ang, (0, 0, w, h), 1.0, color, multiply=mult, floor=0.16 if color == E.RIN else 0.05)
        c.drawImage(line_plate(ink, white), 0, 0)
        c.save()
        c.scale(SS, SS)
        self.cover_type(c, d)
        c.restore()
        return surf.makeImageSnapshot()

    def cover_type(self, c, d):
        # masthead: horizontal, across the top
        mh = 112
        E.rect(c, 0, 0, CW, mh, d["mast_bg"])
        mast = E.fit(d["mast"], d["mast_font"], CW - 250, mh - 26)
        # a right-bound magazine: the masthead reads from the left, the spine is on the right
        mast.draw(c, 26, mh / 2, d["mast_fg"], ax=0)
        date = E.Type("11月20日号", GD, 21)
        price = E.Type("特別定価 480円", GD, 19)
        date.draw(c, CW - 34, mh / 2 - 15, d["mast_fg"], ax=1)
        price.draw(c, CW - 34, mh / 2 + 17, d["mast_fg"], ax=1)
        # the big contradicting line, vertical
        bw, bh = d["big_box"]
        big = E.fit(d["big"], M, bw, bh, vertical=True, max_size=170)
        cx, ty = d["big_x"], d["big_y"]
        big.draw(c, cx, ty, d["big_col"], ax=0.5, ay=0, stroke=(d["big_key"], 16))
        big.draw(c, cx, ty, d["big_col"], ax=0.5, ay=0)
        # kicker: a smaller vertical line on a band
        kick = E.fit(d["kick"], GB, 44, 420, vertical=True, max_size=38)
        kx, ky = d["kick_x"], d["kick_y"]
        E.rect(c, kx - kick.w / 2 - 9, ky - 9, kick.w + 18, kick.h + 18, E.INK)
        kick.draw(c, kx, ky, E.PAPER, ax=0.5, ay=0)
        # small print in the corner
        y = CH - 76
        lines = d["sub"]
        widest = max(E.fit(t, GD, 330, 30, max_size=25).w for t in lines)
        left = CW - widest - 48 if d["big_x"] < CW / 2 else 30
        E.rect(c, left, y - 8, widest + 28, 76, E.PAPER)
        for i, tx in enumerate(lines):
            E.fit(tx, GD, 330, 30, max_size=25).draw(c, left + 14, y + 12 + i * 32, E.INK, ax=0)
        # spine
        E.rect(c, CW - 12, 0, 12, CH, E.INK, alpha=0.20)
        E.rect(c, CW - 13, 0, 2, CH, E.INK, alpha=0.45)
        E.rect(c, 0, 0, CW, 2, E.INK, alpha=0.25)

    def make_feeds(self):
        rng = np.random.default_rng(14)
        self.feeds = []
        for col, (beats, steps) in enumerate(JUMPS):
            total = sum(steps)
            n_after = 4
            cards = []
            for k in range(total * 2 + n_after + 2):
                i = (k * 5 + col * 7) % len(NAMES)
                kind = KINDS[(k * 2 + col * 3) % len(KINDS)]
                cards.append(Card(NAMES[i], HANDLES[i], SAY[(k * 3 + col * 5) % len(SAY)], AGO[int(rng.integers(0, len(AGO)))], kind,
                                  f"{rng.integers(1, 90)}.{rng.integers(0, 9)}万" if rng.random() < 0.5 else f"{rng.integers(120, 9800):,}",
                                  f"{rng.integers(120, 42000):,}"))
            # the post they all stop on
            f = total + 1
            cards[f] = Card(NAMES[(col * 3 + 2) % len(NAMES)], HANDLES[(col * 3 + 2) % len(NAMES)], LAST[col], AGO[col], "full",
                            f"{[3.2, 18, 1.1, 7.4, 2.6][col]}万", f"{[8214, 41052, 2377, 19630, 5148][col]:,}")
            tops = np.concatenate([[0], np.cumsum([q.h for q in cards])])
            # scroll value: the y in feed space shown at the top of the screen area
            final = tops[f] + cards[f].pic_top() - (BAR_Y - BAR_PY * Z0 - (PHONE_TOP + HEADER))
            direction = 1 if col % 2 == 0 else -1
            idx = f - direction * total
            stops = []
            for st in steps:
                # each intermediate stop leaves the post top a little under the header, never exactly flush
                stops.append(tops[idx] - 16 - (idx * 37) % 70)
                idx += direction * st
            stops.append(final)
            # the magazine that dropped into this phone, posted by the magazine itself
            i = next(k for k, v in COL_OF.items() if v == col)
            post = Card(COVERS[i]["mast"], HANDLE_OF[i], COVERS[i]["kick"], "たった今", "cover", f"{4 + col * 3}.{col + 2}万", f"{1280 + col * 2371:,}")
            post.cover = i
            self.feeds.append(dict(cards=cards, tops=tops, beats=[BT(b) for b in beats], stops=stops, post=post))

    # -------------------------------------------------------- timing
    def blur(self, t):
        if T_DROP <= t < T_FEED:
            return 1            # the covers drop hard-edged
        if t < T_FEED:
            for d in COVERS:
                if d["hit"] - d["fall"] - 0.02 <= t < d["hit"]:
                    return 56       # a big thing falling at the lens: a pixel or two a step, or it prints as copies
                if d["hit"] <= t < d["hit"] + 0.16:
                    return 16       # only the table shaking
            return 1
        if t < T_JOIN - 0.05:
            for fd in self.feeds:
                for b in fd["beats"]:
                    if b - 0.07 <= t < b + 0.24:
                        return 48   # a jump of two or three posts crosses most of a phone in a frame
            return 1
        if t < T_PUSH:
            return 16 if t < T_JOIN + 0.3 else 1
        return 12

    def frame_rgb(self, t):
        return K.soft_frame(self, t)

    def scroll(self, fd, t):
        y = fd["stops"][0]
        for i, b in enumerate(fd["beats"]):
            # the jump goes through its fastest point on the beat and settles softly
            u = E.seg(t, b - 0.05, b + 0.22)
            if u <= 0:
                break
            y = E.lerp(fd["stops"][i], fd["stops"][i + 1], E.ease_io(u, 1.6) * 0.25 + E.ease_out(u, 4) * 0.75)
        return y

    def zoom(self, t):
        """Absolute photo-to-screen zoom on the way to the gate: gathers on the band's accents and never stops."""
        keys = [(T_PUSH, Z0), (BT(43), 0.38), (BT(45), 1.05), (BT(46), Z_GATE), (BT(47), 2.5), (BT(47.5), 3.5), (T_END, Z_APEX)]
        for (a, za), (b, zb) in zip(keys, keys[1:]):
            if t < b:
                x = E.seg(t, a, b)
                x = x * 0.55 + E.ease_io(x, 2) * 0.45
                return math.exp(E.lerp(math.log(za), math.log(zb), x))
        return keys[-1][1]

    # -------------------------------------------------------- magazines
    def draw_table(self, c, t):
        c.clear(E.col(E.CYAN))
        if t < c1.FALL1:
            self.opening.falling(c, t)
        shake_x = shake_y = 0.0
        pop = 1.0
        for i, d in enumerate(COVERS):
            u = t - d["hit"]
            if 0 <= u < 0.22:
                decay = (1 - u / 0.22) ** 2
                amp = 15 if i < 4 else 20
                shake_x += math.sin(u * 95 + i * 2.1) * amp * decay
                shake_y += math.cos(u * 83 + i) * amp * decay
                pop += 0.012 * decay
        c.save()
        c.translate(960 + shake_x, 540 + shake_y)
        drift = 1.0 + 0.012 * max(0, t - COVERS[0]["hit"])
        c.scale(pop * drift, pop * drift)
        c.translate(-960, -540)
        for i, d in enumerate(COVERS):
            self.draw_mag(c, t, i, d)
        c.restore()

    def draw_mag(self, c, t, i, d):
        u = E.seg(t, d["hit"] - d["fall"], d["hit"])
        if u <= 0:
            return
        landed = t >= d["hit"]
        # free fall towards the table seen from above: height goes with the square of the time left
        h = 1 - u * u
        s = 1 / (1 - 0.66 * h)
        # later covers knock the ones under them
        nx = ny = rn = 0.0
        for later in COVERS[i + 1:]:
            q = E.ease_out((t - later["hit"]) / 0.10, 3) if t > later["hit"] else 0.0
            nx += later["nudge"][0] * 7 * q
            ny += later["nudge"][1] * 6 * q
            rn += later["nudge"][0] * 0.35 * q
        x = d["x"] + nx
        y = d["y"] + ny
        rot = d["rot"] + rn + (d["rot"] * 2.4) * h
        # shadow on the table: far away while it is high, right beside it when down
        sx = 11 + 1300 * h * h
        sy = 14 + 900 * h * h
        c.save()
        c.translate(x + sx, y + sy)
        c.rotate(rot)
        E.rect(c, -CW / 2, -CH / 2, CW, CH + 6, E.INK, alpha=0.30)
        c.restore()
        # the magazine itself
        c.save()
        c.translate(960 + (x - 960) * s + (x - 960) * 0.4 * h * h, 540 + (y - 540) * s - 2200 * h * h)
        c.rotate(rot)
        c.scale(s, s)
        # page block: the thickness shows along the bottom edge and the fore edge
        E.rect(c, -CW / 2 + 1, CH / 2 - 2, CW - 2, 8, "#D9D5C8")
        E.rect(c, -CW / 2 + 1, CH / 2 + 5, CW - 2, 2, E.INK, alpha=0.6)
        E.rect(c, -CW / 2 + 1, CH / 2 + 1, CW - 2, 1.4, E.INK, alpha=0.25)
        c.scale(1 / SS, 1 / SS)
        c.drawImage(self.covers[i], -CW * SS / 2, -CH * SS / 2, E.SAMPLING)
        c.restore()

    # -------------------------------------------------------- phones
    def draw_avatar(self, c, x, y, r, seed):
        col = ("#20232B", "#7C8798", "#B9BCB6", E.CYAN, "#3C4047")[seed % 5]
        c.drawCircle(x, y, r, skia.Paint(AntiAlias=True, Color4f=E.col(col)))
        n = 3 + seed % 4
        pts = [(x + math.cos(i * 6.283 / n - 1.57) * r * 0.5, y + math.sin(i * 6.283 / n - 1.57) * r * 0.5) for i in range(n)]
        poly(c, pts, E.PAPER)

    def draw_window(self, c, x, y, w, h, img, px, py, zoom=1.0):
        """Show the photo in a window, filling it, around photo point (px, py). Returns the photo-to-screen mapping."""
        sc = max(w / PW, h / PH) * zoom
        vw, vh = w / sc, h / sc
        ox = min(max(px - vw / 2, 0), PW - vw)
        oy = min(max(py - vh / 2, 0), PH - vh)
        c.save()
        c.clipRect(skia.Rect.MakeXYWH(x, y, w, h))
        c.translate(x, y)
        c.scale(sc, sc)
        c.translate(-ox, -oy)
        q = PW / img.width()
        c.scale(q, q)
        c.drawImage(img, 0, 0, E.SAMPLING_DOWN if sc * q < 1 else E.SAMPLING)
        c.restore()
        return sc, ox, oy

    def draw_card(self, c, card, x, y, col, z, focus):
        """Card at phone-screen x, feed-space y already resolved to screen. z only matters for the last post in the centre."""
        pad = 14
        self.draw_avatar(c, x + pad + 19, y + 29, 19, card.seed)
        card.name.draw(c, x + pad + 46, y + 19, E.INK, ax=0)
        card.handle.draw(c, x + pad + 46, y + 41, GREY, ax=0)
        card.ago.draw(c, x + PHONE_W - pad, y + 19, GREY, ax=1)
        card.say.draw(c, x + pad, y + card.head + 15, E.INK, ax=0)
        top = y + card.pic_top()
        if card.kind == "cover":
            if self._t >= T_FEED:
                c.save()
                c.translate(x + pad, top)
                s_ = INNER / (CW * SS)
                c.scale(s_, s_)
                c.drawImage(self.covers[card.cover], 0, 0, E.SAMPLING_DOWN)
                c.restore()
        elif card.kind == "full":
            self.draw_final_photo(c, x + pad, top, z, focus)
        elif card.kind == "crop":
            # a crop around her head
            self.draw_window(c, x + pad, top, INNER, card.pic_h, self.photo_small, 900, 900, 1.35)
        elif card.kind == "circle":
            sc, ox, oy = self.draw_window(c, x + pad, top, INNER, card.pic_h, self.photo_small, 860, 880, 1.12)
            # somebody's red circle round her head
            self.red_ring(c, x + pad + (HEAD_PX - ox) * sc, top + (BAR_PY - 60 - oy) * sc, 92, 86, card.seed)
            self.pen.draw(c, x + pad + 12, top + card.pic_h - 26, E.RED, ax=0)
        elif card.kind == "quote":
            # a quoted post: the photo, smaller, inside somebody else's frame
            E.rect(c, x + pad, top, INNER, card.pic_h, RULE, radius=12)
            E.rect(c, x + pad + 2, top + 2, INNER - 4, card.pic_h - 4, E.PAPER, radius=11)
            self.draw_avatar(c, x + pad + 22, top + 20, 10, card.seed + 2)
            card.handle.draw(c, x + pad + 38, top + 20, GREY, ax=0)
            self.draw_window(c, x + pad + 10, top + 38, INNER - 20, card.pic_h - 48, self.photo_small, 768, 820, 1.0)
        elif card.kind == "coarse":
            # a repost of a repost: the same photo, gone to blocks
            self.draw_window(c, x + pad, top, INNER, card.pic_h, self.photo_coarse, 768, 700, 1.0)
        y2 = top + (card.pic_h + 10 if card.pic_h else 0)
        card.stats.draw(c, x + pad, y2 + 15, GREY, ax=0)
        E.rect(c, x, y + card.h - 1.5, PHONE_W, 1.5, RULE)

    def red_ring(self, c, cx, cy, rx, ry, seed):
        pts = []
        for i in range(30):
            a = -2.2 + i / 29 * 7.0
            k = 1 + 0.03 * math.sin(i * 0.9 + seed) + i * 0.002
            pts.append((cx + math.cos(a) * rx * k, cy + math.sin(a) * ry * k))
        p = skia.Path()
        p.moveTo(*pts[0])
        for q in pts[1:]:
            p.lineTo(*q)
        c.drawPath(p, skia.Paint(AntiAlias=True, Color4f=E.col(E.RED), Style=skia.Paint.kStroke_Style, StrokeWidth=5,
                                 StrokeCap=skia.Paint.kRound_Cap, StrokeJoin=skia.Paint.kRound_Join))

    def draw_final_photo(self, c, x, y, z, focus):
        c.save()
        c.clipRect(skia.Rect.MakeXYWH(x, y, PW * Z0, PH * Z0))
        c.translate(x, y)
        c.scale(Z0, Z0)
        if not focus or z < 0.42:
            q = PW / self.photo_small.width()
            c.scale(q, q)
            c.drawImage(self.photo_small, 0, 0, E.SAMPLING_DOWN)
        elif z < 1.5:
            c.scale(0.5, 0.5)
            c.drawImage(self.photo_full, 0, 0, E.SAMPLING_DOWN)
        else:
            # close enough that every dot is drawn for real, on the same lattice
            m = c.getTotalMatrix()
            inv = skia.Matrix()
            m.invert(inv)
            a, b = inv.mapXY(0, 0), inv.mapXY(E.W, E.H)
            E.rect(c, 0, 0, PW, PH, E.PAPER)
            boost = 1.0 + (BOOST_APEX - 1) * E.ease_in(E.seg(self._t, T_END - 0.5, T_END), 2)
            broken = line_break(z)
            self.paint_dots(c, (a.x(), a.y(), b.x(), b.y()), boost, broken)
            self.draw_gate_ink(c, (a.x(), a.y(), b.x(), b.y()), broken)
            if b.x() > 780:
                c.save()
                c.scale(0.5, 0.5)
                c.drawImage(self.ink_img, 0, 0, E.SAMPLING)
                c.restore()
        c.restore()

    def draw_phone(self, c, t, col, z=Z0, focus=False):
        fd = self.feeds[col]
        x = PHONE_X[col]
        # body runs off the bottom of the frame
        body = skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(x - 8, PHONE_TOP - 8, PHONE_W + 16, 1400), 44, 44)
        c.drawRRect(body, skia.Paint(AntiAlias=True, Color4f=E.col(E.INK)))
        scr = skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(x, PHONE_TOP, PHONE_W, 1400), 36, 36)
        c.drawRRect(scr, skia.Paint(AntiAlias=True, Color4f=E.col(E.PAPER)))
        c.save()
        c.clipRect(skia.Rect.MakeXYWH(x, PHONE_TOP + HEADER, PHONE_W, 1400))
        sc = self.scroll(fd, t)
        for card, top in zip(fd["cards"], fd["tops"]):
            y = PHONE_TOP + HEADER + top - sc
            if y > 1140 or y + card.h < PHONE_TOP:
                continue
            self.draw_card(c, card, x, y, col, z, focus)
        # the magazine's own post stays on top until the feed has carried it off
        post = fd["post"]
        y = PHONE_TOP + HEADER + POST_Y + fd["stops"][0] - sc
        if y < 1140 and y + post.h > PHONE_TOP:
            E.rect(c, x, y - POST_Y, PHONE_W, post.h + POST_Y, E.PAPER)
            self.draw_card(c, post, x, y, col, z, False)
        c.restore()
        # header stays where it is
        c.save()
        c.clipRRect(scr, True)
        E.rect(c, x, PHONE_TOP, PHONE_W, HEADER, E.PAPER)
        self.status[col].draw(c, x + 30, PHONE_TOP + 16, E.INK, ax=0)
        E.rect(c, x + 14, PHONE_TOP + 34, PHONE_W - 28, 44, "#E4E1D6", radius=22)
        self.search.draw(c, x + 34, PHONE_TOP + 56, E.INK, ax=0)
        # the notification count keeps climbing with the beat
        n = 40 + col * 17 + max(0, int((t - T_FEED) / (BT(1) - BT(0)))) * (3 + col)
        ty = E.Type(str(min(n, 999)), GB, 19)
        w = max(ty.w + 18, 30)
        E.rect(c, x + PHONE_W - 28 - w, PHONE_TOP + 41, w, 30, E.RED, radius=15)
        ty.draw(c, x + PHONE_W - 28 - w / 2, PHONE_TOP + 56, E.PAPER)
        E.rect(c, x, PHONE_TOP + HEADER - 1.5, PHONE_W, 1.5, RULE)
        c.restore()

    def draw_bars(self, c, t):
        """The five bars, and once they have run out, the one bar."""
        cx = [PHONE_X[i] + 14 + HEAD_PX * Z0 for i in range(5)]
        half0 = RAW_BAR[2] * FIG_S * Z0 * 0.42
        u = E.ease_io(E.seg(t, T_JOIN - 0.04, T_JOIN + 0.26), 1.6)
        if u > 0:
            th = RAW_BAR[3] * FIG_S * Z0
            reach = 320
            clip = skia.Path()
            for x in cx:
                half = half0 + reach * u
                clip.addRRect(skia.RRect.MakeRectXY(skia.Rect.MakeLTRB(x - half, BAR_Y - th, x + half, BAR_Y + th), th * 0.5, th * 0.5))
            c.save()
            c.clipPath(clip, True)
            c.translate(960, BAR_Y)
            self.long_bar.draw(c)
            c.restore()
        # the handwriting of each stays on the line
        for x in cx:
            c.save()
            c.translate(x, BAR_Y)
            c.scale(FIG_S * Z0, FIG_S * Z0)
            c.translate(-RAW_BAR[0], -RAW_BAR[1])
            self.raw_bar.draw(c)
            c.restore()

    def cover_landing(self, i):
        """The middle of the cover, in the phone, and its scale."""
        col = COL_OF[i]
        post = self.feeds[col]["post"]
        return PHONE_X[col] + PHONE_W / 2, PHONE_TOP + HEADER + POST_Y + post.pic_top() + post.pic_h / 2, INNER / CW

    def table_pose(self, t, i):
        """Where cover i lies on the table on the screen: the same shake, drift and knocks as draw_table and draw_mag."""
        shake_x = shake_y = 0.0
        pop = 1.0
        for k, d in enumerate(COVERS):
            u = t - d["hit"]
            if 0 <= u < 0.22:
                decay = (1 - u / 0.22) ** 2
                amp = 15 if k < 4 else 20
                shake_x += math.sin(u * 95 + k * 2.1) * amp * decay
                shake_y += math.cos(u * 83 + k) * amp * decay
                pop += 0.012 * decay
        drift = pop * (1.0 + 0.012 * max(0, t - COVERS[0]["hit"]))
        d = COVERS[i]
        nx = ny = rn = 0.0
        for later in COVERS[i + 1:]:
            q = E.ease_out((t - later["hit"]) / 0.10, 3) if t > later["hit"] else 0.0
            nx += later["nudge"][0] * 7 * q
            ny += later["nudge"][1] * 6 * q
            rn += later["nudge"][0] * 0.35 * q
        return 960 + shake_x + (d["x"] + nx - 960) * drift, 540 + shake_y + (d["y"] + ny - 540) * drift, d["rot"] + rn, drift

    def draw_drop(self, c, t):
        """The table goes: phones come up from below it, each cover drops into its phone's first post. All hard edges, nothing fades. The covers stay on top."""
        self.feed_ready()
        self._t = t
        c.clear(E.col(E.CYAN))
        for col in range(5):
            u = E.ease_out(E.seg(t, T_DROP + 0.02 * abs(col - 2), T_FEED - 0.03), 2.6)
            c.save()
            c.translate(0, (1 - u) * 1100)
            self.draw_phone(c, t, col)
            c.restore()
        for i, d in enumerate(COVERS):
            # the far ones lift first; they all land together, on the accent
            start = T_DROP + 0.02 * (4 - abs(COL_OF[i] - 2) * 2) / 4
            u = E.seg(t, start, T_FEED) ** 1.8
            x0, y0, r0, s0 = self.table_pose(t, i)
            x1, y1, s1 = self.cover_landing(i)
            s = math.exp(E.lerp(math.log(s0), math.log(s1), u))
            w = (s - s0) / (s1 - s0)
            x, y, r = x0 + (x1 - x0) * w, y0 + (y1 - y0) * w, r0 * (1 - u)
            c.save()
            c.translate(x + (11 * s) * (1 - u), y + (14 * s) * (1 - u))
            c.rotate(r)
            E.rect(c, -CW * s / 2, -CH * s / 2, CW * s, (CH + 6) * s, E.INK, alpha=0.30)
            c.restore()
            c.save()
            c.translate(x, y)
            c.rotate(r)
            c.scale(s, s)
            # the page block goes as it lands: on the screen it is a picture
            E.rect(c, -CW / 2 + 1, CH / 2 - 2, CW - 2, 8 * (1 - u), "#D9D5C8")
            c.scale(1 / SS, 1 / SS)
            c.drawImage(self.covers[i], -CW * SS / 2, -CH * SS / 2, E.SAMPLING_DOWN if s < 0.9 else E.SAMPLING)
            c.restore()

    def feed_ready(self):
        if not hasattr(self, "status"):
            self.status = [E.Type(s, GD, 16) for s in ("15:08", "15:08", "15:08", "15:08", "15:08")]
            self.search = E.Type("少女A", GD, 22)

    def draw_feed(self, c, t):
        self._t = t
        self.feed_ready()
        c.clear(E.col(E.CYAN))
        # phone-space position of the gate door in the centre phone
        tx = PHONE_X[2] + 14 + TARGET[0] * Z0
        ty = BAR_Y + (TARGET[1] - BAR_PY) * Z0
        if t >= T_PUSH:
            z = self.zoom(t)
            k = z / Z0
            move = E.ease_io(E.seg(math.log(z), math.log(Z0), math.log(Z_GATE)), 1.7)
            sx, sy = E.lerp(tx, 960, move), E.lerp(ty, 540, move)
            # past the gate frame the aim settles on the door
            fx, fy = focus(z)
            sx -= (fx - TARGET[0]) * z
            sy -= (fy - TARGET[1]) * z
        else:
            z, k, sx, sy = Z0, 1.0, tx, ty
        c.save()
        # the landing goes through the phones
        c.translate(sx, sy + 13 * (1 - E.seg(t, T_FEED, T_FEED + T_HIT)) ** 2 if t < T_FEED + T_HIT else sy)
        c.scale(k, k)
        c.translate(-tx, -ty)
        for col in range(5):
            if k > 1:
                left = sx + (PHONE_X[col] - 8 - tx) * k
                right = sx + (PHONE_X[col] + PHONE_W + 8 - tx) * k
                if right < 0 or left > E.W:
                    continue
            self.draw_phone(c, t, col, z, focus=(col == 2))
        if t >= T_JOIN - 0.02 and sy + (BAR_Y - ty - 40) * k < E.H:
            self.draw_bars(c, t)
        c.restore()

    def draw(self, c, t):
        if t < T_DROP:
            self.draw_table(c, t)
        elif t < T_FEED:
            self.draw_drop(c, t)
        else:
            self.draw_feed(c, t)
