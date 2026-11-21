"""Infer a projected RGB orthomosaic with the published 2-class roof checkpoint."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import tempfile
import time
import types

import numpy as np
import pyogrio.raw
import rasterio
import shapely
import torch
from pyproj import Transformer
from rasterio.enums import Resampling, ColorInterp
from rasterio.features import geometry_mask
from rasterio.transform import Affine
from rasterio.vrt import WarpedVRT
from rasterio.windows import Window, bounds
from shapely.geometry import box
from shapely.ops import transform

CHIP, PAD, STEP, BLOCK = 512, 128, 256, 512
INPUT = BLOCK + 2 * PAD
CELL = 0.05
CHECKPOINT = "Dominica_SintMaarten_RoofDecking_RoofHole.pth"
CHECKSUM = "ea2e036a652ac8b6c94b73bd8a2a0a808f9ccbcdc14c903c88c13ac8697656d8"
CONFIG = Path(__file__).with_name("mask2former.py")


def load_model(weights, device, *, expected_sha=CHECKSUM, num_classes=3, loss_cls_weights=None):
    from mmcv.utils import ext_loader

    # mmcv-lite has no binary ops. This architecture uses OpenMMLab's
    # grid_sample implementation of MSDeformAttn. Fail on any other binary op.
    def unavailable(*args, **kwargs):
        raise RuntimeError("This model requested an unavailable compiled MMCV operation")

    ext_loader.load_ext = lambda name, funcs: types.SimpleNamespace(
        **{op: unavailable for op in funcs})
    import mmdet.models
    import mmseg.models
    import mmcv.ops.multi_scale_deform_attn as deform
    from mmengine.config import Config
    from mmengine.registry import init_default_scope
    from mmseg.registry import MODELS

    with Path(weights).open("rb") as stream:
        if hashlib.file_digest(stream, "sha256").hexdigest() != expected_sha:
            raise ValueError(f"Unexpected checkpoint SHA-256. Expected {expected_sha}")
    deform.IS_CUDA_AVAILABLE = False
    init_default_scope("mmseg")
    cfg = Config.fromfile(str(CONFIG)).model
    cfg.backbone.init_cfg = None
    cfg.decode_head.pixel_decoder.norm_cfg.type = "BN"
    cfg.decode_head.num_classes = num_classes
    cfg.decode_head.loss_cls.class_weight = loss_cls_weights or [
        2.00003141562227, 1.9921047371577054, 2.007958094086834, 0.1]
    model = MODELS.build(cfg)
    state = torch.load(weights, weights_only=True, map_location="cpu")
    model.load_state_dict(state, strict=True)
    print(f"Strictly loaded {len(state)} checkpoint tensors", flush=True)
    return model.eval().to(device)


def read_boundary(path, layer, crs):
    metadata, _, wkbs, _ = pyogrio.raw.read(path, layer=layer, columns=[])
    if not metadata["crs"]:
        raise ValueError("Boundary must have a declared CRS")
    converters = Transformer.from_crs(metadata["crs"], crs, always_xy=True)
    geoms = shapely.make_valid(shapely.force_2d(shapely.from_wkb(wkbs)))
    return transform(converters.transform, shapely.union_all(geoms))


def block_predictor(model, device, tiling="hann"):
    num_classes = model.decode_head.num_classes
    mean = torch.tensor([.485, .456, .406], device=device)[:, None, None]
    sd = torch.tensor([.229, .224, .225], device=device)[:, None, None]
    one_d = torch.hann_window(CHIP, periodic=True, device=device)
    hann = one_d[:, None] * one_d[None, :]
    core = slice(PAD, PAD + BLOCK)
    if tiling == "hann":
        offsets = [(y, x) for y in (0, STEP) for x in (0, STEP)]
    elif tiling == "nonoverlap":
        offsets = [(PAD, PAD)]
        hann = torch.ones_like(hann)
    else:
        raise ValueError("tiling must be hann or nonoverlap")
    denom = torch.zeros((INPUT, INPUT), device=device)
    for y, x in offsets:
        denom[y:y+CHIP, x:x+CHIP] += hann
    denom = denom[core, core]
    assert denom.min().item() > 0
    metas = [dict(img_shape=(CHIP, CHIP), pad_shape=(CHIP, CHIP), ori_shape=(CHIP, CHIP))]

    @torch.inference_mode()
    def classify(rgb):
        normalized = (torch.as_tensor(rgb, device=device).float() / 255 - mean) / sd
        scores = torch.zeros((num_classes, INPUT, INPUT), device=device)
        for y, x in offsets:
            patch = normalized[:, y:y+CHIP, x:x+CHIP].contiguous().unsqueeze(0)
            activation = model.encode_decode(patch, metas)[0]
            scores[:, y:y+CHIP, x:x+CHIP] += activation * hann
        return (scores[:, core, core] / denom).argmax(0).byte().cpu().numpy()
    return classify


def read_block(vrt, window, region):
    # WarpedVRT does not accept boundless=True. Read only the available window
    # and place it in the correctly offset context canvas.
    available = window.intersection(Window(0, 0, vrt.width, vrt.height))
    pixels = vrt.read([1, 2, 3], window=available, masked=True)
    valid = ~np.ma.getmaskarray(pixels).any(axis=0)
    valid &= geometry_mask([region], out_shape=valid.shape,
                           transform=vrt.window_transform(available), invert=True)
    rgb = np.zeros((3, INPUT, INPUT), dtype=np.uint8)
    coverage = np.zeros((INPUT, INPUT), dtype=bool)
    y = int(available.row_off - window.row_off)
    x = int(available.col_off - window.col_off)
    h, w = valid.shape
    rgb[:, y:y+h, x:x+w] = np.where(valid, pixels.data, 0)
    coverage[y:y+h, x:x+w] = valid
    return rgb, coverage[PAD:PAD+BLOCK, PAD:PAD+BLOCK]


def run(image, output, weights, boundary=None, layer=None, device="cuda", *,
        model_loader=load_model, class_map=(0, 1, 2), class_names=("background", "Decking", "Hole"),
        tiling="hann"):
    image, output = Path(image), Path(output)
    if output.exists():
        raise FileExistsError(output)
    if layer and not boundary:
        raise ValueError("--layer requires --boundary")
    output.parent.mkdir(parents=True, exist_ok=True)
    start = time.perf_counter()
    with rasterio.open(image) as src:
        if not src.crs or not src.crs.is_projected or not math.isclose(src.crs.linear_units_factor[1], 1):
            raise ValueError("Input must use a projected CRS in metres")
        if src.count < 3 or any(d != "uint8" for d in src.dtypes[:3]):
            raise ValueError("Input must have uint8 red, green, blue as the first three bands")
        if src.colorinterp[:3] != (ColorInterp.red, ColorInterp.green, ColorInterp.blue):
            raise ValueError("Input must declare the first three bands as red, green, and blue")
        grid = Affine(CELL, 0, src.bounds.left, 0, -CELL, src.bounds.top)
        extent = box(*src.bounds)
        region = read_boundary(boundary, layer, src.crs).intersection(extent) if boundary else extent
        if region.is_empty or region.area <= 0:
            raise ValueError("Input image and boundary have no area in common")
        left, bottom, right, top = region.bounds
        c0, r0 = ~grid * (left, top)
        c1, r1 = ~grid * (right, bottom)
        c0, r0 = math.floor(c0 / BLOCK), math.floor(r0 / BLOCK)
        c1, r1 = math.ceil(c1 / BLOCK), math.ceil(r1 / BLOCK)
        jobs = []
        for r in range(r0, r1):
            for c in range(c0, c1):
                w = Window(c*BLOCK, r*BLOCK, BLOCK, BLOCK)
                if region.intersection(box(*bounds(w, grid))).area > 0:
                    jobs.append((r, c))
        if not jobs:
            raise ValueError("No output tiles intersect the boundary")
        # Outward tile snapping keeps the grid comparable across runs.
        width = math.ceil((src.bounds.right - src.bounds.left) / CELL / BLOCK) * BLOCK
        height = math.ceil((src.bounds.top - src.bounds.bottom) / CELL / BLOCK) * BLOCK
        width_out, height_out = (c1-c0)*BLOCK, (r1-r0)*BLOCK
        model = model_loader(weights, device)
        if len(class_map) != model.decode_head.num_classes or len(class_names) != len(class_map):
            raise ValueError("Provide one output class code and name per model channel")
        if any(x < 0 or x >= 255 for x in class_map) or len(set(class_map)) != len(class_map):
            raise ValueError("Output class codes must be distinct and in [0,254]")
        classify = block_predictor(model, device, tiling)
        codes = np.asarray(class_map, dtype=np.uint8)
        model_seconds = time.perf_counter() - start
        valid_pixels = 0
        forward_seconds = 0
        # TemporaryDirectory stays on the output volume. Publish only a closed TIFF.
        with tempfile.TemporaryDirectory(dir=output.parent) as tmp, WarpedVRT(
            src, crs=src.crs, transform=grid, width=width, height=height,
            resampling=Resampling.cubic, add_alpha=ColorInterp.alpha not in src.colorinterp,
        ) as vrt:
            tmp_mask = Path(tmp) / "mask.tif"
            with rasterio.open(tmp_mask, "w", driver="GTiff", width=width_out,
                               height=height_out, count=1, dtype="uint8", crs=src.crs,
                               transform=grid*Affine.translation(c0*BLOCK,r0*BLOCK),
                               nodata=255, tiled=True, compress="deflate", BIGTIFF="IF_SAFER") as dst:
                for index, (r, c) in enumerate(jobs, start=1):
                    context = Window(c*BLOCK-PAD, r*BLOCK-PAD, INPUT, INPUT)
                    rgb, valid = read_block(vrt, context, region)
                    before = time.perf_counter()
                    pred = codes[classify(rgb)]
                    forward_seconds += time.perf_counter() - before
                    pred[~valid] = 255
                    dst.write(pred, 1, window=Window((c-c0)*BLOCK, (r-r0)*BLOCK, BLOCK, BLOCK))
                    valid_pixels += int(valid.sum())
                    if index == 1 or index % 25 == 0 or index == len(jobs):
                        print(f"{index}/{len(jobs)} output blocks; {time.perf_counter()-start:.1f}s", flush=True)
                dst.update_tags(classes="; ".join(f"{v}={n}" for v, n in zip(class_map, class_names))+"; 255=NoData",
                                padding=PAD if tiling == "hann" else 0, chip=CHIP,
                                stride=STEP if tiling == "hann" else CHIP,
                                merge="Hann before argmax" if tiling == "hann" else "none")
            tmp_mask.rename(output)
    return dict(blocks=len(jobs), chip_forward_passes=(4 if tiling == "hann" else 1)*len(jobs),
                valid_pixels=valid_pixels,
                device=str(device), hardware=torch.cuda.get_device_name(device) if str(device).startswith("cuda") else "CPU",
                model_setup_seconds=model_seconds, block_forward_and_merge_seconds=forward_seconds,
                total_seconds=time.perf_counter()-start)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--image", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    weights = parser.add_mutually_exclusive_group(required=True)
    weights.add_argument("--weights", type=Path)
    weights.add_argument("--assets-dir", type=Path, help="Directory containing the published .pth")
    parser.add_argument("--boundary", type=Path)
    parser.add_argument("--layer", help="Boundary layer in a multilayer vector dataset")
    parser.add_argument("--device", choices=["cuda", "cpu"], default="cuda")
    parser.add_argument("--tiling", choices=["hann", "nonoverlap"], default="hann")
    parser.add_argument("--stats", type=Path)
    args = parser.parse_args()
    if args.stats:
        if args.stats.exists() or args.stats.resolve() == args.output.resolve():
            parser.error("--stats must name a new file different from --output")
        args.stats.parent.mkdir(parents=True, exist_ok=True)
    torch.set_num_threads(5)
    result = run(args.image, args.output, args.weights or args.assets_dir / CHECKPOINT,
                 args.boundary, args.layer, args.device, tiling=args.tiling)
    stats = json.dumps(result, indent=2)
    print(stats)
    if args.stats:
        args.stats.write_text(stats, encoding="utf-8")


if __name__ == "__main__":
    main()
