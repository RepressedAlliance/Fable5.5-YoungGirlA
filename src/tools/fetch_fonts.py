"""Fetch the Google Fonts used during production; keep fonts out of Git.

python src/tools/fetch_fonts.py          download missing fonts
python src/tools/fetch_fonts.py --check  check filenames without network or writes
"""
import argparse
import concurrent.futures as cf
import json
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DEST = ROOT / "assets/fonts/ttf"


def download(entry):
    path = DEST / entry["filename"]
    if path.is_file() and path.stat().st_size:
        return f"OK {path.name}"
    with urllib.request.urlopen(entry["url"], timeout=60) as response:
        data = response.read()
    if data[:4] not in (b"\x00\x01\x00\x00", b"OTTO", b"ttcf"):
        raise ValueError(f"Not an OpenType/TrueType font: {entry['url']}")
    path.write_bytes(data)
    return f"FETCH {path.name}"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    entries = json.loads((ROOT / "data/fonts.json").read_text(encoding="utf-8"))
    if args.check:
        missing = [e["filename"] for e in entries if not (DEST / e["filename"]).is_file()]
        for name in missing:
            print(f"MISSING {name}")
        print(f"{len(entries) - len(missing)}/{len(entries)} fonts present")
        return int(bool(missing))
    DEST.mkdir(parents=True, exist_ok=True)
    with cf.ThreadPoolExecutor(max_workers=8) as pool:
        for result in pool.map(download, entries):
            print(result, flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
