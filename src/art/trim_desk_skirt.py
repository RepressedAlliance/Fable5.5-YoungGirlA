"""Her classroom drawings end at the small of her back, behind the chair back. 2026-11-18: the navy band of skirt along their
bottom edge reaches further left than her blouse, and that corner showed past the chair back's edge as a scrap of navy.
Below the blouse's hem, nothing further left than the blouse's own left edge is kept.
Usage: trim_desk_skirt.py   (reads untouched copies from work/gen/fix1117/room_orig, writes assets/gen/cut)"""
import shutil
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
CUT = ROOT / "assets" / "gen" / "cut"
ORIG = ROOT / "work" / "gen" / "fix1117" / "room_orig"
NAMES = ["o51_desk_chin", "o54_wind_a", "o54_wind_b0", "o54_wind_b1", "o54_wind_b2", "o54_wind_c", "o58_turn_blown", "o58_mid_blown",
         "o58_press_blown", "o57_press_wind_a", "o58_press_half", "o57_press_wind_b", "o53_desk_press"]
for n in NAMES:
    src = ORIG / f"{n}.png"
    if not src.exists():
        shutil.copy2(CUT / f"{n}.png", src)
    im = cv2.imread(str(src), cv2.IMREAD_UNCHANGED)
    b, g, r, a = [im[..., i].astype(np.int32) for i in range(4)]
    H = im.shape[0]
    navy = (a > 128) & (b > r + 25) & (b < 140)
    white = (a > 128) & (r > 200) & (g > 200) & (b > 190)
    # the skirt band: the lowest rows where navy is most of the width
    rows = np.nonzero(navy.sum(1) > 40)[0]
    rows = rows[rows > H * 0.75]
    if not len(rows):
        print(n, "no skirt band"); continue
    top = rows.min()
    # the blouse's left edge just above the band
    above = white[max(top - 60, 0):top]
    cols = np.nonzero(above.any(0))[0]
    left = int(cols.min()) if len(cols) else 0
    cut = np.zeros(a.shape, bool)
    cut[top - 4:, :left] = True
    # 2026-11-18, second pass: under her arm the band runs on past her body, and that end showed beside the chair back lying on
    # the desk top like a cut-out scrap. From the first column, right of her body, where the sleeve hangs below the blouse's hem,
    # the band goes, and with it the skirt's own outline there (not the sleeve's: dark pixels next to the sleeve's white stay).
    solid = (a > 128) & ~navy
    # walk right along the blouse just above the band: past its left outline, through the blouse (shading included), to the
    # outline where her arm meets her body
    row = top - 10
    light = (a[row] > 128) & (np.maximum(np.maximum(b[row], g[row]), r[row]) > 120)
    under_from, run, c = None, 0, max(left - 5, 0)
    while c < a.shape[1] and not light[c]:
        c += 1
    while c < a.shape[1]:
        if light[c]:
            run += 1
        elif run > 150 and not light[c:c + 3].any():
            under_from = c
            break
        c += 1
    if under_from is not None:
        dark = (a > 128) & (np.maximum(np.maximum(b, g), r) < 80)
        near_white = cv2.dilate(white.astype(np.uint8), np.ones((7, 7), np.uint8)) > 0
        # her sleeve and hand, and the navy cuff between them: kept
        skin = (a > 128) & (r > 200) & (g > 150) & (b > 110) & (r > b + 30)
        arm = cv2.dilate((white | skin).astype(np.uint8), np.ones((25, 25), np.uint8)) > 0
        region = np.zeros(a.shape, bool)
        region[top - 4:, under_from - 4:] = True
        sleeve = region & solid & ~dark
        # what is under the sleeve's lowest point in each column, and every bit of navy, goes
        below = np.zeros(a.shape, bool)
        for c in range(under_from - 4, a.shape[1]):
            col = np.nonzero(sleeve[:, c])[0]
            if len(col):
                below[col.max() + 4:, c] = True
            else:
                below[top - 4:, c] = True
        # and anything at all under the sleeve that is not the sleeve's own outline, faint edge pixels of the old skirt included
        cut |= region & ((navy & ~arm) | (below & ~near_white))
    right = under_from if under_from is not None else -1
    im[..., 3][cut] = 0
    cv2.imwrite(str(CUT / f"{n}.png"), im)
    print(n, "band from row", top, "kept columns", left, "to", right, "removed", int((a[cut] > 0).sum()))
