"""Export the current finished eyes large, as the base for a paint-over."""
import sys
from pathlib import Path

import cv2
import numpy as np
import skia

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "src" / "clips"), str(ROOT / "src" / "art"), str(ROOT / "src" / "three")]
import cel  # noqa: E402
import cutout as C  # noqa: E402
import engine as E  # noqa: E402
import eye_styles as ES  # noqa: E402
import c6 as C6  # noqa: E402

raw = C.load(ROOT / "assets" / "gen" / "cut" / "p05_face_close.png")
im = cel.add_cel(raw, drop=34, hair_inset=30)
H, W = im.shape[:2]
r, g, b = raw[..., 0], raw[..., 1], raw[..., 2]
ir = cv2.morphologyEx(((g > r + 0.12) & (b > r + 0.12) & (g < 0.72)).astype(np.float32), cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
ir = cv2.GaussianBlur(ir, (0, 0), 0.8)
mask = np.zeros((H, W, 4), np.float32)
mask[..., :3] = 1
mask[..., 3] = ir
mask_img = E.np_to_image(mask)
s = skia.Surface(W, H)
c = s.getCanvas()
c.clear(E.col(E.CYAN))
c.drawImage(E.np_to_image(im), 0, 0, E.SAMPLING)
for i, (ex, ey) in enumerate(C6.EYES):
    c.saveLayer()
    ES.key(c, ex, ey, 11, -1 if i == 0 else 1)
    c.drawImage(mask_img, 0, 0, E.SAMPLING, skia.Paint(BlendMode=skia.BlendMode.kDstIn))
    c.restore()
arr = s.makeImageSnapshot().toarray(colorType=skia.ColorType.kRGBA_8888_ColorType, alphaType=skia.AlphaType.kOpaque_AlphaType)[..., :3]
out = ROOT / "work" / "eye"
out.mkdir(parents=True, exist_ok=True)
cv2.imwrite(str(out / "base_face.png"), arr[..., ::-1])
# one eye, very large, for judging shapes
ex, ey = C6.EYES[0]
crop = arr[int(ey - 170):int(ey + 170), int(ex - 255):int(ex + 255)]
cv2.imwrite(str(out / "base_eye.png"), cv2.resize(crop[..., ::-1], (1530, 1020), interpolation=cv2.INTER_CUBIC))
print("ok")
