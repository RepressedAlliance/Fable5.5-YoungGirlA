"""Put each candidate's irises into the real frame, in the dark grade and in full colour, blind-labelled A, B, C..."""
import json
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
import c6 as C6  # noqa: E402

raw = C.load(ROOT / "assets" / "gen" / "cut" / "p05_face_close.png")
im = cel.add_cel(raw, drop=34, hair_inset=30)
H, W = im.shape[:2]
r, g, b = raw[..., 0], raw[..., 1], raw[..., 2]
ir = cv2.morphologyEx(((g > r + 0.12) & (b > r + 0.12) & (g < 0.72)).astype(np.float32), cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
ir = cv2.GaussianBlur(ir, (0, 0), 0.7)[..., None]
night = C6.duotone(im)
BASE = ROOT / "work" / "eye"
CANDS = [("key", BASE / "base_face.png", 1), ("api_a_0", BASE / "api_a_0.png", 1), ("v2_glass_1", BASE / "v2_glass_1.png", 2),
         ("v3_a_0", BASE / "v3_a_0.png", 2), ("v3_a_1", BASE / "v3_a_1.png", 2),
         ("v3_c_0", BASE / "v3_c_0.png", 2), ("v3_c_1", BASE / "v3_c_1.png", 2)]
LABEL = "GBECADF"   # shuffled so the order says nothing


def iris_layer(path, mag):
    src = cv2.imread(str(path))[..., ::-1].astype(np.float32) / 255
    if mag == 1:
        return cv2.resize(src, (W, H), interpolation=cv2.INTER_AREA)
    # the magnified paint-overs cover x 384..1152, y 207..719 of the picture
    small = cv2.resize(src, (768, 512), interpolation=cv2.INTER_AREA)
    out = im[..., :3].copy()
    out[207:719, 384:1152] = small
    return out


def comp(base, bg, layer):
    bgc = np.array([int(bg[i:i + 2], 16) for i in (1, 3, 5)], np.float32) / 255
    rgb = base[..., :3] * base[..., 3:4] + bgc * (1 - base[..., 3:4])
    rgb = rgb * (1 - ir) + layer * ir
    canvas = np.zeros((1080, 1920, 3), np.float32) + bgc
    s = 1080 / 1024
    w = int(W * s)
    canvas[0:1080, (1920 - w) // 2:(1920 - w) // 2 + w] = cv2.resize(rgb, (w, 1080), interpolation=cv2.INTER_AREA)
    return canvas


out_dir = ROOT / "work" / "eye" / "blind"
out_dir.mkdir(parents=True, exist_ok=True)
answer = {}
tiles = []
for (name, path, mag), lab in sorted(zip(CANDS, LABEL), key=lambda q: q[1]):
    answer[lab] = name
    layer = iris_layer(path, mag)
    day = comp(im, "#03C3FB", layer)
    nig = comp(night, "#05070D", layer)
    cv2.imwrite(str(out_dir / f"{lab}_colour.png"), (day[..., ::-1] * 255).astype(np.uint8))
    cv2.imwrite(str(out_dir / f"{lab}_dark.png"), (nig[..., ::-1] * 255).astype(np.uint8))
    a = day[200:780, 400:1520]
    b_ = nig[200:780, 400:1520]
    pair = np.hstack([a, b_])
    pair = cv2.resize(pair, (1680, 435), interpolation=cv2.INTER_AREA)
    t = (pair[..., ::-1] * 255).astype(np.uint8).copy()
    cv2.putText(t, lab, (14, 56), cv2.FONT_HERSHEY_SIMPLEX, 1.8, (0, 0, 255), 4, cv2.LINE_AA)
    tiles.append(t)
cv2.imwrite(str(out_dir / "sheet.png"), np.vstack(tiles))
(out_dir.parent / "blind_answer.json").write_text(json.dumps(answer, indent=1))
print(answer)
