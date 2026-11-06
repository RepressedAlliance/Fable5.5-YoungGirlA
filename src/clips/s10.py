"""Section 10 kowai: inside the black bar, her view of the door. Finished 3D frames, plus falling dust and the lyric tape in dark paper."""
import sys
from pathlib import Path

import numpy as np
import skia

sys.path.insert(0, str(Path(__file__).parent))
import common as K  # noqa: E402
import engine as E  # noqa: E402
import shared_room as S  # noqa: E402

TAPE_PAPER = "#141B38"
TAPE_INK = "#D5DCEF"
TAPE_Y = 1006
DUST = "#A9BAE6"


def tape(line, text):
    return K.Strip(text, K.chars_of(line, text), size=42)


def draw_dust(c, t, shared):
    """Dust shaken off the top of the door frame: short falling lines, placed in the room's space. No glow, no blur."""
    for x, y, z0, z1 in shared.dust_points(t):
        a = shared.project((x, y, z0), t)
        b = shared.project((x, y, z1), t)
        if not a or not b:
            continue
        w = max(1.0, 0.0028 * (shared.lens_at(t) / 36) * 1920 / a[2])
        p = skia.Paint(AntiAlias=True, Color4f=E.col(DUST), StrokeWidth=min(w, 3.5), StrokeCap=skia.Paint.kButt_Cap)
        c.drawLine(a[0], a[1], b[0], b[1], p)


def blit(c, im):
    arr = np.dstack([im[..., ::-1], np.full(im.shape[:2], 255, np.uint8)])
    c.drawImage(E.np_to_image(arr), 0, 0)


class Room(E.Clip):
    name = "s10"
    t0, t1 = S.T0, S.T1
    cuts = tuple(row[0] for row in S.PLAN if S.T0 < row[0] < S.T1)

    def setup(self):
        self.tapes = [(164.33, tape(46, "ああ夢を夢を見てたはずが")),
                      (K.LYRICS[47]["start"], tape(47, "怖い怖い怖い怖い怖い")),
                      (K.LYRICS[48]["start"], tape(48, "怖い怖い怖い怖い怖い")),
                      (K.LYRICS[49]["start"], tape(49, "怖い怖い怖い怖い近づかないで")),
                      (K.LYRICS[50]["start"], tape(50, "合言葉を繰り返すだけ"))]

    def draw(self, c, t):
        blit(c, K.seq_frame("room", t, self.t0))
        draw_dust(c, t, S)
        cur = None
        for start, st in self.tapes:
            if t >= start:
                cur = st
        if cur:
            cur.draw(c, 960, TAPE_Y, t, ax=0.5, color=TAPE_INK, paper=TAPE_PAPER)
