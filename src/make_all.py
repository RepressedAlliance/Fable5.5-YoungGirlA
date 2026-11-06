"""Clip 4's 3D, then all six clips, then the joined demo. Everything runs under one heavy job."""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PY = sys.executable


def run(*a):
    print("STEP", a, flush=True)
    subprocess.run([PY, *map(str, a)], cwd=ROOT, check=True)


clips = [a for a in sys.argv[1:] if not a.startswith("--")]
if clips or "--build-only" in sys.argv:
    if clips:
        run(ROOT / "src" / "assemble.py", "render", *clips)
else:
    run(ROOT / "src" / "three" / "run_chain.py", "c2", "c3", "c4")
    run(ROOT / "src" / "finish_v3.py")
    print("MAKE ALL DONE", flush=True)
    sys.exit(0)
run(ROOT / "src" / "assemble.py", "build")
print("ALL DONE", flush=True)
