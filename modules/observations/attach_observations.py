"""Attach v5 observations to original building grades, retaining both independent quality decisions."""
import argparse
import json
import math
from pathlib import Path
from tempfile import TemporaryDirectory

from evidence import measure
from verify_target import indexed, save

from attach_regions import attach
import qguard


def checked_candidate(case, row, folder):
    if row.get("status") not in {"ok", "quality_limited"}:
        return row
    checked = qguard.inspect(case, row, folder)
    for prefix in ("", "pre_"):
        field = prefix + "valid_mask_sha256"
        mask_supplied = bool(case.get(prefix + "valid_mask_path"))
        recorded = row.get(field)
        if row["status"] == "ok" or recorded is not None:
            if bool(recorded) != mask_supplied or recorded != checked.get(field):
                raise ValueError(f"{case['building_id']}: source validity mask differs from inference input")
    guard = checked["quality_guard"]
    guard["pixel_decision"] = guard["decision"]
    coverage = [float(case.get(key, 1.0)) for key in ("coverage_fraction", "pre_coverage_fraction")]
    if any(not math.isfinite(v) or v < 0 or v > 1 for v in coverage):
        raise ValueError(f"{case['building_id']}: invalid coverage fraction")
    if row["status"] != "quality_limited" and min(coverage) >= 0.98:
        return checked

    # Even when the full footprint passes, a small crop or its two-date overlap can be unusable.
    # Run v5 again so a free-text model reply cannot be published as a measurement-quality reason.
    repeated = measure(case, folder)
    guard["measurement_decision"] = "withhold"
    guard["measurement_reproduced"] = repeated["status"] == "quality_limited"
    guard["decision"] = "withhold"
    if guard["pixel_decision"] == "pass":
        reason = (repeated["explanation_zh"] if guard["measurement_reproduced"]
                  else "区域候选未通过质量检查，需要复核原始选区。")
        checked.update(status="quality_limited", change_status="uncertain", evidence_region=None,
                       explanation_zh=reason, review_required=True)
    return checked


def attach_observations(cases, grades, candidates, output):
    cases, grades, candidates, output = map(Path, (cases, grades, candidates, output))
    source, predictions = indexed(cases), indexed(candidates)
    if predictions.keys() - source.keys():
        raise ValueError("Candidate contains an unknown building ID")
    if output.exists():
        raise FileExistsError(output)
    with TemporaryDirectory() as temporary:
        checked = Path(temporary) / "checked.jsonl"
        save(checked, (checked_candidate(source[k], row, cases.parent) for k, row in predictions.items()))
        return attach(cases, grades, checked, output)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    for key in ("cases", "grades", "candidates", "output"):
        parser.add_argument("--" + key, type=Path, required=True)
    print(json.dumps(attach_observations(**vars(parser.parse_args()))))
