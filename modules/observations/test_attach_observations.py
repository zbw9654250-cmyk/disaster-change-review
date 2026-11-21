"""CPU regression checks for attaching measured evidence to an existing grade manifest."""
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from PIL import Image, ImageDraw

from attach_observations import attach_observations
from evidence import measure


class ObservationAttachmentTests(unittest.TestCase):
    def setUp(self):
        temp = TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.folder = Path(temp.name)
        self.case = {"building_id": "QA", "image_path": "source.png", "mask_path": "outline.png"}
        source = Image.new("RGB", (180, 180), (100, 110, 130))
        ImageDraw.Draw(source).rectangle((42, 45, 90, 90), fill=(160, 178, 185))
        source.save(self.folder / "source.png")
        outline = Image.new("L", source.size)
        ImageDraw.Draw(outline).rectangle((30, 30, 150, 150), fill=255)
        outline.save(self.folder / "outline.png")
        self.output = self.folder / "result.jsonl"

    def run_case(self, prediction):
        grade = {"building_id": "QA", "status": "ok", "grade": "light", "image_sha256": prediction["image_sha256"],
                 "upstream_details": {"confidence": 0.8}}
        if prediction.get("pre_image_sha256"):
            grade["pre_image_sha256"] = prediction["pre_image_sha256"]
        paths = []
        for name, record in (("cases", self.case), ("grade", grade), ("candidates", prediction)):
            path = self.folder / (name + ".jsonl")
            path.write_text(json.dumps(record) + "\n", encoding="utf8")
            paths.append(path)
        attach_observations(*paths, self.output)
        result = json.loads(self.output.read_bytes())
        self.assertEqual(grade, {k: v for k, v in result.items() if k != "regional_observation"})
        return result["regional_observation"]

    def test_low_coverage_keeps_both_quality_decisions_and_recomputes_reason(self):
        self.case.update(pre_image_path="source.png", pre_mask_path="outline.png", pre_coverage_fraction=0.6)
        row = measure(self.case, self.folder)
        self.assertEqual(row["status"], "quality_limited")
        reason = row["explanation_zh"]
        row["explanation_zh"] = "unexpected text"
        obs = self.run_case(row)
        self.assertEqual(obs["status"], "quality_limited")
        self.assertEqual(obs["explanation_zh"], reason)
        self.assertIsNone(obs["evidence_region"])
        self.assertEqual(obs["quality_guard"]["pixel_decision"], "pass")
        self.assertEqual(obs["quality_guard"]["measurement_decision"], "withhold")
        self.assertTrue(obs["quality_guard"]["measurement_reproduced"])
        with self.assertRaises(FileExistsError):
            self.run_case(row)

    def test_explicit_validity_blocks_and_confirms_inference(self):
        self.case["valid_mask_path"] = "valid.png"
        Image.new("L", (180, 180), 0).save(self.folder / "valid.png")
        obs = self.run_case(measure(self.case, self.folder))
        self.assertEqual(obs["quality_guard"]["pixel_decision"], "withhold")
        self.assertTrue(obs["quality_guard"]["measurement_reproduced"])
        self.assertEqual(obs["quality_guard"]["phases"]["post"]["source"], "explicit_valid_mask")
        self.assertEqual(obs["status"], "quality_limited")

    def test_changed_validity_rejects_the_batch_without_writing(self):
        self.case["valid_mask_path"] = "valid.png"
        img = Image.new("L", (180, 180), 255)
        img.save(self.folder / "valid.png")
        row = measure(self.case, self.folder)
        self.assertEqual(row["status"], "ok")
        img.putpixel((0, 0), 0)
        img.save(self.folder / "valid.png")
        with self.assertRaisesRegex(ValueError, "validity mask"):
            self.run_case(row)
        self.assertFalse(self.output.exists())

    def test_passing_single_is_published(self):
        row = measure(self.case, self.folder)
        obs = self.run_case(row)
        self.assertEqual(obs["status"], "available_for_review")
        self.assertEqual(obs["explanation_zh"], row["explanation_zh"])
        self.assertEqual(obs["change_status"], "single")

    def test_updated_earlier_coverage_also_withholds_previously_passing_pair(self):
        self.case.update(pre_image_path="source.png", pre_mask_path="outline.png")
        row = measure(self.case, self.folder)
        self.assertEqual(row["status"], "ok")
        self.case["pre_coverage_fraction"] = 0.5
        obs = self.run_case(row)
        self.assertEqual(obs["status"], "quality_limited")
        self.assertTrue(obs["quality_guard"]["measurement_reproduced"])

    def test_nonfinite_coverage_cannot_publish_a_candidate(self):
        row = measure(self.case, self.folder)
        self.case["coverage_fraction"] = "nan"
        with self.assertRaisesRegex(ValueError, "invalid coverage fraction"):
            self.run_case(row)
        self.assertFalse(self.output.exists())


if __name__ == "__main__":
    unittest.main()
