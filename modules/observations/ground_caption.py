"""Generate footprint-grounded visual observations using Qwen3-VL and a reproducible evidence window."""
import argparse
import hashlib
from io import BytesIO
import json
import os
from pathlib import Path
import re
from tempfile import NamedTemporaryFile
import time

import numpy as np
from PIL import Image, ImageFilter, ImageOps
from scipy.ndimage import binary_erosion, gaussian_filter

MODEL_NAME = "Qwen/Qwen3-VL-4B-Instruct"
SECTORS = {"top_left": ("左上",0,0), "top_right": ("右上",1,0),
           "bottom_left": ("左下",0,1), "bottom_right": ("右下",1,1)}
STATIC = """灰色底是去除建筑以外内容的位置，不能当作建筑像素。图中只有建筑的一个局部。用一句简短中文只描述该局部最清楚的颜色、连续的面、明暗条或纹理；模糊时说明难以区分的细节。不得推断材料、裂纹成因、建筑安全、整栋完好或损毁。不要描述青色线、灰色底、邻栋或图片框。只输出这句话。"""
PAIRED = """这是同一栋建筑同一局部的灾前、灾后图。灰色为被遮去的信息，不是建筑。比较可辨认的较大色块、条带或纹理，用一至两句中文指出同一可见特征在两图中是否保留、不同或无法辨认。颜色变化不能直接用于判断破坏程度。禁止臆测材料、原因及整栋状况。只返回 JSON，键 state 取 changed/stable/uncertain，sentence 为中文。"""
VERIFY = """根据图像核对下面的候选观察。前两图是蒙掉建筑范围以外内容的全目标（灾前、灾后），后两图是选中局部的放大图（同样顺序）。仅核对选中局部；图框或灰底、青线不能作为证据。若能核实差异，指出哪个可见特征原来怎样、现在怎样；仅平移、清晰度差异或无法看清的不能归为建筑变化。删除无法核对的细节或归因；可判稳定或待核。只输出 JSON，state 取 changed/stable/uncertain，sentence 为一至两句经过核对的中文目视描述。候选观察："""

def sha(b):
    return hashlib.sha256(b).hexdigest()


def load_phase(root, row, prefix):
    records={}
    images=[]
    for kind,mode in (("image","RGB"),("mask","L")):
        k=prefix+kind
        data=(root/row[k+"_path"]).read_bytes()
        records[k+"_sha256"]=sha(data)
        with Image.open(BytesIO(data)) as im:
            images.append(ImageOps.exif_transpose(im).convert(mode))
    rgb, mask=images
    if mask.size != rgb.size:
        raise ValueError("Image and footprint sizes differ")
    mask=mask.point(lambda x:255 if x>=128 else 0)
    bbox=mask.getbbox()
    if bbox is None or min(bbox[2]-bbox[0],bbox[3]-bbox[1]) < 4:
        raise ValueError("Footprint is empty or has insufficient pixels")
    rgb=Image.composite(rgb,Image.new("RGB",rgb.size,(127,127,127)),mask)
    return {"rgb":rgb,"mask":mask,"bbox":bbox}, records


def canonical(phase):
    rgb=phase["rgb"].crop(phase["bbox"]).resize((128,128),Image.Resampling.BILINEAR)
    mask=phase["mask"].crop(phase["bbox"]).resize((128,128),Image.Resampling.NEAREST)
    return gaussian_filter(np.asarray(rgb,dtype=float),(2,2,0)),binary_erosion(np.asarray(mask)>0,iterations=4)


def align(pre,post):
    old,mask=pre
    new,valid=post
    best=None
    for dy in range(-6,7,2):
        for dx in range(-6,7,2):
            pair=np.roll(old,(dy,dx),axis=(0,1))
            region=valid & np.roll(mask,(dy,dx),axis=(0,1))
            region[:6,:]=region[-6:,:]=False
            region[:,:6]=region[:,-6:]=False
            if region.sum()<96:continue
            diff=np.abs(pair-new).mean(axis=2)
            objective=float(np.minimum(diff[region],45).mean())+.12*(abs(dx)+abs(dy))
            if best is None or objective < best[0]:
                best=(objective,diff,region,dx,dy)
    if best is None:
        raise ValueError("Too little common footprint area")
    return best[1:]


def select_region(phase, before=None):
    canonical_post=canonical(phase)
    pixel,valid=canonical_post
    difference=None; shift=[0,0]
    if before:
        difference,valid,dx,dy=align(canonical(before),canonical_post)
        shift=[dx,dy]
    stats=[]
    for name,(_,x,y) in SECTORS.items():
        sl=np.s_[y*64:(y+1)*64,x*64:(x+1)*64]
        hits=valid[sl]
        if hits.sum()<max(32,min(256,valid.sum()//12)): continue
        texture=float(np.std(pixel[sl][hits],axis=0).mean())
        quantiles=np.quantile(difference[sl][hits],[.75,.90]) if difference is not None else [0.,0.]
        q75,q90=map(float,quantiles)
        salience=(q75+.35*q90) if before else texture
        stats.append((salience,name,q75,q90,texture))
    if not stats: raise ValueError("Footprint too sparse for evidence regions")
    _,name,q75,q90,texture=max(stats,key=lambda r:r[0])
    low=before is not None and q75<12 and q90<24
    return name, low, dict(q75=round(q75,2),q90=round(q90,2),canonical_shift=shift,texture=round(texture,2))


def window(phase, name):
    left,top,right,bottom=phase["bbox"]
    _,x,y=SECTORS[name]
    xm=(left+right)//2;ym=(top+bottom)//2
    box=(xm if x else left,ym if y else top,right if x else xm,bottom if y else ym)
    w,h=phase["rgb"].size
    return phase["rgb"].crop(box),[round(float(a/b),6) for a,b in zip(box,(w,h,w,h))]


def vision_size(im):
    im=im.copy()
    im.thumbnail((482,482),Image.Resampling.LANCZOS)
    if min(im.size)<160:
        scale=min(160/min(im.size),482/max(im.size))
        if scale>1: im=im.resize(tuple(max(1,round(v*scale)) for v in im.size),Image.Resampling.BILINEAR)
    return im


def generate(model,processor,images,text):
    import torch
    parts=[]
    for caption,im in images:
        parts.extend([{"type":"text","text":caption},{"type":"image","image":vision_size(im)}])
    parts.append({"type":"text","text":text})
    batch=processor.apply_chat_template([{"role":"user","content":parts}],tokenize=True,
                  add_generation_prompt=True,return_tensors="pt",return_dict=True).to(model.device)
    with torch.inference_mode():
        output=model.generate(**batch,max_new_tokens=190,do_sample=False)
    result=processor.decode(output[0,batch.input_ids.shape[1]:],skip_special_tokens=True).strip()
    if not re.search(r"[\u3400-\u9fff]",result):raise ValueError("No Chinese observation")
    return result


def parse(raw):
    stripped=re.sub(r"^\s*`{3}(?:json)?\s*|\s*`{3}\s*$","",raw,flags=re.I)
    item=json.loads(stripped)
    if item.get("state") not in ("changed","stable","uncertain") or not isinstance(item.get("sentence"),str) or not re.search(r"[\u3400-\u9fff]",item["sentence"]):
        raise ValueError("Invalid observation schema")
    return item


def run_case(row,directory,model,processor):
    result={"building_id":row["building_id"],"model":MODEL_NAME,"status":"inference_error","change_status":"uncertain","explanation_zh":""}
    start=time.monotonic()
    try:
        post,hashes=load_phase(directory,row,"");result.update(hashes)
        before=None
        if row.get("pre_image_path"):
            before,hashes=load_phase(directory,row,"pre_");result.update(hashes)
        if float(row.get("coverage_fraction",1.0))<.98:raise ValueError("Insufficient target image coverage")
        name,low,metrics=select_region(post,before)
        local,post_box=window(post,name)
        region=dict(name=name,coords="normalized_original_image",post_xyxy=post_box)
        if before:
            prior,region["pre_xyxy"]=window(before,name)
        result.update(evidence_region=region,comparison=metrics)
        if not before or low:
            raw=generate(model,processor,[("当期选中局部",local)],STATIC)
            text=raw;state="single" if not before else "stable"
            if low: text+=" 两期对应局部的平滑色块对比未检出明显差异。"
            result["raw_candidate"]=raw
        else:
            focus=[("灾前局部",prior),("灾后局部",local)]
            raw=generate(model,processor,focus,PAIRED)
            result["raw_candidate"]=raw
            verification=generate(model,processor,[("灾前全目标",before["rgb"].crop(before["bbox"])),("灾后全目标",post["rgb"].crop(post["bbox"]))]+focus,VERIFY+raw)
            result["raw_verification"]=verification
            answer=parse(verification)
            text,state=answer["sentence"],answer["state"]
        result.update(status="ok",explanation_zh="建筑范围"+SECTORS[name][0]+"区域："+text,change_status=state)
    except (ValueError,OSError,RuntimeError,KeyError,TypeError) as error:
        result["error"]=f"{type(error).__name__}: {error}"
    result["seconds"]=round(time.monotonic()-start,3)
    return result


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for key in ("cases","output","model"):p.add_argument("--"+key,type=Path,required=True)
    args=p.parse_args()
    rows=[json.loads(l) for l in args.cases.read_text(encoding="utf-8-sig").splitlines() if l.strip()]
    keys=[r["building_id"] for r in rows]
    if args.output.exists() or not rows or len(keys)!=len(set(keys)):p.error("New output and unique nonempty cases required")
    import torch
    from transformers import AutoModelForImageTextToText, AutoProcessor
    processor=AutoProcessor.from_pretrained(args.model,local_files_only=True)
    model=AutoModelForImageTextToText.from_pretrained(args.model,local_files_only=True,dtype=torch.bfloat16,attn_implementation="sdpa").to("cuda").eval()
    args.output.parent.mkdir(parents=True,exist_ok=True)
    with NamedTemporaryFile(dir=args.output.parent,delete=False,mode="w",encoding="utf8") as f:
        tmp=Path(f.name)
        try:
            for row in rows:
                result=run_case(row,args.cases.parent,model,processor)
                print(json.dumps(result,ensure_ascii=False,allow_nan=False),file=f,flush=True)
                print(row["building_id"],result["status"],result["seconds"],flush=True)
            f.close();os.link(tmp,args.output)
        finally:
            f.close();tmp.unlink(missing_ok=True)
if __name__=="__main__":main()
