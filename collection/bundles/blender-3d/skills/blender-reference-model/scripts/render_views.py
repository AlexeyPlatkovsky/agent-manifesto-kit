"""Render each spec view orthographically at the reference's pixel scale (transparent background).

  blender -b model.blend --python render_views.py -- ref_spec.json OUTDIR [--scale 2] [--hide A,B] [--pose]

Adds a temporary camera, lights and world; never saves the .blend. The character faces -Y with
its left side on +X, so front = camera on -Y, right = camera on -X, left = +X, back = +Y.
Armatures render in their rest pose unless --pose is given, so a rigged model is compared in the
pose the reference shows. Output: OUTDIR/<view>.png, sized crop * scale.
"""
import argparse
import json
import math
import os
import sys

import bpy

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
p = argparse.ArgumentParser()
p.add_argument("spec")
p.add_argument("outdir")
p.add_argument("--scale", type=float, default=1.0)
p.add_argument("--hide", default="", help="comma-separated object names to exclude from renders")
p.add_argument("--pose", action="store_true", help="keep armatures in their current animated pose")
args = p.parse_args(argv)

with open(args.spec) as f:
    spec = json.load(f)
mpp, ground = spec["meters_per_px"], spec["ground_px"]
os.makedirs(args.outdir, exist_ok=True)

# camera: (rotation, horizontal world axis, sign of image-right along that axis, depth location)
CAMERAS = {
    "front": ((90, 0, 0), "x", 1, (None, -20.0)),
    "back": ((90, 0, 180), "x", -1, (None, 20.0)),
    "right": ((90, 0, -90), "y", -1, (-20.0, None)),
    "left": ((90, 0, 90), "y", 1, (20.0, None)),
}

scene = bpy.context.scene
engines = {i.identifier for i in scene.render.bl_rna.properties["engine"].enum_items}
scene.render.engine = next(e for e in ("BLENDER_EEVEE", "BLENDER_EEVEE_NEXT", "BLENDER_WORKBENCH") if e in engines)
scene.render.film_transparent = True
scene.render.image_settings.file_format = "PNG"
scene.render.image_settings.color_mode = "RGBA"
scene.view_settings.view_transform = "Standard"
scene.view_settings.look = "None"
scene.render.resolution_percentage = 100

for name in filter(None, args.hide.split(",")):
    ob = bpy.data.objects.get(name)
    if ob is None:
        raise SystemExit(f"--hide: no object named {name}")
    ob.hide_render = True

if not args.pose:
    for arm in bpy.data.armatures:
        arm.pose_position = "REST"

world = bpy.data.worlds.new("RefViewsWorld")
scene.world = world
world.use_nodes = True
world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.16, 0.16, 0.16, 1)


def sun(name, energy):
    data = bpy.data.lights.new(name, "SUN")
    data.energy = energy
    data.angle = math.radians(8)
    ob = bpy.data.objects.new(name, data)
    scene.collection.objects.link(ob)
    return ob


key, fill = sun("RefKey", 3.2), sun("RefFill", 0.8)
cam_data = bpy.data.cameras.new("RefCam")
cam_data.type = "ORTHO"
cam = bpy.data.objects.new("RefCam", cam_data)
scene.collection.objects.link(cam)
scene.camera = cam

for name, view in spec["views"].items():
    rot, axis, sign, depth = CAMERAS[view["camera"]]
    x0, y0, x1, y1 = view["crop"]
    w, h = x1 - x0, y1 - y0
    lateral = sign * ((x0 + x1) / 2 - view["center_px"]) * mpp
    z = (ground - (y0 + y1) / 2) * mpp
    cam.location = (lateral if axis == "x" else depth[0], lateral if axis == "y" else depth[1], z)
    cam.rotation_euler = tuple(math.radians(a) for a in rot)
    cam_data.ortho_scale = max(w, h) * mpp
    cam_data.clip_end = 100
    scene.render.resolution_x = round(w * args.scale)
    scene.render.resolution_y = round(h * args.scale)
    # keep the key light at the camera's upper left for every view
    key.rotation_euler = (math.radians(50), 0, math.radians(rot[2] - 30))
    fill.rotation_euler = (math.radians(70), 0, math.radians(rot[2] + 150))
    scene.render.filepath = os.path.join(args.outdir, f"{name}.png")
    bpy.ops.render.render(write_still=True)
    print(f"RENDERED {name} {scene.render.resolution_x}x{scene.render.resolution_y}")
