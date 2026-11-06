"""Clip 2 finished frames. Everything happens in the 3D shot; this only passes it through."""
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
import common as K  # noqa: E402
import engine as E  # noqa: E402
import shared_c2 as S  # noqa: E402


class Samui(E.Clip):
    name = "c2"
    t0, t1 = S.T0, S.T1

    def frame_rgb(self, t):
        im = K.seq_frame("c2", t, self.t0)
        return E.paper_grain(im[..., ::-1].astype(np.float32) / 255, self.grain)
