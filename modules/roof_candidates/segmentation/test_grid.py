"""Verify halo placement, source NoData, and incomplete outer tiles on a tiny raster."""
import tempfile
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace
from importlib.util import find_spec
from unittest import SkipTest

if any(find_spec(dep) is None for dep in ("torch", "pyogrio")):
    raise SkipTest("The optional GeoTIFF segmentation stack needs torch and pyogrio")

def test_hann_and_georeferencing():
    # Keep OpenMMLab/PyTorch native runtimes separate from the CPU review suite.
    subprocess.run([sys.executable, __file__], check=True)


def check_grid():
    import numpy as np
    import rasterio
    from rasterio.enums import ColorInterp
    from rasterio.transform import from_origin
    import torch
    from infer import run

    class ColorModel:
        decode_head = SimpleNamespace(num_classes=3)

        def encode_decode(self, normalized, _):
            return normalized

    torch.set_num_threads(2)
    with tempfile.TemporaryDirectory() as folder:
        rgb = Path(folder) / "rgb.tif"
        out = Path(folder) / "mask.tif"
        h, w = 551, 731
        y, x = np.indices((h, w))
        expected = ((x//17+y//31) % 3).astype("uint8")
        bands = np.stack([(expected == i)*255 for i in range(3)]).astype("uint8")
        alpha = np.full((h, w), 255, dtype="uint8")
        alpha[5:12, 499:520] = 0
        affine = from_origin(500000, 2000000, .05, .05)
        with rasterio.open(rgb, "w", driver="GTiff", count=4, dtype="uint8", width=w, height=h,
                           crs="EPSG:32620", transform=affine, photometric="RGB") as dst:
            dst.colorinterp = (ColorInterp.red, ColorInterp.green, ColorInterp.blue, ColorInterp.alpha)
            dst.write(bands, indexes=[1, 2, 3])
            dst.write(alpha, 4)
        stats = run(rgb, out, None, device="cpu", model_loader=lambda *unused: ColorModel())
        with rasterio.open(out) as ds:
            got = ds.read(1)
            assert ds.transform == affine and ds.nodata == 255
            assert (got[h:] == 255).all() and (got[:, w:] == 255).all()
            expected[alpha == 0] = 255
            np.testing.assert_array_equal(got[:h, :w], expected)
        assert stats["valid_pixels"] == int((alpha != 0).sum())
        baseline = Path(folder) / "baseline.tif"
        stats = run(rgb, baseline, None, device="cpu", tiling="nonoverlap",
                    model_loader=lambda *unused: ColorModel())
        with rasterio.open(baseline) as ds:
            np.testing.assert_array_equal(ds.read(1), got)
        assert stats["chip_forward_passes"] == stats["blocks"]


if __name__ == "__main__":
    check_grid()
    print("Passed coordinate, Hann seam, alpha NoData and partial tile check")
