"""Small generated Blender fixture: deforming foot, collision pair, and real GLB exports."""
import os
import sys
import bpy

out = sys.argv[sys.argv.index("--") + 1]
os.makedirs(out, exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.frame_start, scene.frame_end = 0, 2

arm = bpy.data.armatures.new("Rig")
rig = bpy.data.objects.new("Rig", arm)
scene.collection.objects.link(rig)
bpy.context.view_layer.objects.active = rig
rig.select_set(True)
bpy.ops.object.mode_set(mode="EDIT")
bone = arm.edit_bones.new("Root")
bone.head, bone.tail = (0, 0, 0), (0, 0, 1)
bpy.ops.object.mode_set(mode="OBJECT")


def mesh(name, verts, faces):
    data = bpy.data.meshes.new(name)
    data.from_pydata(verts, [], faces)
    ob = bpy.data.objects.new(name, data)
    bpy.context.scene.collection.objects.link(ob)
    return ob


# Polygon vertices start at index 1, exercising original-index foot tracking.
foot = mesh("Foot", [(0, 0, 2), (0, 0, 0), (.2, 0, 0), (.2, .2, 0), (0, .2, 0)], [(1, 2, 3, 4)])
group = foot.vertex_groups.new(name="Root")
group.add(list(range(5)), 1.0, "REPLACE")
modifier = foot.modifiers.new("Rig", "ARMATURE")
modifier.object = rig
foot.parent = rig
pb = rig.pose.bones["Root"]
pb.rotation_mode = "XYZ"
for frame, x, z, angle in [(0, 0, 0, 0), (1, .01, -.002, .01), (2, .02, 0, .02)]:
    pb.location = (x, z, 0)  # bone local Y is world Z for this upright bone
    pb.rotation_euler = (0, angle, 0)
    pb.keyframe_insert("location", frame=frame)
    pb.keyframe_insert("rotation_euler", frame=frame)
rig.animation_data.action.name = "Walk"
walk = rig.animation_data.action
walk.use_fake_user = True

a = mesh("PairA", [(-1, -1, .5), (1, -1, .5), (0, 1, .5)], [(0, 1, 2)])
b = mesh("PairB", [(-.5, 0, 0), (.5, 0, 0), (0, 0, 1)], [(0, 1, 2)])
for frame, x in [(0, 2), (1, 0), (2, 2)]:
    b.location.x = x
    b.keyframe_insert("location", frame=frame)
scene.frame_set(0)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(out, "motion.blend"))

# Same rig but no active action: loop coverage must be unavailable.
rig.animation_data.action = None
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(out, "no-action.blend"))
rig.animation_data.action = bpy.data.actions.new("Empty")
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(out, "empty-action.blend"))
rig.animation_data.action = None
for frame, angle in [(.1, 0), (.4, .2)]:
    pb.rotation_euler = (0, angle, 0)
    pb.keyframe_insert("rotation_euler", frame=frame)
rig.animation_data.action.name = "SubframeSeam"
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(out, "subframe.blend"))
rig.animation_data.action = walk
scene.frame_set(0)

# An airborne requested foot has no planted transitions, even alongside a measured foot.
air = mesh("AirFoot", [(0, 0, 1), (.2, 0, 1), (0, .2, 1)], [(0, 1, 2)])
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(out, "air.blend"))

# Export genuine weighted geometry and two named NLA clips.
for ob in (a, b, air):
    bpy.data.objects.remove(ob, do_unlink=True)
run = walk.copy()
run.name = "Run"
run.use_fake_user = True
for act in (walk, run):
    track = rig.animation_data.nla_tracks.new()
    track.name = act.name
    track.strips.new(act.name, 0, act)
rig.animation_data.action = None
bpy.ops.export_scene.gltf(filepath=os.path.join(out, "rig.glb"), export_format="GLB",
                          export_animation_mode="NLA_TRACKS", export_frame_range=False,
                          export_skins=True, export_def_bones=False)

# Real static mesh export has geometry but no skin/rig/clips.
bpy.ops.wm.read_factory_settings(use_empty=True)
mesh("Static", [(0, 0, 0), (1, 0, 0), (0, 1, 0)], [(0, 1, 2)])
bpy.ops.export_scene.gltf(filepath=os.path.join(out, "static.glb"), export_format="GLB", export_animations=False)

# Empty scene export has no geometry, even though the GLB is structurally valid.
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.export_scene.gltf(filepath=os.path.join(out, "empty.glb"), export_format="GLB", export_animations=False)
