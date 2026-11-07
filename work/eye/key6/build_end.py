"""Registers Codex's pictures on the master and writes assets/gen/end. Nothing here draws her: every pixel comes out of a Codex picture; code only aligns, cuts and composites."""
import json
import sys
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[3]
sys.path[:0] = [str(ROOT / "src" / "art")]
import cutout as C  # noqa: E402

G = ROOT / "work" / "eye" / "key6" / "end"
OUT = ROOT / "assets" / "gen" / "end"
OUT.mkdir(exist_ok=True)
QC = G / "qc"
QC.mkdir(exist_ok=True)

# what is on the master where
FACE_C = (455.0, 700.0)        # the point between her eyes
EYE_BOX = {"l": (258, 628, 412, 770), "r": (498, 628, 652, 770)}   # the two eyes, with room around them
MOUTH_BOX = (405, 830, 505, 875)


def load_bgr(name):
    return cv2.imread(str(G / f"{name}.png") if not name.startswith("/") else name)


def gray(bgr):
    return cv2.GaussianBlur(cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY), (0, 0), 1.2).astype(np.float32) / 255


def not_green(bgr):
    return (bgr[..., 1].astype(int) - np.maximum(bgr[..., 0], bgr[..., 2]).astype(int) < 60).astype(np.uint8)


def register(bgr, ref, mask, motion=cv2.MOTION_AFFINE, init=None):
    """Warp matrix that puts bgr on ref, judged only inside mask. ECC on smoothed lines, coarse to fine."""
    w = np.eye(2, 3, dtype=np.float32) if init is None else init.copy()
    a, b = gray(ref), gray(bgr)
    m = (mask > 0).astype(np.uint8)
    crit = (cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 200, 1e-6)
    try:
        _, w = cv2.findTransformECC(a, b, w, motion, crit, m, 5)
    except cv2.error as e:
        print("ECC failed", e)
    return w


def warp(img, w, shape):
    return cv2.warpAffine(img, w, (shape[1], shape[0]), flags=cv2.INTER_CUBIC | cv2.WARP_INVERSE_MAP, borderMode=cv2.BORDER_REPLICATE)


def box_mask(shape, box):
    m = np.zeros(shape[:2], np.uint8)
    m[box[1]:box[3], box[0]:box[2]] = 1
    return m


def skin_of(bgr, box):
    x0, y0, x1, y1 = box
    roi = bgr[y0:y1, x0:x1].reshape(-1, 3).astype(np.float32)
    lum = roi.mean(1)
    # the skin is the commonest light colour with red above blue
    sk = roi[(roi[:, 2] > roi[:, 0] + 12) & (lum > 190)]
    return np.median(sk, axis=0)


def save_rgba(name, rgba):
    cv2.imwrite(str(OUT / f"{name}.png"), (np.clip(rgba[..., [2, 1, 0, 3]], 0, 1) * 255 + 0.5).astype(np.uint8))


def colour_fit(src, ref, mask):
    """Per channel, a straight line from src's flat colours to ref's, judged where the two pictures agree. Codex's flats differ by a few levels."""
    out = src.astype(np.float32).copy()
    for ch in range(3):
        a, b = src[..., ch][mask > 0].astype(np.float32), ref[..., ch][mask > 0].astype(np.float32)
        k, c = np.polyfit(a[::7], b[::7], 1)
        out[..., ch] = out[..., ch] * k + c
    return np.clip(out, 0, 255)


def lay(base, src, mask, sigma=1.6):
    """src over base through a mask, softened only enough to hide the pixel stairs."""
    a = cv2.GaussianBlur(mask.astype(np.float32), (0, 0), sigma)[..., None]
    return base.astype(np.float32) * (1 - a) + src.astype(np.float32) * a


def ellipse_mask(shape, c, ax, ang=0):
    m = np.zeros(shape[:2], np.uint8)
    cv2.ellipse(m, (int(c[0]), int(c[1])), (int(ax[0]), int(ax[1])), ang, 0, 360, 1, -1)
    return m


def patch_rgba(name, src_bgr, mask, sigma=1.6):
    """A piece of a Codex picture, in master coordinates, as an RGBA file and its corner."""
    a = cv2.GaussianBlur(mask.astype(np.float32), (0, 0), sigma)
    ys, xs = np.nonzero(a > 0.002)
    x0, x1, y0, y1 = int(xs.min()), int(xs.max()) + 1, int(ys.min()), int(ys.max()) + 1
    rgba = np.dstack([src_bgr[y0:y1, x0:x1][..., ::-1].astype(np.float32) / 255, a[y0:y1, x0:x1]])
    save_rgba(name, rgba)
    return [x0, y0]


def changed_from(a, b, tol=4, thr=42):
    """Where picture a holds something b has nowhere near: a line moved by under tol pixels does not count."""
    k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * tol + 1, 2 * tol + 1))
    lo, hi = cv2.erode(b, k).astype(np.int16), cv2.dilate(b, k).astype(np.int16)
    a_ = a.astype(np.int16)
    over = np.maximum(a_ - hi, lo - a_).max(-1)
    lo2, hi2 = cv2.erode(a, k).astype(np.int16), cv2.dilate(a, k).astype(np.int16)
    b_ = b.astype(np.int16)
    over2 = np.maximum(b_ - hi2, lo2 - b_).max(-1)
    return ((over > thr) | (over2 > thr)).astype(np.uint8)


def build_close(picks):
    """The close-up's lids: Codex's redrawing of p05 with her eyes lowered, registered on p05, and only the eyes kept."""
    raw = cv2.imread(str(ROOT / "assets/gen/raw/p05_face_close.png"))
    head = ellipse_mask(raw.shape, (768, 620), (400, 390))
    eyes_only = ellipse_mask(raw.shape, picks["close_c"]["l"], picks["close_ax"]) | ellipse_mask(raw.shape, picks["close_c"]["r"], picks["close_ax"])
    calib = head & (1 - cv2.dilate(eyes_only, np.ones((9, 9), np.uint8)))
    for st, name in picks["close"].items():
        im = load_bgr(name)
        w = register(im, raw, calib)
        print("close", st, np.round(w, 4).tolist())
        out = warp(im, w, raw.shape)
        out = colour_fit(out, raw, calib)
        a = cv2.GaussianBlur(eyes_only.astype(np.float32), (0, 0), 1.6)
        save_rgba(f"close_{st}", np.dstack([out[..., ::-1] / 255, a]))


def align(name, M, head):
    """A wind drawing put on the master: one affine for the head, then a smooth correction taken only from the lines the two pictures share, so the lines that have not moved lie exactly on the master's."""
    im = load_bgr(name)
    w = register(im, M, head)
    first = np.clip(warp(im, w, M.shape), 0, 255).astype(np.uint8)
    g0, g1 = cv2.cvtColor(M, cv2.COLOR_BGR2GRAY), cv2.cvtColor(first, cv2.COLOR_BGR2GRAY)
    flow = cv2.DISOpticalFlow_create(cv2.DISOPTICAL_FLOW_PRESET_MEDIUM).calc(g0, g1, None)
    same = 1 - cv2.dilate(changed_from(first, M, 7, 42), np.ones((15, 15), np.uint8))
    gx, gy = cv2.Sobel(g0, cv2.CV_32F, 1, 0), cv2.Sobel(g0, cv2.CV_32F, 0, 1)
    conf = ((np.hypot(gx, gy) > 60) & (same > 0)).astype(np.float32)
    # a smooth low-order correction: it can bring whole lines onto the master's, and it cannot make a line wobble
    yy, xx = np.mgrid[0:M.shape[0], 0:M.shape[1]].astype(np.float32)
    H_, W_ = M.shape[:2]

    def basis(x, y):
        u, v = x / W_ - 0.5, y / H_ - 0.5
        return np.stack([np.ones_like(u), u, v, u * u, u * v, v * v, u * u * u, u * u * v, u * v * v, v * v * v], -1)
    ys, xs = np.nonzero(conf)
    pick = np.random.default_rng(1).permutation(len(ys))[:60000]
    ys, xs = ys[pick], xs[pick]
    B = basis(xs.astype(np.float32), ys.astype(np.float32))
    fit = []
    for ch in range(2):
        y_ = flow[ys, xs, ch]
        keep = np.abs(y_) < 8
        for _ in range(4):
            c, *_ = np.linalg.lstsq(B[keep], y_[keep], rcond=None)
            r = y_ - B @ c
            keep = np.abs(r) < max(1.0, 2.0 * np.median(np.abs(r[keep])))
        fit.append(c)
    all_ = basis(xx, yy)
    fx, fy = (all_ @ fit[0]).astype(np.float32), (all_ @ fit[1]).astype(np.float32)
    del all_
    x1, y1 = xx + fx, yy + fy
    mx = w[0, 0] * x1 + w[0, 1] * y1 + w[0, 2]
    my = w[1, 0] * x1 + w[1, 1] * y1 + w[1, 2]
    return np.clip(cv2.remap(im, mx, my, cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE), 0, 255).astype(np.uint8)


def eye_shape(bgr, c, ax):
    """The eye and its lashes as a shape: everything in its oval that is neither skin nor hair, joined up round the iris, with a little skin round it. So a lock of hair near her eye is left to the drawing."""
    oval = ellipse_mask(bgr.shape, c, ax)
    b, g, r = [bgr[..., i].astype(int) for i in range(3)]
    skin = (r > 225) & (g > 200) & (b > 190) & (r - b > 12)
    hair = (r > 200) & (g > 150) & (b < 150)
    m = (oval > 0) & ~skin & ~hair
    n, lab = cv2.connectedComponents(m.astype(np.uint8), connectivity=8)
    keep = lab == lab[int(c[1]), int(c[0])]
    # the eye's small crease lines stand apart from it: anything near enough belongs to the eye, but not what reaches the edge of the oval through hair
    near = cv2.dilate(keep.astype(np.uint8), cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (17, 17))) > 0
    for i in range(1, n):
        comp = lab == i
        if comp[near].any() and comp.sum() < 700:
            keep |= comp
    return cv2.dilate(keep.astype(np.uint8), cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (13, 13))) & oval


def clean_mask(ch):
    """What the wind has moved, as whole shapes: no specks, no holes, so a piece of hair is never part one drawing and part another."""
    k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (31, 31))
    m = cv2.morphologyEx(ch, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, k)
    n, lab, st, _ = cv2.connectedComponentsWithStats(m, connectivity=8)
    for i in range(1, n):
        if st[i, 4] < 1500:
            m[lab == i] = 0
    cs, _ = cv2.findContours(m, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    out = np.zeros_like(m)
    cv2.drawContours(out, cs, -1, 1, -1)
    return out


def main(picks):
    M = cv2.imread(str(ROOT / "work/eye/key6/cand_c2.png"))
    H, W = M.shape[:2]
    head = ellipse_mask(M.shape, (455, 720), (240, 250))
    fg = not_green(M)
    calib = head & fg

    def reg(name, mask=head):
        im = load_bgr(name)
        w = register(im, M, mask)
        out = warp(im, w, M.shape)
        return np.clip(out, 0, 255).astype(np.uint8)

    def fit(im, mask=None):
        return im.astype(np.float32)

    eye_l, eye_r = picks["eye_c"]["l"], picks["eye_c"]["r"]
    ax = picks["eye_ax"]
    eyes = ellipse_mask(M.shape, eye_l, ax) | ellipse_mask(M.shape, eye_r, ax)
    # the face of the film: the master, with the irises that continue the close-up's. No white in them yet
    nohl = fit(reg(picks["nohl"]))
    base = lay(M, nohl, eyes)
    layout = {"centre": list(FACE_C), "patches": {}, "wind": [], "loop": [], "strike": {}}
    # ---- eyes shut, half open; the mouth before the smile
    def skin_match(im, mask):
        """Codex's skin differs by a level or two: the piece is shifted to the master's skin, measured in the ring round it."""
        ring = cv2.dilate(mask, np.ones((9, 9), np.uint8)) - cv2.erode(mask, np.ones((9, 9), np.uint8))
        light = (M.mean(-1) > 200) & (im.mean(-1) > 200) & (ring > 0)
        return np.clip(im.astype(np.float32) + (np.median(M[light], axis=0) - np.median(im[light], axis=0)), 0, 255)

    base = lay(M, skin_match(nohl, eyes), eyes)
    states = {key: reg(name) for key, name in (("closed", picks["closed"]), ("half", picks["half"]))}

    def hair_of(bgr):
        b, g, r = [bgr[..., i].astype(int) for i in range(3)]
        m = ((r > 200) & (g > 150) & (b < 150)).astype(np.uint8)
        return cv2.dilate(cv2.morphologyEx(m, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8)), cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (19, 19)))
    mouth = ellipse_mask(M.shape, picks["mouth_c"], picks["mouth_ax"])
    for key, name in (("mouth_flat", picks["flat"]), ("mouth_mid", picks["mid"])):
        im = reg(name)
        layout["patches"][key] = patch_rgba(key, skin_match(im, mouth), mouth)
    # ---- the white in the eyes: out of the lit picture, stroke, dot and flecks, each its own layer. Stroke cumulative by where the brush has got to
    lit = fit(reg(picks["lit"]))
    nb = np.clip(base, 0, 255).astype(np.uint8)
    # lit is laid on the no-white iris of the same eye: each eye registered on it by its lash and iris outline
    lit_a = np.zeros((H, W), np.float32)
    white = np.clip((lit.min(-1) - 150) / 80, 0, 1)
    teal = ((nb[..., 0].astype(int) > nb[..., 2].astype(int) + 20)).astype(np.uint8)     # blue over red: the iris. BGR
    stroke = [np.zeros((H, W), np.float32) for _ in range(3)]
    dot = np.zeros((H, W), np.float32)
    flecks = [np.zeros((H, W), np.float32) for _ in range(3)]
    for c_ in (eye_l, eye_r):
        box = ellipse_mask(M.shape, c_, ax)
        n, lab, st, _ = cv2.connectedComponentsWithStats(cv2.morphologyEx(teal & box, cv2.MORPH_CLOSE, np.ones((25, 25), np.uint8)))
        big = 1 + int(np.argmax(st[1:, 4]))
        iris = cv2.erode((lab == big).astype(np.uint8), np.ones((5, 5), np.uint8))
        w_ = (white * iris)
        n, lab, st, cen = cv2.connectedComponentsWithStats((w_ > 0.5).astype(np.uint8), connectivity=8)
        comps = sorted(range(1, n), key=lambda i: -st[i, 4])
        print("white marks", [(int(st[i, 4]), [int(v) for v in cen[i]]) for i in comps])
        grow = lambda i: cv2.dilate((lab == i).astype(np.uint8), np.ones((5, 5), np.uint8)) * w_
        m0 = grow(comps[0])
        # the brush lands at the head of the stroke, the highest point, and comes down it
        ys, xs = np.nonzero(lab == comps[0])
        top = np.array([xs[np.argmin(ys)], ys.min()], np.float32)
        yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
        d = np.hypot(xx - top[0], yy - top[1])
        L = float(d[lab == comps[0]].max())
        for i, f in enumerate((0.42, 0.74, 1.05)):
            stroke[i] += m0 * np.clip((f * L - d) / 1.2, 0, 1)
        dot += grow(comps[1])
        for j, i in enumerate(comps[2:]):
            flecks[min(j, 2)] += grow(i)

    def white_patch(key, a):
        ys, xs = np.nonzero(a > 0.004)
        x0, x1, y0, y1 = int(xs.min()), int(xs.max()) + 1, int(ys.min()), int(ys.max()) + 1
        rgba = np.ones((y1 - y0, x1 - x0, 4), np.float32)
        rgba[..., 3] = a[y0:y1, x0:x1]
        save_rgba(key, rgba)
        layout["patches"][key] = [x0, y0]
    for i, a in enumerate(stroke):
        white_patch(f"hl_{i}", a)
    white_patch("hl_dot", dot)
    gl = [["hl_dot", 6]]
    for i, a in enumerate(flecks):
        if a.max() > 0:
            white_patch(f"hl_f{i}", a)
            gl.append([f"hl_f{i}", 8 + 2 * i])
    layout["strike"] = {"stroke": ["hl_0", "hl_1", "hl_2"], "glints": gl}
    # ---- the wind: only what the wind has really moved comes from each drawing; everything else stays the master, so nothing but the wind ever changes
    # her eyes, nose and mouth are the master's in every picture
    tight = picks["eye_tight"]
    face = ellipse_mask(M.shape, (eye_l[0], eye_l[1] + 4), tight) | ellipse_mask(M.shape, (eye_r[0], eye_r[1] + 4), tight) | mouth | ellipse_mask(M.shape, picks["nose_c"], picks["nose_ax"])
    cv2.imwrite(str(QC / "face_keep.png"), face * 255)
    made = {}
    for key, name in picks["wind_files"].items():
        im = align(name, M, head)
        ch = changed_from(im, M, picks.get("tol", 2), 42)
        ch[face > 0] = 0
        grow = cv2.dilate(clean_mask(ch), cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (9, 9)))
        grow[face > 0] = 0
        out = lay(base, im, grow, 1.2)
        rgba = C.cutout(np.clip(out, 0, 255).astype(np.uint8))
        save_rgba(key, rgba)
        cv2.imwrite(str(QC / f"{key}_mask.png"), grow * 255)
        # her eyes shut or half open over this drawing: the hair of this drawing stays in front, and none of the state picture's own hair comes along
        final = np.clip(out, 0, 255).astype(np.uint8)
        for st, sim0 in states.items():
            # the eyes redrawn over this very drawing, when there is one: then her hair and face edge are already the same
            own = picks.get("own", {}).get(f"{st}@{key}")
            sim = reg(own) if own else sim0
            if own:
                # one and the same drawing of the shut eye in every picture, so the line never changes while the wind does
                full = skin_match(sim, eyes)
                full = lay(full, skin_match(sim0, eyes), face & eyes, 1.2)
                layout["patches"][f"eye_{st}@{key}"] = patch_rgba(f"eye_{st}@{key}", full, eyes, 1.2)
                continue
            # nor any line of the drawing beyond the eye itself: the side of her face stays as this drawing has it
            outer = np.zeros((H, W), np.uint8)
            outer[:, :258] = 1
            outer[:, 650:] = 1
            lines = cv2.dilate((((final.max(-1) < 110) | (sim.max(-1) < 110)) & (outer > 0)).astype(np.uint8), np.ones((5, 5), np.uint8))
            mk = eyes & (1 - hair_of(final)) & (1 - hair_of(sim)) & (1 - lines)
            layout["patches"][f"eye_{st}@{key}"] = patch_rgba(f"eye_{st}@{key}", skin_match(sim, eyes), mk, 1.2)
        print("wind", key, name, "taken", round(float(grow.mean()), 3), flush=True)
    layout["wind"] = picks["wind"]
    layout["loop"] = picks["loop"]
    (OUT / "layout.json").write_text(json.dumps(layout, indent=1), encoding="utf-8")


if __name__ == "__main__":
    picks = json.loads((G.parent / "picks.json").read_text(encoding="utf-8"))
    build_close(picks)
    main(picks)
