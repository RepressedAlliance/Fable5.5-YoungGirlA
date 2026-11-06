"""Map the user's romaji karaoke ASS (timing authority) onto the Japanese lyric text.

Every Japanese character gets the start time of the ASS syllable that sings it.
Method: per-character kana readings -> romaji letter stream; ASS syllables -> letter
stream; one global Needleman-Wunsch alignment of the two streams; each character takes
the earliest syllable aligned to any of its letters. Punctuation rides on a neighbour.

Output: work/analysis/lyrics_timed.json (not for version control: contains lyric text).
"""
import json
import re
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
ASS = ROOT / "input" / "lyrics.ass"
JA = ROOT / "work" / "analysis" / "lyrics_ja.txt"
OUT = ROOT / "work" / "analysis" / "lyrics_timed.json"

# Word-level readings first (longest match), then single kanji.
WORDS = {
    "時時々": ["とき", "どき", "どき"],
    "頼り切り": ["た", "より", "ぎ", "り"],
    "言葉": ["こと", "ば"],
    "言い": ["い", "い"],
    "愛憎": ["あい", "ぞう"],
    "憎い": ["にく", "い"],
    "子供": ["こ", "ども"],
    "何番目": ["なん", "ばん", "め"],
    "合言葉": ["あい", "こと", "ば"],
    "微笑む": ["ほほ", "え", "む"],
    "躓いた": ["つまず", "い", "た"],
    "諦めた": ["あきら", "め", "た"],
}
KANJI = dict(
    僕="ぼく", 命="いのち", 誰="だれ", 公="こう", 平="へい", 裁="さば", 暗="くら", 空="そら",
    鬱="うつ", 連="つ", 雨="あめ", 総="そう", 計="けい", 朽="く", 飲="の", 込="こ", 君="きみ",
    簡="かん", 単="たん", 書="か", 曖="あい", 昧="まい", 伝="つた", 信="しん", 捨="す", 夢="ゆめ",
    間="ま", 違="ちが", 時="とき", 寒="さむ", 寄="よ", 声="こえ", 遠="とお", 傷="きず", 契="ちぎ",
    集="あつ", 持="も", 日="ひ", 苦="くる", 花="はな", 追="お", 早="はや", 残="のこ", 思="おも",
    許="ゆる", 怖="こわ", 見="み", 近="ちか", 繰="く", 返="かえ", 願="ねが", 切="き",
)

EXTRA_AFTER = ["間違えたから", "諦めたから？"]

KANA = {}
_rows = {
    "": "a i u e o", "k": "ka ki ku ke ko", "s": "sa shi su se so", "t": "ta chi tsu te to",
    "n": "na ni nu ne no", "h": "ha hi fu he ho", "m": "ma mi mu me mo", "y": "ya - yu - yo",
    "r": "ra ri ru re ro", "w": "wa - - - wo", "g": "ga gi gu ge go", "z": "za ji zu ze zo",
    "d": "da ji zu de do", "b": "ba bi bu be bo", "p": "pa pi pu pe po",
}
_hira = {
    "": "あいうえお", "k": "かきくけこ", "s": "さしすせそ", "t": "たちつてと", "n": "なにぬねの",
    "h": "はひふへほ", "m": "まみむめも", "y": "や-ゆ-よ", "r": "らりるれろ", "w": "わ---を",
    "g": "がぎぐげご", "z": "ざじずぜぞ", "d": "だぢづでど", "b": "ばびぶべぼ", "p": "ぱぴぷぺぽ",
}
for c, ks in _hira.items():
    for k, r in zip(ks, _rows[c].split()):
        if k != "-":
            KANA[k] = r
            KANA[chr(ord(k) + 0x60)] = r  # katakana
KANA.update({"ん": "n", "ン": "n", "っ": "", "ッ": "", "ー": "", "ゃ": "ya", "ゅ": "yu", "ょ": "yo",
             "ぁ": "a", "ぃ": "i", "ぅ": "u", "ぇ": "e", "ぉ": "o"})
SMALL_Y = {"ゃ": "a", "ゅ": "u", "ょ": "o"}


def kana_to_romaji(s):
    out = []
    for i, ch in enumerate(s):
        if ch in SMALL_Y and out:
            prev = out[-1]
            if prev.endswith("i") and len(prev) > 1:
                base = prev[:-1]
                out[-1] = base + ("" if base in ("sh", "ch", "j") else "y") + SMALL_Y[ch]
                continue
        out.append(KANA.get(ch, ""))
    return "".join(out)


def norm(s):
    s = re.sub(r"[^a-z]", "", s.lower())
    s = re.sub(r"([bcdfghjkmprstwz])\1", r"\1", s)  # sokuon doubling
    s = s.replace("tch", "ch")
    return s


def char_readings(text):
    """Return [(char, romaji)] for every character of `text`."""
    out, i = [], 0
    keys = sorted(WORDS, key=len, reverse=True)
    while i < len(text):
        for w in keys:
            if text.startswith(w, i):
                for ch, rd in zip(w, WORDS[w]):
                    out.append((ch, kana_to_romaji(rd)))
                i += len(w)
                break
        else:
            ch = text[i]
            if ch in KANJI:
                out.append((ch, kana_to_romaji(KANJI[ch])))
            elif ch == "々" and out:
                out.append((ch, out[-1][1]))
            else:
                out.append((ch, kana_to_romaji(ch)))
            i += 1
    return out


def parse_ass(path):
    ev = []
    for line in path.read_text(encoding="utf-8-sig").splitlines():
        if not line.startswith("Comment:") or ",karaoke," not in line:
            continue
        parts = line.split(",", 9)
        start, end, body = parts[1], parts[2], parts[9]

        def t(x):
            h, m, s = x.split(":")
            return int(h) * 3600 + int(m) * 60 + float(s)

        t0 = t(start)
        syl, cur = [], t0
        for k, txt in re.findall(r"\{\\k(\d+)\}([^{]*)", body):
            d = int(k) / 100.0
            syl.append({"text": txt, "t": round(cur, 3), "dur": d})
            cur += d
        ev.append({"start": t0, "end": t(end), "syl": syl})
    return ev


def align(a, b):
    """Global alignment of strings a, b. Returns for each index of a the matched index of b or -1."""
    n, m = len(a), len(b)
    M, X, G = 2, -1, -1
    score = np.zeros((n + 1, m + 1), np.int32)
    score[:, 0] = np.arange(n + 1) * G
    score[0, :] = np.arange(m + 1) * G
    bb = np.frombuffer(b.encode(), np.uint8)
    for i in range(1, n + 1):
        sub = np.where(bb == ord(a[i - 1]), M, X)
        diag = score[i - 1, :-1] + sub
        up = score[i - 1, 1:] + G
        row = np.maximum(diag, up)
        # left moves need a running pass
        r = np.empty(m + 1, np.int32)
        r[0] = score[i, 0]
        for j in range(1, m + 1):
            v = row[j - 1]
            lft = r[j - 1] + G
            r[j] = v if v >= lft else lft
        score[i] = r
    i, j, match = n, m, [-1] * n
    while i > 0 and j > 0:
        s = score[i, j]
        if s == score[i - 1, j - 1] + (M if a[i - 1] == b[j - 1] else X):
            if a[i - 1] == b[j - 1]:
                match[i - 1] = j - 1
            i, j = i - 1, j - 1
        elif s == score[i - 1, j] + G:
            i -= 1
        else:
            j -= 1
    return match


def main():
    ev = parse_ass(ASS)
    # ASS letter stream with owner syllable
    b, b_owner = [], []
    for ei, e in enumerate(ev):
        for si, s in enumerate(e["syl"]):
            for ch in norm(s["text"]):
                b.append(ch)
                b_owner.append((ei, si))
    # Japanese stream
    ja = JA.read_text(encoding="utf-8")
    # Sung but missing from the lyric sheet (the ASS has them): "pa pa" after these phrases.
    for anchor in EXTRA_AFTER:
        ja = ja.replace(anchor, anchor + " パッパ", 1)
    chars = char_readings(ja)
    a, a_owner = [], []
    for ci, (ch, rd) in enumerate(chars):
        for c in norm(rd):
            a.append(c)
            a_owner.append(ci)
    match = align("".join(a), "".join(b))
    first = {}
    for k, j in enumerate(match):
        if j >= 0:
            ci = a_owner[k]
            first.setdefault(ci, b_owner[j])
    # unmatched letters / punctuation: attach to neighbour
    owner = [None] * len(chars)
    for ci in range(len(chars)):
        owner[ci] = first.get(ci)
    for ci, (ch, rd) in enumerate(chars):
        if owner[ci] is None and ch in "「（":
            nxt = next((owner[k] for k in range(ci + 1, len(chars)) if owner[k]), None)
            owner[ci] = nxt
    for ci in range(len(chars)):
        if owner[ci] is None and chars[ci][0] not in "\n ":
            prv = next((owner[k] for k in range(ci - 1, -1, -1) if owner[k]), None)
            owner[ci] = prv
    # group characters by ASS event
    out = []
    for ei, e in enumerate(ev):
        out.append({"start": e["start"], "end": e["end"], "syl": e["syl"], "chars": []})
    unmatched_letters = sum(1 for j in match if j < 0)
    for ci, (ch, rd) in enumerate(chars):
        if ch in "\n" or owner[ci] is None:
            continue
        ei, si = owner[ci]
        out[ei]["chars"].append({"c": ch, "t": ev[ei]["syl"][si]["t"], "syl": si})
    matched_b = set(j for j in match if j >= 0)
    syl_hit = {}
    for j, own in enumerate(b_owner):
        syl_hit.setdefault(own, False)
        if j in matched_b:
            syl_hit[own] = True
    for ei, e in enumerate(out):
        e["text"] = "".join(c["c"] for c in e["chars"]).strip()
        # syllables with no aligned Japanese letter (text/ASS mismatch)
        e["unclaimed"] = [s["text"] for si, s in enumerate(e["syl"]) if not syl_hit.get((ei, si), True)]
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    bad = 0
    for i, e in enumerate(out):
        flag = ""
        if e["unclaimed"]:
            flag = "  UNCLAIMED " + " ".join(e["unclaimed"])
            bad += 1
        print(f"{i:2d} {e['start']:7.2f} {e['text']}{flag}")
    print("unmatched japanese letters:", unmatched_letters, "events with unclaimed syllables:", bad)


if __name__ == "__main__":
    sys.exit(main())
