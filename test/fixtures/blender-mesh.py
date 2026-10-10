"""Evaluated mesh fixtures for connectivity and surface-overlap gates."""
import os
import sys
import bpy

bpy.ops.wm.read_factory_settings(use_empty=True)
material = bpy.data.materials.new("Fixture")


def mesh(name, collection, vertices, faces, edges=()):
    col = bpy.data.collections.get(collection)
    if col is None:
        col = bpy.data.collections.new(collection)
        bpy.context.scene.collection.children.link(col)
    data = bpy.data.meshes.new(name)
    data.from_pydata(vertices, edges, faces)
    ob = bpy.data.objects.new(name, data)
    col.objects.link(ob)
    data.materials.append(material)
    return ob


horizontal = [(-1, -1, .5), (1, -1, .5), (0, 1, .5)]
vertical = [(-.5, 0, 0), (.5, 0, 0), (0, 0, 1)]
cube = mesh("Cube", "Valid",
            [(-1, -1, -1), (1, -1, -1), (1, 1, -1), (-1, 1, -1),
             (-1, -1, 1), (1, -1, 1), (1, 1, 1), (-1, 1, 1)],
            [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4),
             (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)])
cube.modifiers.new("Evaluated triangles", "TRIANGULATE")
mesh("SharedVertex", "Valid",
     [(0, 0, 0), (1, 0, 0), (0, 1, 0), (-1, 0, 0), (0, 0, 1)],
     [(0, 1, 2), (0, 3, 4)])
mesh("Split", "Split", horizontal + [(x + 5, y, z) for x, y, z in horizontal],
     [(0, 1, 2), (3, 4, 5)])
mesh("Crossing", "Crossing", horizontal + vertical, [(0, 1, 2), (3, 4, 5)], [(0, 3)])
mesh("PairA", "Pairs", horizontal, [(0, 1, 2)])
pair_b = mesh("PairB", "Pairs", vertical, [(0, 1, 2)])
pair_b.location.x = 5  # PairB/C overlap only after applying object transforms.
pair_c = mesh("PairC", "Pairs", horizontal, [(0, 1, 2)])
pair_c.location.x = 5
mesh("BadHealth", "BadHealth", [(0, 0, 0), (1, 0, 0), (2, 0, 0), (0, 0, 1)], [(0, 1, 2)])
bpy.data.objects["BadHealth"].data.materials.clear()
mesh("Wire", "NoSurface", [(0, 0, 0), (1, 0, 0)], [], [(0, 1)])
mesh("NoVerts", "NoSurface", [], [])
empty = bpy.data.collections.new("Empty")
bpy.context.scene.collection.children.link(empty)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(sys.argv[sys.argv.index("--") + 1], "mesh.blend"))
