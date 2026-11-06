"""Printed things for the gate, lockers, train and outro: run once with the project's Python. Writes assets/tex/s02/."""
import sys
from pathlib import Path

import cv2
import numpy as np
import skia

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / "src")]
import engine as E  # noqa: E402

OUT = ROOT / "assets" / "tex" / "s02"
OUT.mkdir(parents=True, exist_ok=True)
FINAL = ROOT / "assets" / "gen" / "final"
MIN = "ShipporiMinchoB1-ExtraBold"
GOTH = "ZenKakuGothicNew-Black"
GB = "ZenKakuGothicNew-Bold"
GM = "ZenKakuGothicNew-Medium"
TAPE_YELLOW = E.RIN


def save(name, w, h, draw, transparent=False):
    s = skia.Surface(w, h)
    c = s.getCanvas()
    c.clear(skia.Color4f(0, 0, 0, 0) if transparent else E.col(E.PAPER))
    draw(c)
    a = s.makeImageSnapshot().toarray(colorType=skia.ColorType.kRGBA_8888_ColorType, alphaType=skia.AlphaType.kUnpremul_AlphaType)
    cv2.imwrite(str(OUT / f"{name}.png"), a[..., [2, 1, 0, 3]])


def poly(c, pts, color):
    p = skia.Path()
    p.moveTo(*pts[0])
    for q in pts[1:]:
        p.lineTo(*q)
    p.close()
    c.drawPath(p, skia.Paint(AntiAlias=True, Color4f=E.col(color)))


def stroke(c, pts, color, w):
    p = skia.Path()
    p.moveTo(*pts[0])
    for q in pts[1:]:
        p.lineTo(*q)
    c.drawPath(p, skia.Paint(AntiAlias=True, Color4f=E.col(color), Style=skia.Paint.kStroke_Style, StrokeWidth=w,
                             StrokeCap=skia.Paint.kRound_Cap, StrokeJoin=skia.Paint.kRound_Join))


def fitted(c, text, font, x, y, w, h, color=E.INK, vertical=False, ax=0.5, ay=0.5, tracking=0.0):
    t = E.fit(text, font, w, h, vertical=vertical, tracking=tracking)
    t.draw(c, x + w * ax, y + h * ay, color, ax=ax, ay=ay)


# ------------------------------------------------------------------ the school gate
def tape(c):
    E.rect(c, 0, 0, 1024, 128, TAPE_YELLOW)
    E.rect(c, 0, 0, 1024, 10, E.INK)
    E.rect(c, 0, 118, 1024, 10, E.INK)
    for k in range(2):
        fitted(c, "立入禁止", GOTH, 40 + k * 512, 18, 340, 92)
        for i in range(3):
            x = 420 + k * 512 + i * 28
            poly(c, [(x, 18), (x + 16, 18), (x - 4, 110), (x - 20, 110)], E.INK)


def mosaic(c):
    E.rect(c, 0, 0, 296, 920, E.PAPER)
    E.rect(c, 0, 0, 296, 12, E.INK)
    E.rect(c, 0, 908, 296, 12, E.INK)
    # the same blocks as the plate in the magazine photo
    rng = np.random.default_rng(7)
    for j in range(9):
        for i in range(3):
            g = rng.choice(["#1E2127", "#555A62", "#8C9095", "#2E3138"])
            E.rect(c, 40 + i * 76, 64 + j * 88, 72, 84, g)


def school_plate(c):
    E.rect(c, 0, 0, 296, 920, E.PAPER)
    E.rect(c, 0, 0, 296, 12, E.INK)
    E.rect(c, 0, 908, 296, 12, E.INK)
    fitted(c, "東都市立青葉中学校", MIN, 58, 50, 180, 820, vertical=True)


def facade(c):
    w, h = 4096, 1024
    E.rect(c, 0, 0, w, h, "#E3E4DC")
    E.rect(c, 0, 470, w, 26, "#B9BCB6")
    E.rect(c, 0, 0, w, 40, "#5B6068")
    for y in (110, 560):
        for i in range(26):
            x = 20 + i * 158
            E.rect(c, x, y, 118, 300, "#4F6E8E")
            poly(c, [(x, y + 300), (x + 62, y), (x + 100, y), (x + 38, y + 300)], "#8FD3EE")
            E.rect(c, x + 56, y, 8, 300, "#E3E4DC")
            E.rect(c, x, y + 96, 118, 6, "#E3E4DC")
            E.rect(c, x - 8, y + 300, 134, 12, "#B9BCB6")


def facade_warm(c):
    w, h = 4096, 1024
    E.rect(c, 0, 0, w, h, "#EFE7D2")
    E.rect(c, 0, 470, w, 26, "#CFC4A8")
    E.rect(c, 0, 0, w, 40, "#6B6258")
    for y in (110, 560):
        for i in range(26):
            x = 20 + i * 158
            E.rect(c, x, y, 118, 300, "#5F7F96")
            poly(c, [(x, y + 300), (x + 62, y), (x + 100, y), (x + 38, y + 300)], "#F7E7B0")
            E.rect(c, x + 56, y, 8, 300, "#EFE7D2")
            E.rect(c, x, y + 96, 118, 6, "#EFE7D2")
            E.rect(c, x - 8, y + 300, 134, 12, "#CFC4A8")


# ------------------------------------------------------------------ name plates
NAMES = """佐藤 美咲|鈴木 陽菜|高橋 結衣|田中 葵|伊藤 凛|渡辺 咲良|山本 優奈|中村 花|小林 真央|加藤 七海|吉田 愛|山田 彩乃|佐々木 遥|山口 楓|松本 千尋|井上 明日香
木村 莉子|林 菜々子|斎藤 瑞希|清水 詩織|山崎 蒼|森 大翔|池田 悠真|橋本 蓮|阿部 陽斗|石川 湊|山下 樹|中島 颯太|石井 朝陽|小川 律|前田 海斗|岡田 奏
長谷川 新|藤田 悠人|後藤 一輝|近藤 拓海|坂本 匠|遠藤 大和|青木 陸|藤井 蒼空|西村 空|福田 和真|太田 怜|三浦 晴|藤原 光|岡本 翼|松田 涼|中川 隼
中野 千夏|原田 夏帆|小野 美月|田村 桃子|竹内 円香|金子 ひかり|和田 綾|中山 舞|石田 萌|上田 由衣|森田 若葉|原 杏|柴田 恵|酒井 栞|工藤 雫|横山 琴音
宮崎 孝太|宮本 健|内田 誠|高木 亮|安藤 剛|谷口 潤|大野 修|丸山 勇|今井 岳|河野 俊|藤本 聡|村上 宏|武田 洋|上野 学|杉山 悟|増田 徹
小島 香|平野 望|大塚 梓|千葉 茜|久保 薫|松井 環|岩崎 泉|木下 文|野口 静|菊地 雪|佐野 澪|野村 紬|新井 灯|渡部 唯|杉本 碧|古川 文乃""".replace("\n", "|").split("|")
PLATE_W, PLATE_H, PLATE_COLS = 256, 64, 8
PLATE_ROWS = len(NAMES) // PLATE_COLS + (1 if len(NAMES) % PLATE_COLS else 0)


def plates(c):
    for i, n in enumerate(NAMES):
        x, y = (i % PLATE_COLS) * PLATE_W, (i // PLATE_COLS) * PLATE_H
        E.rect(c, x, y, PLATE_W, PLATE_H, E.PAPER)
        E.rect(c, x, y, PLATE_W, 3, "#8C9095")
        E.rect(c, x, y + PLATE_H - 3, PLATE_W, 3, "#8C9095")
        E.rect(c, x, y, 3, PLATE_H, "#8C9095")
        E.rect(c, x + PLATE_W - 3, y, 3, PLATE_H, "#8C9095")
        fitted(c, n, GB, x + 16, y + 9, PLATE_W - 32, PLATE_H - 18, tracking=4)


def plate_black(c):
    """Her plate: a paper plate gone over and over with a marker, past its edges. Transparent around it."""
    w, h = 512, 180
    # the plate underneath, same proportions as the others
    x0, y0, x1, y1 = 36, 36, w - 36, h - 36
    E.rect(c, x0 - 3, y0 - 3, x1 - x0 + 6, y1 - y0 + 6, "#8C9095")
    E.rect(c, x0, y0, x1 - x0, y1 - y0, E.PAPER)
    rng = np.random.default_rng(12)
    # the marker goes over and over, near enough to solid, past the plate's edge here and there
    for k, wd in enumerate((30, 26, 26)):
        pts = []
        n = 13
        for i in range(n * 2 + 1):
            u = i / (n * 2)
            x = x0 - 8 + (x1 - x0 + 16) * u + rng.uniform(-10, 10)
            y = (y0 - 6 + rng.uniform(-14, 6)) if i % 2 == 0 else (y1 + 6 + rng.uniform(-6, 14))
            pts.append((x, y))
        stroke(c, pts, E.INK, wd)
    # long passes along the plate, leaving a sliver of white here and there at the ends
    for y, wd in ((y0 + 14, 26), (y0 + 40, 28), (y1 - 12, 24)):
        stroke(c, [(x0 - 18 + rng.uniform(0, 8), y + rng.uniform(-2, 2)), (x1 + 16 - rng.uniform(0, 8), y + rng.uniform(-3, 3))], E.INK, wd)


def plate_torn(c):
    """Her plate holder after the plate has been torn off: a paler patch, glue marks, torn paper left at the corners."""
    w, h = 512, 180
    x0, y0, x1, y1 = 36, 36, w - 36, h - 36
    E.rect(c, x0 - 3, y0 - 3, x1 - x0 + 6, y1 - y0 + 6, "#BDB7A2")
    E.rect(c, x0, y0, x1 - x0, y1 - y0, "#F4F0E2")
    # glue
    for gx in (x0 + 12, x1 - 88):
        E.rect(c, gx, y0 + 8, 76, 14, "#D8D0B6")
        E.rect(c, gx, y1 - 22, 76, 14, "#D8D0B6")
    # torn paper left behind
    poly(c, [(x0 - 3, y0 - 3), (x0 + 56, y0 - 3), (x0 + 44, y0 + 12), (x0 + 22, y0 + 18), (x0 + 16, y0 + 40), (x0 - 3, y0 + 52)], E.PAPER)
    stroke(c, [(x0 + 56, y0 - 3), (x0 + 44, y0 + 12), (x0 + 22, y0 + 18), (x0 + 16, y0 + 40), (x0 - 3, y0 + 52)], E.INK, 2.5)
    poly(c, [(x1 + 3, y1 + 3), (x1 - 70, y1 + 3), (x1 - 52, y1 - 12), (x1 - 34, y1 - 8), (x1 - 18, y1 - 30), (x1 + 3, y1 - 38)], E.PAPER)
    stroke(c, [(x1 - 70, y1 + 3), (x1 - 52, y1 - 12), (x1 - 34, y1 - 8), (x1 - 18, y1 - 30), (x1 + 3, y1 - 38)], E.INK, 2.5)


def hall_floor(c):
    E.rect(c, 0, 0, 512, 512, "#AEB5AE")
    for i in range(0, 512, 128):
        for j in range(0, 512, 128):
            if (i // 128 + j // 128) % 2:
                E.rect(c, i, j, 128, 128, "#A5ADA7")
    for i in range(0, 513, 128):
        E.rect(c, i - 1, 0, 2, 512, "#8E9690")
        E.rect(c, 0, i - 1, 512, 2, "#8E9690")


def apron(c):
    E.rect(c, 0, 0, 1024, 1024, "#B9BCB6")
    for i in range(0, 1025, 256):
        E.rect(c, i - 2, 0, 4, 1024, "#8F9490")
        E.rect(c, 0, i - 2, 1024, 4, "#8F9490")
    rng = np.random.default_rng(5)
    for _ in range(9):
        x, y = rng.uniform(0, 1024), rng.uniform(0, 1024)
        w, h = rng.uniform(70, 220), rng.uniform(40, 150)
        E.rect(c, x, y, w, h, "#AEB2AC")


def notice(c, title, lines, band=E.CYAN, w=512, h=720):
    E.rect(c, 0, 0, w, h, E.PAPER)
    E.rect(c, 0, 0, w, 110, band)
    fitted(c, title, GOTH, 30, 16, w - 60, 78, E.INK)
    y = 150
    for ln in lines:
        fitted(c, ln, GM, 40, y, w - 80, 70, E.INK, ax=0)
        y += 96


def notice_a(c):
    notice(c, "下校時刻", ["夏季 十七時三十分", "冬季 十六時三十分", "雨の日は傘立てへ", "上履きをそろえる"])


def notice_b(c):
    notice(c, "保健だより", ["手洗い・うがい", "早寝 早起き 朝ごはん", "かぜに気をつけよう", "十一月号"], band=E.RIN)


# ------------------------------------------------------------------ hanging ads about her
AD_W, AD_H = 1456, 1000
HER_ADS = [
    ("週刊東都", "p01_bust_front", "少女Aの素顔", "同級生が語る「普通の子」", "#CFE7EE", 1.12, 0.06),
    ("週刊ライト", "t01_candid_turn", "校門前で直撃", "本誌だけが撮った一枚", "#EDE2B9", 1.05, 0.34),
    ("週刊東都", "w01_honor", "学年一位の優等生", "担任がもらした一言", "#DCE6D2", 1.45, 0.20),
    ("月刊ウワサ", "w02_delinquent", "札付きの不良だった", "近所の人が見た夜", "#D9D5DC", 1.45, 0.20),
    ("週刊ドア", "t03_candid_hand", "なぜ黙るのか", "専門家が徹底検証", "#F1D9C2", 1.4, 0.12),
    ("週刊ライト", "w05_shut_in", "部屋から出ない理由", "元同級生10人の証言", "#D5DEE9", 1.45, 0.20),
    ("週刊東都", "w07_idol", "アイドル志望の噂", "独占入手 未公開写真", "#F5D9E2", 1.45, 0.20),
    ("月刊ウワサ", "w08_artist", "天才絵描きの裏の顔", "本人のノートを入手", "#D8E7E2", 1.45, 0.20),
    ("週刊ドア", "w10_shrine", "実家は神社か", "親族が口を開いた", "#EFE6D0", 1.45, 0.20),
    ("週刊ライト", "g05_stand", "少女Aを知る全員", "緊急特集 第三弾", "#CFE0EE", 1.25, 0.22),
]


def her_ad(i):
    mast, fig, head, sub, panel, zoom, top = HER_ADS[i]

    def draw(c):
        E.rect(c, 0, 0, AD_W, AD_H, E.PAPER)
        # masthead band
        E.rect(c, 0, 0, AD_W, 132, E.INK)
        fitted(c, mast, GOTH, 40, 22, 460, 88, E.RIN, ax=0)
        fitted(c, "11月5日号 定価480円", GB, AD_W - 460, 46, 420, 44, E.PAPER, ax=1)
        # photo panel
        px, py, pw, ph = 40, 166, 610, AD_H - 206
        c.save()
        c.clipRect(skia.Rect.MakeXYWH(px, py, pw, ph))
        E.rect(c, px, py, pw, ph, panel)
        im = E.load_image(FINAL / f"{fig}.png")
        s = pw / im.width() * zoom
        E.draw_image(c, im, px + pw / 2, py - im.height() * s * top * 0.25, s, ax=0.5, ay=0.0)
        c.restore()
        E.rect(c, px, py, pw, 6, E.INK)
        E.rect(c, px, py + ph - 6, pw, 6, E.INK)
        E.rect(c, px, py, 6, ph, E.INK)
        E.rect(c, px + pw - 6, py, 6, ph, E.INK)
        # head and sub in vertical columns, right to left
        # in a vertical line a Latin A lies on its side: the full-width letter stands up like the kana round it
        fitted(c, head.replace("A", "Ａ"), MIN, AD_W - 300, 170, 250, AD_H - 210, vertical=True)
        fitted(c, sub, GOTH, AD_W - 470, 190, 120, AD_H - 250, vertical=True, ay=0.0)
        E.rect(c, 690, 170, 110, 110, E.RIN)
        fitted(c, "独占", GOTH, 700, 180, 90, 90)
        fitted(c, "少女A", MIN, 680, 310, 130, 130, E.INK)
        for k in range(5):
            E.rect(c, 700, 480 + k * 56, 90, 8, "#8C9095")
    return draw


def her_long(i):
    mast, fig, head, sub, panel, zoom, top = HER_ADS[i]

    def draw(c):
        w, h = 2048, 512
        E.rect(c, 0, 0, w, h, E.RIN if i % 2 == 0 else E.PAPER)
        c.save()
        c.clipRect(skia.Rect.MakeXYWH(30, 30, 420, h - 60))
        E.rect(c, 30, 30, 420, h - 60, panel)
        im = E.load_image(FINAL / f"{fig}.png")
        s = 420 / im.width() * zoom
        E.draw_image(c, im, 240, 30 - im.height() * s * top * 0.3, s, ax=0.5, ay=0.0)
        c.restore()
        fitted(c, head, MIN, 490, 60, w - 880, 240)
        fitted(c, sub, GOTH, 490, 320, w - 880, 120)
        fitted(c, mast, GOTH, w - 360, 150, 320, 200)
    return draw


# ------------------------------------------------------------------ the same frames, six months on: other people's business
def ad_onsen(c):
    E.rect(c, 0, 0, AD_W, AD_H, "#CFE9EE")
    poly(c, [(0, 760), (420, 300), (760, 640), (1040, 380), (1456, 780), (1456, 1000), (0, 1000)], "#6FA88E")
    poly(c, [(0, 860), (1456, 800), (1456, 1000), (0, 1000)], "#F2D9A8")
    c.drawCircle(1180, 220, 110, skia.Paint(AntiAlias=True, Color4f=E.col("#F7A65A")))
    fitted(c, "ひと休み、箱根へ。", MIN, 90, 80, 860, 170, E.INK, ax=0)
    fitted(c, "日帰り温泉きっぷ 発売中", GOTH, 90, 880, 900, 80, E.INK, ax=0)


def ad_soda(c):
    E.rect(c, 0, 0, AD_W, AD_H, "#F7E7A6")
    for i, (x, y, r) in enumerate([(240, 620, 60), (420, 300, 34), (150, 260, 22), (560, 780, 40), (640, 180, 28)]):
        c.drawCircle(x, y, r, skia.Paint(AntiAlias=True, Color4f=E.col(E.PAPER)))
    E.rect(c, 880, 120, 270, 760, E.CYAN, radius=50)
    E.rect(c, 950, 40, 130, 100, "#F7F4EA", radius=16)
    fitted(c, "サイダー", MIN, 930, 220, 170, 540, E.INK, vertical=True)
    fitted(c, "はじける、新発売。", MIN, 70, 400, 760, 190, E.INK, ax=0)
    fitted(c, "全国のお店で 150円", GOTH, 70, 620, 620, 70, E.INK, ax=0)


def ad_english(c):
    E.rect(c, 0, 0, AD_W, AD_H, E.PAPER)
    E.rect(c, 0, 0, 520, AD_H, "#F2B8A2")
    fitted(c, "ABC", GOTH, 70, 340, 380, 240, E.PAPER)
    fitted(c, "はじめての英会話", MIN, 590, 200, 800, 220, E.INK, ax=0)
    fitted(c, "駅前校 無料体験 受付中", GOTH, 590, 490, 780, 100, E.INK, ax=0)
    fitted(c, "週一回 三十分から", GB, 590, 640, 600, 70, "#555A62", ax=0)


def ad_condo(c):
    E.rect(c, 0, 0, AD_W, AD_H, "#DDE7D6")
    for i, (x, h) in enumerate([(120, 520), (340, 660), (560, 420)]):
        E.rect(c, x, AD_H - h, 180, h, "#F6F3EA")
        for j in range(int(h / 90)):
            for k in range(2):
                E.rect(c, x + 24 + k * 74, AD_H - h + 26 + j * 90, 52, 54, "#7FA2B4")
    fitted(c, "駅徒歩五分の新築", MIN, 800, 180, 600, 220, E.INK, ax=0)
    fitted(c, "モデルルーム公開中", GOTH, 800, 460, 600, 96, E.INK, ax=0)
    fitted(c, "週末 見学会", GB, 800, 600, 400, 70, "#555A62", ax=0)


def ad_movie(c):
    E.rect(c, 0, 0, AD_W, AD_H, "#23304A")
    c.drawCircle(1000, 400, 300, skia.Paint(AntiAlias=True, Color4f=E.col("#F4D27A")))
    poly(c, [(0, 1000), (0, 760), (500, 640), (980, 780), (1456, 620), (1456, 1000)], "#101726")
    fitted(c, "夏のおわりに", MIN, 90, 140, 640, 200, E.PAPER, ax=0)
    fitted(c, "今秋 全国ロードショー", GOTH, 90, 860, 860, 84, E.PAPER, ax=0)


def ad_other_mag(c):
    """The same magazine's next story. Words only, no picture of anybody."""
    E.rect(c, 0, 0, AD_W, AD_H, E.PAPER)
    E.rect(c, 0, 0, AD_W, 132, E.INK)
    fitted(c, "週刊東都", GOTH, 40, 22, 460, 88, E.RIN, ax=0)
    fitted(c, "5月20日号 定価480円", GB, AD_W - 460, 46, 420, 44, E.PAPER, ax=1)
    fitted(c, "少女Bの素顔", MIN, 90, 220, 1270, 300)
    fitted(c, "同級生が語る「普通の子」", GOTH, 170, 570, 1110, 120)
    fitted(c, "ほかに 夏の行楽特集 / 物価と家計", GB, 240, 780, 970, 70, "#555A62")


def long_other(text, sub, bg):
    def draw(c):
        w, h = 2048, 512
        E.rect(c, 0, 0, w, h, bg)
        fitted(c, text, MIN, 90, 70, w - 180, 240)
        fitted(c, sub, GOTH, 200, 340, w - 400, 100)
    return draw


def gate_notice(c):
    """The enamel notice on a school's gate post."""
    E.rect(c, 0, 0, 552, 408, "#F6F3EA")
    E.rect(c, 10, 10, 532, 388, "#23438C")
    E.rect(c, 20, 20, 512, 368, "#F6F3EA")
    fitted(c, "御用の方は", GOTH, 56, 60, 440, 92, "#23438C", ax=0.5)
    fitted(c, "事務室へ", GOTH, 56, 160, 440, 108, "#23438C", ax=0.5)
    fitted(c, "お回りください", GB, 56, 288, 440, 66, "#23438C", ax=0.5)


# ------------------------------------------------------------------ the weekly in everyone's hands on the train: her on the cover, a slip of paper in the hall
COVER_W, COVER_H = 600, 840


def mag_cover(i):
    """A weekly's cover: readable small. A masthead band, her with the bar over her eyes filling it, one big line."""
    mast, fig, head, sub, panel, zoom, top = HER_ADS[i % len(HER_ADS)]

    def draw(c):
        E.rect(c, 0, 0, COVER_W, COVER_H, panel)
        c.save()
        c.clipRect(skia.Rect.MakeXYWH(0, 110, COVER_W, COVER_H - 110))
        im = E.load_image(FINAL / f"{fig}.png")
        s = COVER_W / im.width() * zoom * 1.05
        E.draw_image(c, im, COVER_W * 0.40, 110 - im.height() * s * top * 0.25, s, ax=0.5, ay=0.0)
        c.restore()
        E.rect(c, 0, 0, COVER_W, 110, E.INK)
        fitted(c, mast, GOTH, 24, 16, COVER_W - 48, 78, E.RIN)
        # the line stands in a paper column down the right edge
        E.rect(c, COVER_W - 170, 110, 170, COVER_H - 110, E.PAPER)
        fitted(c, head.replace("A", "Ａ"), MIN, COVER_W - 158, 130, 146, COVER_H - 150, vertical=True)
    return draw


def mag_back(c):
    """The back cover of the open one: somebody else's ad."""
    E.rect(c, 0, 0, COVER_W, COVER_H, "#DCE7E2")
    E.rect(c, 0, COVER_H - 200, COVER_W, 200, E.INK)
    fitted(c, "のどに、すっと。", MIN, 60, 90, COVER_W - 120, 300)
    fitted(c, "トーブ製薬", GOTH, 60, COVER_H - 160, COVER_W - 120, 110, E.PAPER)


SLIP_COLS, SLIP_ROWS = 4, 3
SLIP_W, SLIP_H = 240, 150
SLIPS = (("見た？", E.PAPER), ("ここ", E.RIN), ("少女Aの", E.PAPER), ("本人？", "#BFE8F5"), ("ここだって", E.PAPER), ("うそ", E.RIN),
         ("写真あるよ", E.PAPER), ("見に来た", "#BFE8F5"), ("ほんと？", E.PAPER), ("→", E.RIN), ("この列", E.PAPER), ("拡散希望", "#BFE8F5"))


def hall_slips(c):
    """Notes people have stuck on the lockers: hand-sized, each one with a strip of tape."""
    for k, (text, bg) in enumerate(SLIPS):
        x, y = (k % SLIP_COLS) * SLIP_W, (k // SLIP_COLS) * SLIP_H
        E.rect(c, x, y, SLIP_W, SLIP_H, bg)
        E.rect(c, x, y, SLIP_W, 5, E.INK)
        E.rect(c, x, y + SLIP_H - 5, SLIP_W, 5, E.INK)
        E.rect(c, x, y, 5, SLIP_H, E.INK)
        E.rect(c, x + SLIP_W - 5, y, 5, SLIP_H, E.INK)
        fitted(c, text, "ZenKakuGothicNew-Bold", x + 18, y + 26, SLIP_W - 36, SLIP_H - 50)


def screen_gate(w, h):
    """A phone's little picture of the gate. What is left magenta, the painter lights."""
    def draw(c):
        E.rect(c, 0, 0, w, h, "#FF00FF")
        gw, gh = w * 0.82, min(h * 0.42, w * 0.5)
        x0, y0 = (w - gw) / 2, h * 0.5 - gh / 2
        for k in range(10):
            E.rect(c, x0 + k * gw / 9 - gw * 0.018, y0, gw * 0.036, gh, E.INK)
        E.rect(c, x0 - gw * 0.02, y0 + gh * 0.08, gw * 1.04, gh * 0.07, E.INK)
        E.rect(c, x0 - gw * 0.02, y0 + gh * 0.86, gw * 1.04, gh * 0.09, E.INK)
        E.rect(c, x0 - gw * 0.04, y0 + gh * 0.42, gw * 1.08, gh * 0.14, E.RIN)
        E.rect(c, 0, y0 + gh * 1.0, w, gh * 0.03, E.INK)
        c.drawCircle(w * 0.12, h * 0.09, w * 0.05 if w < h else h * 0.05, skia.Paint(AntiAlias=True, Color4f=E.col(E.RED)))
    return draw


SCREEN_SHOE_KEY = "#FF0080"     # the painter of the hall gives this her loafers' brown, whatever the lights are doing


def _loafers_icon():
    """Her own loafers, off the picture they stand in: ink stays ink, the rest is the shoe key."""
    im = cv2.imread(str(ROOT / "assets" / "gen" / "cut" / "x01_loafers_cell.png"), cv2.IMREAD_UNCHANGED)[214:848, 297:1238]
    lum = im[..., :3].mean(-1)
    out = np.zeros(im.shape, np.uint8)
    out[..., 3] = (im[..., 3] > 128) * 255
    out[lum < 70, :3] = (0x2A, 0x25, 0x20)
    out[lum >= 70, :3] = (0xFF, 0x00, 0x80)
    return skia.Image.fromarray(out, colorType=skia.ColorType.kRGBA_8888_ColorType)


def screen_cell(w, h):
    """A phone's little photo of her cell: the pair of brown loafers, the cell's frame, and above them her name scribbled out. No shapes that read as a face."""
    def draw(c):
        E.rect(c, 0, 0, w, h, "#FF00FF")
        cw = min(w * 0.86, h * 1.05)
        ch = cw * 0.78
        x0, y0 = (w - cw) / 2, (h - ch) / 2
        t = cw * 0.025
        # the cell, seen as it is: floor, two sides, the shelf above
        for r in ((x0, y0, cw, t), (x0, y0 + ch - t, cw, t), (x0, y0, t, ch), (x0 + cw - t, y0, t, ch)):
            E.rect(c, *r, E.INK)
        # the scribble: strokes of different length, not one bar
        sy, sh = y0 + ch * 0.07, ch * 0.055
        for k, (a, b) in enumerate(((0.08, 0.86), (0.05, 0.93), (0.11, 0.90))):
            E.rect(c, x0 + cw * a, sy + k * sh, cw * (b - a), sh * 1.15, E.INK)
        icon = _loafers_icon()
        iw = cw * 0.82
        ih = iw * icon.height() / icon.width()
        c.drawImageRect(icon, skia.Rect.MakeXYWH(x0 + (cw - iw) / 2, y0 + ch - t - ih - ch * 0.02, iw, ih), skia.SamplingOptions(skia.FilterMode.kLinear))
    return draw


def crowd_textures():
    save("screen_gate_p", 240, 420, screen_gate(240, 420))
    save("screen_gate_l", 420, 240, screen_gate(420, 240))
    save("screen_cell_p", 240, 420, screen_cell(240, 420))
    save("screen_cell_l", 420, 240, screen_cell(420, 240))
    for i in range(6):
        save(f"mag_cover_{i}", COVER_W, COVER_H, mag_cover(i))
    save("mag_back", COVER_W, COVER_H, mag_back)
    save("hall_slips", SLIP_W * SLIP_COLS, SLIP_H * SLIP_ROWS, hall_slips)


def main():
    crowd_textures()
    save("gate_notice", 552, 408, gate_notice)
    save("tape", 1024, 128, tape)
    save("plate_mosaic", 296, 920, mosaic)
    save("plate_school", 296, 920, school_plate)
    save("facade", 4096, 1024, facade)
    save("facade_warm", 4096, 1024, facade_warm)
    save("plates", PLATE_W * PLATE_COLS, PLATE_H * PLATE_ROWS, plates)
    save("plate_black", 512, 180, plate_black, transparent=True)
    save("plate_torn", 512, 180, plate_torn, transparent=True)
    save("hall_floor", 512, 512, hall_floor)
    save("apron", 1024, 1024, apron)
    save("notice_a", 512, 720, notice_a)
    save("notice_b", 512, 720, notice_b)
    for i in range(len(HER_ADS)):
        save(f"ad_her_{i:02d}", AD_W, AD_H, her_ad(i))
    for i in range(6):
        save(f"long_her_{i}", 2048, 512, her_long(i))
    for name, fn in (("onsen", ad_onsen), ("soda", ad_soda), ("english", ad_english), ("condo", ad_condo), ("movie", ad_movie), ("mag", ad_other_mag)):
        save(f"ad_other_{name}", AD_W, AD_H, fn)
    others = [("家族で動物園へ", "春のこども割引 実施中", "#DDE7D6"), ("歯は一生のともだち", "駅前さくら歯科", E.PAPER),
              ("めぐる、この街の図書館", "秋の読書週間", "#F7E7A6")]
    for i, (a, b, bg) in enumerate(others):
        save(f"long_other_{i}", 2048, 512, long_other(a, b, bg))
    print("textures in", OUT)


if __name__ == "__main__":
    main()
