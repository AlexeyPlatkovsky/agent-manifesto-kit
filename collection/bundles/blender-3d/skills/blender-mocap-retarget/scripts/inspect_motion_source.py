"""Inspect a motion source (FBX or glTF) before designing a retarget.

  blender -b --factory-startup --python inspect_motion_source.py -- source.fbx [--json out.json]

Reports the skeleton (bone count, roots, finger bones), armature object scale, frame range and
fps, rest-pose arm angle (T- or A-pose), root motion of the hips over the clip, per-foot lowest
height relative to the rest pose, and the loop seam: how far the last frame's pose is from the
first, ignoring root translation. Works in an empty scene; nothing is saved.
"""
import argparse
import json
import math
import sys

import bpy

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
p = argparse.ArgumentParser()
p.add_argument("source")
p.add_argument("--json")
args = p.parse_args(argv)

bpy.ops.wm.read_factory_settings(use_empty=True)
if args.source.lower().endswith(".fbx"):
    bpy.ops.import_scene.fbx(filepath=args.source, use_anim=True)
else:
    bpy.ops.import_scene.gltf(filepath=args.source)
scene = bpy.context.scene
arms = [o for o in scene.objects if o.type == "ARMATURE"]
if not arms:
    raise SystemExit("no armature in source")
arm = max(arms, key=lambda a: len(a.data.bones))
act = arm.animation_data.action if arm.animation_data else None
if act is None:
    raise SystemExit(f"armature {arm.name} has no action")
f0, f1 = (int(round(v)) for v in act.frame_range)
names = [b.name for b in arm.data.bones]


def find(*keys, exclude=()):
    for n in names:
        low = n.lower()
        if all(k in low for k in keys) and not any(x in low for x in exclude):
            return n
    return None


hips = find("hips") or next(b.name for b in arm.data.bones if b.parent is None)
feet = {side: find(side, "foot") for side in ("left", "right")}
upper_arm = find("left", "arm", exclude=("fore", "shoulder", "hand"))
fingers = [n for n in names if any(k in n.lower() for k in ("index", "middle", "ring", "pinky", "thumb"))]
mw = arm.matrix_world


def head(bone, frame=None):
    if frame is None:
        return mw @ arm.data.bones[bone].head_local
    scene.frame_set(frame)
    return mw @ arm.pose.bones[bone].head


rest_pose = None
if upper_arm:
    b = arm.data.bones[upper_arm]
    d = (mw.to_3x3() @ (b.tail_local - b.head_local)).normalized()
    rest_pose = round(math.degrees(math.asin(max(-1.0, min(1.0, -d.z)))), 1)

report = {
    "armature": arm.name,
    "object_scale": [round(s, 4) for s in arm.scale],
    "bones": len(names),
    "roots": [b.name for b in arm.data.bones if b.parent is None],
    "finger_bones": len(fingers),
    "fps": scene.render.fps / scene.render.fps_base,
    "frame_range": [f0, f1],
    "hips": hips,
    "upper_arm_below_horizontal_deg": rest_pose,
}
h0, h1 = head(hips, f0), head(hips, f1)
report["hips_root_motion_m"] = [round(v, 4) for v in (h1 - h0)]
report["hips_height_rest_m"] = round(head(hips).z, 4)
report["hips_height_range_m"] = [round(min(head(hips, f).z for f in range(f0, f1 + 1)), 4),
                                 round(max(head(hips, f).z for f in range(f0, f1 + 1)), 4)]
report["feet"] = {}
for side, foot in feet.items():
    if foot:
        zs = [(head(foot, f).z, f) for f in range(f0, f1 + 1)]
        low, frame = min(zs)
        report["feet"][foot] = {"rest_z": round(head(foot).z, 4), "lowest_z": round(low, 4),
                                "lowest_minus_rest_m": round(low - head(foot).z, 4), "lowest_frame": frame}


def pose_rotations(frame):
    scene.frame_set(frame)
    return {pb.name: pb.matrix_basis.to_quaternion() for pb in arm.pose.bones}


a, b = pose_rotations(f0), pose_rotations(f1)
worst = max(a, key=lambda n: a[n].rotation_difference(b[n]).angle)
report["loop_seam"] = {"max_rotation_diff_deg": round(math.degrees(a[worst].rotation_difference(b[worst]).angle), 3),
                       "worst_bone": worst,
                       "note": "near 0 with nonzero root motion means the last frame repeats the first plus one stride"}

print(json.dumps(report, indent=2))
if args.json:
    with open(args.json, "w") as f:
        json.dump(report, f, indent=2)
