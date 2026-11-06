"""206-222, the world carries on: gate, lockers, train, classroom in a warm afternoon, hard cuts on two-bar lines."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import seq3d  # noqa: E402
import shared_outro as S  # noqa: E402


class Outro(seq3d.Seq3D):
    name = "s13a"
    shot = "outro"
    t0, t1 = S.T0, S.T1
    cuts = S.CUTS
    lines = ()
