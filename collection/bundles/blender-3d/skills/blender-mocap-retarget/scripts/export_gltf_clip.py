"""Export a rigged character to glTF/GLB with exactly one clip per named action.

  blender -b model.blend --python export_gltf_clip.py -- OUT.glb --rig Armature --actions Walk[,Run] \
      [--collection Character]

Why: exported clip time counts from scene frame 0, so an action starting at frame 1 arrives
offset by a frame. Each action is placed on its own NLA track, named
after the action, with its strip starting at frame 0, and exported in NLA_TRACKS mode. That gives
clips named exactly after the actions, starting at clip time 0 with no duplicated frame.
(ACTIVE_ACTIONS names the clip "Animation"; ACTIONS also exports unrelated actions such as an
imported source clip.) The NLA edits exist only in this process: the .blend is never saved.
Without --actions the model exports static. Only the given collection (default: all visible
objects) is exported, so keep motion-source imports in another collection.
"""
import argparse
import os
import sys

import bpy

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
p = argparse.ArgumentParser()
p.add_argument("out")
p.add_argument("--rig")
p.add_argument("--actions", default="")
p.add_argument("--collection")
p.add_argument("--no-yup", action="store_true", help="keep Blender Z-up instead of glTF Y-up")
args = p.parse_args(argv)

if args.collection:
    col = bpy.data.collections.get(args.collection)
    if col is None:
        raise SystemExit(f"no collection named {args.collection}")
    export_objects = list(col.all_objects)
else:
    export_objects = [o for o in bpy.context.scene.objects if o.visible_get()]

bpy.ops.object.select_all(action="DESELECT")
for ob in export_objects:
    ob.hide_set(False)
    ob.select_set(True)

kw = dict(filepath=os.path.abspath(args.out), export_format="GLB" if args.out.lower().endswith(".glb") else "GLTF_SEPARATE",
          use_selection=True, export_apply=False, export_yup=not args.no_yup, export_materials="EXPORT")

actions = [a for a in args.actions.split(",") if a]
if actions:
    rig = bpy.data.objects.get(args.rig or "")
    if rig is None or rig.type != "ARMATURE":
        raise SystemExit("--actions needs --rig with an armature object")
    if rig not in export_objects:
        raise SystemExit(f"rig {rig.name} is not among the exported objects")
    ad = rig.animation_data or rig.animation_data_create()
    for track in list(ad.nla_tracks):
        ad.nla_tracks.remove(track)
    for name in actions:
        act = bpy.data.actions.get(name)
        if act is None:
            raise SystemExit(f"no action named {name}")
        track = ad.nla_tracks.new()
        track.name = name
        track.strips.new(name, 0, act)
    ad.action = None
    kw.update(export_animations=True, export_animation_mode="NLA_TRACKS", export_skins=True,
              export_def_bones=False, export_frame_range=False)
else:
    kw.update(export_animations=False)

os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
bpy.ops.export_scene.gltf(**kw)
print(f"EXPORTED {len(export_objects)} object(s), clips {actions or 'none'} -> {args.out}")
