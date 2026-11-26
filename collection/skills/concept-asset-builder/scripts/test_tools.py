"""Model-free tests for the concept-asset-builder tools. Skipped when Pillow or numpy (or scipy, for wear_stats)
is missing. The tools resolve paths from their own location (<workspace>/tools), so every test builds a real
workspace with init_workspace.sh and a synthetic concept sheet."""
import json
import pathlib
import subprocess
import sys
import tempfile
import unittest

HERE = pathlib.Path(__file__).resolve().parent
SKILL = HERE.parent

try:
    import numpy as np
    from PIL import Image
    HAVE_DEPS = True
except ImportError:
    HAVE_DEPS = False
try:
    import scipy  # noqa: F401
    HAVE_SCIPY = True
except ImportError:
    HAVE_SCIPY = False

BG = (237, 229, 225)
PAINT = (175, 86, 55)
VIEWS = ["3q", "front", "back", "left", "right"]


def run(*args, cwd=None):
    return subprocess.run([*args], cwd=cwd, capture_output=True, text=True, check=True,
                          env={"PYTHONDONTWRITEBYTECODE": "1", "PATH": "/usr/bin:/bin:/usr/local/bin:/opt/homebrew/bin"})


@unittest.skipUnless(HAVE_DEPS, "Pillow and numpy are required")
class ToolsTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = pathlib.Path(self.tmp.name)
        # sheet: five 100x200 px objects (a painted box with a cream chip) on the page background
        sheet = Image.new("RGB", (700, 300), BG)
        px = sheet.load()
        self.boxes = {}
        for i, v in enumerate(VIEWS):
            x0 = 20 + i * 135
            for x in range(x0 + 10, x0 + 90):
                for y in range(40, 240):
                    px[x, y] = PAINT
            for x in range(x0 + 40, x0 + 52):
                for y in range(100, 116):
                    px[x, y] = (226, 205, 176)
            self.boxes[v] = [x0, 20, x0 + 100, 260]
        self.concept = self.dir / "sheet.png"
        sheet.save(self.concept)
        self.ws = self.dir / "ws"
        run("bash", str(SKILL / "scripts/init_workspace.sh"), str(self.ws), str(self.concept))
        (self.ws / "reference/boxes.json").write_text(json.dumps(self.boxes))
        run(sys.executable, "-B", "tools/crop.py", cwd=self.ws)

    def tearDown(self):
        self.tmp.cleanup()

    def test_workspace_layout_and_crops(self):
        for d in ["reference/crops", "spec", "brief", "tools", "blender", "threejs", "out", "reviews", "reports", "textures"]:
            self.assertTrue((self.ws / d).is_dir(), d)
        for f in ["blender/studio.py", "blender/render_views.py", "threejs/studio.js", "threejs/index.html",
                  "brief/rubric.json", "reference/zones.json", "tools/wear_stats.py", "tools/codex_review.sh"]:
            self.assertTrue((self.ws / f).is_file(), f)
        for v in VIEWS:
            self.assertEqual(Image.open(self.ws / f"reference/crops/{v}.png").size, (100, 240))

    def test_measure_silhouette_reports_metres(self):
        out = run(sys.executable, "-B", "tools/measure_silhouette.py", "front", "--height", "2.0", "--rows", "4", cwd=self.ws).stdout
        # the box is 200 px tall and 80 px wide -> 10 mm/px, 0.8 m wide
        self.assertIn("10.00 mm/px", out)
        self.assertIn("width 0.800 m", out)

    def test_metrics_mask_and_lab(self):
        sys.path.insert(0, str(self.ws / "tools"))
        try:
            import metrics
            img = metrics.load(self.ws / "reference/crops/front.png")
            y0, y1, x0, x1 = metrics.bbox(metrics.mask_of(img))
            self.assertEqual((y1 - y0, x1 - x0), (200, 80))
            white = metrics.srgb_to_lab(np.array([[255.0, 255.0, 255.0]]))[0]
            self.assertAlmostEqual(float(white[0]), 100.0, delta=0.5)
        finally:
            sys.path.remove(str(self.ws / "tools"))
            sys.modules.pop("metrics", None)

    @unittest.skipUnless(HAVE_SCIPY, "scipy is required")
    def test_wear_stats_finds_the_chip(self):
        zones = json.loads((self.ws / "reference/zones.json").read_text())
        zones["height_m"] = 2.0
        zones["bands"] = {"all": [0.0, 2.0]}
        # the synthetic chip is ~12x16 cm: the chip window must be wider than the chips (see SKILL.md Phase 3 traps)
        zones["chip"]["window_m"] = 0.3
        (self.ws / "reference/zones.json").write_text(json.dumps(zones))
        run(sys.executable, "-B", "tools/wear_stats.py", cwd=self.ws)
        res = json.loads((self.ws / "out/wear_stats_concept.json").read_text())
        self.assertGreater(res["front"]["all"]["chip_pct"], 0.5)
        self.assertEqual(res["front"]["all"]["chips"]["count"], 1)

    def test_sheet_builds_concept_render_pairs(self):
        (self.ws / "out/blender").mkdir(parents=True)
        for v in VIEWS:
            Image.open(self.ws / f"reference/crops/{v}.png").save(self.ws / f"out/blender/{v}.png")
        run(sys.executable, "-B", "tools/sheet.py", "out/s.png", "front,back", "blender", "0.5", cwd=self.ws)
        self.assertTrue((self.ws / "out/s.png").is_file())

    def test_shell_scripts_parse_and_rubric_weights_sum_to_one(self):
        for s in ["codex_review.sh", "gen_texture.sh", "init_workspace.sh"]:
            run("bash", "-n", str(SKILL / "scripts" / s))
        for name in ["rubric.json", "rubric_example_vending.json"]:
            crit = json.loads((SKILL / "assets/templates" / name).read_text())["criteria"]
            self.assertAlmostEqual(sum(c["weight"] for c in crit), 1.0, places=6)


if __name__ == "__main__":
    unittest.main()
