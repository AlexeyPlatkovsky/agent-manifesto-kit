"""Render the five concept views of blender/object.blend with Cycles.

Run: Blender -b blender/object.blend --python blender/render_views.py -- [view ...] [--samples N]
Writes out/blender/raw/<view>.png (RGBA, transparent background + shadow) and
out/blender/<view>.png (composited on the spec background colour).
"""
import bpy, json, math, os, sys
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SPEC = json.load(open(os.path.join(ROOT, "spec/object.json")))
argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
samples = None
if "--samples" in argv:
    i = argv.index("--samples")
    samples = int(argv[i + 1])
    del argv[i:i + 2]
views = argv or list(SPEC["cameras"]["views"].keys())

scene = bpy.context.scene
if samples:
    scene.cycles.samples = samples
cam = scene.camera
el = math.radians(SPEC["cameras"]["elevation_deg"])
fill = SPEC["cameras"].get("fill", 0.92)
rig = scene.objects.get("light_rig")

dg = bpy.context.evaluated_depsgraph_get()
pts = []
for o in scene.objects:
    if o.type == "MESH" and not o.hide_render and not o.is_shadow_catcher:
        oe = o.evaluated_get(dg)
        pts += [oe.matrix_world @ Vector(c) for c in oe.bound_box]
lo = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
hi = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
corners = [Vector((x, y, z)) for x in (lo.x, hi.x) for y in (lo.y, hi.y) for z in (lo.z, hi.z)]
target = (lo + hi) / 2


def place(az_deg, d):
    global el
    az = math.radians(az_deg)
    # spec: camera at (sin az, ., cos az) in (x, z-front); blender front is -Y
    off = Vector((d * math.sin(az) * math.cos(el), -d * math.cos(az) * math.cos(el), d * math.sin(el)))
    cam.location = target + off
    cam.rotation_euler = (-off).to_track_quat("-Z", "Y").to_euler()
    bpy.context.view_layer.update()


def fit(az_deg):
    d = 5.0
    for _ in range(6):
        place(az_deg, d)
        ys = [world_to_camera_view(scene, cam, c).y for c in corners]
        ext = max(ys) - min(ys)
        d *= ext / fill
    place(az_deg, d)
    # centre vertically
    ys = [world_to_camera_view(scene, cam, c).y for c in corners]
    return d


raw_dir = os.path.join(ROOT, "out/blender/raw")
os.makedirs(raw_dir, exist_ok=True)
for v in views:
    az = SPEC["cameras"]["views"][v]
    el = math.radians(SPEC["cameras"].get("elevation_overrides", {}).get(v, SPEC["cameras"]["elevation_deg"]))
    fit(az)
    if rig:  # lights turn with the camera: every concept view is lit the same way
        rig.rotation_euler = (0, 0, math.radians(az))
    scene.render.filepath = os.path.join(raw_dir, v + ".png")
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGBA"
    bpy.ops.render.render(write_still=True)
    print("rendered", v)

# composite onto background (numpy ships with Blender)
import numpy as np
bg_hex = SPEC["palette"]["background"].lstrip("#")
bgc = np.array([int(bg_hex[i:i + 2], 16) / 255 for i in (0, 2, 4)], dtype=np.float32)
for v in views:
    img = bpy.data.images.load(os.path.join(raw_dir, v + ".png"))
    w, h = img.size
    px = np.empty(w * h * 4, dtype=np.float32)
    img.pixels.foreach_get(px)
    px = px.reshape(h, w, 4)
    a = px[..., 3:4].copy()
    # shadow-catcher pixels are black with partial alpha: soften the ground shadow (concept has a faint one)
    shadow = (px[..., :3].max(2, keepdims=True) < 0.03) & (a < 0.995)
    a = np.where(shadow, a * 0.2, a)
    # PNG loaded as straight alpha in display space
    rgb = px[..., :3] * a + bgc * (1 - a)
    out = np.concatenate([rgb, np.ones_like(a)], axis=2)
    o = bpy.data.images.new(v + "_comp", w, h, alpha=False)
    o.pixels.foreach_set(out.ravel())
    o.filepath_raw = os.path.join(ROOT, "out/blender", v + ".png")
    o.file_format = "PNG"
    o.save()
    print("composited", v)
