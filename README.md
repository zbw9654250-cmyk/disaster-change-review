# 灾后屋面损伤复核

**简体中文** · [English](README.en.md)

从灾后航拍图中找出值得复查的屋面孔洞和屋面板外露区域。在五个测区，复核人员要看的轮廓数量相同，我们的方法比原模型多找回了 **22 处损伤**，并保留了原模型的全部 501 处命中。

[打开屋面损伤对比演示](https://zbw9654250-cmyk.github.io/disaster-change-review/?lang=zh) · [逐测区结果](results/roof_objects.json) · [原作者的模型与数据](https://github.com/maja-kucharczyk/roof-damage-assessment)

![Ebenezer 同一栋建筑的航拍图，左右对照原模型和当前方法给出的屋面损伤轮廓](docs/assets/demo-preview.webp)

在圣马丁岛 Ebenezer，一处外露的屋面板呈 L 形。原模型把它拆成两块，较大的一块主要覆盖右下角。当前方法从另一组模型预测中选出了更完整的轮廓。最佳预测与人工参考轮廓的交并比（IoU，越接近 1 越吻合）从 **0.328 提高到 0.879**。另一栋屋顶上，原模型漏掉了一个孔洞，当前方法找回了它，IoU 为 **0.858**。演示里可以开关人工参考轮廓，也可以点击任一侧放大。[对照外露屋面板](https://zbw9654250-cmyk.github.io/disaster-change-review/?lang=zh&sample=ebenezer-39) · [对照屋顶孔洞](https://zbw9654250-cmyk.github.io/disaster-change-review/?lang=zh&sample=ebenezer-7)

## 同样的复核数量，多找到了什么

原基线使用两个 Mask2Former 模型，分别找屋面板外露和孔洞。每个测区提交的候选数保持不变。评测中的 880 处人工标注按损伤区域逐处计数，一栋建筑可以有多处损伤。预测类别正确、IoU 至少为 0.50，并与标注一对一匹配，才算命中。

| 五个测区合计 | 提交复核的轮廓 | 命中 | 误报 | 漏检 | F1 |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原模型 | 1,269 | 501 | 768 | 379 | 46.63% |
| 当前方法 | 1,269 | **523** | **746** | **357** | **48.67%** |

新增命中包括 **13 处屋面板外露、9 处孔洞**。我们用两组辅助模型的预测替换了 79 个极小的原始候选。挑选时综合考虑轮廓形状、与其他模型的重合程度和附近候选的密度，并去掉重复轮廓。在同五个测区固定这 79 个名额做对照，只按面积挑选能多找回 14 处，使用完整排序能多找回 22 处。[排序对照记录](results/roof_ranking_ablation.json)

## 在本地复现

下载仓库后，直接打开 [docs/index.html](docs/index.html) 即可离线看演示。要在 CPU 上重跑 Ebenezer 的候选筛选，在仓库根目录用 Python 3.12 执行以下命令。三份输入都是仓库附带的模型预测。

```sh
python -m pip install -r modules/roof_candidates/requirements.txt
python modules/roof_candidates/apply_recall.py --strong data/roof_candidates/strong.geojson --same data/roof_candidates/same.geojson --dual data/roof_candidates/dual.geojson --mode equal_budget --output candidates.geojson
```

用 QGIS 打开 `candidates.geojson`，可以看到 178 个候选轮廓，其中 87 个标为屋面板外露、91 个标为孔洞。运行 `python scripts/replay_results.py` 可从仓库保存的逐区计数复算上表。[筛选代码与输入说明](modules/roof_candidates/README.md)

## 更多案例与工具

- **灾前灾后影像**。五组影像用预设黄圈指示观察位置。滑坡、火山案例的说明依据 NASA 和 USGS 的事件记录，飓风和山火案例的整栋损伤等级来自 xBD。[查看灾前灾后影像](https://zbw9654250-cmyk.github.io/disaster-change-review/?lang=zh&view=gallery) · [影像来源](docs/DATA-NOTICE.md)
- **解释屋顶变化**。系统在两期屋面图上选取对应位置，测量颜色、亮度和反差后生成说明，可用 Qwen3-VL 核验。在 20 栋建筑上，两名 AI 评阅者都认为说明具体且有图可查的有 20 栋，旧版自由生成的检索增强说明有 1 栋。单用图像测量也达到 20 栋。[局部说明与评测方法](modules/observations/README.md)
- **逐栋初评**。给定建筑轮廓，可统计每栋屋顶的损伤面积，并用 Qwen3-VL 给出整栋初评。40 栋中有 14 栋与 xBD 等级一致，7 栋待判。[逐栋评估](modules/buildings/README.md) · [完整评测](results/README.md)

代码采用 [MIT 许可](LICENSE)。屋面轮廓数据和 Ebenezer 航片按 CC BY 4.0 署名，xBD 派生影像采用 CC BY-NC-SA 4.0。[数据、影像和模型许可](NOTICE.md)
