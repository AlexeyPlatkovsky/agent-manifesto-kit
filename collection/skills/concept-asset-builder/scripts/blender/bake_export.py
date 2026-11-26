"""Bake the procedural Cycles look of blender/object.blend into textures and export out/object.glb.

Run: Blender -b --factory-startup blender/object.blend --python blender/bake_export.py -- [--res 2048] [--samples 64]
Bakes base colour (incl. procedural chips / drips / crevice grime), ambient occlusion, roughness and the
tangent-space normal of the bump detail onto one atlas UV, multiplies AO into the base colour (static prop),
and exports a single-material GLB for the three.js viewer (pipeline C).
"""
import bpy, os, sys
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
RES = int(argv[argv.index("--res") + 1]) if "--res" in argv else 2048
SAMPLES = int(argv[argv.index("--samples") + 1]) if "--samples" in argv else 64
TEXDIR = os.path.join(ROOT, "out/glb_tex")
os.makedirs(TEXDIR, exist_ok=True)

scene = bpy.context.scene
scene.render.engine = "CYCLES"
scene.cycles.samples = SAMPLES
dg = bpy.context.evaluated_depsgraph_get()

# 1. evaluated copies of every visible part, joined into one object at the origin
parts = []
for o in list(scene.objects):
    if o.type != "MESH" or o.hide_render or o.is_shadow_catcher:
        continue
    oe = o.evaluated_get(dg)
    me = bpy.data.meshes.new_from_object(oe, preserve_all_data_layers=True, depsgraph=dg)
    me.transform(o.matrix_world)
    no = bpy.data.objects.new(o.name + "_eval", me)
    scene.collection.objects.link(no)
    parts.append(no)
for o in list(scene.objects):
    if o not in parts and o.type == "MESH":
        o.hide_render = True
        o.hide_set(True)

bpy.ops.object.select_all(action="DESELECT")
for p in parts:
    p.select_set(True)
    if not p.data.uv_layers:
        p.data.uv_layers.new(name="UVMap")
    for i, slot in enumerate(p.material_slots):
        if slot.material is None:
            slot.material = next((m for m in bpy.data.materials if m.users), None)
bpy.context.view_layer.objects.active = parts[0]

# 2. one shared atlas UV over all parts (multi-object edit packs every island into the same 0-1 space).
# Parts stay SEPARATE while baking: joined, the Bevel/AO masks saw the joints (hood/body, mark/body) as edges
# and baked light outlines around them (user r6: "noise along the edges" in C).
for p in parts:
    uvl = p.data.uv_layers.new(name="bake")
    p.data.uv_layers.active = uvl
bpy.ops.object.mode_set(mode="EDIT")
bpy.ops.mesh.select_all(action="SELECT")
bpy.ops.uv.smart_project(angle_limit=1.15, island_margin=0.006, area_weight=0.0, scale_to_bounds=True)
try:
    bpy.ops.uv.pack_islands(margin=0.006, rotate=True)
except Exception as e:
    print("pack_islands skipped:", e)
bpy.ops.object.mode_set(mode="OBJECT")
mats = {s_.material for p in parts for s_ in p.material_slots if s_.material}


# 3. bake helpers
def target_image(name, non_color=False):
    img = bpy.data.images.new(name, RES, RES, alpha=False, float_buffer=False)
    if non_color:
        img.colorspace_settings.name = "Non-Color"
    for mat_ in mats:
        nt = mat_.node_tree
        n = nt.nodes.get("__bake__") or nt.nodes.new("ShaderNodeTexImage")
        n.name = "__bake__"
        n.image = img
        nt.nodes.active = n
    return img


def bake(kind, img, **kw):
    bpy.ops.object.select_all(action="DESELECT")
    for p in parts:
        p.select_set(True)
    bpy.context.view_layer.objects.active = parts[0]
    bpy.ops.object.bake(type=kind, margin=12, use_clear=True, uv_layer="bake", **kw)
    path = os.path.join(TEXDIR, img.name + ".png")
    img.filepath_raw = path
    img.file_format = "PNG"
    img.save()
    print("baked", kind, "->", path)
    return img


col = bake("DIFFUSE", target_image("basecolor_raw"), pass_filter={"COLOR"})
ao = bake("AO", target_image("ao", non_color=True))
rough = bake("ROUGHNESS", target_image("roughness", non_color=True))
nrm = bake("NORMAL", target_image("normal", non_color=True), normal_space="TANGENT")


def px(img):
    a = np.empty(RES * RES * 4, np.float32)
    img.pixels.foreach_get(a)
    return a.reshape(RES, RES, 4)


# 4. AO into base colour (sRGB display values are stored in pixels for byte images)
c, a = px(col), px(ao)
aof = 0.55 + 0.45 * a[..., :1]
out = c.copy()
out[..., :3] = np.clip(c[..., :3] * aof, 0, 1)
final = bpy.data.images.new("basecolor", RES, RES, alpha=False)
final.pixels.foreach_set(out.ravel())
final.filepath_raw = os.path.join(TEXDIR, "basecolor.png")
final.file_format = "PNG"
final.save()

# 5. join the parts now (after baking) and give them a single glTF-friendly material
bpy.ops.object.select_all(action="DESELECT")
for p in parts:
    p.select_set(True)
bpy.context.view_layer.objects.active = parts[0]
bpy.ops.object.join()
obj = bpy.context.view_layer.objects.active
obj.name = "object"
me = obj.data

mat = bpy.data.materials.new("object_baked")
nt = mat.node_tree
for n in list(nt.nodes):
    nt.nodes.remove(n)
outn = nt.nodes.new("ShaderNodeOutputMaterial")
bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
nt.links.new(bsdf.outputs["BSDF"], outn.inputs["Surface"])
uvn = nt.nodes.new("ShaderNodeUVMap")
uvn.uv_map = "bake"


def tex(img_path, non_color):
    t = nt.nodes.new("ShaderNodeTexImage")
    t.image = bpy.data.images.load(img_path)
    if non_color:
        t.image.colorspace_settings.name = "Non-Color"
    nt.links.new(uvn.outputs["UV"], t.inputs["Vector"])
    return t


tb = tex(os.path.join(TEXDIR, "basecolor.png"), False)
nt.links.new(tb.outputs["Color"], bsdf.inputs["Base Color"])
tr = tex(os.path.join(TEXDIR, "roughness.png"), True)
sep = nt.nodes.new("ShaderNodeSeparateColor")
nt.links.new(tr.outputs["Color"], sep.inputs["Color"])
nt.links.new(sep.outputs[0], bsdf.inputs["Roughness"])
bsdf.inputs["Metallic"].default_value = 0.0
tn = tex(os.path.join(TEXDIR, "normal.png"), True)
nm = nt.nodes.new("ShaderNodeNormalMap")
nm.uv_map = "bake"
nt.links.new(tn.outputs["Color"], nm.inputs["Color"])
nt.links.new(nm.outputs["Normal"], bsdf.inputs["Normal"])

me.materials.clear()
me.materials.append(mat)
for poly in me.polygons:
    poly.material_index = 0
for uvl in [u for u in me.uv_layers if u.name != "bake"]:
    me.uv_layers.remove(uvl)

bpy.ops.object.select_all(action="DESELECT")
obj.select_set(True)
bpy.context.view_layer.objects.active = obj
glb = os.path.join(ROOT, "out/object.glb")
bpy.ops.export_scene.gltf(filepath=glb, export_format="GLB", use_selection=True, export_yup=True,
                          export_apply=True, export_normals=True, export_tangents=True, export_materials="EXPORT")
print("exported", glb, "tris:", sum(len(p.vertices) - 2 for p in me.polygons))
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(ROOT, "blender/object_baked.blend"))
