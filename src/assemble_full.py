"""The whole film: every section by the frame table in docs/制作约定.md, one continuous song underneath.

usage: assemble_full.py render [names...]   renders sections to work/full/<name>.mp4 (existing ones are kept unless named)
       assemble_full.py build               joins them with the song into out/少女A_full.mp4
       assemble_full.py check               prints which sections exist
"""
import importlib
import multiprocessing as mp
import os
import subprocess
import sys
import time
from collections import deque
from pathlib import Path

# Each worker is single-threaded: without this, OpenBLAS commits a buffer per thread, about 0.7 GB per worker on 24 threads
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("OMP_NUM_THREADS", "1")

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "src" / "clips"), str(ROOT / "src" / "art"), str(ROOT / "src" / "three"), str(ROOT / "src" / "npr")]
import engine as E  # noqa: E402

TABLE = [
    ("s00", "c1", "Opening", 0, 315, 8), ("s01b", "s01b", "MediaMachine", 315, 681, 16),
    ("s02a", "s02a", "Gate", 681, 902, 16), ("s02b", "s02b", "Lockers", 902, 1123, 16), ("s02c", "s02c", "Train", 1123, 1344, 16),
    ("s02d", "s02d", "Drafts", 1344, 1566, 16), ("s03", "s03", "Digging", 1566, 1996, 16), ("s04a", "s04a", "PaperFall", 1996, 2079, 16),
    ("s04", "c2", "Samui", 2079, 2439, 16), ("s05", "c3", "Tooi", 2439, 2880, 16), ("s06", "s06", "Ranking", 2880, 3116, 16),
    ("s07", "c4", "Rin14", 3116, 3395, 16), ("s07x", "s07x", "Stickers", 3395, 3989, 16), ("s08", "s08", "Fast", 3989, 4435, 16),
    ("s09", "c5", "Hate", 4435, 4930, 16), ("s10", "s10", "Room", 4930, 5376, 16), ("s11a", "s11a", "Room2", 5376, 5597, 6),
    ("s11b", "s11b", "Wall", 5597, 5818, 16), ("s12", "c6", "OpenEye", 5818, 6180, 8), ("s13a", "s13a", "Outro", 6180, 6660, 16),
    ("s13b", "s13b", "Form", 6660, 7149, 16),
]
TOTAL = 7265
WORK = ROOT / "work" / "full"
_clip = None


def _init(module, cls):
    global _clip
    os.environ.setdefault("OMP_NUM_THREADS", "1")
    import cv2
    cv2.setNumThreads(1)
    m = importlib.import_module(module)
    _clip = getattr(m, cls)()
    _clip.setup()


def _frame(f):
    rgb = _clip.frame_rgb(f / 30)
    return f, (rgb * 255 + 0.5).astype(np.uint8).tobytes()


def encoder(path):
    cmd = ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{E.W}x{E.H}", "-r", "30",
           "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "12", "-threads", "4", "-pix_fmt", "yuv420p", "-color_primaries", "bt709",
           "-color_trc", "bt709", "-colorspace", "bt709", "-vf", "scale=out_color_matrix=bt709:out_range=tv", str(path)]
    return subprocess.Popen(cmd, stdin=subprocess.PIPE)


def render(name, module, cls, f0, f1, workers):
    out = WORK / f"{name}.mp4"
    tmp = WORK / f"{name}.tmp.mp4"
    ff = encoder(tmp)
    t0 = time.time()
    frames = list(range(f0, f1))
    ctx = mp.get_context("spawn")
    # No batches: a worker takes the next frame the moment it is free, and frames are written in order. Only a bounded
    # number are in flight, so finished frames cannot pile up in memory. Workers are rarely replaced: setup is expensive.
    pending = deque()
    done = [0]

    def write_one():
        f, data = pending.popleft().get()
        ff.stdin.write(data)
        if done[0] % 60 == 0:
            print(f"{name} {done[0]}/{len(frames)} {time.time() - t0:.0f}s", flush=True)
        done[0] += 1

    with ctx.Pool(workers, initializer=_init, initargs=(module, cls), maxtasksperchild=400) as pool:
        for f in frames:
            while len(pending) >= workers * 3:
                write_one()
            pending.append(pool.apply_async(_frame, (f,)))
        while pending:
            write_one()
    ff.stdin.close()
    ff.wait()
    os.replace(tmp, out)
    print(f"DONE {name} {len(frames)} frames {time.time() - t0:.0f}s", flush=True)


def build():
    tail = WORK / "black.mp4"
    ff = encoder(tail)
    black = bytes(E.W * E.H * 3)
    for _ in range(TOTAL - TABLE[-1][4]):
        ff.stdin.write(black)
    ff.stdin.close()
    ff.wait()
    lst = WORK / "list.txt"
    lines = [f"file '{(WORK / (row[0] + '.mp4')).as_posix()}'" for row in TABLE] + [f"file '{tail.as_posix()}'"]
    lst.write_text("\n".join(lines) + "\n", encoding="utf-8")
    joined = WORK / "joined.mp4"
    subprocess.run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", str(lst), "-c", "copy", str(joined)], check=True)
    master = ROOT / "out" / "少女A_full.mp4"
    subprocess.run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", str(joined), "-i", str(ROOT / "input" / "song.mp4"),
                    # the sections are already high-quality x264: joined as they are, for review. Compress only for delivery.
                    "-map", "0:v", "-map", "1:a", "-c:v", "copy",
                    "-c:a", "aac", "-b:a", "256k", "-movflags", "+faststart", "-shortest", str(master)], check=True)
    print("DONE", master, flush=True)


if __name__ == "__main__":
    WORK.mkdir(parents=True, exist_ok=True)
    cmd = sys.argv[1]
    if cmd == "render":
        names = sys.argv[2:]
        for row in TABLE:
            if row[0] in names or (not names and not (WORK / f"{row[0]}.mp4").exists()):
                render(*row)
        print("RENDER DONE", flush=True)
    elif cmd == "build":
        build()
    else:
        for row in TABLE:
            print(row[0], (WORK / f"{row[0]}.mp4").exists(), (ROOT / "src" / "clips" / f"{row[1]}.py").exists())
