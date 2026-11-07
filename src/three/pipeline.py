"""Render a 3D shot: Blender writes data passes, painters turn them into finished PNGs, passes get deleted.

Resumable: frames already painted are skipped, so a crash or a power cut only loses what was in flight.
Usage: pipeline.py c2 [--force-paint]
"""
import atexit
import importlib
import json
import multiprocessing as mp
import os
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
import shutil
import subprocess
import sys
import time
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "src" / "npr"), str(ROOT / "src" / "three")]
BLENDER = (os.environ.get("BLENDER_EXE") or shutil.which("blender")
           or r"C:\Program Files\Blender Foundation\Blender 5.2\blender.exe")
KEEP_EXR = os.environ.get("SHOT_KEEP_EXR") == "1"
LOST_AFTER = 900  # seconds, counted from when a frame is queued, so it allows for a long queue

SHOTS = {
    "c2": ("shot_c2.py", "paint_c2", "shared_c2"),
    "c3": ("shot_c3.py", "paint_c3", "shared_c3"),
    "c4": ("shot_c4.py", "paint_c4", "shared_c4"),
    "gate": ("shot_gate.py", "paint_gate", "shared_gate"),
    "lockers": ("shot_lockers.py", "paint_lockers", "shared_lockers"),
    "train": ("shot_train.py", "paint_train", "shared_train"),
    "outro": ("shot_outro.py", "paint_outro", "shared_outro"),
    "room": ("shot_room.py", "paint_room", "shared_room"),
    "room2": ("shot_room2.py", "paint_room2", "shared_room2"),
}


def paint_one(args):
    shot, exr, png = args
    _, paint_mod, shared_mod = SHOTS[shot]
    cv2.setNumThreads(2)
    P = importlib.import_module(paint_mod)
    S = importlib.import_module(shared_mod)
    ids = json.loads((ROOT / "work" / "render" / f"{shot}_ids.json").read_text())
    n = int(Path(exr).stem[1:])
    t = S.T0 + n / 60.0
    try:
        rgb = P.paint_time(exr, t, ids)
    except Exception as e:
        # an unreadable frame must not stop the whole run: the next pass renders it again
        print(f"FAILED {Path(exr).name}: {e!r}", flush=True)
        os.replace(exr, str(exr) + ".bad")
        return -1
    tmp = str(png) + ".tmp.png"
    cv2.imwrite(tmp, (rgb[..., ::-1] * 255 + 0.5).astype(np.uint8))
    os.replace(tmp, png)
    if KEEP_EXR:
        # the passes stay, so a later change of colour needs only a repaint and not a new render
        keep = ROOT / "work" / "render" / f"{shot}_exr"
        keep.mkdir(parents=True, exist_ok=True)
        os.replace(exr, keep / Path(exr).name)
    else:
        os.remove(exr)
    return n


def main():
    shot = sys.argv[1]
    script, _, shared_mod = SHOTS[shot]
    S = importlib.import_module(shared_mod)
    exr_dir = ROOT / "work" / "render" / shot
    png_dir = ROOT / "work" / "render" / f"{shot}_png"
    exr_dir.mkdir(parents=True, exist_ok=True)
    png_dir.mkdir(parents=True, exist_ok=True)
    # passes left by an earlier run must not get painted into this one
    stale = list(exr_dir.glob("*.exr"))
    if stale:
        keep = ROOT / "work" / "render" / "stale" / f"{shot}_{int(time.time())}"
        keep.mkdir(parents=True, exist_ok=True)
        for f in stale:
            os.replace(f, keep / f.name)
        print(f"moved {len(stale)} old passes to {keep}", flush=True)
    done = {int(p.stem[1:]) for p in png_dir.glob("f*.png")}
    if "--redo-from" in sys.argv:
        # frames from this one onward get rendered again and replace the old pictures
        k = int(sys.argv[sys.argv.index("--redo-from") + 1])
        done = {f for f in done if f < k}
        for p in png_dir.glob("f*.png"):
            if int(p.stem[1:]) >= k:
                p.unlink()   # a redo must not leave pictures of the old version behind
    frames = [f for f in S.frames_all() if f not in done]
    print(f"{shot}: {len(frames)} frames to do, {len(done)} done", flush=True)
    if not frames:
        return
    # Blender skips frames whose exr exists, so hand it the ones without a png by ranges
    # Most of a Blender's frame goes on scene updates and writing the file, not on the GPU, which sat at 25%:
    # two of them share the work and the GPU easily serves both (each holds about 3 GB of its 8 GB).
    env = dict(os.environ)
    n_bl = int(os.environ.get("N_BLENDER", "2")) if len(frames) > 20 else 1
    bls = []
    for k in range(n_bl):
        todo = ROOT / "work" / "render" / f"{shot}_todo{k}.json"
        todo.write_text(json.dumps(frames[k::n_bl]))
        # kept, so that a Blender which stops early can be diagnosed
        blog = open(ROOT / "work" / "render" / f"{shot}_blender{k}.log", "w", encoding="utf-8", errors="replace")
        bls.append(subprocess.Popen([BLENDER, "-b", "--python", str(ROOT / "src" / "three" / script), "--", str(exr_dir), "todo", str(todo)],
                                    stdout=blog, stderr=subprocess.STDOUT, env=env))
    # if this process dies, its own Blenders must not be left behind (a crash loop once left twelve running at once)
    atexit.register(lambda: [b_.kill() for b_ in bls if b_.poll() is None])
    ctx = mp.get_context("spawn")
    pending = set()
    t0 = time.time()
    finished = 0
    # each painter peaks around 3 GB on a frame of this size; three plus Blender hit the memory cap
    # a first pass with two painters; any later pass (with no --redo-from) is a repair pass and uses one
    # Measured 2026-11-05: a painter takes about 6 s a frame, 1.6 GB resident, 2.3 GB committed; Blender on the GPU 1.8 s a
    # frame. Three painters keep up with Blender. c3 stays at two: its town makes Blender much bigger in memory.
    # Re-measured with the beauty pass dropped from memory: see docs/进度.md. The CPU has 24 threads to spare.
    if os.environ.get("PAINT_GPU") == "1":
        # Measured 2026-11-06 next to two Blenders: four GPU painters already outrun them (0.56 s a frame against about 1.25 s).
        # Each holds about 0.75 GB of video memory, so more than that risks Blender's own. room and room2 still colour on the CPU
        # in their own code (only the ink is on the GPU, 0.42 GB each) and need more painters to keep up.
        n_painter = int(os.environ.get("N_PAINTER", "6" if shot in ("room", "room2") else "4"))
    else:
        n_painter = int(os.environ.get("N_PAINTER", "5")) - (1 if shot == "c3" else 0)
    with ctx.Pool(n_painter) as pool:
        results = []
        while True:
            alive = any(b_.poll() is None for b_ in bls)
            for f in sorted(exr_dir.glob("f?????.exr")):
                if f in pending:
                    continue
                pending.add(f)
                results.append((pool.apply_async(paint_one, ((shot, str(f), str(png_dir / (f.stem + ".png"))),)), f, time.time()))
            still = []
            for r, f, started in results:
                if r.ready():
                    r.get()
                    finished += 1
                    if finished % 25 == 0:
                        print(f"{shot} painted {finished}/{len(frames)} {time.time() - t0:.0f}s", flush=True)
                elif time.time() - started > LOST_AFTER:
                    # a Pool never reports a task whose worker died, and would wait for it for ever (it did, 2026-11-06).
                    # Give the frame up: the repair pass renders whatever has no picture.
                    print(f"LOST {f.name}: no result after {LOST_AFTER} s, its worker probably died", flush=True)
                    if f.exists():
                        os.replace(f, str(f) + ".bad")
                else:
                    still.append((r, f, started))
            results = still
            if not alive and not results and not list(exr_dir.glob("f?????.exr")):
                break
            time.sleep(0.4)
    print(f"DONE {shot} painted {finished} frames in {time.time() - t0:.0f}s, blender exit {[b_.returncode for b_ in bls]}", flush=True)


if __name__ == "__main__":
    main()
