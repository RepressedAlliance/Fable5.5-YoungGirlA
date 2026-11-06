"""Render the 2D passes of each clip and put the six together with the song's own audio.

usage: assemble.py render c1 c5 ...   renders those clips to work/clips/<name>.mp4
       assemble.py build              joins all six into out/ with the matching audio
"""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "src" / "clips"), str(ROOT / "src" / "art"), str(ROOT / "src" / "three")]
import engine as E  # noqa: E402

CLIPS = [("c1", "Opening"), ("c2", "Samui"), ("c3", "Tooi"), ("c4", "Rin14"), ("c5", "Hate"), ("c6", "OpenEye")]
GAP = 0.20


def run(cmd):
    print(" ".join(map(str, cmd))[:200], flush=True)
    subprocess.run(list(map(str, cmd)), check=True)


def build():
    import importlib
    work = ROOT / "work" / "clips"
    out = ROOT / "out"
    out.mkdir(exist_ok=True)
    parts = []
    for i, (mod, cls) in enumerate(CLIPS):
        c = getattr(importlib.import_module(mod), cls)
        v = work / f"{mod}.mp4"
        n = int(round((c.t1 - c.t0) * E.FPS))
        dur = n / E.FPS
        seg = work / f"{mod}_av.mp4"
        fo = 0.02 if i < len(CLIPS) - 1 else 0.18
        run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", v, "-ss", f"{c.t0:.3f}", "-t", f"{dur:.3f}",
             "-i", ROOT / "input" / "song.mp4", "-map", "0:v", "-map", "1:a", "-c:v", "copy",
             "-af", f"afade=t=in:st=0:d=0.012,afade=t=out:st={dur - fo:.3f}:d={fo}", "-c:a", "aac", "-b:a", "320k", "-ar", "44100", "-shortest", seg])
        parts.append(seg)
    black = work / "gap.mp4"
    if GAP > 0:
        run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-f", "lavfi", "-i", f"color=c=black:s={E.W}x{E.H}:r={E.FPS}:d={GAP}",
             "-f", "lavfi", "-i", f"anullsrc=r=44100:cl=stereo:d={GAP}", "-shortest", "-c:v", "libx264", "-crf", "12", "-pix_fmt", "yuv420p",
             "-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709", "-c:a", "aac", "-b:a", "320k", black])
    lst = work / "list.txt"
    lines = []
    for i, p in enumerate(parts):
        lines.append(f"file '{p.as_posix()}'")
        if GAP > 0 and i < len(parts) - 1:
            lines.append(f"file '{black.as_posix()}'")
    lst.write_text("\n".join(lines) + "\n", encoding="utf-8")
    master = out / "少女A_demo.mp4"
    run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", lst,
         "-c:v", "libx264", "-preset", "slow", "-crf", "15", "-pix_fmt", "yuv420p", "-color_primaries", "bt709", "-color_trc", "bt709",
         "-colorspace", "bt709", "-c:a", "aac", "-b:a", "256k", "-movflags", "+faststart", master])
    # a smaller copy that can be sent to a phone (limit 30 MiB)
    dur = float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(master)]).decode().strip())
    kbps = int((29.0 * 8192) / dur - 130)
    phone = out / "少女A_demo_手机版.mp4"
    logs = work / "pass"
    run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", master, "-c:v", "libx264", "-preset", "slow", "-b:v", f"{kbps}k", "-pass", "1",
         "-passlogfile", logs, "-an", "-f", "null", "NUL"])
    run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", master, "-c:v", "libx264", "-preset", "slow", "-b:v", f"{kbps}k", "-pass", "2",
         "-passlogfile", logs, "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart", phone])
    print("DONE", master, dur, "s", flush=True)


if __name__ == "__main__":
    if sys.argv[1] == "render":
        names = sys.argv[2:] or [m for m, _ in CLIPS]
        for mod, cls in CLIPS:
            if mod in names:
                # clip 6 keeps double-size face pictures and eye layers in every worker
                E.render_clip(mod, cls, ROOT / "work" / "clips" / f"{mod}.mp4", workers={"c1": 3, "c2": 4}.get(mod, 3))
    else:
        build()
