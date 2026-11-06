"""Comparison sheet for the eye treatments: finished eyes in full colour and in the dark grade, plus the build-up."""
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
ir = ((g > r + 0.12) & (b > r + 0.12) & (g < 0.72)).astype(np.float32)
ir = cv2.morphologyEx(ir, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
ir = cv2.GaussianBlur(ir, (0, 0), 0.8)
mask = np.zeros((H, W, 4), np.float32)
mask[..., :3] = 1
mask[..., 3] = ir
mask_img = E.np_to_image(mask)
full = E.np_to_image(im)
dark = E.np_to_image(C6.duotone(im))
EYES = C6.EYES


def gen_iris(path):
    """Take the irises out of a generated picture and map them onto the drawn ones."""
    g_im = cv2.imread(str(path))
    if g_im is None:
        return None
    if g_im.shape[:2] != (H, W):
        g_im = cv2.resize(g_im, (W, H), interpolation=cv2.INTER_AREA)
    rgb = g_im[..., ::-1].astype(np.float32) / 255
    out = np.zeros((H, W, 4), np.float32)
    for side, (ex, ey) in enumerate(EYES):
        # search the generated picture for this eye's iris: bluish non-background pixels near the same place
        x0, x1, y0, y1 = int(ex - 170), int(ex + 170), int(ey - 170), int(ey + 170)
        patch = rgb[y0:y1, x0:x1]
        m = ((patch[..., 2] > patch[..., 0] + 0.08) & (patch[..., 1] > patch[..., 0] + 0.02)).astype(np.uint8)
        m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, np.ones((9, 9), np.uint8))
        n, lab, st, cen = cv2.connectedComponentsWithStats(m)
        if n < 2:
            continue
        k = 1 + int(np.argmax(st[1:, 4]))
        gx, gy, gw, gh = st[k, :4]
        src = np.float32([[x0 + gx, y0 + gy], [x0 + gx + gw, y0 + gy], [x0 + gx, y0 + gy + gh]])
        dst = np.float32([[ex - 80.5, ey - 105.5], [ex + 80.5, ey - 105.5], [ex - 80.5, ey + 105.5]])
        M = cv2.getAffineTransform(src, dst)
        warped = cv2.warpAffine(rgb, M, (W, H), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
        box = np.zeros((H, W), bool)
        box[int(ey - 125):int(ey + 125), int(ex - 100):int(ex + 100)] = True
        out[box, :3] = warped[box]
        out[box, 3] = 1
    return E.np_to_image(out)


GENS = {}
for name in ("e01_eyes_shining", "e02_eyes_shining"):
    p = ROOT / "assets" / "gen" / "raw" / f"{name}.png"
    if p.exists():
        g2 = gen_iris(p)
        if g2 is not None:
            GENS[name[:3]] = g2


def paint(base, bg, style, n):
    s = skia.Surface(W, H)
    c = s.getCanvas()
    c.clear(E.col(bg))
    c.drawImage(base, 0, 0, E.SAMPLING)
    for i, (ex, ey) in enumerate(EYES):
        c.saveLayer()
        if style in GENS:
            c.drawImage(GENS[style], 0, 0, E.SAMPLING)
        else:
            ES.STYLES[style](c, ex, ey, n, -1 if i == 0 else 1)
        c.drawImage(mask_img, 0, 0, E.SAMPLING, skia.Paint(BlendMode=skia.BlendMode.kDstIn))
        c.restore()
    return s.makeImageSnapshot().toarray(colorType=skia.ColorType.kRGBA_8888_ColorType, alphaType=skia.AlphaType.kOpaque_AlphaType)[..., :3]


rows = []
styles = list(ES.STYLES) + list(GENS)
for st in styles:
    final = paint(full, E.CYAN, st, 11)
    night = paint(dark, "#05070D", st, 11)
    # full frame scale, eyes region large
    a = final[230:700, 300:1240]
    b_ = night[230:700, 300:1240]
    row = [cv2.resize(a, (760, 380), interpolation=cv2.INTER_AREA), cv2.resize(b_, (760, 380), interpolation=cv2.INTER_AREA)]
    if st not in GENS:
        strip = [paint(dark, "#05070D", st, n)[300:640, 400:680] for n in (2, 5, 8)]
        row.append(np.hstack([cv2.resize(x, (253, 380), interpolation=cv2.INTER_AREA) for x in strip]))
    else:
        row.append(np.zeros((380, 759, 3), np.uint8))
    rr = np.hstack(row).copy()
    cv2.putText(rr, st, (10, 34), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 0, 0), 2, cv2.LINE_AA)
    rows.append(rr)
sheet = np.vstack(rows)
cv2.imwrite(str(ROOT / "work" / "qc" / "eye_compare.png"), sheet[..., ::-1])
print(sheet.shape, styles)
