"""Finale key art, drawn whole the way the film's good pictures are, not assembled. 8 takes at once."""
import concurrent.futures as cf
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "work" / "gen"))
import prompts as P  # noqa: E402

D = ROOT / "work" / "eye" / "key6"
BASE = " ".join([
    P.IDENTITY, P.DRAW, P.LARGE, P.SHEET_RULE,
    "Attached Image 2 is the same girl already drawn the way this picture must be drawn: the same slim face shape, small quiet features, line, colours and "
    "elegant proportions. Match its face and its drawing exactly.",
    "Picture: a head and shoulders portrait of her, the same framing as Attached Image 2: head, whole bow, charcoal scarf wrapped around her neck in a few clear folds, "
    "navy sailor collar with one thin white line and the yellow neckerchief. The whole bow is inside the picture with a margin above it.",
    "Her eyes look straight at the viewer, both looking the same way, irises centred. They have the same shape and size as on the model sheet, with the same simple upper lash line. "
    "They have light in them now, drawn in the same flat way: a flat teal #218EA3 iris, a darker teal hard-edged shape across its top third, a small dark pupil, one single crisp white "
    "hard-edged highlight near the top on the viewer's left, and a slightly lighter teal hard-edged crescent at the bottom of the iris. No gloss, no gradient, no rings, no sparkle, no extra lashes.",
])
NEVER = P.NEVER + " " + P.KEY
TAKES = {
    "a": "Her head faces us straight on, level. A very small gentle closed-mouth smile, only one short curved line. A light wind from the viewer's left: the hair ends on the right lift a little in a few bold clumps, the scarf end lifts to the right.",
    "b": "Her head is turned very slightly to the viewer's right and tilted a few degrees, still looking at us. A very small gentle closed-mouth smile, only one short curved line. A wind from the viewer's left: the hair on the right side blows out in a few bold simple clumps, the bow's loops flex, the scarf end flies to the right.",
    "c": "Her chin is lifted very slightly, her head faces us. A very small gentle closed-mouth smile, only one short curved line. A strong wind from the viewer's left: all her hair ends blow to the right in a few bold simple clumps, keeping one strong silhouette, the scarf end flies to the right.",
    "d": "Her head is tilted a few degrees towards the viewer's left, facing us. A very small gentle closed-mouth smile, only one short curved line, like someone who has just decided something. A light wind from the viewer's left moves the hair ends on the right and the scarf end.",
}


def one(job):
    key, n = job
    out = D / f"cand_{key}{n}.png"
    if out.exists():
        return f"skip {out.name}"
    pf = D / f"p_{key}{n}.txt"
    pf.write_text(" ".join([BASE, TAKES[key], NEVER]), encoding="utf-8")
    cmd = [sys.executable, str(ROOT / "src" / "tools" / "codex_gen.py"), str(out), str(pf),
           "--ref", str(ROOT / P.SHEET), "--ref", str(ROOT / "assets" / "gen" / "cut" / "p01_bust_front.png")]
    r = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, encoding="utf-8", errors="replace")
    return f"{out.name} {'ok' if out.exists() else 'FAILED ' + (r.stderr or r.stdout)[-300:]}"


if __name__ == "__main__":
    jobs = [(k, n) for k in TAKES for n in (1, 2)]
    with cf.ThreadPoolExecutor(8) as ex:
        for line in ex.map(one, jobs):
            print(line, flush=True)
    print("ALL DONE", flush=True)
