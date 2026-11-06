"""Section 06: the trending list. She climbs only on the six long notes of "nan-ban-me" twice; every climb
takes rows away and makes the type bigger, until rank 1 is the whole screen and the sung line ends in a big "？"."""
import sys
from pathlib import Path

import skia

sys.path.insert(0, str(Path(__file__).parent))
import common as K  # noqa: E402
import engine as E  # noqa: E402
from bar import Bar  # noqa: E402

F0, F1 = 2880, 3116
LINE = 26
NOTES = [s["t"] for s in K.LYRICS[LINE]["syl"] if s["text"].strip() in ("nan", "ban", "me")]
TOP = K.LYRICS[27]["start"]       # line 27: rank 1
SILENCE = 103.04                  # the band drops out here: the "？" lands in the hole
HIT = 103.46                      # the band comes back with a hit

RANKS = [26, 20, 14, 9, 5, 3, 2, 1]
TIMES = [F0 / 30 - 1.0] + NOTES + [TOP]
HER = ["98.4万件", "108万件", "172万件", "318万件", "566万件", "783万件", "891万件"]
ROLL = ["1,024万件", "1,031万件", "1,039万件", "1,052万件", "1,066万件", "1,083万件", "1,097万件", "1,118万件", "1,136万件", "1,159万件", "1,204万件"]
ROLL_T = [s["t"] for s in K.LYRICS[27]["syl"]]

# (topic, category, count): ordinary life, none of it about her
OTHERS = [
    ("新作スマホ発表", "テクノロジー", "982万件"), ("台風12号", "天気", "874万件"), ("今夜の映画", "エンタメ", "761万件"),
    ("推しの誕生日", "エンタメ", "652万件"), ("ねこの日", "生活", "548万件"), ("期末テスト", "学校", "471万件"),
    ("値上げラッシュ", "ニュース", "402万件"), ("電車遅延", "交通", "351万件"), ("#今日の空", "生活", "306万件"),
    ("結婚発表", "エンタメ", "268万件"), ("新作ゲーム", "ゲーム", "239万件"), ("コンビニ新商品", "グルメ", "214万件"),
    ("#月曜日つらい", "生活", "188万件"), ("ラーメン特集", "グルメ", "167万件"), ("大雨警報", "天気", "151万件"),
    ("花粉", "生活", "136万件"), ("優勝おめでとう", "スポーツ", "124万件"), ("給食の思い出", "生活", "112万件"),
    ("文化祭", "学校", "106万件"), ("ドラマ最終回", "エンタメ", "104万件"), ("夏休み", "生活", "103万件"),
    ("#猫のいる暮らし", "生活", "102万件"), ("朝ごはん", "グルメ", "101万件"), ("手作りケーキ", "グルメ", "99.9万件"),
    ("渋滞情報", "交通", "99.1万件"),
]
# rank 1: everybody suddenly has something to say. One post slapped on the empty page per sung syllable; in the hole in the
# band they are all gone and only the question is left. (text, centre x, centre y, turn, type size)
POSTS = [("誰？", 1560, 118, -5, 96), ("少女Aって誰", 800, 96, 3, 60), ("本人？", 1716, 400, 6, 84), ("特定した", 330, 800, -3, 66),
         ("写真ある", 196, 92, -4, 54), ("同級生です", 1520, 760, -3, 60), ("まとめ", 850, 830, 4, 74), ("知ってる", 1250, 120, 2, 58),
         ("拡散希望", 1720, 590, -6, 56), ("顔みせて", 560, 712, 5, 46)]
BADGE = ["1", "3", "12", "48", "130", "406", "877", "999+", "999+", "999+"]
LIST_BOTTOM = 984                 # below this is the lyric track
GOTHIC = "ZenKakuGothicNew-Black"
BAR_LEN = 400
BASE = 200.0


class Ranking(E.Clip):
    name = "s06"
    t0, t1 = F0 / 30, F1 / 30
    shutter = 0.12
    cuts = tuple(NOTES) + (TOP, SILENCE, HIT) + tuple(ROLL_T[1:])

    def setup(self):
        self.title = [E.Type(o[0], GOTHIC, BASE) for o in OTHERS]
        self.cat = [E.Type(o[1], "ZenKakuGothicNew-Bold", BASE) for o in OTHERS]
        self.cnt = [E.Type(o[2], "ZenKakuGothicNew-Bold", BASE) for o in OTHERS]
        self.num = {i: E.Type(str(i), "ShipporiMinchoB1-ExtraBold", BASE) for i in range(1, 30)}
        self.her_cnt = [E.Type(s, "ZenKakuGothicNew-Bold", BASE) for s in HER]
        self.roll = [E.Type(s, "ZenKakuGothicNew-Bold", BASE) for s in ROLL]
        self.up = {n: E.Type(f"▲{n}", "ZenKakuGothicNew-Black", BASE) for n in (6, 5, 4, 2, 1)}
        self.head = E.Type("トレンド　総合", GOTHIC, BASE)
        self.head2 = E.Type("いま話題のワード", "ZenKakuGothicNew-Bold", BASE)
        self.her_cat = E.Type("話題", "ZenKakuGothicNew-Bold", BASE)
        # the same marker bar and hand as everywhere in the film: unit thickness, scaled to the row
        self.bar = Bar(0, 0, BAR_LEN, 100, 0, seed=26)
        self.q = E.fit("？", "ShipporiMinchoB1-ExtraBold", 470, 760, max_size=1200)
        self.q_full = E.fit("？", "ShipporiMinchoB1-ExtraBold", 1500, 860, max_size=1600)
        self.posts = [(E.Type(tx, "ZenKakuGothicNew-Black", sz), x, y, rot) for tx, x, y, rot, sz in POSTS]
        self.badge = {b: E.Type(b, "ZenKakuGothicNew-Black", 40) for b in BADGE}
        self.lyric26 = K.Strip("何番目でも何番目でも", K.chars_of(26, "何番目でも何番目でも"), size=46)
        # the same size as this line's return in the eye-opening, so the two rhyme
        self.lyric27 = K.Strip("僕が僕であるために", K.chars_of(27, "僕が僕であるために"), size=76, pad=20)

    def blur(self, t):
        for n in TIMES[1:]:
            if n - 0.01 <= t <= n + 0.20:
                return 32
        if SILENCE - 0.01 <= t <= SILENCE + 0.08:
            return 4
        return 1

    def frame_rgb(self, t):
        return K.soft_frame(self, t)

    def state(self, t):
        """Which climb we are on, and how far through its short move."""
        i = 0
        for k, tk in enumerate(TIMES):
            if t >= tk:
                i = k
        u = E.ease_out(E.seg(t, TIMES[i], TIMES[i] + 0.20), 4)
        return i, u

    def row(self, c, y, h, rank, other=None, show_cat=True):
        """A row of the table, laid out for its height: nothing is scaled blind, everything has to fit the width."""
        m = max(40.0, h * 0.14)
        rs = h * 0.70
        digits = self.num[rank]
        # the rank column is as wide as the widest number still on the screen
        rw = self.rank_w * rs / BASE
        digits.draw(c, m + rw, y + h / 2, E.INK, ax=1, scale=rs / BASE)
        x = m + rw + max(26.0, h * 0.26)
        if other is None:
            return x, m
        cnt = self.cnt[other]
        cs = min(h * 0.46, 76.0)
        cnt.draw(c, E.W - m, y + h / 2, E.INK, ax=1, scale=cs / BASE)
        cw = cnt.w * cs / BASE
        tt = self.title[other]
        avail = E.W - m - cw - x - 60
        if show_cat:
            avail = min(avail, 1040 - x)
            cat = self.cat[other]
            cat.draw(c, 1120, y + h / 2, E.INK, ax=0, scale=h * 0.42 / BASE)
        ts = min(h * 0.66, avail / tt.w * BASE)
        tt.draw(c, x, y + h / 2, E.INK, ax=0, scale=ts / BASE)

    def her_row(self, c, y, h, i, rank, u, top_u):
        """Her row: yellow, and instead of a typed name the marker bar with the handwriting."""
        E.rect(c, 0, y, E.W, h, E.RIN)
        x, m = self.row(c, y, h, rank)
        cnt = self.her_cnt[min(i, len(self.her_cnt) - 1)]
        cs = min(h * 0.46, 76.0)
        if rank != 1:    # on the way to the full page the bar is as long as the row: the page brings its own count
            cnt.draw(c, E.W - m, y + h / 2, E.INK, ax=1, scale=cs / BASE)
        th = min(h * 0.80, 240.0)
        scale = th / 100.0
        c.save()
        # the scrawl reaches about half its length either side of its centre
        c.translate(x + BAR_LEN * 0.52 * scale, y + h / 2)
        c.scale(scale, scale)
        self.bar.draw(c)
        c.restore()
        # the jump she just made
        if 1 <= i < len(RANKS) - 1:
            n = RANKS[i - 1] - RANKS[i]
            ty = self.up[n]
            us = min(h * 0.44, 72.0)
            ty.draw(c, E.W - m - cnt.w * cs / BASE - 34, y + h / 2, E.INK, ax=1, scale=us / BASE)
        if show_cat_for(h):
            self.her_cat.draw(c, 1120, y + h / 2, E.INK, ax=0, scale=h * 0.42 / BASE)

    def draw_top(self, c, t):
        """Rank 1: the row is the screen."""
        c.clear(E.col(E.RIN))
        n = 0
        for k, tk in enumerate(ROLL_T):
            if t >= tk:
                n = k
        if t >= HIT:
            # the band comes back and there is nothing left but the question
            self.q_full.draw(c, 960, 455, E.INK)
            return
        # one slow push over the whole held page, never quite still; the question arrives inside it
        s_ = 1.0 + 0.045 * E.seg(t, TOP, HIT)
        c.save()
        c.translate(960, 450)
        c.scale(s_, s_)
        c.translate(-960, -450)
        self.num[1].draw(c, 70, 430, E.INK, ax=0, scale=640 / BASE)
        scale = 2.3
        c.save()
        c.translate(860, 390)
        c.scale(scale, scale)
        self.bar.draw(c)
        c.restore()
        self.roll[n].draw(c, 1320, 630, E.INK, ax=1, scale=92 / BASE)
        if t < SILENCE:
            self.draw_posts(c, t)
        if t >= SILENCE:
            u = E.ease_out(E.seg(t, SILENCE, SILENCE + 0.08), 3)
            self.q.draw(c, 1620, 430, E.INK, scale=1 + 0.14 * (1 - u))
        c.restore()

    def draw_posts(self, c, t):
        """Each lands in two frames, flat and hard, with a hard shadow to the lower left like every shadow in the film."""
        shown = 0
        for k, (ty, x, y, rot) in enumerate(self.posts):
            st = ROLL_T[k + 1]
            if t < st:
                break
            shown = k + 1
            land = E.seg(t, st, st + 2 / 30)
            sc = 1.28 - 0.28 * land
            w, h = ty.w + ty.h * 1.0, ty.h * 1.72
            c.save()
            c.translate(x, y)
            c.rotate(rot)
            c.scale(sc, sc)
            E.rect(c, -w / 2 - 9, -h / 2 + 10, w, h, "#C9A71F", radius=h * 0.26)
            E.rect(c, -w / 2, -h / 2, w, h, E.INK, radius=h * 0.26)
            ty.draw(c, 0, 0, E.PAPER)
            c.restore()
        if shown:
            b = self.badge[BADGE[shown - 1]]
            w = max(76.0, b.w + 34)
            E.rect(c, 1872 - w, 18, w, 76, E.RED, radius=38)
            b.draw(c, 1872 - w / 2, 56, E.PAPER)

    def draw(self, c, t):
        i, u = self.state(t)
        if i == len(RANKS) - 1:
            # the last climb: her row swallows the first row and the lyric band
            if u < 1:
                self.draw_list(c, t, i, u)
            else:
                self.draw_top(c, t)
        else:
            self.draw_list(c, t, i, u)
        if t < TOP:
            self.lyric26.draw(c, 960, 1034, t, ax=0.5)
        else:
            self.lyric27.draw(c, 960, 985, t, ax=0.5)

    def draw_list(self, c, t, i, u):
        c.clear(E.col(E.CYAN))
        n0 = RANKS[max(i - 1, 0)]
        n1 = RANKS[i]
        self.rank_w = E.lerp(self.num[n0].w, self.num[n1].w, u)
        top_u = 0.0
        bottom = LIST_BOTTOM
        # header shrinks away by the time five rows are left
        # the list starts clear of the header: the first row has its own margin under it, and the rows share what is left
        hdr0, hdr1 = header_h(n0), header_h(n1)
        hdr = E.lerp(hdr0, hdr1, u)
        h0, h1 = (LIST_BOTTOM - list_top(hdr0)) / n0, (LIST_BOTTOM - list_top(hdr1)) / max(n1, 1)
        if n1 == 1:
            # the row grows over everything, the band included
            top = E.lerp(LIST_BOTTOM - h0, 0.0, u)
            bot = E.lerp(LIST_BOTTOM, E.H, u)
            h = bot - top
            h_others = h0 * (1 + 0.8 * u)
            self.rows_above(c, n0, n0 - 1, h_others, hdr)
            E.rect(c, 0, LIST_BOTTOM, E.W, E.H - LIST_BOTTOM, E.INK)
            self.her_row(c, top, h, i, RANKS[i], u, 0)
            return
        # multiply so the zoom keeps a constant rate through the move
        h = h0 * (h1 / h0) ** u
        rows = n0 - 1
        self.rows_above(c, rows, n1 - 1, h, hdr)
        E.rect(c, 0, bottom, E.W, E.H - bottom, E.INK)
        rank = n1
        self.her_row(c, bottom - h, h, i, rank, u, top_u)

    def rows_above(self, c, rows, keep, h, hdr):
        cat = show_cat_for(h)
        ln = skia.Paint(AntiAlias=True, Color4f=E.col(E.INK), StrokeWidth=max(2.0, h * 0.022))
        for k in range(rows):
            y = list_top(hdr) + k * h
            if y > LIST_BOTTOM:
                break
            self.row(c, y, h, k + 1, other=k, show_cat=cat)
            c.drawLine(0, y + h, E.W, y + h, ln)
        if hdr > 1:
            E.rect(c, 0, 0, E.W, hdr, E.INK)
            hs = hdr * 0.52
            self.head.draw(c, 40, hdr / 2, E.CYAN, ax=0, scale=hs / BASE)
            self.head2.draw(c, E.W - 40, hdr / 2, E.PAPER, ax=1, scale=hs * 0.8 / BASE)


def show_cat_for(h):
    return h < 125


def header_h(n):
    return {26: 54.0, 20: 58.0, 14: 58.0, 9: 50.0}.get(n, 0.0)


def list_top(hdr):
    """Where the first row starts: below the header by a margin. When the header has gone there is no margin either."""
    return hdr * 1.32
