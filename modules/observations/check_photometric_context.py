"""Use one actual post image per building to create exact paired color/context controls."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import numpy as np
from PIL import Image
from scipy.ndimage import distance_transform_edt
from photometric_context import assess

TRUTH={"same":"no_clear_residual","exposure":"consistent_with_surroundings","color_cast":"consistent_with_surroundings",
       "inside":"local_residual","exposure_plus_inside":"local_residual","invalid_reference":"reference_insufficient",
       "incompatible_context":"reference_insufficient","unverified_alignment":"reference_insufficient"}


def cases_for(im,mask):
    rgb=np.asarray(im).astype("float64");m=np.asarray(mask)>127
    yy,xx=np.indices(m.shape)
    distance=distance_transform_edt(m)
    cy,cx=np.unravel_index(np.argmax(distance),distance.shape)
    rad=min(.85*distance[cy,cx],np.sqrt(.105*m.sum()/np.pi))
    patch=(xx-cx)**2+(yy-cy)**2<=rad**2
    assert np.all(m[patch]) and patch.sum()>=24
    def to_image(a):return Image.fromarray(np.clip(np.rint(a),0,255).astype("uint8"))
    def edit(a):
        result=a.copy()
        result[patch]=np.where(result[patch]<128,result[patch]+60,result[patch]-60)
        return result
    bright=np.clip(1.07*rgb+17,0,255)
    colored=np.clip(rgb*np.array([1.05,.96,1.10])+np.array([22,-19,14]),0,255)
    # Strong spatially inconsistent context makes one common reference transform unsupported.
    tiles=(yy//25+xx//35)%2
    mixed=np.where(tiles[...,None]>0,rgb+37,rgb-37)
    for name,arr in (("same",rgb),("exposure",bright),("color_cast",colored),("inside",edit(rgb)),
                     ("exposure_plus_inside",edit(bright)),("invalid_reference",bright),
                     ("incompatible_context",np.where(m[...,None],rgb,mixed)),("unverified_alignment",bright)):
        valid=Image.fromarray(m.astype("uint8")*255) if name=="invalid_reference" else None
        yield name,to_image(arr),valid,name!="unverified_alignment",int(patch.sum())


def run(cases,output):
    rows=[json.loads(s) for s in cases.read_text(encoding="utf-8-sig").splitlines() if s.strip()]
    from run_roofs import inspect_case
    details=[];groups={};selected={}
    for row in rows:
        source=cases.parent/row["image_path"]
        with Image.open(source) as pic, Image.open(cases.parent/row["mask_path"]) as footprint:
            image=pic.convert("RGB");mask=footprint.convert("L")
        for name,post,valid,same,patch in cases_for(image,mask):
            tested=assess(image,post,mask,mask,same_grid=same,registration_error_px=0. if same else None,
                          pre_valid=valid,post_valid=valid,coverage_fraction=1.,pre_coverage_fraction=1.)
            with TemporaryDirectory() as tmp:
                folder=Path(tmp)
                image.save(folder/"pre.png");post.save(folder/"post.png");mask.save(folder/"mask.png")
                (valid or Image.new("L",image.size,255)).save(folder/"valid.png")
                case=dict(building_id=row["building_id"],pre_image_path="pre.png",image_path="post.png",
                          mask_path="mask.png",pre_mask_path="mask.png",pre_valid_mask_path="valid.png",valid_mask_path="valid.png",
                          same_pixel_grid=same,registration_error_px=0. if same else None,coverage_fraction=1.,pre_coverage_fraction=1.)
                observation=inspect_case(case,folder,photometric_context=True)
                window=observation["photometric_context"]
            good=int(window["status"]==TRUTH[name])
            count=selected.setdefault(name,Counter())
            count.update(n=1,correct=good);count[window["status"]]+=1
            if "reason" in window:count["reason/"+window["reason"]]+=1
            m=np.asarray(mask)>127
            diff=np.abs(np.asarray(post).astype(float)-np.asarray(image).astype(float)).max(axis=-1)
            raw_ratio=float(np.mean(diff[m]>16))
            raw_call=bool(raw_ratio>=.025)
            counts=groups.setdefault(name,Counter())
            counts.update(n=1,correct=int(tested["status"]==TRUTH[name]),naive_target_change=int(raw_call))
            counts[tested["status"]]+=1
            details.append(dict(building_id=row["building_id"],source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
                                synthetic=name,expected=TRUTH[name],edit_pixels=patch if name in ("inside","exposure_plus_inside") else 0,
                                raw_fraction=raw_ratio,raw_threshold_call=raw_call,selected_window=window,
                                observation_status=observation["status"],observation_region=observation.get("evidence_region"),
                                **tested))
    report={"source_manifest_sha256":hashlib.sha256(cases.read_bytes()).hexdigest(),
            "code_sha256":hashlib.sha256(Path(__file__).with_name("photometric_context.py").read_bytes()).hexdigest(),
            "whole_footprint_groups":groups,"product_selected_window_groups":selected,"rows":details}
    with output.open("x",encoding="utf8") as f:json.dump(report,f,indent=2,ensure_ascii=False)
    print(json.dumps(groups));print(json.dumps(selected))


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--cases",required=True,type=Path);p.add_argument("--output",required=True,type=Path)
    a=p.parse_args()
    run(a.cases,a.output)
