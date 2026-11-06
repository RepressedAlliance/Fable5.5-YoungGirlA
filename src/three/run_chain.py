"""Render the three 3D shots one after another under one heavy job."""
import os
import subprocess
import sys
from pathlib import Path

os.environ["SHOT_KEEP_EXR"] = "1"

ROOT = Path(__file__).resolve().parents[2]
PY = sys.executable
PIPE = str(ROOT / "src" / "three" / "pipeline.py")
steps = [["c2", "--redo-from", "0"], ["c3", "--redo-from", "0"], ["c4", "--redo-from", "0"]]
if len(sys.argv) > 1:
    steps = [[s, "--redo-from", "0"] for s in sys.argv[1:]]
for s in steps:
    print("START", s, flush=True)
    r = subprocess.run([PY, PIPE, *s], cwd=ROOT)
    print("END", s, r.returncode, flush=True)
    # a second pass picks up any frame that failed
    r = subprocess.run([PY, PIPE, s[0]], cwd=ROOT)
    print("RETRY PASS", s[0], r.returncode, flush=True)
print("CHAIN DONE", flush=True)
