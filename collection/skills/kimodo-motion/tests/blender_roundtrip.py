"""Blender check for kimodo_retarget.py (run by test_kimodo_motion.py): a synthetic Mixamo-named rig with its own
proportions and bone rolls, a random pose, kimodo_pose (rig -> Kimodo) then bake (Kimodo -> rig) must give back every
mapped bone's world turn and the hips' height.

  blender -b --factory-startup --python-exit-code 1 --python blender_roundtrip.py
"""
import math
import os
import random
import sys
import tempfile

import bpy
from mathutils import Quaternion, Vector

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "scripts"))
import kimodo_motion as km  # noqa: E402
import kimodo_retarget as kr  # noqa: E402

rng = random.Random(3)
SCALE = 1.08                    # a taller rig than Kimodo's body
RIG_OF = {kj: hb for hb, (kj, *_) in kr.MAP.items()}
EXTRA = {}                      # rig-only bones: name -> (Kimodo joint for the head, parent rig bone)
for s in ("Left", "Right"):
    EXTRA[s + "HandMiddle1"] = (s + "HandMiddleEnd", s + "Hand")
    EXTRA[s + "HandThumb1"] = (s + "HandThumbEnd", s + "Hand")


def build_rig():
    rest = km.fk(km.OFFSETS[0], [km.IDENTITY] * len(km.NAMES))[1]
    head = {}
    for kj, hb in RIG_OF.items():
        head[hb] = kr.vk(rest[km.INDEX[kj]]) * SCALE + Vector([rng.uniform(-0.01, 0.01) for _ in range(3)])
    for name, (kj, _) in EXTRA.items():
        head[name] = kr.vk(rest[km.INDEX[kj]]) * SCALE
    parent = {}
    for kj, hb in RIG_OF.items():
        p = km.PARENTS[km.INDEX[kj]]
        while p >= 0 and km.NAMES[p] not in RIG_OF:     # Neck2 has no rig bone
            p = km.PARENTS[p]
        parent[hb] = RIG_OF[km.NAMES[p]] if p >= 0 else None
    parent.update({n: p for n, (_, p) in EXTRA.items()})
    children = {}
    for b, p in parent.items():
        children.setdefault(p, []).append(b)
    arm = bpy.data.armatures.new("rig")
    rig = bpy.data.objects.new("rig", arm)
    bpy.context.scene.collection.objects.link(rig)
    bpy.context.view_layer.objects.active = rig
    bpy.ops.object.mode_set(mode="EDIT")
    made = {}
    order, todo = [], [b for b, p in parent.items() if p is None]
    while todo:
        b = todo.pop(0)
        order.append(b)
        todo += sorted(children.get(b, []))
    for b in order:
        eb = arm.edit_bones.new(kr.pn(b))
        eb.head = head[b]
        kids = [c for c in children.get(b, []) if c not in EXTRA or b.endswith("Hand")]
        tail = sum((head[c] for c in kids), Vector()) / len(kids) if kids else head[b] + Vector((0, -0.05, 0.02))
        eb.tail = tail if (tail - eb.head).length > 1e-3 else eb.head + Vector((0, 0, 0.05))
        eb.roll = rng.uniform(-math.pi, math.pi)
        if parent[b]:
            eb.parent = made[parent[b]]
        made[b] = eb
    bpy.ops.object.mode_set(mode="POSE")
    return rig


def main():
    rig = build_rig()
    for pb in rig.pose.bones:
        pb.rotation_mode = "QUATERNION"
        name = pb.name[len(kr.PREFIX):]
        if name in kr.MAP and name not in ("Head", "LeftToeBase", "RightToeBase"):
            axis = Vector([rng.uniform(-1, 1) for _ in range(3)]).normalized()
            pb.rotation_quaternion = Quaternion(axis, rng.uniform(0.1, 0.6))
    rig.pose.bones[kr.pn("Hips")].location = Vector((0, 0.05, 0))     # bone-local: a lift or drop of the hips
    bpy.context.view_layer.update()
    want = {pb.name: pb.matrix.to_quaternion() for pb in rig.pose.bones}
    hips_z = rig.pose.bones[kr.pn("Hips")].head.z
    align = kr.setup(rig)
    root, local, worst = kr.kimodo_pose(rig, align)
    assert worst[0] < 0.5, f"direction on the pose {worst}"
    d = tempfile.mkdtemp()
    km.save(d, [root, root], [local, local])
    for pb in rig.pose.bones:
        pb.rotation_quaternion = Quaternion()
        pb.location = Vector()
    act, worst = kr.bake(rig, "trip", d, align)
    assert worst[0] < 0.5, f"direction after bake {worst}"
    bpy.context.scene.frame_set(1)
    bpy.context.view_layer.update()
    turn = max((math.degrees(want[pb.name].rotation_difference(pb.matrix.to_quaternion()).angle), pb.name)
               for pb in rig.pose.bones if pb.name[len(kr.PREFIX):] in kr.MAP)
    turn = (min(turn[0], 360 - turn[0]), turn[1])
    height = abs(rig.pose.bones[kr.pn("Hips")].head.z - hips_z)
    print(f"ROUNDTRIP worst bone turn {turn[0]:.4f} deg ({turn[1]}), hips height {height * 1000:.2f} mm")
    assert turn[0] < 0.1, turn
    assert height < 0.001, height
    print("PASS blender_roundtrip")


main()
