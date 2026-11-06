"""Debug stills and contact sheets. usage: preview.py module Class t1 t2 ...  -> work/qc/<name>_sheet.jpg"""
import sys
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "src" / "clips"), str(ROOT / "src" / "art"), str(ROOT / "src" / "three")]
import importlib  # noqa: E402

module, cls = sys.argv[1], sys.argv[2]
times = [float(x) for x in sys.argv[3:]]
m = importlib.import_module(module)
clip = getattr(m, cls)()
clip.setup()
out = ROOT / "work" / "qc" / clip.name
out.mkdir(parents=True, exist_ok=True)
ims = []
for t in times:
    rgb = clip.frame_rgb(t)
    im = (rgb * 255 + 0.5).astype(np.uint8)[..., ::-1]
    cv2.imwrite(str(out / f"s{t:07.3f}.png"), im)
    small = cv2.resize(im, (960, 540), interpolation=cv2.INTER_AREA)
    cv2.putText(small, f"{t:.2f}", (10, 26), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2, cv2.LINE_AA)
    ims.append(small)
while len(ims) % 2:
    ims.append(np.zeros_like(ims[0]))
sheet = np.vstack([np.hstack(ims[i:i + 2]) for i in range(0, len(ims), 2)])
cv2.imwrite(str(ROOT / "work" / "qc" / f"{clip.name}_sheet.jpg"), sheet, [cv2.IMWRITE_JPEG_QUALITY, 90])
print("sheet", clip.name, len(times))
