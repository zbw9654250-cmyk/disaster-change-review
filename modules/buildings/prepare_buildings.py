"""Prepare footprint-conditioned building images and intersect optional roof-damage predictions."""
import argparse
import hashlib
import json
import math
import os
from pathlib import Path
from tempfile import TemporaryDirectory

import numpy as np
import rasterio
from PIL import Image, ImageDraw
from pyproj import CRS, Transformer
from rasterio.enums import ColorInterp, Resampling
from rasterio.features import rasterize
from rasterio.windows import Window
from shapely import STRtree, union_all, transform
from shapely.affinity import affine_transform
from shapely.geometry import mapping, shape

WGS84 = CRS.from_epsg(4326)
CLASSES = ("Decking", "Hole")


def polygons(path):
    doc = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    if doc.get("type") != "FeatureCollection" or not isinstance(doc.get("features"), list):
        raise ValueError(f"Expected a FeatureCollection in {path}")
    src = CRS.from_user_input(doc["crs"]["properties"]["name"]) if "crs" in doc else WGS84
    result = []
    for i, feature in enumerate(doc["features"]):
        geom = shape(feature["geometry"])
        if geom.geom_type not in ("Polygon", "MultiPolygon") or geom.is_empty or not geom.is_valid:
            raise ValueError(f"Invalid polygon in {path} at feature {i}")
        result.append((geom, feature.get("properties") or {}))
    return src, result


def reproject(geometry, source, destination):
    if source == destination:
        return geometry
    forward = Transformer.from_crs(source, destination, always_xy=True).transform
    return transform(geometry, forward, interleaved=False)


def affine_geometry(g, a):
    return affine_transform(g, [a.a, a.b, a.d, a.e, a.c, a.f])


def roof_stats(building, metric_damages, damage_index):
    clipped = {c: [] for c in CLASSES}
    area = building.area
    for i in damage_index.query(building, predicate="intersects"):
        damage, label, source_id = metric_damages[i]
        part = damage.intersection(building)
        if part.area > 0:
            clipped[label].append((part, source_id))
    result = {}
    all_parts = []
    for label, clips in clipped.items():
        parts = [g for g, _ in clips]
        all_parts.extend(parts)
        result[label] = {"count": len(clips), "area_m2": round(union_all(parts).area, 3),
                         "source_ids": sorted(source_id for _, source_id in clips)}
    total = union_all(all_parts).area
    result.update(footprint_m2=round(area, 3), union_damage_m2=round(total, 3),
                  damage_fraction=round(min(1.0, total / area), 6))
    return result


def crop_image(src, footprint, source_crs, bands):
    pixels = affine_geometry(reproject(footprint, source_crs, src.crs), ~src.transform)
    lo_x, lo_y, hi_x, hi_y = pixels.bounds
    side = max(32, math.ceil(max(hi_x - lo_x, hi_y - lo_y) * 1.34))
    left = math.floor((lo_x + hi_x - side) / 2)
    top = math.floor((lo_y + hi_y - side) / 2)
    window = Window(left, top, side, side)
    size = min(side, 768)
    scale = size / side
    rgb = src.read(bands, window=window, out_shape=(3, size, size), boundless=True,
                   resampling=Resampling.bilinear)
    valid = src.read_masks(bands, window=window, out_shape=(3, size, size), boundless=True,
                           resampling=Resampling.nearest).all(axis=0)
    outline = affine_transform(pixels, [scale, 0, 0, scale, -left * scale, -top * scale])
    target = rasterize([(mapping(outline), 1)], out_shape=(size, size), dtype="uint8").astype(bool)
    visible = np.count_nonzero(target & valid) / target.sum() if target.any() else 0.
    if size < 320:
        size_out = 320
    else:
        size_out = size
    img = Image.fromarray(np.moveaxis(rgb, 0, -1)).resize((size_out, size_out), Image.Resampling.BILINEAR)
    preview = img.copy()
    draw = ImageDraw.Draw(preview)
    width = max(1, round(size_out / 320))
    factor = size_out / size
    marked = outline.buffer((2 * width) / factor, join_style="mitre")
    for part in ([marked] if marked.geom_type == "Polygon" else marked.geoms):
        for ring in (part.exterior, *part.interiors):
            draw.line([(x * factor, y * factor) for x, y in ring.coords],
                      fill=(5, 237, 239), width=width)
    def binary_image(values):
        return Image.fromarray(values.astype("uint8") * 255).resize(img.size, Image.Resampling.NEAREST)
    return img, preview, binary_image(target), binary_image(valid), float(visible), [left, top, side, side]


def prepare(raster, footprints, damage, scene_id, output):
    fp_crs, fp = polygons(footprints)
    if not fp:
        raise ValueError("No building footprints found")
    ids = [v.get("building_id") for _, v in fp]
    if any(not isinstance(v, str) or not v.strip() for v in ids) or len(set(ids)) != len(ids):
        raise ValueError("Each footprint must have a unique nonempty string building_id")
    lon, lat = reproject(fp[0][0], fp_crs, WGS84).representative_point().coords[0]
    if not (-180 <= lon <= 180 and -80 <= lat <= 84):
        raise ValueError("Expected a scene within WGS84 UTM coverage")
    zone = min(60, 1 + int((lon + 180) // 6))
    metric = CRS.from_epsg((32600 if lat >= 0 else 32700) + zone)
    metric_damages = []
    if damage:
        damage_crs, predictions = polygons(damage)
        for i, (geom, prop) in enumerate(predictions):
            label = prop.get("cls")
            if label not in CLASSES:
                raise ValueError(f"Unrecognized roof class {label!r}")
            metric_damages.append((reproject(geom, damage_crs, metric), label,
                                   f"{label}:{prop.get('id', i)}"))
    index = STRtree([g for g, _, _ in metric_damages])
    output = Path(output)
    if output.exists():
        raise FileExistsError(f"Choose a new output directory: {output}")
    output.parent.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(dir=output.parent) as temp, rasterio.open(raster) as src:
        if not src.crs:
            raise ValueError("GeoTIFF must declare a coordinate system")
        try:
            bands = [src.colorinterp.index(c) + 1 for c in (ColorInterp.red, ColorInterp.green, ColorInterp.blue)]
        except ValueError as e:
            raise ValueError("Expected GeoTIFF bands identified as RGB") from e
        if any(src.dtypes[b - 1] != "uint8" for b in bands):
            raise ValueError("Expected a display-ready 8-bit RGB orthomosaic")
        directory = Path(temp) / "output"
        for subdir in ("images", "previews", "masks", "valid"):
            (directory / subdir).mkdir(parents=True)
        with (directory / "cases.jsonl").open("w", encoding="utf-8") as stream:
            for (geom, prop), fid in zip(fp, ids):
                wgs = reproject(geom, fp_crs, WGS84)
                building = reproject(geom, fp_crs, metric)
                if not building.is_valid or not math.isfinite(building.area) or building.area <= 0:
                    raise ValueError(f"Invalid footprint in scene coordinates: {fid}")
                img, preview, mask, valid, fraction, win = crop_image(src, geom, fp_crs, bands)
                filename = hashlib.sha256(fid.encode("utf-8")).hexdigest()[:24] + ".png"
                for subdir, image in (("images", img), ("previews", preview), ("masks", mask), ("valid", valid)):
                    image.save(directory / subdir / filename)
                record = dict(building_id=fid, scene_id=scene_id, image_path="images/" + filename,
                              preview_path="previews/" + filename, mask_path="masks/" + filename,
                              valid_mask_path="valid/" + filename, tile=scene_id, bbox_lonlat=list(wgs.bounds),
                              geometry=mapping(wgs), footprint_source=prop.get("footprint_source") or Path(footprints).name,
                              coverage_fraction=round(fraction, 6),
                              quality_flag="partial_coverage" if fraction < .98 else "full_coverage",
                              window_pixel_xywh=win,
                              roof_evidence=roof_stats(building, metric_damages, index) if damage else None)
                stream.write(json.dumps(record, ensure_ascii=False, allow_nan=False) + "\n")
        os.rename(directory, output)
    return output / "cases.jsonl"


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--raster", required=True, type=Path)
    p.add_argument("--footprints", required=True, type=Path)
    p.add_argument("--damage", type=Path)
    p.add_argument("--scene-id", required=True)
    p.add_argument("--output", required=True, type=Path)
    args = p.parse_args()
    print(prepare(args.raster, args.footprints, args.damage, args.scene_id, args.output))


if __name__ == "__main__":
    main()
