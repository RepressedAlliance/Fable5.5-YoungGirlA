"""Prepare clip 4: die-cut standee images with a paper border, and the printed wall."""
import json
import sys
from pathlib import Path

import cv2
import numpy as np
import skia

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "src" / "art"), str(ROOT / "src" / "three")]
import cutout as C  # noqa: E402
import engine as E  # noqa: E402
import shared_c4 as S  # noqa: E402

FINAL = ROOT / "assets" / "gen" / "final"
OUT = ROOT / "assets" / "gen" / "standee"
BARS = json.loads((ROOT / "assets" / "gen" / "bars.json").read_text(encoding="utf-8"))
FIG_H = 1.62   # bow to shoes, metres, the same for all of them
PPM = 900      # pixels per metre on the printed wall


def standee(name):
    im = C.load(FINAL / f"{name}.png")
    a = im[..., 3]
    ys, xs = np.where(a > 0.5)
    y0, y1, x0, x1 = ys.min(), ys.max(), xs.min(), xs.max()
    pad = 34
    crop = im[max(0, y0 - pad):y1 + pad, max(0, x0 - pad):x1 + pad]
    # paper border: a slightly wobbly die cut
    ca = (crop[..., 3] > 0.5).astype(np.uint8)
    r = 12
    k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * r + 1, 2 * r + 1))
    border = cv2.dilate(ca, k)
    border = cv2.GaussianBlur(border.astype(np.float32), (0, 0), 3.0)
    border = (border > 0.5).astype(np.float32)
    border = cv2.GaussianBlur(border, (0, 0), 0.7)
    paper = np.array([0.975, 0.965, 0.93], np.float32)
    rgb = crop[..., :3] * crop[..., 3:4] + paper * (1 - crop[..., 3:4])
    out = np.dstack([rgb, np.maximum(border, crop[..., 3])])
    C.save(out, OUT / f"{name}.png")
    h, w = out.shape[:2]
    scale = FIG_H / (y1 - y0)
    bx, by, ln, th, ang, _ = BARS[name]
    ox, oy = max(0, x0 - pad), max(0, y0 - pad)
    return {"w_m": w * scale, "h_m": h * scale, "w": w, "h": h,
            "bar": [(bx - ox) / w, (by - oy) / h, ln / w, th / h, ang]}


def wall():
    W = int(S.COLS * S.CELL_W * PPM)
    H = int(S.ROWS * S.CELL_H * PPM)
    surf = skia.Surface(W, H)
    c = surf.getCanvas()
    c.clear(E.col("#03C3FB"))
    cw, ch = S.CELL_W * PPM, S.CELL_H * PPM
    for (r, col) in zip(S.RUMOURS, S.ORDER):
        name, text, who, bg, fg, _ = r
        x, y = col[0] * cw, col[1] * ch
        E.rect(c, x, y, cw, ch, bg)
        # the rumour: large and vertical down the left of the cell, always measured to fit
        t = E.fit(text, "ShipporiMinchoB1-ExtraBold", cw * 0.24, ch * 0.84, vertical=True, max_size=300)
        t.draw(c, x + cw * 0.17, y + ch * 0.5, fg, ax=0.5, ay=0.5)
        sm = E.Type("——" + who + "談", "ZenKakuGothicNew-Bold", 40, vertical=True)
        sm.draw(c, x + cw * 0.075, y + ch * 0.92, fg, ax=0.5, ay=1.0, alpha=0.85)
        # a hairline frame, like a printed form
        p = skia.Paint(AntiAlias=True, Color4f=E.col(E.INK), Style=skia.Paint.kStroke_Style, StrokeWidth=5)
        c.drawRect(skia.Rect.MakeXYWH(x + 22, y + 22, cw - 44, ch - 44), p)
    # the empty cell
    ex, ey = S.EMPTY[0] * cw, S.EMPTY[1] * ch
    E.rect(c, ex, ey, cw, ch, "#F6F3EA")
    p = skia.Paint(AntiAlias=True, Color4f=E.col(E.INK), Style=skia.Paint.kStroke_Style, StrokeWidth=5)
    c.drawRect(skia.Rect.MakeXYWH(ex + 22, ey + 22, cw - 44, ch - 44), p)
    t = E.fit("本人より", "ShipporiMinchoB1-ExtraBold", cw * 0.62, ch * 0.3, max_size=400)
    t.draw(c, ex + cw * 0.5, ey + ch * 0.36, E.INK)
    # an empty input line under it
    E.rect(c, ex + cw * 0.18, ey + ch * 0.68, cw * 0.64, 10, E.INK)
    arr = surf.makeImageSnapshot().toarray(colorType=skia.ColorType.kRGBA_8888_ColorType,
                                           alphaType=skia.AlphaType.kOpaque_AlphaType)[..., :3]
    cv2.imwrite(str(ROOT / "assets" / "gen" / "c4_wall.png"), arr[..., ::-1])
    print("wall", W, H)


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    meta = {}
    for r in S.RUMOURS:
        meta[r[0]] = standee(r[0])
        print(r[0], {k: round(v, 3) if isinstance(v, float) else v for k, v in meta[r[0]].items() if k != "bar"})
    (OUT / "meta.json").write_text(json.dumps(meta, indent=1), encoding="utf-8")
    wall()
