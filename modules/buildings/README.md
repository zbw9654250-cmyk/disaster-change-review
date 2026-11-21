# 逐栋建筑损伤初评

输入带坐标的灾后 RGB 正射影像、带唯一 `building_id` 的建筑多边形，以及可选的屋面损伤图层。程序在当地米制坐标中对候选与每栋的相交部分取并集，分别统计外露和孔洞数量、面积及总覆盖率。输入建筑即使没有局部候选也会保留。

## 无 GPU 浏览已记录的评级

从仓库根目录执行。已有的真实模型输出可以直接用来生成地图图层和离线页。

```sh
python -m pip install -r modules/buildings/requirements.txt
python modules/buildings/export_buildings.py --cases data/ebenezer/recorded/cases.jsonl --predictions data/ebenezer/recorded/grades.jsonl --out building-replay --credit "GlobalMedic / OpenAerialMap, CC BY 4.0"
```

示范来自 Ebenezer 的 8 栋建筑。旧评级基于当时使用的目标描线图，导出时会校验照片哈希。这批预测有 7 栋未见明显损伤、1 栋轻度；现场真值缺失，故只供复核。[示范数据来源](../../data/ebenezer/README.md)

## 在自己的影像上运行

以下命令生成供分级和 [局部解释](../observations/README.md) 共用的清单。每栋产出未描边的 RGB 原图 `image_path`、建筑掩膜 `mask_path`、有效像素掩膜 `valid_mask_path` 和定位描边预览 `preview_path`。掩膜与预览处于同一图像网格。

```sh
python modules/buildings/prepare_buildings.py --raster data/ebenezer/post.tif --footprints data/ebenezer/footprints.geojson --damage data/ebenezer/damage.geojson --scene-id ebenezer --output building-inputs
python modules/observations/run_roofs.py --cases building-inputs/cases.jsonl --output observations.jsonl
```

在 CUDA 模型环境安装匹配设备的 PyTorch、torchvision、Transformers 和 accelerate；参考环境为 PyTorch 2.8 与 Transformers 5.18。将 Qwen3-VL-4B-Instruct 权重下载到本地后运行：

```sh
python modules/buildings/vlm_predict.py --cases building-inputs/cases.jsonl --model /models/Qwen3-VL-4B-Instruct --model-id Qwen/Qwen3-VL-4B-Instruct --output grades.jsonl
python modules/observations/attach_observations.py --cases building-inputs/cases.jsonl --grades grades.jsonl --candidates observations.jsonl --output building-observations.jsonl
python modules/buildings/export_buildings.py --cases building-inputs/cases.jsonl --predictions grades.jsonl --out building-review
```

也可用 `run_buildings.py` 的 `--raster`、`--footprints`、`--damage`、`--scene-id`、`--model` 和 `--out` 一次运行裁图、Qwen 初评、GeoJSON 与 HTML 导出。已有两期建筑裁图时可以在清单加入 `pre_image_path` 直接运行 `vlm_predict.py`。整栋等级为无明显损伤、轻、中、重或待判，来源覆盖低于 98% 时转待判。历史 xBD 四档分级面板共 40 栋，默认模型答对 14 栋，此分数与局部外观说明的通过率分开计算。新清单采用未描边照片，与已归档的描边评级分别保留来源哈希。[Qwen3-VL](https://github.com/QwenLM/Qwen3-VL) · [xBD](https://arxiv.org/abs/1911.09296)
