"""Per-object mesh health and cost report for a saved .blend (read-only).

  blender -b model.blend --python mesh_report.py -- [--collection NAME] [--exclude-prefix SRC_] [--json out.json] [--strict]

Reports evaluated triangles, vertices, non-manifold edges, zero-area faces, loose vertices,
empty material slots, origin and dimensions. Non-manifold edges are acceptable on deliberately
open shells (hems, cards); treat them as findings to explain, not automatic failures.
--strict exits non-zero when any object has degenerate faces, loose vertices or empty slots.
"""
import argparse
import json
import sys

import bmesh
import bpy

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
p = argparse.ArgumentParser()
p.add_argument("--collection")
p.add_argument("--exclude-prefix", default="")
p.add_argument("--json")
p.add_argument("--strict", action="store_true")
args = p.parse_args(argv)

if args.collection:
    col = bpy.data.collections.get(args.collection)
    if col is None:
        raise SystemExit(f"no collection named {args.collection}")
    objects = [o for o in col.all_objects if o.type == "MESH"]
else:
    objects = [o for o in bpy.context.scene.objects if o.type == "MESH"]
objects = [o for o in objects if not (args.exclude_prefix and o.name.startswith(args.exclude_prefix))]

dg = bpy.context.evaluated_depsgraph_get()
rows, problems = [], 0
for ob in sorted(objects, key=lambda o: o.name):
    ev = ob.evaluated_get(dg)
    me = ev.to_mesh()
    bm = bmesh.new()
    bm.from_mesh(me)
    row = {
        "object": ob.name,
        "tris": sum(len(f.verts) - 2 for f in bm.faces),
        "verts": len(bm.verts),
        "non_manifold_edges": sum(1 for e in bm.edges if not e.is_manifold),
        "degenerate_faces": sum(1 for f in bm.faces if f.calc_area() < 1e-10),
        "loose_verts": sum(1 for v in bm.verts if not v.link_edges),
        "empty_material_slots": sum(1 for s in ob.material_slots if s.material is None) + (0 if ob.material_slots else 1),
        "origin": [round(c, 4) for c in ob.matrix_world.translation],
        "dimensions": [round(c, 4) for c in ob.dimensions],
    }
    bm.free()
    ev.to_mesh_clear()
    problems += bool(row["degenerate_faces"] or row["loose_verts"] or row["empty_material_slots"])
    rows.append(row)

print(f"{'object':24s} {'tris':>6s} {'verts':>6s} {'nonman':>6s} {'degen':>5s} {'loose':>5s} {'nomat':>5s}  origin")
for r in rows:
    print(f"{r['object'][:24]:24s} {r['tris']:6d} {r['verts']:6d} {r['non_manifold_edges']:6d} {r['degenerate_faces']:5d} "
          f"{r['loose_verts']:5d} {r['empty_material_slots']:5d}  {tuple(r['origin'])}")
total = sum(r["tris"] for r in rows)
print(f"TOTAL {len(rows)} objects, {total} triangles; {problems} object(s) with degenerate faces, loose vertices or empty slots")
if args.json:
    with open(args.json, "w") as f:
        json.dump({"objects": rows, "total_tris": total}, f, indent=2)
if args.strict and problems:
    sys.exit(1)
