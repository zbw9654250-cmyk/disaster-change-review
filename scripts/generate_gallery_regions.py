"""Generate the two post-disaster region sets used by the offline gallery.

The baseline keeps only the highest-scoring connected region. The model view
keeps the detector's bounded multi-candidate result, with an optional
deterministic review subset for the two building examples. Both views use the
same post-disaster pixels, so the gallery compares localization rather than
crops.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
from PIL import Image

from detect_geology_changes import detect_changes


ROOT = Path(__file__).resolve().parents[1]
GALLERY = ROOT / "docs" / "assets" / "gallery.js"


def read_gallery() -> list[dict]:
    text = GALLERY.read_text(encoding="utf-8")
    return json.loads(text.removeprefix("const GALLERY = ").removesuffix(";\n"))


def rings_for(before: Path, after: Path) -> list[list[float]]:
    with Image.open(before) as first, Image.open(after) as second:
        a = np.asarray(first.convert("RGB"))
        b = np.asarray(second.convert("RGB"))
    return detect_changes(a, b)


def record_for(row: dict) -> dict:
    before = ROOT / "docs" / "assets" / row["before"]["file"]
    after = ROOT / "docs" / "assets" / row["after"]["file"]
    rings = rings_for(before, after)
    if not rings:
        raise ValueError(f"No generated region for {row['id']}")
    indices = row.get("oursCandidateIndices")
    if indices is None:
        ours_rings = rings
        ours_method = "multi-candidate-v1"
    else:
        if not indices or any(not isinstance(index, int) or index < 0 or index >= len(rings)
                              for index in indices):
            raise ValueError(f"Invalid reviewed candidate indices for {row['id']}")
        ours_rings = [rings[index] for index in indices]
        ours_method = "reviewed-candidate-subset-v1"
    return {
        "beforeSha256": hashlib.sha256(before.read_bytes()).hexdigest(),
        "afterSha256": hashlib.sha256(after.read_bytes()).hexdigest(),
        "baseline": {
            "method": "single-candidate-v1",
            "rings": rings[:1],
        },
        "ours": {
            "method": ours_method,
            "rings": ours_rings,
        },
    }


def generate(output: Path) -> None:
    records = {row["id"]: record_for(row) for row in read_gallery()}
    output.write_text(
        "const CHANGE_REGIONS = "
        + json.dumps(records, ensure_ascii=False, indent=2)
        + ";\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path,
                        default=ROOT / "docs" / "assets" / "change_regions.js")
    args = parser.parse_args()
    generate(args.output)
