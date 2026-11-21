"""Compare local RGB change to same-grid surrounding reference pixels; returns an observation only."""
import argparse
import hashlib
from io import BytesIO
import json
from math import isfinite
from pathlib import Path
import numpy as np
from PIL import Image
from scipy.ndimage import binary_dilation, label


def insufficient(reason,stats):
    return {"status":"reference_insufficient","note_zh":"周边参考不足，无法判断局部色变与周边是否一致。",
            "reason":reason,"measurements":stats}


def finite_number(value):
    return isinstance(value,(int,float,np.integer,np.floating)) and not isinstance(value,bool) and isfinite(value)


def fit_channel(x,y):
    interior=(x>4)&(x<251)&(y>4)&(y<251)
    if interior.sum()<80:
        return None
    x,y=x[interior],y[interior]
    spread=np.quantile(x,.9)-np.quantile(x,.1)
    if spread<15: return None
    keep=np.ones(x.size,bool)
    for _ in range(4):
        xx,yy=x[keep],y[keep]
        if xx.size<50 or xx.std()<3:return None
        slope=float(np.dot(xx-xx.mean(),yy-yy.mean())/np.dot(xx-xx.mean(),xx-xx.mean()))
        offset=float(np.median(yy-slope*xx))
        error=np.abs(y-(slope*x+offset))
        keep=error<=max(3.,2.8*float(np.median(error)))
    if not .60<=slope<=1.55 or abs(offset)>72:return None
    return slope,offset


def assess(pre,post,pre_mask,post_mask,*,same_grid=False,registration_error_px=None,
           pre_valid=None,post_valid=None,coverage_fraction=None,pre_coverage_fraction=None,roi=None):
    stats={"registration_error_px":registration_error_px if finite_number(registration_error_px) else None}
    if same_grid is not True or not finite_number(registration_error_px) or not 0<=registration_error_px<=1.0:
        return insufficient("grid_or_registration_unverified",stats)
    if pre_mask is None or post_mask is None:return insufficient("footprint_missing",stats)
    if any(not finite_number(x) for x in (coverage_fraction,pre_coverage_fraction)):
        return insufficient("source_coverage_unverified",stats)
    if any(not .98<=x<=1. for x in (coverage_fraction,pre_coverage_fraction)):
        return insufficient("source_coverage_below_98pct",stats)
    a,b=np.asarray(pre.convert("RGB"),dtype=float),np.asarray(post.convert("RGB"),dtype=float)
    m,n=np.asarray(pre_mask.convert("L"))>127,np.asarray(post_mask.convert("L"))>127
    if a.shape!=b.shape or m.shape!=a.shape[:2] or n.shape!=m.shape:
        return insufficient("grid_size_mismatch",stats)
    valid=np.ones(m.shape,bool)
    for im in (pre_valid,post_valid):
        if im is not None:
            mask=np.asarray(im.convert("L"))>0
            if mask.shape!=m.shape:return insufficient("validity_grid_mismatch",stats)
            valid &= mask
    union=m|n; joint=m&n
    if joint.sum()<64 or joint.sum()<.70*union.sum():return insufficient("target_overlap_too_small",stats)
    if valid[joint].mean()<.98:return insufficient("valid_target_coverage_below_98pct",stats)
    target=joint.copy()
    if roi is not None:
        if len(roi)!=4 or not all(finite_number(x) for x in roi):return insufficient("invalid_normalized_roi",stats)
        x0,y0,x1,y1=roi
        if not 0<=x0<x1<=1 or not 0<=y0<y1<=1:return insufficient("invalid_normalized_roi",stats)
        h,w=target.shape
        yy,xx=np.indices(m.shape)
        target &= (xx+.5>=x0*w)&(xx+.5<x1*w)&(yy+.5>=y0*h)&(yy+.5<y1*h)
    if target.any() and valid[target].mean()<.98:return insufficient("valid_window_coverage_below_98pct",stats)
    target &= valid
    if target.sum()<64:return insufficient("too_few_target_pixels",stats)
    ys,xs=np.where(union)
    h,w=union.shape;yy,xx=np.indices((h,w))
    # Limit reference distance and keep separate from immediate roof edges.
    pad=max(16,round(.55*max(np.ptp(xs),np.ptp(ys))))
    near=(yy>=ys.min()-pad)&(yy<=ys.max()+pad)&(xx>=xs.min()-pad)&(xx<=xs.max()+pad)
    ref=near & valid & ~binary_dilation(union,iterations=max(3,round(.02*min(h,w))))
    # The validation split holds out spatial blocks, not random pixels.
    block=max(8,round(min(h,w)/12))
    hold=((xx//block+2*(yy//block))%3)==0
    train=ref & ~hold; test=ref & hold
    sectors=2*(yy>=(ys.min()+ys.max())/2)+(xx>=(xs.min()+xs.max())/2)
    supported=[k for k in range(4) if (test&(sectors==k)).sum()>=64]
    stats.update(reference_n=int(ref.sum()),target_n=int(target.sum()),held_out_n=int(test.sum()),supported_sectors=supported)
    if train.sum()<384 or test.sum()<256 or len(supported)<3:return insufficient("reference_area_or_spread",stats)
    train_ids=np.flatnonzero(train)
    train_ids=train_ids[::max(1,int(np.ceil(len(train_ids)/8000)))]
    arr_a=a.reshape(-1,3)[train_ids];arr_b=b.reshape(-1,3)[train_ids]
    fits=[fit_channel(arr_a[:,c],arr_b[:,c]) for c in range(3)]
    if any(f is None for f in fits):return insufficient("unstable_channel_fit",stats)
    gain,offset=np.asarray(fits).T
    predicted=np.clip(a*gain+offset,0,255)
    residual=np.abs(b-predicted).max(axis=2)
    reference_p90=float(np.quantile(residual[test],.90))
    sector_support=[float((residual[test&(sectors==k)]<=14).mean()) for k in supported]
    stats.update(gain=np.round(gain,4).tolist(),offset=np.round(offset,3).tolist(),
                 reference_p90=round(reference_p90,3),held_out_inlier_by_sector=np.round(sector_support,3).tolist())
    if reference_p90>12 or min(sector_support)<.82:return insufficient("surroundings_not_consistent",stats)
    threshold=max(16,2.5*reference_p90)
    changed=target & (residual>threshold)
    component_ids,count=label(changed,structure=np.ones((3,3),dtype=np.uint8))
    largest=int(np.bincount(component_ids.ravel())[1:].max()) if count else 0
    raw_delta=np.abs(b-a).max(axis=2)
    raw=float(np.median(raw_delta[target]))
    modeled=float(np.median(np.abs(predicted-a).max(axis=2)[target]))
    stats.update(raw_target_median=round(raw,2),modeled_target_median=round(modeled,2),
                 residual_target_p90=round(float(np.quantile(residual[target],.90)),2),threshold=round(threshold,2),
                 largest_residual_component_px=largest,affected_fraction=round(float(changed.sum()/target.sum()),4))
    if largest>=max(24,int(np.ceil(.025*target.sum()))):
        return {"status":"local_residual","note_zh":"周边颜色映射后，目标选区仍有一片连续的色差。","measurements":stats}
    if raw>=8 and modeled>=6:
        return {"status":"consistent_with_surroundings","note_zh":"目标选区的主要色变与周边拟合的颜色映射相符。","measurements":stats}
    return {"status":"no_clear_residual","note_zh":"当前阈值下未见足够大的连续局部色差。","measurements":stats}


def assess_case(row,folder,region=None,*,expected_hashes=None):
    base=Path(folder)
    if not row.get("pre_image_path"):return insufficient("single_period",{})
    source_ids={}; planes={}; validity={}; geogrids={}; roi=None
    def read(k,mode):
        data=(base/row[k+"_path"]).read_bytes()
        digest=hashlib.sha256(data).hexdigest()
        source_ids[k+"_sha256"]=digest
        for metadata in (row,expected_hashes or {}):
            if k+"_sha256" in metadata and metadata[k+"_sha256"]!=digest:
                raise ValueError("source_identity_mismatch")
        with Image.open(BytesIO(data)) as img:
            if img.getexif().get(274,1)!=1:raise ValueError("unverified_exif_coordinate_system")
            if k.endswith("mask") and img.mode not in ("1","L","I","I;16"):
                raise ValueError("ambiguous_mask_channels")
            if k.endswith("image") and img.mode not in ("RGB","L"):
                raise ValueError("unsupported_color_or_alpha_plane")
            return img.convert(mode)
    try:
        for phase in ("pre_",""):
            planes[phase]=read(phase+"image","RGB")
            planes[phase+"m"]=read(phase+"mask","L")
            path=base/row[phase+"image_path"]
            valid_key=phase+"valid_mask"
            supplied=read(valid_key,"L") if row.get(valid_key+"_path") else None
            masks=[]
            if supplied is not None:masks.append(np.asarray(supplied)>0)
            sidecar=Path(str(path)+".msk")
            if path.suffix.lower() in (".tif",".tiff") or sidecar.is_file():
                import rasterio
                if sidecar.is_file():source_ids[phase+"gdal_sidecar_sha256"]=hashlib.sha256(sidecar.read_bytes()).hexdigest()
                with rasterio.open(path) as ds:
                    if ds.crs:geogrids[phase]=(ds.crs,ds.transform)
                    flags=[flag.name for band in ds.mask_flag_enums for flag in band]
                    if any(flag!="all_valid" for flag in flags):
                        masks.append(np.all(ds.read_masks()>0,axis=0))
                if hashlib.sha256(path.read_bytes()).hexdigest()!=source_ids[phase+"image_sha256"]:
                    raise ValueError("source_changed_during_read")
            if not masks:raise ValueError("source_valid_mask_unverified")
            if any(m.shape!=(planes[phase].height,planes[phase].width) for m in masks):
                raise ValueError("validity_grid_mismatch")
            from evidence import edge_band
            good=np.logical_and.reduce(masks) & ~edge_band(np.asarray(planes[phase]))
            validity[phase]=Image.fromarray(good.astype("uint8")*255)
        if geogrids and geogrids.get("pre_")!=geogrids.get(""):raise ValueError("source_geogrids_differ")
        if region is not None:
            boxes=[region.get(key) for key in ("pre_xyxy","post_xyxy")]
            if region.get("coords")!="normalized_original_image" or any(
                not isinstance(box,(list,tuple)) or len(box)!=4 or not all(finite_number(x) for x in box)
                or not 0<=box[0]<box[2]<=1 or not 0<=box[1]<box[3]<=1 for box in boxes):
                raise ValueError("invalid_pair_of_source_windows")
            left=max(box[0] for box in boxes);top=max(box[1] for box in boxes)
            right=min(box[2] for box in boxes);bottom=min(box[3] for box in boxes)
            shared_area=max(0,right-left)*max(0,bottom-top)
            if any(shared_area<.75*(box[2]-box[0])*(box[3]-box[1]) for box in boxes):
                raise ValueError("evidence_windows_not_colocated")
            roi=[left,top,right,bottom]
        result=assess(planes["pre_"],planes[""],planes["pre_m"],planes["m"],
                      pre_valid=validity["pre_"],post_valid=validity[""],same_grid=row.get("same_pixel_grid"),
                      registration_error_px=row.get("registration_error_px"),coverage_fraction=row.get("coverage_fraction"),
                      pre_coverage_fraction=row.get("pre_coverage_fraction"),roi=roi)
    except (OSError,ImportError,KeyError,TypeError,ValueError) as exc:
        reason=str(exc) if isinstance(exc,ValueError) else type(exc).__name__
        result=insufficient(reason,{})
    result.update(source_hashes=source_ids,evidence_region=region,compared_common_xyxy=roi)
    return result


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--cases",type=Path,required=True)
    p.add_argument("--output",type=Path,required=True)
    args=p.parse_args()
    from verify_target import indexed,save
    save(args.output,({"building_id":k,**assess_case(row,args.cases.parent)} for k,row in indexed(args.cases).items()))
