"""Find where the eye is in a side-on picture of her, from its flat teal. usage: bars_c.py calibrate g11_run ... | bars_c.py place ANGLE TH SEED0 id id ...
place: writes the bars into assets/gen/bars.json (a quick read-change-write, the file is shared), stamps, and checks that no teal or lash is left."""
import json
import sys
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src" / "art"))
import cutout as C  # noqa: E402

CUT = ROOT / "assets" / "gen" / "cut"
BARS = ROOT / "assets" / "gen" / "bars.json"
TEAL = np.array([0x21, 0x8E, 0xA3], np.float32) / 255


def eye(aid):
    im = C.load(CUT / f"{aid}.png")
    d = np.abs(im[..., :3] - TEAL).max(-1)
    m = ((d < 0.16) & (im[..., 3] > 0.5)).astype(np.uint8)
    # the eye is in the top half of the figure; the largest teal blob
    n, lab, st, cen = cv2.connectedComponentsWithStats(m, connectivity=8)
    if n < 2:
        return None
    best = max(range(1, n), key=lambda i: st[i, 4])
    return float(cen[best][0]), float(cen[best][1]), int(st[best, 4]), st[best][:4].tolist()


if __name__ == "__main__":
    spec = json.loads(BARS.read_text(encoding="utf-8"))
    if sys.argv[1] == "calibrate":
        # the older pictures in cut/ have their eyes: how the hand-placed bars sit on them
        for aid in sys.argv[2:]:
            e = eye(aid)
            b = spec.get(aid)
            print(aid, e, b, None if not (e and b) else (round(b[0] - e[0]), round(b[1] - e[1])))
    else:
        ang, th, seed = float(sys.argv[2]), float(sys.argv[3]), int(sys.argv[4])
        dx, dy = float(sys.argv[5]), float(sys.argv[6])
        new = {}
        for k, aid in enumerate(sys.argv[7:]):
            e = eye(aid)
            new[aid] = [round(e[0] + dx), round(e[1] + dy), 155, th, ang, seed + k]
            print(aid, new[aid], e[2:])
        spec = json.loads(BARS.read_text(encoding="utf-8"))
        spec.update(new)
        BARS.write_text(json.dumps(spec, ensure_ascii=False, indent=1), encoding="utf-8")
