"""Draw each image's hand-placed bar into it (assets/gen/final) and write a zoomed check sheet."""
import json
import sys
from pathlib import Path

import cv2
import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
import bar as B  # noqa: E402
import cutout as C  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
CUT = ROOT / "assets" / "gen" / "cut"
FINAL = ROOT / "assets" / "gen" / "final"
SPEC = json.loads((ROOT / "assets" / "gen" / "bars.json").read_text(encoding="utf-8"))


def main(only=None):
    FINAL.mkdir(parents=True, exist_ok=True)
    crops = []
    for name, s in SPEC.items():
        if name.startswith("_") or (only and name not in only):
            continue
        im = C.load(CUT / f"{name}.png")
        if name == "p01_bust_front":
            import cel
            im = cel.add_cel(im, drop=20, hair_inset=18)
        cx, cy, ln, th, ang, seed = s
        b = B.Bar(cx, cy, ln, th, ang, seed)
        out = B.stamp(im, b)
        C.save(out, FINAL / f"{name}.png")
        # before / after, zoomed on the head
        m = int(max(ln, th * 3) * 0.72)
        x0, x1 = max(0, int(cx - m)), min(im.shape[1], int(cx + m))
        y0, y1 = max(0, int(cy - m)), min(im.shape[0], int(cy + m))
        bg = np.array([0.5, 0.5, 0.5], np.float32)
        def flat(a):
            return a[..., :3] * a[..., 3:4] + bg * (1 - a[..., 3:4])
        pair = np.hstack([flat(im[y0:y1, x0:x1]), flat(out[y0:y1, x0:x1])])
        hh = 300
        pair = cv2.resize(pair, (int(pair.shape[1] * hh / pair.shape[0]), hh), interpolation=cv2.INTER_AREA)
        pair = (pair[..., ::-1] * 255).astype(np.uint8)
        cv2.putText(pair, name[:14], (6, 18), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1, cv2.LINE_AA)
        crops.append(pair)
    cols = 3
    rows = []
    for i in range(0, len(crops), cols):
        row = crops[i:i + cols]
        w = sum(c.shape[1] for c in row)
        rows.append(np.hstack(row))
    W = max(r.shape[1] for r in rows)
    sheet = np.vstack([np.pad(r, ((0, 0), (0, W - r.shape[1]), (0, 0))) for r in rows])
    out_path = ROOT / "work" / "qc" / "bars_check.jpg"
    cv2.imwrite(str(out_path), sheet, [cv2.IMWRITE_JPEG_QUALITY, 92])
    print("sheet", sheet.shape, out_path)


if __name__ == "__main__":
    main(sys.argv[1:] or None)
