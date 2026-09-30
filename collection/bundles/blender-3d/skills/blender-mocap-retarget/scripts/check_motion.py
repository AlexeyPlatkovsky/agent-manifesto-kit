"""Per-frame motion QA for a rigged, animated character (read-only).

  blender -b model.blend --python check_motion.py -- --rig Armature \
      --feet Boot_L,Boot_R --pairs "Shirt@LeftForeArm:Belt;Shirt@RightForeArm:Pouch_R;Boot_L:Boot_R" [--json qa.json]

Checks over the scene frame range (or --frames A-B):
- ground: lowest point of each --feet part per frame; below -tolerance is penetration
- slide: horizontal travel of foot vertices that stay in floor contact between frames
- interpenetration: overlapping triangles per --pairs entry, minus the count already present
  in the rest pose (bridged seams and tucked cloth are not motion errors)
- loop seam: rotation difference between the action's first and last frame, and root delta

Neighbouring regions of one mesh share edges, and deforming them can register as overlap; pair
regions that should never touch (arm vs belt kit, arm vs torso front) rather than adjacent ones.
A part is an object name, optionally narrowed to polygons whose dominant vertex group contains a
substring: "Shirt@LeftArm" = Shirt polygons weighted mostly to a group containing "LeftArm".
Judge motion quality from playback renders too; these numbers catch regressions, not style.
"""
import argparse
import json
import math
import sys

import bpy
from mathutils.bvhtree import BVHTree

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
p = argparse.ArgumentParser()
p.add_argument("--rig", required=True)
p.add_argument("--feet", default="", help="comma-separated parts that touch the floor")
p.add_argument("--pairs", default="", help="semicolon-separated A:B part pairs to test for overlap")
p.add_argument("--frames", help="START-END; default is the scene range")
p.add_argument("--contact-mm", type=float, default=6.0, help="height that counts as floor contact")
p.add_argument("--ground-z", type=float, default=0.0)
p.add_argument("--json")
args = p.parse_args(argv)

scene = bpy.context.scene
rig = bpy.data.objects.get(args.rig)
if rig is None or rig.type != "ARMATURE":
    raise SystemExit(f"--rig: no armature object named {args.rig}")
f0, f1 = (int(x) for x in args.frames.split("-")) if args.frames else (scene.frame_start, scene.frame_end)
feet = [s for s in args.feet.split(",") if s]
pairs = [tuple(pair.split(":")) for pair in args.pairs.split(";") if pair]
contact = args.contact_mm / 1000.0


def parse(part):
    name, _, group = part.partition("@")
    ob = bpy.data.objects.get(name)
    if ob is None or ob.type != "MESH":
        raise SystemExit(f"no mesh object named {name}")
    return ob, group


def select_polys(ob, group):
    me = ob.data
    if not group:
        return [list(poly.vertices) for poly in me.polygons]
    names = {g.index: g.name for g in ob.vertex_groups}
    chosen = []
    for poly in me.polygons:
        acc = {}
        for vi in poly.vertices:
            for g in me.vertices[vi].groups:
                acc[g.group] = acc.get(g.group, 0.0) + g.weight
        if acc and group in names.get(max(acc, key=acc.get), ""):
            chosen.append(list(poly.vertices))
    if not chosen:
        raise SystemExit(f"no polygons of {ob.name} are dominated by a group containing '{group}'")
    return chosen


parts = sorted({p for pair in pairs for p in pair} | set(feet))
POLYS = {part: select_polys(*parse(part)) for part in parts}


def evaluate():
    dg = bpy.context.evaluated_depsgraph_get()
    verts = {}
    for part in parts:
        ob, _ = parse(part)
        if ob.name in verts:
            continue
        ev = ob.evaluated_get(dg)
        me = ev.to_mesh()
        if len(me.vertices) != len(ob.data.vertices):
            raise SystemExit(f"{ob.name}: modifiers change the vertex count; check_motion needs only deforming modifiers (Armature)")
        verts[ob.name] = [ob.matrix_world @ v.co for v in me.vertices]
        ev.to_mesh_clear()
    return verts


def overlaps(verts):
    trees = {part: BVHTree.FromPolygons(verts[parse(part)[0].name], POLYS[part]) for part in {p for pair in pairs for p in pair}}
    return {pair: len(trees[pair[0]].overlap(trees[pair[1]])) for pair in pairs}


rig.data.pose_position = "REST"
scene.frame_set(f0)
baseline = overlaps(evaluate())
rig.data.pose_position = "POSE"

ground, slide, hits = {f: [] for f in feet}, {f: [] for f in feet}, {pair: [] for pair in pairs}
prev = {}
for frame in range(f0, f1 + 1):
    scene.frame_set(frame)
    verts = evaluate()
    for pair, n in overlaps(verts).items():
        extra = n - baseline[pair]
        if extra > 0:
            hits[pair].append((frame, extra))
    for foot in feet:
        ob, _ = parse(foot)
        idx = sorted({i for poly in POLYS[foot] for i in poly})
        co = [verts[ob.name][i] for i in idx]
        low = min(c.z for c in co) - args.ground_z
        ground[foot].append((frame, low))
        touching = {i for i, c in zip(idx, co) if c.z - args.ground_z < contact}
        if foot in prev:
            both = touching & prev[foot][1]
            if both:
                pc = prev[foot][0]
                slide[foot].append((frame, max((verts[ob.name][i].xy - pc[i].xy).length for i in both)))
        prev[foot] = (verts[ob.name], touching)

report = {"frames": [f0, f1], "ground": {}, "slide": {}, "interpenetration": {}, "rest_baseline_overlaps": {}}
for foot in feet:
    lows = [z for _, z in ground[foot]]
    report["ground"][foot] = {"min_mm": round(min(lows) * 1000, 1), "contact_frames": sum(z < contact for z in lows)}
    if slide[foot]:
        vals = [v for _, v in slide[foot]]
        worst = max(slide[foot], key=lambda fv: fv[1])
        report["slide"][foot] = {"max_mm_per_frame": round(worst[1] * 1000, 1), "worst_frame": worst[0],
                                 "mean_mm_per_frame": round(sum(vals) / len(vals) * 1000, 1)}
for pair in pairs:
    key = f"{pair[0]} x {pair[1]}"
    report["rest_baseline_overlaps"][key] = baseline[pair]
    if hits[pair]:
        report["interpenetration"][key] = {"frames": len(hits[pair]), "max_extra_tris": max(n for _, n in hits[pair]),
                                           "first_frames": [f for f, _ in hits[pair]][:12]}

act = rig.animation_data.action if rig.animation_data else None
if act:
    a0, a1 = (int(round(v)) for v in act.frame_range)

    def pose(frame):
        scene.frame_set(frame)
        return {pb.name: (pb.matrix_basis.to_quaternion(), pb.matrix_basis.to_translation()) for pb in rig.pose.bones}

    pa, pb_ = pose(a0), pose(a1)
    worst = max(pa, key=lambda n: pa[n][0].rotation_difference(pb_[n][0]).angle)
    root = next(b.name for b in rig.data.bones if b.parent is None)
    report["loop_seam"] = {"action": act.name, "action_range": [a0, a1],
                           "max_rotation_diff_deg": round(math.degrees(pa[worst][0].rotation_difference(pb_[worst][0]).angle), 3),
                           "worst_bone": worst, "root_bone": root,
                           "root_delta_bone_space_m": [round(v, 4) for v in (pb_[root][1] - pa[root][1])]}

print(json.dumps(report, indent=2))
if args.json:
    with open(args.json, "w") as f:
        json.dump(report, f, indent=2)
