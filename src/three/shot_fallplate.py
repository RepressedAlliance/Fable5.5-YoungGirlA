"""Stills of the warm classroom seen straight down from above her desk, for the newspaper's fall (src/clips/s04a.py).

The same room, sun and paint as clip 2, without the newspaper, so that the fall lands in the room clip 2 starts in. Only
a few heights are drawn; s04a scales the nearest one for the heights between, which the speed of the fall hides.

Run in Blender:  blender -b --python shot_fallplate.py -- OUTDIR h1 h2 ...      h: metres above the page
Then: python src/three/shot_fallplate.py paint OUTDIR                           writes assets/tex/fall/h*.png
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
ROOT = Path(__file__).resolve().parents[2]
PLATES = ROOT / "assets" / "tex" / "fall"
# metres above the page. Dense near the landing, where it slows down; the last is exactly clip 2's first height.
HEIGHTS = (0.366, 0.385, 0.41, 0.44, 0.48, 0.58, 0.72, 0.90, 1.14, 1.45, 1.82, 2.26, 2.75, 3.3)


def blender(args):
    import bpy
    from mathutils import Vector
    import setkit
    import shared_c2 as S
    import shot_c2 as C
    import kit
    out = Path(args[0]).resolve()
    out.mkdir(parents=True, exist_ok=True)
    state = C.build()
    sc, cam = state[0], state[1]
    # no newspaper; and from above the ceiling there is no ceiling
    for name in ("page", "page_under"):
        bpy.data.objects[name].hide_render = True
    for o in bpy.data.objects:
        if o.name.split(".")[0] in ("ceil", "lamp_base", "lamp_tube"):
            o.hide_render = True
    C.set_frame(S.T0, *state)
    up = (S.math.sin(S.PAGE_ANGLE), -S.math.cos(S.PAGE_ANGLE), 0.0)
    for h in (float(a) for a in args[1:]):
        path = out / f"h{h:05.3f}.exr"
        if path.exists():
            continue
        setkit.set_camera(cam, (S.PAGE_C[0], S.PAGE_C[1], S.PAGE_C[2] + h), S.PAGE_C, up)
        tmp = path.with_suffix(".tmp.exr")
        sc.render.filepath = str(tmp)
        bpy.ops.render.render(write_still=True)
        tmp.rename(path)
        print("RENDERED", path.name, flush=True)


def paint(d):
    import json
    import cv2
    import numpy as np
    sys.path[:0] = [str(ROOT / "src"), str(ROOT / "src" / "npr")]
    import comp
    import engine as E
    import paint_c2 as P
    import shared_c2 as S
    ids = json.loads((ROOT / "work" / "render" / "c2_ids.json").read_text())
    PLATES.mkdir(parents=True, exist_ok=True)
    cyan = np.array([int(E.CYAN[i:i + 2], 16) / 255 for i in (1, 3, 5)], np.float32)
    for f in sorted(Path(d).glob("h*.exr")):
        rgba = comp.paint(comp.read_exr(f), P.look_at(S.T0, {"board": ids["board"]}), ss=S.SS)
        # past the window wall there is only the song's flat cyan, as in the shots of this room
        rgb = rgba[..., :3] * rgba[..., 3:4] + cyan * (1 - rgba[..., 3:4])
        cv2.imwrite(str(PLATES / f"{f.stem}.png"), (np.clip(rgb, 0, 1)[..., ::-1] * 255 + 0.5).astype(np.uint8))
        print(f.stem, flush=True)


if __name__ == "__main__":
    if "--" in sys.argv:
        blender(sys.argv[sys.argv.index("--") + 1:])
    elif sys.argv[1] == "paint":
        paint(sys.argv[2])
    else:
        print(" ".join(str(h) for h in HEIGHTS))
