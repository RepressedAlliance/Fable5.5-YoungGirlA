"""Rain drawn as ink: three layers of lines redrawn at 12 fps, and hard rings on the wet ground.

No fading and no blur. A layer is a fresh set of strokes every 12th of a second, so it reads as hand-drawn rain.
"""
import math

import cv2
import numpy as np

# far, middle, near: count at full rain, stroke length in px, width in px at 1080p
LAYERS = ((340, 46, 1), (150, 110, 2), (44, 250, 4))
INK = np.array((0.075, 0.075, 0.095), np.float32)
PALE = np.array((0.74, 0.84, 0.94), np.float32)
TONE = (0.42, 0.70, 1.0)     # strength per layer: the far ones sit back, nothing is ever soft


def tick(t):
    return int(math.floor(t * 12 + 1e-6))


def layer_mask(t, layer, density=1.0, slant=0.19, size=(1920, 1080), seed=11):
    """A uint8 mask of one layer at this 12 fps tick. Drawn at 2x and reduced, so widths can be 1, 2, 4 and stay clean."""
    w, h = size
    n, ln, wd = LAYERS[layer]
    rng = np.random.default_rng(seed * 1000 + layer * 100003 + tick(t) * 7)
    count = int(n * density)
    m = np.zeros((h * 2, w * 2), np.uint8)
    xs = rng.uniform(-0.1 * w, 1.1 * w, count)
    ys = rng.uniform(-0.1 * h, 1.05 * h, count)
    ls = ln * rng.uniform(0.7, 1.25, count)
    for x, y, l in zip(xs, ys, ls):
        p0 = (int(x * 2), int(y * 2))
        p1 = (int((x - slant * l) * 2), int((y + l) * 2))
        cv2.line(m, p0, p1, 255, wd * 2 - (0 if wd > 1 else 0), cv2.LINE_8)
    return cv2.resize(m, (w, h), interpolation=cv2.INTER_AREA)


def apply_rain(rgb, t, densities=(1.0, 1.0, 1.0), slant=0.19, mask=None, seed=11, base=None):
    """Over light things the rain is ink. Over the dark it turns to pale lines, or it would vanish.
    base: judge light and dark on this picture, so a line does not flicker to pale where it crosses a ring."""
    out = rgb
    h, w = rgb.shape[:2]
    for i, d in enumerate(densities):
        if d <= 0:
            continue
        m = layer_mask(t, i, d, slant, (w, h), seed).astype(np.float32)[..., None] / 255.0
        if mask is not None:
            m = m * mask
        lum = (out if base is None else base).mean(-1, keepdims=True)
        col = np.where(lum < 0.30, PALE, INK).astype(np.float32)
        k = m * TONE[i]
        out = out * (1 - k) + col * k
    return out


def rings(t, x_range, y_range, z, density=1.0, seed=3):
    """Splash rings on the ground: (x, y, z, radius m, line index). Each lives about half a second, growing in 12 fps steps."""
    tk = tick(t)
    out = []
    life = 6
    n = int(42 * (x_range[1] - x_range[0]) * (y_range[1] - y_range[0]) / 24 * density)
    for birth in range(tk - life + 1, tk + 1):
        if birth < 0:
            continue
        rng = np.random.default_rng(seed + birth * 31)
        for _ in range(n // life + 1):
            x, y = rng.uniform(*x_range), rng.uniform(*y_range)
            age = tk - birth
            r0 = rng.uniform(0.16, 0.30)
            out.append((x, y, z, r0 * (age + 1) / life, age, life))
    return out


def draw_rings(rgb, rs, project, seg=28, width_near=3.0, mask=None):
    """Project each ring and draw it hard: a thin ellipse of ink, a second ring inside once it has grown.
    mask (h, w, 1): rings exist only where it is 1, so a pillar in front of the ground hides them."""
    h, w = rgb.shape[:2]
    m = np.zeros((h * 2, w * 2), np.uint8)
    for x, y, z, r, age, life in rs:
        loops = [r] + ([r * 0.55] if age >= 2 else [])
        for rr in loops:
            pts = []
            ok = True
            for k in range(seg):
                a = 2 * math.pi * k / seg
                p = project((x + rr * math.cos(a), y + rr * math.sin(a), z))
                if p is None:
                    ok = False
                    break
                pts.append((p[0] * 2, p[1] * 2))
            if not ok:
                continue
            pts = np.array(pts, np.int32).reshape(-1, 1, 2)
            if pts[..., 1].max() < 0 or pts[..., 1].min() > h * 2 or pts[..., 0].max() < 0 or pts[..., 0].min() > w * 2:
                continue
            th = max(1, int(round(width_near * 2 * (1 - age / life * 0.6))))
            cv2.polylines(m, [pts], True, 255, th, cv2.LINE_8)
    k = cv2.resize(m, (w, h), interpolation=cv2.INTER_AREA).astype(np.float32)[..., None] / 255.0
    if mask is not None:
        k = k * mask
    lum = rgb.mean(-1, keepdims=True)
    col = np.where(lum < 0.30, PALE, INK).astype(np.float32)
    return rgb * (1 - k) + col * k
