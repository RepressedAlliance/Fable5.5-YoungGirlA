"""Clip 4 painter: the wall takes a hard shadow from each paper figure, and a clean ink line where it matters."""
import json
import sys
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "src" / "npr"), str(ROOT / "src" / "three")]
import comp  # noqa: E402
import engine as E  # noqa: E402
import shared_c4 as S  # noqa: E402


def paint_time(exr, t, ids):
    p = comp.read_exr(exr)
    # no scene ink here: the frames are printed on the wall and each paper figure has its own outline
    look = comp.Look(shadow_tint=(0.56, 0.54, 0.62), line_alpha=0.0, light_threshold=0.05)
    rgba = comp.paint(p, look, ss=S.SS)
    return rgba[..., :3]


if __name__ == "__main__":
    ids = json.loads((ROOT / "work" / "render" / "c4_ids.json").read_text())
    d = Path(sys.argv[1])
    out = ROOT / "work" / "qc" / "c4"
    out.mkdir(parents=True, exist_ok=True)
    for f in sorted(d.glob("t*.exr")):
        t = float(f.stem[1:])
        rgb = E.paper_grain(paint_time(f, t, ids), 0.010)
        cv2.imwrite(str(out / f"{f.stem}.png"), (rgb[..., ::-1] * 255 + 0.5).astype(np.uint8))
        print(f.stem, flush=True)
