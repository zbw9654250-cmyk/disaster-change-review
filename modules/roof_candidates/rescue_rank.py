"""Rank auxiliary roof damage outlines with the published frozen coefficients."""
import numpy as np
import shapely
from scipy.special import expit
from rescue import CLASSES, overlaps

FEATURES = ["hole", "dual", "log_area", "area_below_1m2", "solidity", "compactness",
            "peer_iou", "strong_iou", "strong_iou_above_035", "intersects_strong",
            "log_strong_area_ratio", "other_class_iou", "log_local_strong_count"]


def describe(strong, same, dual, c):
    s, d, base = (np.asarray(x[c], dtype=object) for x in (same, dual, strong))
    geom = np.r_[s, d]
    area = shapely.area(geom)
    hull = shapely.area(shapely.convex_hull(geom))
    length = shapely.length(geom)
    log_area = np.log(np.maximum(area, 1e-6))
    pair = overlaps(s, d)
    peer = np.r_[pair.max(axis=1, initial=0), pair.max(axis=0, initial=0)]
    main = overlaps(geom, base)
    best = main.max(axis=1, initial=0)
    ratio = np.zeros(len(geom))
    if len(base):
        ratio = np.where(best > 0, log_area - np.log(np.maximum(shapely.area(base[main.argmax(axis=1)]), 1e-6)), 0.)
    other = next(k for k in CLASSES if k != c)
    near, _ = shapely.STRtree(base).query(geom, predicate="dwithin", distance=5.0)
    n_near = np.bincount(near, minlength=len(geom))
    x = np.column_stack((np.full(len(geom), c=="Hole"), np.r_[np.zeros(len(s)), np.ones(len(d))],
                         np.clip(log_area, -8, 7), np.clip(-log_area, 0, 8),
                         np.divide(area, hull, where=hull>0, out=np.zeros_like(area)),
                         np.divide(4*np.pi*area, length**2, where=length>0, out=np.zeros_like(area)),
                         peer, best, np.maximum(0, best-0.35), best>0, np.clip(ratio,-6,6),
                         overlaps(geom, strong[other]).max(axis=1, initial=0), np.log1p(n_near)))
    # Very similar same-class baseline polygons provide negligible additional coverage.
    eligible = (area > 0) & (best < 0.80)
    return geom[eligible], x[eligible]


def rank_data(data, config, floor):
    if config["features"] != FEATURES:
        raise ValueError("Ranking feature schema differs")
    output = []
    for c, (g, x) in data.items():
        weights = np.asarray(config["weights"])
        logits = weights[0] + ((x-config["center"])/config["scale"]) @ weights[1:]
        probs = expit(logits)
        keep = []
        suppressed = set()
        tree = shapely.STRtree(g)
        for i in np.argsort(-probs,kind="stable"):
            if probs[i] < floor:
                break
            if i in suppressed:
                continue
            keep.append(i)
            neighbors = tree.query(g[i],predicate="intersects")
            ious = overlaps(g[i:i+1],g[neighbors])[0]
            suppressed.update(neighbors[ious>=0.4].tolist())
        output.extend((c,g[i],float(probs[i])) for i in keep)
    return sorted(output,key=lambda row: -row[2])


def ranked_from_layers(strong, same, dual, config, floor):
    """Return (category, original auxiliary geometry, probability) across both classes."""
    data = {c:describe(strong,same,dual,c) for c in CLASSES}
    return rank_data(data,config, config["floor"] if floor is None else floor)
