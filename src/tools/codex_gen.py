"""Generate one image with the Codex CLI's built-in image tool and copy it into the project.

Usage:
  python src/tools/codex_gen.py OUT.png PROMPT.txt [--ref a.png --ref b.png] [--tries 2]

Codex writes images to ~/.codex/generated_images/<thread_id>/; the thread id comes from
the --json event stream, so several generations can run side by side without mixing up.
A log (prompt, thread id, timing, last message) is written next to OUT as OUT.log.json.
"""
import argparse
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

GEN_DIR = Path(os.path.expanduser("~")) / ".codex" / "generated_images"
CODEX = shutil.which("codex") or shutil.which("codex.cmd")

PREAMBLE = (
    "Use your built-in image generation tool to create exactly ONE image as described below. "
    "Do not write code, do not run shell commands, do not create or edit files. "
    "If reference images are attached, use them only as described. "
    "After the image is generated, reply with one short line describing it.\n\n"
)


def run_once(prompt, refs, workdir, timeout):
    cmd = [CODEX, "exec", "--skip-git-repo-check", "--json", "-s", "read-only", "-C", str(workdir)]
    for r in refs:
        cmd += ["-i", str(r)]
    cmd.append("-")
    t0 = time.time()
    p = subprocess.run(cmd, input=PREAMBLE + prompt, capture_output=True, text=True,
                       encoding="utf-8", errors="replace", timeout=timeout)
    thread, last = None, ""
    for line in p.stdout.splitlines():
        try:
            ev = json.loads(line)
        except json.JSONDecodeError:
            continue
        if ev.get("type") == "thread.started":
            thread = ev.get("thread_id")
        item = ev.get("item") or {}
        if item.get("type") == "agent_message":
            last = item.get("text", "")
    imgs = []
    if thread and (GEN_DIR / thread).is_dir():
        imgs = sorted((GEN_DIR / thread).glob("*.png"), key=lambda q: q.stat().st_mtime)
    return {"returncode": p.returncode, "thread": thread, "images": [str(i) for i in imgs],
            "last": last, "seconds": round(time.time() - t0, 1), "stderr_tail": p.stderr[-800:]}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("out")
    ap.add_argument("prompt_file")
    ap.add_argument("--ref", action="append", default=[])
    ap.add_argument("--tries", type=int, default=2)
    ap.add_argument("--timeout", type=int, default=900)
    a = ap.parse_args()
    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    prompt = Path(a.prompt_file).read_text(encoding="utf-8")
    refs = [Path(r).resolve() for r in a.ref]
    work = out.parent
    log = {"prompt_file": str(a.prompt_file), "refs": [str(r) for r in refs], "attempts": []}
    ok = False
    for i in range(a.tries):
        try:
            r = run_once(prompt, refs, work, a.timeout)
        except subprocess.TimeoutExpired:
            r = {"error": "timeout"}
        log["attempts"].append(r)
        if r.get("images"):
            shutil.copy2(r["images"][-1], out)
            ok = True
            break
    Path(str(out) + ".log.json").write_text(json.dumps(log, ensure_ascii=False, indent=1), encoding="utf-8")
    print(("OK " if ok else "FAIL ") + str(out), json.dumps(log["attempts"][-1], ensure_ascii=False)[:400])
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
