"""What the painters of the gate, the hall and the train do for their people: the patch under the feet, lit phone screens, and one light on the cards."""
import numpy as np


def card_mask(p, uid):
    return np.abs(p["IndexOB"] - uid) < 0.5


def floor_patches(p, patches, low_z=0.02, half_x=None, tone=(0.42, 0.38, 0.40), z_band=None):
    """Joins people to the floor: fixed to the floor through the position pass, one hard tone, whatever it falls across."""
    pos = np.nan_to_num(p["Position"][..., :3]).astype(np.float32)
    low = pos[..., 2] < low_z
    if z_band is not None:
        low = (pos[..., 2] > z_band[0]) & (pos[..., 2] < z_band[1])
    if half_x is not None:
        low &= np.abs(pos[..., 0]) < half_x
    idx = np.where(low)
    px_, py_ = pos[..., 0][idx], pos[..., 1][idx]
    hit = np.zeros(px_.shape, bool)
    for x, y, a, b, ang in patches:
        c, s_ = np.cos(ang), np.sin(ang)
        dx, dy = px_ - x, py_ - y
        u = dx * c + dy * s_
        v = -dx * s_ + dy * c
        hit |= (u / a) ** 2 + (v / b) ** 2 < 1
    col = p["DiffCol"][..., :3].astype(np.float32)
    col[idx[0][hit], idx[1][hit]] *= np.array(tone, np.float32)
    p["DiffCol"] = col
    return p


def screens(p, uid):
    """Where a card shows a phone screen. The pictures have them flat magenta."""
    col = p["DiffCol"][..., :3]
    r, g, b = col[..., 0], col[..., 1], col[..., 2]
    low = np.minimum(r, b)
    return card_mask(p, uid) & (low > 0.02) & (g < 0.35 * low)


def light_screens(p, uid, colour):
    """The screens, in one hard flat colour. Returns the mask, so that a painter that darkens the frame can leave them bright."""
    m = screens(p, uid)
    col = p["DiffCol"][..., :3].astype(np.float32)
    col[m] = np.array(colour, np.float32)
    p["DiffCol"] = col
    return m


def tone_cards(p, uid, tone, keep=None):
    """The cards are not shaded by the sun: where everything else facing the lens is in its shadow tone, so are they."""
    m = card_mask(p, uid)
    if keep is not None:
        m &= ~keep
    col = p["DiffCol"][..., :3].astype(np.float32)
    col[m] *= np.array(tone, np.float32)
    p["DiffCol"] = col
    return p
