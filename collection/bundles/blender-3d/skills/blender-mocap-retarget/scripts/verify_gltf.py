"""Re-import an exported glTF/GLB into an empty scene and verify what arrived.

  blender -b --factory-startup --python-exit-code 1 --python verify_gltf.py -- OUT.glb \
      --expect-clips Walk,Run --exact-clips --require-mesh --require-skin --require-rig

Legacy --expect-clips matches imported action prefixes. --exact-clips compares the
original glTF animation names as an exact set, including unexpected exports; this
avoids ambiguity from Blender's action renaming. Structural requirements check
imported usable geometry, weighted skinned geometry, and an armature with bones.
Without requirements the script remains diagnostic, apart from expected missing
clips and nonzero clip start frames. --json writes a machine-readable summary.
"""
import argparse
import json
import math
import struct
import sys

import bpy


def fps_value(value):
    fps = float(value)
    if not math.isfinite(fps) or fps < 1 or fps > 32767:
        raise argparse.ArgumentTypeError("must be finite and between 1 and 32767")
    return fps


def read_gltf(path):
    """Read the export's JSON, without depending on Blender action name suffixes."""
    with open(path, "rb") as stream:
        data = stream.read()
    if data[:4] != b"glTF":
        return json.loads(data.decode("utf-8-sig"))
    if len(data) < 20:
        raise ValueError("truncated GLB header")
    magic, version, length = struct.unpack_from("<4sII", data)
    if version != 2 or length != len(data):
        raise ValueError("invalid GLB version or length")
    chunk_length, chunk_type = struct.unpack_from("<II", data, 12)
    if chunk_type != 0x4E4F534A or 20 + chunk_length > len(data):
        raise ValueError("missing or truncated GLB JSON chunk")
    return json.loads(data[20:20 + chunk_length].decode("utf-8"))


argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
p = argparse.ArgumentParser()
p.add_argument("path")
p.add_argument("--expect-clips", default="")
p.add_argument("--exact-clips", action="store_true", help="require exactly --expect-clips using original exported animation names")
p.add_argument("--require-mesh", action="store_true")
p.add_argument("--require-skin", action="store_true")
p.add_argument("--require-rig", action="store_true")
p.add_argument("--fps", type=fps_value, default=30.0)
p.add_argument("--json")
args = p.parse_args(argv)
expected = [name.strip() for name in args.expect_clips.split(",") if name.strip()]
if len(expected) != len(set(expected)):
    p.error("--expect-clips contains duplicate names")
source = read_gltf(args.path)
source_clips = [animation.get("name") for animation in source.get("animations", [])]

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.context.scene.render.fps = int(args.fps)
bpy.context.scene.render.fps_base = int(args.fps) / args.fps
bpy.ops.import_scene.gltf(filepath=args.path)
objects = bpy.context.scene.objects
meshes = [o for o in objects if o.type == "MESH"]
skinned = [o for o in meshes if any(m.type == "ARMATURE" for m in o.modifiers)]
arms = [o for o in objects if o.type == "ARMATURE"]
geometry = [o for o in meshes if o.data.vertices and o.data.polygons]
usable_skin = [o for o in geometry
               if any(m.type == "ARMATURE" and m.object and m.object.type == "ARMATURE" and m.object.data.bones
                      for m in o.modifiers)
               and any(g.weight > 0 for vertex in o.data.vertices for g in vertex.groups)]
rigs = [a for a in arms if a.data.bones]
print(f"MESHES {len(meshes)} (skinned {len(skinned)})  ARMATURES {len(arms)}  BONES {sum(len(a.data.bones) for a in arms)}")

problems = []
clips = {}
for act in bpy.data.actions:
    f0, f1 = act.frame_range
    clips[act.name] = [float(f0), float(f1)]
    print(f"CLIP {act.name}: frames {f0:g}-{f1:g}  duration {(f1 - f0) / args.fps:.3f} s")
    if abs(f0) > 1e-3:
        problems.append(f"clip {act.name} starts at frame {f0:g}, not 0")
for want in expected:
    if not any(name == want or name.startswith(want + "_") or name.startswith(want + ".") for name in clips):
        problems.append(f"expected clip {want} not found after import (have {sorted(clips)})")
if args.exact_clips:
    named = [name for name in source_clips if isinstance(name, str) and name]
    if len(named) != len(source_clips):
        problems.append("export contains unnamed animation clips")
    if len(named) != len(set(named)):
        problems.append("export contains duplicate animation clip names")
    missing, extra = sorted(set(expected) - set(named)), sorted(set(named) - set(expected))
    if missing:
        problems.append(f"expected exported clips missing: {missing}")
    if extra:
        problems.append(f"unexpected exported clips: {extra}")
if args.require_mesh and not geometry:
    problems.append("required mesh with vertices and polygons not found")
if args.require_skin and not usable_skin:
    problems.append("required weighted skinned mesh with geometry and a bone rig not found")
if args.require_rig and not rigs:
    problems.append("required armature with bones not found")
report = {"status": "fail" if problems else "pass", "meshes": len(meshes), "skinned_meshes": len(skinned),
          "armatures": len(arms), "bones": sum(len(a.data.bones) for a in arms),
          "clips": clips, "exported_clips": source_clips, "problems": problems,
          "requirements": {"exact_clips": args.exact_clips, "expected_clips": expected,
                           "mesh": args.require_mesh, "skin": args.require_skin, "rig": args.require_rig}}
for problem in problems:
    print("PROBLEM", problem)
if args.json:
    with open(args.json, "w") as stream:
        json.dump(report, stream, indent=2)
sys.exit(1 if problems else 0)
