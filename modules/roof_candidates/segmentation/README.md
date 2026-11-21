# 灾后正射图分割

独立的 OpenMMLab 推理环境读取有米制投影、标记红绿蓝波段的 8 位 RGB GeoTIFF，以 0.05 米网格执行 Mask2Former 推理。程序使用 512 像素窗口和 256 像素步长，将重叠窗口的类别分数按 Hann 窗加权后生成分类图。输出值为 0 背景、1 屋面板外露、2 孔洞、255 无数据。

单独的 Python 3.12 虚拟环境中先按设备安装 PyTorch 2.7 和 torchvision 0.22，再安装本目录的依赖。以下命令从仓库根目录执行，所有输出均选用新路径。首次下载需访问 Zenodo，下载器校验 CRC、文件尺寸与固定 SHA-256。完成下载后推理可离线运行。

```sh
python -m pip install -r modules/roof_candidates/segmentation/requirements.txt
python modules/roof_candidates/segmentation/fetch.py --model dual --assets-dir weights
python modules/roof_candidates/segmentation/fetch.py --model hole --assets-dir weights
python modules/roof_candidates/segmentation/infer.py --image data/ebenezer/post.tif --assets-dir weights --output dual.tif --device cuda
python modules/roof_candidates/segmentation/predict_holes.py --image data/ebenezer/post.tif --assets-dir weights --output holes.tif --device cuda
python modules/roof_candidates/segmentation/merge_masks.py --dual-mask dual.tif --hole-mask holes.tif --output combined.tif
python modules/roof_candidates/segmentation/vectorize_mask.py --mask combined.tif --output roof-damage.geojson
```

`--device cpu` 支持 CPU 推理。双类模型提供外露预测，四地区孔洞模型提供孔洞预测；合并图的冲突像素采用孔洞标签。矢量化按同类别像素的四邻域连接，并将 Polygon 汇出为 WGS84。该图层可交给整栋初评程序。随仓库的 Ebenezer 正射图为公开影像的裁片；裁片单独送入网络与在原图推理后裁切，边缘上下文会不同。

模型作者为 Maja Kucharczyk、Paul R. Nesbit、Chris H. Hugenholtz。下载的权重与 EMD 来自其 Zenodo 归档。模型配置 `mask2former.py` 源自 MMSegmentation 并保留 Apache-2.0 署名与许可证；项目自己的推理适配和融合代码依主仓库 MIT 条款。[原仓库的推理实现](https://github.com/maja-kucharczyk/roof-damage-assessment/blob/1698d70dc3adcc81e2599a4fdbd3ab46d97dc520/Tools/Toolbox_Scripts/delineate_roof_damage.py) · [数据与权重](https://zenodo.org/records/20581719) · [配置许可证](LICENSE-MMSegmentation.txt)
