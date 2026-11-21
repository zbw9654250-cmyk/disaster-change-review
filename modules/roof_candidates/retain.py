"""Filter strong predictions in projected metres. Input is keyed by strong/same/dual."""

import numpy as np
import shapely

CLASSES = ("Decking", "Hole")



def best_iou(left, right):
    left, right = (np.asarray(layer, dtype=object) for layer in (left, right))
    i, j = shapely.STRtree(right).query(left, predicate="intersects")
    shared = shapely.area(shapely.intersection(left[i], right[j]))
    union = shapely.area(left[i]) + shapely.area(right[j]) - shared
    iou = np.divide(shared, union, out=np.zeros_like(shared), where=union > 0)
    best = np.zeros(len(left))
    np.maximum.at(best, i, iou)
    return best


def features(pred_dicts, category):
    strong = np.asarray(pred_dicts["strong"][category], dtype=object)
    area = shapely.area(strong)
    support = np.maximum(best_iou(strong, pred_dicts["same"][category]),
                         best_iou(strong, pred_dicts["dual"][category]))
    return area, support


def mask(area, support, rule):
    minimum = np.where(support < rule["support_iou"], rule["weak_m2"], rule["supported_m2"])
    return area >= minimum


def keep_indices(pred_dicts, policy):
    return {c: np.flatnonzero(mask(*features(pred_dicts, c), policy["rules"][c]))
            for c in CLASSES}
