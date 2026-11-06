"""Paint one EXR to PNG for look checks. usage: test_comp.py in.exr out.png [cold] [frost]"""
import sys
import time
from pathlib import Path

import cv2
import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
import comp  # noqa: E402

src, dst = sys.argv[1], sys.argv[2]
cold = float(sys.argv[3]) if len(sys.argv) > 3 else 0
frost = float(sys.argv[4]) if len(sys.argv) > 4 else 0
t = time.time()
p = comp.read_exr(src)
print({k: v.shape for k, v in p.items()}, round(time.time() - t, 2))
for k in ("DiffDir",):
    print(k, float(np.nanmin(p[k])), float(np.nanmax(p[k])), float(np.nanmedian(p[k])))
t = time.time()
rgba = comp.paint(p, comp.Look(cold=cold, frost=frost), ss=1.5)
print("paint", round(time.time() - t, 2))
rgb = comp.apply_grain(rgba[..., :3], 0.012)
cv2.imwrite(dst, cv2.cvtColor((rgb * 255).astype(np.uint8), cv2.COLOR_RGB2BGR))
