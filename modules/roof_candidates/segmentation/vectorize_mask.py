"""Convert a single-band georeferenced roof mask to WGS84 candidate polygons."""
import argparse
import json
import os
from pathlib import Path
from tempfile import NamedTemporaryFile

import rasterio
from rasterio.features import shapes
from rasterio.warp import transform_geom
from shapely import make_valid
from shapely.geometry import mapping, shape

CLASSES = {1: "Decking", 2: "Hole"}


def surfaces(geometry):
    if geometry.is_empty:
        return
    if geometry.geom_type == "Polygon":
        yield geometry
    elif geometry.geom_type in ("MultiPolygon", "GeometryCollection"):
        for part in geometry.geoms:
            yield from surfaces(part)


def vectorize(mask, output):
    output = Path(output)
    if output.exists():
        raise FileExistsError(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    temporary = None
    try:
        with rasterio.open(mask) as src, NamedTemporaryFile(
            "w", encoding="utf8", dir=output.parent, delete=False
        ) as dst:
            temporary = Path(dst.name)
            if src.count != 1 or src.dtypes[0] != "uint8" or not src.crs:
                raise ValueError("A single-band uint8 classification raster with a CRS is required")
            if src.nodata not in (None, 0, 255):
                raise ValueError("Expected nodata 255 or background 0")
            dst.write('{"type":"FeatureCollection","features":[')
            for geom, raw_code in shapes(rasterio.band(src, 1), transform=src.transform, connectivity=4):
                code = int(raw_code)
                if code in (0, 255):
                    continue
                if code not in CLASSES:
                    raise ValueError(f"Unknown roof class {code}")
                projected = shape(transform_geom(src.crs, "EPSG:4326", geom))
                for polygon in surfaces(make_valid(projected)):
                    feature = {"type": "Feature", "geometry": mapping(polygon),
                               "properties": {"id": count, "cls": CLASSES[code]}}
                    if count:
                        dst.write(",")
                    json.dump(feature, dst, separators=(",", ":"), allow_nan=False)
                    count += 1
            dst.write("]}\n")
        os.link(temporary, output)
    finally:
        if temporary:
            temporary.unlink(missing_ok=True)
    return count


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mask", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    print(f"{vectorize(args.mask, args.output)} roof polygons")
