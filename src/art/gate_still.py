"""The gate as the photo shows it: work/render/gate_still.png.

The very first frame of the gate shot (s02a), painted as if no camera went off on it. s01b prints the photo everybody passes
round from it and, at the end of its push, turns the photo back into it, so the cut to s02a lands on the same people in the
same places and only the flashes of the singer's first word are new (2026-11-18: the photo used to be the frame 0.4 s later,
and at the cut the crowd jumped to other drawings). Run again after the gate shot is rendered again.
"""
import json
import sys
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "src" / "npr"), str(ROOT / "src" / "three")]
import paint_gate as P  # noqa: E402
import shared_gate as S  # noqa: E402

OUT = ROOT / "work" / "render" / "gate_still.png"


def main():
    ids = json.loads((ROOT / "work" / "render" / "gate_ids.json").read_text())
    rgb = P.paint_time(ROOT / "work" / "render" / "gate_exr" / "f00000.exr", S.T0, ids, lit=False)
    cv2.imwrite(str(OUT), (rgb[..., ::-1] * 255 + 0.5).astype(np.uint8))
    print("->", OUT)


if __name__ == "__main__":
    main()
