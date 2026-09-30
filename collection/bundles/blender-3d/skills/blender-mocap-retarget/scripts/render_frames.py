"""Render animation frames from several angles with cameras that follow the character.

  blender -b model.blend --python render_frames.py -- OUTDIR --rig Armature \
      [--views front,side,q34,back,feet] [--frames all|1,5,9|1-41:4] [--res 520] [--follow Hips]

A checker floor makes foot sliding visible; cameras track the --follow bone horizontally so root
motion stays in frame. Writes OUTDIR/<view>_<frame>.png; tile them with contact_sheet.py from the
sibling skill (../blender-reference-model/scripts/ relative to this skill's folder). Never saves the .blend.
Views: front, back, side (character's right), left, q34, q34b, feet, hipL, hipR, shoulderL, shoulderR.
"""
import argparse
import math
import os
import sys

import bpy
from mathutils import Vector

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
p = argparse.ArgumentParser()
p.add_argument("outdir")
p.add_argument("--rig", required=True)
p.add_argument("--views", default="front,side,q34")
p.add_argument("--frames", default="all")
p.add_argument("--res", type=int, default=520)
p.add_argument("--follow", default="Hips", help="bone whose ground position the cameras track")
p.add_argument("--height", type=float, default=1.8, help="character height, scales camera distances")
args = p.parse_args(argv)

scene = bpy.context.scene
rig = bpy.data.objects.get(args.rig)
if rig is None or args.follow not in rig.pose.bones:
    raise SystemExit(f"need armature {args.rig} with bone {args.follow}")
if args.frames == "all":
    frames = list(range(scene.frame_start, scene.frame_end + 1))
elif "-" in args.frames:
    span, _, step = args.frames.partition(":")
    a, b = (int(x) for x in span.split("-"))
    frames = list(range(a, b + 1, int(step or 1)))
else:
    frames = [int(x) for x in args.frames.split(",")]
os.makedirs(args.outdir, exist_ok=True)

k = args.height / 1.8
# view: (camera offset from the tracked ground point, look-at offset, ortho scale or None, lens)
SETUPS = {
    "front": ((0, -6, 0.95), (0, 0, 0.95), 2.2, None),
    "back": ((0, 6, 0.95), (0, 0, 0.95), 2.2, None),
    "side": ((-6, 0, 0.95), (0, 0, 0.95), 2.2, None),
    "left": ((6, 0, 0.95), (0, 0, 0.95), 2.2, None),
    "q34": ((2.4, -3.6, 1.5), (0, 0, 0.9), None, 45),
    "q34b": ((-2.6, 3.4, 1.5), (0, 0, 0.9), None, 45),
    "feet": ((1.4, -2.0, 0.6), (0, 0, 0.18), None, 45),
    "hipL": ((1.3, -0.9, 1.05), (0.25, 0, 0.85), None, 40),
    "hipR": ((-1.3, -0.9, 1.05), (-0.25, 0, 0.85), None, 40),
    "shoulderL": ((1.2, -1.2, 1.55), (0.3, 0, 1.2), None, 40),
    "shoulderR": ((-1.2, -1.2, 1.55), (-0.3, 0, 1.2), None, 40),
}
views = args.views.split(",")
unknown = [v for v in views if v not in SETUPS]
if unknown:
    raise SystemExit(f"unknown views {unknown}; choose from {sorted(SETUPS)}")

engines = {i.identifier for i in scene.render.bl_rna.properties["engine"].enum_items}
scene.render.engine = next(e for e in ("BLENDER_EEVEE", "BLENDER_EEVEE_NEXT", "BLENDER_WORKBENCH") if e in engines)
scene.render.film_transparent = False
scene.view_settings.view_transform = "Standard"
world = bpy.data.worlds.new("FramesWorld")
scene.world = world
world.use_nodes = True
world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.16, 0.16, 0.16, 1)
for name, rot, energy in (("FramesKey", (50, 0, -30), 3.0), ("FramesFill", (70, 0, 150), 0.8)):
    light = bpy.data.lights.new(name, "SUN")
    light.energy = energy
    ob = bpy.data.objects.new(name, light)
    ob.rotation_euler = [math.radians(a) for a in rot]
    scene.collection.objects.link(ob)

mesh = bpy.data.meshes.new("FramesFloor")
size = 20.0
mesh.from_pydata([(-size, -size, 0), (size, -size, 0), (size, size, 0), (-size, size, 0)], [], [(0, 1, 2, 3)])
floor = bpy.data.objects.new("FramesFloor", mesh)
scene.collection.objects.link(floor)
mat = bpy.data.materials.new("FramesChecker")
mat.use_nodes = True
nodes = mat.node_tree.nodes
checker = nodes.new("ShaderNodeTexChecker")
checker.inputs["Scale"].default_value = 2  # object coords: 0.5 m tiles
checker.inputs["Color1"].default_value = (0.42, 0.42, 0.42, 1)
checker.inputs["Color2"].default_value = (0.36, 0.36, 0.36, 1)
coords = nodes.new("ShaderNodeTexCoord")
mat.node_tree.links.new(coords.outputs["Object"], checker.inputs["Vector"])
mat.node_tree.links.new(checker.outputs["Color"], nodes["Principled BSDF"].inputs["Base Color"])
mesh.materials.append(mat)

cam_data = bpy.data.cameras.new("FramesCam")
cam = bpy.data.objects.new("FramesCam", cam_data)
scene.collection.objects.link(cam)
scene.camera = cam

for view in views:
    offset, target, ortho, lens = SETUPS[view]
    for frame in frames:
        scene.frame_set(frame)
        hp = rig.matrix_world @ rig.pose.bones[args.follow].head
        base = Vector((hp.x, hp.y, 0))
        cam.location = base + Vector(offset) * k
        cam.rotation_euler = ((base + Vector(target) * k) - cam.location).to_track_quat("-Z", "Y").to_euler()
        if ortho:
            cam_data.type, cam_data.ortho_scale = "ORTHO", ortho * k
            scene.render.resolution_x, scene.render.resolution_y = int(args.res * 0.8), args.res
        else:
            cam_data.type, cam_data.lens = "PERSP", lens
            scene.render.resolution_x = scene.render.resolution_y = args.res
        scene.render.filepath = os.path.join(args.outdir, f"{view}_{frame:03d}.png")
        bpy.ops.render.render(write_still=True)
print(f"RENDERED {len(views) * len(frames)} frame(s) -> {args.outdir}")
