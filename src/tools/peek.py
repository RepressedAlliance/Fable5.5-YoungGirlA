"""Render single frames of a section for review: peek.py <module> <Class> <t> [t ...]  ->  work/qc/fix/<module>_<t>.png"""
import importlib
import os
import sys
from pathlib import Path

os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "src" / "clips"), str(ROOT / "src" / "art"), str(ROOT / "src" / "three"), str(ROOT / "src" / "npr")]
import cv2  # noqa: E402
import numpy as np  # noqa: E402

mod, cls = sys.argv[1], sys.argv[2]
clip = getattr(importlib.import_module(mod), cls)()
clip.setup()
out = ROOT / "work" / "qc" / "fix"
out.mkdir(parents=True, exist_ok=True)
for a in sys.argv[3:]:
    t = float(a)
    rgb = clip.frame_rgb(t)
    cv2.imwrite(str(out / f"{mod}_{a}.png"), (np.clip(rgb, 0, 1)[..., ::-1] * 255 + 0.5).astype(np.uint8))
    print("wrote", a, flush=True)
