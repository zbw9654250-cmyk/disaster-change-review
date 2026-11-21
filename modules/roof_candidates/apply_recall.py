"""Apply the frozen roof pipeline to three sets of scene predictions."""
import argparse
import hashlib
import json
import os
from pathlib import Path
from tempfile import NamedTemporaryFile

HERE = Path(__file__).resolve().parent
import numpy as np
from pyproj import CRS, Transformer
from pyproj.aoi import AreaOfInterest
from pyproj.database import query_utm_crs_info
import shapely
from shapely.geometry import mapping, shape

# The GeoJSON and projection functions come from strong-v1/apply_roof.py.
CLASSES = ("Decking", "Hole")
WGS = CRS.from_epsg(4326)


def is_utm(crs):
    code = crs.to_epsg() or 0
    return 32601 <= code <= 32660 or 32701 <= code <= 32760


def read_source(paths, fallback_crs, field):
    batches = []
    for path in paths:
        doc = json.loads(path.read_text(encoding="utf-8-sig"))
        if not isinstance(doc, dict) or doc.get("type") != "FeatureCollection" or not isinstance(doc.get("features"), list):
            raise ValueError(f"{path}: expected a GeoJSON FeatureCollection")
        declared = doc.get("crs")
        if declared is not None and (not isinstance(declared, dict) or declared.get("type") != "name" or
                                     not isinstance(declared.get("properties"), dict) or not declared["properties"].get("name")):
            raise ValueError(f"{path}: unsupported GeoJSON CRS declaration")
        src = CRS.from_user_input(declared["properties"]["name"]) if declared else fallback_crs
        if not (src.equals(WGS, ignore_axis_order=True) or is_utm(src)):
            raise ValueError(f"{path}: expected WGS84 longitude/latitude or WGS84 UTM")
        objects = {c: [] for c in CLASSES}
        for i, f in enumerate(doc["features"]):
            if not isinstance(f, dict) or f.get("type") != "Feature" or not isinstance(f.get("geometry"), dict) or f["geometry"].get("type") not in ("Polygon", "MultiPolygon"):
                raise ValueError(f"{path}, feature {i}: expected a Polygon or MultiPolygon")
            cls = f["properties"].get(field) if isinstance(f.get("properties"), dict) else None
            if cls not in CLASSES:
                raise ValueError(f"{path}, feature {i}: {field} must be Decking or Hole")
            geom = shapely.force_2d(shape(f["geometry"]))
            coords = shapely.get_coordinates(geom)
            if not len(coords) or not np.isfinite(coords).all():
                raise ValueError(f"{path}, feature {i}: empty or nonfinite geometry")
            if src.is_geographic and (np.abs(coords[:, 0]).max() > 180 or np.abs(coords[:, 1]).max() > 90):
                raise ValueError(f"{path}, feature {i}: coordinates outside WGS84 longitude/latitude bounds")
            objects[cls].append(geom)
        batches.append((src, objects))
    return batches


def reproject(geoms, src, dst):
    if src.equals(dst, ignore_axis_order=True):
        return geoms
    transform = Transformer.from_crs(src, dst, always_xy=True).transform
    return shapely.transform(geoms, transform, interleaved=False)


def choose_utm(batches):
    for src, objects in batches:
        for geoms in objects.values():
            if geoms:
                if is_utm(src):
                    return src
                point = geoms[0].representative_point()
                aoi = AreaOfInterest(point.x, point.y, point.x, point.y)
                choices = query_utm_crs_info(datum_name="WGS 84", area_of_interest=aoi)
                if not choices:
                    raise ValueError("No WGS84 UTM zone covers this scene")
                return CRS.from_epsg(choices[0].code)
    return None


def polygon_parts(geom):
    if geom.geom_type == "Polygon":
        if geom.area > 0:
            yield geom
    elif geom.geom_type in ("GeometryCollection", "MultiPolygon"):
        for part in geom.geoms:
            yield from polygon_parts(part)


def to_metric(batches, metric):
    output = {c: [] for c in CLASSES}
    for src, objects in batches:
        for c, geoms in objects.items():
            if geoms:
                projected = reproject(np.asarray(geoms, dtype=object), src, metric)
                for geom in shapely.make_valid(projected):
                    if geom.geom_type not in ("Polygon", "MultiPolygon"):
                        geom = shapely.union_all(list(polygon_parts(geom)))
                    if geom.is_empty or not np.isfinite(geom.area) or geom.area <= 0:
                        raise ValueError("A feature has no polygon area in the scene UTM CRS")
                    output[c].append(geom)
    return {c: np.asarray(values, dtype=object) for c, values in output.items()}


def geojson(objects, metric):
    features = []
    for cls, geoms in objects.items():
        if len(geoms):
            wgs84 = shapely.orient_polygons(reproject(geoms, metric, WGS))
            features.extend({"type": "Feature", "properties": {"cls": cls}, "geometry": mapping(g)}
                            for g in wgs84)
    return json.dumps({"type": "FeatureCollection", "features": features}, allow_nan=False) + "\n"


def run(args):
    from pipeline import infer

    model_path = HERE / "pipeline_policy.json"
    sources = {name: getattr(args, name) for name in ("strong", "same", "dual")}
    destination = args.output.resolve()
    for path in [model_path, *(p for group in sources.values() for p in group)]:
        if destination == path.resolve() or (destination.exists() and destination.samefile(path)):
            raise ValueError("Output must be distinct from all input files and the policy")
    fallback = CRS.from_user_input(args.input_crs)
    batches = {v: read_source(paths, fallback, args.class_field) for v, paths in sources.items()}
    metric = CRS.from_user_input(args.work_crs) if args.work_crs else choose_utm(
        batch for group in batches.values() for batch in group)
    if metric is not None and not is_utm(metric):
        raise ValueError("Working CRS must be a WGS84 UTM zone")
    layers = {v: to_metric(group, metric) for v, group in batches.items()}
    policy = model_path.read_bytes()
    predicted = infer(layers, json.loads(policy))[args.mode]
    content = geojson(predicted, metric)
    status = dict(mode=args.mode, working_crs=metric.to_string() if metric else None,
                  policy_sha256=hashlib.sha256(policy).hexdigest(),
                  inputs={v: {c: len(layer[c]) for c in CLASSES} for v, layer in layers.items()},
                  objects={c: len(predicted[c]) for c in CLASSES},
                  total=sum(len(predicted[c]) for c in CLASSES))
    temporary_path = None
    try:
        with NamedTemporaryFile(mode="w", encoding="utf-8", dir=destination.parent, delete=False) as tmp:
            temporary_path = Path(tmp.name)
            tmp.write(content)
        os.replace(temporary_path, destination)
    finally:
        if temporary_path:
            temporary_path.unlink(missing_ok=True)
    return status


def main():
    cli = argparse.ArgumentParser(description=__doc__)
    for name in ("strong", "same", "dual"):
        cli.add_argument("--" + name, type=Path, required=True, nargs="+", metavar="GEOJSON")
    cli.add_argument("--mode", choices=("main", "equal_budget", "low_fp"), default="main")
    cli.add_argument("--class-field", default="cls", help="Common input class property")
    cli.add_argument("--input-crs", default="EPSG:4326", help="CRS for files without an explicit declaration")
    cli.add_argument("--work-crs", help="Explicit WGS84 UTM projection for this scene")
    cli.add_argument("--output", type=Path, required=True, help="WGS84 GeoJSON destination")
    try:
        result = run(cli.parse_args())
    except (OSError, ValueError) as exc:
        cli.exit(2, f"{exc}\n")
    print(json.dumps(result))


if __name__ == "__main__":
    main()
