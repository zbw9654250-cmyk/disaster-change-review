"""Read and index building manifests used by the grade attachment step."""
import json
from pathlib import Path


def read(path):
    return [json.loads(s) for s in Path(path).read_text(encoding="utf-8-sig").splitlines() if s.strip()]


def index(rows, *fields):
    by_id = {}
    for row in rows:
        k = tuple(row[f] for f in fields)
        if k in by_id:
            raise ValueError(f"Duplicate key {k}")
        by_id[k] = row
    return by_id
