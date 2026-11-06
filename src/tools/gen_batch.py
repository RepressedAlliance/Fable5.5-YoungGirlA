"""Generate character and component images from work/gen/prompts.py entries, a few at a time.

Usage: python src/tools/gen_batch.py ID [ID ...] [--force] [--jobs 3]
Each image goes to assets/gen/raw/<ID>.png (or --out DIR). Existing files are skipped unless --force.
A numbered take is kept when an image is regenerated (<ID>.t2.png ...), so nothing is overwritten.
"""
import argparse
import concurrent.futures as cf
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "work" / "gen"))
import prompts as P  # noqa: E402

OUT = ROOT / "assets" / "gen" / "raw"


def out_path(aid, force):
    base = OUT / f"{aid}.png"
    if not base.exists() or not force:
        return base
    n = 2
    while (OUT / f"{aid}.t{n}.png").exists():
        n += 1
    return OUT / f"{aid}.t{n}.png"


def gen(aid, force):
    out = out_path(aid, force)
    if out.exists():
        return f"SKIP {aid}"
    refs = [ROOT / r for r in P.refs(aid)]   # the sheet always goes along when she is drawn
    with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False, encoding="utf-8") as f:
        f.write(P.build(aid))
        pf = f.name
    cmd = [sys.executable, str(ROOT / "src" / "tools" / "codex_gen.py"), str(out), pf]
    for r in refs:
        cmd += ["--ref", str(r)]
    p = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    Path(pf).unlink(missing_ok=True)
    return f"{aid}: {p.stdout.strip()[:160]} {p.stderr.strip()[-160:]}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("ids", nargs="+")
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--jobs", type=int, default=3)
    ap.add_argument("--out", default=None, help="write here instead of assets/gen/raw, so a running render never sees a half-new set")
    a = ap.parse_args()
    global OUT
    if a.out:
        OUT = Path(a.out).resolve()
    OUT.mkdir(parents=True, exist_ok=True)
    ids = list(P.ASSETS) if a.ids == ["all"] else a.ids
    with cf.ThreadPoolExecutor(a.jobs) as ex:
        for r in ex.map(lambda i: gen(i, a.force), ids):
            print(r, flush=True)


if __name__ == "__main__":
    main()
