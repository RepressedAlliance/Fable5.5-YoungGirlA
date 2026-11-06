"""Section 02, end: a line is typed and taken back three times. Above it, an old chat: two friends, a drawing, and the word that was theirs."""
import math
import sys
from pathlib import Path

import skia

sys.path.insert(0, str(Path(__file__).parent))
import common as K  # noqa: E402
import engine as E  # noqa: E402
import s03  # noqa: E402

ROOT = K.ROOT
F0, F1 = 1344, 1566
BG = "#171B26"      # the same dark interface as the comment thread in section 09: it is the same phone
BAR = "#171A24"
CARD = "#272C3A"
GREY = "#8C93A1"
TXT = "#E8E9EC"
UI = "ZenKakuGothicNew-Medium"
UIB = "ZenKakuGothicNew-Bold"
TEXT_SIZE = 58

# the camera: close on the input field, then back as the second draft is taken back, so what sits above it comes into view: the third
# draft is typed right under the old chat, and rubbed out under it
PULL0, PULL1 = 47.91, 48.50
PY_WIDE = 230.0       # at the wide end the field sits low in the frame and the keyboard is below it, the thread has all the rest
HOPS = (49.29, 49.75) # she scrolls down it, two flicks on the beat, to the end of it

# (who, text or None for the drawing, time). Two people going back and forth, big enough to read and to feel. Old to new.
CHAT = (("them", "ねえ なにしてるの", "16:40"), ("her", "ひま", "16:40"), ("them", "花かいた", "16:41"), ("them", None, "16:41"),
        ("her", "へたすぎ", "16:42"), ("them", "パッパ", "16:42"), ("her", "パッパ", "16:42"))
CHAT_SIZE = 60
BUB_H, BUB_GAP = 104, 14
HER_BUB = "#41507A"   # no yellow here yet: that she is one of these two is for section 09 to say
PHOTO_W = 380
SHEET_W, SHEET_H = 660, 440   # the drawing in the chat is a photo of the very sheet that lies on the table in section 03
PHOTO_H = PHOTO_W * SHEET_H / SHEET_W
PHOTO_X = 166
PUSH_IN = 51.44               # the last character has gone: nothing is left to look at but the drawing. The camera goes into it until its paper fills the frame

# compose bar / keyboard geometry, in final-framing pixels
BAR_Y, BAR_H = 540, 140
FIELD = (150, 562, 1490, 96)
CAND_Y, CAND_H = 680, 62
KEY_Y = 742
KEY_H = 82
ROWS = ["QWERTYUIOP", "ASDFGHJKL", "ZXCVBNM"]
MARGIN = 40


def syl(i):
    return [s["t"] for s in K.LYRICS[i]["syl"]]


def _events():
    """Every keystroke of the three drafts on the sung morae. Real romaji input: letters turn into kana, a space converts, enter confirms.
    (time, key, composing, selected, confirmed, candidates)"""
    a, b, d = syl(12), syl(13), syl(14)
    ev = []

    def add(t, key, comp="", sel="", done="", cand=()):
        ev.append((t, key, comp, sel, done, cand))

    # 本当は, on こ と ば を か く
    add(a[0], "H", "h", cand=())
    add(a[0] + 0.055, "O", "ほ", cand=("本", "星", "欲しい"))
    add(a[1], "N", "ほn", cand=("本", "星", "欲しい"))
    add(a[2], "T", "ほんt", cand=("本", "本当", "本当に"))
    add(a[2] + 0.055, "O", "ほんと", cand=("本当", "ほんと", "ホント"))
    add(a[3], "U", "ほんとう", cand=("本当", "本当に", "本島"))
    add(a[4], "H", "ほんとうh", cand=("本当", "本当に", "本島"))
    add(a[4] + 0.055, "A", "ほんとうは", cand=("本当は", "本当", "ホントウハ"))
    add(a[5], "SPACE", sel="本当は", cand=("本当は", "本当", "ホントウハ"))
    add(a[6], "RET", done="本当は")
    add(a[8], "BS", done="本当")
    add(a[8] + 0.15, "BS", done="本")
    add(a[8] + 0.30, "BS", done="")
    # あのね、 on こ と ば を; held; gone on ai-mai-ni
    add(b[0], "A", "あ", cand=("あの", "ありがとう", "会いたい"))
    add(b[1], "N", "あn", cand=("あの", "ありがとう", "会いたい"))
    add(b[1] + 0.055, "O", "あの", cand=("あの", "あのね", "あの人"))
    add(b[2], "N", "あのn", cand=("あの", "あのね", "あの人"))
    add(b[2] + 0.055, "E", "あのね", cand=("あのね", "アノネ", "あの"))
    add(b[3], "RET", done="あのね")
    add(b[5], "COMMA", done="あのね、")
    add(b[8], "BS", done="あのね")
    add(b[8] + 0.09, "BS", done="あの")
    add(b[8] + 0.18, "BS", done="あ")
    add(b[8] + 0.27, "BS", done="")
    # 違うの: it stays while the message comes into view, and goes on 君だけをさ
    add(d[0], "T", "t", cand=())
    add(d[0] + 0.055, "I", "ち", cand=("地", "血", "違う"))
    add(d[1], "G", "ちg", cand=("地", "血", "違う"))
    add(d[1] + 0.055, "A", "ちが", cand=("違う", "違い", "血が"))
    add(d[2], "U", "ちがう", cand=("違う", "ちがう", "違うの"))
    add(d[3], "N", "ちがうn", cand=("違う", "ちがう", "違うの"))
    add(d[3] + 0.055, "O", "ちがうの", cand=("違うの", "違う", "チガウノ"))
    add(d[5], "SPACE", sel="違うの", cand=("違うの", "違う", "チガウノ"))
    add(d[6], "RET", done="違うの")
    e = syl(15)
    add(e[5], "BS", done="違う")
    add(e[6], "BS", done="違")
    add(e[7], "BS", done="")
    return ev


class Drafts(E.Clip):
    name = "s02d"
    t0, t1 = F0 / 30, F1 / 30
    grain = 0.010
    shutter = 0.3

    def setup(self):
        self.ev = _events()
        self.cuts = tuple(e[0] for e in self.ev)     # a key is down or it is not: never half a letter in the shutter
        self.sheet = s03.record(SHEET_W, SHEET_H, s03.make_flowers()[2])
        self.strips = []
        for i, tx in ((12, "言葉を書く曖昧に"), (13, "言葉を書く曖昧に"), (14, "伝わりきらんないから"), (15, "君だけをさ信じて")):
            self.strips.append((K.LYRICS[i]["start"], K.Strip(tx, K.chars_of(i, tx), size=46)))
        self.keys = {ch: E.Type(ch, UIB, 28) for row in ROWS for ch in row}
        self.hint = E.Type("メッセージを入力", UI, 40)
        self.send = E.Type("送信", UIB, 38)
        self.date = E.Type("2年前", UIB, 30)
        self.stamps = {c_[2]: E.Type(c_[2], "ZenKakuGothicNew-Regular", 24) for c_ in CHAT}
        self.read = E.Type("既読", "ZenKakuGothicNew-Regular", 24)
        self.chat = [(w, None if tx is None else E.Type(tx, UIB, CHAT_SIZE), self.stamps[st]) for w, tx, st in CHAT]
        self.cache = {}

    def ty(self, s):
        if s not in self.cache:
            self.cache[s] = E.Type(s, UI, TEXT_SIZE)
        return self.cache[s]

    def small(self, s):
        k = ("s", s)
        if k not in self.cache:
            self.cache[k] = E.Type(s, UIB, 30)
        return self.cache[k]

    def photo_y(self, dy):
        """The top of the drawing on the thread's page."""
        y = BAR_Y - 22 + dy - self.chat_height() + 62
        for _, tx, _ in self.chat:
            if tx is None:
                return y
            y += BUB_H + BUB_GAP
        return y

    def push_matrix(self, t, s, px, py, dy):
        """After the camera of this section: the move into the drawing. Ends on section 03's first frame of it, turned and scaled to the unit."""
        u = E.ease_io(E.seg(t, PUSH_IN, self.t1), 2.1)
        # the drawing's centre on the screen under the section's own camera
        ax, ay = 960 + s * (PHOTO_X + PHOTO_W / 2 - px), 540 + s * (self.photo_y(dy) + PHOTO_H / 2 - py)
        bx, by, rot, unit = s03.fill_pose(self.t1)
        full = unit * SHEET_W / (PHOTO_W * s)
        k = math.exp(math.log(full) * u)
        w = (k - 1) / (full - 1)
        return skia.Matrix.Concat(skia.Matrix.Translate(ax + (bx - ax) * w, ay + (by - ay) * w),
                                  skia.Matrix.Concat(skia.Matrix.RotateDeg(rot * u), skia.Matrix.Concat(skia.Matrix.Scale(k, k), skia.Matrix.Translate(-ax, -ay))))

    def blur(self, t):
        if t >= PUSH_IN:
            return 1
        if PULL0 - 0.02 <= t <= PULL1 + 0.02:
            return 24
        for h in HOPS:
            if h - 0.02 <= t <= h + 0.20:
                return 16
        return 1

    def frame_rgb(self, t):
        return K.soft_frame(self, t)

    def state(self, t):
        cur = (self.t0, "", "", "", "", ())
        for e in self.ev:
            if e[0] <= t:
                cur = e
            else:
                break
        return cur

    def key_lit(self, t):
        lit = {}
        for e in self.ev:
            if e[0] <= t < e[0] + 0.10:
                lit[e[1]] = 1.0
        return lit

    def chat_height(self):
        h = 62 + sum((PHOTO_H if tx is None else BUB_H) + BUB_GAP for _, tx, _ in self.chat)
        return h

    def thread(self, c, dy):
        """The old chat, bottom-aligned on the input bar. No name, no face: a grey shape, like the strangers in section 09."""
        y = BAR_Y - 22 + dy - self.chat_height()
        self.date_chip(c, y)
        y += 62
        prev = None
        for who, ty, stamp in self.chat:
            if ty is None:
                # the drawing
                h = PHOTO_H
                x = PHOTO_X
                clip = skia.Path()
                clip.addRRect(skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(x, y, PHOTO_W, h), 22, 22))
                c.save()
                c.clipPath(clip, True)
                E.rect(c, x, y, PHOTO_W, h, E.PAPER)
                c.save()
                c.translate(x, y)
                c.scale(PHOTO_W / SHEET_W, h / SHEET_H)
                c.drawPicture(self.sheet)
                c.restore()
                c.restore()
                stamp.draw(c, x + PHOTO_W + 16, y + h - 6, GREY, ax=0, ay=1)
                y += h + BUB_GAP
                prev = who
                continue
            w = ty.w + 76
            if who == "them":
                x = 166
                if prev != "them":
                    self.icon(c, 96, y + BUB_H / 2)
                E.rect(c, x, y, w, BUB_H, CARD, radius=30)
                ty.draw(c, x + w / 2, y + BUB_H / 2, TXT)
                stamp.draw(c, x + w + 16, y + BUB_H - 8, GREY, ax=0, ay=1)
            else:
                x = 1860 - w
                E.rect(c, x, y, w, BUB_H, HER_BUB, radius=30)
                ty.draw(c, x + w / 2, y + BUB_H / 2, TXT)
                stamp.draw(c, x - 16, y + BUB_H - 8, GREY, ax=1, ay=1)
                self.read.draw(c, x - 16, y + BUB_H - 36, GREY, ax=1, ay=1)
            y += BUB_H + BUB_GAP
            prev = who

    def icon(self, c, x, y):
        c.drawCircle(x, y, 44, skia.Paint(AntiAlias=True, Color4f=E.col("#2C313E")))
        p = skia.Path()
        for i in range(10):
            a = -math.pi / 2 + i / 10 * math.tau
            q = 27 if i % 2 == 0 else 13
            (p.moveTo if i == 0 else p.lineTo)(x + math.cos(a) * q, y + math.sin(a) * q)
        p.close()
        c.drawPath(p, skia.Paint(AntiAlias=True, Color4f=E.col("#9AA1AE")))

    def compose(self, c, t, st):
        tt, key, comp, sel, done, cand = st
        E.rect(c, 0, BAR_Y, 1920, BAR_H, BAR)
        # no icon of hers here yet: that belongs to section 09. Only the same yellow caret.
        c.drawCircle(92, BAR_Y + BAR_H / 2, 34, skia.Paint(AntiAlias=True, Color4f=E.col("#2C313E")))
        pl = skia.Paint(AntiAlias=True, Color4f=E.col(GREY), Style=skia.Paint.kStroke_Style, StrokeWidth=5, StrokeCap=skia.Paint.kRound_Cap)
        c.drawLine(76, BAR_Y + BAR_H / 2, 108, BAR_Y + BAR_H / 2, pl)
        c.drawLine(92, BAR_Y + BAR_H / 2 - 16, 92, BAR_Y + BAR_H / 2 + 16, pl)
        fx, fy, fw, fh = FIELD
        E.rect(c, fx, fy, fw, fh, "#0E1118", radius=fh / 2)
        cy = fy + fh / 2
        x = fx + 44
        cur = x
        shown = comp or sel or done
        if shown:
            ty = self.ty(shown)
            if sel:
                E.rect(c, x - 6, cy - 44, ty.r - ty.l + 14, 88, "#39415A")
            ty.draw(c, x, cy, TXT, ax=0)
            if comp:
                E.rect(c, x, cy + 39, ty.w + 2, 4, TXT)
            elif sel:
                E.rect(c, x - 6, cy + 39, ty.w + 14, 6, TXT)
            cur = x + ty.w + 8
        else:
            self.hint.draw(c, x + 16, cy, "#5C6372", ax=0)
        # solid while the keys go, blinking when nothing is happening
        since = t - tt
        if since < 0.26 or int((since - 0.26) / 0.26) % 2 == 1:
            E.rect(c, cur, cy - 37, 5, 74, E.RIN)
        E.rect(c, 1670, fy, 190, fh, "#2C313E", radius=fh / 2)
        self.send.draw(c, 1765, cy, GREY)
        # the conversion strip of a Japanese keyboard
        E.rect(c, 0, CAND_Y, 1920, CAND_H, "#1C202C")
        cx = FIELD[0] + 44
        for i, s in enumerate(cand):
            w_ = self.small(s)
            if sel and i == 0:
                E.rect(c, cx - 18, CAND_Y + 8, w_.w + 36, CAND_H - 16, "#39415A", radius=8)
            w_.draw(c, cx, CAND_Y + CAND_H / 2, TXT if i == 0 else "#A9AEBA", ax=0)
            cx += w_.w + 70
            if i < len(cand) - 1:
                E.rect(c, cx - 36, CAND_Y + 16, 2, CAND_H - 32, "#343945")

    def key_rect(self, c, x, y, w, h, lit, base="#343945", radius=12):
        E.rect(c, x + 5, y + 5, w - 10, h - 10, "#7B8296" if lit else base, radius=radius)

    def keyboard(self, c, t, st):
        lit = self.key_lit(t)
        E.rect(c, 0, KEY_Y, 1920, 1080 - KEY_Y, "#20242F")
        kw = (1920 - 2 * MARGIN) / 10
        for r_, row in enumerate(ROWS):
            x0 = MARGIN + (10 - len(row)) * kw / 2
            y = KEY_Y + 4 + r_ * KEY_H
            for i_, ch in enumerate(row):
                on = ch in lit
                self.key_rect(c, x0 + i_ * kw, y, kw, KEY_H, on)
                self.keys[ch].draw(c, x0 + i_ * kw + kw / 2, y + KEY_H / 2, E.PAPER if on else "#C9CDD6")
        # shift and backspace share the third row
        y = KEY_Y + 4 + 2 * KEY_H
        self.key_rect(c, MARGIN, y, kw * 1.3, KEY_H, False, "#2A2E39")
        ax, ay = MARGIN + kw * 0.65, y + KEY_H / 2
        p = skia.Path()
        p.moveTo(ax, ay - 17)
        p.lineTo(ax + 18, ay + 2)
        p.lineTo(ax + 8, ay + 2)
        p.lineTo(ax + 8, ay + 16)
        p.lineTo(ax - 8, ay + 16)
        p.lineTo(ax - 8, ay + 2)
        p.lineTo(ax - 18, ay + 2)
        p.close()
        c.drawPath(p, skia.Paint(AntiAlias=True, Color4f=E.col("#C9CDD6"), Style=skia.Paint.kStroke_Style, StrokeWidth=3, StrokeJoin=skia.Paint.kRound_Join))
        bx = 1920 - MARGIN - kw * 1.3
        on = "BS" in lit
        self.key_rect(c, bx, y, kw * 1.3, KEY_H, on, "#2A2E39")
        ax, ay = bx + kw * 0.65, y + KEY_H / 2
        p = skia.Path()
        p.moveTo(ax - 32, ay)
        p.lineTo(ax - 14, ay - 18)
        p.lineTo(ax + 28, ay - 18)
        p.lineTo(ax + 28, ay + 18)
        p.lineTo(ax - 14, ay + 18)
        p.close()
        stroke = skia.Paint(AntiAlias=True, Color4f=E.col(E.PAPER if on else "#C9CDD6"), Style=skia.Paint.kStroke_Style, StrokeWidth=3, StrokeJoin=skia.Paint.kRound_Join, StrokeCap=skia.Paint.kRound_Cap)
        c.drawPath(p, stroke)
        c.drawLine(ax - 6, ay - 8, ax + 12, ay + 8, stroke)
        c.drawLine(ax + 12, ay - 8, ax - 6, ay + 8, stroke)
        # bottom row: labels change with the input state, as they do on a real keyboard
        tt, key, comp, sel, done, cand = st
        y = KEY_Y + 4 + 3 * KEY_H
        self.key_rect(c, MARGIN, y, kw * 1.6, KEY_H, False, "#2A2E39")
        self.small("?123").draw(c, MARGIN + kw * 0.8, y + KEY_H / 2, "#C9CDD6")
        self.key_rect(c, MARGIN + kw * 1.6, y, kw * 1.0, KEY_H, "COMMA" in lit)
        self.small("、").draw(c, MARGIN + kw * 2.1, y + KEY_H / 2, E.PAPER if "COMMA" in lit else "#C9CDD6")
        sx, sw = MARGIN + kw * 2.6, kw * 5.2
        self.key_rect(c, sx, y, sw, KEY_H, "SPACE" in lit)
        self.small("次候補" if sel else ("変換" if comp else "空白")).draw(c, sx + sw / 2, y + KEY_H / 2, E.PAPER if "SPACE" in lit else "#C9CDD6")
        rx, rw = MARGIN + kw * 7.8, kw * 2.2
        self.key_rect(c, rx, y, rw, KEY_H, "RET" in lit, "#2A2E39")
        self.small("確定" if (comp or sel) else "改行").draw(c, rx + rw / 2, y + KEY_H / 2, E.PAPER if "RET" in lit else "#C9CDD6")

    def draw(self, c, t):
        c.clear(E.col(BG))
        u = E.ease_io(E.seg(t, PULL0, PULL1), 2.6)
        # close framing: the field fills the frame, the keyboard is cropped; a slow lean in while she types
        sa = 1.90 * (1 + 0.012 * (t - self.t0))
        # final framing: the whole width of the screen, leaning in very slightly
        sb = 1.0 + 0.016 * E.seg(t, PULL1, self.t1)
        s = math.exp(E.lerp(math.log(sa), math.log(sb), u))
        # the close framing is anchored at the left end of the field, so the lean never crops what she is typing
        px = E.lerp(118 + 960 / s, 960.0, u)
        py = E.lerp(700.0, PY_WIDE, u)
        # nothing past the sides of the screen may show, so the view stays inside its width; above the bar is the thread
        hw = 960 / s
        px = min(max(px, hw), 1920 - hw) if hw <= 960 else 960
        st = self.state(t)
        # the thread is scrolled away while we are close; it comes down into the space above the field, and is flicked on to its end
        over = max(self.chat_height() - 798.0, 60.0)     # the first thing seen is the top of the chat
        hop = over * (1 - 0.5 * E.ease_out(E.seg(t, HOPS[0], HOPS[0] + 0.18), 3) - 0.5 * E.ease_out(E.seg(t, HOPS[1], HOPS[1] + 0.18), 3))
        scroll = E.lerp(-760, 0, u) + hop
        c.save()
        if t >= PUSH_IN:
            c.concat(self.push_matrix(t, s, px, py, scroll))
        c.translate(960, 540)
        c.scale(s, s)
        c.translate(-px, -py)
        c.save()
        c.clipRect(skia.Rect.MakeXYWH(0, -900, 1920, 900 + BAR_Y))
        if u > 0:
            self.thread(c, scroll)
        c.restore()
        self.compose(c, t, st)
        self.keyboard(c, t, st)
        c.restore()
        # the sung line
        cur = None
        for start, strip in self.strips:
            if t >= start:
                cur = strip
        if cur is not None:
            cur.draw(c, 960, 1034, t, ax=0.5)

    def date_chip(self, c, dy):
        w, h = self.date.w + 44, 46
        E.rect(c, 960 - w / 2, 18 + dy, w, h, "#232836", radius=h / 2)
        self.date.draw(c, 960, 18 + dy + h / 2, GREY)
