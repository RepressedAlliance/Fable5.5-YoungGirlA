"""Helpers used inside Blender. Scenes only output data passes; src/npr/comp.py does the painting.

Object pass_index: unique per object, used for ink lines.
Material pass_index: 0 painted surface, 1 unlit (sky, screens), 2 cut-out character.
"""
import math
import os
from pathlib import Path

import bmesh
import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[2]
_next_id = [1]


def srgb(h):
    h = h.lstrip("#")
    out = []
    for i in (0, 2, 4):
        c = int(h[i:i + 2], 16) / 255
        out.append(c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4)
    return (*out, 1.0)


def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.world = bpy.data.worlds.new("w")
    sc.world.use_nodes = True
    sc.world.node_tree.nodes["Background"].inputs[0].default_value = (0, 0, 0, 1)
    sc.world.node_tree.nodes["Background"].inputs[1].default_value = 0
    return sc


def setup_render(sc, w=1920, h=1080, ss=1.5, fps=60, samples=3, threads=0):
    r = sc.render
    r.engine = "CYCLES"
    r.resolution_x, r.resolution_y = int(w * ss), int(h * ss)
    r.resolution_percentage = 100
    r.fps = fps
    r.film_transparent = True
    r.filter_size = 0.01 if False else r.filter_size
    r.use_compositing = False
    r.use_sequencer = False
    if threads:
        r.threads_mode = "FIXED"
        r.threads = threads
    c = sc.cycles
    c.device = "CPU"
    if os.environ.get("KIT_GPU") == "1":
        # User-approved 2026-11-05: Cycles on the RTX 4060, in G-Helper mode 7 (GPU capped at 2000 MHz)
        prefs = bpy.context.preferences.addons["cycles"].preferences
        # OptiX fails to compile its kernel on this machine (OPTIX_ERROR_INTERNAL_COMPILER_ERROR)
        prefs.compute_device_type = "CUDA"
        prefs.get_devices()
        for d in prefs.devices:
            d.use = d.type == "CUDA"
        c.device = "GPU"
    c.samples = samples
    c.use_adaptive_sampling = False
    c.use_denoising = False
    c.max_bounces = 0
    c.diffuse_bounces = 0
    c.glossy_bounces = 0
    c.transmission_bounces = 0
    c.volume_bounces = 0
    c.transparent_max_bounces = 8
    c.pixel_filter_type = "BOX"
    c.filter_width = 1.0
    c.use_auto_tile = False
    vl = sc.view_layers[0]
    vl.use_pass_combined = True
    vl.use_pass_z = True
    vl.use_pass_normal = True
    vl.use_pass_position = True
    vl.use_pass_diffuse_color = True
    vl.use_pass_diffuse_direct = True
    vl.use_pass_object_index = True
    vl.use_pass_material_index = True
    s = r.image_settings
    s.media_type = "MULTI_LAYER_IMAGE"
    s.color_depth = "32"
    s.exr_codec = "ZIP"


def mat(name, color="#808080", kind=0, tex=None, alpha_tex=False, repeat=None):
    """Flat diffuse material. `tex` is an sRGB image; `repeat` (u, v) metres-per-tile via object coords."""
    if name in bpy.data.materials:
        return bpy.data.materials[name]
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    m.pass_index = kind
    nt = m.node_tree
    bsdf = nt.nodes["Principled BSDF"]
    nt.nodes.remove(bsdf)
    out = nt.nodes["Material Output"]
    d = nt.nodes.new("ShaderNodeBsdfDiffuse")
    d.inputs["Color"].default_value = srgb(color)
    surface = d.outputs[0]
    if tex:
        img = bpy.data.images.load(str(tex), check_existing=True)
        t = nt.nodes.new("ShaderNodeTexImage")
        t.image = img
        t.interpolation = "Linear"
        if repeat:
            co = nt.nodes.new("ShaderNodeTexCoord")
            mp = nt.nodes.new("ShaderNodeMapping")
            mp.inputs["Scale"].default_value = (repeat[0], repeat[1], 1)
            nt.links.new(co.outputs["UV"], mp.inputs[0])
            nt.links.new(mp.outputs[0], t.inputs[0])
            t.extension = "REPEAT"
        nt.links.new(t.outputs[0], d.inputs["Color"])
        if alpha_tex:
            tr = nt.nodes.new("ShaderNodeBsdfTransparent")
            mx = nt.nodes.new("ShaderNodeMixShader")
            nt.links.new(t.outputs[1], mx.inputs[0])
            nt.links.new(tr.outputs[0], mx.inputs[1])
            nt.links.new(d.outputs[0], mx.inputs[2])
            surface = mx.outputs[0]
    nt.links.new(surface, out.inputs[0])
    return m


def _link(name, mesh, loc=(0, 0, 0), rot=(0, 0, 0), material=None, parent=None, uid=None):
    ob = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(ob)
    ob.location = loc
    ob.rotation_euler = rot
    if material is not None and not mesh.materials:
        mesh.materials.append(material)
    if uid is None:
        uid = _next_id[0]
        _next_id[0] += 1
    ob.pass_index = uid
    if material is not None and material.pass_index in (1, 5):
        ob.visible_shadow = False  # backdrops must not block the sun
    if parent:
        ob.parent = parent
    return ob


def box_mesh(name, sx, sy, sz, origin="center"):
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts:
        v.co.x *= sx
        v.co.y *= sy
        v.co.z *= sz
        if origin == "floor":
            v.co.z += sz / 2
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    return me


def box(name, center, size, material, rot=(0, 0, 0), parent=None, uid=None):
    me = box_mesh(name, *size)
    return _link(name, me, center, rot, material, parent, uid)


def plane(name, center, sx, sy, material, rot=(0, 0, 0), parent=None, uid=None):
    me = bpy.data.meshes.new(name)
    hx, hy = sx / 2, sy / 2
    me.from_pydata([(-hx, -hy, 0), (hx, -hy, 0), (hx, hy, 0), (-hx, hy, 0)], [], [(0, 1, 2, 3)])
    me.update()
    uv = me.uv_layers.new(name="UV")
    for i, co in enumerate(((0, 0), (1, 0), (1, 1), (0, 1))):
        uv.data[i].uv = co
    return _link(name, me, center, rot, material, parent, uid)


def cyl(name, p0, p1, radius, material, parent=None, uid=None, seg=8):
    p0, p1 = Vector(p0), Vector(p1)
    d = p1 - p0
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=seg, radius1=radius, radius2=radius, depth=d.length)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    for p in me.polygons:
        p.use_smooth = False
    ob = _link(name, me, (p0 + p1) / 2, (0, 0, 0), material, parent, uid)
    ob.rotation_mode = "QUATERNION"
    ob.rotation_quaternion = d.to_track_quat("Z", "Y")
    ob.rotation_mode = "XYZ"
    return ob


def join(objects, name):
    """Merge many objects into one mesh, keeping materials; keeps one ink id for the whole group."""
    ctx = bpy.context
    for o in ctx.selected_objects:
        o.select_set(False)
    for o in objects:
        o.select_set(True)
    ctx.view_layer.objects.active = objects[0]
    bpy.ops.object.join()
    ob = ctx.view_layer.objects.active
    ob.name = name
    return ob


def sun(sc, direction, energy=3.14159):
    """`direction`: the way the light travels."""
    d = bpy.data.lights.new("sun", "SUN")
    d.energy = energy
    d.angle = 0.0
    ob = bpy.data.objects.new("sun", d)
    sc.collection.objects.link(ob)
    v = Vector(direction).normalized()
    ob.rotation_mode = "QUATERNION"
    ob.rotation_quaternion = v.to_track_quat("-Z", "Y")
    return ob


def camera(sc, lens=28.0, clip_end=20000.0):
    c = bpy.data.cameras.new("cam")
    c.lens = lens
    c.sensor_width = 36
    c.clip_start = 0.02
    c.clip_end = clip_end
    ob = bpy.data.objects.new("cam", c)
    sc.collection.objects.link(ob)
    sc.camera = ob
    return ob


def look_at(ob, eye, target, roll=0.0):
    eye, target = Vector(eye), Vector(target)
    ob.location = eye
    q = (target - eye).to_track_quat("-Z", "Y")
    ob.rotation_mode = "QUATERNION"
    ob.rotation_quaternion = q
    if roll:
        from mathutils import Quaternion
        ob.rotation_quaternion = q @ Quaternion((0, 0, 1), math.radians(roll))


def set_args():
    import sys
    return sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
