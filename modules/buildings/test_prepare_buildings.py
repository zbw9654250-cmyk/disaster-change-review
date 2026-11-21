"""Small regression tests for cropped coverage and overlapping damage measurements."""
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

import numpy as np
from PIL import Image
import rasterio
from rasterio.transform import from_origin
from shapely.geometry import box, mapping

from prepare_buildings import prepare


class BuildingPreparation(unittest.TestCase):
    def test_overlap_no_data_and_partial_images(self):
        with TemporaryDirectory() as example:
            folder = Path(example)
            image = folder / "raster.tif"
            with rasterio.open(image, "w", driver="GTiff", width=50, height=50, count=3,
                               crs="EPSG:32620", dtype="uint8", photometric="RGB",
                               transform=from_origin(500000, 2000050, 1, 1)) as out:
                out.write(np.full((3, 50, 50), 121, dtype=np.uint8))
                mask = np.full((50, 50), 255, dtype=np.uint8)
                mask[10:20, 30:40] = 0
                out.write_mask(mask)

            def collection(filename, features):
                path = folder / filename
                path.write_text(json.dumps({"type":"FeatureCollection","features":[
                    {"type":"Feature","properties":props,"geometry":mapping(rect)}
                    for props, rect in features], "crs":{"type":"name","properties":{"name":"EPSG:32620"}}}))
                return path

            footprints = collection("f.geojson", [
                ({"building_id":"complete"}, box(500010,2000010,500020,2000020)),
                ({"building_id":"partial"}, box(499995,2000010,500005,2000020)),
                ({"building_id":"occluded"}, box(500030,2000030,500040,2000040)),
            ])
            damage = collection("d.geojson", [
                ({"cls":"Decking"}, box(500012,2000012,500016,2000016)),
                ({"cls":"Hole"}, box(500014,2000014,500018,2000018)),
            ])
            output = folder / "output"
            manifest = prepare(image, footprints, damage, "test", output)
            records = list(map(json.loads, manifest.read_text().splitlines()))
            complete, partial, occluded = records
            self.assertEqual(complete["roof_evidence"]["union_damage_m2"], 28)
            self.assertEqual(complete["roof_evidence"]["damage_fraction"], .28)
            self.assertEqual(complete["coverage_fraction"], 1)
            self.assertAlmostEqual(partial["coverage_fraction"], .5, places=2)
            self.assertEqual(occluded["coverage_fraction"], 0)
            self.assertEqual(partial["quality_flag"], "partial_coverage")
            self.assertEqual(occluded["quality_flag"], "partial_coverage")
            for rec in records:
                self.assertTrue((output / rec["image_path"]).is_file())
                with Image.open(output / rec["image_path"]) as clean, Image.open(output / rec["mask_path"]) as mask, Image.open(output / rec["valid_mask_path"]) as valid, Image.open(output / rec["preview_path"]) as preview:
                    self.assertEqual(clean.size, mask.size)
                    self.assertEqual(mask.size, valid.size)
                    self.assertEqual(set(np.unique(mask)), {0, 255})
                    self.assertNotEqual(clean.tobytes(), preview.tobytes())
                    self.assertFalse(((np.asarray(clean) == [5, 237, 239]).all(axis=-1)).any())
            self.assertRaises(FileExistsError, prepare, image, footprints, damage, "test", output)
            without = prepare(image, footprints, None, "test", folder / "no-damage")
            self.assertIsNone(json.loads(without.read_text().splitlines()[0])["roof_evidence"])


if __name__ == "__main__":
    unittest.main()
