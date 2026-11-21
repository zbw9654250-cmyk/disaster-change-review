"""Fast checks for the image-only model adapter, including decisions without usable pixels."""
from pathlib import Path
import json
from tempfile import TemporaryDirectory

from PIL import Image
import vlm_predict as vlm


def test_response_schema():
    partial = '{"grade":"moderate","explanation_zh":"西侧屋面边界出现明显中断。","review_required":false}'
    row = vlm.parse_answer(partial)
    assert row["grade"] == "moderate" and row["review_required"]
    for invalid in (partial.replace("moderate", "ruined"), partial.replace("false", '"false"'),
                    partial.replace("西侧屋面边界出现明显中断。", "broken edge")):
        try:
            vlm.parse_answer(invalid)
        except ValueError:
            continue
        raise AssertionError("Malformed model result was accepted")


def test_missing_blank_and_partial_inputs():
    with TemporaryDirectory() as temp:
        root = Path(temp)
        img = root / "building.png"
        case = {"building_id": "A", "image_path": img.name}
        args = (case, root, None, None, None, "test", 32)
        assert vlm.grade_case(*args)["status"] == "inference_error"
        Image.new("RGB", (30, 30), "gray").save(img)
        blank = vlm.grade_case(*args)
        assert blank["status"] == "abstained" and blank["explanation_zh"] == ""
        assert len(blank["image_sha256"]) == 64
        img_data = Image.open(img).convert("RGB")
        img_data.putpixel((2, 2), (255, 0, 0))
        img_data.save(img)
        case["coverage_fraction"] = 0.97
        partial = vlm.grade_case(*args)
        assert partial["status"] == "abstained" and partial["review_required"]
        manifest = root / "cases.jsonl"
        manifest.write_text((json.dumps(case) + "\n") * 2)
        try:
            vlm.records(manifest)
        except ValueError:
            return
        raise AssertionError("Duplicate buildings must be rejected")
