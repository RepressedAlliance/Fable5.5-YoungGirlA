"""A clip that is a finished 3D sequence with 2D drawn over it: lyric tapes, flashes."""
import sys
from pathlib import Path

import numpy as np
import skia

sys.path.insert(0, str(Path(__file__).parent))
import common as K  # noqa: E402
import engine as E  # noqa: E402


class Seq3D(E.Clip):
    shot = ""
    lines = ()         # lyric line numbers shown as tapes

    def setup(self):
        self.tapes = []
        for k, i in enumerate(self.lines):
            ln = K.LYRICS[i]
            tx = ln["text"].strip()
            nxt = K.LYRICS[self.lines[k + 1]]["start"] if k + 1 < len(self.lines) else self.t1 + 1
            self.tapes.append((ln["start"], min(nxt, ln["end"] + 0.7), K.Strip(tx, K.chars_of(i, tx), size=46)))

    def overlay(self, c, t):
        for a, b, st in self.tapes:
            if a <= t < b:
                st.draw(c, 960, 1034, t, ax=0.5)

    def frame_rgb(self, t):
        im = K.seq_frame(self.shot, t, self.t0)
        arr = np.dstack([im[..., ::-1], np.full(im.shape[:2], 255, np.uint8)])
        surf = skia.Surface(E.W, E.H)
        c = surf.getCanvas()
        c.drawImage(E.np_to_image(arr), 0, 0)
        self.overlay(c, t)
        out = surf.makeImageSnapshot().toarray(colorType=skia.ColorType.kRGBA_8888_ColorType,
                                               alphaType=skia.AlphaType.kOpaque_AlphaType)[..., :3]
        return E.paper_grain(out.astype(np.float32) / 255, self.grain)
