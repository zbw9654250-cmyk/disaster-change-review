# 灾变影像变化定位与建筑损伤复核

**简体中文** · [English](README.en.md)

对照同一地点的灾前影像、基线灾后结果和改进后的灾后结果。默认展示拉帕尔马火山、迈克尔飓风和圣罗莎山火三组更容易核对的变化。每组都把灾前、灾后基线圈和灾后改进轮廓放在一起。

[打开在线演示](https://zbw9654250-cmyk.github.io/disaster-change-review/?lang=zh) · [影像来源](docs/DATA-NOTICE.md)

仓库仍保留奥索和大苏尔两组原始案例，打开对应的 `case` 参数即可复现，但它们不放在默认精选列表中，因为两种候选在这些图上没有形成可见增益。橙色基线圈由 RGB 变化检测器生成。拉帕尔马的绿色轮廓由灾后像素变化掩膜矢量化得到。迈克尔和圣罗莎的绿色轮廓由同一裁切范围内的公开 xBD destroyed 建筑 footprint 引导，覆盖完整受灾屋顶。xBD 轮廓是公开标注引导的参考边界，不代表独立模型已经输出了精确损伤掩膜。灾害类型和影响依据 NASA、USGS 的事件记录，建筑案例使用 xBD 影像与标注。[区域生成脚本](scripts/generate_gallery_regions.py) · [影像与判读依据](docs/DATA-NOTICE.md)

这里的基线和拉帕尔马改进结果使用同一个变化检测器。基线只保留最高分区域，拉帕尔马改进结果将连续变化掩膜转成边缘轮廓。两组建筑示例把公开建筑 footprint 作为完整受灾建筑的空间约束，用来直观看局部候选与整栋轮廓的覆盖差异。

点击任一张图可以放大。要离线查看，下载并解压仓库，双击 [docs/index.html](docs/index.html)。

## 在本地跑一个例子

这个例子用 CPU 比较 8 栋建筑的灾前后影像。下载仓库后，在根目录用 Python 3.12 运行以下命令。

```sh
python -m pip install -r modules/observations/requirements.txt
python modules/observations/run_roofs.py --cases data/xbd/confirm/cases.jsonl --output observations.jsonl
```

生成的 `observations.jsonl` 每行对应一栋建筑。`explanation_zh` 描述屋面颜色或亮度的变化，`evidence_region` 给出两张图上的对应位置。再次运行时请换一个输出文件名。[查看样例输出](results/observations/out/confirm-measure.jsonl)

## 代码能做什么

| 任务 | 输入和输出 |
| --- | --- |
| [找屋面损伤](modules/roof_candidates/README.md) | 合并多组分割预测，在地图上标出屋面孔洞和屋面板外露的位置，导出 GeoJSON。 |
| [按栋评估损伤](modules/buildings/README.md) | 用灾后航片和建筑轮廓统计损伤面积。Qwen3-VL 的整栋初评在 40 栋中有 14 栋与 xBD 标注一致，7 栋待判。 |
| [解释局部变化](modules/observations/README.md) | 比较同一屋面在两期影像里的颜色和亮度，给出说明和对应区域，可用 Qwen3-VL 核对。 |

项目代码采用 [MIT 许可](LICENSE)。公开影像和模型各有使用条件，xBD 派生影像限非商业使用并要求署名、以相同方式共享。[数据和模型许可](NOTICE.md)
