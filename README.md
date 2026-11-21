# 灾变影像变化定位与建筑损伤复核

**简体中文** · [English](README.en.md)

把同一地点灾前、灾后的两张影像放在一起，圈出发生变化的位置。比如在奥索滑坡案例里，左圈能看到泥石横过河道，右圈能看到上游的水面变宽。

[打开在线演示](https://zbw9654250-cmyk.github.io/disaster-change-review/?lang=zh) · [影像来源](docs/DATA-NOTICE.md)

![奥索滑坡前后对比，两组圆圈分别标出滑坡和上游积水](docs/assets/demo-preview.webp)

演示里有 5 个案例。三个地质灾害案例的圈由人工标出，影响范围来自 NASA 和 USGS 的事件记录。另两个案例展示飓风和山火前后的屋面变化，整栋建筑的损伤等级来自 xBD 标注。点击任一张图可以放大。要离线查看，下载并解压仓库，双击 [docs/index.html](docs/index.html)。

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
| [按栋评估损伤](modules/buildings/README.md) | 用灾后航片和建筑轮廓逐栋裁图，统计屋面损伤面积，可用 Qwen3-VL 给出整栋初评。 |
| [解释局部变化](modules/observations/README.md) | 比较同一屋面在两期影像里的颜色和亮度，给出说明和对应区域，可用 Qwen3-VL 核对。 |

在 5 个测区，两种方法各标出 1,269 处疑似损伤。合并多组预测后，正确定位的损伤从 501 处增至 523 处，误报从 768 处降至 746 处。整栋评级单独评测，40 栋建筑中有 14 栋与 xBD 标注一致，7 栋待判，评级仍需人工复核。[评测方法与完整结果](results/README.md)

项目代码采用 [MIT 许可](LICENSE)。公开影像和模型各有使用条件，xBD 派生影像限非商业使用并要求署名、以相同方式共享。[数据和模型许可](NOTICE.md)
