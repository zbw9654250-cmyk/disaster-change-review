# 屋面损伤轮廓

输入同一测区的三组模型预测，输出 WGS84 GeoJSON。每个 Polygon 包含 `cls=Decking`（屋面板外露）或 `cls=Hole`（屋面孔洞）。程序在当地 UTM 坐标系计算面积和几何交叠，按固定模型系数为辅助候选排序。

## 复跑公开测区

以下命令从仓库根目录执行。输出目录需已存在。程序会替换同名输出 GeoJSON。

```sh
python -m pip install -r modules/roof_candidates/requirements.txt
python modules/roof_candidates/apply_recall.py --strong data/roof_candidates/strong.geojson --same data/roof_candidates/same.geojson --dual data/roof_candidates/dual.geojson --mode equal_budget --output candidates.geojson
```

`strong` 是四地区训练的两个单类专用模型预测，`same` 是两地区训练的两个单类模型预测，`dual` 是同样两地区训练的双类模型预测。每组可传一个合并文件或多个同场景分类文件。输入格式为 GeoJSON FeatureCollection，可使用 WGS84 或有明示坐标系的图层。空图层须提供空 features 数组。`equal_budget` 保持强模型的复核总量，`low_fp` 减少辅助补入数量。参数保存在 `pipeline_policy.json`。模型融合的结果可以作为 [整栋初评](../buildings/README.md) 的 `--damage` 输入。

五个公开测区有 880 个人工标注对象。按同类 IoU ≥ 0.5 一对一匹配，等预算模式在 1,269 个候选中命中 523 个，原四地区单类模型命中 501 个。该比较复用了原作者已发布的预测图层。仓库附带一个测区用于重放。[示范数据说明](../../data/roof_candidates/README.md) · [原作者模型、预测与人工轮廓](https://zenodo.org/records/20581719)

## 从单张正射图推理

[整图分割程序](segmentation/README.md) 可以运行原作者的双类权重和四地区孔洞权重，产生带坐标的分类 GeoTIFF，并导出损伤 GeoJSON。等预算对照另需上述三组真实模型输出；单张双类分割图可直接用于逐栋面积统计。

代码采用 MIT；上游模型和权重分别按发布者条款使用。[原 GitHub 项目](https://github.com/maja-kucharczyk/roof-damage-assessment) · [论文](https://doi.org/10.3390/rs17203456)
