import hashlib
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from PIL import Image, ImageDraw
import numpy as np
import rasterio
from rasterio.transform import from_origin

from attach_regions import attach
from blind_review import read
from qguard import inspect


class AttachmentTests(unittest.TestCase):
    def setUp(self):
        temporary = TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.folder = Path(temporary.name)
        self.case = {"building_id": "A"}
        self.grade = {"building_id": "A", "grade": "moderate", "status": "ok",
                      "explanation_zh": "原始说明", "future_field": {"preserve": [None, 0, False]}}
        self.region = {"coords": "normalized_original_image", "post_xyxy": [.25, .25, .5, .5]}
        self.candidate = {"building_id": "A", "model": "test", "status": "ok", "change_status": "single",
                          "explanation_zh": "局部观察", "evidence_region": self.region}
        self.phase("")
        self.outputs = 0

    def record_image(self, key, image):
        filename = key + ".png"
        path = self.folder / filename
        image.save(path)
        self.case[key + "_path"] = filename
        self.candidate[key + "_sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()

    def phase(self, prefix):
        image = Image.new("RGB", (20, 20), "grey" if prefix else "white")
        self.record_image(prefix + "image", image)
        self.grade[prefix + "image_sha256"] = self.candidate[prefix + "image_sha256"]
        mask = Image.new("L", image.size)
        ImageDraw.Draw(mask).rectangle((5, 5, 14, 14), fill=255)
        self.record_image(prefix + "mask", mask)
        if prefix:
            self.region["pre_xyxy"] = [.4, .4, .7, .7]
            self.candidate["change_status"] = "changed"

    def inputs(self, candidates=None):
        rows = ([self.case], [self.grade], [self.candidate] if candidates is None else candidates)
        paths = tuple(self.folder / name for name in ("cases", "grades", "captions"))
        for path, records in zip(paths, rows):
            path.write_text("".join(json.dumps(r) + "\n" for r in records), encoding="utf8")
        return paths

    def observation(self, candidates=None):
        self.outputs += 1
        out = self.folder / str(self.outputs)
        counts = attach(*self.inputs(candidates), out)
        [record] = read(out)
        observation = record.pop("regional_observation")
        self.assertEqual(record, self.grade)
        self.assertEqual(counts, {observation["status"]: 1})
        return observation

    def test_single_and_pair(self):
        for prefix in ("", "pre_"):
            if prefix:
                self.phase(prefix)
            actual = self.observation()
            self.assertEqual(actual["status"], "available_for_review")
            for key in ("change_status", "evidence_region", "explanation_zh", prefix + "mask_sha256"):
                self.assertEqual(actual[key], self.candidate[key])

    def test_all_image_and_mask_hashes(self):
        self.phase("pre_")
        for key in ("image_sha256", "mask_sha256", "pre_image_sha256", "pre_mask_sha256"):
            with self.subTest(key=key):
                self.assertEqual(self.observation([{**self.candidate, key: "stale"}]),
                                 {"status": "regional_input_mismatch"})

    def test_replaced_explicit_validity_mask(self):
        self.phase("pre_")
        for key in ("valid_mask", "pre_valid_mask"):
            with self.subTest(key=key):
                self.record_image(key, Image.new("L", (20, 20), 255))
                self.assertEqual(self.observation()["status"], "available_for_review")
                path = self.folder / self.case[key + "_path"]
                Image.new("L", (20, 20), 0).save(path)
                self.assertEqual(self.observation(), {"status": "regional_input_mismatch"})
                self.record_image(key, Image.new("L", (20, 20), 255))

    def test_invalid_boxes_in_either_phase(self):
        self.phase("pre_")
        for key in ("pre_xyxy", "post_xyxy"):
            for box in (None, [-.1, 0, .5, .5], [0, 0, 1.1, .4], [0, 0, .2, .2],
                        [.2, .25, .26, .5], [.4, .4, .4, .5]):
                with self.subTest(key=key, box=box):
                    row = {**self.candidate, "evidence_region": {**self.region, key: box}}
                    self.assertEqual(self.observation([row]), {"status": "invalid_region"})

    def test_incomplete_candidates_and_phase(self):
        self.assertEqual(self.observation([]), {"status": "regional_output_unavailable"})
        row = {**self.candidate, "explanation_zh": ""}
        self.assertEqual(self.observation([row]), {"status": "regional_text_unavailable"})
        self.phase("pre_")
        del self.case["pre_mask_path"]
        self.assertEqual(self.observation(), {"status": "footprint_unavailable"})

    def test_missing_current_image_is_rejected_even_when_no_hash_claims_it(self):
        del self.case["image_path"], self.grade["image_sha256"], self.candidate["image_sha256"]
        self.candidate["evidence_region"] = None
        out = self.folder / "result"
        with self.assertRaises(ValueError):
            attach(*self.inputs(), out)
        self.assertFalse(out.exists())

    def test_quality_explanation_survives_upstream_abstention(self):
        self.grade.update(status="abstained", grade="uncertain")
        self.assertEqual(self.observation(), {"status": "upstream_review_required"})
        self.record_image("valid_mask", Image.new("L", (20, 20), 0))
        self.candidate = inspect(self.case, self.candidate, self.folder)
        actual = self.observation()
        self.assertEqual(actual["status"], "quality_limited")
        self.assertEqual(actual["explanation_zh"], self.candidate["explanation_zh"])
        self.assertIn("标记为无效", actual["explanation_zh"])
        self.assertIsNone(actual["evidence_region"])
        self.candidate["quality_guard"] = "invalid"
        self.assertEqual(self.observation(), {"status": "invalid_quality_record"})

    def test_external_gdal_validity_is_rechecked(self):
        self.phase("pre_")
        path = self.folder / "before.tif"
        self.case["pre_image_path"] = path.name
        valid = np.full((20, 20), 255, dtype=np.uint8)
        with rasterio.Env(GDAL_TIFF_INTERNAL_MASK=False):
            with rasterio.open(path, "w", driver="GTiff", height=20, width=20, count=3,
                               dtype="uint8", transform=from_origin(50, 50, 1, 1)) as image:
                image.write(np.full((3, 20, 20), 135, dtype=np.uint8))
                image.write_mask(valid)
        self.grade["pre_image_sha256"] = self.candidate["pre_image_sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
        self.candidate = inspect(self.case, self.candidate, self.folder)
        self.assertEqual(self.candidate["quality_guard"]["phases"]["pre"]["source"], "gdal_dataset_mask")
        self.assertEqual(self.observation()["status"], "available_for_review")
        with rasterio.open(str(path) + ".msk", "r+") as sidecar:
            valid[5:15, 5:15] = 0
            sidecar.write(valid, 1)
        self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), self.grade["pre_image_sha256"])
        self.assertEqual(self.observation(), {"status": "regional_input_mismatch"})

    def test_no_overwrite_or_double_attach(self):
        inputs = self.inputs()
        out = self.folder / "result"
        attach(*inputs, out)
        data = out.read_bytes()
        with self.assertRaises(FileExistsError):
            attach(*inputs, out)
        self.assertEqual(out.read_bytes(), data)
        again = self.folder / "again"
        with self.assertRaisesRegex(ValueError, "original grade"):
            attach(inputs[0], out, inputs[2], again)
        self.assertFalse(again.exists())

    def test_wrong_batch_rejected_atomically(self):
        for rows in ([{**self.candidate, "building_id": "foreign"}], [self.candidate] * 2):
            with self.assertRaises(ValueError):
                attach(*self.inputs(rows), self.folder / "result")
        self.grade["image_sha256"] = "stale"
        with self.assertRaisesRegex(ValueError, "different images"):
            attach(*self.inputs(), self.folder / "result")
        self.assertFalse((self.folder / "result").exists())
