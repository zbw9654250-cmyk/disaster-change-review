"""Locate conspicuous surface changes in already co-registered, true-color image pairs."""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage as ndi
from scipy.spatial import cKDTree


SITE = Path(__file__).resolve().parents[1] / "docs" / "assets" / "geology"
PAIRS = {
    "oso": ("oso-pre.png", "oso-post.png"),
    "mud-creek": ("mud-creek-pre.png", "mud-creek-post.png"),
    "la-palma": ("volcano/la-palma-before.png", "volcano/la-palma-after.png"),
}


def color_features(rgb):
    red, green, blue = ndi.gaussian_filter(rgb, (1, 1, 0)).transpose(2, 0, 1)
    return np.stack((.299 * red + .587 * green + .114 * blue, red - green, green - blue), axis=-1)


def color_residual(before, after):
    """Compare each pixel with the usual later appearance of similar starting colors."""
    old = before[::4, ::4].reshape(-1, 3)
    new = after[::4, ::4].reshape(-1, 3)
    tree = cKDTree(old)
    # Bound working memory even for a full-resolution crop.
    result = np.empty(before.shape[:2])
    for y in range(0, before.shape[0], 24):
        block = before[y:y+24]
        _, near = tree.query(block, k=min(40, len(old)))
        expected = np.median(new[near], axis=-2)
        # The original JPEGs differ in illumination; hue carries more weight.
        result[y:y+24] = np.linalg.norm((after[y:y+24] - expected) * [.36, 1, 1], axis=-1)
    return result


def change_scores(a, b):
    before, after = color_features(a), color_features(b)
    old, new = before[..., 0], after[..., 0]
    scale = max(1., min(old.shape) / 48)
    error = color_residual(before, after)
    # Limit the score to the observed difference: identical pixels cannot be changes.
    actual = np.linalg.norm((before - after) * [.36, 1, 1], axis=2)
    error = np.minimum(error, actual)

    red, _, blue = a.transpose(2, 0, 1)
    red2, _, blue2 = b.transpose(2, 0, 1)
    water = (blue - red) / (old + 1) > .61
    coastal = ndi.distance_transform_edt(water) < 3 * scale
    blue_again = (blue2 - red2) / (new + 1) > .42
    haze = (new > old * 1.65) & (blue2 > red2)
    cloud = ((new > 175) & (np.ptp(b, axis=2) < 30)) | ((old > 185) & (np.ptp(a, axis=2) < 30))
    valid = ~(ndi.binary_dilation(cloud, iterations=round(scale)) | (water & (~coastal | blue_again | haze)))
    if not np.any(valid):
        return np.zeros_like(old)

    mean_old = ndi.gaussian_filter(old, scale)
    mean_new = ndi.gaussian_filter(new, scale)
    var_old = np.maximum(0., ndi.gaussian_filter(old**2, scale) - mean_old**2)
    var_new = np.maximum(0., ndi.gaussian_filter(new**2, scale) - mean_new**2)
    cov = ndi.gaussian_filter(old * new, scale) - mean_old * mean_new
    corr = np.clip(cov / np.sqrt(4 + var_old * var_new), 0., 1.)
    # Favor coherent color changes accompanied by a change in local structure.
    reliable = np.clip(np.sqrt(var_old) / 10, .20, 1.)
    # A cap based only on the global percentile can erase a single small change
    # in an otherwise identical pair (the 98th percentile could be exactly zero).
    strength = np.minimum(error, max(32., np.percentile(error[valid], 98)))
    score = ndi.gaussian_filter(strength * valid, scale * .6) * (1 - corr) * reliable
    score[~valid] = 0
    return score


def detect_changes(before_rgb, after_rgb):
    """Return up to two ellipse boxes [left%, top%, width%, height%] on the shared grid.

    Inputs are same-sized HxWx3 RGB arrays in the 0–255 range. These boxes identify
    review areas; they are not damage outlines or estimates of affected area.
    """
    a, b = np.asarray(before_rgb, dtype=float), np.asarray(after_rgb, dtype=float)
    if a.shape != b.shape or a.ndim != 3 or a.shape[-1] != 3 or min(a.shape[:2]) < 16:
        raise ValueError("Expected two aligned RGB images with identical dimensions of at least 16 x 16")
    if not (np.isfinite(a).all() and np.isfinite(b).all() and min(a.min(), b.min()) >= 0 and
            max(a.max(), b.max()) <= 255):
        raise ValueError("RGB values must be finite and between 0 and 255")
    score = change_scores(a, b)
    height, width = score.shape
    positive = score[score > 0]
    if positive.size == 0:
        return []
    # Include unchanged cells when the scene is almost entirely unchanged.
    population = score if np.count_nonzero(score > 3) < .12 * score.size else positive
    low, high = np.maximum(np.percentile(population, [84, 94]), [3., 5.])
    border = np.pad(np.ones_like(score, dtype=bool), 1)
    score *= np.minimum(1., ndi.distance_transform_edt(border)[1:-1, 1:-1] / (min(width, height) * .05))
    connected, _ = ndi.label(ndi.binary_opening(score > low, iterations=max(1, round(min(width, height)*.004))))
    candidates = []
    for index, box in enumerate(ndi.find_objects(connected), start=1):
        ys, xs = box
        values = score[box][connected[box] == index]
        if len(values) < max(12, .0007 * width * height) or values.max() <= high:
            continue
        # At the crop margin a region may be incomplete (cloud edges are common).
        if min(xs.start/width, ys.start/height, 1-xs.stop/width, 1-ys.stop/height) < .035:
            continue
        mass = np.sum(values - low) * min(1., len(values) / (.005 * width * height))
        # A small shared margin keeps the component boundary visible under the stroke.
        padx, pady = (xs.stop - xs.start) * .07, (ys.stop - ys.start) * .07
        x0, x1 = max(0., xs.start - padx), min(width, xs.stop + padx)
        y0, y1 = max(0., ys.start - pady), min(height, ys.stop + pady)
        ring = [100 * x0 / width, 100 * y0 / height,
                100 * (x1-x0) / width, 100 * (y1-y0) / height]
        candidates.append((mass, [round(v, 3) for v in ring]))
    candidates.sort(key=lambda item: item[0], reverse=True)
    return [ring for mass, ring in candidates[:2] if mass >= .25 * candidates[0][0]]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path, help="Classic JavaScript file for the offline gallery")
    args = parser.parse_args()
    records = {}
    for key, names in PAIRS.items():
        paths = [SITE / name for name in names]
        images = []
        for path in paths:
            with Image.open(path) as source:
                images.append(np.asarray(source.convert("RGB")))
        records[key] = {
            "rings": detect_changes(*images),
            "beforeSha256": hashlib.sha256(paths[0].read_bytes()).hexdigest(),
            "afterSha256": hashlib.sha256(paths[1].read_bytes()).hexdigest(),
        }
    args.output.write_bytes(("const GEO_CHANGES = " + json.dumps(records, indent=2) + ";\n").encode("utf-8"))


if __name__ == "__main__":
    main()
