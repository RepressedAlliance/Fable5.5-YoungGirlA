"""Clip 5: the trending list, all the way down to its last row; the nearly empty thread behind it; then the hate fills
the screen, and every account turns out to be hers. The phone is in her own hands."""
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
import cutout as C  # noqa: E402
from bar import Bar  # noqa: E402

ROOT = K.ROOT
T0, T1 = 4435 / 30, 164.3     # T1 is where the last move ends; the clip's last frame (see t1 below) is already black
DEMO_T0 = 154.2                # the part from here on is the approved demo and is not touched
HITS = K.syllable_times(43, "ni") + K.syllable_times(44, "ni") + K.syllable_times(45, "ni")
KUI = K.syllable_times(43, "kui") + K.syllable_times(44, "kui") + K.syllable_times(45, "kui")
HITS, KUI = HITS[:14], KUI[:14]
FLIP = 160.20
PULL = 161.60
PULLED = 162.38
SEND = 162.42
FRONT = 162.70
FRONT_K = 3
# the empty thread, before the approved part: hard cuts on the sung beats. The reply count, then her reply field, where a
# word starts and is taken back. The same hesitation as the drafts in section 02.
CUT_ZERO = 151.43
CUT_FIELD = 152.35
DRAFT = ((152.81, "あ"), (153.27, "あの"), (153.73, "あ"), (153.96, ""))
UI_W, UI_H = 2090, 1080
SAFE = 85
BG = "#171B26"
CARD = "#272C3A"
GREY = "#8C93A1"
TXT = "#E8E9EC"
HANDLE = "@shoujo_a"
# the list: four hard cuts down it, each on a sung note; each lands further down and the list gets darker. Every frame can
# be read: inside a run the list only drifts, the distance is all in the cuts
LIST_RUNS = [  # start, end, top rank at start, top rank at end
    (T0, 148.67, 0.35, 6.0),       # the first row starts clear of the header, with a margin above it, and is still clear at 148.1
    (148.67, 149.13, 118.0, 120.4),
    (149.13, 149.59, 462.0, 464.4),
    (149.59, 150.25, 835.4, 839.2),
]
TAP = 150.51                   # the last sound of the first phrase: the last row is pressed
PUSH0, PUSH1 = TAP + 0.10, TAP + 0.30     # the thread slides in over the list
LIST_TOP = 60
ROW_H = 78
LAST_RANK = K.TREND_LAST
RANKED = 100                   # the list only prints a rank down to here; below it everything, her too, is just 圏外
GOTHIC = "ZenKakuGothicNew-Black"
# (band's first rank, row colour, text colour, rule colour): hard steps, no gradient
BANDS = [(1, E.CYAN, E.INK, "#0A0A0F"), (100, "#0795C4", E.INK, "#0A0A0F"), (400, "#10506F", "#D4E4EC", "#06222F"), (700, BG, "#AEB4C0", "#2C313E")]
# the top of the list two months after section 06: the same kind of list in the middle of January, with the new girl on top of
# it. Nothing on it is left from November. (topic, category, posts)
TODAY = "1月12日"              # the date at the foot of the chart she has just stopped on
TOPICS = [
    ("少女B", "話題", 14800000), ("成人の日", "生活", 11200000), ("共通テスト", "学校", 9360000), ("大雪警報", "天気", 8120000), ("冬ドラマ初回", "エンタメ", 7030000),
    ("箱根駅伝の録画", "スポーツ", 6550000), ("福袋の中身", "生活", 5280000), ("#今日の雪", "生活", 4670000), ("路線運休", "交通", 3910000), ("お雑煮の味", "グルメ", 3440000),
    ("インフルエンザ", "生活", 2960000), ("新年会", "生活", 2510000), ("推しの新曲", "エンタメ", 2190000), ("冬休み明け", "学校", 1970000), ("鍋の素", "グルメ", 1760000),
    ("大相撲初場所", "スポーツ", 1580000), ("年賀状の返事", "生活", 1410000), ("ダウンの洗い方", "生活", 1290000), ("七草がゆ", "グルメ", 1180000), ("初売りセール", "生活", 1110000),
    ("雪かき", "生活", 1080000), ("#手袋かたほう", "生活", 1050000), ("こたつ猫", "生活", 1030000), ("みかん箱", "グルメ", 1010000), ("加湿器", "生活", 998000),
    ("凍結注意", "交通", 991000),
]
# far down the list: small things, none of which has been on it before, and no two alike on a screen or from cut to cut
DEEP = [
    ("近所のパン屋", "グルメ"), ("傘の忘れ物", "生活"), ("公園の桜", "生活"), ("駅前の工事", "地域"), ("靴ひもの結び方", "生活"),
    ("昨日の夕焼け", "生活"), ("自販機の新作", "グルメ"), ("図書館の休館日", "地域"), ("カップ麺の待ち時間", "グルメ"), ("朝の体操", "生活"),
    ("迷子の手袋", "地域"), ("消しゴムの角", "生活"), ("バスの時刻表", "交通"), ("雨上がりの匂い", "生活"), ("町内会のお知らせ", "地域"),
    ("冷蔵庫の中身", "生活"), ("ベランダの鳩", "生活"), ("お弁当の卵焼き", "グルメ"), ("押し入れの整理", "生活"), ("商店街の福引き", "地域"),
    ("洗濯物の乾き方", "生活"), ("回覧板", "地域"), ("踏切の音", "地域"), ("鉛筆の削り方", "生活"), ("電池の買い置き", "生活"),
    ("坂道の猫", "地域"), ("ポストの場所", "地域"), ("水筒の洗い方", "生活"), ("夕飯の献立", "グルメ"), ("靴下の片方", "生活"),
    ("信号の待ち時間", "交通"), ("ゴミの日", "地域"), ("窓の結露", "生活"), ("そろばん教室", "地域"), ("古い切手", "生活"),
    ("お茶の淹れ方", "グルメ"), ("畳の掃除", "生活"), ("駐輪場の空き", "地域"), ("みかんの剥き方", "グルメ"), ("金魚の餌", "生活"),
    ("庭の草むしり", "生活"), ("銭湯の営業日", "地域"), ("年賀はがき", "生活"), ("マスクの紐", "生活"), ("雑巾の絞り方", "生活"),
    ("ボタン付け", "生活"), ("小鳥の声", "生活"), ("豆腐屋のラッパ", "地域"), ("公民館の掲示板", "地域"), ("爪切りの置き場所", "生活"), ("朝の霜", "生活"),
    ("ねじの巻き方", "生活"), ("牛乳パックの開け方", "生活"), ("床屋の回転灯", "地域"),
]
# each of the three deep screens has its own rows: nothing on one can turn up on the next with another number beside it
DEEP_RUNS = ((118, 0), (462, 19), (835, 38))


def row_topic(rank):
    if rank <= len(TOPICS):
        return TOPICS[rank - 1][:2]
    for r0, off in DEEP_RUNS:
        if r0 <= rank < r0 + 19:
            return DEEP[(off + rank - r0) % len(DEEP)]
    return DEEP[rank % len(DEEP)]


ORDER = [3, 10, 0, 7, 12, 5, 1, 9, 13, 4, 8, 2, 11, 6]
NAMES = ["通りすがり", "名無し", "正義マン", "ねこ太郎", "元同級生", "主婦です", "真実の人", "匿名希望", "ゆう", "kei_0417", "にわか", "見てるだけ", "おとうふ", "りん好き"]
HANDLES = ["@passerby", "@nanashi88", "@justice_m", "@neko_taro", "@class3_b", "@mama_life", "@truth_only", "@anon_x", "@yuu0922", "@kei_0417", "@niwaka", "@lurk_only", "@otofu_2", "@a_fan_1"]
COMMENTS = ["目立ちたいだけでしょ", "嘘つき", "気持ち悪い", "もう黙ってて", "何様のつもり", "かまってちゃん", "全部自分のせい",
            "誰も聞いてないよ", "ずるい", "被害者ぶるな", "最初から嫌いだった", "恥ずかしくないの", "いい気味", "お前が一番嫌い"]
# fourteen distinct grey icons, none of them a person
SHAPES = [(5, 0.45), (3, 1.0), (8, 0.7), (4, 1.0), (6, 0.5), (12, 0.8), (7, 0.42), (5, 1.0), (10, 0.6), (3, 0.55), (4, 0.5), (9, 0.84), (6, 1.0), (8, 0.38)]
# 憎い: one of the loudest stretches of the song. Each sung word is a blow: the card lands white, the camera is thrown on to it, and over the three phrases
# (5, 5 and 4 words) it goes closer each time, until the sung word fills the frame. Size of the view per word.
HIT_S = (1.62, 1.62, 1.62, 1.62, 1.62, 2.02, 2.02, 2.02, 2.02, 2.02, 2.70, 3.05, 3.40, 3.80)
# the turn is seen close: one card, the last line anyone would want to read there, and the stranger's icon turns over into her
TURN_SLOT = 6                  # 全部自分のせい
TURN_S = 4.4
TURN_OUT0, TURN_OUT1 = 160.72, 161.34   # then we back away and all the others have gone the same way
HIT_HOT = 2.5 / 30             # how long a card that has just landed stays white
THROW = 0.05                   # the view starts for the next card this long before the word


def row_count(rank):
    """The number of posts: January's list at the top, falling away to 3 at the very bottom."""
    if rank <= len(TOPICS):
        return K.count_text(TOPICS[rank - 1][2])
    return K.count_text(K.trend_count(rank - 1))


def rank_type(rank):
    """Below the top hundred the list has no number to give: the very word that was on her plate takes its place."""
    if rank < RANKED:
        return E.Type(str(rank), "ShipporiMinchoB1-ExtraBold", 54)
    return E.Type("圏外", "ShipporiMinchoB1-ExtraBold", 38)


def band_of(rank):
    out = BANDS[0]
    for b in BANDS:
        if rank >= b[0]:
            out = b
    return out


def poly_path(n, inner, r):
    p = skia.Path()
    m = n * 2 if inner < 1 else n
    for i in range(m):
        a = -math.pi / 2 + i / m * math.tau
        q = r if (inner >= 1 or i % 2 == 0) else r * inner
        (p.moveTo if i == 0 else p.lineTo)(math.cos(a) * q, math.sin(a) * q)
    p.close()
    return p


class Hate(E.Clip):
    name = "c5"
    t0, t1 = T0, 4930 / 30
    grain = 0.010
    cuts = tuple(r[0] for r in LIST_RUNS[1:]) + (FRONT, CUT_ZERO, CUT_FIELD, DEMO_T0)
    shutter = 0.25

    def setup(self):
        col_w = (UI_W - 2 * SAFE - 40) / 2
        self.slots = []
        for i in range(14):
            cx = SAFE + 10 + (i % 2) * (col_w + 20)
            cy = 76 + (i // 2) * 130
            self.slots.append((cx, cy, col_w, 120))
        self.type = {}
        for i in range(14):
            self.type[i] = (E.Type(NAMES[i], "ZenKakuGothicNew-Bold", 28), E.Type(HANDLES[i], "ZenKakuGothicNew-Regular", 21),
                            E.fit(COMMENTS[i], "ZenKakuGothicNew-Medium", col_w - 340, 44, max_size=38))
        self.me_name = E.Type("少女A", "ZenKakuGothicNew-Bold", 28)
        self.me_handle = E.Type(HANDLE, "ZenKakuGothicNew-Regular", 21)
        self.stamp1 = E.Type("憎", "ShipporiMinchoB1-ExtraBold", 100)
        self.stamp2 = E.Type("い", "ShipporiMinchoB1-ExtraBold", 100)
        self.count_big = {n: E.Type(f"返信 {n}件", "ZenKakuGothicNew-Black", 46) for n in range(0, 16)}
        self.header = E.Type("少女A　▼　話題圏外", "ZenKakuGothicNew-Bold", 26)
        self.hint = E.Type("返信を入力…", "ZenKakuGothicNew-Regular", 30)
        self.typed = E.Type("許されないの？", "ZenKakuGothicNew-Medium", 38)
        self.typed_t = K.chars_of(45, "許されないの？")
        self.sent = E.Type("許されないの？", "ZenKakuGothicNew-Medium", 38)
        self.lyric = K.Strip("残した思いが", K.chars_of(42, "残した思いが"), size=58)
        self.lyric_first = K.Strip("捨てきれず", K.chars_of(42, "捨てきれず"), size=58)
        self.lyric_big = K.Strip("残した思いが", K.chars_of(42, "残した思いが"), size=118, pad=24)
        self.zero = E.Type("返信 0件", "ZenKakuGothicNew-Black", 210, tracking=6)
        self.zero_sub = E.Type("まだ返信はありません", "ZenKakuGothicNew-Medium", 54)
        self._quiet = False
        self._blows = False
        # the list, in the same type as the ranking in section 06
        self.list_head = E.Type("トレンド　総合", GOTHIC, 28)
        self.list_head_out = E.Type("トレンド　総合　▼　圏外", GOTHIC, 28)
        self.list_head2 = E.Type("いま話題のワード", "ZenKakuGothicNew-Bold", 24)
        self.list_date = E.Type(TODAY, GOTHIC, 30)
        self.list_end = E.Type("これ以上はありません", "ZenKakuGothicNew-Medium", 28)
        self.her_bar = Bar(0, 0, 400, 100, 0, seed=26)
        self.her_cat = E.Type("話題", "ZenKakuGothicNew-Bold", 30)
        # her icon: a crop from a picture with the bar already drawn in
        im = C.load(ROOT / "assets" / "gen" / "final" / "p01_bust_front.png")
        crop = im[300:1020, 180:900]
        bg = np.array([254, 228, 95], np.float32) / 255
        rgb = crop[..., :3] * crop[..., 3:4] + bg * (1 - crop[..., 3:4])
        self.me_icon = E.np_to_image(cv2.resize(np.dstack([rgb, np.ones(rgb.shape[:2], np.float32)]), (720, 720), interpolation=cv2.INTER_AREA))
        phone = C.load(ROOT / "assets" / "gen" / "cut" / "p03_phone_over_shoulder.png")
        phone, _ = C.key_magenta(phone)
        self.phone = E.np_to_image(K.duotone(phone, light=(0.60, 0.70, 0.90)))
        front = C.load(ROOT / "assets" / "gen" / "final" / "p04_face_lit_by_phone.png")
        import crisp
        # the last push goes past 4 times this picture's pixels
        self.front = E.np_to_image(crisp.upscale(K.duotone(front, light=(0.62, 0.80, 1.0)), FRONT_K))
        self.keys = {ch: E.Type(ch, "ZenKakuGothicNew-Bold", 30) for ch in "QWERTYUIOPASDFGHJKLZXCVBNM"}
        # where the screen is in the phone picture
        self.quad = (848.0, 275.0, 1392.0, 556.0)

    def flip_at(self, slot):
        """When each card turns over: the one in close-up first, the others in a wave going out from it as we back away."""
        if slot == TURN_SLOT:
            return FLIP + 0.05
        col, row = slot % 2, slot // 2
        tc, tr = TURN_SLOT % 2, TURN_SLOT // 2
        return TURN_OUT0 + 0.05 + 0.055 * (abs(row - tr) + 1.6 * abs(col - tc))

    def hit_view(self, k, t):
        """Where the view is for sung word k, at time t: centre in the page's own units, and size. A steady push on top of the blow."""
        x, y, w, h = self.slots[ORDER[k]]
        sv = HIT_S[k]
        # up close there is no room for a whole card: the sung word goes in the middle
        cx = x + w / 2 if sv < 2.4 else x + w - 120
        cy = y + h / 2
        nxt = HITS[k + 1] if k + 1 < len(HITS) else FLIP
        return cx, cy, sv * (1 + 0.05 * E.seg(t, HITS[k], nxt))

    def camera(self, t):
        """(cx, cy, s) from the first blow to where the wide page comes back."""
        if t >= FLIP:
            x, y, w, h = self.slots[TURN_SLOT]
            near = (x + 223.0, y + h / 2, TURN_S * (1 + 0.03 * E.seg(t, FLIP, TURN_OUT0)))
            far = (960.0 + SAFE, 540.0, 1.025)
            u = E.ease_io(E.seg(t, TURN_OUT0, TURN_OUT1), 2.2)
            return (E.lerp(near[0], far[0], u), E.lerp(near[1], far[1], u), math.exp(E.lerp(math.log(near[2]), math.log(far[2]), u)))
        k = 0
        for i, h_ in enumerate(HITS):
            if t >= h_ - THROW:
                k = i
        cx, cy, sv = self.hit_view(k, t)
        # thrown from the last card on to this one in two or three frames, there as the word is sung, and a little too close for a moment
        d = t - (HITS[k] - THROW)
        u = E.ease_out(d / (THROW + 0.035), 3.2)
        if k > 0:
            px, py, ps = self.hit_view(k - 1, HITS[k] - THROW)
            cx, cy = E.lerp(px, cx, u), E.lerp(py, cy, u)
            sv = math.exp(E.lerp(math.log(ps), math.log(sv), u))
        else:
            cx, cy = E.lerp(960.0 + SAFE, cx, u), E.lerp(540.0, cy, u)
            sv = math.exp(E.lerp(math.log(1.025), math.log(sv), u))
        sv *= 1 + 0.10 * math.exp(-max(d - 0.05, 0.0) * 13)
        # the blow itself, along a different line each time
        sign = 1 if k % 2 else -1
        j = 16 * math.exp(-max(d - 0.03, 0.0) * 22)
        return cx + sign * j / sv * 0.5, cy + j / sv, sv

    def frame_rgb(self, t):
        # a very short shutter on the page that comes over the list: it crosses the screen in a few frames
        self.shutter = 0.10 if PUSH0 - 0.02 <= t <= PUSH1 + 0.02 else 0.25
        if t < PUSH1 + 0.02 or HITS[0] - THROW - 0.01 <= t < TURN_OUT1 + 0.02:
            return K.soft_frame(self, t)
        return super().frame_rgb(t)

    def blur(self, t):
        if t < LIST_RUNS[-1][1]:
            return 12
        if PUSH0 - 0.02 <= t <= PUSH1 + 0.02:
            return 40
        for h in HITS:
            if h - THROW - 0.01 <= t <= h + 0.14:
                return 20
        if FLIP - 0.02 <= t <= FLIP + 0.22:
            return 8
        if TURN_OUT0 <= t <= TURN_OUT1:
            return 14
        if t >= FRONT:
            return 16   # the push speeds up on screen: too few sub-frames show as ghosted copies of the handwriting
        if PULL <= t <= PULLED:
            return 10
        return 1

    def avatar(self, c, x, y, r, i, flip_u):
        """flip_u: 0 still the stranger's icon, 1 fully turned into her."""
        k = math.cos(flip_u * math.pi)
        c.save()
        c.translate(x, y)
        c.scale(max(abs(k), 0.02), 1)
        if flip_u < 0.5:
            c.drawCircle(0, 0, r, skia.Paint(AntiAlias=True, Color4f=E.col("#2C313E")))
            n, inner = SHAPES[i]
            tone = ["#9AA1AE", "#C2C6CF", "#7C8391"][i % 3]
            c.drawPath(poly_path(n, inner, r * 0.62), skia.Paint(AntiAlias=True, Color4f=E.col(tone)))
        else:
            self.me(c, r)
        c.restore()

    def me(self, c, r):
        p = skia.Path()
        p.addCircle(0, 0, r)
        c.save()
        c.clipPath(p, True)
        s = 2 * r / self.me_icon.width()
        c.scale(s, s)
        c.translate(-self.me_icon.width() / 2, -self.me_icon.height() / 2)
        c.drawImage(self.me_icon, 0, 0, E.SAMPLING_DOWN)
        c.restore()
        c.drawCircle(0, 0, r, skia.Paint(AntiAlias=True, Color4f=E.col(E.RIN), Style=skia.Paint.kStroke_Style, StrokeWidth=4))

    def ui(self, c, t):
        c.clear(E.col(BG))
        E.rect(c, 0, 0, UI_W, 62, "#171A24")
        self.header.draw(c, SAFE + 26, 31, GREY, ax=0)
        count = sum(1 for h in HITS if t >= h)
        cnt = E.Type(f"返信 {count + (1 if t >= SEND else 0)}件", "ZenKakuGothicNew-Bold", 26)
        draft = ""
        for tk, tx in DRAFT:
            if t >= tk:
                draft = tx
        if not self._blows:
            cnt.draw(c, UI_W - SAFE - 26, 31, GREY, ax=1)
        # empty slots are very faint, so the screen visibly has room to fill
        for (x, y, w, h) in self.slots:
            E.rect(c, x, y, w, h, "#141822", radius=10)
        for k, slot in enumerate(ORDER):
            ht = HITS[k]
            if t < ht - 0.03:
                continue
            land = E.ease_out(E.seg(t, ht - 0.03, ht + 0.05), 3)
            x, y, w, h = self.slots[slot]
            sc = 1 + 0.55 * (1 - land)
            rec = 0.0
            a = E.clamp01(land * 2.5)
            hot = ht - 0.03 <= t < ht + HIT_HOT
            c.save()
            c.translate(x + w / 2, y + h / 2)
            c.scale(sc, sc)
            c.translate(-(x + w / 2), -(y + h / 2))
            E.rect(c, x, y, w, h, E.PAPER if hot else CARD, a, radius=10)
            if a >= 1:
                i = slot
                # the wave of flips runs in reading order
                ft = self.flip_at(slot)
                u = E.seg(t, ft, ft + (0.17 if slot == TURN_SLOT else 0.13))
                self.avatar(c, x + 66, y + h / 2, 50, i, u)
                n, hd, tx = self.type[i]
                if u >= 0.5:
                    n, hd = self.me_name, self.me_handle
                    color_n, color_h = E.RIN, E.RIN
                else:
                    color_n, color_h = (E.INK, E.INK) if hot else (TXT, GREY)
                n.draw(c, x + 134, y + 16, color_n, ax=0, ay=0)
                hd.draw(c, x + 142 + n.w, y + 22, color_h, ax=0, ay=0)
                tx.draw(c, x + 134, y + 58, E.INK if hot else TXT, ax=0, ay=0)
                # the sung word, stamped onto each card
                st_x = x + w - 172
                dim = 1 - 0.78 * E.ease_out(E.seg(t, ft, ft + 0.3), 2)
                st_col = E.INK if hot else "#F6F3EA"
                self.stamp1.draw(c, st_x, y + h / 2, st_col, alpha=dim)
                if t >= KUI[k]:
                    pop = 1 + 0.35 * (1 - E.ease_out((t - KUI[k]) / 0.08, 3))
                    self.stamp2.draw(c, st_x + 104, y + h / 2, st_col, alpha=dim, scale=pop)
            c.restore()
        # the keyboard comes up as we pull back: now this is plainly somebody typing
        ku = E.ease_out(E.seg(t, PULL - 0.16, PULL + 0.12), 3)
        kh = 590 * ku
        cy = 1020 - kh
        if ku > 0:
            E.rect(c, 0, 1080 - kh, UI_W, kh, "#20242F")
            rows = ["QWERTYUIOP", "ASDFGHJKL", "ZXCVBNM"]
            kw = (UI_W - 2 * SAFE - 120) / 10
            for r_, row in enumerate(rows):
                x0 = SAFE + 60 + (10 - len(row)) * kw / 2
                for i_, ch in enumerate(row):
                    kx, ky = x0 + i_ * kw, 1080 - kh + 24 + r_ * 140
                    E.rect(c, kx + 6, ky, kw - 12, 126, "#343945", radius=12)
                    self.keys[ch].draw(c, kx + kw / 2, ky + 63, "#C9CDD6")
            ky = 1080 - kh + 24 + 3 * 140
            E.rect(c, SAFE + 66, ky, kw * 1.5, 126, "#2A2E39", radius=12)
            E.Type("?123", "ZenKakuGothicNew-Bold", 28).draw(c, SAFE + 66 + kw * 0.75, ky + 63, "#C9CDD6")
            E.rect(c, SAFE + 66 + kw * 1.6, ky, kw * 6.3, 126, "#343945", radius=12)
            E.rect(c, SAFE + 66 + kw * 8.0, ky, kw * 1.9, 126, "#2A2E39", radius=12)
            E.Type("改行", "ZenKakuGothicNew-Bold", 30).draw(c, SAFE + 66 + kw * 8.95, ky + 63, "#C9CDD6")
        # compose bar: her icon has been sitting here all along, the only yellow on screen
        E.rect(c, 0, cy - 40, UI_W, 100, "#171A24")
        c.save()
        c.translate(SAFE + 100, cy + 10)
        self.me(c, 34)
        c.restore()
        E.rect(c, SAFE + 150, cy - 20, UI_W - 2 * SAFE - 330, 60, "#0E1118", radius=30)
        shown = [g for g in self.typed.run.glyphs if g.cluster < len(self.typed_t) and self.typed_t[g.cluster] <= t]
        if t >= SEND:
            shown = []
        cur_x = SAFE + 180
        if draft and t < DEMO_T0:
            dt_ = E.Type(draft, "ZenKakuGothicNew-Medium", 38)
            dt_.draw(c, cur_x, cy + 10, TXT, ax=0)
            cur_x += dt_.w + 6
        elif shown:
            dx = cur_x - self.typed.l
            dy = cy + 10 - self.typed.t - self.typed.h / 2
            for g in shown:
                c.drawPath(E.typo.glyph_path(g, dx=dx, dy=dy), skia.Paint(AntiAlias=True, Color4f=E.col(TXT)))
            b_ = shown[-1]
            cur_x = dx + b_.x + b_.path.computeTightBounds().right() + 6
        else:
            self.hint.draw(c, cur_x, cy + 10, "#5C6372", ax=0)
        if math.floor((t - DEMO_T0) / 0.26) % 2 == 0 or (shown and t < SEND) or (t < DEMO_T0 and any(0 <= t - tk < 0.16 for tk, _ in DRAFT)):
            E.rect(c, cur_x - 2, cy - 12, 4, 44, E.RIN)
        btn = SEND - 0.06 <= t <= SEND + 0.14
        E.rect(c, UI_W - SAFE - 170, cy - 20, 134, 60, E.RIN if btn else "#2C313E", radius=30)
        E.Type("送信", "ZenKakuGothicNew-Bold", 28).draw(c, UI_W - SAFE - 103, cy + 10, E.INK if btn else GREY)
        # the fifteenth comment: this line too is hers
        if t >= SEND:
            u = E.ease_out((t - SEND) / 0.16, 3)
            x, y, w, h = SAFE + 140, E.lerp(cy - 40, cy - 174, u), UI_W - 2 * SAFE - 280, 124
            E.rect(c, x, y, w, h, "#2A2610", radius=10)
            c.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(x, y, w, h), 10, 10),
                        skia.Paint(AntiAlias=True, Color4f=E.col(E.RIN), Style=skia.Paint.kStroke_Style, StrokeWidth=4))
            c.save()
            c.translate(x + 66, y + h / 2)
            self.me(c, 48)
            c.restore()
            self.me_name.draw(c, x + 134, y + 14, E.RIN, ax=0, ay=0)
            self.sent.draw(c, x + 134, y + 58, TXT, ax=0, ay=0)
        # the end of the last words, in the empty thread
        if t < HITS[0] - THROW and not self._quiet:
            self.lyric.draw(c, UI_W / 2, 520, t, ax=0.5, paper="#E8E9EC")
            # the first half of the line ends here; the second half takes over its place on its first note
            if PUSH1 <= t < self.lyric.times[0]:
                self.lyric_first.draw(c, UI_W / 2, 520, t, ax=0.5, paper="#E8E9EC")

    # ---- the way in: the list, and the last row of it ----
    def list_top(self, t):
        """The rank at the top of the screen. The last run comes to rest with a little give at the bottom of the list."""
        for a, b, r0, r1 in LIST_RUNS[:3]:
            if t < b:
                u = E.seg(t, a, b)
                return E.lerp(r0, r1, u ** 2.2 if a == T0 else u)
        a, b, r0, r1 = LIST_RUNS[3]
        return E.lerp(r0, r1, E.ease_out(E.seg(t, a, b), 1.7))

    def her_row(self, c, y, t):
        E.rect(c, 0, y, E.W, ROW_H, E.RIN)
        # pressed: a flat disc spreads from the finger across the row
        if t >= TAP:
            r = 1500 * E.ease_out(E.seg(t, TAP, TAP + 0.16), 2.5) + 30
            c.save()
            c.clipRect(skia.Rect.MakeXYWH(0, y, E.W, ROW_H))
            c.drawCircle(1130, y + ROW_H / 2, r, skia.Paint(AntiAlias=True, Color4f=E.col("#FFF4B0")))
            c.restore()
        rank_type(LAST_RANK).draw(c, 158, y + ROW_H / 2, E.INK, ax=1)
        s = ROW_H * 0.80 / 100
        c.save()
        c.translate(190 + 400 * 0.52 * s, y + ROW_H / 2)
        c.scale(s, s)
        self.her_bar.draw(c)
        c.restore()
        self.her_cat.draw(c, 1120, y + ROW_H / 2, E.INK, ax=0)
        E.Type(row_count(LAST_RANK), "ZenKakuGothicNew-Bold", 34).draw(c, E.W - 40, y + ROW_H / 2, E.INK, ax=1)

    def draw_list(self, c, t):
        top = self.list_top(t)
        c.clear(E.col(BG))
        first = max(1, int(math.floor(top)))
        # the margin above the first row is the list's own colour
        if top < 1:
            E.rect(c, 0, LIST_TOP, E.W, (1 - top) * ROW_H + 2, band_of(1)[1])
        for rank in range(first, min(first + 15, LAST_RANK + 1)):
            y = LIST_TOP + (rank - top) * ROW_H
            if y > E.H:
                break
            if rank == LAST_RANK:
                self.her_row(c, y, t)
                continue
            _, tone, text, rule = band_of(rank)
            E.rect(c, 0, y, E.W, ROW_H, tone)
            E.rect(c, 0, y + ROW_H - 2, E.W, 2, rule)
            title, cat = row_topic(rank)
            rank_type(rank).draw(c, 158, y + ROW_H / 2, text, ax=1)
            E.fit(title, GOTHIC, 880, 52, max_size=46).draw(c, 190, y + ROW_H / 2, text, ax=0)
            E.Type(cat, "ZenKakuGothicNew-Bold", 30).draw(c, 1120, y + ROW_H / 2, text, ax=0)
            E.Type(row_count(rank), "ZenKakuGothicNew-Bold", 34).draw(c, E.W - 40, y + ROW_H / 2, text, ax=1)
        # under the last row there is nothing; the list says so, in the dark
        end_y = LIST_TOP + (LAST_RANK + 1 - top) * ROW_H
        if end_y < E.H:
            self.list_end.draw(c, 960, end_y + 56, "#5C6372")
        E.rect(c, 0, 0, E.W, LIST_TOP, "#0A0A0F")
        (self.list_head if top < RANKED else self.list_head_out).draw(c, 40, LIST_TOP / 2, E.PAPER, ax=0)
        self.list_head2.draw(c, E.W - 40, LIST_TOP / 2, E.PAPER, ax=1)
        self.list_date.draw(c, 960, LIST_TOP / 2, E.RIN)

    def draw_way_in(self, c, t):
        u = E.ease_out(E.seg(t, PUSH0, PUSH1), 3)
        if u <= 0:
            self.draw_list(c, t)
        else:
            # the list slips a little to the left as the thread comes over it
            c.save()
            c.translate(-420 * u, 0)
            self.draw_list(c, t)
            c.restore()
            surf = skia.Surface(UI_W, UI_H)
            self.ui(surf.getCanvas(), t)
            x = E.W * (1 - u)
            c.drawImage(surf.makeImageSnapshot(), x - SAFE, 0, E.SAMPLING_DOWN)
            E.rect(c, x - 3, 0, 3, E.H, "#0A0A0F")
        # the sung words hang in the same place across the whole way in
        self.lyric_first.draw(c, 960, 520, t, ax=0.5, paper="#E8E9EC")

    def draw_empty(self, c, t):
        """151 to the demo: the thread has nothing in it. So close on what it does have."""
        self._quiet = True
        if t < CUT_ZERO:
            surf = skia.Surface(UI_W, UI_H)
            self.ui(surf.getCanvas(), t)
            c.clear(E.col(BG))
            c.drawImage(surf.makeImageSnapshot(), -SAFE, 0, E.SAMPLING_DOWN)
        elif t < CUT_FIELD:
            # the reply count, as large as the page
            c.clear(E.col(BG))
            s_ = 1 + 0.03 * E.seg(t, CUT_ZERO, CUT_FIELD)
            c.save()
            c.translate(960, 540)
            c.scale(s_, s_)
            c.translate(-960, -540)
            self.zero.draw(c, 960, 690, TXT)
            self.zero_sub.draw(c, 960, 846, GREY)
            c.restore()
        else:
            # her reply field, close, drawn large and not scaled up from a picture; very slowly nearer
            s_ = 2.5 + 0.16 * E.seg(t, CUT_FIELD, DEMO_T0)
            c.clear(E.col(BG))
            c.save()
            c.translate(70, 760)
            c.scale(s_, s_)
            c.translate(-(SAFE + 66), -1020)
            self.ui(c, t)
            c.restore()
        self._quiet = False
        self.lyric_big.draw(c, 960, 280, t, ax=0.5, paper="#E8E9EC")

    def draw(self, c, t):
        if t >= FRONT:
            self.draw_front(c, t)
            return
        if t < PUSH1:
            self.draw_way_in(c, t)
            return
        if t < DEMO_T0 and t >= self.lyric.times[0]:
            self.draw_empty(c, t)
            return
        if HITS[0] - THROW <= t < TURN_OUT1:
            self.draw_blows(c, t)
            return
        surf = skia.Surface(UI_W, UI_H)
        self.ui(surf.getCanvas(), t)
        ui = surf.makeImageSnapshot()
        if t < PULL:
            c.clear(E.col(BG))
            jolt = 0.0
            for h_ in HITS:
                if t >= h_:
                    jolt = 9 * math.exp(-(t - h_) * 26)
            lean = 1 + 0.025 * E.ease_io(E.seg(t, FLIP, FLIP + 0.5), 2)
            # the empty thread: the view settles back very slowly, and is at rest where the demo begins
            lean *= 1 + 0.025 * (1 - E.ease_io(E.seg(t, PUSH1, DEMO_T0), 2))
            c.save()
            c.translate(960, 540)
            c.scale(lean, lean)
            c.translate(-960, -540)
            c.drawImage(ui, -SAFE, jolt, E.SAMPLING_DOWN)
            c.restore()
            return
        # back out at a steady log rate: the whole interface is a phone screen in her hands
        qx0, qy0, qx1, qy1 = self.quad
        s0 = UI_H / (qy1 - qy0)
        # it stops close: the phone stays about half the frame, so her thumbs and the screen are what you read
        s1 = 1.75
        u = E.ease_out(E.seg(t, PULL, PULLED), 2.2)
        s = math.exp(E.lerp(math.log(s0), math.log(s1), u))
        cx0 = (qx0 + qx1) / 2
        cy0 = (qy0 + qy1) / 2
        px = E.lerp(cx0, 990.0, u)
        py = E.lerp(cy0, 430.0, u)
        c.clear(E.col("#0A0D16"))
        c.save()
        c.translate(960, 540)
        c.scale(s, s)
        c.translate(-px, -py)
        c.save()
        c.translate(qx0, qy0)
        c.scale((qx1 - qx0) / UI_W, (qy1 - qy0) / UI_H)
        c.drawImage(ui, 0, 0, E.SAMPLING)
        c.restore()
        p = skia.Paint(AntiAlias=True)
        p.setAlphaf(E.clamp01((t - PULL) / 0.08))
        c.drawImage(self.phone, 0, 0, E.SAMPLING, p)
        c.restore()

    def draw_blows(self, c, t):
        """The page itself, drawn at the size it is seen, so nothing goes soft however close we are."""
        cx, cy, s = self.camera(t)
        c.save()
        c.translate(960, 540)
        c.scale(s, s)
        c.translate(-cx, -cy)
        self._blows = t < FLIP
        self.ui(c, t)
        self._blows = False
        c.restore()
        # the count keeps going up in the corner of the frame while the page is too close to show its own
        if t < FLIP:
            n = sum(1 for h in HITS if t >= h)
            ty = self.count_big[n]
            E.rect(c, E.W - 40 - ty.w - 44, 34, ty.w + 44, 84, "#0E1118")
            ty.draw(c, E.W - 40 - 22, 76, E.PAPER, ax=1)

    def draw_front(self, c, t):
        c.clear(E.col("#070A12"))
        # a steady log push towards plain black inside the bar, clear of the handwriting
        u = E.seg(t, FRONT, T1 - 0.1)
        s0 = 1080 / self.front.height()
        # ends inside plain black: the solid bar to the side of the handwriting
        s = s0 * math.exp(u ** 1.15 * math.log(15.0))
        tx, ty = (595 + 212) * FRONT_K, 744 * FRONT_K
        cx = E.lerp(self.front.width() / 2, tx, E.ease_io(E.seg(u, 0.0, 0.5), 2))
        cy = E.lerp(self.front.height() / 2, ty, E.ease_io(E.seg(u, 0.0, 0.5), 2))
        c.save()
        c.translate(960, 540)
        c.scale(s, s)
        c.translate(-cx, -cy)
        c.drawImage(self.front, 0, 0, E.SAMPLING)
        c.restore()
        if t >= T1 - 0.12:
            c.clear(E.col("#050507"))
