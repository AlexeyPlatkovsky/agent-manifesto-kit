"""Model-free tests for compare.py and metrics.py. Skipped when Pillow or numpy is missing."""
import json
import pathlib
import random
import sys
import tempfile
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

try:
    import numpy  # noqa: F401
    from PIL import Image
    HAVE_DEPS = True
except ImportError:
    HAVE_DEPS = False


@unittest.skipUnless(HAVE_DEPS, "Pillow and numpy are required")
class ToolsTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = pathlib.Path(self.tmp.name)
        self.red = self.dir / "red.png"
        self.blue = self.dir / "blue.png"
        Image.new("RGB", (64, 32), (255, 0, 0)).save(self.red)
        Image.new("RGB", (32, 32), (0, 0, 255)).save(self.blue)

    def tearDown(self):
        self.tmp.cleanup()

    def test_sheet_scales_to_common_height(self):
        import compare
        out = self.dir / "sheet.png"
        compare.main(["sheet", str(self.red), str(self.blue), str(self.red), "-o", str(out)])
        im = Image.open(out)
        self.assertEqual(im.height, compare.HEIGHT + compare.LABEL_BAR)
        self.assertEqual(im.width, 1440 + 720 + 1440 + 2 * compare.GAP)

    def test_blind_keeps_mapping_outside_the_reviewer_folder(self):
        import compare
        out = self.dir / "blind"
        mapping = compare.blind(str(self.red), str(self.blue), out, rng=random.Random(1))
        self.assertEqual(sorted(p.name for p in out.iterdir()), ["A.png", "B.png"])
        saved = json.loads((self.dir / "blind.mapping.json").read_text())
        self.assertEqual(saved, mapping)
        self.assertEqual(sorted(saved.values()), ["after", "before"])
        before_slot = next(s for s, label in saved.items() if label == "before")
        self.assertEqual(Image.open(out / f"{before_slot}.png").getpixel((0, 0)), (255, 0, 0))

    def test_blind_writes_an_explicit_mapping_and_refuses_one_inside_the_folder(self):
        import compare
        out = self.dir / "tmp" / "gameplay_wide"
        target = self.dir / "project" / "gameplay_wide.mapping.json"
        mapping = compare.blind(str(self.red), str(self.blue), out, mapping=target)
        self.assertEqual(json.loads(target.read_text()), mapping)
        self.assertFalse((out.parent / "gameplay_wide.mapping.json").exists())
        refused = self.dir / "tmp" / "refused"
        with self.assertRaises(ValueError):
            compare.blind(str(self.red), str(self.blue), refused, mapping=refused / "m.json")
        self.assertFalse(refused.exists())

    def test_metrics_are_deterministic_and_find_the_palette(self):
        import metrics
        half = self.dir / "half.png"
        im = Image.new("RGB", (40, 20), (0, 0, 0))
        im.paste((255, 255, 255), (20, 0, 40, 20))
        im.save(half)
        out = self.dir / "m.json"
        metrics.main([str(half), "-o", str(out)])
        first = out.read_text()
        metrics.main([str(half), "-o", str(out)])
        self.assertEqual(first, out.read_text())
        data = json.loads(first)[str(half)]
        self.assertEqual(data["lum_p5_p50_p95"][0], 0.0)
        self.assertEqual(data["lum_p5_p50_p95"][2], 1.0)
        self.assertEqual(data["sat_mean"], 0.0)
        top = {c["hex"]: c["share"] for c in data["palette"] if c["share"] > 0}
        self.assertEqual(top, {"#000000": 0.5, "#ffffff": 0.5})


if __name__ == "__main__":
    unittest.main()
