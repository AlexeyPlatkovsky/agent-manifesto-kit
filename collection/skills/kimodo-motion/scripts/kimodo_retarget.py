"""Kimodo SOMA30 motions to and from a Mixamo-named Blender rig (rotation copy through both rests). Runs in Blender.

  blender -b RIG.blend --factory-startup --python-exit-code 1 --python kimodo_retarget.py -- \
      keypose NAME=ACTION.blend[@FRAME] [...] --out POSES.json [--toe-y M] [--prefix mixamorig:]
      each action's pose on the rig (an action-only .blend: its first action, applied at FRAME, default its first)
      as a Kimodo key pose {"poses": {NAME: {"root", "local_xyzw", ...}}}, the root raised or lowered so the lower toe
      stands at --toe-y (Kimodo's own standing height, about 0.015 m), then this script's direction check on it
  blender -b RIG.blend --factory-startup --python-exit-code 1 --python kimodo_retarget.py -- \
      retarget --clip NAME=MOTION_DIR [...] --out CLIPS.glb [--report REPORT.json] [--prefix mixamorig:]
      each motion baked onto the rig as an action (every mapped bone's world turn copied, only the hips moved,
      scaled by the hips' rest heights), exported together; fails above DIRECTION_TOL_DEG (the report is written,
      no GLB)

The rig: one armature, Mixamo bone names (with --prefix), Z up, facing -Y (Blender's Mixamo import), with Hips, Spine,
Spine1, Spine2, Neck, Head, Left/Right Shoulder, Arm, ForeArm, Hand, HandMiddle1, HandThumb1, UpLeg, Leg, Foot,
ToeBase. Kimodo's Leg is Mixamo's UpLeg, its Shin Mixamo's Leg; Neck2 has no Mixamo bone. The rests are aligned once
(each rig bone's rest frame turned onto the Kimodo T-pose frame: the bone toward its mapped child and one side
vector, hands by the middle finger and the thumb). Unmapped rig bones (fingers, toe ends) keep their rest; Kimodo
has no fingers, so add finger poses in the consumer project. The check: every mapped bone's direction against
Kimodo's, on every frame (retarget) or on the pose (keypose).
"""
import json
import math
import os
import sys

import bpy
from mathutils import Matrix, Quaternion, Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kimodo_motion as km  # noqa: E402

DIRECTION_TOL_DEG = 3.0
FWD, SIDE, UP = Vector((0, -1, 0)), Vector((1, 0, 0)), Vector((0, 0, 1))
# rig bone (no prefix) -> (Kimodo joint, Kimodo child for the direction, rig child, side vector)
MAP = {
    "Hips": ("Hips", "Spine1", "Spine", FWD),
    "Spine": ("Spine1", "Spine2", "Spine1", FWD),
    "Spine1": ("Spine2", "Chest", "Spine2", FWD),
    "Spine2": ("Chest", "Neck1", "Neck", FWD),
    "Neck": ("Neck1", "Head", "Head", FWD),
    "Head": ("Head", None, None, FWD),
}
for _s in ("Left", "Right"):
    MAP.update({
        _s + "Shoulder": (_s + "Shoulder", _s + "Arm", _s + "Arm", FWD),
        _s + "Arm": (_s + "Arm", _s + "ForeArm", _s + "ForeArm", FWD),
        _s + "ForeArm": (_s + "ForeArm", _s + "Hand", _s + "Hand", FWD),
        _s + "Hand": (_s + "Hand", _s + "HandMiddleEnd", _s + "HandMiddle1", "thumb"),
        _s + "UpLeg": (_s + "Leg", _s + "Shin", _s + "Leg", FWD),
        _s + "Leg": (_s + "Shin", _s + "Foot", _s + "Foot", FWD),
        _s + "Foot": (_s + "Foot", _s + "ToeBase", _s + "ToeBase", SIDE),
        _s + "ToeBase": (_s + "ToeBase", None, None, SIDE),
    })
C = Quaternion((1, 0, 0), math.radians(90))     # Kimodo (Y up, +Z forward) into Blender (Z up, -Y forward)
PREFIX = "mixamorig:"


def pn(name):
    return PREFIX + name


def qk(q):
    return Quaternion((q[3], q[0], q[1], q[2]))


def vk(v):
    return C @ Vector(v)


def frame(primary, side):
    y = primary.normalized()
    z = side.cross(y).normalized()
    x = y.cross(z)
    return Matrix((x, y, z)).transposed().to_quaternion()


def rest_rot(b):
    return b.matrix_local.to_quaternion()


def setup(rig):
    """Per mapped bone the alignment A (rig rest frame -> Kimodo rest frame)."""
    bones = rig.data.bones
    missing = [pn(n) for n in list(MAP) + [s + f for s in ("Left", "Right") for f in ("HandMiddle1", "HandThumb1")]
               if pn(n) not in bones]
    if missing:
        raise SystemExit(f"FAIL rig lacks {missing} (prefix {PREFIX!r})")
    rest_pos = km.fk(km.OFFSETS[0], [km.IDENTITY] * len(km.NAMES))[1]
    align = {}
    for hb, (kj, kc, hc, side) in MAP.items():
        b = bones[pn(hb)]
        if kc is None:          # the head and the toes: up and forward
            k1 = h1 = UP if hb == "Head" else FWD
            k2 = h2 = FWD if hb == "Head" else UP
        else:
            k1 = vk(rest_pos[km.INDEX[kc]]) - vk(rest_pos[km.INDEX[kj]])
            h1 = bones[pn(hc)].head_local - b.head_local
            if side == "thumb":
                k2 = vk(rest_pos[km.INDEX[hb + "ThumbEnd"]]) - vk(rest_pos[km.INDEX[kj]])
                h2 = bones[pn(hb + "Thumb1")].head_local - b.head_local
                k2, h2 = k2 - k2.project(k1), h2 - h2.project(h1)
            else:
                k2 = h2 = side
        align[hb] = frame(k1, k2) @ frame(h1, h2).inverted()
    return align


def direction_worst(rig, kp):
    """Largest angle (deg) between a mapped rig bone's posed direction and Kimodo's, and that bone."""
    worst = (0.0, "")
    for short, (kj, kc, hc, _) in MAP.items():
        if kc is not None:
            h = rig.pose.bones[pn(hc)].head - rig.pose.bones[pn(short)].head
            worst = max(worst, (math.degrees(h.angle(vk(kp[km.INDEX[kc]]) - vk(kp[km.INDEX[kj]]))), short))
    return worst


def kimodo_pose(rig, align):
    """The rig's current pose as Kimodo's root (metres, Y up) and local rotations (xyzw): mapped joints take their
    rig bone's world turn through the alignment, the rest stay unturned against their parent. Returns (root, local,
    the direction check)."""
    bones = rig.data.bones
    hips_scale = bones[pn("Hips")].head_local.z / km.OFFSETS[0][1]
    rig_of = {kj: hb for hb, (kj, *_) in MAP.items()}
    world = []
    for j, name in enumerate(km.NAMES):
        hb = rig_of.get(name)
        if hb is None:
            world.append(world[km.PARENTS[j]])
            continue
        w = rig.pose.bones[pn(hb)].matrix.to_quaternion()
        world.append((C.inverted() @ w @ rest_rot(bones[pn(hb)]).inverted() @ align[hb].inverted() @ C).normalized())
    local = []
    for j, p in enumerate(km.PARENTS):
        q = world[j] if p < 0 else world[p].inverted() @ world[j]
        local.append((q.x, q.y, q.z, q.w))
    root = tuple(C.inverted() @ (rig.pose.bones[pn("Hips")].head / hips_scale))
    return root, local, direction_worst(rig, km.fk(root, local)[1])


def load_action(path, name):
    """The first action of an action-only .blend."""
    with bpy.data.libraries.load(path) as (src, dst):
        dst.actions = src.actions[:1]
    if not dst.actions:
        raise SystemExit(f"FAIL no action in {path}")
    dst.actions[0].name = name
    return dst.actions[0]


def apply(rig, act, frame_no):
    rig.animation_data_create()
    rig.animation_data.action = act
    if hasattr(rig.animation_data, "action_slot") and act.slots:
        rig.animation_data.action_slot = act.slots[0]
    bpy.context.scene.frame_set(int(frame_no))
    bpy.context.view_layer.update()


def keypose_cmd(rig, specs, out, toe_y):
    align = setup(rig)
    result = {}
    for spec in specs:
        name, path = spec.split("=", 1)
        path, _, at = path.partition("@")
        act = load_action(os.path.abspath(path), name)
        frame_no = int(at) if at else int(act.frame_range[0])
        apply(rig, act, frame_no)
        root, local, worst = kimodo_pose(rig, align)
        pos = km.fk(root, local)[1]
        shift = toe_y - min(pos[km.INDEX["LeftToeBase"]][1], pos[km.INDEX["RightToeBase"]][1])
        result[name] = {"source": os.path.abspath(path), "frame": frame_no,
                        "root": [root[0], root[1] + shift, root[2]], "local_xyzw": [list(q) for q in local],
                        "ground_shift_m": round(shift, 4), "direction_worst_deg": round(worst[0], 2),
                        "direction_worst_bone": worst[1]}
        print(f"KEYPOSE {name}: {path}@{frame_no} ground shift {shift * 1000:.0f} mm, direction worst {worst[0]:.2f} "
              f"deg ({worst[1]})")
        if worst[0] > DIRECTION_TOL_DEG:
            raise SystemExit(f"FAIL keypose {name}: direction {worst[0]:.2f} deg > {DIRECTION_TOL_DEG}")
    with open(out, "w") as fh:
        json.dump({"_doc": "Kimodo key poses (SOMA30: root metres Y up, local xyzw)", "poses": result}, fh, indent=1)
    print("POSES", out)


def bake(rig, name, motion_dir, align):
    """One motion as an action on the rig; returns it and the worst direction (deg, bone, frame)."""
    roots, rots = km.load(motion_dir)
    bones = rig.data.bones
    hips_scale = bones[pn("Hips")].head_local.z / km.OFFSETS[0][1]
    act = bpy.data.actions.new(name)
    rig.animation_data_create()
    rig.animation_data.action = act
    for pb in rig.pose.bones:
        pb.rotation_mode = "QUATERNION"
    worst, last = (0.0, "", 0), {}
    for f in range(len(roots)):
        kw, kp = km.fk(roots[f], rots[f])
        world = {}
        for b in bones:                 # parents come before children in Blender's bone list
            short = b.name[len(PREFIX):] if b.name.startswith(PREFIX) else b.name
            parent = b.parent
            rel = (rest_rot(parent).inverted() @ rest_rot(b)) if parent else rest_rot(b)
            if short in MAP:
                w = C @ qk(kw[km.INDEX[MAP[short][0]]]) @ C.inverted() @ align[short] @ rest_rot(b)
                basis = rel.inverted() @ (world[parent.name].inverted() if parent else Quaternion()) @ w
            else:
                basis = Quaternion()
                w = (world[parent.name] @ rel) if parent else rel
            world[b.name] = w
            basis = basis.normalized()
            if b.name in last and last[b.name].dot(basis) < 0:      # one hemisphere: no flips between keys
                basis = -basis
            last[b.name] = basis
            pb = rig.pose.bones[b.name]
            pb.rotation_quaternion = basis
            pb.keyframe_insert("rotation_quaternion", frame=f + 1)
        root = roots[f]
        target = vk((root[0] - roots[0][0], root[1], root[2] - roots[0][2])) * hips_scale
        hips = bones[pn("Hips")]
        rig.pose.bones[hips.name].location = rest_rot(hips).inverted() @ (target - hips.head_local)
        rig.pose.bones[hips.name].keyframe_insert("location", frame=f + 1)
        bpy.context.scene.frame_set(f + 1)
        angle, bone = direction_worst(rig, kp)
        if angle > worst[0]:
            worst = (angle, bone, f)
    act.frame_range = (1, len(roots))
    act.use_fake_user = True
    return act, worst


def retarget_cmd(rig, clips, out, report_path):
    align = setup(rig)
    report, failed = {}, []
    for name, motion in clips:
        act, worst = bake(rig, name, os.path.abspath(motion), align)
        report[name] = {"motion": os.path.abspath(motion), "frames": round(act.frame_range[1]),
                        "direction_worst_deg": round(worst[0], 2), "direction_worst_bone": worst[1],
                        "direction_worst_frame": worst[2]}
        print(f"DIRECTION {name}: worst {worst[0]:.2f} deg ({worst[1]}, frame {worst[2]})")
        if worst[0] > DIRECTION_TOL_DEG:
            failed.append(f"{name}: direction {worst[0]:.2f} > {DIRECTION_TOL_DEG}")
    if report_path:
        with open(report_path, "w") as fh:
            json.dump(report, fh, indent=1)
    if failed:                          # before the export: a failed bake never replaces an existing GLB
        raise SystemExit("FAIL kimodo_retarget: " + "; ".join(failed))
    rig.animation_data.action = bpy.data.actions[clips[0][0]]
    bpy.ops.object.select_all(action="DESELECT")
    rig.select_set(True)
    bpy.context.view_layer.objects.active = rig
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    bpy.ops.export_scene.gltf(filepath=os.path.abspath(out), export_format="GLB", use_selection=True,
                              export_animations=True, export_animation_mode="ACTIONS", export_force_sampling=True,
                              export_skins=True, export_yup=True)
    print("PASS kimodo_retarget:", out, [n for n, _ in clips])


def main():
    global PREFIX
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    PREFIX = km.flag(argv, "--prefix", PREFIX)
    rigs = [o for o in bpy.data.objects if o.type == "ARMATURE"]
    if len(rigs) != 1:
        raise SystemExit(f"FAIL expected one armature, found {len(rigs)}")
    rig = rigs[0]
    values = ("--out", "--report", "--prefix", "--toe-y", "--clip")
    positional = [a for i, a in enumerate(argv[1:], 1) if not a.startswith("--") and argv[i - 1] not in values]
    if argv and argv[0] == "keypose":
        keypose_cmd(rig, positional, km.flag(argv, "--out"), float(km.flag(argv, "--toe-y", km.TOE_Y)))
    elif argv and argv[0] == "retarget":
        clips = [a.split("=", 1) for i, a in enumerate(argv) if i and argv[i - 1] == "--clip"]
        retarget_cmd(rig, clips, km.flag(argv, "--out"), km.flag(argv, "--report"))
    else:
        print(__doc__)
        raise SystemExit(2)


if __name__ == "__main__":
    main()
