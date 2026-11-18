"""Cards for the people in 0:24-0:43: one upright card per drawing of each person, the one to show stands on the floor and faces the lens; a second, unseen, throws the shadow from the same feet."""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import bpy  # noqa: E402
from mathutils import Matrix, Vector  # noqa: E402
import kit  # noqa: E402
import setkit  # noqa: E402
import shared_crowd as C  # noqa: E402

DIR = kit.ROOT / "assets" / "gen" / "crowd"
UID_CROWD = 9950


def _flip_uv(ob):
    uv = ob.data.uv_layers[0].data
    for d in uv:
        d.uv = (1 - d.uv[0], d.uv[1])


class Crowd:
    def __init__(self, people, sun, pos_fn, tilt=0.0, shadows=True, room=None, poles=()):
        """pos_fn(person, t) -> (x, y). tilt 0..1: how far a card leans back to face a lens above it, about its feet.
        room(y, z) -> (xmin, xmax): where the set behind people starts (setkit.pull_to_lens); None leaves the cards where they stand."""
        self.people, self.pos_fn, self.tilt, self.room, self.poles = people, pos_fn, tilt, room, poles
        self.cards = []
        for p in people:
            cards = {}
            px = C.person_px(p)
            for d, flip in C.keys_of(p):
                r = C.TABLE[f"{p['pid']}_{d}"]
                col = r["wh"][0] - r["col"] if flip else r["col"]
                # the shadow grows from the feet
                nm = f"crowd_{p['name']}_{d}{'f' if flip else ''}"
                # a picture with print on it has its own mirrored version, in which the print still reads
                mirrored = DIR / f"{p['pid']}_{d}_m.png"
                own = flip and mirrored.exists()
                f = setkit.Figure(mirrored if own else DIR / f"{p['pid']}_{d}.png", nm, px, r["sole"], col, sun=sun if shadows else None, img_wh=tuple(r["wh"]), uid=UID_CROWD)
                if flip and not own:
                    _flip_uv(f.card)
                    f.uv_flipped = True
                    if f.shadow is not None:
                        _flip_uv(f.shadow)
                f.show(False)
                cards[(d, flip)] = f
            self.cards.append(cards)
        self.shown = [None] * len(people)

    def place(self, t, eye):
        for i, p in enumerate(self.people):
            key = (C.drawing_at(p, t), C.flip_at(p, t))
            cur = self.cards[i][key]
            if self.shown[i] is not None and self.shown[i] is not cur:
                self.shown[i].show(False)
            cur.show(True)
            self.shown[i] = cur
            x, y = self.pos_fn(p, t)
            pos = (x, y, p["z"] + p.get("lift", 0.0))
            cur.place(pos, eye)
            if p.get("lift"):
                cur.place_shadow((*C.seen_at(p, x, y, eye), p["z"]))
            if self.tilt:
                # a lens above them: the card leans back about its feet, or a person seen from a crane is squashed
                dx, dy, dz = eye[0] - x, eye[1] - y, eye[2] - p["z"] - 0.9
                a = math.atan2(max(dz, 0.0), math.hypot(dx, dy)) * self.tilt
                if a > 0.001:
                    r_ = Vector((0, 0, 1)).cross(Vector((dx, dy, 0))).normalized()
                    m = Matrix.Translation(pos) @ Matrix.Rotation(-a, 4, r_) @ Matrix.Translation((-pos[0], -pos[1], -pos[2]))
                    cur.card.matrix_world = m @ cur.card.matrix_world
        shown = [s_ for s_ in self.shown if s_ is not None]
        for p, f in zip(self.people, self.shown):
            if p.get("pull") and f is not None:
                setkit.pull_by(f, shown, eye, p["pull"])
        if self.room:
            # all at once, so nobody is brought in front of someone, or a pole, who stands in front of them
            setkit.pull_to_lens_all([s_ for s_ in self.shown if s_ is not None], eye, self.room, self.poles)


def more_bounces(sc):
    """A camera ray in a crowd goes through many cards' clear corners."""
    sc.cycles.transparent_max_bounces = 48
