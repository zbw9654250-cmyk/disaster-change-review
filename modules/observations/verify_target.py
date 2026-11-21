"""Replay a retrieved draft against measured and visually checked evidence from the target."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import random
import re
import time
from tempfile import NamedTemporaryFile

from evidence import base, focus, measure


def source_views(case,folder,region):
    views=[]
    for prefix,label,box in (("pre_","灾前","pre_xyxy"),("","灾后","post_xyxy")):
        if not case.get(prefix+"image_path"): continue
        ph,_=base.load_phase(folder,case,prefix)
        rgb=ph["rgb"]
        pixel=tuple(round(v*n) for v,n in zip(region[box],rgb.size*2))
        views.append((label+"目标整栋",rgb.crop(ph["bbox"])))
        views.append((label+"屋面同一选区",rgb.crop(pixel)))
    return views


def parse_json(text):
    s=re.sub(r"^\s*`{3}(?:json)?\s*|\s*`{3}\s*$","",text,flags=re.I)
    obj=json.loads(s)
    if not isinstance(obj,dict): raise ValueError("Expected JSON object")
    return obj


def model_on(path):
    import torch
    from transformers import AutoModelForImageTextToText,AutoProcessor
    return (AutoModelForImageTextToText.from_pretrained(path,local_files_only=True,dtype=torch.bfloat16,
            attn_implementation="sdpa").to("cuda").eval(),AutoProcessor.from_pretrained(path,local_files_only=True))


def digest(text):
    return hashlib.sha256(text.encode()).hexdigest()


def indexed(path):
    rows=[json.loads(s) for s in path.read_text(encoding="utf-8-sig").splitlines() if s.strip()]
    keys=[r["building_id"] for r in rows]
    if not keys or len(set(keys))!=len(keys): raise ValueError("Expected nonempty unique case IDs")
    return dict(zip(keys,rows))


def save(path,rows):
    path.parent.mkdir(parents=True,exist_ok=True)
    if path.exists(): raise FileExistsError(path)
    with NamedTemporaryFile("w",dir=path.parent,encoding="utf8",delete=False) as f:
        tmp=Path(f.name)
        try:
            for row in rows: print(json.dumps(row,ensure_ascii=False,allow_nan=False),file=f)
            f.close(); os.link(tmp,path)
        finally:
            f.close(); tmp.unlink(missing_ok=True)


def free_check(case,folder,old,meas,model,proc):
    prompt=("核实同一建筑局部的可见外观。只采纳两期目标图可复查的变化。旧说明中不受支持的特征应删去，"
            "严禁猜测材料、损坏机理、结构安全或别栋情况。用一到两句中文具体写本栋选区的色块、明暗或纹理。"
            "只输出JSON，state是changed/stable/uncertain/single，sentence是你的中文观察。旧说明："+old["explanation_zh"])
    raw=base.generate(model,proc,source_views(case,folder,old["evidence_region"]),prompt)
    val=parse_json(raw)
    return {**meas,"method":"free","model":base.MODEL_NAME,"raw_verification":raw,
            "change_status":val["state"],"explanation_zh":val["sentence"],"prompt_sha256":digest(prompt)}


def as_counterfact(measurements):
    post=measurements["post"]
    pre=measurements.get("pre")
    if pre and abs(post["median_luma"]-pre["median_luma"])>=18:
        reversed_direction="更暗" if post["median_luma"]>pre["median_luma"] else "更亮"
        return "灾后选区主体比灾前"+reversed_direction+"。"
    unlikely="近黑色" if post["median_luma"]>80 else "明亮的白色"
    return "灾后这处选区的主要色调为"+unlikely+"。"


def target_check(case,folder,old,meas,model,proc,cards,swap_views=False):
    measurement=meas["measurement"]
    facts=measurement["facts"]
    hits=old.get("retrieval",{}).get("matches",[])
    card=None
    if hits and cards:
        if old["retrieval"]["index_sha256"]!=cards.get("index_sha256"):
            raise ValueError("Reference card belongs to a different retrieval index")
        card=cards["cases"].get(hits[0]["case_id"])
        if card and card["uid"]!=hits[0]["uid"]:raise ValueError("Reference source UID mismatch")
    refs={f["kind"] for f in (card or {}).get("local_facts",[])}
    labels=[]
    for kind,note in (("color","色调"),("contrast","明暗反差"),("brightness","亮度"),("spatial","选框内部位置")):
        if any(kind in r for r in refs):labels.append(note)
    draft=old.get("explanation_zh","")
    empirical_categories=[name for name,pattern in (("brightness","亮|暗"),("geometry","多边形|轮廓|边界"),
            ("texture","纹理|斑|条"),("causal_or_damage","损坏|结构形态|坍塌|涂层|脱落|污染|覆盖物")) if re.search(pattern,draft)]
    options=[(f["id"],f["text"]) for f in facts]+[("decoy",as_counterfact(measurement))]
    random.Random(digest(case["building_id"]+"|roof-v5")).shuffle(options)
    choices={chr(65+i):obj for i,obj in enumerate(options)}
    prompt=("逐张检查目标建筑的同一选区，外部案例只能提示检查哪种属性。"
            "给出的几项备选观察中可能有看反、看错或在图中看不清的。仅凭本栋照片选择最清楚的一或两项；"
            "两期的整体色调转变通常比细小花纹更容易判断。灰底是遮罩，不属于目标。"
            "候选正文只适用于给定局部，不猜测材料、成因或结构。"
            "返回JSON，choices为最有把握的选项字母列表（不支持时空列表），reason用中文写出你在本栋图上实际看到的依据。"
            +"\n需检查的属性："+("、".join(labels) if labels else "颜色与明暗")+"\n"
            +"\n".join(letter+"　"+text for letter,(_,text) in choices.items()))
    views=source_views(case,folder,meas["evidence_region"])
    if swap_views and len(views)==4:
        views=[(views[i][0],views[(i+2)%4][1]) for i in range(4)]
    mode="visual_fact_selection"
    raw=""
    explanation=""
    picked=[]
    invalid=[]
    try:
        raw=base.generate(model,proc,views,prompt)
        result=parse_json(raw)
        letters=result["choices"]
        if not isinstance(letters,list) or not all(isinstance(x,str) and x in choices for x in letters):
            raise ValueError("Invalid visible fact choice")
        for letter in dict.fromkeys(letters):
            fid,_=choices[letter]
            if fid!="decoy": picked.append(fid)
            else: invalid.append(letter)
        selected=[f for f in facts if f["id"] in picked][:2]
        if selected:
            explanation="".join(f["text"] for f in selected)
            if not explanation.startswith("建筑足迹"):
                explanation="建筑足迹"+measurement["region_zh"]+"的选区内，"+explanation
        else:
            mode="measurement_fallback_no_supported_choice"
    except (ValueError,KeyError,TypeError,RuntimeError) as error:
        mode="measurement_fallback_verifier_error"
        invalid.append(str(error))
    return {**meas,"method":"verify","model":base.MODEL_NAME,"render_mode":mode,
        "explanation_zh":explanation or meas["explanation_zh"],"change_status_basis":"registered_target_measurements",
        "raw_verification":raw,"selected_fact_ids":picked,"rejected_choices":invalid,
        "menu":{k:v[0] for k,v in choices.items()},"counterfactual_text":dict(options)["decoy"],
        "prompt_sha256":digest(prompt),"draft_attribute_types":empirical_categories,
        "source_claim_policy":"draft facts require independent target observations",
        "reference_case":None if not hits else {"case_id":hits[0]["case_id"],"score":hits[0]["score"],
            "reference_attribute_types":sorted(refs),"reference_region":(card or {}).get("evidence_region")},
        "text_provenance":"measured candidate text; verifier selects supported IDs; no free-form reason published"}


def locked_check(case,folder,old,meas,model,proc,cards):
    return target_check(case,folder,old,meas,model,proc,cards)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--cases",type=Path,required=True);p.add_argument("--source",type=Path)
    p.add_argument("--output",type=Path,required=True);p.add_argument("--model",type=Path,required=True)
    p.add_argument("--cards",type=Path);p.add_argument("--library",type=Path)
    p.add_argument("--arm",choices=("free","verify"),required=True);p.add_argument("--prefix",default="")
    args=p.parse_args()
    cases=indexed(args.cases)
    old=indexed(args.source) if args.source else {}
    if args.source and old.keys()!=cases.keys(): raise ValueError("Source IDs must match cases")
    cards=json.loads(args.cards.read_bytes()) if args.cards else {}
    model,proc=model_on(args.model)
    measurements=[];drafts=[];verified=[]
    for k,case in cases.items():
        source=old[k] if args.source else focus.run(case,args.cases.parent,model,proc,method="rag",library=args.library)
        start=time.monotonic()
        m=measure(case,args.cases.parent,source.get("evidence_region"))
        for phase in ("","pre_"):
            for kind in ("image","mask"):
                key=phase+kind+"_sha256"
                if source.get(key)!=m.get(key): raise ValueError(f"{k}: {key} mismatch")
        try:
            if m["status"]!="ok" or source["status"]!="ok":
                result={**m,"method":args.arm,"render_mode":"quality_gate"}
            elif args.arm=="free":
                result=free_check(case,args.cases.parent,source,m,model,proc)
            else:
                result=locked_check(case,args.cases.parent,source,m,model,proc,cards)
        except (TypeError,KeyError,ValueError,RuntimeError,OSError) as exc:
            result={**m,"method":args.arm,"model":base.MODEL_NAME,"render_mode":"verifier_error_measurement","error":str(exc)}
        result["base_draft"]=source["explanation_zh"]
        result["base_raw"]=source.get("raw_candidate")
        result["verification_seconds"]=round(time.monotonic()-start,4)
        result["seconds"]=round(result["verification_seconds"]+source["seconds"],4)
        drafts.append(source);measurements.append(m);verified.append(result)
        print(k,result.get("render_mode","free"),flush=True)
    if not args.source: save(args.output/(args.prefix+"old.jsonl"),drafts)
    save(args.output/(args.prefix+"measure.jsonl"),measurements)
    save(args.output/(args.prefix+args.arm+".jsonl"),verified)


if __name__=="__main__":
    main()
