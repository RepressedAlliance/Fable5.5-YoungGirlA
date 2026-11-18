"""Where to stand a sitting person's card on a train bench so that, from the lens, they sit on it. Plain Python.

A sitting drawing on a flat card shows the seat resting on the bench, and below that what hangs over the bench's front edge: a
skirt or coat, the shins, the shoes. Seen from the lens it looks right only if
  - the resting part (the drawing's seat contact, assets/gen/sit_contacts.json) lies on the cushion, at its height, and
  - everything lower than the cushion is in front of the bench: past the front edge of the seat, and below the seat's front
    board past the board under it.
Otherwise the seat floats above the cushion, or a hem or a pair of knees rests on the cushion while the shins hang down
through it (2026-11-18: Rin, the old woman, the office worker and the woman in the beige coat in the outro's car).

fit() gives the place of the card's pin (its soles): as far back on the bench as the hanging parts allow, at the height that
puts the contact on the cushion. The height is often not the floor: the drawings' legs are not all one length against their
bodies. Seen from the lens a card raised or lowered is the same person sitting a little further off or nearer and a little
bigger or smaller, so their shadow and the dark patch under their shoes go where the line from the lens through the soles meets
the floor (see shared_crowd.seen_at)."""
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
_BANDS = json.loads((ROOT / "assets" / "gen" / "opaque_bands.json").read_text())
CONTACTS = json.loads((ROOT / "assets" / "gen" / "sit_contacts.json").read_text())

LIP = 0.91      # the seat's front edge, metres from the car's middle (shot_train.build_set)
BASE = 1.00     # the board under the seat, set back from that edge
FACE = 0.10     # the seat's own front, from the cushion down
REST = 0.004    # the contact sits this far above the cushion: on it, not in it


def fit(key, rel_path, px, sole, col, flip, side, y, eye, seat, margin=0.015, base_margin=0.015, x0=None):
    """(x, z) of the pin of drawing `key` (file rel_path under the project, as in opaque_bands.json) on the bench at `side`
    (+1 right, -1 left), at y along the car, seen from `eye`. px, sole, col: the card's metres a pixel, row of the soles and
    pinned column, as setkit.Figure has them; flip: the card shows the picture mirrored. margin: how far in front of the seat's
    edge the hanging parts keep; base_margin: the same for what stands on the floor by the board under the seat (a bag put down
    against it may touch it). Returns (x, z, how far the contact is in from the seat's edge)."""
    c = CONTACTS[key]
    bands = _BANDS[rel_path]
    sg = -1 if flip else 1
    z = seat + REST - (sole - c["row"]) * px
    sx = side * (x0 if x0 is not None else 0.75 * side)
    for _ in range(3):
        x = side * sx
        fx, fy = eye[0] - x, eye[1] - y
        n = math.hypot(fx, fy)
        rx = -fy / n            # the card's right, across the picture, has this much x
        k = side * rx * sg * px  # metres towards the wall per column
        if k * c["wall"] <= 0:
            raise ValueError(f"{key}: the drawing's back faces the aisle on this bench")
        lim = []
        for row, c0, c1 in bands:
            zb = z + (sole - row) * px
            if zb >= seat - 0.01:
                continue
            cw = c1 if c["wall"] > 0 else c0
            edge = LIP - margin if zb > seat - FACE else BASE - base_margin
            lim.append(edge - k * (cw - col))
        sx = min(lim)
    x = side * sx
    on = sx + k * (c["col"] - col) - LIP
    return x, z, on
