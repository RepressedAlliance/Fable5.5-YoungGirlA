"""Make a take the one in use: raw/<id>.png, cut/<id>.png, then the bar, final/<id>.png. usage: pick_c.py id=take id=take ..."""
import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / "src" / "art"), str(ROOT / "work" / "gen")]
import cv2  # noqa: E402
import cutout as C  # noqa: E402
import bars_c  # noqa: E402

RAW = ROOT / "assets" / "gen" / "raw"
CUT = ROOT / "assets" / "gen" / "cut"
# family: offset of the bar from the eye as on the hand-placed bars of the same family, thickness, angle
FAM = {"g6": (-38, 4, 58, 0), "g7": (-27, -2, 58, 6), "g25": (-38, 0, 58, 0), "g26": (-38, -3, 58, 0), "g27": (-36, -4, 58, 8), "g28": (-35, -3, 62, 14),
       "g3": (-35, -3, 62, 16)}
SEEDS = {"g61": 301, "g62": 302, "g63": 303, "g64": 304, "g71": 311, "g72": 312, "g73": 313, "g74": 314, "g25": 321, "g26": 322, "g27": 323, "g28": 324,
         "g35": 331, "g36": 332, "g37": 333, "g38": 334}

ids = []
for a in sys.argv[1:]:
    aid, take = a.split("=")
    src = RAW / f"{aid}.t{take}.png"
    dst = RAW / f"{aid}.png"
    # gen_batch.py names takes the same way; the file without a number is simply the one in use
    shutil.copy2(src, dst)
    C.save(C.cutout(cv2.imread(str(dst))), CUT / f"{aid}.png")
    if aid.startswith("g"):
        fam = next(k for k in sorted(FAM, key=len, reverse=True) if aid.startswith(k))
        dx, dy, th, ang = FAM[fam]
        e = bars_c.eye(aid)
        spec = json.loads(bars_c.BARS.read_text(encoding="utf-8"))
        spec[aid] = [round(e[0] + dx), round(e[1] + dy), 155, th, ang, SEEDS[aid[:3]]]
        bars_c.BARS.write_text(json.dumps(spec, ensure_ascii=False, indent=1), encoding="utf-8")
        ids.append(aid)
    print(aid, flush=True)
if ids:
    subprocess.run([sys.executable, str(ROOT / "src" / "art" / "stamp_bars.py")] + ids, check=True)
