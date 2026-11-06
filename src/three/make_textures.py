"""Painted textures for the 3D scenes: flat tones with hard-edged marks, no photographic detail."""
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "assets" / "tex"
OUT.mkdir(parents=True, exist_ok=True)


def hexrgb(h):
    h = h.lstrip("#")
    return np.array([int(h[i:i + 2], 16) for i in (0, 2, 4)], np.float32)


def save(name, rgb):
    cv2.imwrite(str(OUT / name), cv2.cvtColor(np.clip(rgb, 0, 255).astype(np.uint8), cv2.COLOR_RGB2BGR))


def blotch(h, w, cell, seed):
    r = np.random.default_rng(seed)
    g = r.random((h // cell + 2, w // cell + 2), dtype=np.float32)
    return cv2.resize(g, (w, h), interpolation=cv2.INTER_CUBIC)


def floor():
    """Long boards with hand-ruled seams: 2.4 m of floor per tile across the width."""
    h, w = 2048, 2048
    r = np.random.default_rng(1)
    img = np.ones((h, w, 3), np.float32) * hexrgb("#B98B5C")
    nb = 26
    bw = w / nb
    for i in range(nb):
        x0, x1 = int(i * bw), int((i + 1) * bw)
        tone = hexrgb("#B98B5C") * (0.94 + 0.12 * r.random())
        img[:, x0:x1] = tone
        y = int(r.random() * h)
        L = int(h * (0.45 + 0.4 * r.random()))
        for seg in range(4):
            yy = (y + seg * L) % h
            img[yy:yy + 3, x0:x1] = hexrgb("#7B5A38")
            t2 = hexrgb("#B98B5C") * (0.94 + 0.12 * r.random())
            img[yy + 3:min(h, yy + L), x0:x1] = t2
        img[:, x0:x0 + 3] = hexrgb("#7B5A38")
    # scuffs: hard-edged worn patches down the aisles
    m = blotch(h, w, 150, 2) * 0.7 + blotch(h, w, 40, 3) * 0.3
    img = np.where((m > 0.66)[..., None], img * 1.07, img)
    save("floor.png", img)


def wall():
    h, w = 1024, 2048
    img = np.ones((h, w, 3), np.float32) * hexrgb("#F2ECD9")
    save("wall.png", img)


def desktop():
    h, w = 512, 720
    r = np.random.default_rng(7)
    img = np.ones((h, w, 3), np.float32) * hexrgb("#E5B56E")
    for _ in range(9):
        y = int(r.random() * h)
        pts = []
        for x in np.linspace(0, w, 9):
            pts.append([x, y + 8 * np.sin(x * 0.012 + r.random())])
        cv2.polylines(img, [np.int32(pts)], False, tuple(float(v) for v in hexrgb("#C9975A")), 2, cv2.LINE_AA)
    save("desktop.png", img)


def board():
    """Wiped blackboard: long hard-edged eraser sweeps and the date left in the corner by hand."""
    h, w = 1024, 3840
    r = np.random.default_rng(8)
    img = np.ones((h, w, 3), np.float32) * hexrgb("#2F5B4C")
    for _ in range(26):
        y0 = int(r.random() * h)
        x0 = int(r.random() * w)
        L = int(600 + r.random() * 1400)
        th = int(30 + r.random() * 70)
        ov = img.copy()
        cv2.line(ov, (x0, y0), (x0 + L, y0 + int((r.random() - 0.5) * 80)), tuple(float(v) for v in hexrgb("#3A6858")), th, cv2.LINE_AA)
        img = img * 0.5 + ov * 0.5
    save("board.png", img)


def sky():
    h, w = 1024, 2048
    img = np.ones((h, w, 3), np.float32) * hexrgb("#83CDEB")
    m = blotch(h, w, 60, 11) * 0.7 + blotch(h, w, 18, 12) * 0.3
    vert = np.linspace(0, 1, h, dtype=np.float32)[:, None]
    # hard banded clouds in two tones, thicker low down
    th = 0.72 - vert * 0.25
    img = np.where((m > th)[..., None], hexrgb("#F4F2E7"), img)
    img = np.where((m > th + 0.09)[..., None], hexrgb("#D5E5E6"), img)
    # distant roof line painted at the bottom
    base = int(h * 0.52)
    img[base:] = hexrgb("#6E8C8C")
    x = 0
    r = np.random.default_rng(13)
    while x < w:
        bw = int(10 + r.random() * 30)
        bh = int(3 + r.random() * 26)
        tone = hexrgb("#6E8C8C") * (0.92 + 0.14 * r.random())
        img[base - bh:base, x:x + bw] = tone
        x += bw
    save("sky.png", img)


if __name__ == "__main__":
    floor()
    wall()
    desktop()
    board()
    sky()
    print("textures written to", OUT)
