"""Model-free tests for grid_overlay.py, crop.py and blend.py. Skipped when Pillow or numpy is missing."""
import json
import pathlib
import sys
import tempfile
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

try:
    import numpy as np
    from PIL import Image
    HAVE_DEPS = True
except ImportError:
    HAVE_DEPS = False


@unittest.skipUnless(HAVE_DEPS, "Pillow and numpy are required")
class ToolsTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = pathlib.Path(self.tmp.name)
        self.concept = self.dir / "concept.png"
        Image.new("RGB", (200, 100), (10, 20, 30)).save(self.concept)

    def tearDown(self):
        self.tmp.cleanup()

    def test_homography_maps_the_four_corners(self):
        import grid_overlay
        src = [(0, 0), (4, 0), (4, 3), (0, 3)]
        dst = [(20, 10), (180, 15), (170, 90), (30, 85)]
        h = grid_overlay.homography(src, dst)
        np.testing.assert_allclose(grid_overlay.project(h, np.asarray(src, float)), dst, atol=1e-6)

    def test_cell_labels(self):
        import grid_overlay
        square = grid_overlay.cells("square", "pointy", 2, 2, cell_m=2.5)
        self.assertEqual([label for _, label in square], ["1.25,1.25", "3.75,1.25", "1.25,3.75", "3.75,3.75"])
        hexes = grid_overlay.cells("hex", "pointy", 2, 3)
        self.assertEqual([label for _, label in hexes], ["0,0", "1,0", "0,1", "1,1", "-1,2", "0,2"])
        self.assertTrue(all(len(p) == 6 for p, _ in hexes))
        flat = grid_overlay.cells("hex", "flat", 3, 2)
        self.assertEqual([label for _, label in flat], ["0,0", "1,0", "2,-1", "0,1", "1,1", "2,0"])

    def test_overlay_draws_on_the_concept(self):
        import grid_overlay
        out = self.dir / "overlay.png"
        grid_overlay.main([str(self.concept), "--grid", "square", "--cols", "4", "--rows", "2",
                           "--corners", "10,10 190,10 190,90 10,90", "-o", str(out)])
        im = Image.open(out)
        self.assertEqual(im.size, (200, 100))
        self.assertIn((255, 0, 255), {px for _, px in im.getcolors(200 * 100)})
        for bad in ("1,1 2,2 3,3", "5,5 5,5 5,5 5,5", "0,0 10,0 20,0 30,0", "10,10 190,10 10,90 190,90"):
            with self.assertRaises(ValueError, msg=bad):
                grid_overlay.parse_corners(bad)
        # mirrored order (counter-clockwise) is still a valid convex quad
        grid_overlay.parse_corners("10,90 190,90 190,10 10,10")

    def test_crop_writes_each_box_and_rejects_bad_boxes(self):
        import crop
        out = self.dir / "kit"
        written = crop.crop(str(self.concept), {"tile_grass": [0, 0, 50, 40]}, out)
        self.assertEqual([p.name for p in written], ["tile_grass.png"])
        self.assertEqual(Image.open(out / "tile_grass.png").size, (50, 40))
        fresh = self.dir / "fresh"
        for boxes in ({"ok": [0, 0, 5, 5], "bad": [150, 0, 250, 40]}, {"../escape": [0, 0, 5, 5]},
                      {"short": [0, 0, 5]}, [[0, 0, 5, 5]]):
            with self.assertRaises(ValueError, msg=str(boxes)):
                crop.crop(str(self.concept), boxes, fresh)
        self.assertFalse(fresh.exists())
        boxes = self.dir / "boxes.json"
        boxes.write_text(json.dumps({"rock": [10, 10, 20, 30]}))
        crop.main([str(self.concept), str(boxes), "-o", str(out)])
        self.assertEqual(Image.open(out / "rock.png").size, (10, 20))

    def test_blend_resizes_the_render_to_the_concept(self):
        import blend
        render = self.dir / "render.png"
        Image.new("RGB", (50, 25), (210, 220, 230)).save(render)
        out = self.dir / "blend.png"
        blend.main([str(self.concept), str(render), "-o", str(out)])
        im = Image.open(out)
        self.assertEqual(im.size, (200, 100))
        self.assertEqual(im.getpixel((100, 50)), (110, 120, 130))


if __name__ == "__main__":
    unittest.main()
