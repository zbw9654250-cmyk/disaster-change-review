"""Recalculate the released headline metrics from the per-scene counts and blind votes."""
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"


def load(path):
    return json.loads(path.read_bytes())


def keyed_votes(path):
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]
    records = {(r["building_id"], r["slot"]): r for r in rows}
    if len(records) != len(rows):
        raise ValueError(f"Duplicate building and slot in {path.name}")
    return records


def observations():
    review = RESULTS / "observations" / "review"
    published = load(review / "scores.json")["real"]
    accepted = Counter()
    for group in ("panel", "confirm"):
        folder = review / group
        key, reader_a, reader_b = (keyed_votes(folder / f"{name}.jsonl")
                                   for name in ("key", "reader-a", "reader-b"))
        if not key.keys() == reader_a.keys() == reader_b.keys():
            raise ValueError(f"Incomplete votes in {group}")
        counts = Counter()
        for idx, entry in key.items():
            if all(v[idx]["specific"] and v[idx]["grounded"] for v in (reader_a, reader_b)):
                counts[entry["method"]] += 1
        for method, result in published[group].items():
            if counts[method] != result["both_accepted"]:
                raise ValueError(f"Disagreement with the released counts for {group}/{method}")
            accepted[method] += counts[method]
    return dict(accepted)


def roof_objects():
    report = load(RESULTS / "roof_objects.json")
    output = {}
    for method in ("baseline", "equal_budget"):
        count = Counter()
        for scene in report["scenes"].values():
            for record in scene[method]["classes"].values():
                for k in ("tp", "fp", "fn"):
                    count[k] += record[k]
        if any(count[k] != report["totals"][method]["both"][k] for k in count):
            raise ValueError(f"Scene counts do not match totals for {method}")
        tp, fp, fn = count["tp"], count["fp"], count["fn"]
        output[method] = dict(candidates=tp + fp, true_positives=tp, false_positives=fp,
                              false_negatives=fn, f1_percent=round(200 * tp / (2 * tp + fp + fn), 2))
    return output


def grades():
    correct = total = 0
    for p in ("grades_first.json", "grades_confirm.json"):
        matrix = load(RESULTS / p)["confusion_rows_true_columns_predicted"]
        correct += sum(row[label] for label, row in matrix.items())
        total += sum(sum(row.values()) for row in matrix.values())
    return dict(correct=correct, total=total)


def roof_ranking():
    report = load(RESULTS / "roof_ranking_ablation.json")
    rows = [row for site in report["sites"].values() for row in site["equal_budget"].values()]
    counts = {"replacement_slots": sum(row["quota"] for row in rows)}
    for method in ("area_only", "frozen"):
        recovered = sum(len(row["methods"][method]["new_ids"]) for row in rows)
        if recovered != report["totals"]["equal_budget"][method]["new_ids"]:
            raise ValueError(f"Ranking totals disagree for {method}")
        counts[method + "_recovered"] = recovered
    return counts


if __name__ == "__main__":
    print(json.dumps(dict(roof_objects=roof_objects(), roof_ranking=roof_ranking(), building_grades=grades(),
                          explanations_accepted_by_both=observations()), indent=2))
