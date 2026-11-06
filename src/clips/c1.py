"""Clip 1: the label arrives before the person. Then the band enters and everybody starts talking."""
import json
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
import cutout as C  # noqa: E402

ROOT = K.ROOT
HIT = 7.40
BEAT = 0.46155
L2 = HIT + 2 * BEAT
TITLE = 9.567
END = 10.49
# the talk: the first comment lands on the news on one beat, by the next they are pouring in and the camera sets off for the bar,
# and on the third the camera is there. They cover the black completely, then rush past the lens.
TALK0, PUSH0, COVERED = 8.59, 9.05, 9.34
# the wall stands for a moment, then the camera goes through it: the outer comments pass the lens first, the last ones go after it has landed
FLY0, FLY1 = 9.38, 9.86
# she falls out of the frame and the first magazine comes down right behind her. The fall carries on into s01b, which draws its end.
DROP0, FALL1 = 10.26, 10.86
FALL_PAD = 1420
S0 = 0.78
TITLE_K = 3
BX, BY = 543.0, 700.0
# the label starts as big as the frame and is written there; then we back away from it and it is small on an empty field, and only
# then does anything grow out of it. K_BIG is how much larger than the figure's own bar it is while it is being written
K_BIG = 2.55
PULL0, PULL1 = 2.98, 3.86

PILLS = [(4.62, 142, 300, "誰？"), (5.10, 1600, 214, "見たことある"), (5.48, 214, 820, "あの子？"), (5.75, 1640, 700, "名前は？"),
         (6.02, 96, 540, "学校どこ"), (6.25, 1690, 460, "ニュース見た"), (6.47, 310, 128, "え、同じ中学"), (6.64, 1490, 900, "嘘でしょ"),
         (6.80, 120, 960, "写真ある？"), (6.93, 1700, 90, "特定した"), (7.04, 330, 650, "拡散希望"), (7.12, 1560, 540, "マジで？")]
SIDE_TEXT = ("関係者によると少女Aは普通の子だったという。別の関係者はそうではないと語る。少女Aについて分かっていることは少ない。"
             "同級生の話はそれぞれ違う。少女Aの本当の姿はどこにあるのか。")
FLOOD = ["少女Aって誰", "同じクラスだった", "本当はいい子らしい", "いや最悪だったよ", "目立ちたいだけ", "かわいそう", "自業自得でしょ",
         "顔見たい", "ソースは？", "全部嘘", "全部本当", "知らないくせに", "親の顔が見たい", "話したことある", "ない", "少女A", "少女A", "少女A",
         "もう飽きた", "続報まだ", "なんで少女A", "Aって何", "私の友達が", "昔から変だった", "優しかったよ", "怖い", "応援してる", "本人見てる？"]


def trace_skeleton(mask):
    """Split an ink mask into pen paths: skeleton, cut at junctions, then re-joined across each junction where the line carries straight on."""
    from scipy import ndimage as ndi
    from skimage.morphology import skeletonize
    sk = skeletonize(mask)
    nb = ndi.convolve(sk.astype(np.uint8), np.ones((3, 3), np.uint8), mode="constant") - 1
    H, W = sk.shape
    nodes = sk & (nb != 2)
    lab, _ = ndi.label(nodes, np.ones((3, 3)))     # a junction is usually a little clump of pixels

    def around(y, x):
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                if (dy or dx) and 0 <= y + dy < H and 0 <= x + dx < W and sk[y + dy, x + dx]:
                    yield y + dy, x + dx

    seen = np.zeros_like(sk)
    segs = []
    for y, x in zip(*np.nonzero(nodes)):
        for q in around(y, x):
            if nodes[q] or seen[q]:
                continue
            path = [(y, x), q]
            seen[q] = True
            while not nodes[path[-1]]:
                nx = [r for r in around(*path[-1]) if not seen[r] and r != path[-2]]
                hit = [r for r in nx if nodes[r]]
                free = [r for r in nx if not nodes[r]]
                if hit:
                    path.append(hit[0])
                    break
                if not free:
                    break
                path.append(free[0])
                seen[free[0]] = True
            segs.append(path)
    # plain loops have no node at all
    for y, x in zip(*np.nonzero(sk & ~nodes & ~seen)):
        if seen[y, x]:
            continue
        path = [(y, x)]
        seen[y, x] = True
        while True:
            free = [r for r in around(*path[-1]) if not seen[r]]
            if not free:
                break
            path.append(free[0])
            seen[free[0]] = True
        segs.append(path)
    # at every junction, pair the ends that continue each other
    ends = {}
    for i, p in enumerate(segs):
        for side, q in ((0, p[0]), (1, p[-1])):
            if nodes[q]:
                ends.setdefault(lab[q], []).append((i, side))

    def heading(i, side):
        p = np.array(segs[i], float)
        a, b = (p[0], p[min(14, len(p) - 1)]) if side == 0 else (p[-1], p[max(-15, -len(p))])
        d = b - a
        return d / max(np.hypot(*d), 1e-6)     # pointing away from the junction, along the line

    link = {}
    for items in ends.values():
        pairs = []
        for u in range(len(items)):
            for v in range(u + 1, len(items)):
                if items[u][0] != items[v][0]:
                    pairs.append((float(np.dot(heading(*items[u]), heading(*items[v]))), items[u], items[v]))
        used = set()
        for dot, a, b in sorted(pairs, key=lambda q: q[0]):
            if dot < -0.72 and a not in used and b not in used:
                used |= {a, b}
                link[a], link[b] = b, a
    # walk the links into whole strokes
    done = set()
    out = []
    for i in range(len(segs)):
        if i in done or len(segs[i]) < 2:
            continue
        # go back to the free end of this chain
        cur, side = i, 0
        guard = set()
        while (cur, side) in link and cur not in guard:
            guard.add(cur)
            cur, oth = link[(cur, side)]
            side = 1 - oth
        pts = []
        while True:
            done.add(cur)
            pts += segs[cur] if side == 0 else segs[cur][::-1]
            nxt = link.get((cur, 1 - side))
            if nxt is None or nxt[0] in done:
                break
            cur, side = nxt
        out.append(np.array(pts, np.float32)[:, ::-1])     # x, y
    return out


# Which part of her a stroke belongs to, and when that part is drawn. Each part starts on a sixteenth the band plays.
PARTS = (("face", 3.86, 4.21), ("hair", 4.21, 4.78), ("fringe", 4.78, 5.82), ("bow", 5.82, 6.28), ("scarf", 6.28, 6.56), ("uniform", 6.56, 7.34))


def part_of(p):
    x, y = float(p[:, 0].mean()), float(p[:, 1].mean())
    if y < 345:
        return "bow"
    if y > 1125 or (y > 1000 and (x < 300 or x > 790)):
        return "uniform"
    if y > 975 or (y > 935 and 345 < x < 760):
        return "scarf"
    if 340 < x < 745 and y > 770:
        return "face"
    ln = float(np.hypot(*np.diff(p, axis=0).T).sum())
    if ln > 240 and (x < 335 or x > 755 or y < 470):
        return "hair"
    return "fringe"


def stroke_field(ink, bar):
    """The time each ink pixel is reached, drawing her one line after another: where the pen is at each moment, with its lifts."""
    cache = ROOT / "work" / "cache" / "p01_strokes.npz"
    if cache.exists():
        return np.load(cache)["t"]
    from scipy import ndimage as ndi
    mask = ink > 0.5
    # what the bar hides is not drawn: the pen goes straight to where the line comes out again
    yy, xx = np.mgrid[:mask.shape[0], :mask.shape[1]]
    co, si = math.cos(math.radians(bar.angle)), math.sin(math.radians(bar.angle))
    u = (xx - bar.cx) * co + (yy - bar.cy) * si
    v = -(xx - bar.cx) * si + (yy - bar.cy) * co
    hidden = (np.abs(u) < bar.length * 0.47) & (np.abs(v) < bar.thick * 0.44)
    strokes = [p for p in trace_skeleton(mask & ~hidden) if len(p) >= 9]
    by = {n: [] for n, _, _ in PARTS}
    for p in strokes:
        by[part_of(p)].append(p)
    field = np.full(mask.shape, np.inf, np.float32)
    pen = np.array([543.0, 880.0])
    for n, ta, tb in PARTS:
        group = by[n]
        # the long lines first, then what hangs off them, each time going on to the nearest
        order = []
        for pool in ([p for p in group if len(p) > 170], [p for p in group if len(p) <= 170]):
            while pool:
                def reach(p):
                    # a hand draws down and to the right, unless the other end is much nearer
                    top = p if (p[0, 1], p[0, 0]) <= (p[-1, 1], p[-1, 0]) else p[::-1]
                    return min(np.hypot(*(top[0] - pen)), np.hypot(*(top[-1] - pen)) + 160)
                p = pool.pop(min(range(len(pool)), key=lambda k: reach(pool[k])))
                top = p if (p[0, 1], p[0, 0]) <= (p[-1, 1], p[-1, 0]) else p[::-1]
                if np.hypot(*(top[-1] - pen)) + 160 < np.hypot(*(top[0] - pen)):
                    top = top[::-1]
                order.append(top)
                pen = top[-1]
        # share of the time: long lines get more, but not in proportion, and every lift costs a little
        cost = [len(p) ** 0.8 + 9.0 for p in order]
        total = sum(cost) or 1.0
        clock = ta
        for p, k in zip(order, cost):
            dur = (tb - ta) * k / total
            lift = dur * min(0.5, 9.0 / k)
            d = np.concatenate([[0], np.cumsum(np.hypot(*np.diff(p, axis=0).T))])
            w = d / max(d[-1], 1.0)
            # lands quickly, settles at the end of the line
            w = 0.55 * w + 0.45 * (1 - (1 - w) ** 2)
            field[p[:, 1].astype(int), p[:, 0].astype(int)] = clock + (dur - lift) * w
            clock += dur
    # every ink pixel takes the time of the nearest point of the line it lies on
    idx = ndi.distance_transform_edt(~np.isfinite(field), return_distances=False, return_indices=True)
    out = field[idx[0], idx[1]]
    cache.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(cache, t=out)
    return out


class Opening(E.Clip):
    name = "c1"
    t0, t1 = 0.0, END
    grain = 0.010
    cuts = (HIT, L2)     # both on the band, with her staying exactly where she is
    shutter = 0.3

    def setup(self):
        import cel
        import crisp
        self.cut = cel.add_cel(C.load(ROOT / "assets" / "gen" / "cut" / "p01_bust_front.png"), drop=20, hair_inset=18)
        spec = json.loads((ROOT / "assets" / "gen" / "bars.json").read_text(encoding="utf-8"))["p01_bust_front"]
        self.bar = B.Bar(*spec)
        lum = self.cut[..., :3].mean(-1)
        # only true ink: the scarf and the collar are colours, not lines
        self.ink_alpha = self.cut[..., 3] * np.clip((0.17 - lum) / 0.09, 0, 1)
        # the title pushes in about 2.7 times: a crisp enlargement with no sharpening, so no line gets a white ring
        big = crisp.upscale(self.cut, TITLE_K)
        # the enlargement leaves pure magenta specks where a hair tip's ink meets the transparent edge: they are ink
        rgb = big[..., :3].astype(np.int16)
        big[(rgb[..., 0] > rgb[..., 1] + 30) & (rgb[..., 2] > rgb[..., 1] + 30), :3] = (10, 10, 15)
        self.full2 = E.np_to_image(big)
        self.drawn_at = stroke_field(self.ink_alpha, self.bar)
        self.full = E.np_to_image(self.cut)
        self.y0 = 30 - 60 * S0
        self.pills = [(t, x, y, E.Type(s, "ZenKakuGothicNew-Bold", 30)) for t, x, y, s in PILLS]
        self.make_layouts()
        self._fall = None

    def make_layouts(self):
        M = "ShipporiMinchoB1-ExtraBold"
        G = "ZenKakuGothicNew-Black"
        self.w_good = E.fit("優等生", M, 420, 960, vertical=True, max_size=340)
        self.w_bad = E.fit("不良", M, 420, 960, vertical=True, max_size=420)
        self.w_a1 = E.Type("少女A", G, 86)
        self.w_angel = E.fit("天使か", G, 540, 360, max_size=230)
        self.w_devil = E.fit("悪魔か", G, 540, 360, max_size=230)
        self.w_breaking = E.Type("速報", G, 54)
        self.w_name = E.Type("少女A（14）", G, 46)
        self.w_ticker = E.Type("少女Aの素顔に迫る　◆　同級生が語る本当の姿　◆　少女A、あの日何が　◆　専門家の見解は　◆　少女Aの今　◆　", "ZenKakuGothicNew-Bold", 38)
        self.cols = []
        i = 0
        while i < len(SIDE_TEXT) and len(self.cols) < 8:
            self.cols.append(E.Type(SIDE_TEXT[i:i + 26], "ShipporiMincho-Medium", 24, vertical=True))
            i += 26
        self.credit1 = E.Type("作詞作曲　椎名もた", "ZenKakuGothicNew-Bold", 34)
        self.credit2 = E.Type("歌　鏡音リン", "ZenKakuGothicNew-Bold", 34)
        self.make_cards()

    def make_cards(self):
        """A wall of comments that leaves no gap: rows of cards, each row a different height, overlapping a little."""
        rng = np.random.default_rng(14)
        cards = []
        y = -44.0
        n = 0
        while y < 1124:
            h = float(rng.choice([66, 84, 106, 134]))
            x = -float(rng.uniform(20, 190))
            while x < 1960:
                tx = FLOOD[(n * 11) % len(FLOOD)]
                n += 1
                ty = E.Type(tx, "ZenKakuGothicNew-Bold", h * 0.60)
                w = ty.w + h * 0.56
                kind = "ink" if n % 7 == 3 else "rin" if tx == "少女A" else "paper"
                cards.append(dict(x=x + w / 2, y=y + h / 2, w=w, h=h, ty=ty, kind=kind))
                x += w - float(rng.uniform(4, 16))
            y += h - float(rng.uniform(5, 12))
        cy = self.y0 + BY * S0
        # the edges of the picture go first and it closes in towards her, so the news stays readable for a moment
        for d in cards:
            dx, dy = d["x"] - 960, d["y"] - cy
            d["order"] = -max(abs(dx) / 960, abs(dy) / 540) + float(rng.uniform(0, 0.42))
            n_ = math.hypot(dx * 0.7, dy) or 1.0
            d["dir"] = (dx * 0.7 / n_, dy / n_)
            # a comment comes in from whichever edge is nearest to where it lands
            if abs(dy) / 540 > abs(dx) / 960:
                d["from"] = (0.0, 1500.0 if dy > 0 else -1500.0)
            else:
                d["from"] = (2100.0 if dx > 0 else -2100.0, 0.0)
            d["fly"] = FLY0 + 0.16 * (1 - min(1.0, max(abs(dx) / 960, abs(dy) / 540))) + float(rng.uniform(0, 0.05))
            d["dur"] = float(rng.uniform(0.20, 0.27))
            d["front"] = d["y"] > 800
        cards.sort(key=lambda d: d["order"])
        last = COVERED - 0.15
        for i, d in enumerate(cards):
            # one at a time at first, then too many to count
            d["t"] = TALK0 + (last - TALK0) * (i / (len(cards) - 1)) ** 0.42
        self.cards = cards

    def label_zoom(self, t):
        """A very slow push while she writes, a long pull back as soon as the last stroke is down. A steady rate on a log scale."""
        big = K_BIG * (1 + 0.035 * E.seg(t, 0.0, PULL0))
        return math.exp(math.log(big) * (1 - E.ease_io(E.seg(t, PULL0, PULL1), 2.4)))

    def frame_rgb(self, t):
        return K.soft_frame(self, t)

    def blur(self, t):
        # the fast parts keep their hard edges: a short shutter, so a card or a falling bow is itself on every frame and not a smear of copies
        self.shutter = 0.3 if t < HIT else 0.2
        if PULL0 <= t < PULL1:
            return 12
        if HIT - 0.01 <= t < HIT + 0.2 or L2 - 0.01 <= t < L2 + 0.2:
            return 16
        if t >= DROP0 - 0.01:
            return 12
        if TALK0 - 0.01 <= t < FLY1:
            return 16
        return 1

    def figure_transform(self, c, s, cx=960.0, cy=None):
        cy = self.y0 + BY * S0 if cy is None else cy
        c.translate(cx, cy)
        c.scale(s, s)
        c.translate(-BX, -BY)

    def draw_lines(self, c, t, s):
        # one pen: each line is drawn from one end to the other, in order, and the pen lifts between them
        m = np.clip((t - self.drawn_at) * 240, 0, 1) * self.ink_alpha
        rgba = np.zeros((*m.shape, 4), np.float32)
        rgba[..., 0], rgba[..., 1], rgba[..., 2] = 0.04, 0.04, 0.06
        rgba[..., 3] = m
        img = E.np_to_image(rgba)
        c.save()
        self.figure_transform(c, s)
        c.drawImage(img, 0, 0, E.SAMPLING)
        c.restore()

    def draw_pills(self, c, t, blown=0.0):
        for pt, x, y, ty in self.pills:
            if t < pt:
                continue
            p = E.back_out((t - pt) / 0.13, 2.2)
            w, h = ty.w + 52, ty.h + 28
            c.save()
            # when she lands, the jolt throws everybody's questions off the page
            c.translate(x + (1 if x > 960 else -1) * blown * (900 + 0.5 * abs(x - 960)), y + (y - 540) * 0.5 * blown)
            c.scale(p, p)
            E.rect(c, -w / 2, -h / 2, w, h, E.PAPER, radius=h / 2)
            ty.draw(c, 6, 0, E.INK)
            c.drawCircle(-w / 2 + 20, 0, 7, skia.Paint(AntiAlias=True, Color4f=E.col(E.RED)))
            c.restore()

    def draw(self, c, t):
        if t < HIT:
            c.clear(E.col(E.CYAN))
            s = S0 * (1 + 0.006 * t) * self.label_zoom(t)
            if t >= 3.80:
                self.draw_lines(c, t, s)
            if t >= 4.6:
                self.draw_pills(c, t)
            c.save()
            self.figure_transform(c, s)
            self.bar.draw(c, progress=E.ease_io(E.seg(t, 0.20, 1.42), 1.5), write=E.seg(t, 1.46, 2.95))
            c.restore()
            return
        if t < L2:
            self.layout_news(c, t)
        elif t < TITLE:
            self.layout_tv(c, t)
        else:
            self.title(c, t)

    def figure(self, c, s=S0, cx=960.0, cy=None):
        c.save()
        self.figure_transform(c, s, cx, cy)
        c.drawImage(self.full, 0, 0, E.SAMPLING)
        self.bar.draw(c)
        c.restore()

    def layout_news(self, c, t):
        self.news_back(c, t)
        if t < HIT + 0.2:
            self.draw_pills(c, t, E.ease_in((t - HIT) / 0.2, 1.6))
        # she lands with the band: a jolt of scale, then settling
        pop = 1 + 0.05 * (1 - E.ease_out((t - HIT) / 0.22, 3))
        self.figure(c, S0 * pop)

    def news_back(self, c, t):
        u = t - HIT
        c.clear(E.col(E.CYAN))
        k = E.ease_out(u / 0.16, 3)
        # small columns behind everything, like a page
        for i, col in enumerate(self.cols):
            x = 60 + (len(self.cols) - 1 - i) * 34
            col.draw(c, x, 70 + (i % 3) * 18, E.INK, ax=0, ay=0, alpha=0.75)
            col.draw(c, 1860 - i * 34, 70 + ((i + 1) % 3) * 18, E.INK, ax=1, ay=0, alpha=0.75)
        drift = u * 16
        self.w_good.draw(c, E.lerp(-280, 470, k) - drift, 540, E.INK)
        self.w_bad.draw(c, E.lerp(2200, 1450, k) + drift, 540, E.INK)

    def push(self, t):
        """How far the camera has gone from the news towards the bar, 0 to 1."""
        return E.ease_io(E.seg(t, PUSH0, TITLE) ** 1.5, 2.2)

    def cam(self, c, t):
        """The camera on the bar: everything in the news picture is one flat thing it pushes into."""
        cy = self.y0 + BY * S0
        f = self.push(t)
        q = math.exp(math.log(3.45) * f)
        c.translate(960, E.lerp(cy, 500, f))
        c.scale(q, q)
        c.translate(-960, -cy)
        return q

    def draw_cards(self, c, t, q, front):
        cy = self.y0 + BY * S0
        fy = E.lerp(cy, 500, self.push(t))
        todo = []
        for d in self.cards:
            if t < d["t"] or d["front"] != front:
                continue
            v = E.ease_in(E.seg(t, d["fly"], d["fly"] + d["dur"]), 2.0)
            if v < 1:
                todo.append((v, d))
        # the nearer a card has come, the more it covers
        todo.sort(key=lambda a: a[0])
        for v, d in todo:
            u = E.ease_out((t - d["t"]) / 0.15, 2.2)
            # where the card lies on the picture, in the camera's frame; then it comes on past the lens, outward from where the camera is going
            z = 1 / (1 - 0.90 * v)
            x = 960 + (d["x"] + d["from"][0] * (1 - u) - 960) * q * z + d["dir"][0] * v * v * 2600
            y = fy + (d["y"] + d["from"][1] * (1 - u) - cy) * q * z + d["dir"][1] * v * v * 2600
            k = q * (1 + 1.2 * v)
            w, h = d["w"] * k, d["h"] * k
            if x + w / 2 < -40 or x - w / 2 > E.W + 40 or y + h / 2 < -40 or y - h / 2 > E.H + 40:
                continue
            fill, text, edge = {"paper": (E.PAPER, E.INK, E.INK), "ink": (E.INK, E.PAPER, E.PAPER), "rin": (E.RIN, E.INK, E.INK)}[d["kind"]]
            line = 2.5 * k
            E.rect(c, x - w / 2, y - h / 2, w, h, edge)
            E.rect(c, x - w / 2 + line, y - h / 2 + line, w - 2 * line, h - 2 * line, fill)
            d["ty"].draw(c, x, y, text, scale=k)

    def layout_tv(self, c, t):
        u = t - L2
        covered = t >= COVERED
        if u < 0.16:
            # the black closes in from both sides behind her, carrying the new captions with it, over the old page
            self.news_back(c, t)
            k = E.ease_out(u / 0.14, 3)
            E.rect(c, -20, -20, E.lerp(-10, 1000, k) + 20, 1120, E.INK)
            x = E.lerp(1990, 920, k)
            E.rect(c, x, -20, 1940 - x, 1120, E.INK)
        else:
            # once the wall leaves no gap there is nothing black left: it is cyan that shows as the comments go past
            c.clear(E.col(E.CYAN if covered else E.INK))
        k = E.ease_out(u / 0.14, 3)
        drift = u * 16
        x1, x2 = E.lerp(-320, 330, k) - drift, E.lerp(2240, 1590, k) + drift
        c.save()
        q = self.cam(c, t)
        if not covered:
            for w, x in ((self.w_angel, x1), (self.w_devil, x2)):
                # a Japanese TV caption: fill, a black keyline, and a white outer keyline
                w.draw(c, x, 470, E.RIN, stroke=(E.PAPER, 34))
                w.draw(c, x, 470, E.RIN, stroke=(E.INK, 18))
                w.draw(c, x, 470, E.RIN)
        c.restore()
        self.draw_cards(c, t, q, False)
        c.save()
        self.cam(c, t)
        pop = 1 + 0.03 * (1 - E.ease_out(u / 0.2, 3))
        if q > 1.3:
            cy = self.y0 + BY * S0
            c.save()
            self.figure_transform(c, S0 * pop, 960.0, cy)
            c.save()
            c.scale(1 / TITLE_K, 1 / TITLE_K)
            c.drawImage(self.full2, 0, 0, E.SAMPLING)
            c.restore()
            self.bar.draw(c)
            c.restore()
        else:
            self.figure(c, S0 * pop)
        if not covered:
            # lower third, sharp as broadcast graphics
            h = 150 * E.ease_out(u / 0.12, 3)
            E.rect(c, 0, 1080 - h - 70, 1920, h, E.PAPER)
            E.rect(c, 0, 1080 - h - 70, 280, h, E.RED)
            c.save()
            c.clipRect(skia.Rect.MakeXYWH(0, 1080 - h - 70, 1920, h))
            self.w_breaking.draw(c, 140, 1080 - 70 - 75, E.PAPER)
            self.w_name.draw(c, 320, 1080 - 70 - 75, E.INK, ax=0)
            c.restore()
            E.rect(c, 0, 1010, 1920, 70, E.INK)
            off = (u * 620) % (self.w_ticker.w + 40)
            self.w_ticker.draw(c, 1920 - off, 1045, E.PAPER, ax=0)
            self.w_ticker.draw(c, 1920 - off - self.w_ticker.w - 40, 1045, E.PAPER, ax=0)
        c.restore()
        self.draw_cards(c, t, q, True)

    def title_figure(self, c, t):
        s = S0 * 3.45 * (1 + 0.012 * (t - TITLE))
        c.save()
        c.translate(960, 500)
        c.scale(s, s)
        c.translate(-BX, -BY)
        c.save()
        c.scale(1 / TITLE_K, 1 / TITLE_K)
        c.drawImage(self.full2, 0, 0, E.SAMPLING)
        c.restore()
        self.bar.draw(c)
        c.restore()

    def falling(self, c, t):
        """She falls out of the picture, with the credits on her. Everything that will ever come into view is already on one sheet."""
        if self._fall is None:
            surf = skia.Surface(E.W, E.H + FALL_PAD)
            sc = surf.getCanvas()
            sc.clear(skia.Color4f(0, 0, 0, 0))
            sc.translate(0, FALL_PAD)
            self.title_figure(sc, DROP0)
            self._fall = surf.makeImageSnapshot()
        drop = 2520 * E.ease_in(E.seg(t, DROP0, FALL1), 2.2)
        c.drawImage(self._fall, 0, drop - FALL_PAD, skia.SamplingOptions(skia.FilterMode.kLinear))
        self.credits(c, t, drop)

    def credits(self, c, t, drop):
        k = E.ease_out((t - TITLE - 0.12) / 0.14, 3)
        if k > 0:
            for ty, y, x in ((self.credit1, 930 + drop, 1860), (self.credit2, 990 + drop, 1860)):
                w = ty.w + 36
                E.rect(c, x - w * k, y - 26, w, 52, E.PAPER)
                c.save()
                c.clipRect(skia.Rect.MakeXYWH(x - w * k, y - 26, w, 52))
                ty.draw(c, x - 18, y, E.INK, ax=1)
                c.restore()

    def title(self, c, t):
        # the camera has arrived: the handwriting on the bar IS the title. The last comments are still going past
        c.clear(E.col(E.CYAN))
        if t < FLY1:
            self.draw_cards(c, t, 3.45, False)
        if t >= DROP0:
            self.falling(c, t)
            return
        self.title_figure(c, t)
        if t < FLY1:
            self.draw_cards(c, t, 3.45, True)
        self.credits(c, t, 0.0)
