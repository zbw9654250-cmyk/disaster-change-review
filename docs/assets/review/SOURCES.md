# Ebenezer 航拍与损伤轮廓 · Image and outline credits

两例均来自 2017 年 9 月 24 日荷属圣马丁 Ebenezer 的同一次灾后航拍。两种方法使用同一张裁图。左、右轮廓分别来自原作者的四地区单类模型和本项目在相同复核名额下导出的结果。图中可叠加原作者的人工参考轮廓。对照页保存了真实推理记录，打开网页时直接读取对应坐标。[五测区评测](https://github.com/zbw9654250-cmyk/disaster-change-review/blob/main/results/roof_objects.json)

Both cases use a single post-storm orthophoto of Ebenezer, Sint Maarten, captured on September 24, 2017. Both models are displayed over the same RGB crop. The baseline is the published four-region specialist model for each class. The current outlines are from the project’s saved equal-budget output. The reference is the human annotation released with the dataset. [Current prediction layer](https://github.com/zbw9654250-cmyk/disaster-change-review/blob/main/results/ebenezer_candidates.geojson)

| 原图与改动 · Source and adaptation | 署名与许可 · Attribution and license |
| --- | --- |
| `s_ebenezer.tif` · 原始 RGB、原生分辨率裁切。Native-resolution crops of the original RGB orthophoto. | GlobalMedic / RescUAV via OpenAerialMap, CC BY 4.0. [Image record](https://api.openaerialmap.org/meta/59e62be63d6412ef7220c38b) |
| `Polygons.zip` · 原始人工标注与模型预测；投影到裁图像素坐标。Published reference and prediction polygons transformed to crop pixel coordinates. | Maja Kucharczyk, Paul R. Nesbit and Chris H. Hugenholtz, CC BY 4.0. [Data release](https://zenodo.org/records/20581719) · [Upstream model code](https://github.com/maja-kucharczyk/roof-damage-assessment) |

复用这些裁片和轮廓时请保留上述署名、来源及许可，并标明裁切和坐标变换。Retain the credits, source links and license when reusing these crops or outlines, and identify the adaptations. [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/)

## 逐例核对 · Case records

窗口以原始 GeoTIFF 的左上角为原点，依次为像素列、行、宽、高。面积和交并比（IoU）在 EPSG:32620 坐标系下计算。网页保存与目标参考轮廓有正面积相交的所有同类预测。IoU 取单个预测与参考的最高交并比。评测要求类别一致、IoU 至少 0.50，且每个标注最多计一次命中。

Windows below are pixel column, row, width and height in the original GeoTIFF, measured from the upper left. Areas and IoUs are computed in EPSG:32620. The viewer stores all same-class outlines that overlap the target. The displayed IoU is the best overlap of an individual prediction with the reference. Evaluation counts each same-class reference at most once, at IoU ≥ 0.50.

| 人工参考 FID · Reference | 裁切窗口 · Crop window | 参考面积 · Area | 原预测 GDB FIDs / IoU | 当前输出 `id` / IoU |
| --- | --- | ---: | --- | --- |
| 39 · 屋面板外露 / Exposed decking | `7085, 11676, 330, 220` | 73.13 m² | 63 / 0.3282, 64 / 0.0308 | 83 / 0.8788, 60 / 0.3282, 61 / 0.0308 |
| 7 · 屋面孔洞 / Roof hole | `5486, 4672, 156, 104` | 1.37 m² | 无相交轮廓 / No overlap | 84 / 0.8580 |

原始标注来自 `Reference_Polygons.gdb` 的 `s_ebenezer` 图层。基线在同名图层中分别读取 `Predicted_Polygons_Dominica_SintMaarten_TheBahamas_USVI_RoofDecking.gdb` 和 `Predicted_Polygons_Dominica_SintMaarten_TheBahamas_USVI_RoofHole.gdb`。用 GeoTIFF 的仿射变换将轮廓转成以各裁图左上角为原点的路径，显示坐标保留到 0.01 像素。

The source layer is `s_ebenezer` in each geodatabase named above. Each path in the viewer is derived using the inverse affine transform for the image window. Display coordinates are rounded to 0.01 pixels. [Viewer image paths and polygons](cases.js)

| 文件 · File | SHA-256 |
| --- | --- |
| `s_ebenezer.tif` | `1506d0c1473849d20b5730e1e502d2193829c0453c399c5235bc8efdc2e17dda` |
| `Polygons.zip` | `06108e7cf4152f0ba798fbb566546b4780585480dee946e27d855034e21094de` |
| `results/ebenezer_candidates.geojson` | `b758a9653247380e1bd7798aa73fe81796a2b6a933791af4a3bca1a8989eeb4c` |
