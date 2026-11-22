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

from detect_geology_changes import contour_changes, detect_changes


ROOT = Path(__file__).resolve().parents[1]
GALLERY = ROOT / "docs" / "assets" / "gallery.js"

# Public xBD building footprints transformed into the two cropped gallery
# images. They let the display show the full damaged building outline instead
# of a small candidate box.
XBD_FOOTPRINTS = {
    "hurricane-michael": [
        [82.032, 63.291], [90.429, 62.279], [90.996, 83.525],
        [82.509, 84.569], [83.125, 96.063], [41.519, 98.425],
        [41.181, 87.022], [38.816, 86.262], [38.309, 65.483],
        [56.434, 63.849], [56.697, 53.036], [57.103, 52.277],
        [81.492, 51.019],
    ],
    "santa-rosa": [
        [41.896, 30.299], [42.753, 31.07], [46.78, 33.383],
        [50.893, 31.712], [54.749, 36.082], [61.004, 42.766],
        [68.116, 42.38], [67.773, 45.979], [68.458, 56.775],
        [68.287, 60.888], [67.43, 61.531], [64.945, 64.23],
        [57.043, 65.872], [56.634, 68.985], [52.435, 70.656],
        [52.178, 72.841], [48.836, 72.97], [47.98, 67.057],
        [43.781, 68.471], [41.296, 54.719], [34.527, 47.521],
    ],
}


def read_gallery() -> list[dict]:
    text = GALLERY.read_text(encoding="utf-8")
    return json.loads(text.removeprefix("const GALLERY = ").removesuffix(";\n"))


def rings_for(before: Path, after: Path) -> list[list[float]]:
    with Image.open(before) as first, Image.open(after) as second:
        a = np.asarray(first.convert("RGB"))
        b = np.asarray(second.convert("RGB"))
    return detect_changes(a, b)


def contours_for(row: dict, before: Path, after: Path) -> tuple[list[list[list[float]]], str]:
    with Image.open(before) as first, Image.open(after) as second:
        a = np.asarray(first.convert("RGB"))
        b = np.asarray(second.convert("RGB"))
    if row["id"] == "la-palma":
        return contour_changes(a, b), "pixel-change-contour-v1"
    footprint = XBD_FOOTPRINTS.get(row["id"])
    if footprint is not None:
        return [footprint], "xbd-footprint-guided-contour-v1"
    return [], ""


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
    contours, contour_method = contours_for(row, before, after)
    if contours:
        ours_method = contour_method
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
            "contours": contours,
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
