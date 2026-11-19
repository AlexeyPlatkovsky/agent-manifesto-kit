"""Build a three-part rigged unit for the machine-builder validate.py test: <out.blend> ok|collide."""
import bpy, sys
argv = sys.argv[sys.argv.index("--") + 1:]
out, collide = argv[0], argv[1] == "collide"
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.object.armature_add(location=(0, 0, 0))
arm = bpy.context.object
bpy.ops.object.mode_set(mode="EDIT")
eb = arm.data.edit_bones
root = eb[0]; root.name = "root"; root.head = (0, 0, 0); root.tail = (0, 0, 0.5)
pel = eb.new("pelvis"); pel.head = (0, 0, 0.5); pel.tail = (0, 0, 1.0); pel.parent = root
tor = eb.new("torso"); tor.head = (0, 0, 1.0); tor.tail = (0, 0, 2.0); tor.parent = pel
arm_b = eb.new("arm"); arm_b.head = (0.8, 0, 1.8); arm_b.tail = (1.6, 0, 1.8); arm_b.parent = tor
bpy.ops.object.mode_set(mode="OBJECT")
def part(name, bone, loc, size, **props):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
    o = bpy.context.object; o.name = name; o.scale = size
    bpy.ops.object.transform_apply(scale=True)
    mw = o.matrix_world.copy()
    o.parent = arm; o.parent_type = "BONE"; o.parent_bone = bone
    o.matrix_world = mw
    for k, v in props.items(): o[k] = v
part("ll__foot", "root", (0, 0, 0.1), (1.2, 1.2, 0.2), contact=True)
part("ct__torso", "torso", (0, 0, 1.5), (0.8, 0.8, 0.8))
# root is not connected to arm; in "collide" mode the arm part reaches down into the foot
part("ra__arm", "arm", (1.2, 0, 1.8) if not collide else (0.3, 0, 0.15), (0.6, 0.3, 0.3))
bpy.ops.object.empty_add(location=(0, 0, 2)); bpy.context.object.name = "socket_gun"
bpy.ops.wm.save_as_mainfile(filepath=out)
