"""Final clean-up of a painted iris: tones become flat shapes on the official colours with smooth hard edges,
highlights get one clean edge. What was painterly in the source becomes confident cel paint.

usage: eye_clean.py in.png out.png [--tones 7]   (input is the magnified 1536x1024 eye region)
"""
import argparse

import cv2
import numpy as np

PALETTE = ["#06262F", "#0B4A58", "#07647A", "#048396", "#218EA3", "#3FA5B8", "#5BB8CA", "#8AD3DC", "#B0E8EA"]


def hexrgb(h):
    h = h.lstrip("#")
    return np.array([int(h[i:i + 2], 16) for i in (0, 2, 4)], np.float32) / 255


def clean(bgr, tones_smooth=9.0, white_cut=0.80):
    src = bgr[..., ::-1].astype(np.float32) / 255
    # teal-ish pixels are the irises; everything else passes through untouched
    r, g, b = src[..., 0], src[..., 1], src[..., 2]
    iris = (g > r + 0.05) & (b > r + 0.05)
    white = src.min(-1) > white_cut
    region = cv2.morphologyEx((iris | white).astype(np.uint8), cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8)) > 0
    # the highlights: blur and threshold gives one clean continuous edge
    w = (src.min(-1) > white_cut).astype(np.float32)
    w = cv2.GaussianBlur(w, (0, 0), 2.4)
    w_mask = np.clip((w - 0.5) * 6 + 0.5, 0, 1)
    # the tones: remove the highlights, smooth away mottling while keeping shapes, then snap to the palette
    inp = cv2.inpaint(bgr, cv2.dilate((src.min(-1) > 0.62).astype(np.uint8), np.ones((9, 9), np.uint8)), 9, cv2.INPAINT_TELEA)
    smooth = cv2.pyrMeanShiftFiltering(inp, 18, 26, maxLevel=2)
    smooth = cv2.GaussianBlur(smooth, (0, 0), tones_smooth * 0.35)[..., ::-1].astype(np.float32) / 255
    pal = np.stack([hexrgb(p) for p in PALETTE])
    v = smooth.mean(-1)
    vp = pal.mean(-1)
    edges = (vp[1:] + vp[:-1]) / 2
    # soft boundary that resolves to a crisp line after the downscale to picture size
    out = np.zeros_like(src)
    idx = np.digitize(v, edges)
    flat = pal[idx]
    # smooth the region map so tone boundaries are clean curves, not stair-steps
    layers = []
    for i in range(len(pal)):
        m = cv2.GaussianBlur((idx == i).astype(np.float32), (0, 0), 3.2)
        layers.append(m)
    layers = np.stack(layers, -1)
    pick = layers.argmax(-1)
    flat = pal[pick]
    res = src.copy()
    res = np.where(region[..., None], flat, res)
    res = res * (1 - w_mask[..., None]) + np.array([1, 1, 1], np.float32) * w_mask[..., None] * region[..., None] + res * 0
    res = np.where(region[..., None], res, src)
    return (np.clip(res, 0, 1)[..., ::-1] * 255 + 0.5).astype(np.uint8)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("input")
    ap.add_argument("output")
    a = ap.parse_args()
    cv2.imwrite(a.output, clean(cv2.imread(a.input)))
    print("ok", a.output)
