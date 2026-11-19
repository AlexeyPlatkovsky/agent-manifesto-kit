"""Validate a machine built from rigid parts parented to armature bones.

blender -b unit.blend --python-exit-code 1 --python validate.py -- --spec spec.yaml --out report.json

Exits 0 when every check passes and 1 otherwise. Any error (bad spec, unknown bone, missing armature)
also exits 1 and writes a report with "passed": false, so a stale passing report never survives a crash.

Checks, per test pose and sweep step from the spec:
  - collisions between parts that are not on the same or directly connected bones
  - centre of mass over the support polygon of the contact parts (when the ground check applies)
Plus static checks: part count, triangles, loose islands per part, missing sockets, unparented meshes.

Part custom properties (optional): "density" (default 1.0), "contact" (True for feet/tracks/wheels),
"max_islands" (default 1).
Spec keys used:
  test_poses {pose: {bone: VALUE}}         VALUE = [x, y, z] rotation in degrees,
                                           or {"rot": [x, y, z], "loc": [x, y, z]} (loc in bone-local metres,
                                           e.g. suspension travel)
  sweeps {name: {bone, axis, from, to, step, pose?}}   pose = a base pose (same format) applied first,
                                           e.g. a turret sweep at full gun depression
  hardpoints [{id}], allowed_contacts [[partA, partB]], budgets {tris_lod0}, min_support_margin_m,
  profile (walker/tracked/wheeled/hover/rotorcraft/fixed_wing/static),
  ground_check (overrides the profile default), ground_check_poses [pose names] (check only these poses,
  e.g. gear_down for a rotorcraft).

Rotations are Euler XYZ in Blender BONE-LOCAL space: Y runs along the bone (twist / yaw of an upright bone),
X and Z bend it. A torso twist on an upright torso bone is [0, angle, 0].
"""
import json
import math
import os
import sys

import bmesh
import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree

GROUND_PROFILES = ("walker", "tracked", "wheeled", "static")
AXIS = {"x": 0, "y": 1, "z": 2}


class SpecError(Exception):
    pass


def load_spec(path):
    with open(path) as f:
        if path.endswith(".json"):
            return json.load(f)
        try:
            import yaml
        except ImportError as e:
            raise SpecError("PyYAML missing in Blender's Python: install it or pass a .json copy of the spec") from e
        return yaml.safe_load(f)


def vec3(value, what):
    if not isinstance(value, (list, tuple)) or len(value) != 3 or not all(isinstance(v, (int, float)) for v in value):
        raise SpecError(f"{what} must be three numbers, got {value!r}")
    return [float(v) for v in value]


def normalise_pose(pose, where):
    out = {}
    for bone, value in (pose or {}).items():
        if isinstance(value, dict):
            unknown = set(value) - {"rot", "loc"}
            if unknown:
                raise SpecError(f"{where}: bone {bone} has unknown keys {sorted(unknown)}")
            out[bone] = (vec3(value.get("rot", [0, 0, 0]), f"{where}.{bone}.rot"),
                         vec3(value.get("loc", [0, 0, 0]), f"{where}.{bone}.loc"))
        else:
            out[bone] = (vec3(value, f"{where}.{bone}"), [0.0, 0.0, 0.0])
    return out


def build_poses(spec):
    poses = {"rest": {}}
    for name, pose in (spec.get("test_poses") or {}).items():
        poses[name] = normalise_pose(pose, f"test_poses.{name}")
    for name, sw in (spec.get("sweeps") or {}).items():
        missing = {"bone", "from", "to", "step"} - set(sw)
        if missing:
            raise SpecError(f"sweeps.{name} is missing {sorted(missing)}")
        axis = sw.get("axis", "y")
        if axis not in AXIS:
            raise SpecError(f"sweeps.{name}.axis must be x, y or z, got {axis!r}")
        if not sw["step"] > 0:
            raise SpecError(f"sweeps.{name}.step must be positive")
        base = normalise_pose(sw.get("pose"), f"sweeps.{name}.pose")
        a = sw["from"]
        while a <= sw["to"] + 1e-9:
            pose = dict(base)
            rot, loc = pose.get(sw["bone"], ([0.0, 0.0, 0.0], [0.0, 0.0, 0.0]))
            rot = list(rot)
            rot[AXIS[axis]] = float(a)
            pose[sw["bone"]] = (rot, loc)
            poses[f"{name}@{a:g}"] = pose
            a += sw["step"]
    return poses


def islands(bm):
    bm.faces.ensure_lookup_table()
    seen, count = set(), 0
    for f in bm.faces:
        if f.index in seen:
            continue
        count += 1
        stack = [f]
        while stack:
            cur = stack.pop()
            if cur.index in seen:
                continue
            seen.add(cur.index)
            for e in cur.edges:
                stack.extend(lf for lf in e.link_faces if lf.index not in seen)
    return count


def hull(pts):
    pts = sorted(set(pts))
    if len(pts) < 3:
        return pts

    def cross(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])

    lo, up = [], []
    for p in pts:
        while len(lo) >= 2 and cross(lo[-2], lo[-1], p) <= 0:
            lo.pop()
        lo.append(p)
    for p in reversed(pts):
        while len(up) >= 2 and cross(up[-2], up[-1], p) <= 0:
            up.pop()
        up.append(p)
    return lo[:-1] + up[:-1]


def inside_margin(p, poly):
    """Signed distance from p to the convex polygon edges (positive = inside)."""
    if len(poly) < 3:
        return None
    best = float("inf")
    for i in range(len(poly)):
        a, b = poly[i], poly[(i + 1) % len(poly)]
        ex, ey = b[0] - a[0], b[1] - a[1]
        length = math.hypot(ex, ey) or 1e-9
        best = min(best, (ex * (p[1] - a[1]) - ey * (p[0] - a[0])) / length)
    return best


def validate(spec):
    arm = next((o for o in bpy.data.objects if o.type == "ARMATURE"), None)
    if arm is None:
        raise SpecError("no armature in the file: build the skeleton first")
    meshes = [o for o in bpy.data.objects if o.type == "MESH"]
    parts = [o for o in meshes if o.parent == arm and o.parent_type == "BONE"]
    if not parts:
        raise SpecError("no mesh parts parented to armature bones")
    allowed = {frozenset(p) for p in spec.get("allowed_contacts", [])}
    ground = spec.get("ground_check", spec.get("profile", "walker") in GROUND_PROFILES)
    ground_poses = spec.get("ground_check_poses")
    poses = build_poses(spec)
    for name, pose in poses.items():
        for bone in pose:
            if bone not in arm.pose.bones:
                raise SpecError(f"pose {name} references unknown bone {bone}")
    for name in ground_poses or []:
        if name not in poses:
            raise SpecError(f"ground_check_poses names unknown pose {name}")

    def connected(a, b):
        ba, bb = arm.data.bones[a.parent_bone], arm.data.bones[b.parent_bone]
        return ba == bb or ba.parent == bb or bb.parent == ba

    def world_mesh(obj, dg):
        ev = obj.evaluated_get(dg)
        me = ev.to_mesh()
        bm = bmesh.new()
        bm.from_mesh(me)
        bm.transform(ev.matrix_world)
        ev.to_mesh_clear()
        return bm

    def set_pose(pose):
        for pb in arm.pose.bones:
            pb.rotation_mode = "XYZ"
            pb.rotation_euler = (0, 0, 0)
            pb.location = (0, 0, 0)
        for bone, (rot, loc) in pose.items():
            arm.pose.bones[bone].rotation_euler = [math.radians(d) for d in rot]
            arm.pose.bones[bone].location = loc
        bpy.context.view_layer.update()

    report = {"static": {}, "poses": {}, "failures": []}

    # ---- static checks (rest pose)
    set_pose({})
    dg = bpy.context.evaluated_depsgraph_get()
    tris, loose = 0, {}
    for o in parts:
        bm = world_mesh(o, dg)
        tris += sum(len(f.verts) - 2 for f in bm.faces)
        n = islands(bm)
        if n > o.get("max_islands", 1):
            loose[o.name] = n
        bm.free()
    report["static"] = {
        "parts": len(parts),
        "triangles": tris,
        "unparented_meshes": [o.name for o in meshes if o not in parts],
        "parts_with_extra_islands": loose,
        "missing_sockets": [h["id"] for h in spec.get("hardpoints", []) if f"socket_{h['id']}" not in bpy.data.objects],
    }
    budget = spec.get("budgets", {}).get("tris_lod0")
    if budget and tris > budget:
        report["failures"].append(f"triangles {tris} > budget {budget}")
    for key in ("unparented_meshes", "parts_with_extra_islands", "missing_sockets"):
        if report["static"][key]:
            report["failures"].append(f"{key}: {report['static'][key]}")

    # ---- per-pose checks
    for name, pose in poses.items():
        set_pose(pose)
        dg = bpy.context.evaluated_depsgraph_get()
        data = {}
        for o in parts:
            bm = world_mesh(o, dg)
            verts = [v.co.copy() for v in bm.verts]
            if not verts:
                bm.free()
                report["failures"].append(f"pose {name}: part {o.name} has no geometry")
                continue
            polys = [[v.index for v in f.verts] for f in bm.faces]
            vol = abs(bm.calc_volume()) or 1e-6
            data[o.name] = {
                "tree": BVHTree.FromPolygons(verts, polys),
                "centroid": sum(verts, Vector()) / len(verts),
                "mass": vol * o.get("density", 1.0),
                "verts": verts,
                "contact": bool(o.get("contact", False)),
            }
            bm.free()
        if not data:
            continue

        hits = []
        names = list(data)
        for i, a in enumerate(names):
            for b in names[i + 1:]:
                if connected(bpy.data.objects[a], bpy.data.objects[b]) or frozenset((a, b)) in allowed:
                    continue
                if data[a]["tree"].overlap(data[b]["tree"]):
                    hits.append([a, b])
        result = {"collisions": hits}
        if hits:
            report["failures"].append(f"pose {name}: {len(hits)} colliding pairs")

        check_ground = name in ground_poses if ground_poses else ground
        if check_ground:
            total = sum(d["mass"] for d in data.values())
            com = sum((d["centroid"] * d["mass"] for d in data.values()), Vector()) / total
            contact_verts = [v for d in data.values() if d["contact"] for v in d["verts"]]
            if not contact_verts:
                report["failures"].append(f"pose {name}: no ground contact parts (set custom prop contact=True)")
            else:
                ground_z = min(v.z for v in contact_verts)
                lowest = min(v.z for d in data.values() for v in d["verts"])
                contact_pts = [(v.x, v.y) for v in contact_verts if v.z - ground_z < 0.03]
                margin = inside_margin((com.x, com.y), hull(contact_pts))
                result.update({"com": [round(c, 3) for c in com], "ground_z": round(ground_z, 3),
                               "support_margin_m": None if margin is None else round(margin, 3)})
                if lowest < ground_z - 0.03:
                    report["failures"].append(f"pose {name}: a non-contact part is {ground_z - lowest:.2f} m below the contacts")
                if margin is None:
                    report["failures"].append(f"pose {name}: contact parts give no support polygon")
                elif margin < spec.get("min_support_margin_m", 0.0):
                    report["failures"].append(f"pose {name}: centre of mass outside support polygon by {-margin:.2f} m")
        report["poses"][name] = result

    set_pose({})
    report["passed"] = not report["failures"]
    return report


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    args = dict(zip(argv[::2], argv[1::2]))
    out_path = args.get("--out", "report.json")
    if os.path.exists(out_path):
        os.remove(out_path)  # never leave a stale report behind
    try:
        if "--spec" not in args:
            raise SpecError("usage: blender -b unit.blend --python-exit-code 1 --python validate.py -- --spec spec.yaml [--out report.json]")
        report = validate(load_spec(args["--spec"]) or {})
    except Exception as e:  # any failure is a failed validation, never a silent pass
        report = {"passed": False, "failures": [f"error: {type(e).__name__}: {e}"]}
    with open(out_path, "w") as f:
        json.dump(report, f, indent=2)
    print(json.dumps({"passed": report["passed"], "failures": report["failures"]}, indent=2))
    sys.exit(0 if report["passed"] else 1)


main()
