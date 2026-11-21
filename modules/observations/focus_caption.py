"""Generate footprint-level and local visual observations, optionally using a train-only case bank."""
import argparse
import json
import os
import time
from pathlib import Path
from tempfile import NamedTemporaryFile
import numpy as np
from PIL import Image
from scipy.ndimage import uniform_filter

import ground_caption as baseline
from retrieval import retrieve
from cue_questions import questions


PAIRED = """依次是同栋灾前全图、灾后全图、灾前选区和灾后同一选区。灰色遮罩无图像内容。前两张只提供上下文，结论落在后两张的屋面内。先逐图找同一处可辨的色块、轮廓交界或纹理，再用一至两句中文比较它在前后如何呈现。如果只改变清晰度、整体光照或轻微位置，说明判读限制；仅据颜色或纹理差异不能确定损坏原因、材料或结构状态。若仍然一致，写出保留的可见特征。方位前缀由系统另行添加。只输出JSON，state取changed/stable/uncertain，sentence为一句或两句中文。"""
STATIC = """照片是同栋建筑及该栋一个局部。请在第二张图中找到屋面上最清楚的大色块、条纹或边界，用一句中文描述形态和颜色。首图只用来理解局部位置；灰色遮罩不是屋面。细节模糊时说明能辨出什么。请避免猜测材料、构件、裂缝和受损原因。只输出该句话。"""


def choose(before, after):
    post = baseline.canonical(after)
    if before:
        diff, valid, dx, dy = baseline.align(baseline.canonical(before), post)
        signal = np.minimum(diff, 150)
    else:
        valid = post[1]
        rgb = post[0]
        blur = uniform_filter(rgb, size=(9,9,1))
        signal = np.abs(rgb-blur).mean(axis=2)
        dx=dy=0
    ranked=[]
    for size in (12,24,40):
        coverage=uniform_filter(valid.astype(float),size=size,mode="constant")
        local=uniform_filter(np.where(valid,signal,0.),size=size,mode="constant") / np.maximum(coverage,.01)
        eligible=valid & (coverage>=.60)
        if eligible.any():
            weights=np.where(eligible,local,-np.inf)
            y,x=np.unravel_index(np.argmax(weights),weights.shape)
            ranked.append((float(weights[y,x])*(1+.07*np.log2(size/12)),int(x),int(y),size,float(weights[y,x])))
    if not ranked:
        raise ValueError("No sufficiently covered local window")
    _,x,y,size,magnitude=max(ranked)
    half=max(14,round(size*.85))
    def coords(cx,cy):
        return (max(0,cx-half),max(0,cy-half),min(128,cx+half+1),min(128,cy+half+1))
    name=("top" if y<64 else "bottom")+("_left" if x<64 else "_right")
    return name,coords(x,y),coords(x-dx,y-dy),dict(local_mean=round(magnitude,4),scale=size,
             shift_xy=[dx,dy],peak_xy=[x,y],low_difference=bool(before and magnitude<12))


def window(phase,c):
    l,t,r,b=phase["bbox"]
    w,h=phase["rgb"].size
    x0,y0,x1,y1=c
    xy=(l+int(np.floor(x0*(r-l)/128)),t+int(np.floor(y0*(b-t)/128)),
        l+int(np.ceil(x1*(r-l)/128)),t+int(np.ceil(y1*(b-t)/128)))
    return phase["rgb"].crop(xy),[round(v/s,6) for v,s in zip(xy,(w,h,w,h))],xy


def run(case,folder,model,processor,rag=False,*,method=None,library=None,retriever=None):
    method=method or ("rag" if rag else "focus")
    if method not in {"focus","rag","cue"}:
        raise ValueError("Unknown caption method")
    start=time.monotonic()
    row=dict(building_id=case["building_id"],model=baseline.MODEL_NAME,method=method,
             status="inference_error",change_status="uncertain",explanation_zh="",retrieval_used=False,
             injected_context_zh="",fallback_reason=None,
             retrieval={"matches":[],"index_sha256":None,"context_zh":"","reason":"not_requested" if method=="focus" else "not_run"})
    try:
        post,hashes=baseline.load_phase(folder,case,"")
        row.update(hashes)
        pre=None
        if case.get("pre_image_path"):
            pre,hashes=baseline.load_phase(folder,case,"pre_")
            row.update(hashes)
        if min(case.get("coverage_fraction",1.),case.get("pre_coverage_fraction",1.))<.98:
            raise ValueError("Insufficient source coverage")
        name,c,p,metrics=choose(pre,post)
        current,post_box,xy=window(post,c)
        region=dict(name=name,post_xyxy=post_box,coords="normalized_original_image")
        row.update(evidence_region=region,comparison=metrics)
        if pre:
            earlier,region["pre_xyxy"],_=window(pre,p)
        context=""
        if method in {"rag","cue"}:
            # Use one query grid with matched target extents when pre/post masks differ.
            query_post=post["rgb"].crop(post["bbox"])
            mask=post["mask"].crop(post["bbox"])
            query_pre=None
            if pre:
                query_pre=pre["rgb"].crop(pre["bbox"]).resize(query_post.size,Image.Resampling.BILINEAR)
                before_mask=pre["mask"].crop(pre["bbox"]).resize(query_post.size,Image.Resampling.NEAREST)
                mask=Image.fromarray(np.minimum(np.asarray(mask),np.asarray(before_mask)))
            l,t,_,_=post["bbox"]
            roi=(xy[0]-l,xy[1]-t,xy[2]-l,xy[3]-t)
            try:
                search=retrieve if retriever is None else retriever
                found=search(query_pre,query_post,mask,roi,case,library_path=library)
            except FileNotFoundError:
                found={"matches":[],"context_zh":"","reason":"library_missing","index_sha256":None}
            row["retrieval"]=found
            context=found["context_zh"]
            if context and method=="cue":
                context=questions(found["matches"][0]["caption_zh"])
                if pre is None or metrics["low_difference"]:
                    context=context.replace("同一处轮廓在两期能对准吗？","选区边缘能清楚区分吗？")
                row["cue_context"]=context
            row["retrieval_used"]=bool(context)
            row["injected_context_zh"]=context
            row["fallback_reason"]=None if context else (found["reason"] if not found["matches"] else "no_observation_question")
        low=metrics["low_difference"]
        if not pre or low:
            views=[("当期屋面",post["rgb"].crop(post["bbox"])),("当期局部",current)]
            prompt=STATIC
            route="stable_local_comparison" if pre else "single_observation"
        else:
            views=[("灾前全栋",pre["rgb"].crop(pre["bbox"])),("灾后全栋",post["rgb"].crop(post["bbox"])),
                   ("灾前选区",earlier),("灾后选区",current)]
            prompt=PAIRED
            route="paired_observation"
        if context: prompt=context+"\n\n"+prompt
        row.update(route=route,prompt_sha256=baseline.sha(prompt.encode()))
        raw=baseline.generate(model,processor,views,prompt)
        row["raw_candidate"]=raw
        if route=="paired_observation":
            answer=baseline.parse(raw)
            state,text=answer["state"],answer["sentence"]
        else:
            state="stable" if pre else "single"
            text=raw+(" 两期对齐后，这一局部的平滑颜色差异较小。" if low else "")
        row.update(status="ok",change_status=state,explanation_zh="建筑范围"+baseline.SECTORS[name][0]+"区域："+text)
    except (KeyError, ValueError, OSError, TypeError, RuntimeError) as exc:
        row["error"]=f"{type(exc).__name__}: {exc}"
    row["seconds"]=round(time.monotonic()-start,4)
    return row


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--model",type=Path,required=True)
    p.add_argument("--cases",type=Path,nargs="+",required=True)
    p.add_argument("--output-dir",type=Path,required=True)
    p.add_argument("--method",choices=("focus","rag","cue"),nargs="+",default=["focus"])
    p.add_argument("--library",type=Path,help="Path to a compatible training-only case index")
    a=p.parse_args()
    import torch
    from transformers import AutoModelForImageTextToText, AutoProcessor
    processor=AutoProcessor.from_pretrained(a.model,local_files_only=True)
    model=AutoModelForImageTextToText.from_pretrained(a.model,local_files_only=True,dtype=torch.bfloat16,
           attn_implementation="sdpa").to("cuda").eval()
    a.output_dir.mkdir(parents=True,exist_ok=True)
    for cases in a.cases:
        inputs=[json.loads(s) for s in cases.read_text(encoding="utf-8-sig").splitlines() if s.strip()]
        ids=[r["building_id"] for r in inputs]
        if not ids or len(set(ids))!=len(ids): raise ValueError("Unique, nonempty input required")
        for method in a.method:
            prefix="stress-" if cases.parent.name=="stress" else ""
            path=a.output_dir/(prefix+method+".jsonl")
            if path.exists(): raise FileExistsError(path)
            with NamedTemporaryFile(mode="w",encoding="utf8",dir=a.output_dir,delete=False) as f:
                tmp=Path(f.name)
                try:
                    for case in inputs:
                        row=run(case,cases.parent,model,processor,method=method,library=a.library)
                        print(json.dumps(row,ensure_ascii=False,allow_nan=False),file=f,flush=True)
                        print(path.name,row["building_id"],row["status"],flush=True)
                    f.close()
                    os.link(tmp,path)
                finally:
                    f.close()
                    tmp.unlink(missing_ok=True)


if __name__=="__main__":
    main()
