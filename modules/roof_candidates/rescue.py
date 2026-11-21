"""Candidate agreement and overlap in projected metric coordinates."""
import numpy as np
import shapely
from retain import CLASSES


def overlaps(left, right):
    """Sparse polygon intersections populated into a small scene IoU matrix."""
    left, right = np.asarray(left, dtype=object), np.asarray(right, dtype=object)
    values = np.zeros((len(left), len(right)))
    if len(left) and len(right):
        i, j = shapely.STRtree(right).query(left, predicate="intersects")
        shared = shapely.area(shapely.intersection(left[i], right[j]))
        union = shapely.area(left[i]) + shapely.area(right[j]) - shared
        values[i, j] = np.divide(shared, union, where=union > 0, out=np.zeros_like(shared))
    return values


def describe(strong, same, dual):
    arrays = [np.asarray(a, dtype=object) for a in (same, dual)]
    geom = np.concatenate(arrays)
    cross = overlaps(*arrays)
    duplicate = overlaps(geom, geom)
    base = overlaps(geom, strong).max(axis=1, initial=0)
    peer = np.r_[cross.max(axis=1, initial=0), cross.max(axis=0, initial=0)]
    area = shapely.area(geom)
    hull = shapely.area(shapely.convex_hull(geom))
    solidity = np.divide(area, hull, out=np.zeros_like(area), where=hull > 0)
    return geom, peer, base, solidity, duplicate


def select(features, rule):
    if rule is None:
        return []
    geom, peer, base, solidity, duplicate = features
    # Put directly corroborated candidates first, including partial contour corrections.
    quality = peer + 0.15 * solidity - 0.08 * base
    eligible = (peer >= rule["peer"]) & (base <= rule["base"]) & (solidity >= rule["solidity"])
    order = np.argsort(-quality, kind="stable")
    selected = []
    for i in order[eligible[order]]:
        if not selected or duplicate[i, [j for j, _ in selected]].max() < 0.4:
            selected.append((int(i), float(quality[i])))
    return selected


def ranked_from_layers(strong, same, dual, config):
    """Return (class, unmodified polygon, score) sorted across classes without accessing any scene."""
    result = []
    for c in CLASSES:
        data = describe(strong[c], same[c], dual[c])
        for i, quality in select(data, config["rules"][c]):
            result.append((c, data[0][i], quality))
    return sorted(result, key=lambda x: -x[2])
