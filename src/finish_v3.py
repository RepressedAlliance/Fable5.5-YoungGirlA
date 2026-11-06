"""Repair any missing 3D frames, check that every frame exists, then render the rest and join the demo."""
import importlib
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "src" / "three")]
PY = sys.executable
os.environ["SHOT_KEEP_EXR"] = "1"
MODS = {"c2": "shared_c2", "c3": "shared_c3", "c4": "shared_c4"}


def missing(shot):
    S = importlib.import_module(MODS[shot])
    d = ROOT / "work" / "render" / f"{shot}_png"
    return [f for f in S.frames_all() if not (d / f"f{f:05d}.png").exists()]


for shot in MODS:
    for attempt in range(4):
        m = missing(shot)
        print(shot, "missing", len(m), flush=True)
        if not m:
            break
        subprocess.run([PY, str(ROOT / "src" / "three" / "pipeline.py"), shot], cwd=ROOT)
    if missing(shot):
        raise SystemExit(f"{shot} still has missing frames: {missing(shot)[:20]}")
subprocess.run([PY, str(ROOT / "src" / "assemble.py"), "render"], cwd=ROOT, check=True)
subprocess.run([PY, str(ROOT / "src" / "assemble.py"), "build"], cwd=ROOT, check=True)
print("ALL DONE", flush=True)
