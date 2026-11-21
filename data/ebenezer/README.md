# Ebenezer 单期建筑示例

`post.tif` 是荷属圣马丁 Ebenezer 地区 2017 年 9 月 24 日的 RGB 航拍正射裁片，约 0.072 米/像素，坐标系为 EPSG:32620。GlobalMedic – RescUAV 通过 OpenAerialMap 发布该航片，许可为 CC BY 4.0。[影像记录](https://api.openaerialmap.org/meta/59e62be63d6412ef7220c38b) · [许可](https://creativecommons.org/licenses/by/4.0/)

`footprints.geojson` 的 8 栋建筑范围根据当期影像独立描绘。该测区缺少现场损伤等级真值。`damage.geojson` 保留上游等预算推理结果中与这张裁片相交的 3 个候选，其来源为 Kucharczyk 等人公开的模型输出。[源数据](https://zenodo.org/records/20581719)

`recorded/` 包含实际在 RTX 5090 运行 Qwen3-VL-4B-Instruct 时使用的带目标描边裁图、记录影像哈希的原始预测（`grades.jsonl`）与该运行的清单。可用建筑模块的导出命令离线重建照片页。新生成的无标线 RGB 和掩膜适合用于新评级和局部解释；挂接程序会校验两边使用的源 RGB 字节，避免把来自旧图的模型判断移到另一幅图上。
