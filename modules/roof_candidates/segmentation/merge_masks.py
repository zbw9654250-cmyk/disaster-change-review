"""Merge dual-model decking and specialist holes. The hole prediction wins overlaps."""
import argparse
import json
from pathlib import Path
from tempfile import TemporaryDirectory

import numpy as np
import rasterio


def merge(dual_mask, hole_mask, output):
    if output.exists():
        raise FileExistsError(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    with rasterio.open(dual_mask) as dual, rasterio.open(hole_mask) as holes:
        if (dual.crs, dual.transform, dual.shape) != (holes.crs, holes.transform, holes.shape):
            raise ValueError("Input masks must have identical CRS, transform and extent")
        if any(ds.count != 1 or ds.nodata != 255 for ds in (dual, holes)):
            raise ValueError("Both masks must have one band and use 255 for nodata")
        valid_pixels = conflict_pixels = total_holes = dual_holes_replaced = 0
        with TemporaryDirectory(dir=output.parent) as tmp:
            local = Path(tmp) / "mask.tif"
            with rasterio.open(local, "w", **dual.profile) as dst:
                for _, window in dual.block_windows(1):
                    d, h = dual.read(1, window=window), holes.read(1, window=window)
                    if not np.isin(d, [0, 1, 2, 255]).all() or not np.isin(h, [0, 2, 255]).all():
                        raise ValueError("Unexpected class codes")
                    if not np.array_equal(d == 255, h == 255):
                        raise ValueError("Valid pixel footprints differ")
                    valid_pixels += int(np.count_nonzero(d != 255))
                    conflict_pixels += int(np.count_nonzero((d == 1) & (h == 2)))
                    total_holes += int(np.count_nonzero(h == 2))
                    dual_holes_replaced += int(np.count_nonzero((d == 2) & (h == 0)))
                    combined = np.where(h == 2, 2, np.where(d == 2, 0, d))
                    dst.write(combined.astype("uint8"), 1, window=window)
                dst.update_tags(classes="0=background; 1=Decking; 2=Hole; 255=NoData",
                                conflict_rule="expert Hole (2) has priority over dual Decking (1)")
            local.rename(output)
    return dict(valid_pixels=valid_pixels, expert_hole_pixels=total_holes,
                dual_decking_expert_hole_conflict_pixels=conflict_pixels,
                dual_only_hole_pixels_removed=dual_holes_replaced,
                rule="Use only dual Decking and specialist Hole, with Hole priority at conflicts")


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("--dual-mask", required=True, type=Path)
    cli.add_argument("--hole-mask", required=True, type=Path)
    cli.add_argument("--output", required=True, type=Path)
    cli.add_argument("--stats", type=Path)
    args = cli.parse_args()
    report = json.dumps(merge(args.dual_mask, args.hole_mask, args.output), indent=2)
    if args.stats:
        args.stats.write_text(report, encoding="utf-8")
    print(report)
