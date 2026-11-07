"""build_end.py's wind drawings again, with a wider seam between each drawing and the master, so no line steps where it passes from one to the other (docs/全片修改清单3.md)."""
import importlib.util
import json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
spec = importlib.util.spec_from_file_location("build_end", ROOT / "work/eye/key6/build_end.py")
BE = importlib.util.module_from_spec(spec)
spec.loader.exec_module(BE)
lay0 = BE.lay
BE.lay = lambda base, src, mask, sigma=1.6: lay0(base, src, mask, 2.6 if sigma == 1.2 else sigma)
cut0 = BE.C.cutout


def cut(bgr):
    r = cut0(bgr)
    n, lab, st, _ = BE.cv2.connectedComponentsWithStats((r[..., 3] > 0.03).astype(BE.np.uint8), connectivity=8)
    for i in range(1, n):
        if st[i, 4] < 600:
            r[..., 3][lab == i] = 0
    return r


BE.C.cutout = cut
BE.main(json.loads((BE.G.parent / "picks.json").read_text(encoding="utf-8")))
