# 灾变影像变化定位与建筑损伤复核

**简体中文** · [English](README.en.md)

并排查看同一地点灾前、灾后的两张影像。以奥索滑坡为例，可以沿河道对照滑坡前的山坡和滑坡后的堆积物。

[打开在线演示](https://zbw9654250-cmyk.github.io/disaster-change-review/?lang=zh) · [影像来源](docs/DATA-NOTICE.md)

![奥索滑坡前后影像及程序标出的变化区域](docs/assets/demo-preview.webp)

演示里有 5 个案例。对两处滑坡和拉帕尔马火山，程序比较灾前、灾后的 RGB 影像，自动圈出变化明显的位置。圈的位置可从原图重新计算，灾害类型和影响依据 NASA、USGS 的事件记录。另两个案例用预设圈对照飓风后的厂房和山火后的住宅，整栋损伤等级来自 xBD 标注。[变化检测脚本](scripts/detect_geology_changes.py) · [影像与判读依据](docs/DATA-NOTICE.md)

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
