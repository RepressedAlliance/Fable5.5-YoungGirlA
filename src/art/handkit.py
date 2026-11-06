"""Small helpers for the hand drawings of the last act."""
import numpy as np
import cv2


def extrude(rgba, d, pad=1000, loose=0.0):
    """The sleeve carries on past the picture's edge, along direction d, so its end can never show.
    Returns a bigger picture; the original sits at its top left.
    loose=0 repeats the edge straight on, a rigid board with whatever crossed the edge drawn out into parallel streaks. With loose>0 the
    carried part is plain cloth: the outlines ease apart towards the elbow, by about loose times the sleeve's width over 1000 px,
    the near side more than the far side, and everything inside them is the sleeve's flat paint."""
    H, W = rgba.shape[:2]
    dx, dy = d
    yy, xx = np.mgrid[0:H + pad, 0:W + pad].astype(np.float32)

    def back(x, y):
        # how far back along d until the point is just inside the picture
        return np.maximum(np.maximum(x - (W - 3), 0) / max(dx, 1e-3), np.maximum(y - (H - 3), 0) / max(dy, 1e-3))

    k = back(xx, yy)
    if loose > 0:
        n = np.array([-dy, dx], np.float32) / max(float(np.hypot(dx, dy)), 1e-3)
        q = xx * n[0] + yy * n[1]
        # the sleeve where it crosses the picture's edge
        edge = np.zeros((H, W), bool)
        edge[H - 3, :] = edge[:, W - 3] = True
        edge &= rgba[..., 3] > 0.5
        ey, ex = np.nonzero(edge)
        eq = ex * n[0] + ey * n[1]
        q0, hw = float(eq.min() + eq.max()) / 2, float(eq.max() - eq.min()) / 2
        # flat paint: the commonest bright colour on that edge; ink: how far from each outline the paint starts
        lum = rgba[ey, ex, :3].mean(-1)
        paint = np.median(rgba[ey, ex, :3][lum >= np.percentile(lum, 50)], axis=0).astype(np.float32)
        ink = float(np.mean(lum < 0.35)) * hw
        dist = k * float(np.hypot(dx, dy))
        # starts tangent to the picture's own outline; a long slow drift so the outlines are not ruled
        grow = dist * dist / (dist + 260.0)
        drift = 0.016 * np.sin(dist / 420.0) * dist
        # the near side lets go more than the far side; both meet the picture's own outline where it stops
        scale = np.where(q - q0 - drift > 0, 1 + 1.3 * loose * grow / 1000.0, 1 + 0.7 * loose * grow / 1000.0)
        q_src = q0 + (q - q0 - drift) / scale
        xs, ys = xx + (q_src - q) * n[0], yy + (q_src - q) * n[1]
        mask = k > 0
        xs, ys = np.where(mask, xs, xx), np.where(mask, ys, yy)
        k2 = back(xs, ys)
        out = cv2.remap(rgba, xs - k2 * dx, ys - k2 * dy, cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=(0, 0, 0, 0))
        # inside the outlines nothing but paint; whatever crossed the edge fades out over the first stretch
        inside = np.clip((hw - ink - 3.0 - np.abs(q_src - q0)) / 2.5, 0, 1) * np.clip(dist / 90.0, 0, 1) * mask
        inside = inside[..., None]
        out[..., :3] = out[..., :3] * (1 - inside) + paint * inside
        return out
    sx, sy = xx - k * dx, yy - k * dy
    out = cv2.remap(rgba, sx, sy, cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=(0, 0, 0, 0))
    return out


def silhouette(rgba):
    arr = np.zeros(rgba.shape, np.float32)
    arr[..., 3] = rgba[..., 3]
    return arr


def match_skin(rgba, ref):
    """Same skin as another hand picture, so a hard cut does not change her: each channel's light and shade tones of the
    skin are mapped on to the other picture's."""
    def mask(im):
        return (im[..., 0] > 0.45) & (im[..., 0] - im[..., 2] > 0.07) & (im[..., 3] > 0.5)
    out = rgba.copy()
    m, mr = mask(rgba), mask(ref)
    for i in range(3):
        a0, a1 = np.percentile(rgba[..., i][m], [10, 90])
        b0, b1 = np.percentile(ref[..., i][mr], [10, 90])
        out[..., i] = np.where(m, np.clip(b0 + (rgba[..., i] - a0) * (b1 - b0) / max(a1 - a0, 1e-3), 0, 1), rgba[..., i])
    return out
