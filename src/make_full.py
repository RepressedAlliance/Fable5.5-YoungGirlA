"""Everything for the whole film under one heavy job: 3D shots on the GPU, repair of any missing frame, all sections, the join.
Resumable: run it again and it picks up where it stopped. To redo a shot, remove its name from work/full/redo_done.txt;
to redo a section, delete work/full/<section>.mp4. The GPU is logged to work/render/gpu_log.csv by src/tools/gpu_watch.py."""
import importlib
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "src" / "three")]
PY = sys.executable
os.environ["SHOT_KEEP_EXR"] = "1"
os.environ["KIT_GPU"] = "1"
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")  # without it every worker commits a buffer per thread, about 0.7 GB
os.environ.setdefault("PAINT_GPU", "1")   # painters colour on the GPU; PAINT_GPU=0 keeps them on the CPU
SHOTS = {"c2": "shared_c2", "c3": "shared_c3", "gate": "shared_gate", "lockers": "shared_lockers", "train": "shared_train",
         "room": "shared_room", "room2": "shared_room2", "outro": "shared_outro", "c4": "shared_c4"}
PIPE = str(ROOT / "src" / "three" / "pipeline.py")
FLAG = ROOT / "work" / "full" / "redo_done.txt"
FLAG.parent.mkdir(parents=True, exist_ok=True)
watch = subprocess.Popen([PY, str(ROOT / "src" / "tools" / "gpu_watch.py"), str(ROOT / "work" / "render" / "gpu_log.csv")])


def missing(shot):
    S = importlib.import_module(SHOTS[shot])
    d = ROOT / "work" / "render" / f"{shot}_png"
    return [f for f in S.frames_all() if not (d / f"f{f:05d}.png").exists()]


try:
    done = set(FLAG.read_text().split()) if FLAG.exists() else set()
    for shot in SHOTS:
        if shot not in done:
            print("START", shot, flush=True)
            subprocess.run([PY, PIPE, shot, "--redo-from", "0"], cwd=ROOT)
            done.add(shot)
            FLAG.write_text(" ".join(sorted(done)))
        for attempt in range(5):
            m = missing(shot)
            print(shot, "missing", len(m), flush=True)
            if not m:
                break
            subprocess.run([PY, PIPE, shot], cwd=ROOT)
        if missing(shot):
            raise SystemExit(f"{shot} still has missing frames: {missing(shot)[:20]}")
finally:
    watch.terminate()
subprocess.run([PY, str(ROOT / "src" / "assemble_full.py"), "render"], cwd=ROOT, check=True)
subprocess.run([PY, str(ROOT / "src" / "assemble_full.py"), "build"], cwd=ROOT, check=True)
print("FULL DONE", flush=True)
