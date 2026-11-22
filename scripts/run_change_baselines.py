"""Run one of the three change-localization baselines on an aligned RGB pair.

The RGB baseline runs with the repository's CPU-only detector. FC-Siam-Diff and
BIT are optional Open-CD models. They are loaded only when the optional
``opencd-lite`` package and a compatible checkpoint are supplied.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib
import json
import time
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw
from skimage import measure

from detect_geology_changes import detect_changes


MODEL_NAMES = {
    "rgb": "RGB-rule-v1",
    "fc_siam_diff": "FC-Siam-Diff",
    "bit": "BIT",
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_pair(before_path: Path, after_path: Path) -> tuple[np.ndarray, np.ndarray]:
    with Image.open(before_path) as before_image, Image.open(after_path) as after_image:
        before = np.asarray(before_image.convert("RGB"))
        after = np.asarray(after_image.convert("RGB"))
    if before.shape != after.shape:
        raise ValueError("before and after images must have the same dimensions")
    return before, after


def rasterize_rings(rings: list[list[float]], shape: tuple[int, int]) -> np.ndarray:
    height, width = shape
    mask = Image.new("L", (width, height), 0)
    draw = ImageDraw.Draw(mask)
    for left, top, box_width, box_height, *angle in rings:
        x0, y0 = left * width / 100, top * height / 100
        x1, y1 = (left + box_width) * width / 100, (top + box_height) * height / 100
        # The RGB baseline publishes ellipse candidates. Drawing the envelope
        # keeps the common output contract honest without implying a pixel mask.
        draw.ellipse((x0, y0, x1, y1), fill=255)
    return (np.asarray(mask, dtype=np.uint8) > 0).astype(np.uint8)


def contours_from_mask(mask: np.ndarray) -> list[list[list[float]]]:
    height, width = mask.shape
    contours = []
    for path in measure.find_contours(mask.astype(float), 0.5):
        if len(path) < 4:
            continue
        points = [[round(100 * float(column) / width, 3),
                   round(100 * float(row) / height, 3)]
                  for row, column in path]
        contours.append(points)
    contours.sort(key=len, reverse=True)
    return contours


def run_opencd(model_name: str, before: np.ndarray, after: np.ndarray,
               checkpoint: Path, device: str) -> np.ndarray:
    """Run the optional opencd-lite adapter.

    The adapter is intentionally isolated from the CPU path. This repository
    does not vendor model code or weights, and the exact package API is checked
    at runtime so a missing optional dependency produces an actionable error.
    """
    try:
        module = importlib.import_module("opencd_lite")
    except ImportError as exc:
        raise RuntimeError(
            "FC-Siam-Diff/BIT require the optional opencd-lite package. "
            "Install it with `pip install \"opencd-lite[torch]\"`."
        ) from exc
    builder = getattr(module, "build_model", None)
    if builder is None:
        raise RuntimeError("The installed opencd-lite package does not expose build_model")
    model = builder(model_name, checkpoint=str(checkpoint), device=device)
    prediction = model.predict(before, after)
    if hasattr(prediction, "detach"):
        prediction = prediction.detach().cpu().numpy()
    prediction = np.asarray(prediction)
    if prediction.ndim == 4:
        prediction = prediction[0]
    if prediction.ndim == 3:
        if prediction.shape[0] in (1, 2):
            prediction = prediction[min(1, prediction.shape[0] - 1)]
        elif prediction.shape[-1] in (1, 2):
            prediction = prediction[..., min(1, prediction.shape[-1] - 1)]
        else:
            prediction = prediction[0]
    if prediction.ndim != 2:
        raise RuntimeError(f"Unexpected model output shape: {prediction.shape}")
    if prediction.shape != before.shape[:2]:
        resized = Image.fromarray(prediction.astype(np.float32), mode="F")
        prediction = np.asarray(resized.resize((before.shape[1], before.shape[0]), Image.Resampling.BILINEAR))
    return (prediction >= 0.5).astype(np.uint8)


def write_outputs(output: Path, model: str, before_path: Path, after_path: Path,
                  before: np.ndarray, after: np.ndarray, mask: np.ndarray,
                  latency_ms: float, checkpoint: Path | None) -> None:
    output.mkdir(parents=True, exist_ok=True)
    Image.fromarray(mask * 255).save(output / "mask.png")
    overlay = Image.fromarray(after.copy())
    draw = ImageDraw.Draw(overlay)
    for contour in contours_from_mask(mask):
        points = [(x * after.shape[1] / 100, y * after.shape[0] / 100) for x, y in contour]
        draw.line(points + [points[0]], fill=(32, 165, 138), width=max(1, after.shape[1] // 240), joint="curve")
    overlay.save(output / "overlay.png")
    features = []
    for contour in contours_from_mask(mask):
        if len(contour) < 4:
            continue
        features.append({
            "type": "Feature",
            "properties": {
                "model": MODEL_NAMES[model],
                "coordinate_space": "image_percent",
            },
            "geometry": {"type": "Polygon", "coordinates": [[
                [x, y] for x, y in contour + [contour[0]]
            ]]},
        })
    (output / "regions.geojson").write_text(json.dumps({
        "type": "FeatureCollection",
        "features": features,
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    metrics = {
        "model": MODEL_NAMES[model],
        "input": {
            "before": str(before_path),
            "after": str(after_path),
            "before_sha256": sha256(before_path),
            "after_sha256": sha256(after_path),
            "shape": [int(v) for v in before.shape],
        },
        "output": {
            "mask_pixels": int(mask.sum()),
            "mask_fraction": round(float(mask.mean()), 6),
            "contour_count": len(contours_from_mask(mask)),
        },
        "latency_ms": round(latency_ms, 3),
        "checkpoint": str(checkpoint) if checkpoint else None,
        "metrics_note": "No damage-mask ground truth is inferred from xBD footprints.",
    }
    (output / "metrics.json").write_text(json.dumps(metrics, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", choices=MODEL_NAMES, default="rgb")
    parser.add_argument("--before", required=True, type=Path)
    parser.add_argument("--after", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--checkpoint", type=Path,
                        help="Required for fc_siam_diff and bit")
    parser.add_argument("--device", default="auto", help="opencd-lite device, for example cuda or cpu")
    args = parser.parse_args()
    before, after = read_pair(args.before, args.after)
    started = time.perf_counter()
    if args.model == "rgb":
        mask = rasterize_rings(detect_changes(before, after), before.shape[:2])
    else:
        if args.checkpoint is None:
            parser.error("--checkpoint is required for fc_siam_diff and bit")
        mask = run_opencd(args.model, before, after, args.checkpoint, args.device)
    latency_ms = (time.perf_counter() - started) * 1000
    write_outputs(args.output, args.model, args.before, args.after, before, after, mask, latency_ms, args.checkpoint)
    print(json.dumps({"model": MODEL_NAMES[args.model], "output": str(args.output),
                      "latency_ms": round(latency_ms, 3)}, ensure_ascii=False))


if __name__ == "__main__":
    main()

