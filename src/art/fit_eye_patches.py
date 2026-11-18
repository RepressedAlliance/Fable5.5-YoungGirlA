"""Keep the eye patches of the ending's bust off her hair.

2026-11-17: the closed and half-open eyes are laid over each wind drawing as an oval of skin with the new eye in it. Where the
oval reached up into the bangs it painted skin over the hair, a bite out of the hair's edge, and at its rim it carried crumbs
of a lash cut off by the oval. Now a patch shows only where the drawing under it is not hair (hair and the ink line round it
stay the drawing's), and dark crumbs in the rim of the patch are dropped.
Usage: fit_eye_patches.py   (reads the untouched patches from work/gen/fix1117/end_orig, writes assets/gen/end)"""
import json
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
END = ROOT / "assets" / "gen" / "end"
ORIG = ROOT / "work" / "gen" / "fix1117" / "end_orig"
LINE_W = 5.0                 # px: the drawings' hair outline is 4 to 6 px
INK_BGR = (19, 15, 13)
lay = json.loads((END / "layout.json").read_text(encoding="utf-8"))["patches"]
for name, (px, py) in lay.items():
    if not name.startswith(("eye_closed@", "eye_half@")):
        continue
    base = cv2.imread(str(END / (name.split("@")[1] + ".png")), cv2.IMREAD_UNCHANGED)
    p = cv2.imread(str(END / f"{name}.png"), cv2.IMREAD_UNCHANGED)
    h, w = p.shape[:2]
    b = base[py:py + h, px:px + w].astype(np.float32) / 255
    bb, bg, br = b[..., 0], b[..., 1], b[..., 2]
    hair = (br > 0.80) & (bg > 0.62) & (bb < 0.55) & (br - bb > 0.30)
    hair_raw = hair.copy()
    # only the hair's paint stays the drawing's; every ink line under the patch is covered (the open eye's lash touches the bangs,
    # and kept as "hair outline" it showed as a row of dashes), and the hair gets its outline back, drawn along its new edge
    # hair here is the bangs reaching into the patch: smoothed, and without the stray yellow specks a lash's blur leaves
    hair = cv2.morphologyEx(hair.astype(np.uint8), cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7)))
    n_, lab, st, _ = cv2.connectedComponentsWithStats(hair, connectivity=8)
    hair = np.isin(lab, [i for i in range(1, n_) if st[i, cv2.CC_STAT_AREA] >= 400])
    keep_base = cv2.dilate(hair.astype(np.uint8), np.ones((3, 3), np.uint8)) > 0
    outside = (~keep_base).astype(np.uint8)
    dist = cv2.distanceTransform(outside, cv2.DIST_L2, 3)
    line = (dist > 0) & (dist <= LINE_W)
    a = p[..., 3].astype(np.float32) / 255
    # dark crumbs in the patch's rim
    rim = (a > 0.05) & (cv2.erode((a > 0.5).astype(np.uint8), np.ones((13, 13), np.uint8)) == 0)
    plum = p[..., :3].astype(np.float32).mean(-1) / 255
    crumbs = rim & (plum < 0.45)
    a[keep_base | crumbs] = 0
    # the drawing's own open-eye lash reaching just past the patch's upper edge: covered with the patch's skin. Only ink right
    # against the patch, near the eye, and well clear of the hair's outline
    lum = b[..., :3].mean(-1)
    eye_near = cv2.dilate((((lum > 0.85) & ~hair) | ((bb > bg) & (bb > br))).astype(np.uint8), np.ones((41, 41), np.uint8)) > 0
    hair_far = ~(cv2.dilate(hair_raw.astype(np.uint8), np.ones((15, 15), np.uint8)) > 0)
    against = cv2.dilate((a > 0.5).astype(np.uint8), np.ones((21, 21), np.uint8)) > 0
    stray = (lum < 0.45) & eye_near & hair_far & against & (a < 0.5)
    stray = (cv2.dilate(stray.astype(np.uint8), np.ones((3, 3), np.uint8)) > 0) & hair_far
    skin = np.median(p[..., :3][(a > 0.9) & (p[..., :3].astype(np.float32).mean(-1) > 200)], axis=0)
    p[..., :3][stray] = skin
    a[stray] = 1.0
    # the new outline: only where the patch would otherwise meet the hair
    draw = line & (p[..., 3] > 128) & ~crumbs
    p[..., :3][draw] = INK_BGR
    a[draw] = 1.0
    a = cv2.GaussianBlur(a, (0, 0), 0.7)
    p[..., 3] = (np.clip(a, 0, 1) * 255 + 0.5).astype(np.uint8)
    cv2.imwrite(str(END / f"{name}.png"), p)
    print(name, int(keep_base.sum()), "kept from the drawing,", int(crumbs.sum()), "crumbs")
