"""Produce a single atomic manifest of target-verified observations from an external case bank."""
import argparse
import json
from pathlib import Path
import time

import numpy as np
from PIL import Image
from evidence import base,focus,measure
from verify_target import indexed,locked_check,model_on,save


def reference(case,folder,region,library):
    post,_=base.load_phase(folder,case,"")
    image=post["rgb"].crop(post["bbox"])
    mask=post["mask"].crop(post["bbox"])
    old_image=None
    if case.get("pre_image_path"):
        pre,_=base.load_phase(folder,case,"pre_")
        old_image=pre["rgb"].crop(pre["bbox"]).resize(image.size,Image.Resampling.BILINEAR)
        old_mask=pre["mask"].crop(pre["bbox"]).resize(image.size,Image.Resampling.NEAREST)
        mask=Image.fromarray(np.minimum(np.asarray(mask),np.asarray(old_mask)))
    left,top,_,_=post["bbox"]
    xy=[round(v*s)-offset for v,s,offset in zip(region["post_xyxy"],post["rgb"].size*2,(left,top,left,top))]
    try:
        return focus.retrieve(old_image,image,mask,xy,case,library_path=library)
    except FileNotFoundError:
        return {"matches":[],"context_zh":"","reason":"library_missing","index_sha256":None}


def run(case,folder,model,proc,cards,library,source=None):
    start=time.monotonic()
    if source is not None and source["building_id"]!=case["building_id"]:
        raise ValueError("Expected source from the same building")
    observed=measure(case,folder,source.get("evidence_region") if source else None)
    if observed["status"]!="ok":
        return {**observed,"method":"verify","render_mode":"quality_gate","seconds":round(time.monotonic()-start,4)}
    if source is None:
        found=reference(case,folder,observed["evidence_region"],library)
        source={"building_id":case["building_id"],"retrieval":found,"explanation_zh":""}
        route="target_and_external_case"
    else:
        for phase in ("","pre_"):
            for kind in ("image","mask"):
                key=phase+kind+"_sha256"
                if source.get(key)!=observed.get(key):raise ValueError("RAG source input mismatch: "+key)
        route="existing_rag_draft"
    row=locked_check(case,folder,source,observed,model,proc,cards)
    row.update(entry_route=route,base_draft=source["explanation_zh"],base_raw=source.get("raw_candidate"),
               retrieval_reason=source["retrieval"]["reason"],seconds=round(time.monotonic()-start,4))
    return row


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for k in ("cases","output","model"):
        p.add_argument("--"+k,type=Path,required=True)
    for k in ("cards","library","source"):
        p.add_argument("--"+k,type=Path)
    a=p.parse_args()
    if a.output.exists():raise FileExistsError(a.output)
    cases=indexed(a.cases);source=indexed(a.source) if a.source else {}
    if source and source.keys()!=cases.keys():raise ValueError("RAG/cases manifest ID mismatch")
    cards=json.loads(a.cards.read_bytes()) if a.cards else {}
    model,proc=model_on(a.model)
    def rows():
        for k,case in cases.items():
            row=run(case,a.cases.parent,model,proc,cards,a.library,source.get(k))
            print(k,row["status"],flush=True)
            yield row
    save(a.output,rows())


if __name__=="__main__":
    main()
