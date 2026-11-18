"""Paint out the ghost lines a generated drawing keeps from the picture it was edited from.

2026-11-17: the bust drawings of the wind (assets/gen/end) were made by redrawing one picture with new hair; faint grey traces of
the old outlines stayed in the skin and the hair, and at full screen they read as seams, as if the hair had been cut out and
moved on its own. In a flat-painted drawing a pixel is either ink, or one of a few flat paints, or the soft edge between them.
A ghost is none of these: lighter than ink, darker than the paint it lies in, and thin. Where the paint around a pixel is skin
or hair and the pixel strays from it without being ink, it takes the paint's colour. Ink, eyes, the bow and edges stay.

Usage: clean_ghosts.py IN.png OUT.png [--debug DBG.png]
"""
import sys

import cv2
import numpy as np


def clean(rgba):
    rgb = rgba[..., :3].astype(np.float32) / 255
    a = rgba[..., 3].astype(np.float32) / 255
    lum = rgb @ np.array([0.3, 0.59, 0.11], np.float32)
    ink = lum < 0.30
    near_ink = cv2.dilate(ink.astype(np.uint8), np.ones((5, 5), np.uint8)) > 0
    med = cv2.medianBlur((rgb * 255).astype(np.uint8), 9).astype(np.float32) / 255
    r, g, b = med[..., 0], med[..., 1], med[..., 2]
    skin = (r > 0.85) & (g > 0.78) & (b > 0.68) & (r - b < 0.25)
    hair = (r > 0.80) & (g > 0.62) & (b < 0.55) & (r - b > 0.30)
    paint = (skin | hair) & (a > 0.99)
    dev = np.abs(rgb - med).max(-1)
    darker = (med @ np.array([0.3, 0.59, 0.11], np.float32)) - lum
    # strays of any kind, and the faintest traces too as long as they are darker than the paint (a ghost line always is)
    ghost = paint & ~near_ink & (lum > 0.30) & ((dev > 0.035) | (darker > 0.012))
    # a ghost is a line: keep only thin things, never a whole flat area that just happens to differ from the median
    ghost = cv2.morphologyEx(ghost.astype(np.uint8), cv2.MORPH_OPEN, np.ones((1, 1), np.uint8)) > 0
    grow = cv2.dilate(ghost.astype(np.uint8), np.ones((3, 3), np.uint8)) > 0
    grow &= paint & ~near_ink
    out = rgba.copy()
    out[..., :3][grow] = (med[grow] * 255 + 0.5).astype(np.uint8)
    return out, grow


if __name__ == "__main__":
    src, dst = sys.argv[1], sys.argv[2]
    im = cv2.imread(src, cv2.IMREAD_UNCHANGED)
    rgba = np.dstack([im[..., 2], im[..., 1], im[..., 0], im[..., 3]])
    out, m = clean(rgba)
    cv2.imwrite(dst, out[..., [2, 1, 0, 3]])
    if "--debug" in sys.argv:
        cv2.imwrite(sys.argv[sys.argv.index("--debug") + 1], (m * 255).astype(np.uint8))
    print(dst, int(m.sum()), "pixels repainted")
