"""Checks the GPU painter against the CPU painter on real passes and measures it. Nothing here writes to the film's folders.

  paint_gpu_check.py cpu  OUT [frames_per_shot]       CPU pictures of frames across every shot, kept as references in OUT
  paint_gpu_check.py diff OUT                         paints the same frames on the GPU, reports the difference from the references
  paint_gpu_check.py loop SECONDS LOG [shot ...]      paints frames for that long, one line per frame in LOG, flushed (the first-run trial)
  paint_gpu_check.py rate N SECONDS LOG [shot ...]    N painter processes for that long: seconds per frame with them all running

PAINT_GPU decides which painter runs. loop stops early at 87 C on the GPU, 95 C on the board or when the mains goes,
reading Codex-Safe-Workspace/GPU-Load-Test/logs/latest.json from telemetry.py.
"""
import importlib
import json
import multiprocessing as mp
import os
import sys
import time
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "src" / "npr"), str(ROOT / "src" / "three")]
SHOTS = ["c2", "c3", "gate", "lockers", "train", "room", "room2", "outro", "c4"]
LATEST = Path(os.environ.get("GPU_LOAD_LOG", "latest.json"))


def frames_of(shot, count):
    S = importlib.import_module(f"shared_{shot}")
    d = ROOT / "work" / "render" / f"{shot}_exr"
    fs = [n for n in S.frames_all() if (d / f"f{n:05d}.exr").exists()]
    if not fs:
        return []
    return sorted({fs[int((i + 0.5) * len(fs) / count)] for i in range(count)})


def paint(shot, n):
    """As pipeline.paint_one does it, up to the 8-bit picture."""
    P = importlib.import_module(f"paint_{shot}")
    S = importlib.import_module(f"shared_{shot}")
    ids = json.loads((ROOT / "work" / "render" / f"{shot}_ids.json").read_text())
    rgb = P.paint_time(str(ROOT / "work" / "render" / f"{shot}_exr" / f"f{n:05d}.exr"), S.T0 + n / 60.0, ids)
    return (rgb[..., ::-1] * 255 + 0.5).astype(np.uint8)


def references(out, count):
    out.mkdir(parents=True, exist_ok=True)
    for shot in SHOTS:
        for n in frames_of(shot, count):
            f = out / f"{shot}_{n:05d}.png"
            if not f.exists():
                t0 = time.time()
                cv2.imwrite(str(f), paint(shot, n))
                print(shot, n, f"{time.time() - t0:.1f}s", flush=True)


def diff(out):
    import torch
    totals = {}
    for f in sorted(out.glob("*_?????.png")):
        shot, n = f.stem.rsplit("_", 1)
        cpu = cv2.imread(str(f))
        t0 = time.time()
        gpu = paint(shot, int(n))
        dt = time.time() - t0
        d = np.abs(cpu.astype(np.int16) - gpu.astype(np.int16))
        px = d.max(-1)
        line = dict(shot=shot, n=int(n), max=int(d.max()), mean=round(float(d.mean()), 5), over1=int((px > 1).sum()), over2=int((px > 2).sum()),
                    sec=round(dt, 2), vram_gib=round(torch.cuda.max_memory_allocated() / 2 ** 30, 2))
        print(json.dumps(line), flush=True)
        t = totals.setdefault(shot, [0, 0.0, 0, 0, 0])
        t[0] = max(t[0], line["max"])
        t[1] += line["mean"]
        t[2] += line["over2"]
        t[3] += 1
        if line["over2"]:
            cv2.imwrite(str(out / f"diff_{shot}_{n}.png"), np.clip(d.astype(np.int32) * 20, 0, 255).astype(np.uint8))
    for shot, t in totals.items():
        print(f"{shot}: max {t[0]}/255, mean {t[1] / t[3]:.5f}, pixels over 2: {t[2]} in {t[3]} frames", flush=True)


def stop_reason():
    try:
        r = json.loads(LATEST.read_text(encoding="utf-8"))
        if float(r.get("gpu_c") or 0) >= 87 or float(r.get("tz01_c") or 0) >= 95:
            return f"temperature gpu={r.get('gpu_c')} tz={r.get('tz01_c')}"
        if r.get("ac") == "0":
            return "mains unplugged"
    except (OSError, ValueError):
        pass
    return None


def cycle(shots):
    jobs = [(s, n) for s in shots for n in frames_of(s, 12)]
    rng = np.random.default_rng(os.getpid())
    rng.shuffle(jobs)
    return jobs


def loop(seconds, log, shots):
    log = Path(log)
    log.parent.mkdir(parents=True, exist_ok=True)
    with open(log, "a", encoding="utf-8") as f:
        end = time.time() + seconds
        jobs = cycle(shots)
        k = 0
        while time.time() < end:
            why = stop_reason()
            if why:
                f.write(f"STOPPED {why}\n")
                f.flush()
                os.fsync(f.fileno())
                print("STOPPED", why, flush=True)
                return
            shot, n = jobs[k % len(jobs)]
            k += 1
            t0 = time.time()
            paint(shot, n)
            f.write(f"{time.strftime('%H:%M:%S')} {shot} {n} {time.time() - t0:.2f}\n")
            f.flush()
            os.fsync(f.fileno())
    print("trial done", k, "frames", flush=True)


def worker(arg):
    """One painter in a rate test: paints until the stop time, as the pipeline's paint_one does (PNG encode included)."""
    start, end, shots = arg
    cv2.setNumThreads(2)
    jobs = cycle(shots)
    rows = []
    k = 0
    paint(*jobs[0])   # imports and CUDA start: they happen once per painter and are not what is being timed
    time.sleep(max(0.0, start - time.time()))
    while time.time() < end:
        shot, n = jobs[k % len(jobs)]
        k += 1
        t0 = time.time()
        ok, png = cv2.imencode(".png", paint(shot, n))
        rows.append((shot, n, t0, time.time()))
    extra = {}
    if "torch" in sys.modules:
        import torch
        extra = dict(vram_alloc_gib=round(torch.cuda.max_memory_allocated() / 2 ** 30, 2), vram_reserved_gib=round(torch.cuda.max_memory_reserved() / 2 ** 30, 2),
                     torch_alive=True)
    return rows, extra, os.getpid()


def rate(n_proc, seconds, log, shots):
    start = time.time() + 30 + 6 * n_proc   # imports and CUDA take a while; the clock starts with everyone ready
    end = start + seconds
    ctx = mp.get_context("spawn")
    with ctx.Pool(n_proc) as pool:
        results = pool.map(worker, [(start, end, shots)] * n_proc, chunksize=1)
    done = sorted(r for rows, _, _ in results for r in rows)
    whole = [r for r in done if r[3] <= end]
    span = max(r[3] for r in done) - start
    per_shot = {}
    for s, _, a, b in done:
        per_shot.setdefault(s, []).append(b - a)
    line = dict(n=n_proc, frames=len(done), span=round(span, 1), sec_per_frame=round(span / max(len(done), 1), 3), whole_frames=len(whole),
                mean_frame_s=round(float(np.mean([b - a for _, _, a, b in done])), 2),
                per_shot={k: round(float(np.mean(v)), 2) for k, v in sorted(per_shot.items())}, gpu_on=os.environ.get("PAINT_GPU") == "1",
                vram=[e for _, e, _ in results])
    print(json.dumps(line), flush=True)
    with open(log, "a", encoding="utf-8") as f:
        f.write(json.dumps(line) + "\n")


if __name__ == "__main__":
    cv2.setNumThreads(2)
    mode = sys.argv[1]
    if mode == "cpu":
        references(Path(sys.argv[2]), int(sys.argv[3]) if len(sys.argv) > 3 else 4)
    elif mode == "diff":
        diff(Path(sys.argv[2]))
    elif mode == "loop":
        loop(float(sys.argv[2]), sys.argv[3], sys.argv[4:] or SHOTS[:-1])
    elif mode == "rate":
        rate(int(sys.argv[2]), float(sys.argv[3]), sys.argv[4], sys.argv[5:] or SHOTS[:-1])
