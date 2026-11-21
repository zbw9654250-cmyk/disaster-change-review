"""Grade and describe a single target building per case using Qwen3-VL images only."""
import argparse
import hashlib
from io import BytesIO
import json
import os
from pathlib import Path
import re
import tempfile
import time

from PIL import Image, ImageOps

GRADES = ("none", "light", "moderate", "severe", "uncertain")
PROMPT = """观察目标建筑，用于灾后遥感影像人工复核。目标是图片中央被标记或居中的同一栋建筑，只看其边界内。彩色边线是位置提示，邻栋、道路、阴影、树木、屋顶正常接缝和色差不能作为损伤依据。
先用一至两句中文记录灾后可见证据：说明目标的哪个部位，边缘、屋面轮廓或可见碎片呈什么状态。目视依据不足时具体说明有什么看不清。不要为结论编造事实、百分比、致灾原因、建筑内部情况或居住安全。
然后给出整栋的影像损伤等级。none=整体轮廓和屋面可辨且没有明确损伤，light=局部小面积可见破损而主体完好，moderate=明显较大范围损伤、仍可辨认建筑主体，severe=建筑基本毁坏或大范围坍毁，uncertain=目标不可辨、影像质量或遮挡使分级依据不足。一般屋面破损不能算整栋毁坏。
仅返回一个 JSON 对象，键为 explanation_zh、grade、review_required。grade 使用上述英文值，review_required 为布尔值。"""

def records(path):
    seen = set()
    result = []
    for line in path.read_text(encoding="utf-8-sig").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        key = row.get("building_id")
        if not isinstance(key, str) or not key.strip() or key in seen:
            raise ValueError("building_id must be nonempty and unique")
        seen.add(key)
        result.append(row)
    return result


def read_image(path):
    data = path.read_bytes()
    digest = hashlib.sha256(data).hexdigest()
    with Image.open(BytesIO(data)) as src:
        image = ImageOps.exif_transpose(src).convert("RGB")
    image.thumbnail((896, 896), Image.Resampling.LANCZOS)
    return image, digest


def parse_answer(raw):
    text = raw.strip()
    match = re.fullmatch(r"```(?:json)?\s*(.*?)\s*```", text, re.S | re.I)
    result = json.loads(match.group(1) if match else text)
    if not isinstance(result, dict) or result.get("grade") not in GRADES:
        raise ValueError("Invalid grade in model response")
    observation = result.get("explanation_zh")
    if not isinstance(observation, str) or not re.search(r"[\u3400-\u9fff]", observation):
        raise ValueError("Expected a Chinese visual observation")
    review = result.get("review_required")
    if type(review) is not bool:
        raise ValueError("Expected boolean review_required")
    return {"grade": result["grade"], "explanation_zh": observation.strip(),
            "review_required": review or result["grade"] in ("uncertain", "moderate", "severe")}


def describe(processor, model, images, torch, max_tokens):
    parts = []
    captions = ["灾前参考（较早影像）", "灾后待评影像"] if len(images) == 2 else ["灾后待评影像（单期）"]
    for caption, image in zip(captions, images):
        parts.extend([{"type": "text", "text": caption}, {"type": "image", "image": image}])
    parts.append({"type": "text", "text": PROMPT})
    inputs = processor.apply_chat_template([{"role": "user", "content": parts}],
             tokenize=True, add_generation_prompt=True, return_dict=True, return_tensors="pt").to(model.device)
    with torch.inference_mode():
        generated = model.generate(**inputs, max_new_tokens=max_tokens, do_sample=False)
    return processor.decode(generated[0, inputs.input_ids.shape[1]:], skip_special_tokens=True).strip()


def grade_case(case, directory, processor, model, torch, model_id, max_tokens):
    result = {"building_id": case["building_id"], "model": model_id,
              "grade": "uncertain", "explanation_zh": "", "review_required": True,
              "status": "inference_error"}
    start = time.perf_counter()
    try:
        post, result["image_sha256"] = read_image(directory / case["image_path"])
        images = [post]
        if case.get("pre_image_path"):
            pre, result["pre_image_sha256"] = read_image(directory / case["pre_image_path"])
            images.insert(0, pre)
        if float(case.get("coverage_fraction", 1.0)) < 0.98 or all(lo == hi for lo, hi in post.getextrema()):
            result.update(status="abstained", reason="insufficient_target_coverage_or_blank_post_image")
        else:
            raw = describe(processor, model, images, torch, max_tokens)
            result["raw_model_output"] = raw
            result.update(parse_answer(raw))
            result["status"] = "abstained" if result["grade"] == "uncertain" else "ok"
    except (OSError, ValueError, RuntimeError, TypeError, KeyError) as error:
        result["error"] = f"{type(error).__name__}: {error}"
    result["seconds"] = round(time.perf_counter() - start, 4)
    return result


def main():
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("--cases", required=True, type=Path)
    cli.add_argument("--output", required=True, type=Path)
    cli.add_argument("--model", required=True, type=Path, help="Local Qwen3-VL Instruct checkpoint")
    cli.add_argument("--model-id", help="Public checkpoint name for prediction provenance")
    cli.add_argument("--max-tokens", type=int, default=220)
    args = cli.parse_args()
    cases = records(args.cases)
    if args.output.exists() or not cases or args.max_tokens < 1:
        cli.error("Provide nonempty cases, a new output file and a positive token limit")
    import torch
    from transformers import AutoModelForImageTextToText, AutoProcessor
    processor = AutoProcessor.from_pretrained(args.model, local_files_only=True)
    model = AutoModelForImageTextToText.from_pretrained(args.model, dtype=torch.bfloat16,
            attn_implementation="sdpa", local_files_only=True).to("cuda").eval()
    model_id = args.model_id or args.model.name
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=args.output.parent, delete=False, mode="w", encoding="utf-8") as stream:
        temp = Path(stream.name)
        try:
            for case in cases:
                result = grade_case(case, args.cases.parent, processor, model, torch, model_id, args.max_tokens)
                print(json.dumps(result, ensure_ascii=False), file=stream, flush=True)
                print(case["building_id"], result["status"], result["seconds"], flush=True)
            stream.close()
            os.link(temp, args.output)
        finally:
            stream.close()
            temp.unlink(missing_ok=True)


if __name__ == "__main__":
    main()
