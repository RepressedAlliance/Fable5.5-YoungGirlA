"""Enlarge flat ink-and-paint art without changing a shape and without halos.

Root cause this replaces (docs/问题根因清单.md, "主视觉丑"): shots that push in past the picture's own resolution used cubic
enlargement plus unsharp mask, which draws a white ring round every ink line. Here each edge pixel is pushed towards the two
colours it is a mix of, the local min and max, so nothing can overshoot them: the line stays where it was, just crisp.
Use this for any picture shown bigger than about 1.5 times its own pixels.
"""
import cv2
import numpy as np


def upscale(rgba, k=3, tile=384, margin=24):
    """rgba: float straight alpha in 0..1. Returns uint8 straight alpha, k times the size. Works in tiles, so memory stays small."""
    h, w = rgba.shape[:2]
    out = np.empty((h * k, w * k, 4), np.uint8)
    for y in range(0, h, tile):
        for x in range(0, w, tile):
            y0, y1, x0, x1 = max(0, y - margin), min(h, y + tile + margin), max(0, x - margin), min(w, x + tile + margin)
            big = _upscale(rgba[y0:y1, x0:x1], k)
            yy, xx = (y - y0) * k, (x - x0) * k
            hh, ww = (min(h, y + tile) - y) * k, (min(w, x + tile) - x) * k
            out[y * k:y * k + hh, x * k:x * k + ww] = (np.clip(big[yy:yy + hh, xx:xx + ww], 0, 1) * 255 + 0.5).astype(np.uint8)
    return out


def _upscale(rgba, k, gain=3.2, floor=0.05):
    pre = np.dstack([rgba[..., :3] * rgba[..., 3:4], rgba[..., 3]]).astype(np.float32)
    big = cv2.resize(pre, None, fx=k, fy=k, interpolation=cv2.INTER_CUBIC)
    big = cv2.GaussianBlur(np.clip(big, 0, 1), (0, 0), k * 0.42)   # rounds off the source pixels' stair-steps
    r = max(1, int(round(k * 1.4)))
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * r + 1, 2 * r + 1))
    lo = cv2.erode(big, kernel)
    hi = cv2.dilate(big, kernel)
    span = hi - lo
    t = (big - lo) / np.maximum(span, 1e-4)
    sharp = lo + span * np.clip((t - 0.5) * gain + 0.5, 0, 1)
    # flat paint keeps its own values: only real edges are touched
    # and so does paint merely near a line: only the pixels really inside the transition move, or round marks show around line ends
    edge = np.clip(span / floor - 1, 0, 1) * (1 - np.clip((np.abs(t - 0.5) - 0.30) / 0.15, 0, 1))
    out = big * (1 - edge) + sharp * edge
    a = np.clip(out[..., 3:4], 0, 1)
    rgb = np.clip(out[..., :3] / np.maximum(a, 1e-3), 0, 1)
    return np.dstack([_clear_rings(rgb, rgba, k), a]).astype(np.float32)


def _clear_rings(rgb, src, k):
    """Generated pictures carry their own faint pale ring beside ink lines: near ink, paint a bit lighter than its surroundings goes back to them."""
    paint = cv2.medianBlur((np.clip(src[..., :3], 0, 1) * 255 + 0.5).astype(np.uint8), 15)
    paint = cv2.resize(paint.astype(np.float32) / 255, (rgb.shape[1], rgb.shape[0]), interpolation=cv2.INTER_LINEAR)
    ink = (rgb.mean(-1) < 0.30).astype(np.uint8)
    near = cv2.dilate(ink, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (8 * k + 1, 8 * k + 1))).astype(np.float32)
    near = cv2.GaussianBlur(near, (0, 0), 1.5 * k)
    d = (rgb - paint).max(-1)
    w = (np.clip(d / 0.008, 0, 1) * np.clip((0.13 - d) / 0.04, 0, 1) * near)[..., None].astype(np.float32)
    return rgb * (1 - w) + paint * w
