"""Attach an optional, image-verified regional observation beside an existing building grade."""
import argparse
import hashlib
import json
import math
import os
from pathlib import Path
from tempfile import NamedTemporaryFile

from PIL import Image
from blind_review import read, index


PHASES = (("image_path", "image_sha256"), ("mask_path", "mask_sha256"),
          ("pre_image_path", "pre_image_sha256"), ("pre_mask_path", "pre_mask_sha256"))
VALIDITY = (("valid_mask_path","valid_mask_sha256"), ("pre_valid_mask_path","pre_valid_mask_sha256"))


def guard_input_status(quality, case, directory):
    from qguard import load_pixels, validity

    phases = {"post": ""}
    if case.get("pre_image_path"):
        phases["pre"] = "pre_"
    if not isinstance(quality, dict) or not isinstance(quality.get("phases"), dict) or phases.keys() != quality["phases"].keys():
        return "invalid_quality_record"
    for phase, prefix in phases.items():
        recorded = quality["phases"][phase]
        if not isinstance(recorded, dict) or not isinstance(recorded.get("invalid_pixels_sha256"), str):
            return "invalid_quality_record"
        explicit = case.get(prefix + "valid_mask_path")
        target = load_pixels(directory / case[prefix + "mask_path"], "L") >= 128
        invalid, provenance = validity(directory / case[prefix + "image_path"],
                                       directory / explicit if explicit else None, target)
        if (recorded.get("source") != provenance["source"] or
                recorded["invalid_pixels_sha256"] != hashlib.sha256(invalid.tobytes()).hexdigest()):
            return "regional_input_mismatch"
    return None


def region_valid(region, case, directory):
    if not isinstance(region, dict) or region.get("coords") != "normalized_original_image":
        return False
    for xy, mk, im in (("post_xyxy", "mask_path", "image_path"), ("pre_xyxy", "pre_mask_path", "pre_image_path")):
        if not case.get(im):
            if region.get(xy) is not None:
                return False
            continue
        box = region.get(xy)
        if not isinstance(box, list) or len(box) != 4:
            return False
        if not all(type(v) in (int, float) and math.isfinite(v) and 0 <= v <= 1 for v in box):
            return False
        x0, y0, x1, y1 = box
        if x0 >= x1 or y0 >= y1:
            return False
        with Image.open(directory / case[mk]) as mask, Image.open(directory / case[im]) as src:
            if mask.size != src.size:
                return False
            w, h = src.size
            pixels = (round(w*x0), round(h*y0), round(w*x1), round(h*y1))
            if pixels[0] >= pixels[2] or pixels[1] >= pixels[3]:
                return False
            if mask.convert("L").crop(pixels).getextrema()[1] < 128:
                return False
    return True


def attach(cases, grades, candidates, output):
    cases = Path(cases)
    source = index(read(cases), "building_id")
    original = index(read(grades), "building_id")
    captions = index(read(candidates), "building_id")
    if not source or source.keys() != original.keys() or captions.keys() - source.keys():
        raise ValueError("Grade / case ID mismatch, or regional output from another batch")
    if Path(output).exists():
        raise FileExistsError(output)
    Path(output).parent.mkdir(parents=True, exist_ok=True)
    temp_path = None
    counts = {}
    try:
        with NamedTemporaryFile("w", dir=Path(output).parent, encoding="utf-8", delete=False) as dst:
            temp_path = Path(dst.name)
            for bid, case in source.items():
                base, row = original[bid], captions.get(bid, {})
                if "regional_observation" in base:
                    raise ValueError(f"{bid}: expected original grade manifest")
                if not case.get("image_path"):
                    raise ValueError(f"{bid}: missing current image path")
                hashes = {digest: hashlib.sha256((cases.parent / case[field]).read_bytes()).hexdigest()
                          for field, digest in (*PHASES,*VALIDITY) if case.get(field)}
                if any(base.get(field) != hashes.get(field) for field in ("image_sha256", "pre_image_sha256")
                       if base.get("status") != "inference_error" or base.get(field) is not None):
                    raise ValueError(f"{bid}: original grade was produced from different images")
                quality = row.get("quality_guard", {})
                if not row or row.get("status") not in {"ok","quality_limited"}:
                    status = "regional_output_unavailable"
                elif not case.get("mask_path") or bool(case.get("pre_mask_path")) != bool(case.get("pre_image_path")):
                    status = "footprint_unavailable"
                elif any(row.get(digest) != hashes.get(digest) for _, digest in (*PHASES,*VALIDITY)):
                    status = "regional_input_mismatch"
                elif "quality_guard" in row and (guard_status := guard_input_status(quality, case, cases.parent)):
                    status = guard_status
                elif row.get("status") == "quality_limited":
                    status = ("quality_limited" if quality.get("decision")=="withhold" and row.get("change_status")=="uncertain"
                              and row.get("evidence_region") is None and isinstance(row.get("explanation_zh"),str)
                              and row["explanation_zh"].strip() else "invalid_quality_record")
                elif base.get("status") != "ok" or case.get("coverage_fraction", 1) < .98:
                    status = "upstream_review_required"
                elif "quality_guard" in row and quality.get("decision") != "pass":
                    status = "invalid_quality_record"
                elif row.get("change_status") not in ({"changed","stable","uncertain"} if case.get("pre_image_path") else {"single","uncertain"}):
                    status = "invalid_change_status"
                elif not isinstance(row.get("explanation_zh"), str) or not row["explanation_zh"].strip() or not row.get("model"):
                    status = "regional_text_unavailable"
                elif row.get("evidence_region") is not None and not region_valid(row["evidence_region"], case, cases.parent):
                    status = "invalid_region"
                elif row.get("change_status") == "changed" and not row.get("evidence_region"):
                    status = "change_without_region"
                else:
                    status = "available_for_review"
                observation = {"status": status}
                if status == "available_for_review":
                    observation.update({k: row.get(k) for k in ("explanation_zh", "change_status", "evidence_region",
                                       "model", "adapter_sha256", "prompt_sha256", *hashes)})
                if status == "quality_limited":
                    observation.update(explanation_zh=row["explanation_zh"],change_status="uncertain",evidence_region=None)
                if quality and status in {"available_for_review","quality_limited"}:
                    observation["quality_guard"] = quality
                counts[status] = counts.get(status, 0) + 1
                dst.write(json.dumps({**base, "regional_observation": observation}, ensure_ascii=False, allow_nan=False) + "\n")
        os.link(temp_path, output)
    finally:
        if temp_path is not None:
            temp_path.unlink(missing_ok=True)
    return counts


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    for name in ("cases", "grades", "candidates", "output"):
        p.add_argument("--" + name, type=Path, required=True)
    print(json.dumps(attach(**vars(p.parse_args()))))
