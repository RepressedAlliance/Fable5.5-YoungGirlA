"""Repaint a shot from its kept passes, without rendering it again. usage: repaint.py c3"""
import importlib
import json
import multiprocessing as mp
import os
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
import sys
import time
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "src" / "npr"), str(ROOT / "src" / "three")]
MODS = {"c2": ("paint_c2", "shared_c2"), "c3": ("paint_c3", "shared_c3"), "c4": ("paint_c4", "shared_c4")}


def one(args):
    shot, exr = args
    cv2.setNumThreads(2)
    P = importlib.import_module(MODS[shot][0])
    S = importlib.import_module(MODS[shot][1])
    ids = json.loads((ROOT / "work" / "render" / f"{shot}_ids.json").read_text())
    n = int(Path(exr).stem[1:])
    rgb = P.paint_time(exr, S.T0 + n / 60.0, ids)
    png = ROOT / "work" / "render" / f"{shot}_png" / (Path(exr).stem + ".png")
    tmp = str(png) + ".tmp.png"
    cv2.imwrite(tmp, (rgb[..., ::-1] * 255 + 0.5).astype(np.uint8))
    os.replace(tmp, png)
    return n


if __name__ == "__main__":
    shot = sys.argv[1]
    # only the film's own frames: passes kept from earlier 60 fps versions are stale
    S = importlib.import_module(MODS[shot][1])
    d = ROOT / "work" / "render" / f"{shot}_exr"
    fs = [str(d / f"f{n:05d}.exr") for n in S.frames_all() if (d / f"f{n:05d}.exr").exists()]
    print(shot, "frames", len(fs), "of", len(S.frames_all()), flush=True)
    t0 = time.time()
    # With no Blender beside them six GPU painters are the fastest (measured 2026-11-06: 0.51 s a frame; eight were slower, 0.66 s).
    with mp.get_context("spawn").Pool(6 if os.environ.get("PAINT_GPU") == "1" else 2) as pool:
        for k, _ in enumerate(pool.imap_unordered(one, [(shot, f) for f in fs])):
            if k % 50 == 0:
                print(shot, k, len(fs), f"{time.time() - t0:.0f}s", flush=True)
    print("REPAINTED", shot, len(fs), flush=True)
