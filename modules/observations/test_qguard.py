import hashlib
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

import numpy as np
from PIL import Image, ImageDraw
import rasterio
from rasterio.transform import from_origin

from qguard import apply, inspect


class QualityFixtures(unittest.TestCase):
    def setUp(self):
        temporary = TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.rgb = np.full((128, 128, 3), 145, dtype=np.uint8)
        self.target = np.zeros((128, 128), dtype=np.uint8)
        self.target[:96, 20:100] = 255
        self.case = {"building_id": "fixture", "image_path": "current.png", "mask_path": "foot.png"}
        self.candidate = {"building_id": "fixture", "model": "fixture", "status": "ok", "change_status": "changed",
                          "explanation_zh": "待复核的结构断言", "raw_candidate": "旧候选", "raw_verification": "旧结果",
                          "evidence_region": {"coords": "normalized_original_image", "post_xyxy": [.2, 0, .55, .3]}}
        self.write("image", self.rgb)
        self.write("mask", self.target)

    def write(self, key, array):
        path = self.root / self.case[key + "_path"]
        Image.fromarray(array).save(path)
        self.candidate[key + "_sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()

    def check(self):
        return inspect(self.case, self.candidate, self.root)

    def test_frame_void_censors_all_model_assertions(self):
        self.rgb[:25] = 0
        self.write("image", self.rgb)
        result = self.check()
        self.assertEqual(result["status"], "quality_limited")
        self.assertEqual(result["change_status"], "uncertain")
        self.assertIsNone(result["evidence_region"])
        self.assertNotIn("raw_verification", result)
        self.assertNotIn("raw_candidate", result)
        self.assertNotIn("结构断言", result["explanation_zh"])
        self.assertIn("缺少可辨细节", result["explanation_zh"])
        self.assertEqual(result["quality_guard"]["phases"]["post"]["bands_px"], {"top": 25})

    def test_dark_roof_and_edge_touching_shadow(self):
        self.rgb[self.target > 0] = (4, 3, 2)
        self.rgb[:88, :43] = 0
        self.write("image", self.rgb)
        self.assertEqual(self.check()["quality_guard"]["decision"], "pass")

    def test_cyan_jpeg_footprint_outline_inside_frame_band(self):
        self.case["image_path"] = "marked.jpg"
        self.target[:] = 0
        self.target[12:90, 28:89] = 255
        self.write("mask", self.target)
        self.rgb[:50] = 0
        image = Image.fromarray(self.rgb)
        ImageDraw.Draw(image).rectangle((28, 12, 88, 89), outline=(0, 255, 255), width=1)
        image.save(self.root / "marked.jpg", quality=90)
        self.candidate["image_sha256"] = hashlib.sha256((self.root / "marked.jpg").read_bytes()).hexdigest()
        result = self.check()
        self.assertEqual(result["status"], "quality_limited")
        self.assertGreaterEqual(result["quality_guard"]["phases"]["post"]["bands_px"]["top"], 46)

    def test_unrelated_frame_void_preserves_candidate(self):
        self.rgb[-25:] = 0
        self.write("image", self.rgb)
        result = self.check()
        self.assertEqual(result["quality_guard"]["decision"], "pass")
        self.assertEqual(result["explanation_zh"], self.candidate["explanation_zh"])
        self.assertEqual(result["evidence_region"], self.candidate["evidence_region"])

    def test_explicit_all_valid_precedes_shadow_heuristic(self):
        self.rgb[:25] = 0
        self.write("image", self.rgb)
        self.case["valid_mask_path"] = "valid.png"
        Image.fromarray(np.full((128, 128), 255, dtype=np.uint8)).save(self.root / "valid.png")
        result = self.check()
        self.assertEqual(result["quality_guard"]["decision"], "pass")
        self.assertEqual(result["quality_guard"]["phases"]["post"]["source"], "explicit_valid_mask")
        self.assertEqual(result["valid_mask_sha256"], hashlib.sha256((self.root / "valid.png").read_bytes()).hexdigest())

    def test_earlier_explicit_mask_blocks_roi_even_when_target_fraction_is_small(self):
        self.case.update(pre_image_path="before.png", pre_mask_path="prior-foot.png", pre_valid_mask_path="valid.png")
        self.write("pre_image", self.rgb)
        self.write("pre_mask", self.target)
        self.candidate["evidence_region"]["pre_xyxy"] = [20/128, 0, 40/128, 20/128]
        valid = np.full(self.target.shape, 255, dtype=np.uint8)
        valid[:16, 20:37] = 0
        Image.fromarray(valid).save(self.root / "valid.png")
        result = self.check()
        self.assertEqual(result["status"], "quality_limited")
        self.assertIn("较早影像", result["explanation_zh"])
        self.assertFalse(result["quality_guard"]["phases"]["post"]["withhold"])
        self.assertTrue(result["quality_guard"]["phases"]["pre"]["withhold"])
        self.assertEqual(result["pre_valid_mask_sha256"], hashlib.sha256((self.root / "valid.png").read_bytes()).hexdigest())

    def test_embedded_gdal_mask_overrides_visible_rgb(self):
        path = self.root / "image.tif"
        self.case["image_path"] = path.name
        valid = np.full(self.target.shape, 255, dtype=np.uint8)
        valid[:30, 20:100] = 0
        with rasterio.open(path, "w", driver="GTiff", height=128, width=128, count=3, dtype="uint8",
                           crs="EPSG:3857", transform=from_origin(10, 74, 1, 1)) as src:
            src.write(self.rgb.transpose(2, 0, 1))
            src.write_mask(valid)
        self.candidate["image_sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
        result = self.check()
        self.assertEqual(result["quality_guard"]["phases"]["post"]["source"], "gdal_dataset_mask")
        self.assertEqual(result["status"], "quality_limited")

    def test_mismatched_bytes_abort_atomic_batch(self):
        self.candidate["mask_sha256"] = "stale"
        for name, obj in (("cases", self.case), ("candidates", self.candidate)):
            (self.root / name).write_text(json.dumps(obj), encoding="utf8")
        with self.assertRaisesRegex(ValueError, "differs"):
            apply(self.root / "cases", self.root / "candidates", self.root / "out")
        self.assertFalse((self.root / "out").exists())

    def test_stale_earlier_phase_is_rejected(self):
        self.candidate["pre_image_sha256"] = self.candidate["image_sha256"]
        with self.assertRaisesRegex(ValueError, "phases differ"):
            self.check()


if __name__ == "__main__":
    unittest.main()
