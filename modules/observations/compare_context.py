"""Paired release check of the linear and adaptive surrounding-color checks."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
from tempfile import TemporaryDirectory

import numpy as np
from PIL import Image
from scipy.ndimage import distance_transform_edt

from check_photometric_context import cases_for, TRUTH
from evidence import measure
from verify_target import indexed


def to_rgb(values):
    return Image.fromarray(np.clip(np.rint(values), 0, 255).astype("uint8"))


def conditions(image, mask):
    for name, post, valid, aligned, count in cases_for(image, mask):
        yield name, post, valid, aligned
    rgb = np.asarray(image, dtype=float)
    m = np.asarray(mask) > 127
    yy, xx = np.indices(m.shape)
    dist = distance_transform_edt(m)
    y, x = np.unravel_index(dist.argmax(), dist.shape)
    rad = min(.80 * dist[y,x], np.sqrt(.09 * m.sum() / np.pi))
    patch = (xx-x)**2 + (yy-y)**2 <= rad**2
    gamma = 255 * (rgb/255)**1.4
    plus = gamma.copy()
    plus[patch] = np.where(plus[patch] < 128, plus[patch]+68, plus[patch]-68)
    zones = rgb + np.where(xx < m.shape[1]//2, -31, 31)[..., None]
    for name, values in (("global_gamma", gamma), ("gamma_plus_patch", plus),
                         ("two_illumination_zones", zones)):
        yield name, to_rgb(values), None, True


def includes(box, xy):
    return bool(box and box[0] <= xy[0] <= box[2] and box[1] <= xy[1] <= box[3])


def run(manifest):
    import photometric_context
    import photometric_context_v2
    methods = {"linear": photometric_context, "adaptive": photometric_context_v2}
    truth = {**TRUTH, "global_gamma": "consistent_with_surroundings",
             "gamma_plus_patch": "local_residual", "two_illumination_zones": "reference_insufficient"}
    groups = {name: {} for name in methods}
    rows = []
    manifests = indexed(manifest)
    if len(manifests) != 8:
        raise ValueError("Expected eight held-out roofs")
    with TemporaryDirectory() as folder:
        root = Path(folder)
        for building, record in manifests.items():
            source = manifest.parent / record["image_path"]
            with Image.open(source) as src, Image.open(manifest.parent/record["mask_path"]) as footprint:
                image, mask = src.convert("RGB"), footprint.convert("L")
            image.save(root/"pre.png")
            mask.save(root/"roof.png")
            dist = distance_transform_edt(np.asarray(mask)>127)
            y, x = np.unravel_index(dist.argmax(), dist.shape)
            center_xy = [float((x+.5)/mask.width), float((y+.5)/mask.height)]
            for kind, after, valid, same in conditions(image, mask):
                after.save(root/"post.png")
                (valid or Image.new("L", mask.size, 255)).save(root/"valid.png")
                case = dict(building_id=building, image_path="post.png", pre_image_path="pre.png",
                            pre_mask_path="roof.png", mask_path="roof.png", valid_mask_path="valid.png",
                            pre_valid_mask_path="valid.png", same_pixel_grid=same,
                            registration_error_px=0.0 if same else None, coverage_fraction=1.,
                            pre_coverage_fraction=1.)
                appearance = measure(case, root)
                if appearance["status"] != "ok":
                    raise ValueError(f"{building}/{kind}: target observation failed")
                info = {"building_id": building, "condition": kind, "expected": truth[kind],
                        "initial_appearance_xyxy": appearance["evidence_region"]["post_xyxy"],
                        "edit_center": center_xy if truth[kind]=="local_residual" else None}
                for name, mod in methods.items():
                    result = mod.assess_case(case, root, appearance["evidence_region"], expected_hashes=appearance)
                    state = result["status"]
                    # The legacy implementation only identified its entire comparison window.
                    area = result.get("residual_xyxy") if name=="adaptive" else result.get("compared_common_xyxy")
                    located = includes(area, center_xy) and state=="local_residual"
                    extra = result.get("footprint_followup") or {}
                    extra_local = extra.get("status")=="local_residual"
                    extra_located = extra_local and includes(extra.get("residual_xyxy"), center_xy)
                    counts = groups[name].setdefault(kind, Counter())
                    counts.update(n=1, correct=int(state==truth[kind]))
                    counts[state] += 1
                    counts["any_reported_local"] += int(state=="local_residual" or extra_local)
                    if truth[kind]=="local_residual":
                        counts["correct_and_located"] += int(located)
                        counts["located_in_either_reported_region"] += int(located or extra_located)
                    info[name] = dict(status=state, reason=result.get("reason"), residual_or_legacy_window=area,
                                      separate_followup_status=extra.get("status"),
                                      separate_followup_xyxy=extra.get("residual_xyxy"),
                                      edit_center_in_output=located if truth[kind]=="local_residual" else None,
                                      edit_center_in_followup=extra_located if truth[kind]=="local_residual" else None)
                rows.append(info)
    g = groups["adaptive"]
    gates = dict(gamma_clear=g["global_gamma"]["consistent_with_surroundings"]>=6,
                 gamma_false=g["global_gamma"]["any_reported_local"]<=1,
                 mixed_localized=g["gamma_plus_patch"]["located_in_either_reported_region"]>=6,
                 reject_split_lighting=g["two_illumination_zones"]["reference_insufficient"]>=7
                                       and g["two_illumination_zones"]["any_reported_local"]<=1)
    digest = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
    return {"source_manifest_sha256": digest(manifest), "model_sha256": {k:digest(Path(v.__file__)) for k,v in methods.items()},
            "groups": groups, "acceptance": gates, "rows": rows}


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cases", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args=parser.parse_args()
    output=run(args.cases)
    with args.output.open("x", encoding="utf8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    print(json.dumps({"groups":output["groups"],"acceptance":output["acceptance"]},indent=1))
