"""Measure co-located visible colour and contrast on a building's two source images."""
import argparse
import colorsys
import hashlib
import json
from math import ceil
from pathlib import Path
import time

import numpy as np
from PIL import Image, ImageOps
from scipy.ndimage import binary_erosion, gaussian_filter

import focus_caption as focus
import ground_caption as base

GRID = 48
LUMA = np.array([.2126,.7152,.0722])


def color_name(rgb):
    r,g,b = map(float,rgb)
    light = np.dot(rgb,LUMA)
    chroma = max(rgb)-min(rgb)
    if chroma < max(9., .082*max(rgb)):
        if light >= 224: return "近白色"
        if light >= 167: return "浅灰色"
        if light >= 95: return "灰色"
        if light >= 45: return "深灰色"
        return "近黑色"
    hue = colorsys.rgb_to_hsv(r/255,g/255,b/255)[0]*360
    if light>=199 and chroma<70:
        if 164<=hue<270: return "带蓝调的浅色"
        if 65<=hue<164: return "带绿调的浅色"
        if 15<=hue<65: return "带暖调的浅色"
        return "浅色"
    muted = chroma < 26 or chroma < max(rgb)*.21
    if hue < 18 or hue >= 345: return "灰褐色" if muted else "红褐色"
    if hue < 49: return "灰褐色" if muted else "棕褐色"
    if hue < 68: return "黄灰色" if muted else "黄褐色"
    if hue < 92: return "黄绿色" if not muted else "灰绿色"
    if hue < 164: return "灰绿色" if muted else "绿色"
    if hue < 193: return "青灰色" if muted else "青色"
    if hue < 273: return "蓝灰色" if muted else "蓝色"
    return "紫灰色" if muted else "紫色"


def edge_band(rgb):
    dark=np.max(rgb,axis=2)<=8
    invalid=np.zeros_like(dark)
    for axis in (0,1):
        stripes=dark if axis==0 else dark.T
        dest=invalid if axis==0 else invalid.T
        near=np.mean(stripes,axis=1)>=.985
        minimum=max(6,ceil(len(near)*.035))
        for side in (0,1):
            seq=near if side==0 else near[::-1]
            length=int(np.argmin(seq)) if not np.all(seq) else len(seq)
            if length>=minimum:
                if side==0: dest[:length,:]=True
                else: dest[-length:,:]=True
    return invalid


def phase_data(case,folder,prefix,xy):
    image_path=folder/case[prefix+"image_path"]
    with Image.open(image_path) as src:
        rgb=np.asarray(ImageOps.exif_transpose(src).convert("RGB"))
    h,w=rgb.shape[:2]
    if len(xy)!=4 or not (0<=xy[0]<xy[2]<=1 and 0<=xy[1]<xy[3]<=1):
        raise ValueError("Invalid normalized evidence window")
    coords=tuple(round(v*n) for v,n in zip(xy,(w,h,w,h)))
    x0,y0,x1,y1=coords
    if x1-x0<2 or y1-y0<2: raise ValueError("Unresolved evidence window")
    with Image.open(folder/case[prefix+"mask_path"]) as src:
        foot=np.asarray(ImageOps.exif_transpose(src).convert("L"))>=128
    if foot.shape!=(h,w): raise ValueError("Image and building mask grids differ")
    vp=case.get(prefix+"valid_mask_path")
    valid_digest=None
    if vp:
        data_path=folder/vp
        valid_digest=hashlib.sha256(data_path.read_bytes()).hexdigest()
        with Image.open(data_path) as src:
            vm=np.asarray(src)
        if vm.shape!=foot.shape: raise ValueError("Invalid validity-mask grid")
        good=vm>0
        source="provided"
    elif image_path.suffix.lower() in {".tif",".tiff"} or Path(str(image_path)+".msk").is_file():
        import rasterio
        with rasterio.open(image_path) as src:
            good=src.dataset_mask()>0
        source="gdal"
    else:
        good=~edge_band(rgb)
        source="edge_band_screen"
    fg=foot[y0:y1,x0:x1]
    valid=fg & good[y0:y1,x0:x1]
    n=int(valid.sum())
    fraction=n/max(1,int(fg.sum()))
    if n<24 or fraction<.85:
        raise ArithmeticError("选区内可用的建筑像素不足。")
    crop=rgb[y0:y1,x0:x1].copy()
    crop[~valid]=0
    target=Image.fromarray(valid.astype(np.uint8)*255)
    alpha=np.asarray(target.resize((GRID,GRID),Image.Resampling.BILINEAR),dtype=float)/255
    image=np.asarray(Image.fromarray(crop).resize((GRID,GRID),Image.Resampling.BILINEAR),dtype=float)
    # Premultiplied resampling prevents surrounding ground or the mask background from leaking in.
    alpha=gaussian_filter(alpha,.7)
    image=gaussian_filter(image,(.7,.7,0))/np.maximum(alpha[:,:,None],1e-6)
    usable=binary_erosion(alpha>.90,iterations=1)
    return image.clip(0,255),usable,dict(valid_source_pixels=n,footprint_source_pixels=int(fg.sum()),
                       valid_fraction=round(fraction,4),source_window_xyxy=list(coords),
                       validity_source=source,valid_mask_sha256=valid_digest)


def summary(rgb,common,info):
    pixels=rgb[common]
    median=np.median(pixels,axis=0)
    y=pixels@LUMA
    lo,mid,hi=np.percentile(y,[10,50,90])
    spread=hi-lo
    return {**info,"median_rgb":[round(float(v),1) for v in median],"color_zh":color_name(median),
            "median_luma":round(mid,1),"luma_p10":round(lo,1),"luma_p90":round(hi,1),
            "luma_spread":round(spread,1),"contrast_zh":"明暗差较大" if spread>45 else
            "亮度较为接近" if spread<20 else "可见深浅过渡"}


def fact(entries,kind,text):
    entries.append(dict(id=f"F{len(entries)+1}",kind=kind,text=text,text_zh=text))


def appearance(pre,post,paired_diff,name,low):
    a=pre["color_zh"] if pre else None
    b=post["color_zh"]
    facts=[]
    where="建筑足迹"+base.SECTORS[name][0]+"的选区内"
    if pre is None:
        fact(facts,"color",f"{where}，当期画面以{b}为主。")
        fact(facts,"contrast",f"该处{post['contrast_zh']}。")
        return "single",facts
    diff=post["median_luma"]-pre["median_luma"]
    direction="变亮" if diff>0 else "变暗"
    if low and paired_diff<8:
        if a==b:
            fact(facts,"stable",f"{where}，两期均呈{b}，整体明暗接近。")
        else:
            fact(facts,"stable",f"{where}，灾前的中间色调为{a}，灾后为{b}，两期像素差异较小。")
        state="stable"
    elif a!=b:
        extra=f"，局部整体{direction}" if abs(diff)>=24 else ""
        fact(facts,"color_change",f"{where}，灾前画面呈{a}，灾后呈{b}{extra}。")
        state="changed" if paired_diff>=12 else "uncertain"
    elif abs(diff)>=14:
        fact(facts,"brightness_change",f"{where}，两期主体均呈{b}，灾后比灾前明显{direction}。")
        state="changed"
    else:
        fact(facts,"color",f"{where}，两期画面的主要色调均为{b}。")
        state="stable" if low else ("changed" if paired_diff>=15 else "uncertain")
    spread_delta=post["luma_spread"]-pre["luma_spread"]
    if abs(spread_delta)>=17:
        phrase="更加明显" if spread_delta>0 else "减弱"
        fact(facts,"contrast_change",f"与灾前相比，选区内不同位置的明暗反差在灾后{phrase}。")
    elif 14<=abs(diff)<24 and facts[0]["kind"]!="brightness_change":
        fact(facts,"brightness_change",f"比较同一选区的中间亮度，灾后画面{direction}。")
    elif pre["luma_spread"]<20 and post["luma_spread"]<20:
        fact(facts,"contrast",f"两个时期的局部都比较均匀，选区内部亮度起伏小。")
    elif pre["luma_spread"]>45 and post["luma_spread"]>45:
        fact(facts,"contrast","两期选区内均能区分较亮和较暗的部分。")
    else:
        fact(facts,"contrast",f"灾后选区内{post['contrast_zh']}。")
    if state=="changed" and facts[0]["kind"]=="color" and abs(spread_delta)<17:
        state="uncertain"
    return state,facts


def subregion_fact(image,common,facts):
    y=image@LUMA
    levels=[]
    for iy in (0,1):
        for ix in (0,1):
            yy=slice(iy*24,(iy+1)*24)
            xx=slice(ix*24,(ix+1)*24)
            supported=common[yy,xx]
            if supported.mean()>=.45:
                levels.append((float(np.median(y[yy,xx][supported])),("左上","右上","左下","右下")[iy*2+ix]))
    if len(levels)<2: return None
    light,bright=max(levels)
    dark,dim=min(levels)
    if light-dark<29: return None
    fact(facts,"local_spatial_contrast",f"在灾后这处选框内，{bright}部分比{dim}部分更亮。")
    return {"brighter_cell":bright,"darker_cell":dim,"median_luma_gap":round(light-dark,1)}


def measure(case,root,region=None):
    start=time.monotonic()
    folder=Path(root)
    result=dict(building_id=case["building_id"],model="target-local-photometry-v1",method="measurement",
                status="inference_error",change_status="uncertain",explanation_zh="")
    try:
        post,hashes=base.load_phase(folder,case,"")
        result.update(hashes)
        pre=None
        if case.get("pre_image_path"):
            pre,hashes=base.load_phase(folder,case,"pre_")
            result.update(hashes)
        if min(float(case.get("pre_coverage_fraction",1)),float(case.get("coverage_fraction",1)))<.98:
            raise ArithmeticError("建筑影像未完整覆盖，选区需要复核。")
        name,c,p,alignment=focus.choose(pre,post)
        if region is None:
            _,post_box,_=focus.window(post,c)
            region=dict(name=name,post_xyxy=post_box,coords="normalized_original_image")
            if pre:
                _,region["pre_xyxy"],_=focus.window(pre,p)
        name=region["name"]
        if region.get("coords")!="normalized_original_image" or name not in base.SECTORS:
            raise ValueError("Invalid region metadata")
        new,nmask,ninfo=phase_data(case,folder,"",region["post_xyxy"])
        oldinfo=None
        common=nmask
        overlap=1.0
        if pre:
            old,omask,oinfo=phase_data(case,folder,"pre_",region["pre_xyxy"])
            common=nmask&omask
            overlap=common.sum()/max(1,(nmask|omask).sum())
            if overlap<.55: raise ArithmeticError("两期选区的共同有效像素过少。")
        if common.sum()<48: raise ArithmeticError("选区内可复查的像素过少。")
        now=summary(new,common,ninfo)
        paired_diff=None
        if pre:
            oldinfo=summary(old,common,oinfo)
            paired_diff=round(float(np.abs(new-old)[common].mean()),2)
        state,facts=appearance(oldinfo,now,paired_diff,name,alignment["low_difference"])
        spatial=subregion_fact(new,common,facts)
        measurement=dict(quality="usable",region_zh=base.SECTORS[name][0],pre=oldinfo,post=now,
                         registration=alignment,common_grid_size=[GRID,GRID],valid_grid_cells=int(common.sum()),
                         grid_mask_iou=round(float(overlap),4),pair_mean_abs_rgb_0_255=paired_diff,
                         spatial_contrast=spatial,facts=facts)
        report=[facts[0],facts[-1]] if spatial and facts[1]["kind"]=="contrast" else facts[:2]
        result.update(status="ok",change_status=state,explanation_zh="".join(f["text"] for f in report),
                      evidence_region=region,measurement=measurement)
        for prefix,info in (("",now),("pre_",oldinfo)):
            if info and info["valid_mask_sha256"]:
                result[prefix+"valid_mask_sha256"]=info["valid_mask_sha256"]
    except ArithmeticError as exc:
        result.update(status="quality_limited",explanation_zh=str(exc),evidence_region=None,
                      measurement={"quality":"insufficient","facts":[]})
    except (ValueError,KeyError,OSError,TypeError) as exc:
        result["error"]=str(exc)
    result["seconds"]=round(time.monotonic()-start,4)
    return result


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cases",type=Path,required=True)
    parser.add_argument("--output",type=Path,required=True)
    args=parser.parse_args()
    rows=[json.loads(s) for s in args.cases.read_text(encoding="utf-8-sig").splitlines() if s.strip()]
    if not rows or len({r["building_id"] for r in rows})!=len(rows):raise ValueError("Duplicate or missing cases")
    results=[measure(r,args.cases.parent) for r in rows]
    args.output.parent.mkdir(exist_ok=True,parents=True)
    with args.output.open("x",encoding="utf8") as f:
        for row in results:f.write(json.dumps(row,ensure_ascii=False,allow_nan=False)+"\n")
