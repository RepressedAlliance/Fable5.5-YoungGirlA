"""Fetch reference lyrics for 少女A (text only, used to map the user's romaji ASS to Japanese).

Sources: lrclib.net (retries on 503) and NetEase cloud music. Results go to work/analysis/
and stay out of version control.
"""
import json
import time
import urllib.parse
import urllib.request
from pathlib import Path

OUT = Path(__file__).resolve().parents[2] / "work" / "analysis"
OUT.mkdir(parents=True, exist_ok=True)
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}


def get(url, data=None, headers=None, tries=6):
    h = dict(UA)
    h.update(headers or {})
    for i in range(tries):
        try:
            req = urllib.request.Request(url, data=data, headers=h)
            with urllib.request.urlopen(req, timeout=20) as r:
                return r.read().decode("utf-8")
        except Exception as e:  # noqa: BLE001 - network retries
            print("retry", i, url[:60], e)
            time.sleep(3 + 3 * i)
    return None


def lrclib():
    q = urllib.parse.urlencode({"q": "少女A 椎名もた"})
    s = get("https://lrclib.net/api/search?" + q)
    if not s:
        return
    d = json.loads(s)
    if isinstance(d, list):
        (OUT / "lrclib_search.json").write_text(s, encoding="utf-8")
        for x in d[:20]:
            print("lrclib", x["id"], x["trackName"], "|", x["artistName"], "|", x.get("duration"), bool(x.get("syncedLyrics")))


def netease():
    data = urllib.parse.urlencode({"s": "少女A 椎名もた", "type": 1, "limit": 20}).encode("utf-8")
    s = get("https://music.163.com/api/cloudsearch/pc", data=data,
            headers={"Referer": "https://music.163.com", "Content-Type": "application/x-www-form-urlencoded"})
    if not s:
        return
    d = json.loads(s)
    songs = (d.get("result") or {}).get("songs") or []
    for x in songs:
        print("netease", x["id"], x["name"], "|", "/".join(a["name"] for a in x.get("ar", [])), x.get("dt"))
    for x in songs:
        lyr = get(f"https://music.163.com/api/song/lyric/v1?id={x['id']}&lv=1&yv=1&tv=-1",
                  headers={"Referer": "https://music.163.com"})
        if lyr:
            j = json.loads(lyr)
            text = (j.get("lrc") or {}).get("lyric") or ""
            if "寒い" in text or "さむい" in text:
                (OUT / f"netease_{x['id']}.json").write_text(lyr, encoding="utf-8")
                print("saved lyric for", x["id"], len(text))


if __name__ == "__main__":
    netease()
    lrclib()
