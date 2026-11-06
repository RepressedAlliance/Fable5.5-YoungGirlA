"""Clip 4: paper standees stand off a printed wall, in one sun with hard shadows."""
import json
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import bpy  # noqa: E402
from mathutils import Matrix, Vector  # noqa: E402
import kit  # noqa: E402
import shared_c4 as S  # noqa: E402

ROOT = kit.ROOT
SUN = (-0.42, 0.72, -0.55)   # the way the light travels: from upper right behind the camera


def build():
    sc = kit.reset()
    kit.setup_render(sc, 1920, 1080, ss=S.SS, fps=60, samples=3, threads=12)
    sc.render.use_persistent_data = True
    kit.sun(sc, SUN)
    cam = kit.camera(sc, lens=S.LENS, clip_end=500)
    W = S.COLS * S.CELL_W
    H = S.ROWS * S.CELL_H
    wall = kit.plane("wall", (0, 0, 0), W, H, kit.mat("wall", "#FFFFFF", tex=ROOT / "assets" / "gen" / "c4_wall.png"),
                     rot=(math.pi / 2, 0, 0))
    # big surround so the edge of the printed wall never shows void
    kit.plane("surround", (0, 0.05, 0), W * 6, H * 6, kit.mat("surround", "#03C3FB", kind=5), rot=(math.pi / 2, 0, 0))
    meta = S.meta()
    ids = {}
    for (r, cell) in zip(S.RUMOURS, S.ORDER):
        name, _, _, _, _, off = r
        m = meta[name]
        cx, cz = S.cell_center(*cell)
        mat = kit.mat("st_" + name, "#FFFFFF", kind=2, tex=ROOT / "assets" / "gen" / "standee" / f"{name}.png", alpha_tex=True)
        # feet near the bottom of the cell, figure a little right of centre to leave the words clear
        px = cx + S.CELL_W * 0.13
        pz = cz - S.CELL_H / 2 + 0.11 + m["h_m"] / 2
        ob = kit.plane(name, (px, -off, pz), m["w_m"], m["h_m"], mat, rot=(math.pi / 2, 0, 0))
        ids[name] = {"center": [px, -off, pz], "w": m["w_m"], "h": m["h_m"]}
    (ROOT / "work" / "render").mkdir(parents=True, exist_ok=True)
    (ROOT / "work" / "render" / "c4_ids.json").write_text(json.dumps(ids))
    return sc, cam


def set_frame(t, sc, cam):
    eye, target, up = S.camera_at(t)
    z = (Vector(eye) - Vector(target)).normalized()
    x = Vector(up).cross(z).normalized()
    y = z.cross(x)
    cam.rotation_mode = "QUATERNION"
    cam.matrix_world = Matrix.Translation(eye) @ Matrix((x, y, z)).transposed().to_4x4()


def main():
    args = kit.set_args()
    out = Path(args[0]).resolve()
    out.mkdir(parents=True, exist_ok=True)
    state = build()
    if args[1] == "todo":
        frames = json.loads(Path(args[2]).read_text())
        items = [(S.T0 + f / 60.0, out / f"f{f:05d}.exr") for f in frames]
    else:
        items = [(float(a), out / f"t{float(a):07.3f}.exr") for a in args[1:]]
    sc = state[0]
    for t, path in items:
        if path.exists():
            continue
        set_frame(t, *state)
        tmp = path.with_suffix(".tmp.exr")
        sc.render.filepath = str(tmp)
        bpy.ops.render.render(write_still=True)
        tmp.rename(path)
        print("RENDERED", path.name, flush=True)


if __name__ == "__main__":
    main()
