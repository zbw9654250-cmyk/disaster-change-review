"""Run the building-level assessment from a post-disaster orthomosaic to a GIS layer and a review page."""
import argparse
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory

HERE = Path(__file__).resolve().parent


def run(args):
    output = args.out.resolve()
    if output.exists():
        raise FileExistsError(f"Select a new output directory: {output}")
    output.parent.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(dir=output.parent) as temp:
        work = Path(temp) / "run"
        work.mkdir()
        prepare = [sys.executable, str(HERE / "prepare_buildings.py"), "--raster", str(args.raster),
                   "--footprints", str(args.footprints), "--scene-id", args.scene_id, "--output", str(work / "inputs")]
        if args.damage:
            prepare.extend(["--damage", str(args.damage)])
        subprocess.run(prepare, check=True)
        cases = str(work / "inputs" / "cases.jsonl")
        answers = str(work / "predictions.jsonl")
        predict = [sys.executable, str(HERE / "vlm_predict.py"), "--cases", cases,
                   "--output", answers, "--model", str(args.model)]
        if args.model_id:
            predict.extend(["--model-id", args.model_id])
        subprocess.run(predict, check=True)
        export = [sys.executable, str(HERE / "export_buildings.py"), "--cases", cases,
                  "--predictions", answers, "--out", str(work / "review")]
        if args.credit:
            export.extend(["--credit", args.credit])
        subprocess.run(export, check=True)
        work.rename(output)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raster", type=Path, required=True)
    parser.add_argument("--footprints", type=Path, required=True)
    parser.add_argument("--damage", type=Path)
    parser.add_argument("--scene-id", required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument("--model-id", help="Published checkpoint name for provenance")
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--credit", help="Credits for the source imagery and annotations")
    run(parser.parse_args())
