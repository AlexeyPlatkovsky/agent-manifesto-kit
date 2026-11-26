"""Shared neutral studio for every object of the scene (same as the post box studio, scaled to the object height).
Usage inside a build script (Blender, background):
    import sys, os; sys.path.insert(0, os.path.dirname(__file__)); import studio
    ... build the object (Z-up, front faces -Y, ground at z=0) ...
    studio.setup(SPEC)              # render settings, world, camera-relative light rig, shadow catcher, camera
    studio.save(ROOT, "object")     # -> blender/object.blend (render_views.py renders it)
Do not change the light values: all objects of the scene must be lit identically.
"""
import bpy, math, os
from mathutils import Vector


def _link(obj):
    bpy.context.scene.collection.objects.link(obj)
    return obj


def setup(spec):
    scene = bpy.context.scene
    scene.render.engine = "CYCLES"
    scene.cycles.samples = 128
    scene.cycles.use_denoising = True
    try:
        prefs = bpy.context.preferences.addons["cycles"].preferences
        prefs.compute_device_type = "METAL"
        prefs.get_devices()
        for d in prefs.devices:
            d.use = True
        scene.cycles.device = "GPU"
    except Exception as e:
        print("GPU setup failed, using CPU:", e)
    scene.render.film_transparent = True
    scene.render.resolution_x, scene.render.resolution_y = spec["cameras"]["image"]
    scene.render.resolution_percentage = 100
    scene.view_settings.view_transform = "Standard"
    try:
        scene.view_settings.look = "None"
    except Exception:
        pass
    scene.view_settings.exposure = -0.3
    world = bpy.data.worlds.new("studio")
    scene.world = world
    nt = world.node_tree
    bg = nt.nodes.get("Background") or nt.nodes.new("ShaderNodeBackground")
    bg.inputs["Color"].default_value = (1, 1, 1, 1)
    bg.inputs["Strength"].default_value = 0.16
    out = nt.nodes.get("World Output") or nt.nodes.new("ShaderNodeOutputWorld")
    nt.links.new(bg.outputs["Background"], out.inputs["Surface"])
    k = spec["height"] / 1.35  # post box studio scaled to this object's size
    ty = spec["cameras"].get("target_y", spec["height"] * 0.5)
    rig = _link(bpy.data.objects.new("light_rig", None))
    rig.location = (0, 0, ty)
    for name, az, el, dist, size, power in (("key", -40, 38, 4.0, 3.0, 210), ("fill", 55, 15, 4.0, 3.0, 85), ("rim", 170, 35, 4.0, 2.5, 70)):
        a, e = math.radians(az), math.radians(el)
        d = dist * k
        off = Vector((d * math.sin(a) * math.cos(e), -d * math.cos(a) * math.cos(e), d * math.sin(e)))
        ld = bpy.data.lights.new(name, "AREA"); ld.shape = "DISK"; ld.size = size * k; ld.energy = power * k * k
        lo = _link(bpy.data.objects.new(name, ld))
        lo.location = rig.location + off
        lo.rotation_euler = (-off).to_track_quat("-Z", "Y").to_euler()
        lo.parent = rig
        lo.location = off
    bpy.ops.mesh.primitive_plane_add(size=10 * k, location=(0, 0, 0))
    g = bpy.context.active_object; g.name = "shadow_catcher"; g.is_shadow_catcher = True
    cd = bpy.data.cameras.new("cam"); cd.sensor_fit = "VERTICAL"; cd.angle_y = math.radians(spec["cameras"]["fov_deg"])
    scene.camera = _link(bpy.data.objects.new("cam", cd))


def save(root, name="object"):
    os.makedirs(os.path.join(root, "blender"), exist_ok=True)
    path = os.path.join(root, "blender", f"{name}.blend")
    bpy.ops.wm.save_as_mainfile(filepath=path)
    print("saved", path)
