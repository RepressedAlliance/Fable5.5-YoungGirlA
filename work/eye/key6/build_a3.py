"""Third round of the ending (docs/全片修改清单3.md, group A). Registers Codex's pictures and writes assets/gen/end/{closew_*, lid_*, t_*, layout3.json}. Every pixel of her comes from a Codex picture.
Usage: build_a3.py close | lids | tilt   (picks in work/eye/key6/picks3.json)"""
import importlib.util
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "src" / "clips"), str(ROOT / "src" / "art")]
import cv2  # noqa: E402
import numpy as np  # noqa: E402
import c6  # noqa: E402
import cutout as C  # noqa: E402

spec = importlib.util.spec_from_file_location("build_end", ROOT / "work/eye/key6/build_end.py")
BE = importlib.util.module_from_spec(spec)
spec.loader.exec_module(BE)
G3 = ROOT / "work/eye/key6/end3"
BE.G = G3
_cut0 = C.cutout


def _cut(bgr):
    """As cutout, without the specks a seam can leave out in the empty background."""
    r = _cut0(bgr)
    n, lab, st, _ = cv2.connectedComponentsWithStats((r[..., 3] > 0.03).astype(np.uint8), connectivity=8)
    for i in range(1, n):
        if st[i, 4] < 600:
            r[..., 3][lab == i] = 0
    return r


C.cutout = _cut
OUT = BE.OUT
QC = G3 / "qc"
QC.mkdir(exist_ok=True)
LAYOUT = OUT / "layout3.json"
RAW = ROOT / "assets/gen/raw/p05_face_close.png"
EYES = [(544, 464), (992, 464)]


def layout():
    return json.loads(LAYOUT.read_text(encoding="utf-8")) if LAYOUT.exists() else dict(patches={}, close_lids={}, close_wind=[], wind=[], loop=[])


def save_layout(L):
    LAYOUT.write_text(json.dumps(L, indent=1), encoding="utf-8")


def save_u8(name, rgba_u8):
    cv2.imwrite(str(OUT / f"{name}.png"), rgba_u8[..., [2, 1, 0, 3]])


def close_protect(bgr):
    """Her eyes, nose and mouth in the close-up. They are the same drawing in every picture, so nothing but the hair moves."""
    m = np.zeros(bgr.shape[:2], np.uint8)
    for c_ in EYES:
        m |= BE.eye_shape(bgr, c_, (168, 146))
    m |= BE.ellipse_mask(bgr.shape, (768, 645), (26, 34))
    m |= BE.ellipse_mask(bgr.shape, (768, 778), (76, 24))
    return m


def flat_match(im, ref, mask):
    """Codex's skin differs by a level or two: everything but its green is shifted to the reference's skin, so the eyes sit in it without a seam. A straight fit would disturb the green."""
    ok = (mask > 0) & (ref.mean(-1) > 200) & (im.mean(-1) > 200) & (ref[..., 2].astype(int) > ref[..., 0].astype(int) + 8) & (im[..., 2].astype(int) > im[..., 0].astype(int) + 8)
    d = np.median(ref[ok], axis=0) - np.median(im[ok], axis=0)
    print("  skin shift", d, flush=True)
    g = BE.not_green(im)[..., None].astype(np.float32)
    return np.clip(im.astype(np.float32) + d * g, 0, 255).astype(np.uint8)


def build_close(p):
    raw = cv2.imread(str(RAW))
    face = BE.ellipse_mask(raw.shape, (768, 610), (300, 330))
    prot0 = close_protect(raw)
    calib = face & (1 - cv2.dilate(prot0, np.ones((9, 9), np.uint8)))
    L = layout()
    seq = []
    done = set()
    for key, name, hold in p["close"]:
        seq.append([f"closew_{key}", hold])
        if key in done:
            continue
        done.add(key)
        im = BE.align(name, raw, face)
        im = flat_match(im, raw, calib)
        # all of the drawing is this picture but for her eyes, nose and mouth: then there is no seam where a line passes from one picture to the other
        grow = 1 - prot0
        out = np.clip(BE.lay(raw, im, grow, 1.2), 0, 255).astype(np.uint8)
        cv2.imwrite(str(G3 / f"closew_{key}_green.png"), out)
        cv2.imwrite(str(QC / f"closew_{key}_mask.png"), grow * 255)
        im0, im1, big = c6.paint_close(C.cutout(out))
        save_u8(f"closew_{key}", (big * 255 + 0.5).astype(np.uint8))
        print("close", key, name, round(float(grow.mean()), 3), flush=True)
    L["close_wind"] = [[None, p["close_start"]]] + seq
    save_layout(L)
    # what Codex sees when it lowers her lids on the last of these
    g = cv2.imread(str(G3 / f"closew_{p['lid_base']}_green.png")).astype(np.float32)
    paint = cv2.imread(str(ROOT / "work/eye/key6/ref_p05_paint.png")).astype(np.float32)
    a = cv2.GaussianBlur(prot0.astype(np.float32), (0, 0), 1.0)[..., None]
    cv2.imwrite(str(G3 / "ref_cw_paint.png"), np.clip(g * (1 - a) + paint * a, 0, 255).astype(np.uint8))


def build_lids(p):
    g = cv2.imread(str(G3 / f"closew_{p['lid_base']}_green.png"))
    oval = BE.ellipse_mask(g.shape, (510, 440), (188, 168)) | BE.ellipse_mask(g.shape, (1022, 440), (188, 168))
    # the whole drawing but her eyes: its hair and outlines are what the two pictures share
    calib = BE.not_green(g) & (1 - oval)
    prot = close_protect(g)
    im0, im1, _ = c6.paint_close(C.cutout(g))
    ref = cv2.imread(str(G3 / "ref_cw_paint.png"))
    L = layout()
    for st, name in p["lids"].items():
        im = BE.load_bgr(name)
        w = BE.register(im, g, calib)
        out = flat_match(np.clip(BE.warp(im, w, g.shape), 0, 255).astype(np.uint8), g, calib)
        print("  ", np.round(w, 3).tolist(), flush=True)
        # only her eyes and the skin round them: never her hair, which stays the drawing's own
        hair = lambda q: cv2.dilate(cv2.morphologyEx(((q[..., 2] > 200) & (q[..., 1] > 150) & (q[..., 0] < 150)).astype(np.uint8), cv2.MORPH_OPEN, np.ones((5, 5), np.uint8)), np.ones((9, 9), np.uint8))
        m = oval & (1 - hair(g)) & (1 - hair(out))
        a = cv2.GaussianBlur(m.astype(np.float32), (0, 0), 1.4)
        patch = np.dstack([out[..., ::-1].astype(np.float32) / 255, a])
        up, (x0, y0) = c6.lid_layer(patch, im0, im1)
        save_u8(f"lid_{st}", up)
        L["close_lids"][st] = [x0, y0]
        print("lid", st, name, flush=True)
    save_layout(L)


def tilt_face(T):
    """Where her eyes have gone in the tilted drawing: the two biggest patches of iris."""
    b, g, r = [T[..., i].astype(int) for i in range(3)]
    teal = ((b > r + 35) & (g > r + 25) & (r < 170) & (b < 245)).astype(np.uint8)
    teal = cv2.morphologyEx(teal, cv2.MORPH_CLOSE, np.ones((15, 15), np.uint8))
    n, lab, st, cen = cv2.connectedComponentsWithStats(teal)
    big = sorted(range(1, n), key=lambda i: -st[i, 4])[:2]
    a, b_ = sorted([cen[i] for i in big], key=lambda q: q[0])
    th = math.degrees(math.atan2(b_[1] - a[1], b_[0] - a[0]))
    print("irises", np.round(a), np.round(b_), "tilt", round(th, 2), flush=True)
    return a, b_, th


def build_tilt(p):
    REF = cv2.imread(str(G3 / "ref_wind_g.png"))
    H, W = REF.shape[:2]
    fg = BE.not_green(REF)
    body = np.zeros((H, W), np.uint8)
    body[960:, 60:850] = 1
    body &= fg
    L = layout()

    def on_body(name):
        im = BE.load_bgr(name)
        w = BE.register(im, REF, body)
        return np.clip(BE.warp(im, w, REF.shape), 0, 255).astype(np.uint8)

    def over_ref(im):
        ch = BE.changed_from(im, REF, 3, 42)
        m = cv2.dilate(BE.clean_mask(ch), cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (9, 9)))
        return np.clip(BE.lay(REF, im, m, 1.2), 0, 255).astype(np.uint8), m

    # the tilted drawing whole: a seam between two pictures shows as a step in every line it crosses. It comes in under the blink, its body registered on the upright one
    T = on_body(p["t2"])
    cv2.imwrite(str(G3 / "t2_final.png"), T)
    BE.save_rgba("t_w0", C.cutout(T))
    a, b, th = tilt_face(T)
    mid = (np.array(a) + np.array(b)) / 2
    rad = math.radians(th)
    down = np.array((-math.sin(rad), math.cos(rad)))
    nose_c, mouth_c = mid + down * 92, mid + down * 158

    def rell(c_, ax):
        m_ = np.zeros((H, W), np.uint8)
        cv2.ellipse(m_, (int(c_[0]), int(c_[1])), (int(ax[0]), int(ax[1])), th, 0, 360, 1, -1)
        return m_
    # the eye and its lashes, not the eyebrow above it: the drawing's own eyebrow stays
    up = np.array((math.sin(rad), -math.cos(rad)))
    eyes = rell(np.array(a) - up * 8, (80, 56)) | rell(np.array(b) - up * 8, (80, 56))
    mouth = rell(mouth_c, (50, 22))
    tight = rell(a, (68, 58)) | rell(b, (68, 58))
    face = tight | mouth | rell(nose_c, (14, 18))
    head = rell(mid + down * 20, (240, 250))

    def state(name):
        im = BE.load_bgr(name)
        w = BE.register(im, T, head)
        return np.clip(BE.warp(im, w, T.shape), 0, 255)

    def skin_match(im, mask):
        ring = cv2.dilate(mask, np.ones((9, 9), np.uint8)) - cv2.erode(mask, np.ones((9, 9), np.uint8))
        light = (T.mean(-1) > 200) & (im.mean(-1) > 200) & (ring > 0)
        return np.clip(im.astype(np.float32) + (np.median(T[light], axis=0) - np.median(im[light], axis=0)), 0, 255)
    for key, name, mask in (("t_closed", p["t_closed"], eyes), ("t_half", p["t_half"], eyes), ("t_flat", p["t_flat"], mouth), ("t_mid", p["t_mid"], mouth)):
        L["patches"][key] = BE.patch_rgba(key, skin_match(state(name), mask), mask)
    # the head on its way: shut eyes, flat mouth, whole drawings, the neck, scarf and collar staying put
    for key in ("t1a", "t1b"):
        im = on_body(p[key])
        BE.save_rgba(f"t_{key}", C.cutout(im))
        L[key] = f"t_{key}"
    loop = [["t_w0", p["loop_hold"]]]
    for i, name in enumerate(p["loop"]):
        im = BE.align(name, T, head)
        ch = BE.changed_from(im, T, 2, 42)
        ch[face > 0] = 0
        grow = cv2.dilate(BE.clean_mask(ch), cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (9, 9)))
        grow[face > 0] = 0
        # the seam is wide and lies where the two pictures' lines still agree, so a line passes from one to the other with no step
        out = np.clip(BE.lay(T, im, grow, 2.6), 0, 255).astype(np.uint8)
        BE.save_rgba(f"t_w{i + 1}", C.cutout(out))
        cv2.imwrite(str(QC / f"t_w{i + 1}_mask.png"), grow * 255)
        loop.append([f"t_w{i + 1}", p["loop_hold"]])
        print("loop", name, round(float(grow.mean()), 3), flush=True)
    L["loop"] = loop
    L["wind"] = p["wind"]
    save_layout(L)


if __name__ == "__main__":
    picks = json.loads((ROOT / "work/eye/key6/picks3.json").read_text(encoding="utf-8"))
    for job in sys.argv[1:]:
        dict(close=build_close, lids=build_lids, tilt=build_tilt)[job](picks)
