"""Second tone for the flat close-ups, painted by rule: hair casts one hard shadow on the skin below it,
and the bottoms of the hair's own clumps take one hard darker tone. No gradients are added anywhere.
Masks are smoothed before they are thresholded, so edges are clean curves at any size."""
import cv2
import numpy as np


def tone(hex_color):
    h = hex_color.lstrip("#")
    return np.array([int(h[i:i + 2], 16) for i in (0, 2, 4)], np.float32) / 255


def near(rgb, hex_color, tol):
    return np.abs(rgb - tone(hex_color)).max(-1) < tol


def _clean(mask, sigma):
    m = cv2.GaussianBlur(mask.astype(np.float32), (0, 0), sigma)
    return np.clip((m - 0.5) * sigma * 2.2 + 0.5, 0, 1)


def add_cel(rgba, drop=30, hair_inset=26, skin_shadow="#F3CDB6", hair_shadow="#EDBB34"):
    """rgba float image. `drop`: how far the hair's shadow falls on the skin, in pixels."""
    rgb = rgba[..., :3]
    a = rgba[..., 3]
    skin = near(rgb, "#FDE8DA", 0.075) & (a > 0.9)
    hair = near(rgb, "#FEDB52", 0.10) & (a > 0.9)
    hu = cv2.morphologyEx(hair.astype(np.uint8), cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8))
    # never paint over ink: the ink's own soft edge decides where the tone stops
    lum = rgb.mean(-1)
    not_ink = np.clip((lum - 0.22) / 0.30, 0, 1)
    # shadow on the skin: the hair silhouette moved down and a touch to the side
    M = np.float32([[1, 0, drop * 0.25], [0, 1, drop]])
    moved = cv2.warpAffine(hu, M, (hu.shape[1], hu.shape[0])) > 0
    cast = _clean(cv2.morphologyEx((moved & skin).astype(np.uint8), cv2.MORPH_OPEN, np.ones((7, 7), np.uint8)), 2.2)
    out = rgba.copy()
    k = (cast * not_ink)[..., None]
    out[..., :3] = out[..., :3] * (1 - k) + tone(skin_shadow) * k
    # the lower part of every clump
    M2 = np.float32([[1, 0, 0], [0, 1, -hair_inset]])
    up = cv2.warpAffine(hu, M2, (hu.shape[1], hu.shape[0])) > 0
    low = cv2.morphologyEx((hair & ~up).astype(np.uint8), cv2.MORPH_OPEN, np.ones((5, 5), np.uint8))
    low = _clean(low, 2.2)
    k = (low * not_ink)[..., None]
    out[..., :3] = out[..., :3] * (1 - k) + tone(hair_shadow) * k
    return out
