import json
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest

import numpy as np
import rasterio
from rasterio.transform import from_origin

from apply_recall import run
from segmentation.vectorize_mask import vectorize


class ReviewPipeline(unittest.TestCase):
    def test_mask_to_projected_candidate_review(self):
        with TemporaryDirectory() as folder:
            root = Path(folder)
            tif = root / "raw.tif"
            pixels = np.zeros((12, 12), dtype="uint8")
            pixels[2:5, 2:7] = 1
            pixels[7:10, 8:10] = 2
            pixels[:, 0] = 255
            with rasterio.open(tif, "w", driver="GTiff", width=12, height=12, count=1,
                               dtype="uint8", crs="EPSG:32620", nodata=255,
                               transform=from_origin(500000, 2000000, 0.2, 0.2)) as dst:
                dst.write(pixels, 1)
            candidates = root / "source.geojson"
            self.assertEqual(vectorize(tif, candidates), 2)
            for mode in ("equal_budget", "low_fp"):
                output = root / (mode + ".geojson")
                result = run(SimpleNamespace(strong=[candidates], same=[candidates], dual=[candidates],
                                             mode=mode, class_field="cls", input_crs="EPSG:4326",
                                             work_crs=None, output=output))
                self.assertEqual(result["total"], 2)
                features = json.loads(output.read_bytes())["features"]
                self.assertEqual({f["properties"]["cls"] for f in features}, {"Decking", "Hole"})
            with self.assertRaises(FileExistsError):
                vectorize(tif, candidates)


if __name__ == "__main__":
    unittest.main()
