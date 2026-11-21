"""Join building-level VLM predictions to their source images and optional WGS84 footprints."""
import argparse
import base64
from html import escape
from hashlib import sha256
from io import BytesIO
import json
import math
from pathlib import Path
from tempfile import TemporaryDirectory

from PIL import Image, ImageOps

GRADE = {"none": "未见明显损伤", "light": "轻度", "moderate": "中度", "severe": "重度", "uncertain": "待判"}


def keyed(path):
    rows = {}
    for line_number, line in enumerate(path.read_text(encoding="utf-8-sig").splitlines(), start=1):
        if not line.strip():
            continue
        item = json.loads(line)
        key = item.get("building_id") if isinstance(item, dict) else None
        if not isinstance(key, str) or not key.strip() or key in rows:
            raise ValueError(f"{path}:{line_number}: missing or duplicate building_id {key!r}")
        rows[key] = item
    if not rows:
        raise ValueError(f"{path}: empty manifest")
    return rows


def preview(manifest, value, caption, expected_sha=None, optional=False):
    src = Path(value)
    if not src.is_absolute():
        src = manifest.parent / src
    if optional and not src.is_file():
        return f"<figure><figcaption>{caption}影像不可用</figcaption></figure>"
    if expected_sha and sha256(src.read_bytes()).hexdigest() != expected_sha:
        raise ValueError(f"Image no longer matches inference input: {src}")
    try:
        with Image.open(src) as image:
            rgb = ImageOps.exif_transpose(image).convert("RGB")
            rgb.thumbnail((720, 720))
            output = BytesIO()
            rgb.save(output, format="JPEG", quality=89)
    except OSError:
        if optional:
            return f"<figure><figcaption>{caption}影像不可读</figcaption></figure>"
        raise
    encoded = base64.b64encode(output.getvalue()).decode("ascii")
    return f'<figure><img alt="{caption}" src="data:image/jpeg;base64,{encoded}"><figcaption>{caption}</figcaption></figure>'


def validate_geometry(geometry):
    if geometry is None:
        return
    if geometry.get("type") not in ("Polygon", "MultiPolygon"):
        raise ValueError("Expected a WGS84 Polygon or MultiPolygon building footprint")
    polygons = geometry["coordinates"] if geometry["type"] == "MultiPolygon" else [geometry["coordinates"]]
    if not polygons or any(not rings for rings in polygons):
        raise ValueError("Empty building footprint")
    for rings in polygons:
        for ring in rings:
            if len(ring) < 4 or ring[0] != ring[-1]:
                raise ValueError("Unclosed building footprint")
            for xy in ring:
                if len(xy) < 2 or not (-180 <= xy[0] <= 180 and -90 <= xy[1] <= 90):
                    raise ValueError("Invalid WGS84 coordinate")


def combine(cases, predictions, out, credit=None):
    cases, predictions, out = Path(cases), Path(predictions), Path(out)
    targets, answers = keyed(cases), keyed(predictions)
    if targets.keys() != answers.keys():
        raise ValueError(f"IDs differ: missing={sorted(targets.keys()-answers.keys())}, extra={sorted(answers.keys()-targets.keys())}")
    if out.exists():
        raise FileExistsError(f"Choose a new export directory: {out}")
    cards, features = [], []
    totals = {name: 0 for name in GRADE}
    for key, case in targets.items():
        answer = answers[key]
        grade = answer.get("grade")
        explanation = answer.get("explanation_zh")
        model = answer.get("model")
        status = answer.get("status", "ok")
        if status not in ("ok", "abstained", "inference_error") or (status != "ok" and grade != "uncertain"):
            raise ValueError(f"{key}: incompatible prediction status and grade")
        if grade not in GRADE or not isinstance(explanation, str) or (status == "ok" and not explanation.strip()):
            raise ValueError(f"{key}: invalid grade or missing explanation")
        if not isinstance(model, str) or not model.strip() or not isinstance(answer.get("review_required"), bool):
            raise ValueError(f"{key}: missing model or review flag")
        geometry = case.get("geometry")
        validate_geometry(geometry)
        coverage = case.get("coverage_fraction")
        if coverage is not None and (not isinstance(coverage, (int, float)) or not 0 <= coverage <= 1):
            raise ValueError(f"{key}: invalid image coverage")
        partial = coverage is not None and coverage < .98
        reported = "uncertain" if partial else grade
        totals[reported] += 1
        review = partial or grade == "uncertain" or answer["review_required"]
        roof = case.get("roof_evidence")
        fraction = roof.get("damage_fraction") if isinstance(roof, dict) else None
        if fraction is not None and (not math.isfinite(fraction) or not 0 <= fraction <= 1):
            raise ValueError(f"{key}: invalid roof evidence fraction")
        disagreement = reported == "none" and fraction is not None and fraction > 0
        review = review or (fraction is not None and fraction > 0)
        properties = {"building_id": key, "grade": reported, "grade_zh": GRADE[reported],
                      "model_grade": grade, "explanation_zh": explanation or None, "model": model, "status": status,
                      "grade_status": "preliminary", "review_required": True,
                      "priority_review": review, "image_coverage": coverage,
                      "roof_visual_disagreement": disagreement,
                      "roof_damage_fraction": fraction, "footprint_source": case.get("footprint_source")}
        if geometry is not None:
            features.append({"type": "Feature", "id": key, "properties": properties, "geometry": geometry})
        pictures = ""
        if case.get("pre_image_path"):
            pictures += preview(cases, case["pre_image_path"], "灾前目标", answer.get("pre_image_sha256"), status == "inference_error")
        pictures += preview(cases, case["image_path"], "灾后目标", answer.get("image_sha256"), status == "inference_error")
        details = []
        if fraction is not None:
            parts = []
            for label, name in (("Decking", "屋面板外露"), ("Hole", "孔洞")):
                if label in roof:
                    properties[label.lower()+"_count"] = roof[label]["count"]
                    properties[label.lower()+"_m2"] = roof[label]["area_m2"]
                    parts.append(f'{name} {roof[label]["count"]} 处')
            details.append("屋面模型候选：" + "、".join(parts) + f"，合并覆盖建筑轮廓的 {fraction:.1%}")
        if disagreement:
            details.append("屋面模型有候选，整栋目视判为未见明显损伤，两项需对照")
        if partial:
            details.append(f"有效影像覆盖 {coverage:.1%}，整栋等级待判")
        if review:
            details.append("优先复核")
        if not explanation:
            details.append("模型推理失败，无目视解释" if status == "inference_error" else "影像质量检查触发待判，无模型目视解释")
        tags = " · ".join(details)
        cards.append(f'<article><header><h2>{escape(key)}</h2><b class="{reported}">{GRADE[reported]}</b></header>'
                     f'<div class="photos">{pictures}</div><p>{escape(explanation)}</p>'
                     f'<small>{escape(tags)}</small><footer>{escape(model)}</footer></article>')
    counts = "　".join(f"{GRADE[g]} {n}" for g, n in totals.items() if n)
    html = """<!DOCTYPE html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>逐栋灾后影像复核</title><style>
*{box-sizing:border-box}body{margin:auto;max-width:1400px;padding:28px;background:#f4f5f0;color:#172c33;font:16px/1.55 system-ui,sans-serif}h1{margin:0}
main{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,380px),1fr));gap:18px}article{background:white;border:1px solid #cbd5d4;border-radius:8px;padding:16px;min-width:0}header,.photos{display:flex;gap:8px}header{justify-content:space-between;align-items:start}h2{font-size:16px;margin:0;overflow-wrap:anywhere}b{white-space:nowrap;padding:2px 8px;border-radius:4px;background:#e2f1e9}.moderate{background:#ffdfa7}.severe{background:#f6c6bd}.uncertain{background:#d9e0e6}.photos{margin-top:12px;align-items:flex-start}figure{margin:0;flex:1;min-width:0}img{width:100%;height:auto;display:block}figcaption,small,footer{font-size:13px;color:#42565b}footer{margin-top:6px;overflow-wrap:anywhere}p{margin:.65em 0}
</style><h1>逐栋灾后影像复核</h1><p>等级和图下说明来自影像初评，每栋均待人工确认。现场结构安全需另行鉴定。</p>"""
    html += f"<p>{counts}</p><main>{''.join(cards)}</main>"
    if credit:
        html += f"<footer>{escape(credit)}</footer>"
    html += "</html>"
    out.parent.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(dir=out.parent) as temp:
        staging = Path(temp) / "review"
        staging.mkdir()
        (staging / "review.html").write_text(html, encoding="utf-8")
        (staging / "buildings.geojson").write_text(json.dumps({"type": "FeatureCollection", "features": features},
                                          ensure_ascii=False, allow_nan=False), encoding="utf-8")
        staging.rename(out)
    return {"cases": len(cards), "geolocated": len(features), "grades": totals}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cases", required=True, type=Path)
    parser.add_argument("--predictions", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--credit", help="Image and annotation credits for the offline viewer")
    args = parser.parse_args()
    print(json.dumps(combine(args.cases, args.predictions, args.out, args.credit)))
