"""Produce one local appearance observation per building and retain the source of each claim."""
import argparse
import hashlib
import json
import math
from pathlib import Path
from time import monotonic
from evidence import measure
from explain_roof import run as verify
from verify_target import indexed, model_on, save


def inspect_case(case, folder, verifier=None, photometric_context=False, *, context_version="linear"):
    """Generate an observation. Older experiment callers replay the linear context check."""
    start = monotonic()
    if verifier is None:
        row = measure(case, folder)
        row["render_mode"] = "target_measurement" if row["status"] == "ok" else row["status"]
    else:
        model, processor, index_path, cards = verifier
        row = verify(case, folder, model, processor, cards, index_path)
    row["observation_scope"] = "visible_appearance_in_selected_footprint_window"
    row["change_status_basis"] = "registered_target_measurements"
    if photometric_context:
        if context_version == "adaptive":
            from photometric_context_v2 import assess_case
        elif context_version == "linear":
            from photometric_context import assess_case
        else:
            raise ValueError(f"Unknown context version: {context_version}")
        if row["status"] == "ok":
            row["photometric_context"] = assess_case(case, folder, row["evidence_region"],
                                                     expected_hashes=row)
        else:
            row["photometric_context"] = {"status": "reference_insufficient",
                                          "reason": "target_observation_unavailable"}
        row["photometric_context"]["method"] = context_version
        row["total_seconds_with_context"] = round(monotonic() - start, 4)
    return row


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cases", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True, help="New JSONL output file")
    parser.add_argument("--mode", choices=("measure", "verify"), default="measure")
    parser.add_argument("--model", type=Path, help="Local Qwen3-VL-4B-Instruct weights")
    parser.add_argument("--library", type=Path, help="Case bank index.json")
    parser.add_argument("--cards", type=Path, help="Matching grounded_cases.json")
    parser.add_argument("--photometric-context", action="store_true",
                        help="Compare the observed window with co-registered surroundings")
    args = parser.parse_args()
    if args.output.exists():
        parser.error("Output already exists")
    cases = indexed(args.cases)
    for building, case in cases.items():
        if not isinstance(building, str) or not building.strip():
            parser.error("Each building requires a nonempty string ID")
        if bool(case.get("pre_mask_path")) != bool(case.get("pre_image_path")):
            parser.error(f"{building}: provide the pre image and footprint together")
        for field in ("pre_coverage_fraction", "coverage_fraction"):
            if field in case:
                value = case[field]
                if not isinstance(value, (float, int)) or not math.isfinite(value) or not 0 <= value <= 1:
                    parser.error(f"{building}: invalid {field}")
    verifier = None
    if args.mode == "verify":
        if not (args.model and args.library and args.cards):
            parser.error("verify requires --model, --library and --cards")
        cards = json.loads(args.cards.read_bytes())
        if hashlib.sha256(args.library.read_bytes()).hexdigest() != cards["index_sha256"]:
            parser.error("Case cards do not match this retrieval index")
        model, processor = model_on(args.model)
        verifier = (model, processor, args.library, cards)
    elif args.model or args.library or args.cards:
        parser.error("Use --mode verify with model or case bank arguments")
    rows = (inspect_case(case, args.cases.parent, verifier, args.photometric_context,
                         context_version="adaptive")
            for case in cases.values())
    save(args.output, rows)


if __name__ == "__main__":
    main()
