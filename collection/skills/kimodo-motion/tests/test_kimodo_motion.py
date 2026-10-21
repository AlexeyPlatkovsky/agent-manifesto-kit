"""kimodo_motion.py without the model; the Blender round trip runs when BLENDER (or `blender`) is available.

  python3 -m unittest discover -s <skill>/tests -v
"""
import json
import math
import os
import random
import shutil
import struct
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPTS = os.path.join(HERE, "..", "scripts")
sys.path.insert(0, SCRIPTS)
import kimodo_motion as km  # noqa: E402

J = len(km.NAMES)


def rand_q(rng, scale):
    return km.quat([rng.uniform(-scale, scale) for _ in range(3)])


def motion(rng, n, drift):
    """A smooth synthetic take: every joint turning slowly, the root walking."""
    base = [rand_q(rng, 0.4) for _ in range(J)]
    rate = [[rng.uniform(-drift, drift) for _ in range(3)] for _ in range(J)]
    roots = [(0.01 * t, 0.95, 0.005 * t) for t in range(n)]
    rots = [[km.qmul(km.quat([r * t for r in rate[j]]), base[j]) for j in range(J)] for t in range(n)]
    return roots, rots


def positions(roots, rots):
    return [km.fk(r, q)[1] for r, q in zip(roots, rots)]


def largest_step(pos):
    return max(max(math.dist(a, b) for a, b in zip(pos[t], pos[t + 1])) for t in range(len(pos) - 1))


def pose_off(key, pos):
    return max(math.dist(a, b) for a, b in zip(km.fk(*key)[1], pos))


class KimodoMotion(unittest.TestCase):
    def setUp(self):
        self.rng = random.Random(7)
        self.tmp = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def test_skeleton_and_rotations(self):
        self.assertEqual((len(km.NAMES), len(km.PARENTS), len(km.OFFSETS)), (30, 30, 30))
        self.assertTrue(all(p < j for j, p in enumerate(km.PARENTS)))
        for _ in range(20):
            q = rand_q(self.rng, 2.0)
            self.assertLess(km.qangle(q, km.quat(km.axis_angle(q))), 1e-4)
        rest = km.fk(km.OFFSETS[0], [km.IDENTITY] * J)[1]
        self.assertAlmostEqual(rest[km.INDEX["Hips"]][1], 0.988)
        self.assertGreater(rest[km.INDEX["LeftHand"]][0], 0.5)        # the left side is +X

    def test_constraints_json(self):
        pose = {"root": [0.3, 1.0, -0.2], "local_xyzw": [list(rand_q(self.rng, 0.3)) for _ in range(J)]}
        c = km.constraints([(0, pose), (1, pose), (74, pose)])
        self.assertEqual([e["type"] for e in c], ["fullbody", "end-effector"])
        self.assertEqual(c[1]["joint_names"], km.EFFECTORS)
        self.assertEqual(c[0]["frame_indices"], [0, 1, 74])
        self.assertEqual(c[0]["root_positions"][0], [0.0, 1.0, 0.0])
        self.assertEqual(len(c[0]["local_joints_rot"][0]), J)
        self.assertEqual([e["type"] for e in km.constraints([(0, pose)], effectors=[])], ["fullbody"])

    def test_ease_exact_and_untouched_outside(self):
        roots, rots = motion(self.rng, 75, 0.01)
        keys = {f: (tuple(x + 0.03 for x in roots[f]), [km.qmul(rand_q(self.rng, 0.4), q) for q in rots[f]])
                for f in (0, 1, 2, 72, 73, 74)}
        er, eq = [tuple(r) for r in roots], [list(q) for q in rots]
        km.ease_onto(er, eq, keys, 9)
        got = positions(er, eq)
        for f, key in keys.items():
            self.assertLess(pose_off(key, got[f]), 1e-6, f)
        for t in range(2 + 9, 72 - 9 + 1):
            self.assertEqual((tuple(er[t]), list(eq[t])), (tuple(roots[t]), list(rots[t])), t)

    def test_ease_overlapping_windows_continuous(self):
        # keys 6 frames apart with a 9-frame window: a nearest-key rule snapped mid-gap (a step of ~the residual)
        roots, rots = motion(self.rng, 15, 0.01)
        keys = {f: (tuple(x + 0.05 * (1 if f else -1) for x in roots[f]), [km.qmul(rand_q(self.rng, 0.5), q) for q in rots[f]])
                for f in (4, 10)}
        er, eq = [tuple(r) for r in roots], [list(q) for q in rots]
        km.ease_onto(er, eq, keys, 9)
        eased, raw = positions(er, eq), positions(roots, rots)
        residual = max(pose_off(keys[f], raw[f]) for f in keys)
        self.assertLess(largest_step(eased), largest_step(raw) + residual / 3)
        for f, key in keys.items():
            self.assertLess(pose_off(key, eased[f]), 1e-6)

    def write(self, roots, rots, cons):
        km.save(self.tmp, roots, rots)
        with open(os.path.join(self.tmp, "constraints.json"), "w") as fh:
            json.dump(cons, fh)

    def test_check_known_good_and_known_bad(self):
        roots, rots = motion(self.rng, 75, 0.02)
        pose_a = {"root": list(roots[0]), "local_xyzw": [list(q) for q in rots[0]]}
        pose_b = {"root": list(roots[74]), "local_xyzw": [list(q) for q in rots[74]]}
        cons = km.constraints([(0, pose_a), (74, pose_b)])
        shifted = [(r[0] - roots[0][0], r[1], r[2] - roots[0][2]) for r in roots]
        self.write(shifted, rots, cons)
        ok, report = km.check(self.tmp)
        self.assertTrue(ok, report)
        other_roots, other = motion(self.rng, 75, 0.02)
        self.write(other_roots, other, cons)
        self.assertFalse(km.check(self.tmp)[0])
        # one frame keyed twice (overlapping holds), the violated key listed first: it still fails
        cons = km.constraints([(0, pose_a), (0, pose_b)])
        for e in cons:
            for f in ("frame_indices", "root_positions", "local_joints_rot"):
                e[f] = e[f][::-1]          # a copy: the two entries share their lists
        self.write(shifted, rots, cons)
        self.assertFalse(km.check(self.tmp)[0])

    def test_post_keeps_raw_and_lands_on_keys(self):
        roots, rots = motion(self.rng, 40, 0.01)
        pose = {"root": [0.0, 0.97, 0.0], "local_xyzw": [list(rand_q(self.rng, 0.2)) for _ in range(J)]}
        self.write(roots, rots, km.constraints([(f, pose) for f in (0, 1, 2)]))
        before = [km.read(os.path.join(self.tmp, f), "rb") for f in ("root_positions.f32", "local_rotations_xyzw.f32")]
        moved = km.post(self.tmp, 0.3)
        self.assertGreater(moved, 0)
        after = [km.read(os.path.join(self.tmp, "raw", f), "rb") for f in ("root_positions.f32", "local_rotations_xyzw.f32")]
        self.assertEqual(before, after)             # the model's take is kept untouched in raw/
        self.assertTrue(km.check(self.tmp)[0])

    def test_generate_refuses_overlapping_holds(self):
        saved, km.KIMODO_ROOT = km.KIMODO_ROOT, self.tmp
        try:
            with self.assertRaises(SystemExit) as e:
                km.generate("x", self.tmp, "never", [1], 4, "a.json:p", "b.json:p", hold=3)
        finally:
            km.KIMODO_ROOT = saved
        self.assertIn("cannot hold", str(e.exception))

    def test_check_model_gate_cli(self):
        # the model gate reads raw/ beside the take: a take without keys (known-bad) fails it, the keyed one passes
        roots, rots = motion(self.rng, 30, 0.02)
        pose = {"root": list(roots[0]), "local_xyzw": [list(q) for q in rots[0]]}
        self.write([(r[0] - roots[0][0], r[1], r[2] - roots[0][2]) for r in roots], rots, km.constraints([(0, pose)]))
        os.makedirs(os.path.join(self.tmp, "raw"))
        km.save(os.path.join(self.tmp, "raw"), *motion(self.rng, 30, 0.02))
        cons = os.path.join(self.tmp, "constraints.json")
        self.assertEqual(km.main(["check", self.tmp, "--model"]), 1)
        km.save(os.path.join(self.tmp, "raw"), *km.load(self.tmp))
        self.assertEqual(km.main(["check", self.tmp, "--model", "--constraints", cons]), 0)

    def test_sheet_renders(self):
        try:
            import PIL  # noqa: F401
        except ImportError:
            self.skipTest("Pillow not installed")
        roots, rots = motion(self.rng, 20, 0.01)
        pose = {"root": list(roots[0]), "local_xyzw": [list(q) for q in rots[0]]}
        self.write(roots, rots, km.constraints([(0, pose)]))
        out = os.path.join(self.tmp, "sheet.png")
        km.sheet([self.tmp], out, span=(0, 5))
        self.assertGreater(os.path.getsize(out), 1000)


@unittest.skipUnless(shutil.which(os.environ.get("BLENDER", "blender")), "Blender not found (set BLENDER)")
class BlenderRoundTrip(unittest.TestCase):
    def test_pose_to_keypose_to_rig(self):
        blender = shutil.which(os.environ.get("BLENDER", "blender"))
        run = subprocess.run([blender, "-b", "--factory-startup", "--python-exit-code", "1", "--python",
                              os.path.join(HERE, "blender_roundtrip.py")], capture_output=True, text=True, timeout=600)
        self.assertEqual(run.returncode, 0, run.stdout[-3000:] + run.stderr[-3000:])
        self.assertIn("PASS blender_roundtrip", run.stdout)


if __name__ == "__main__":
    unittest.main()
