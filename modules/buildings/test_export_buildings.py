import hashlib
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from PIL import Image
from export_buildings import combine


class ExportTest(unittest.TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.cases = self.root / "cases.jsonl"
        self.pred = self.root / "predictions.jsonl"
        self.out = self.root / "out"
        photo = self.root / "post.png"
        Image.new("RGB", (32, 32), "blue").save(photo)
        self.rows = [{"building_id": "A", "image_path": "post.png", "geometry": {
            "type": "Polygon", "coordinates": [[[0,0],[1,0],[1,1],[0,0]]]}, "coverage_fraction": .9},
            {"building_id": "B", "image_path": "post.png"}]
        self.answers = [{"building_id": k, "grade":"moderate", "explanation_zh":"轮廓中部可见色块 <核对>",
                     "model":"test-fixture", "review_required":False,
                     "image_sha256": hashlib.sha256(photo.read_bytes()).hexdigest()} for k in ("B","A")]
        self.save()

    def save(self):
        for path, records in ((self.cases,self.rows),(self.pred,self.answers)):
            path.write_text("".join(json.dumps(item)+"\n" for item in records), encoding="utf-8")

    def test_join_geometry_and_partial(self):
        report = combine(self.cases,self.pred,self.out)
        self.assertEqual((report["cases"],report["geolocated"]),(2,1))
        props = json.loads((self.out/"buildings.geojson").read_bytes())["features"][0]["properties"]
        self.assertEqual((props["building_id"],props["grade"],props["model_grade"]),("A","uncertain","moderate"))
        self.assertTrue(props["review_required"])
        self.assertIn("&lt;核对&gt;",(self.out/"review.html").read_text("utf-8"))
        with self.assertRaises(FileExistsError):
            combine(self.cases,self.pred,self.out)

    def test_mismatched_ids_and_photo_rejected(self):
        self.answers[0]["building_id"] = "C"
        self.save()
        with self.assertRaisesRegex(ValueError,"IDs differ"):
            combine(self.cases,self.pred,self.out)
        self.answers[0]["building_id"] = "B"
        self.answers[0]["image_sha256"] = "0"*64
        self.save()
        with self.assertRaisesRegex(ValueError,"matches inference input"):
            combine(self.cases,self.pred,self.out)
        self.assertFalse(self.out.exists())

    def test_failed_prediction_preserves_building_with_no_fabricated_observation(self):
        self.rows[0]["image_path"] = "absent.png"
        self.answers[1].update(status="inference_error", grade="uncertain", explanation_zh="", review_required=True)
        self.save()
        combine(self.cases,self.pred,self.out)
        props = json.loads((self.out/"buildings.geojson").read_bytes())["features"][0]["properties"]
        self.assertIsNone(props["explanation_zh"])
        self.assertEqual(props["status"], "inference_error")


if __name__ == "__main__":
    unittest.main()
