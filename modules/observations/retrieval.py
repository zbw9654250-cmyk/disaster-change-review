"""Footprint-masked, image-to-image case search. Inference reads only the training index."""
from functools import lru_cache
import hashlib
import json
import math
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter

DEFAULT_INDEX = Path(__file__).resolve().parent / "library" / "index.json"
METHOD = "roof-case-grid-v1"
SCORE_MIN = 0.47
GEO_MARGIN = 0.0005
GRID = 48
NAMES = ["左上", "上中", "右上", "左中", "中央", "右中", "左下", "下中", "右下"]
SLICES = [np.s_[y:y+16, x:x+16] for y in (0, 16, 32) for x in (0, 16, 32)]


def digest(data):
    return hashlib.sha256(data).hexdigest()


def image_hash(im):
    info = f"{im.mode}:{im.width}x{im.height}\n".encode()
    return digest(info + im.tobytes())


def as_mask(image, size):
    arr = np.asarray(image)
    if arr.ndim != 2 or (arr.shape[1], arr.shape[0]) != size:
        raise ValueError("Expected one mask channel with the same dimensions as post")
    return Image.fromarray((arr > 0).astype("uint8") * 255)


def describe(pre, post, mask, roi=None):
    """Grid of normalized RGB, texture, orientation, geometry and registered-coordinate temporal differences."""
    post = post.convert("RGB")
    if pre is not None:
        pre = pre.convert("RGB")
        if pre.size != post.size:
            raise ValueError("pre and post must use the same pixel grid")
    mask = as_mask(mask, post.size)
    box = mask.getbbox()
    if not box or min(box[2]-box[0], box[3]-box[1]) < 4:
        raise ValueError("Empty or unresolved building footprint")
    shape = np.array(mask.crop(box).resize((GRID, GRID), Image.Resampling.NEAREST)) != 0
    # The one-cell inner rim keeps interpolation of the background out of the statistics.
    interior = np.pad(shape, 1)
    valid = np.logical_and.reduce([interior[y:y+GRID, x:x+GRID] for x in range(3) for y in range(3)])
    if valid.sum() < 32:
        raise ValueError("Insufficient interior support")
    binary_roi = None
    if roi is None:
        focus = valid
    else:
        if np.shape(roi) == (4,):
            left, top, right, bottom = map(float, roi)
            if not (0 <= left < right <= post.width and 0 <= top < bottom <= post.height):
                raise ValueError("ROI must be a nonempty xyxy box in image coordinates")
            binary_roi = Image.new("L", post.size)
            binary_roi.paste(255, (int(left), int(top), math.ceil(right), math.ceil(bottom)))
        else:
            binary_roi = as_mask(roi, post.size)
        small = binary_roi.crop(box).resize((GRID, GRID), Image.Resampling.NEAREST)
        focus = valid & (np.array(small) > 0)
        if focus.sum() < 6:
            raise ValueError("Insufficient ROI footprint overlap")

    def canonical(im):
        # Weighted resampling: off-target RGB is zeroed before interpolation. Divide by
        # the interpolated alpha so a changed exterior cannot contaminate roof cells.
        cut = im.crop(box)
        m = mask.crop(box)
        rgb = Image.composite(cut, Image.new("RGB", cut.size), m)
        reduced = np.asarray(rgb.resize((GRID, GRID), Image.Resampling.BILINEAR), dtype=float)
        alpha = np.asarray(m.resize((GRID, GRID), Image.Resampling.BILINEAR), dtype=float)
        return np.clip(reduced / np.maximum(alpha[..., None], 1), 0, 1)

    imgs = [canonical(post)] if pre is None else [canonical(pre), canonical(post)]
    def gradients(i):
        lum = i @ np.array([.299, .587, .114])
        gy, gx = np.gradient(lum)
        return lum, np.abs(gx), np.abs(gy)

    fields = [gradients(im) for im in imgs]
    if pre is not None:
        delta = imgs[1] - imgs[0]
        offset = np.median(delta[valid], axis=0)
        abs_diff = np.abs(delta).mean(axis=2)
        residual = np.abs(delta-offset).mean(axis=2)
        near = np.mean(abs_diff[valid]) < .018 and np.quantile(abs_diff[valid], .9) < .038
        mode = "near_identity" if near else "compared"
    else:
        mode = "post_only"

    def block(sl):
        m = valid[sl]
        if m.sum() < 4:
            return None
        out = []
        for im, (lum, gx, gy) in zip(imgs, fields):
            vals = lum[sl][m]
            out += np.mean(im[sl][m], axis=0).tolist()
            out += [float(np.std(vals)), float(gx[sl][m].mean()), float(gy[sl][m].mean())]
        if pre is not None:
            out += np.mean(delta[sl][m], axis=0).tolist()
            out += [float(np.quantile(abs_diff[sl][m], .8)), float(np.quantile(residual[sl][m], .8))]
        return np.round(out, 5).tolist()

    extent = min(4., max(-4., math.log2((box[2]-box[0])/(box[3]-box[1]))))
    geometry = [extent] + [float(np.mean(shape[sl])) for sl in SLICES]
    count = np.array([int(focus[s].sum()) for s in SLICES])
    features = {"phase": mode, "geometry": np.round(geometry, 5).tolist(),
                "global": block(np.s_[:, :]), "cells": [block(s) for s in SLICES]}
    audit = {"pre_pixel_sha256": None if pre is None else image_hash(pre), "post_pixel_sha256": image_hash(post),
             "mask_pixel_sha256": image_hash(mask), "footprint_xyxy": list(box),
             "roi_pixel_sha256": image_hash(binary_roi) if binary_roi is not None else None,
             "roi_xyxy": list(binary_roi.getbbox()) if binary_roi is not None else list(box),
             "region": NAMES[int(np.argmax(count))] if roi is not None else "全目标",
             "cell_counts": count.tolist(), "phase": mode}
    return features, audit


def similarity(a, b, counts):
    paired = a["phase"] != "post_only"
    # Scale each field by a predeclared absolute difference on [0,1] RGB data.
    scales = [.24, .24, .24, .10, .055, .055]
    def distance(x, y):
        diff = np.abs(np.asarray(x)-np.asarray(y))
        appearance = np.mean(diff[:12 if paired else 6] / (scales * (2 if paired else 1)))
        if not paired:
            return float(appearance)
        temporal = np.mean(diff[12:] / [.18, .18, .18, .18, .15])
        return float(.52*appearance + .48*temporal)

    global_dist = distance(a["global"], b["global"])
    dists, weights = [], []
    for ca, cb, weight in zip(a["cells"], b["cells"], counts):
        if weight and ca is not None and cb is not None:
            weights.append(weight)
            dists.append(distance(ca, cb))
    overlap = sum(weights) / sum(counts)
    if overlap < .60:
        return None
    local = float(np.average(dists, weights=weights))
    geom = np.abs(np.asarray(a["geometry"])-np.asarray(b["geometry"]))
    shape = .45*geom[0]/1.5 + .55*geom[1:].mean()/.35
    d = .30*global_dist + .50*local + .20*shape + .2*(1-overlap)
    return (float(math.exp(-d)), {"global_distance":round(global_dist,5), "local_distance":round(local,5),
                                  "geometry_distance":round(float(shape),5), "roi_grid_overlap":round(overlap,5)})


def checked_box(box):
    try:
        west, south, east, north = map(float, box)
        if -180 <= west < east <= 180 and -90 <= south < north <= 90:
            return (west, south, east, north)
    except (ValueError, TypeError):
        pass
    return None


def excluded(meta, row):
    if (meta.get("uid") and meta["uid"] == row["uid"]) or meta.get("building_id") == row["parent_id"]:
        return "same_building"
    if meta["tile"] == row["tile"]:
        return "same_tile"
    a, b = meta["bbox_lonlat"], row["bbox_lonlat"]
    if a[0] <= b[2]+GEO_MARGIN and b[0] <= a[2]+GEO_MARGIN and a[1] <= b[3]+GEO_MARGIN and b[1] <= a[3]+GEO_MARGIN:
        return "geographic_neighbor"
    return None


@lru_cache(maxsize=4)
def _load(path, mtime_ns, size):
    data = Path(path).read_bytes()
    idx = json.loads(data)
    if idx["method"] != METHOD or idx["split"] != "train":
        raise ValueError("Incompatible case index")
    return idx, digest(data)


def retrieve(pre, post, mask, roi=None, exclude=None, *, top_k=1, library_path=None):
    """Pass uid or parent building_id, tile and bbox_lonlat for fail-closed exclusion.
    Results include provenance for auditing. Only context_zh is intended for the model.
    """
    if not isinstance(top_k, int) or top_k < 0:
        raise ValueError("top_k must be a nonnegative integer")
    path = Path(library_path or DEFAULT_INDEX)
    stat = path.stat()
    idx, index_hash = _load(str(path.resolve()), stat.st_mtime_ns, stat.st_size)
    result = {"method":METHOD, "index_sha256":index_hash, "min_score":SCORE_MIN,
              "matches":[], "context_zh":"", "reason":"", "filtered":{}}
    meta = dict(exclude or {})
    meta["bbox_lonlat"] = checked_box(meta.get("bbox_lonlat"))
    if not meta.get("tile") or not (meta.get("uid") or meta.get("building_id")) or not meta["bbox_lonlat"]:
        result["reason"] = "missing_exclusion_metadata"
        return result
    if not idx["cases"] or not top_k:
        result["reason"] = "empty_library" if not idx["cases"] else "disabled"
        return result
    try:
        q, audit = describe(pre, post, mask, roi)
    except ValueError as e:
        result.update(reason="invalid_query", detail=str(e))
        return result
    result["query"] = audit
    choices = []
    for row in idx["cases"]:
        veto = excluded(meta, row)
        if not veto and q["phase"] != row["features"]["phase"]:
            veto = "phase_mismatch"
        if not veto:
            rank = similarity(q, row["features"], audit["cell_counts"])
            if rank is None:
                veto = "insufficient_roi_overlap"
            elif rank[0] < SCORE_MIN:
                veto = "below_threshold"
        if veto:
            result["filtered"][veto] = result["filtered"].get(veto, 0)+1
        else:
            choices.append((rank[0], row, rank[1]))
    seen = set()
    for score, row, details in sorted(choices, key=lambda t:(-t[0], t[1]["case_id"])):
        if row["uid"] in seen:
            continue
        case = {k:v for k,v in row.items() if k != "features"}
        case.update(score=round(score, 6), distances=details, region=audit["region"])
        result["matches"].append(case)
        seen.add(row["uid"])
        if len(seen) == top_k:
            break
    if result["matches"]:
        result["reason"] = "matched"
        sentences = [r["caption_zh"] for r in result["matches"]]
        result["context_zh"] = ("以下是其他训练建筑的整栋读图笔记，供选择核对线索。"
            "笔记中的方位、颜色和变化都属于参考建筑。请逐项查看本栋选区，只写本栋图中能独立辨认的现象。\n"
            + "\n".join("参考笔记："+s for s in sentences))
    else:
        result["reason"] = "no_eligible_match"
    return result
