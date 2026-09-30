"""Re-import an exported glTF/GLB into an empty scene and report what actually arrived.

  blender -b --factory-startup --python verify_gltf.py -- OUT.glb [--expect-clips Walk,Run] [--fps 30]

Reports meshes, skinned meshes, armatures, bone count, and each imported clip with its frame
range and duration. Exits non-zero when an expected clip is missing or a clip does not start at
frame 0 (a sign the export offset was wrong). Blender may suffix imported action names with the
object name, so clips match by prefix.
"""
import argparse
import sys

import bpy

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
p = argparse.ArgumentParser()
p.add_argument("path")
p.add_argument("--expect-clips", default="")
p.add_argument("--fps", type=float, default=30.0)
args = p.parse_args(argv)

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.context.scene.render.fps = int(args.fps)
bpy.ops.import_scene.gltf(filepath=args.path)
objects = bpy.context.scene.objects
meshes = [o for o in objects if o.type == "MESH"]
skinned = [o for o in meshes if any(m.type == "ARMATURE" for m in o.modifiers)]
arms = [o for o in objects if o.type == "ARMATURE"]
print(f"MESHES {len(meshes)} (skinned {len(skinned)})  ARMATURES {len(arms)}  BONES {sum(len(a.data.bones) for a in arms)}")

problems = []
clips = {}
for act in bpy.data.actions:
    f0, f1 = act.frame_range
    clips[act.name] = (f0, f1)
    print(f"CLIP {act.name}: frames {f0:g}-{f1:g}  duration {(f1 - f0) / args.fps:.3f} s")
    if abs(f0) > 1e-3:
        problems.append(f"clip {act.name} starts at frame {f0:g}, not 0")
for want in filter(None, args.expect_clips.split(",")):
    if not any(name == want or name.startswith(want + "_") or name.startswith(want + ".") for name in clips):
        problems.append(f"expected clip {want} not found (have {sorted(clips)})")
for problem in problems:
    print("PROBLEM", problem)
sys.exit(1 if problems else 0)
