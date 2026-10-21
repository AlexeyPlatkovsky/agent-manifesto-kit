#!/usr/bin/env python3
"""Kimodo (NVIDIA text-to-motion, native kimodo.cpp build) motions on Kimodo's own SOMA30 skeleton.

  python3 kimodo_motion.py generate --prompt TEXT --out DIR [--name NAME] [--seeds 1,2,3] [--frames 75]
      [--start POSES.json:POSE] [--end POSES.json:POSE] [--hold N] [--post S] [--no-effectors]
      DIR/NAME_s<seed>/: the motion, prompt.txt, constraints.json (upstream's key-pose JSON), keypose_error.json
      (the model's own take on its keys, then after post), raw/ (the model's take before post); DIR/provenance.json
  python3 kimodo_motion.py check MOTION_DIR [--constraints FILE] [--model]
      joint-position error on every key frame (world rotations reported); fails above KEY_POS_TOL_M on any joint, or
      with --model (the model's own take: MOTION_DIR/raw when present) above KEY_MEAN_TOL_M on the joints' mean
  python3 kimodo_motion.py sheet MOTION_DIR [...] --out SHEET.png [--frames 8 | --span A:B] [--keys CONSTRAINTS.json]
      front and right views per motion at evenly spaced frames (or every frame A..B: the junction strips), the right
      hand's path, the key poses grey under their frames (the dir's constraints.json, else --keys); needs Pillow
  python3 kimodo_motion.py stats MOTION_DIR
      frames, seconds, root travel, and for reach/draw clips the right hand's closest approach to the right hip
  python3 kimodo_motion.py keypose --rig RIG.blend NAME=ACTION.blend[@FRAME] [...] --out POSES.json [--toe-y M]
      [--prefix mixamorig:]
      game poses as Kimodo key poses: runs kimodo_retarget.py keypose in Blender (see its docstring)

A motion dir is what kmd-generate writes: root_positions.f32 (frames x 3, metres, Y up, little-endian f32) and
local_rotations_xyzw.f32 (frames x 30 x 4, each joint against its parent; identity is the T-pose of OFFSETS). The body
faces +Z, its left side is +X. Configuration (environment): KIMODO_ROOT (the kimodo.cpp checkout), KIMODO_GENERATE
(its kmd-generate, default build/kmd-generate), KIMODO_MOTION_GGUF / KIMODO_TEXT_GGUF (model files; these three
relative to KIMODO_ROOT or absolute), KIMODO_EXPORT_GLB (optional: kimodo.cpp's scripts/export_glb.py, writes animation.glb beside each take),
BLENDER (executable). Standard library only, except sheet (Pillow).

Key poses (the build needs the key-pose patch, see the skill): each key is a `fullbody` entry (every joint's FK
position, the root height and heading) plus an `end-effector` one on the same frames (EFFECTORS: the hands' and
feet's global turn; positions alone left the hands 24-39 deg off). Keys are held HOLD frames at either end (a single
key let a take leave a still pose at full speed). The model still misses its keys by about 2 cm, so post eases
each key's residual out over POST_S (an offset; a blend toward the static key moved joints 14-20 cm mid-motion).
"""
import json
import math
import os
import struct
import subprocess
import sys

FPS = 30
HERE = os.path.dirname(os.path.abspath(__file__))
KIMODO_ROOT = os.environ.get("KIMODO_ROOT", "")
GENERATE = os.environ.get("KIMODO_GENERATE", "build/kmd-generate")
MOTION_GGUF = os.environ.get("KIMODO_MOTION_GGUF", "models/kimodo-soma-rp-v1.1-f32.gguf")
TEXT_GGUF = os.environ.get("KIMODO_TEXT_GGUF", "models/Llama-3-Kimodo-Q8_0.gguf")
BLENDER = os.environ.get("BLENDER", "blender")
STEPS = 100
HOLD = 3                # key poses held over this many frames at either end
EFFECTORS = ["LeftHand", "RightHand", "LeftFoot", "RightFoot"]
POST_S = 0.3            # post: the model's residual on its keys eased out over this on either side
KEY_MEAN_TOL_M = 0.03   # the model's own take on its key frames: joints' mean distance off the key (constraints took:
                        # about 19 mm measured; the same prompt without keys, 79-289 mm)
KEY_POS_TOL_M = 0.005   # after post: any joint off its key pose
TOE_Y = 0.015           # keypose default: Kimodo's own standing takes keep ToeBase about this high

# SOMA30 (Kimodo SOMA RP v1.1), copied from kimodo.cpp scripts/export_glb.py (Apache-2.0; names and parents from
# NVIDIA Kimodo's skeleton definitions). Offsets are parent-local, metres; the Hips entry is its rest height.
NAMES = ["Hips", "Spine1", "Spine2", "Chest", "Neck1", "Neck2", "Head", "Jaw", "LeftEye", "RightEye", "LeftShoulder",
         "LeftArm", "LeftForeArm", "LeftHand", "LeftHandThumbEnd", "LeftHandMiddleEnd", "RightShoulder", "RightArm",
         "RightForeArm", "RightHand", "RightHandThumbEnd", "RightHandMiddleEnd", "LeftLeg", "LeftShin", "LeftFoot",
         "LeftToeBase", "RightLeg", "RightShin", "RightFoot", "RightToeBase"]
PARENTS = [-1, 0, 1, 2, 3, 4, 5, 6, 6, 6, 3, 10, 11, 12, 13, 13, 3, 16, 17, 18, 19, 19, 0, 22, 23, 24, 0, 26, 27, 28]
OFFSETS = [(0.0, 0.988, 0.0), (-0.00013727, 0.0500376256, -0.00053726669), (-1.86574103e-09, 0.0712530139, -0.000298248546),
           (-5.75188398e-09, 0.0755006305, -0.00815970992), (-0.00181676517, 0.263112953, -0.00553348292),
           (-2.85102231e-08, 0.0770939664, 0.0230258546), (-4.5975437e-08, 0.0612891595, 0.0195370861),
           (2.63687901e-05, 0.0047559225, 0.0309494062), (0.0320638079, 0.0538020513, 0.0758688308),
           (-0.0322244017, 0.05361869, 0.0755823359), (0.0162165175, 0.232371641, 0.0511341324),
           (0.149198457, 2.19397873e-08, -0.0550232576), (0.287393078, 2.50268389e-09, -2.58787737e-05),
           (0.270939812, -7.06625108e-09, 2.60897248e-05), (0.122686267, -0.0322017573, 0.0483306876),
           (0.190119595, -0.00312878387, -0.000339570373), (-0.0138011824, 0.231803086, 0.0521415786),
           (-0.150371962, 1.17387901e-07, -0.0554560437), (-0.287366393, 1.87628082e-08, -2.59709359e-05),
           (-0.271336198, -1.16767401e-09, 2.61269368e-05), (-0.122642483, -0.0321145448, 0.0480403904),
           (-0.190005945, -0.00306615542, -0.0003157343), (0.10043214, -0.0843452671, 0.0259565473),
           (-1e-08, -0.432217537, -0.00802912805), (1e-08, -0.421550959, -0.0348152298), (0.0, -0.0505947206, 0.132315294),
           (-0.10047278, -0.0829525995, 0.0262031695), (1e-08, -0.433622059, -0.00805555828),
           (2e-08, -0.421173943, -0.0347839785), (-3.42907669e-09, -0.0507960932, 0.132841956)]
INDEX = {n: i for i, n in enumerate(NAMES)}
IDENTITY = (0.0, 0.0, 0.0, 1.0)


def qmul(a, b):
    ax, ay, az, aw = a
    bx, by, bz, bw = b
    return (aw * bx + ax * bw + ay * bz - az * by, aw * by - ax * bz + ay * bw + az * bx,
            aw * bz + ax * by - ay * bx + az * bw, aw * bw - ax * bx - ay * by - az * bz)


def qinv(q):
    return (-q[0], -q[1], -q[2], q[3])


def qrot(q, v):
    x, y, z, w = q
    vx, vy, vz = v
    tx, ty, tz = 2 * (y * vz - z * vy), 2 * (z * vx - x * vz), 2 * (x * vy - y * vx)
    return (vx + w * tx + y * tz - z * ty, vy + w * ty + z * tx - x * tz, vz + w * tz + x * ty - y * tx)


def qangle(a, b):
    """Degrees between two rotations."""
    return math.degrees(2 * math.acos(min(1.0, abs(sum(x * y for x, y in zip(a, b))))))


def axis_angle(q):
    x, y, z, w = q
    if w < 0:
        x, y, z, w = -x, -y, -z, -w
    n = math.sqrt(x * x + y * y + z * z)
    a = 2 * math.atan2(n, w)
    return (0.0, 0.0, 0.0) if n < 1e-12 else (x / n * a, y / n * a, z / n * a)


def quat(v):
    a = math.sqrt(sum(c * c for c in v))
    if a < 1e-12:
        return IDENTITY
    s = math.sin(a / 2) / a
    return (v[0] * s, v[1] * s, v[2] * s, math.cos(a / 2))


def slerp(a, b, w):
    d = sum(x * y for x, y in zip(a, b))
    if d < 0:
        b, d = tuple(-x for x in b), -d
    if d > 0.9995:
        q = tuple(x + (y - x) * w for x, y in zip(a, b))
    else:
        th = math.acos(d)
        q = tuple((math.sin((1 - w) * th) * x + math.sin(w * th) * y) / math.sin(th) for x, y in zip(a, b))
    n = math.sqrt(sum(x * x for x in q))
    return tuple(x / n for x in q)


def read(path, mode="r"):
    with open(path, mode) as fh:
        return fh.read()


def read_json(path):
    return json.loads(read(path))


def load(motion_dir):
    """(roots [(x, y, z)], rotations [[(x, y, z, w)] * 30]) per frame."""
    raw = read(os.path.join(motion_dir, "root_positions.f32"), "rb")
    roots = [struct.unpack_from("<3f", raw, 12 * f) for f in range(len(raw) // 12)]
    raw = read(os.path.join(motion_dir, "local_rotations_xyzw.f32"), "rb")
    n = len(NAMES)
    rots = [[struct.unpack_from("<4f", raw, 16 * (f * n + j)) for j in range(n)] for f in range(len(raw) // (16 * n))]
    if len(rots) != len(roots):
        raise SystemExit(f"{motion_dir}: {len(roots)} roots but {len(rots)} rotation frames")
    return roots, rots


def save(motion_dir, roots, rots):
    with open(os.path.join(motion_dir, "root_positions.f32"), "wb") as fh:
        fh.write(b"".join(struct.pack("<3f", *r) for r in roots))
    with open(os.path.join(motion_dir, "local_rotations_xyzw.f32"), "wb") as fh:
        fh.write(b"".join(struct.pack("<4f", *q) for frame in rots for q in frame))


def fk(root, rots):
    """World rotations (xyzw) and positions of every joint for one frame."""
    world, pos = [None] * len(NAMES), [None] * len(NAMES)
    for j, p in enumerate(PARENTS):
        if p < 0:
            world[j], pos[j] = tuple(rots[j]), tuple(root)
        else:
            world[j] = qmul(world[p], rots[j])
            o = qrot(world[p], OFFSETS[j])
            pos[j] = (pos[p][0] + o[0], pos[p][1] + o[1], pos[p][2] + o[2])
    return world, pos


def stats(motion_dir):
    roots, rots = load(motion_dir)
    best = (1e9, 0)
    for f in range(len(roots)):
        _, pos = fk(roots[f], rots[f])
        best = min(best, (math.dist(pos[INDEX["RightHand"]], pos[INDEX["RightLeg"]]), f))
    travel = math.dist((roots[0][0], roots[0][2]), (roots[-1][0], roots[-1][2]))
    return {"frames": len(roots), "seconds": round((len(roots) - 1) / FPS, 3), "root_travel_m": round(travel, 3),
            "hand_to_hip_min_m": round(best[0], 3), "hand_to_hip_frame": best[1],
            "hand_to_hip_s": round(best[1] / FPS, 3)}


def pick_pose(spec):
    """POSES.json:NAME -> {"root": [x, y, z], "local_xyzw": [[x, y, z, w] * 30], ...}"""
    path, name = spec.rsplit(":", 1)
    return read_json(path)["poses"][name]


def constraints(keys, effectors=EFFECTORS):
    """[(frame, pose)] as upstream's key-pose JSON: a fullbody entry and, with effectors, an end-effector entry on the
    same frames. XZ relative to the first key's root (upstream canonicalises the first frame to the origin)."""
    x0, z0 = keys[0][1]["root"][0], keys[0][1]["root"][2]
    full = {"type": "fullbody", "frame_indices": [f for f, _ in keys],
            "root_positions": [[p["root"][0] - x0, p["root"][1], p["root"][2] - z0] for _, p in keys],
            "local_joints_rot": [[list(axis_angle(q)) for q in p["local_xyzw"]] for _, p in keys]}
    return [full, dict(full, type="end-effector", joint_names=list(effectors))] if effectors else [full]


def key_poses(path):
    """{frame: (root, local xyzw)} of a constraints file (the last entry wins a frame keyed twice)."""
    return {f: (c["root_positions"][i], [quat(v) for v in c["local_joints_rot"][i]])
            for c in read_json(path) for i, f in enumerate(c["frame_indices"])}


def check(motion_dir, path=None, tol_m=KEY_POS_TOL_M, stat="pos_max_mm"):
    """Per key frame: the generated joint positions against the key's (FK of both) and world rotations. Passes when
    stat stays within tol_m for every key entry; a frame keyed twice reports its worse key."""
    path = path or os.path.join(motion_dir, "constraints.json")
    roots, rots = load(motion_dir)
    report, every = {}, []
    for c in read_json(path):
        for i, f in enumerate(c["frame_indices"]):
            kw, kp = fk(c["root_positions"][i], [quat(v) for v in c["local_joints_rot"][i]])
            gw, gp = fk(roots[f], rots[f])
            err = [math.dist(a, b) for a, b in zip(kp, gp)]
            ang = [qangle(a, b) for a, b in zip(kw, gw)]
            worst, wa = max(range(len(err)), key=err.__getitem__), max(range(len(ang)), key=ang.__getitem__)
            entry = {"pos_max_mm": round(err[worst] * 1000, 1), "pos_max_joint": NAMES[worst],
                     "pos_mean_mm": round(sum(err) / len(err) * 1000, 1), "root_mm": round(err[0] * 1000, 1),
                     "rot_max_deg": round(ang[wa], 1), "rot_max_joint": NAMES[wa],
                     "right_hand_rot_deg": round(ang[INDEX["RightHand"]], 1)}
            every.append(entry)
            if f not in report or entry[stat] > report[f][stat]:
                report[f] = entry
    return all(r[stat] <= tol_m * 1000 for r in every), report


def ease_onto(roots, rots, keys, span):
    """roots/rots moved onto keys {frame: (root, local xyzw)} in place: each key's residual (every joint's local turn,
    the root's offset) added around it, weight 1 on the key falling smoothly to 0 span frames away (or at the next
    key); between two keys the residuals mix by those weights, so the result is continuous and exact on every key.
    Returns the largest joint move (metres)."""
    res = {f: ([a - b for a, b in zip(root, roots[f])], [qmul(k, qinv(q)) for k, q in zip(local, rots[f])])
           for f, (root, local) in keys.items()}
    order = sorted(res)

    def weight(d, reach):
        x = min(1.0, d / reach)
        return 1.0 - x * x * (3 - 2 * x)

    moved = 0.0
    for t in range(len(roots)):
        prev = max((f for f in order if f <= t), default=None)
        nxt = min((f for f in order if f >= t), default=None)
        gap = nxt - prev if prev is not None and nxt is not None else None
        reach = min(span, gap) if gap else span
        wp = weight(t - prev, reach) if prev is not None else 0.0
        wn = weight(nxt - t, reach) if nxt is not None and nxt != prev else 0.0
        if wp + wn <= 0.0:
            continue
        a, mix = max(wp, wn), wn / (wp + wn)
        sp, tp = res[prev] if prev is not None else res[nxt]
        sn, tn = res[nxt] if nxt is not None else res[prev]
        before = fk(roots[t], rots[t])[1]
        roots[t] = tuple(r + a * (x + (y - x) * mix) for r, x, y in zip(roots[t], sp, sn))
        rots[t] = [qmul(slerp(IDENTITY, slerp(dp, dn, mix), a), q) for dp, dn, q in zip(tp, tn, rots[t])]
        moved = max(moved, *(math.dist(p, q) for p, q in zip(before, fk(roots[t], rots[t])[1])))
    return moved


def post(motion_dir, window_s=POST_S):
    """The model's take (kept in raw/) eased onto its key poses over window_s. Returns the largest joint move (mm)."""
    raw = os.path.join(motion_dir, "raw")
    os.makedirs(raw)
    for f in ("root_positions.f32", "local_rotations_xyzw.f32"):
        os.replace(os.path.join(motion_dir, f), os.path.join(raw, f))
    roots, rots = load(raw)
    moved = ease_onto(roots, rots, key_poses(os.path.join(motion_dir, "constraints.json")), window_s * FPS)
    save(motion_dir, roots, rots)
    return round(moved * 1000, 1)


def kimodo_path(rel):
    return rel if os.path.isabs(rel) else os.path.join(KIMODO_ROOT, rel)


def generate(prompt, out, name, seeds, frames, start=None, end=None, steps=STEPS, post_s=POST_S, hold=HOLD,
             effectors=EFFECTORS):
    """One motion dir per seed through the local build, with key poses when given (then post); returns
    {dir: (pass, report)} for keyed takes."""
    if not KIMODO_ROOT:
        raise SystemExit("set KIMODO_ROOT to the kimodo.cpp install (build/kmd-generate, models/)")
    if start and end and frames < 2 * hold:
        raise SystemExit(f"{frames} frames cannot hold the start and the end pose {hold} frames each")
    keys = [(f, pick_pose(start)) for f in range(hold)] if start else []
    if end:
        keys += [(frames - hold + f, pick_pose(end)) for f in range(hold)]
    os.makedirs(out, exist_ok=True)
    prov_path = os.path.join(out, "provenance.json")
    prov = read_json(prov_path) if os.path.exists(prov_path) else {
        "generator": "Kimodo (NVIDIA), local kimodo.cpp build with the kimodo-motion key-pose patch",
        "motion_model": MOTION_GGUF, "text_model": TEXT_GGUF, "candidates": {}}
    command = (f"build/kmd-generate MOTION.gguf TEXT.gguf <dir>/prompt.txt {frames} {steps} <seed> <dir>"
               + (" --constraints <dir>/constraints.json" if keys else ""))
    results = {}
    for seed in seeds:
        d = os.path.join(out, f"{name}_s{seed}")
        if os.path.exists(d):
            raise SystemExit(f"exists, choose a new --name: {d}")
        os.makedirs(d)
        with open(os.path.join(d, "prompt.txt"), "w") as fh:
            fh.write(prompt + "\n")
        cmd = [kimodo_path(GENERATE), kimodo_path(MOTION_GGUF), kimodo_path(TEXT_GGUF),
               os.path.join(d, "prompt.txt"), str(frames), str(steps), str(seed), d]
        if keys:
            with open(os.path.join(d, "constraints.json"), "w") as fh:
                json.dump(constraints(keys, effectors), fh)
            cmd += ["--constraints", os.path.join(d, "constraints.json")]
        run = subprocess.run(cmd, capture_output=True, text=True)
        if run.returncode:
            raise SystemExit(f"kmd-generate failed ({run.returncode}): {run.stderr[-2000:]}")
        entry = {"seed": seed, "command": command, "used_as": None}
        if keys:
            entry["keys"] = {"start": start, "end": end, "hold": hold, "effectors": list(effectors)}
            raw_ok, raw = check(d, tol_m=KEY_MEAN_TOL_M, stat="pos_mean_mm")
            moved = post(d, post_s) if post_s else 0.0
            post_ok, final = check(d)
            ok = raw_ok and post_ok
            with open(os.path.join(d, "keypose_error.json"), "w") as fh:
                json.dump({"model": {"tolerance_mean_mm": KEY_MEAN_TOL_M * 1000, "pass": raw_ok, "frames": raw},
                           "post": {"window_s": post_s, "largest_move_mm": moved,
                                    "tolerance_max_mm": KEY_POS_TOL_M * 1000, "pass": post_ok, "frames": final}},
                          fh, indent=1)
            entry["keypose_pass"] = ok
            results[d] = (ok, {"model": raw, "post_move_mm": moved, "post": final})
            print(f"{'PASS' if ok else 'FAIL'} {os.path.basename(d)}: model {json.dumps(raw)}; post moved {moved} mm, "
                  f"{json.dumps(final)}")
        else:
            print("MOTION", d)
        prov["candidates"][f"{name}_s{seed}"] = entry
        with open(prov_path, "w") as fh:            # after each seed: a later failure keeps the earlier entries
            json.dump(prov, fh, indent=2)
        exporter = os.environ.get("KIMODO_EXPORT_GLB")
        if exporter:
            run = subprocess.run([sys.executable, exporter, "--motion-dir", d, "--output",
                                  os.path.join(d, "animation.glb"), "--model", "soma30", "--fps", str(FPS)],
                                 capture_output=True, text=True)
            if run.returncode:
                raise SystemExit(f"export_glb failed ({run.returncode}): {run.stderr[-2000:]}")
    return results


def keypose(rig, specs, out, toe_y=TOE_Y, prefix="mixamorig:"):
    """Runs kimodo_retarget.py keypose in Blender on the rig. A separate script on purpose: a launcher that re-ran
    itself in Blender from an `except ImportError` relaunched Blender hundreds of times on one missing module."""
    cmd = [BLENDER, "-b", rig, "--factory-startup", "--python-exit-code", "1", "--python",
           os.path.join(HERE, "kimodo_retarget.py"), "--", "keypose", *specs, "--out", os.path.abspath(out),
           "--toe-y", str(toe_y), "--prefix", prefix]
    run = subprocess.run(cmd, capture_output=True, text=True)
    for line in run.stdout.splitlines():
        if line.startswith(("KEYPOSE", "POSES", "FAIL", "Traceback")) or run.returncode:
            print(line)
    if run.returncode:
        print(run.stderr[-3000:])
        raise SystemExit(run.returncode)


BONES = [(j, p) for j, p in enumerate(PARENTS) if p >= 0 and NAMES[j] not in ("Jaw", "LeftEye", "RightEye")]


def sheet(dirs, out, frames=8, keys_path=None, span=None):
    from PIL import Image, ImageDraw, ImageFont
    cell, pad = 190, 6
    font = ImageFont.load_default()
    rows = []
    for d in dirs:
        roots, rots = load(d)
        own = os.path.join(d, "constraints.json")
        path_ = own if os.path.exists(own) else keys_path
        keys = {f: fk(*k)[1] for f, k in key_poses(path_).items()} if path_ else {}
        picks = (list(range(span[0], min(span[1], len(roots) - 1) + 1)) if span else
                 [round(i * (len(roots) - 1) / (frames - 1)) for i in range(frames)])
        prompt_file = os.path.join(d, "prompt.txt")
        prompt = read(prompt_file).strip() if os.path.exists(prompt_file) else ""
        hand = [fk(roots[f], rots[f])[1][INDEX["RightHand"]] for f in range(len(roots))]
        label = os.path.basename(os.path.normpath(d))
        if label == "raw":                          # generate's raw/ beside its eased take
            label = os.path.basename(os.path.dirname(os.path.normpath(d))) + "/raw"
        row = Image.new("RGB", (cell * (len(picks) + 1), 2 * cell + 28), "white")
        dr = ImageDraw.Draw(row)
        dr.text((4, 4), f"{label}: {prompt}", fill="black", font=font)
        for view in (0, 1):            # 0 front (looking at the +Z face: screen x = -X), 1 right side (screen x = +Z)
            def px(p, i, f0):
                sx = -(p[0] - f0[0]) if view == 0 else (p[2] - f0[2])
                return (cell * i + cell / 2 + sx * cell / 2.1, 28 + cell * view + cell - 8 - p[1] * cell / 2.1)
            f0 = roots[0]
            for i, f in enumerate(picks):
                _, pos = fk(roots[f], rots[f])
                floor = 28 + cell * view + cell - 8
                dr.line([(cell * i, floor), (cell * (i + 1) - pad, floor)], fill=(200, 200, 200))
                for j, p in BONES if f in keys else ():      # the key pose under its frame, grey
                    dr.line([px(keys[f][p], i, f0), px(keys[f][j], i, f0)], fill=(185, 185, 185), width=7)
                for j, p in BONES:
                    side = NAMES[j]
                    colour = (200, 40, 40) if side.startswith("Right") else (40, 90, 200) if side.startswith("Left") \
                        else (40, 40, 40)
                    dr.line([px(pos[p], i, f0), px(pos[j], i, f0)], fill=colour, width=3)
                dr.text((cell * i + 4, 28 + cell * view + 4),
                        f"{f / FPS:.2f}s f{f} {'front' if view == 0 else 'right'}", fill="black", font=font)
            dr.line([px(p, len(picks), f0) for p in hand], fill=(200, 40, 40), width=2)
            dr.text((cell * len(picks) + 4, 28 + cell * view + 4), "right hand path", fill="black", font=font)
        rows.append(row)
    width = max(r.width for r in rows)
    img = Image.new("RGB", (width, sum(r.height for r in rows)), "white")
    y = 0
    for r in rows:
        img.paste(r, (0, y))
        y += r.height
    img.save(out)
    print("SHEET", out)


def flag(args, name, default=None):
    return args[args.index(name) + 1] if name in args else default


def main(args):
    takes_value = ("--out", "--frames", "--keys", "--span", "--constraints", "--rig", "--toe-y", "--prefix", "--prompt",
                   "--name", "--seeds", "--start", "--end", "--hold", "--post")
    positional = [a for i, a in enumerate(args[1:], 1) if not a.startswith("--") and args[i - 1] not in takes_value]
    cmd = args[0] if args else ""
    if cmd == "generate":
        results = generate(flag(args, "--prompt"), flag(args, "--out"), flag(args, "--name", "k"),
                           [int(s) for s in flag(args, "--seeds", "1,2,3").split(",")], int(flag(args, "--frames", 75)),
                           flag(args, "--start"), flag(args, "--end"), post_s=float(flag(args, "--post", POST_S)),
                           hold=int(flag(args, "--hold", HOLD)), effectors=[] if "--no-effectors" in args else EFFECTORS)
        return 0 if all(ok for ok, _ in results.values()) else 1
    if cmd == "check":
        take, cons = positional[0], flag(args, "--constraints")
        if "--model" in args:
            raw = os.path.join(take, "raw")
            cons = cons or os.path.join(take, "constraints.json")
            ok, report = check(raw if os.path.isdir(raw) else take, cons, KEY_MEAN_TOL_M, "pos_mean_mm")
        else:
            ok, report = check(take, cons)
        print("PASS" if ok else "FAIL", json.dumps(report))
        return 0 if ok else 1
    if cmd == "stats":
        for d in positional:
            print(os.path.basename(os.path.normpath(d)), stats(d))
        return 0
    if cmd == "sheet":
        span = tuple(int(v) for v in flag(args, "--span").split(":")) if "--span" in args else None
        sheet(positional, flag(args, "--out"), int(flag(args, "--frames", 8)), flag(args, "--keys"), span)
        return 0
    if cmd == "keypose":
        keypose(flag(args, "--rig"), positional, flag(args, "--out"), float(flag(args, "--toe-y", TOE_Y)),
                flag(args, "--prefix", "mixamorig:"))
        return 0
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
