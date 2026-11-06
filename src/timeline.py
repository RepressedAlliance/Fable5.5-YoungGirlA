"""Song time, beat grid and lyric timing in one place.

All times are seconds of the song (input/song.mp4). Frame numbers depend on the fps the
caller chooses; nothing here assumes one.
"""
import json
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AUDIO = ROOT / "work" / "analysis" / "audio.json"
LYRICS = ROOT / "work" / "analysis" / "lyrics_timed.json"


@lru_cache(maxsize=None)
def audio():
    return json.loads(AUDIO.read_text())


@lru_cache(maxsize=None)
def lyrics():
    """List of lines: {start, end, text, syl:[{text,t,dur}], chars:[{c,t,syl}]}.

    A small っ belongs to the mora after it (っつ is sung on "tsu"), so it is revealed with
    the next character; a partial line never ends on a dangling っ."""
    L = json.loads(LYRICS.read_text(encoding="utf-8"))
    for ln in L:
        ch = ln["chars"]
        for i in range(len(ch) - 2, -1, -1):
            if ch[i]["c"] in "っッ":
                ch[i]["t"] = max(ch[i]["t"], ch[i + 1]["t"])
    return L


def beat_period():
    return audio()["beat_period"]


def beat_time(n):
    """Time of beat n on the constant grid (n may be fractional)."""
    a = audio()
    return a["beat0"] + n * a["beat_period"]


def beat_index(t):
    a = audio()
    return (t - a["beat0"]) / a["beat_period"]


def bar_time(n):
    """Time of bar line n (bar 0 = first bar line of the song's bar grid)."""
    a = audio()
    return a["beat0"] + (a["bar_phase"] + 4 * n) * a["beat_period"]


def snap_beat(t, div=1):
    """Nearest grid time at 1/div beat resolution."""
    n = round(beat_index(t) * div) / div
    return beat_time(n)


def frame(t, fps):
    return int(round(t * fps))


def lines_between(t0, t1):
    return [ln for ln in lyrics() if ln["end"] > t0 and ln["start"] < t1]


def chars_between(t0, t1):
    out = []
    for i, ln in enumerate(lyrics()):
        for c in ln["chars"]:
            if t0 <= c["t"] < t1:
                out.append({**c, "line": i})
    return out
