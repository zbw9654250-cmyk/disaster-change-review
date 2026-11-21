"""Run the four-region roof-hole Mask2Former on a projected RGB orthomosaic."""
import argparse
from functools import partial
import hashlib
import json
from pathlib import Path

from fetch import MODEL, MODELS, ASSETS

from infer import load_model, run
import torch

EMD_SHA256 = MODELS["hole"][".emd"]
WEIGHTS_SHA256 = MODELS["hole"][".pth"]


def predict(image, output, assets_dir, boundary=None, layer=None, device="cuda"):
    raw = (assets_dir / f"{MODEL}.emd").read_bytes()
    if hashlib.sha256(raw).hexdigest() != EMD_SHA256:
        raise ValueError("Unexpected Zenodo model definition")
    emd = json.loads(raw)
    if [(c["Value"], c["Name"]) for c in emd["Classes"]] != [(2, "Hole")]:
        raise ValueError("Unexpected class mapping in the Esri model definition")
    loader = partial(load_model, expected_sha=WEIGHTS_SHA256, num_classes=2,
                     loss_cls_weights=[1.0, 1.0, 0.1])
    stats = run(image, output, assets_dir / emd["ModelFile"], boundary, layer, device,
                model_loader=loader, class_map=(0, 2), class_names=("background", "Hole"))
    return dict(model=MODEL, checkpoint_sha256=WEIGHTS_SHA256, emd_sha256=EMD_SHA256,
                source="https://zenodo.org/records/20581719", **stats)


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("--image", required=True, type=Path)
    cli.add_argument("--output", required=True, type=Path)
    cli.add_argument("--assets-dir", type=Path, default=ASSETS)
    cli.add_argument("--boundary", type=Path)
    cli.add_argument("--layer")
    cli.add_argument("--device", choices=["cuda", "cpu"], default="cuda")
    cli.add_argument("--stats", type=Path)
    args = cli.parse_args()
    torch.set_num_threads(5)
    stats = predict(args.image, args.output, args.assets_dir, args.boundary, args.layer, args.device)
    report = json.dumps(stats, indent=2)
    print(report)
    if args.stats:
        args.stats.write_text(report, encoding="utf-8")
