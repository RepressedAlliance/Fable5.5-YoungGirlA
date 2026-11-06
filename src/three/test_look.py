"""Look test: one frame of the classroom. Run in Blender; writes work/look/test_<view>.exr"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import bpy  # noqa: E402
import kit  # noqa: E402
import classroom  # noqa: E402

args = kit.set_args()
view = args[0] if args else "rear"
sc = kit.reset()
kit.setup_render(sc, 1920, 1080, ss=1.5, samples=3)
classroom.build()
kit.sun(sc, (0.80, -0.22, -0.42))
cam = kit.camera(sc, lens=26)
if view == "rear":
    kit.look_at(cam, (2.6, 0.9, 1.5), (-1.2, 7.0, 1.1))
elif view == "front":
    kit.look_at(cam, (-2.2, 7.4, 1.75), (0.8, 1.8, 0.8))
out = kit.ROOT / "work" / "look"
out.mkdir(parents=True, exist_ok=True)
sc.render.filepath = str(out / f"test_{view}.exr")
bpy.ops.render.render(write_still=True)
print("DONE", sc.render.filepath)
