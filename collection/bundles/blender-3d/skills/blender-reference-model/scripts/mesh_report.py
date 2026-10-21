"""Per-object mesh health and cost report for a saved .blend (read-only).

  blender -b model.blend --python-exit-code 1 --python mesh_report.py -- [--collection NAME] [--exclude-prefix SRC_] [--json out.json] [--strict] [--organic] [--pairs A:B,C:D]

Reports evaluated triangles, vertices, non-manifold edges, zero-area faces, loose vertices,
empty material slots, origin and dimensions. Non-manifold edges are acceptable on deliberately
open shells (hems, cards); treat them as findings to explain, not automatic failures.
--strict exits non-zero when any object has degenerate faces, loose vertices or empty slots.
--organic also requires faces, one connected component and no self-overlap per scoped object.
Self-overlap ignores face pairs sharing vertices. --pairs reports world-space surface
overlaps between named scoped meshes; --strict or --organic rejects non-zero counts.
Missing surfaces report null (not_tested) and fail required pair checks.
BVH surface checks do not detect containment without surface intersections.
"""
import argparse
import json
import sys

import bmesh
import bpy
from mathutils.bvhtree import BVHTree

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
p = argparse.ArgumentParser()
p.add_argument("--collection")
p.add_argument("--exclude-prefix", default="")
p.add_argument("--json")
p.add_argument("--strict", action="store_true")
p.add_argument("--organic", action="store_true")
p.add_argument("--pairs", default="")
args = p.parse_args(argv)

if args.collection:
    col = bpy.data.collections.get(args.collection)
    if col is None:
        raise SystemExit(f"no collection named {args.collection}")
    objects = [o for o in col.all_objects if o.type == "MESH"]
else:
    objects = [o for o in bpy.context.scene.objects if o.type == "MESH"]
objects = [o for o in objects if not (args.exclude_prefix and o.name.startswith(args.exclude_prefix))]
scoped = {o.name: o for o in objects}
pairs = []
for value in args.pairs.split(",") if args.pairs else []:
    names = value.split(":")
    if len(names) != 2 or names[0] == names[1] or any(n not in scoped for n in names):
        p.error(f"pair must name two distinct scoped meshes: {value}")
    pairs.append(tuple(names))
pair_names = {name for pair in pairs for name in pair}

dg = bpy.context.evaluated_depsgraph_get()
rows, problems = [], 0
trees = {}
for ob in sorted(objects, key=lambda o: o.name):
    ev = ob.evaluated_get(dg)
    me = ev.to_mesh()
    bm = bmesh.new()
    bm.from_mesh(me)
    degenerate_faces = sum(1 for f in bm.faces if f.calc_area() < 1e-10)
    unseen = set(bm.verts)
    components = 0
    while unseen:
        components += 1
        pending = [unseen.pop()]
        while pending:
            for edge in pending.pop().link_edges:
                for vertex in edge.verts:
                    if vertex in unseen:
                        unseen.remove(vertex)
                        pending.append(vertex)
    self_overlaps = None
    if args.organic or ob.name in pair_names:
        bm.faces.ensure_lookup_table()
        bm.faces.index_update()
        bm.transform(ob.matrix_world)
        tree = BVHTree.FromBMesh(bm) if bm.faces else None
        if ob.name in pair_names:
            trees[ob.name] = tree
        if args.organic and tree is not None:
            face_verts = [set(f.verts) for f in bm.faces]
            self_overlaps = sum(1 for a, b in tree.overlap(tree)
                                if a < b and not face_verts[a].intersection(face_verts[b]))
    row = {
        "object": ob.name,
        "tris": sum(len(f.verts) - 2 for f in bm.faces),
        "verts": len(bm.verts),
        "components": components,
        "self_overlap_pairs": self_overlaps,
        "non_manifold_edges": sum(1 for e in bm.edges if not e.is_manifold),
        "degenerate_faces": degenerate_faces,
        "loose_verts": sum(1 for v in bm.verts if not v.link_edges),
        "empty_material_slots": sum(1 for s in ob.material_slots if s.material is None) + (0 if ob.material_slots else 1),
        "origin": [round(c, 4) for c in ob.matrix_world.translation],
        "dimensions": [round(c, 4) for c in ob.dimensions],
    }
    bm.free()
    ev.to_mesh_clear()
    problems += bool(row["degenerate_faces"] or row["loose_verts"] or row["empty_material_slots"]
                     or (args.organic and (not row["tris"] or components != 1 or self_overlaps)))
    rows.append(row)

overlaps = {f"{a} x {b}": len(trees[a].overlap(trees[b]))
            if trees[a] is not None and trees[b] is not None else None for a, b in pairs}
problems += sum(count is None or count > 0 for count in overlaps.values())
if not objects and (args.strict or args.organic):
    problems += 1

print(f"{'object':24s} {'tris':>6s} {'verts':>6s} {'parts':>5s} {'self':>5s} {'nonman':>6s} {'degen':>5s} {'loose':>5s} {'nomat':>5s}  origin")
for r in rows:
    overlap_text = "-" if r["self_overlap_pairs"] is None else str(r["self_overlap_pairs"])
    print(f"{r['object'][:24]:24s} {r['tris']:6d} {r['verts']:6d} {r['components']:5d} {overlap_text:>5s} {r['non_manifold_edges']:6d} {r['degenerate_faces']:5d} "
          f"{r['loose_verts']:5d} {r['empty_material_slots']:5d}  {tuple(r['origin'])}")
for pair, count in overlaps.items():
    print(f"OVERLAP {pair}: {count if count is not None else 'not_tested'} face pair(s)")
total = sum(r["tris"] for r in rows)
print(f"TOTAL {len(rows)} objects, {total} triangles; {problems} failing check(s)")
if args.json:
    with open(args.json, "w") as f:
        json.dump({"objects": rows, "total_tris": total, "organic_checked": args.organic,
                   "pair_overlaps": overlaps}, f, indent=2)
if (args.strict or args.organic) and problems:
    sys.exit(1)
