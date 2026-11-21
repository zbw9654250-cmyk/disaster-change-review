"""Apply an optional observation-quality guard to saved footprint-grounded building captions."""
import argparse
from hashlib import sha256
import json
from pathlib import Path
import os
from tempfile import NamedTemporaryFile
import warnings

import numpy as np
from PIL import Image, ImageFilter
import rasterio
from rasterio.enums import MaskFlags
from rasterio.errors import NotGeoreferencedWarning


def edge_bands(rgb, target):
    """Mark near-black lines connected to an outer frame edge; never segment individual dark pixels."""
    dark = np.asarray(Image.fromarray(rgb.max(axis=2)).filter(ImageFilter.MedianFilter(3)))
    # Marked input crops can carry a thin cyan footprint outline and its JPEG colour halo.
    # Exclude only detected cyan along the supplied footprint boundary from frame statistics.
    mask = Image.fromarray(target.astype("uint8") * 255)
    boundary = np.asarray(mask.filter(ImageFilter.MaxFilter(9))) != np.asarray(mask.filter(ImageFilter.MinFilter(9)))
    red, green, blue = rgb.astype("int16").transpose(2, 0, 1)
    marker = boundary & (np.minimum(green, blue) > red + 32) & (np.abs(green - blue) < 70)
    ignored = np.asarray(Image.fromarray(marker.astype("uint8")).filter(ImageFilter.MaxFilter(9))) > 0
    invalid = np.zeros(dark.shape, dtype=bool)
    bands = {}
    for axis, edges in ((0, ("top", "bottom")), (1, ("left", "right"))):
        rows = dark if axis == 0 else dark.T
        eligible = ~ignored if axis == 0 else ~ignored.T
        count = eligible.sum(axis=1)
        flagged = ((count >= .35 * rows.shape[1]) &
                   (((rows > 8) & eligible).sum(axis=1) <= np.rint(.015 * count)) &
                   (((rows <= 3) & eligible).sum(axis=1) > .5 * count))
        for name, from_end in zip(edges, (False, True)):
            sequence = flagged[::-1] if from_end else flagged
            length = int(np.flatnonzero(~sequence)[0]) if (~sequence).any() else len(sequence)
            if length < max(6, np.ceil(.035 * len(sequence))):
                continue
            bands[name] = length
            axis_view = invalid if axis == 0 else invalid.T
            selected = slice(-length, None) if from_end else slice(0, length)
            axis_view[selected] = True
    return invalid, {"bands_px": bands, "outline_excluded_pixels": int(ignored.sum())}


def load_pixels(path, mode):
    with Image.open(path) as image:
        if image.getexif().get(274, 1) != 1:
            raise ValueError(f"Normalize image and masks to the same upright grid before checking {path.name}")
        return np.asarray(image.convert(mode))


def validity(image_path, explicit, target):
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", NotGeoreferencedWarning)
        with rasterio.open(image_path) as source:
            if source.shape != target.shape:
                raise ValueError("Footprint and image dimensions differ")
            if explicit is not None:
                with rasterio.open(explicit) as mask:
                    if mask.count != 1 or mask.shape != source.shape:
                        raise ValueError("Explicit validity mask requires one band on the image grid")
                    if mask.crs and source.crs and (mask.crs != source.crs or not mask.transform.almost_equals(source.transform)):
                        raise ValueError("Image and explicit validity mask grids differ")
                    values = mask.read(1)
                    if values.dtype.kind not in "bu":
                        raise ValueError("Use an unsigned integer valid-data mask; positive pixels denote valid data")
                    invalid = values == 0
                return invalid, {"source": "explicit_valid_mask", "file_sha256": sha256(explicit.read_bytes()).hexdigest()}
            flags = {flag for band in source.mask_flag_enums for flag in band}
            if flags - {MaskFlags.all_valid}:
                invalid = source.dataset_mask() == 0
                return invalid, {"source": "gdal_dataset_mask", "flags": sorted(flag.name for flag in flags)}
    invalid, observation = edge_bands(load_pixels(image_path, "RGB"), target)
    return invalid, {"source": "frame_edge_observation", **observation}


def phase_check(case, candidate, folder, prefix):
    phase = "pre" if prefix else "post"
    image_path = folder / case[prefix + "image_path"]
    footprint_path = folder / case[prefix + "mask_path"]
    for key, path in (("image", image_path), ("mask", footprint_path)):
        if sha256(path.read_bytes()).hexdigest() != candidate.get(prefix + key + "_sha256"):
            raise ValueError(f"{case['building_id']}: {phase} {key} differs from inference input")
    explicit = case.get(prefix + "valid_mask_path")
    target = load_pixels(footprint_path, "L") >= 128
    invalid, provenance = validity(image_path, folder / explicit if explicit else None, target)
    with Image.open(image_path) as img:
        if img.getexif().get(274, 1) != 1:
            raise ValueError("Normalize source EXIF orientation and all masks first")
    if invalid.shape != target.shape or not np.any(target):
        raise ValueError(f"{case['building_id']}: invalid or empty footprint grid")
    problem = invalid & target
    n_target, n_problem = int(target.sum()), int(problem.sum())
    n_region = n_region_problem = 0
    region = candidate.get("evidence_region")
    if region is not None:
        coordinates = region.get(phase + "_xyxy")
        if region.get("coords") != "normalized_original_image" or not isinstance(coordinates, list) or len(coordinates) != 4:
            raise ValueError("Invalid regional coordinate schema")
        x0, y0, x1, y1 = coordinates
        if not (0 <= x0 < x1 <= 1 and 0 <= y0 < y1 <= 1):
            raise ValueError("Regional coordinates are outside the image")
        h, w = target.shape
        area = np.s_[round(y0 * h):round(y1 * h), round(x0 * w):round(x1 * w)]
        n_region = int(target[area].sum())
        if n_region == 0:
            raise ValueError("Evidence window misses footprint")
        n_region_problem = int(problem[area].sum())
    blocked = (n_problem >= 32 and n_problem >= .10 * n_target) or (
        n_region_problem >= 32 and n_region_problem >= .25 * n_region)
    return {**provenance, "invalid_pixels_sha256": sha256(invalid.tobytes()).hexdigest(),
            "target_pixels": n_target, "affected_target_pixels": n_problem,
            "regional_pixels": n_region, "affected_regional_pixels": n_region_problem, "withhold": blocked}


def inspect(case, candidate, folder):
    if "quality_guard" in candidate:
        raise ValueError("A fresh guard requires the original inference candidate")
    paired = bool(case.get("pre_image_path"))
    if paired != bool(case.get("pre_mask_path")) or paired != bool(candidate.get("pre_image_sha256")):
        raise ValueError("Input and candidate phases differ")
    if not paired and (case.get("pre_valid_mask_path") or candidate.get("pre_mask_sha256")):
        raise ValueError("Unexpected earlier mask")
    phases = {"post": phase_check(case, candidate, folder, "")}
    if paired:
        phases["pre"] = phase_check(case, candidate, folder, "pre_")
    blocked = [name for name, data in phases.items() if data["withhold"]]
    guard = {"version": 1, "decision": "withhold" if blocked else "pass", "phases": phases}
    explicit_hashes = {("pre_" if name == "pre" else "") + "valid_mask_sha256": data["file_sha256"]
                       for name, data in phases.items() if data["source"] == "explicit_valid_mask"}
    if not blocked:
        return {**candidate, **explicit_hashes, "quality_guard": guard}
    reasons = []
    for name in blocked:
        phase = ("较早影像" if name == "pre" else "较晚影像") if paired else "本期影像"
        if phases[name]["source"] == "frame_edge_observation":
            reasons.append(phase + "中紧贴画幅边缘的连续近黑带与目标重叠，该处缺少可辨细节")
        else:
            reasons.append(phase + "的有效数据掩膜将部分目标标记为无效，该处无法观察")
    message = "。".join(reasons) + "。请复核原始影像后再判读该栋建筑。"
    keep = ("building_id", "model", "seconds", "image_sha256", "mask_sha256",
            "pre_image_sha256", "pre_mask_sha256", "adapter_sha256", "prompt_sha256")
    return {**{key: candidate[key] for key in keep if key in candidate},
            **explicit_hashes,
            "status": "quality_limited", "change_status": "uncertain", "explanation_zh": message,
            "evidence_region": None, "review_required": True, "quality_guard": guard}


def apply(cases, candidates, output):
    def indexed(path):
        items = [json.loads(line) for line in path.read_text(encoding="utf-8-sig").splitlines() if line.strip()]
        by_id = {item["building_id"]: item for item in items}
        if not by_id or len(by_id) != len(items):
            raise ValueError("Expected nonempty unique building IDs")
        return by_id

    source, predictions = indexed(cases), indexed(candidates)
    if source.keys() != predictions.keys():
        raise ValueError("Cases and candidate IDs differ")
    if output.exists():
        raise FileExistsError(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    counts = {"pass": 0, "withhold": 0}
    with NamedTemporaryFile("w", dir=output.parent, delete=False, encoding="utf8") as stream:
        tmp = Path(stream.name)
        try:
            for key, case in source.items():
                record = inspect(case, predictions[key], cases.parent)
                counts[record["quality_guard"]["decision"]] += 1
                stream.write(json.dumps(record, ensure_ascii=False, allow_nan=False) + "\n")
            stream.close()
            os.link(tmp, output)
        finally:
            stream.close()
            tmp.unlink(missing_ok=True)
    return counts


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    for field in ("cases", "candidates", "output"):
        parser.add_argument("--" + field, type=Path, required=True)
    print(json.dumps(apply(**vars(parser.parse_args()))))
