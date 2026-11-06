"""Repaint the 3D shots from their kept passes, render all six clips, join the demo."""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PY = sys.executable
for shot in ("c2", "c3"):
    subprocess.run([PY, str(ROOT / "src" / "three" / "repaint.py"), shot], cwd=ROOT, check=True)
subprocess.run([PY, str(ROOT / "src" / "assemble.py"), "render"], cwd=ROOT, check=True)
subprocess.run([PY, str(ROOT / "src" / "assemble.py"), "build"], cwd=ROOT, check=True)
print("ALL DONE", flush=True)
